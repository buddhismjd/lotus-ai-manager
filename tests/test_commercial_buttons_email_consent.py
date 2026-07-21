from __future__ import annotations

from types import SimpleNamespace

from backend.sales_assistant.dialogue import NextActionType
from backend.sales_assistant.service import SalesAssistant, SalesReply
from backend.sales_assistant.state import DialogueStage


class FakeLeadRepository:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save(self, **payload):
        self.saved.append(payload)
        return SimpleNamespace(id=91)


def _url_suggestions(reply):
    return [item for item in reply.suggestions if item.action == NextActionType.OPEN_URL]


def test_tour_url_is_exposed_as_button() -> None:
    assistant = SalesAssistant()
    reply = assistant._with_dialogue(
        SalesReply(
            answer="Карточка путешествия без открытой ссылки.",
            kind="tour",
            topic="tour",
            title="Тибет + Кайлас",
            url="https://example.com/kailas",
        ),
        "tour_details",
    )

    links = _url_suggestions(reply)
    assert "https://" not in reply.answer
    assert len(links) == 1
    assert links[0].url == "https://example.com/kailas"
    assert links[0].message == ""


def test_product_url_is_exposed_as_button() -> None:
    assistant = SalesAssistant()
    reply = assistant._with_dialogue(
        SalesReply(
            answer="Карточка товара без открытой ссылки.",
            kind="product",
            topic="product",
            title="Ваджра",
            url="https://example.com/vajra",
        ),
        "product_search",
    )

    links = _url_suggestions(reply)
    assert len(links) == 1
    assert links[0].label == "Открыть товар"


def test_tour_email_consent_is_thematic_and_saved() -> None:
    assistant = SalesAssistant()
    repository = FakeLeadRepository()
    assistant._leads = repository  # type: ignore[assignment]
    state = assistant._states.get("email-tour-topic")
    state.topic = "tour"
    state.active_title = "Тибет + Кайлас"
    state.last_query = "Расскажите про Кайлас"

    request = assistant.reply(
        "Хочу получать информацию о новых турах на email",
        "email-tour-topic",
    )
    assert request.dialogue_stage == DialogueStage.EMAIL_VALUE.value
    assert "новых турах" in request.answer.casefold()

    completed = assistant.reply("guest@example.com", "email-tour-topic")
    assert completed.kind == "email_saved"
    assert "новых путешествиях" in completed.answer.casefold()
    comment = repository.saved[0]["comment"]
    assert "subscription_topic=new_tours" in comment
    assert "interest_category=tour" in comment
    assert "Тибет + Кайлас" in comment


def test_product_email_consent_is_thematic_and_saved() -> None:
    assistant = SalesAssistant()
    repository = FakeLeadRepository()
    assistant._leads = repository  # type: ignore[assignment]
    state = assistant._states.get("email-product-topic")
    state.topic = "product"
    state.active_title = "Ваджра"

    request = assistant.reply(
        "Хочу получать информацию о новых товарах на email",
        "email-product-topic",
    )
    assert "новых товарах" in request.answer.casefold()
    assistant.reply("buyer@example.com", "email-product-topic")
    assert "subscription_topic=new_products" in repository.saved[0]["comment"]


def test_psychologist_email_is_service_information_not_news() -> None:
    assistant = SalesAssistant()
    repository = FakeLeadRepository()
    assistant._leads = repository  # type: ignore[assignment]
    state = assistant._states.get("email-psychologist-topic")
    state.topic = "psychologist"
    state.active_title = "Консультация психолога-буддолога"

    request = assistant.reply(
        "Отправьте информацию о консультации на email",
        "email-psychologist-topic",
    )
    lowered = request.answer.casefold()
    assert "консультац" in lowered
    assert "новых турах" not in lowered
    assert "новых товарах" not in lowered

    assistant.reply("client@example.com", "email-psychologist-topic")
    comment = repository.saved[0]["comment"]
    assert "subscription_topic=psychologist_service_information" in comment
