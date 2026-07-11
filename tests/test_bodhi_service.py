from types import SimpleNamespace

import backend.services.bodhi_service as bodhi_service
from backend.rag.dynamic_query_router import Route


def test_answer_query_builds_product_response(monkeypatch) -> None:
    monkeypatch.setattr(
        bodhi_service,
        "route_query",
        lambda _: Route(
            intent="product",
            confidence=0.99,
            reason="test",
            matched_title="Ваджра",
            matched_url="https://example.com/vajra",
        ),
    )
    monkeypatch.setattr(
        bodhi_service.ProductRepository,
        "list_all",
        lambda self: [
            SimpleNamespace(
                title="Ваджра",
                description="Традиционный ритуальный предмет.",
                url="https://example.com/vajra",
            )
        ],
    )

    response = bodhi_service.answer_query("У вас есть ваджра?")

    assert response.kind == "product"
    assert "Ваджра" in response.text
    assert "Традиционный ритуальный предмет." in response.text


def test_answer_query_builds_tour_response(monkeypatch) -> None:
    monkeypatch.setattr(
        bodhi_service,
        "route_query",
        lambda _: Route(
            intent="tour",
            confidence=0.99,
            reason="test",
            matched_title="Тибет + Кайлас — 18 дней",
            matched_url="https://example.com/kailash",
        ),
    )
    monkeypatch.setattr(
        bodhi_service.TourRepository,
        "list_all",
        lambda self: [
            SimpleNamespace(
                title="Тибет + Кайлас — 18 дней",
                description="Паломническое путешествие с акклиматизацией.",
                url="https://example.com/kailash",
            )
        ],
    )

    response = bodhi_service.answer_query("Хочу на Кайлас")

    assert response.kind == "tour"
    assert "Кайлас" in response.text
    assert "Паломническое путешествие" in response.text


def test_answer_query_returns_honest_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        bodhi_service,
        "route_query",
        lambda _: Route(
            intent="unknown",
            confidence=0.25,
            reason="test",
        ),
    )

    response = bodhi_service.answer_query("Неизвестный вопрос")

    assert response.kind == "fallback"
    assert "не смог найти достоверную информацию" in response.text
