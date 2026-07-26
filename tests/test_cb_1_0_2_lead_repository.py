from __future__ import annotations

import sqlite3
from pathlib import Path

import backend.storage.database as database
from backend.sales_assistant.handoff import HandoffPriority, HandoffReason
from backend.sales_assistant.lead_validator import LeadContactChannel, LeadContactData
from backend.storage.repositories import LeadRepository


def _temporary_database(tmp_path: Path, monkeypatch) -> Path:
    db_path = tmp_path / "cb-1-0-2.db"
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DATABASE_FILE", db_path)
    database.initialize_database()
    return db_path


def test_database_migrates_existing_leads_without_data_loss(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dialog_id INTEGER,
            name TEXT,
            phone TEXT,
            email TEXT,
            telegram TEXT,
            interest TEXT,
            comment TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL
        );
        INSERT INTO leads (name, telegram, interest, status, created_at)
        VALUES ('Анна', '@anna', 'Тур в Непал', 'new', '2026-07-26T10:00:00');
        """
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DATABASE_FILE", db_path)
    database.initialize_database()

    with database.get_connection() as migrated:
        row = migrated.execute("SELECT * FROM leads WHERE id = 1").fetchone()
    assert row["name"] == "Анна"
    assert row["contact_channel"] == "telegram"
    assert row["contact_value"] == "@anna"
    assert row["updated_at"] == "2026-07-26T10:00:00"


def test_repository_saves_structured_handoff(tmp_path, monkeypatch) -> None:
    db_path = _temporary_database(tmp_path, monkeypatch)
    repository = LeadRepository()
    saved = repository.save_handoff(
        contact=LeadContactData(
            name="Евгения",
            contact_channel=LeadContactChannel.TELEGRAM,
            contact_value="@evgenia",
            email="evgenia@example.com",
        ),
        reason=HandoffReason.BOOKING_REQUEST,
        priority=HandoffPriority.HIGH,
        manager_summary="Клиент хочет забронировать тур в Непал.",
        interest="Тур в Непал",
        session_id="session-42",
    )

    assert saved.id == 1
    assert saved.email == "evgenia@example.com"
    assert saved.handoff_reason == "booking_request"

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    row = connection.execute("SELECT * FROM leads WHERE id = ?", (saved.id,)).fetchone()
    connection.close()
    assert row["contact_channel"] == "telegram"
    assert row["contact_value"] == "@evgenia"
    assert row["handoff_priority"] == "high"
    assert row["manager_summary"] == "Клиент хочет забронировать тур в Непал."
    assert row["session_id"] == "session-42"


def test_legacy_repository_import_and_save_remain_compatible(tmp_path, monkeypatch) -> None:
    _temporary_database(tmp_path, monkeypatch)
    from backend.sales_assistant.leads import LeadRepository as LegacyLeadRepository

    saved = LegacyLeadRepository().save(
        name="Анна",
        contact_method="telegram",
        contact_value="@anna_test",
        interest="Кайлас",
    )

    assert saved.contact_method == "telegram"
    assert saved.contact_value == "@anna_test"
    assert LegacyLeadRepository().count() == 1


def test_repository_get_returns_saved_lead(tmp_path, monkeypatch) -> None:
    _temporary_database(tmp_path, monkeypatch)
    repository = LeadRepository()
    saved = repository.save(
        name="Ирина",
        contact_method="email",
        contact_value="irina@example.com",
        interest="Консультация",
    )

    loaded = repository.get(saved.id)
    assert loaded is not None
    assert loaded.name == "Ирина"
    assert loaded.email == "irina@example.com"
    assert loaded.status == "new"
