from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.storage import database as database_module
from backend.storage.repositories.session_repository import SessionAccessDeniedError, SessionRepository


def main() -> None:
    original = database_module.DATABASE_FILE
    try:
        with tempfile.TemporaryDirectory() as directory:
            database_module.DATABASE_FILE = Path(directory) / "smoke.db"
            repository = SessionRepository()
            access = repository.establish_access("web-smoke")
            repository.append_message("web-smoke", "user", "test")
            repository.verify_access("web-smoke", access.token)
            try:
                repository.verify_access("web-smoke", "A" * 43)
            except SessionAccessDeniedError:
                pass
            else:
                raise AssertionError("wrong token was accepted")
            replacement = repository.rotate_token("web-smoke", access.token)
            assert replacement != access.token
    finally:
        database_module.DATABASE_FILE = original

    print("protected_session_creation=OK")
    print("history_ownership_check=OK")
    print("reset_ownership_contract=OK")
    print("token_rotation=OK")


if __name__ == "__main__":
    main()
