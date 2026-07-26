from __future__ import annotations

import json

from fastapi.testclient import TestClient

import backend.admin_security as admin_security
import backend.main as main_module
import backend.runtime_security as runtime_security
import backend.storage.database as database_module


def test_cors_allows_svet_lotosa_and_rejects_unknown_origin() -> None:
    client = TestClient(main_module.app)
    allowed = client.options(
        "/api/sales/chat",
        headers={
            "Origin": "https://svet-lotosa.tilda.ws",
            "Access-Control-Request-Method": "POST",
        },
    )
    denied = client.options(
        "/api/sales/chat",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://svet-lotosa.tilda.ws"
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def test_sqlite_connection_enables_wal_and_busy_timeout(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database_module, "DATABASE_FILE", tmp_path / "runtime.db")
    database_module.initialize_database()
    with database_module.get_connection() as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
    assert journal_mode.lower() == "wal"
    assert busy_timeout == database_module.SQLITE_BUSY_TIMEOUT_MS


def test_rate_limiter_returns_safe_429_contract(monkeypatch) -> None:
    runtime_security.rate_limiter.clear()
    monkeypatch.setattr(runtime_security, "CHAT_RATE_LIMIT_PER_MINUTE", 1)
    client = TestClient(main_module.app)
    first = client.post("/api/sales/chat", json={"message": "", "session_id": "limit-a"})
    second = client.post("/api/sales/chat", json={"message": "", "session_id": "limit-b"})
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limit_exceeded"
    assert second.headers["retry-after"] == "60"
    runtime_security.rate_limiter.clear()


def test_admin_routes_require_configured_token(monkeypatch) -> None:
    monkeypatch.setattr(admin_security, "ADMIN_TOKEN", "test-admin-token")
    client = TestClient(main_module.app)
    denied = client.get("/admin")
    allowed = client.get("/admin", headers={"X-Admin-Token": "test-admin-token"})
    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_security_events_are_written_as_json_lines(monkeypatch, tmp_path) -> None:
    log_file = tmp_path / "security.jsonl"
    monkeypatch.setattr(runtime_security, "SECURITY_LOG_FILE", log_file)
    runtime_security.rate_limiter.clear()
    monkeypatch.setattr(runtime_security, "CHAT_RATE_LIMIT_PER_MINUTE", 1)
    client = TestClient(main_module.app)
    client.post("/api/sales/chat", json={"message": "", "session_id": "log-a"})
    client.post("/api/sales/chat", json={"message": "", "session_id": "log-b"})
    payload = json.loads(log_file.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["event"] == "rate_limit_exceeded"
    assert payload["path"] == "/api/sales/chat"
    runtime_security.rate_limiter.clear()
