from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

import backend.main as main_module
import backend.storage.database as database_module
from backend.storage.database import get_connection, initialize_database


def _temporary_database(monkeypatch, tmp_path):
    path = tmp_path / "session-security.db"
    monkeypatch.setattr(database_module, "DATABASE_FILE", path)
    initialize_database()
    return TestClient(main_module.app)


def _new_session_id() -> str:
    return f"web-security-{uuid4().hex}"


def test_first_chat_issues_cryptographic_session_token(monkeypatch, tmp_path) -> None:
    client = _temporary_database(monkeypatch, tmp_path)
    session_id = _new_session_id()

    response = client.post(
        "/api/sales/chat",
        json={"message": "Какие есть туры?", "session_id": session_id},
    )

    assert response.status_code == 200
    token = response.json()["session_token"]
    assert isinstance(token, str)
    assert len(token) >= 32
    with get_connection() as connection:
        row = connection.execute(
            "SELECT ownership_token_hash FROM dialogs WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    assert row["ownership_token_hash"]
    assert row["ownership_token_hash"] != token


def test_protected_history_requires_ownership_token(monkeypatch, tmp_path) -> None:
    client = _temporary_database(monkeypatch, tmp_path)
    session_id = _new_session_id()
    created = client.post(
        "/api/sales/chat",
        json={"message": "Какие есть туры?", "session_id": session_id},
    ).json()

    denied = client.get(f"/api/sales/session/{session_id}")
    allowed = client.get(
        f"/api/sales/session/{session_id}",
        headers={"X-Session-Token": created["session_token"]},
    )

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "session_access_denied"
    assert allowed.status_code == 200
    assert len(allowed.json()["messages"]) == 2


def test_wrong_token_cannot_continue_or_reset_session(monkeypatch, tmp_path) -> None:
    client = _temporary_database(monkeypatch, tmp_path)
    session_id = _new_session_id()
    created = client.post(
        "/api/sales/chat",
        json={"message": "Хочу консультацию", "session_id": session_id},
    ).json()
    wrong = "A" * 43

    continued = client.post(
        "/api/sales/chat",
        json={"message": "Продолжим", "session_id": session_id, "session_token": wrong},
    )
    reset = client.post(
        "/api/sales/reset",
        json={"session_id": session_id, "session_token": wrong},
    )

    assert created["session_token"] != wrong
    assert continued.status_code == 403
    assert reset.status_code == 403


def test_token_rotation_invalidates_previous_token(monkeypatch, tmp_path) -> None:
    client = _temporary_database(monkeypatch, tmp_path)
    session_id = _new_session_id()
    old_token = client.post(
        "/api/sales/chat",
        json={"message": "Есть товары?", "session_id": session_id},
    ).json()["session_token"]

    rotated = client.post(
        "/api/sales/session/rotate-token",
        json={"session_id": session_id, "session_token": old_token},
    )
    new_token = rotated.json()["session_token"]

    assert rotated.status_code == 200
    assert new_token != old_token
    assert client.get(
        f"/api/sales/session/{session_id}",
        headers={"X-Session-Token": old_token},
    ).status_code == 403
    assert client.get(
        f"/api/sales/session/{session_id}",
        headers={"X-Session-Token": new_token},
    ).status_code == 200


def test_legacy_unprotected_history_remains_readable_during_migration(monkeypatch, tmp_path) -> None:
    client = _temporary_database(monkeypatch, tmp_path)
    session_id = _new_session_id()
    now = "2026-07-26T12:00:00"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO dialogs (session_id, status, started_at, updated_at)
            VALUES (?, 'active', ?, ?)
            """,
            (session_id, now, now),
        )

    response = client.get(f"/api/sales/session/{session_id}")
    assert response.status_code == 200
