from __future__ import annotations

from pathlib import Path

import backend.storage.database as database
from backend.sales_assistant.dialogue import NextActionType
from backend.sales_assistant.service import SalesAssistant


def _temporary_database(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DATABASE_FILE", tmp_path / "lead-test.db")
    database.initialize_database()


def test_lead_capture_intercepts_search_and_preserves_tour(tmp_path, monkeypatch) -> None:
    _temporary_database(tmp_path, monkeypatch)
    assistant = SalesAssistant()
    state = assistant._states.get("lead-tour")
    state.topic = "tour"
    state.active_title = "Тибет + Кайлас — 18 дней"

    start = assistant.reply("Хочу оставить контакт для связи", "lead-tour")
    assert start.kind == "lead_capture"
    assert start.next_action == NextActionType.ASK_NAME
    assert "Как я могу" in start.answer

    method = assistant.reply("Евгения", "lead-tour")
    assert method.next_action == NextActionType.ASK_CONTACT_METHOD

    value = assistant.reply("Telegram", "lead-tour")
    assert value.next_action == NextActionType.ASK_CONTACT_VALUE

    completed = assistant.reply("@evgenia_test", "lead-tour")
    assert completed.kind == "lead_saved"
    assert completed.lead_id is not None
    assert "Кайлас" in completed.answer


def test_invalid_contact_does_not_complete_lead(tmp_path, monkeypatch) -> None:
    _temporary_database(tmp_path, monkeypatch)
    assistant = SalesAssistant()
    assistant.reply("Хочу оставить заявку", "invalid")
    assistant.reply("Анна", "invalid")
    assistant.reply("Телефон", "invalid")

    reply = assistant.reply("123", "invalid")
    assert reply.kind == "lead_capture"
    assert reply.next_action == NextActionType.ASK_CONTACT_VALUE
    assert reply.lead_id is None


def test_lead_capture_can_be_cancelled(tmp_path, monkeypatch) -> None:
    _temporary_database(tmp_path, monkeypatch)
    assistant = SalesAssistant()
    assistant.reply("Хочу оставить заявку", "cancel")
    reply = assistant.reply("Отмена", "cancel")
    assert reply.kind == "lead_cancelled"
    assert reply.dialogue_stage == "discovery"

def test_lead_capture_does_not_route_to_random_tour(tmp_path, monkeypatch) -> None:
    _temporary_database(tmp_path, monkeypatch)
    assistant = SalesAssistant()
    state = assistant._states.get("no-random")
    state.topic = "tour"
    state.active_title = "Тибет + Кайлас — 18 дней"
    assistant.reply("Хочу оставить контакт для связи", "no-random")
    reply = assistant.reply("Мария", "no-random")
    assert "Занскар" not in reply.answer
    assert reply.kind == "lead_capture"
