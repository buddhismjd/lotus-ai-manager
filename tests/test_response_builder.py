from backend.services.response_builder import (
    BuiltResponse,
    build_fallback_response,
    build_product_response,
    build_tour_response,
)


def test_product_response_contains_title_summary_and_url() -> None:
    response = build_product_response(
        title="Ваджра",
        summary="Традиционный ритуальный предмет.",
        url="https://example.com/vajra",
    )

    assert isinstance(response, BuiltResponse)
    assert response.kind == "product"
    assert response.title == "Ваджра"
    assert "Ваджра" in response.text
    assert "Традиционный ритуальный предмет." in response.text
    assert "https://example.com/vajra" in response.text


def test_tour_response_contains_title_summary_and_url() -> None:
    response = build_tour_response(
        title="Тибет + Кайлас — 18 дней",
        summary="Паломническое путешествие с акклиматизацией.",
        url="https://example.com/kailash",
    )

    assert response.kind == "tour"
    assert response.title == "Тибет + Кайлас — 18 дней"
    assert "Кайлас" in response.text
    assert "Паломническое путешествие" in response.text
    assert "https://example.com/kailash" in response.text


def test_product_response_without_title_returns_fallback() -> None:
    response = build_product_response(title="   ")

    assert response.kind == "fallback"
    assert "не смог определить название товара" in response.text


def test_tour_response_without_title_returns_fallback() -> None:
    response = build_tour_response(title="")

    assert response.kind == "fallback"
    assert "не смог определить название путешествия" in response.text


def test_fallback_response_is_honest_and_helpful() -> None:
    response = build_fallback_response()

    assert response.kind == "fallback"
    assert "не смог найти достоверную информацию" in response.text
    assert "Попробуйте сформулировать запрос" in response.text
