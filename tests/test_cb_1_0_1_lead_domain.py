from __future__ import annotations

import pytest

from backend.sales_assistant.handoff import (
    HandoffDecision,
    HandoffPriority,
    HandoffReason,
)
from backend.sales_assistant.lead_summary import LeadSummaryBuilder, LeadSummaryContext
from backend.sales_assistant.lead_validator import (
    LeadContactChannel,
    LeadValidationCode,
    LeadValidator,
)


def test_handoff_decision_requires_reason() -> None:
    with pytest.raises(ValueError):
        HandoffDecision(required=True)


def test_handoff_decision_factory_preserves_structured_reason() -> None:
    decision = HandoffDecision.transfer(
        HandoffReason.AVAILABILITY_REQUEST,
        priority=HandoffPriority.HIGH,
    )

    assert decision.required is True
    assert decision.reason == HandoffReason.AVAILABILITY_REQUEST
    assert decision.priority == HandoffPriority.HIGH


def test_lead_validator_accepts_telegram_and_mandatory_email() -> None:
    result = LeadValidator().validate(
        name="  Анна  ",
        contact_channel="телеграм",
        contact_value="anna_lotus",
        email=" ANNA@EXAMPLE.COM ",
    )

    assert result.is_valid is True
    assert result.data is not None
    assert result.data.name == "Анна"
    assert result.data.contact_channel == LeadContactChannel.TELEGRAM
    assert result.data.contact_value == "@anna_lotus"
    assert result.data.email == "anna@example.com"


def test_lead_validator_accepts_max_contact() -> None:
    result = LeadValidator().validate(
        name="Ирина",
        contact_channel="MAX",
        contact_value="max-id-123",
        email="irina@example.com",
    )

    assert result.is_valid is True
    assert result.data is not None
    assert result.data.contact_channel == LeadContactChannel.MAX


def test_lead_validator_rejects_missing_email() -> None:
    result = LeadValidator().validate(
        name="Ирина",
        contact_channel="telegram",
        contact_value="@irina_lotus",
        email="",
    )

    assert result.is_valid is False
    assert LeadValidationCode.EMAIL_REQUIRED in {error.code for error in result.errors}


def test_lead_validator_rejects_unsupported_channel() -> None:
    result = LeadValidator().validate(
        name="Ирина",
        contact_channel="whatsapp",
        contact_value="+37100000000",
        email="irina@example.com",
    )

    assert result.is_valid is False
    assert LeadValidationCode.CONTACT_CHANNEL_UNSUPPORTED in {
        error.code for error in result.errors
    }


def test_summary_is_deterministic_and_manager_friendly() -> None:
    summary = LeadSummaryBuilder().build(
        LeadSummaryContext(
            interest_title="Тур в Лапчи",
            last_question="Есть ли свободные места?",
            handoff_reason=HandoffReason.AVAILABILITY_REQUEST,
            topic="tour",
        )
    )

    assert summary == (
        "Клиент интересуется: Тур в Лапчи. "
        "Последний вопрос: Есть ли свободные места. "
        "Причина передачи: уточнение наличия мест или товара."
    )
