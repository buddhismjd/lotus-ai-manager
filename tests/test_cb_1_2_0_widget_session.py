from __future__ import annotations

from fastapi.testclient import TestClient

import backend.main as main_module
import backend.storage.database as database_module
from backend.sales_assistant.service import SalesAssistant
from backend.sales_assistant.state import DialogueStage
from backend.storage.repositories.session_repository import SessionRepository


def _temporary_database(monkeypatch, tmp_path):
    path = tmp_path / "session-test.db"
    monkeypatch.setattr(database_module, "DATABASE_FILE", path)
    return path


def test_session_repository_persists_state_and_history(monkeypatch, tmp_path) -> None:
    _temporary_database(monkeypatch, tmp_path)
    repository = SessionRepository()

    repository.append_message("visitor-1", "user", "Хочу тур в Непал")
    repository.save_state(
        "visitor-1",
        {"stage": DialogueStage.HANDOFF_NAME.value, "topic": "tour"},
        handoff_status="collecting",
    )
    repository.append_message("visitor-1", "assistant", "Как Вас зовут?")

    session = repository.get_session("visitor-1")
    assert session.handoff_status == "collecting"
    assert session.state["stage"] == DialogueStage.HANDOFF_NAME.value
    assert [message.role for message in session.messages] == ["user", "assistant"]


def test_new_assistant_instance_restores_handoff_stage(monkeypatch, tmp_path) -> None:
    _temporary_database(monkeypatch, tmp_path)
    repository = SessionRepository()
    first = SalesAssistant(repository)
    started = first.reply("Хочу забронировать место в туре", "restore-visitor")
    assert started.dialogue_stage == DialogueStage.HANDOFF_NAME.value

    second = SalesAssistant(SessionRepository())
    continued = second.reply("Анна", "restore-visitor")
    assert continued.dialogue_stage == DialogueStage.HANDOFF_CONTACT_METHOD.value


def test_reset_closes_old_dialog_and_starts_clean_session(monkeypatch, tmp_path) -> None:
    _temporary_database(monkeypatch, tmp_path)
    assistant = SalesAssistant(SessionRepository())
    assistant.reply("Свяжите меня с менеджером", "reset-visitor")
    assistant.reset("reset-visitor")

    restored = SalesAssistant().session("reset-visitor")
    assert restored.status == "reset"

    reply = SalesAssistant(SessionRepository()).reply("Какие есть туры?", "reset-visitor")
    assert reply.dialogue_stage == DialogueStage.DISCOVERY.value


def test_session_api_returns_persisted_messages(monkeypatch, tmp_path) -> None:
    _temporary_database(monkeypatch, tmp_path)
    assistant = SalesAssistant(SessionRepository())
    assistant.reply("Какие есть туры?", "api-session")
    monkeypatch.setattr("backend.sales_assistant.api.get_sales_assistant", lambda: assistant)

    response = TestClient(main_module.app).get("/api/sales/session/api-session")
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "api-session"
    assert [item["role"] for item in payload["messages"]] == ["user", "assistant"]
