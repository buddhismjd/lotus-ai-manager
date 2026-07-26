from __future__ import annotations

from dataclasses import dataclass

from backend.sales_assistant.handoff import HandoffPriority, HandoffReason
from backend.sales_assistant.handoff_engine import HandoffEngine
from backend.sales_assistant.service import SalesAssistant
from backend.sales_assistant.state import DialogueStage


@dataclass(frozen=True)
class _Saved:
    id: int = 501


class _LeadRepositorySpy:
    def __init__(self) -> None:
        self.payload: dict | None = None

    def save_handoff(self, **kwargs):
        self.payload = kwargs
        return _Saved()


def test_engine_detects_booking_as_high_priority_handoff() -> None:
    decision = HandoffEngine().evaluate("Можно забронировать место в туре в Непал?")

    assert decision.required is True
    assert decision.reason == HandoffReason.BOOKING_REQUEST
    assert decision.priority == HandoffPriority.HIGH


def test_engine_does_not_transfer_an_information_question() -> None:
    decision = HandoffEngine().evaluate("Какая программа тура в Непал?")

    assert decision.required is False
    assert decision.reason is None


def test_booking_flow_collects_required_contacts_and_saves_context() -> None:
    assistant = SalesAssistant()
    repository = _LeadRepositorySpy()
    assistant._leads = repository  # type: ignore[assignment]
    session_id = "cb-1.1.0-test"

    started = assistant.reply("Хочу забронировать место в туре в Непал", session_id)
    assert started.kind == "handoff_capture"
    assert started.dialogue_stage == DialogueStage.HANDOFF_NAME.value
    assert started.handoff_reason == HandoffReason.BOOKING_REQUEST.value

    name = assistant.reply("Анна", session_id)
    assert name.dialogue_stage == DialogueStage.HANDOFF_CONTACT_METHOD.value

    channel = assistant.reply("Telegram", session_id)
    assert channel.dialogue_stage == DialogueStage.HANDOFF_CONTACT_VALUE.value

    contact = assistant.reply("@anna_lotus", session_id)
    assert contact.dialogue_stage == DialogueStage.HANDOFF_EMAIL.value

    completed = assistant.reply("anna@example.com", session_id)
    assert completed.kind == "handoff_saved"
    assert completed.lead_id == 501
    assert completed.dialogue_stage == DialogueStage.HANDOFF_COMPLETE.value
    assert repository.payload is not None
    assert repository.payload["session_id"] == session_id
    assert repository.payload["reason"] == HandoffReason.BOOKING_REQUEST
    assert "запрос на бронирование" in repository.payload["manager_summary"]


def test_handoff_can_be_cancelled_without_saving() -> None:
    assistant = SalesAssistant()
    repository = _LeadRepositorySpy()
    assistant._leads = repository  # type: ignore[assignment]

    assistant.reply("Свяжите меня с менеджером", "cancel-session")
    cancelled = assistant.reply("Отмена", "cancel-session")

    assert cancelled.kind == "handoff_cancelled"
    assert cancelled.dialogue_stage == DialogueStage.DISCOVERY.value
    assert repository.payload is None
