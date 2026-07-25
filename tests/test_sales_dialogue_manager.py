from __future__ import annotations

from fastapi.testclient import TestClient

import backend.main as main_module
from backend.sales_assistant.dialogue import NextActionType, SalesDialogueManager
from backend.sales_assistant.service import SalesAssistant
import backend.sales_assistant.service as service_module
from backend.services.response_builder import BuiltResponse
from backend.structured_catalog.models import StructuredTour


def test_tour_list_offers_typed_next_actions() -> None:
    reply = SalesAssistant().reply("Какие есть туры в сентябре?", "sdm-list")

    assert reply.next_action == NextActionType.ASK_PREFERENCE
    labels = {suggestion.label for suggestion in reply.suggestions}
    assert "Помочь с выбором" in labels
    assert "Рассказать о Кайласе" not in labels


def test_missing_tour_price_is_honest_and_requests_manager(monkeypatch) -> None:
    route = type(
        "Route",
        (),
        {
            "intent": "tour",
            "matched_title": "Тибет + Кайлас — 18 дней",
            "matched_url": "https://example.test/kailash",
        },
    )()
    tour = StructuredTour(
        id="kailash",
        title="Тибет + Кайлас — 18 дней",
        url="https://example.test/kailash",
        price=None,
    )
    monkeypatch.setattr(service_module, "route_query", lambda _: route)
    monkeypatch.setattr(
        SalesAssistant,
        "_find_structured_tour",
        staticmethod(lambda _title, _url: tour),
    )

    reply = SalesAssistant().reply("Сколько стоит тур на Кайлас?", "sdm-price")

    assert reply.kind == "tour_price"
    assert "не указана" in reply.answer
    assert "не буду придумывать" in reply.answer
    assert reply.needs_manager
    assert reply.next_action == NextActionType.LEAVE_CONTACT


def test_tour_details_do_not_offer_program_or_price(monkeypatch) -> None:
    route = type(
        "Route",
        (),
        {"intent": "tour", "matched_title": None, "matched_url": None},
    )()
    monkeypatch.setattr(service_module, "route_query", lambda _: route)
    monkeypatch.setattr(
        service_module,
        "answer_query",
        lambda _: BuiltResponse(
            kind="tour",
            text="Паломнический тур.",
            title="Тибет + Кайлас — 18 дней",
            url="https://example.test/kailash",
        ),
    )

    reply = SalesAssistant().reply("Расскажите про Кайлас", "sdm-details")

    labels = {suggestion.label for suggestion in reply.suggestions}
    assert "Оставить заявку" in labels
    assert "Программа" not in labels
    assert "Стоимость" not in labels


def test_psychologist_dialogue_offers_booking() -> None:
    reply = SalesAssistant().reply(
        "Хочу консультацию буддолога-психолога",
        "sdm-psychologist",
    )

    assert reply.next_action == NextActionType.BOOK_CONSULTATION
    assert any(item.label == "Записаться" for item in reply.suggestions)


def test_api_serializes_next_action_and_suggestions() -> None:
    client = TestClient(main_module.app)
    response = client.post(
        "/api/sales/chat",
        json={"message": "Сколько стоит тур на Кайлас?", "session_id": "sdm-api"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["next_action"] == "leave_contact"
    assert payload["needs_manager"] is True
    assert payload["suggestions"]
    assert {"action", "label", "message"} <= set(payload["suggestions"][0])


def test_fallback_has_manager_action() -> None:
    plan = SalesDialogueManager().plan(
        strategy="fallback",
        topic="unknown",
        kind="fallback",
        needs_manager=True,
    )

    assert plan.next_action == NextActionType.TRANSFER_MANAGER
    assert plan.requires_manager
