from __future__ import annotations

from decimal import Decimal

from backend.catalog.models import Product
from backend.sales_assistant.product_selection import ProductSelectionService
from backend.sales_assistant.selection_page import _render_product_card
from backend.sales_assistant.tone import TONE


def test_greeting_matches_commercial_copy() -> None:
    assert TONE.greeting == (
        "Добрый день! Буду рада помочь! Подобрать путешествие или товар? "
        "Записать на бесплатную консультацию психолога-буддолога?"
    )


def test_product_card_contains_required_catalog_fields() -> None:
    product = Product(
        id="statue-1",
        title="Статуя Зеленой Тары",
        url="https://example.com/statue-1",
        description="Высота: 14 см",
        material="бронза",
        price=Decimal("25000"),
        currency="RUB",
        availability_status="Под заказ",
        image_url="https://example.com/image.jpg",
    )

    html = _render_product_card(product, ProductSelectionService())

    assert "https://example.com/image.jpg" in html
    assert "Статуя Зеленой Тары" in html
    assert "25 000 ₽" in html
    assert "Высота: 14 см" not in html
    assert "Материал: бронза" not in html
    assert "Под заказ" in html
    assert ">Открыть товар<" in html


def test_product_card_uses_honest_unknown_status() -> None:
    product = Product(
        id="statue-2",
        title="Статуя Будды",
        url="https://example.com/statue-2",
        description="Высота: 12 см",
    )

    html = _render_product_card(product, ProductSelectionService())

    assert "Наличие уточняется" in html
    assert "Цена уточняется" in html
    assert "В наличии" not in html
    assert "Под заказ" not in html
