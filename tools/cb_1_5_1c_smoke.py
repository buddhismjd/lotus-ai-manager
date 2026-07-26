from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import backend.admin_security as admin_security
import backend.main as main_module
import backend.runtime_security as runtime_security
import backend.storage.database as database_module

client = TestClient(main_module.app)
preflight = client.options(
    "/api/sales/chat",
    headers={"Origin": "https://svet-lotosa.tilda.ws", "Access-Control-Request-Method": "POST"},
)
assert preflight.status_code == 200
print("trusted_cors_origin=OK")

with TemporaryDirectory() as folder:
    original = database_module.DATABASE_FILE
    database_module.DATABASE_FILE = Path(folder) / "smoke.db"
    try:
        database_module.initialize_database()
        with database_module.get_connection() as connection:
            assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        print("sqlite_wal=OK")
    finally:
        database_module.DATABASE_FILE = original

original_token = admin_security.ADMIN_TOKEN
admin_security.ADMIN_TOKEN = "smoke-admin-token"
try:
    assert client.get("/admin").status_code == 401
    assert client.get("/admin", headers={"X-Admin-Token": "smoke-admin-token"}).status_code == 200
    print("admin_auth=OK")
finally:
    admin_security.ADMIN_TOKEN = original_token

runtime_security.rate_limiter.clear()
original_limit = runtime_security.CHAT_RATE_LIMIT_PER_MINUTE
runtime_security.CHAT_RATE_LIMIT_PER_MINUTE = 1
try:
    assert client.post("/api/sales/chat", json={"message": "", "session_id": "smoke-rate-a"}).status_code == 200
    assert client.post("/api/sales/chat", json={"message": "", "session_id": "smoke-rate-b"}).status_code == 429
    print("safe_429_contract=OK")
finally:
    runtime_security.CHAT_RATE_LIMIT_PER_MINUTE = original_limit
    runtime_security.rate_limiter.clear()
