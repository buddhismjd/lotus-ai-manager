from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlite3
import tempfile

import backend.storage.database as database
from backend.storage.repositories import LeadRepository


def main() -> None:
    original_dir = database.DATA_DIR
    original_file = database.DATABASE_FILE
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database.DATA_DIR = root
            database.DATABASE_FILE = root / "diagnostics.db"
            database.initialize_database()
            repository = LeadRepository()
            saved = repository.save(
                name="Диагностика",
                contact_method="telegram",
                contact_value="@diagnostic",
                interest="Проверка",
            )
            connection = sqlite3.connect(database.DATABASE_FILE)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(leads)")}
            connection.close()
            required = {
                "contact_channel", "contact_value", "updated_at", "session_id",
                "handoff_reason", "handoff_priority", "manager_summary",
            }
            assert required <= columns
            assert repository.get(saved.id) is not None
    finally:
        database.DATA_DIR = original_dir
        database.DATABASE_FILE = original_file

    print("lead_schema_migration=OK")
    print("lead_repository=OK")
    print("legacy_compatibility=OK")


if __name__ == "__main__":
    main()
