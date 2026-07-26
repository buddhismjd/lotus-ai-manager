from __future__ import annotations

from fastapi.testclient import TestClient

import backend.main as main_module
from backend.sales_assistant.api_models import MAX_MESSAGE_LENGTH

client = TestClient(main_module.app)


def test_chat_rejects_unknown_request_fields() -> None:
    response = client.post(
        "/api/sales/chat",
        json={"message": "Есть туры?", "session_id": "security-test", "admin": True},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "invalid_request"
    assert payload["error"]["code"] == "validation_error"
    assert "admin" in payload["error"]["fields"]


def test_chat_rejects_message_above_public_limit() -> None:
    response = client.post(
        "/api/sales/chat",
        json={"message": "я" * (MAX_MESSAGE_LENGTH + 1), "session_id": "security-test"},
    )

    assert response.status_code == 422
    assert "message" in response.json()["error"]["fields"]


def test_chat_rejects_invalid_session_identifier() -> None:
    response = client.post(
        "/api/sales/chat",
        json={"message": "Есть туры?", "session_id": "../private/session"},
    )

    assert response.status_code == 422
    assert "session_id" in response.json()["error"]["fields"]


def test_session_path_uses_same_identifier_contract() -> None:
    response = client.get("/api/sales/session/bad%21session")

    assert response.status_code == 422
    assert "session_id" in response.json()["error"]["fields"]


def test_empty_message_keeps_widget_compatibility() -> None:
    response = client.post("/api/sales/chat", json={"message": "   "})

    assert response.status_code == 200
    assert response.json()["status"] == "sales_empty"
    assert response.json()["session_id"] == "default"


def test_reset_rejects_extra_fields() -> None:
    response = client.post(
        "/api/sales/reset",
        json={"session_id": "security-test", "delete_all": True},
    )

    assert response.status_code == 422
    assert "delete_all" in response.json()["error"]["fields"]
