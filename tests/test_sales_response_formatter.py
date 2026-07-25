from __future__ import annotations

from decimal import Decimal

import backend.sales_assistant.formatter as formatter_module
from backend.catalog.models import Product, Tour
from backend.services.response_builder import BuiltResponse
from backend.sales_assistant.formatter import format_sales_response


class _TourRepository:
    def list_all(self):
        return [
            Tour(
                id="tour-kailash",
                title="Тибет + Кайлас — 18 дней",
                url="https://example.com/kailash",
                description=(
                    "Путешествия\nМагазин\nПсихолог-буддолог\nОтзывы\n"
                    "Связаться с нами\nТибет + Кайлас — 18 дней\n"
                    "22 сентября – 9 октября\nОтправить заявку\n"
                    "Паломническое путешествие по главным местам Тибета.\n"
                    "План маршрута\n🗓️ День 0\nПрибытие в Чэнду\n"
                ),
            )
        ]


class _ProductRepository:
    def list_all(self):
        return [
            Product(
                id="vajra",
                title="Ваджра пятиконечная",
                url="https://example.com/vajra",
                description="Магазин\nВаджра пятиконечная\nРитуальный предмет для практики.",
                price=Decimal("5400"),
                material="бронза",
            )
        ]


def test_tour_formatter_removes_page_navigation_and_route(monkeypatch) -> None:
    monkeypatch.setattr(formatter_module, "TourRepository", _TourRepository)
    response = format_sales_response(
        BuiltResponse(
            kind="tour",
            text="raw",
            title="Тибет + Кайлас — 18 дней",
            url="https://example.com/kailash",
        )
    )
    assert "Путешествия\nМагазин" not in response.text
    assert "День 0" not in response.text
    assert "22 сентября – 9 октября" in response.text
    assert "⏱ 18 дней" not in response.text
    assert "**" not in response.text


def test_product_formatter_uses_structured_fields(monkeypatch) -> None:
    monkeypatch.setattr(formatter_module, "ProductRepository", _ProductRepository)
    response = format_sales_response(
        BuiltResponse(
            kind="product",
            text="raw",
            title="Ваджра пятиконечная",
            url="https://example.com/vajra",
        )
    )
    assert "5 400 ₽" in response.text
    assert "Материал: бронза" in response.text
    assert "Магазин\n" not in response.text


def test_fallback_only_removes_raw_markdown() -> None:
    response = format_sales_response(
        BuiltResponse(kind="fallback", text="**Нет данных**")
    )
    assert response.text == "Нет данных"
