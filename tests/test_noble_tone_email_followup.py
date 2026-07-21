from __future__ import annotations

from types import SimpleNamespace

from backend.sales_assistant.dialogue import NextActionType, SalesDialogueManager
from backend.sales_assistant.service import SalesAssistant
from backend.sales_assistant.state import DialogueStage
from backend.sales_assistant.tone import TONE, warm_missing_price


class FakeLeadRepository:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save(self, **payload):
        self.saved.append(payload)
        return SimpleNamespace(id=77)


def test_noble_tone_avoids_dry_or_misleading_price_language() -> None:
    text = warm_missing_price("Тибет + Кайлас")

    assert "не стану вводить Вас в заблуждение" in text
    assert "Я не буду придумывать" not in text
    assert "пока не указана" in text


def test_dialogue_offers_email_with_clear_purpose() -> None:
    plan = SalesDialogueManager().plan(
        strategy="tour_details",
        topic="tour",
        kind="tour",
        title="Тибет + Кайлас",
    )

    email = [item for item in plan.suggestions if item.action == NextActionType.EMAIL_FOLLOWUP]

    assert len(email) == 1
    assert "email" in email[0].label.casefold()
    assert "информац" in email[0].message.casefold()


def test_email_followup_saves_interest_and_context() -> None:
    assistant = SalesAssistant()
    repository = FakeLeadRepository()
    assistant._leads = repository  # type: ignore[assignment]
    state = assistant._states.get("email-session")
    state.topic = "tour"
    state.active_title = "Тибет + Кайлас — 18 дней"
    state.last_query = "Расскажите подробнее про Кайлас"

    start = assistant.reply("Отправьте, пожалуйста, информацию на email", "email-session")

    assert start.kind == "email_capture"
    assert start.dialogue_stage == DialogueStage.EMAIL_VALUE.value
    assert "только для отправки информации" in start.answer

    invalid = assistant.reply("ошибка", "email-session")
    assert invalid.kind == "email_capture"
    assert "неточность" in invalid.answer
    assert repository.saved == []

    completed = assistant.reply("guest@example.com", "email-session")

    assert completed.kind == "email_saved"
    assert completed.lead_id == 77
    assert completed.next_action == NextActionType.EMAIL_SAVED
    assert repository.saved[0]["contact_method"] == "email"
    assert repository.saved[0]["contact_value"] == "guest@example.com"
    assert repository.saved[0]["interest"] == "Тибет + Кайлас — 18 дней"
    assert "Расскажите подробнее про Кайлас" in repository.saved[0]["comment"]


def test_tone_policy_greeting_is_warm_and_domain_bounded() -> None:
    assert TONE.greeting.startswith("Добрый день! Буду рада помочь!")
    assert "путешествие" in TONE.greeting
    assert "товар" in TONE.greeting
    assert "психолога-буддолога" in TONE.greeting
