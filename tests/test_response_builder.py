from backend.services.response_builder import (
    build_product_response,
    build_tour_response,
    build_fallback_response,
)


def test_product():
    text = build_product_response(
        "Ваджра",
        "Традиционный ритуальный предмет.",
        "https://example.com",
    )

    assert "Ваджра" in text


def test_tour():
    text = build_tour_response(
        "Кайлас",
        "Паломничество в Тибет.",
        "https://example.com",
    )

    assert "Кайлас" in text


def test_fallback():
    text = build_fallback_response()

    assert "не смог найти" in text