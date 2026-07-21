from decimal import Decimal

from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.tours.collection_builder import detect_country


def test_product_collection_returns_all_matching_aspect_products(monkeypatch):
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    products = [
        Product(
            id="1",
            title="Статуя Белой Тары 29 см",
            url="https://example.test/tproduct/1",
            description="Изображение: https://img.test/white-tara-29.jpg",
            price=Decimal("12000"),
        ),
        Product(
            id="2",
            title="Статуя Белой Тары 42 см",
            url="https://example.test/tproduct/2",
            description="Изображение: https://img.test/white-tara-42.jpg",
            price=Decimal("24000"),
        ),
        Product(
            id="3",
            title="Статуя Зелёной Тары 30 см",
            url="https://example.test/tproduct/3",
        ),
    ]

    items = build_product_collection("Покажи все статуи Белой Тары", products)

    assert [item.title for item in items] == [
        "Статуя Белой Тары 29 см",
        "Статуя Белой Тары 42 см",
    ]
    assert items[0].image_url == "https://img.test/white-tara-29.jpg"
    assert items[0].price == "12 000 ₽"


def test_tour_country_detection_is_strict():
    assert detect_country("Есть поездка в Непал?") == "Непал"
    assert detect_country("Есть поездка на Алтай?") == "Россия"
    assert detect_country("Какие путешествия у вас есть?") is None


def test_product_collection_prefers_structured_image_and_availability(monkeypatch):
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    product = Product(
        id="product-1",
        title="Статуя Белой Тары",
        url="https://example.test/tproduct/1",
        image_url="https://img.test/catalog-white-tara.jpg",
        availability_status="Под заказ",
    )

    items = build_product_collection("Белая Тара", [product])

    assert len(items) == 1
    assert items[0].image_url == "https://img.test/catalog-white-tara.jpg"
    assert items[0].availability == "Под заказ"
