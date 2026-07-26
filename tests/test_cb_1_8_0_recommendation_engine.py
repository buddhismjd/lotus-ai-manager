from decimal import Decimal

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.catalog.recommendation_engine import analyze_recommendation_query


def _product(index: int, description: str, *, title: str | None = None) -> Product:
    return Product(
        id=f"p-{index}",
        title=title or f"Товар {index}",
        description=description,
        category="Буддийские товары",
        price=Decimal("1000") + index,
        currency="RUB",
        availability_status="В наличии",
        url=f"https://example.test/p-{index}",
    )


def test_gift_query_is_a_commercial_recommendation() -> None:
    intent = analyze_recommendation_query("Подберите подарок")

    assert intent.is_recommendation is True
    assert intent.usage == "gift"
    assert intent.result_limit == 6


def test_gift_recommendation_uses_catalog_evidence_and_is_limited() -> None:
    products = [
        _product(index, "Подходит в подарок")
        for index in range(8)
    ] + [_product(20, "Предмет для коллекции", title="Обычный предмет")]

    result = build_product_collection("Подберите подарок", products)

    assert len(result) == 6
    assert all("Обычный предмет" != item.title for item in result)
    assert all(item.price is not None for item in result)
    assert all(item.availability == "В наличии" for item in result)


def test_home_altar_query_selects_only_supported_products() -> None:
    products = [
        _product(1, "Статуя для домашнего алтаря", title="Для алтаря"),
        _product(2, "Украшение интерьера", title="Для интерьера"),
    ]

    result = build_product_collection("Что подобрать для домашнего алтаря?", products)

    assert [item.title for item in result] == ["Для алтаря"]


def test_explicit_all_aspect_request_is_never_truncated() -> None:
    products = [
        _product(index, "Калачакра, подходит в подарок", title=f"Калачакра {index}")
        for index in range(8)
    ]

    result = build_product_collection("Покажи все товары с Калачакрой", products)

    assert len(result) == 8
