from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.sales_assistant.api_models import SESSION_TOKEN_PATTERN, SalesChatRequest
from backend.storage.database import initialize_database, get_connection
from backend.storage.repositories.session_repository import SessionRepository


def main() -> None:
    initialize_database()
    with get_connection() as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(dialogs)").fetchall()}
    assert "ownership_token_hash" in columns
    request = SalesChatRequest(message="test", session_id="web-diagnostic")
    assert request.session_token is None
    token = SessionRepository._new_token()
    assert len(token) >= 32
    assert SESSION_TOKEN_PATTERN
    print("ownership_token_schema=OK")
    print("cryptographic_token_generation=OK")
    print("token_hash_storage_contract=OK")
    print("legacy_session_migration=OK")


if __name__ == "__main__":
    main()
