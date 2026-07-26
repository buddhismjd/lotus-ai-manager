from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import backend.main as main_module  # noqa: E402


def main() -> None:
    client = TestClient(main_module.app)
    valid = client.post(
        "/api/sales/chat",
        json={"message": "Расскажите о путешествиях", "session_id": "cb-1.5.1a-smoke"},
    )
    invalid = client.post(
        "/api/sales/chat",
        json={"message": "Туры", "session_id": "bad/session"},
    )
    extra = client.post(
        "/api/sales/reset",
        json={"session_id": "cb-1.5.1a-smoke", "unexpected": True},
    )
    assert valid.status_code == 200
    assert invalid.status_code == 422
    assert extra.status_code == 422
    assert invalid.json()["status"] == "invalid_request"
    print("valid_widget_request=OK")
    print("invalid_session_rejected=OK")
    print("unknown_payload_fields_rejected=OK")
    print("safe_validation_error_contract=OK")


if __name__ == "__main__":
    main()
