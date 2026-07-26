from decimal import Decimal

from backend.catalog.collection_builder import CollectionItem
from backend.catalog.commercial_cards import commercial_card


def test_product_card_contract_is_minimal_and_complete() -> None:
    item = CollectionItem(
        id="p1",
        title="Статуя Белой Тары",
        url="https://example.test/p1",
        image_url="https://example.test/p1.jpg",
        price="25 000 ₽",
        availability="В наличии",
        material="Латунь",
        size="18 см",
        description="Полное описание товара",
        item_type="product",
    )

    card = commercial_card(item)

    assert card == {
        "id": "p1",
        "item_type": "product",
        "title": "Статуя Белой Тары",
        "image_url": "https://example.test/p1.jpg",
        "price": "25 000 ₽",
        "availability": "В наличии",
        "url": "https://example.test/p1",
        "button_label": "Открыть товар",
        "status": "published",
    }
    assert "description" not in card
    assert "material" not in card
    assert "size" not in card


def test_tour_card_contract_requires_dates_and_price() -> None:
    card = commercial_card(CollectionItem(
        id="t1",
        title="Непал — Лапчи",
        url="https://example.test/t1",
        image_url="https://example.test/t1.jpg",
        price="1 450 $",
        availability="4–11 ноября 2026",
        description="Программа тура",
        item_type="tour",
        button_label="Неверная подпись",
    ))

    assert card["price"] == "1 450 $"
    assert card["availability"] == "4–11 ноября 2026"
    assert card["button_label"] == "Открыть тур"
    assert "description" not in card


def test_missing_commercial_values_use_honest_labels() -> None:
    product = commercial_card(CollectionItem(id="p", title="Товар", url="https://x", item_type="product"))
    tour = commercial_card(CollectionItem(id="t", title="Тур", url="https://y", item_type="tour"))

    assert product["price"] == "Цена уточняется"
    assert product["availability"] == "Наличие уточняется"
    assert tour["price"] == "Цена уточняется"
    assert tour["availability"] == "Даты уточняются"
