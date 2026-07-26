from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.catalog.product_intelligence import analyze_product


def _product(product_id: str, title: str, category: str) -> Product:
    return Product(
        id=product_id,
        title=title,
        category=category,
        url=f"https://example.test/tproduct/{product_id}",
        image_url=f"https://img.test/{product_id}.jpg",
    )


def test_kalachakra_is_recognized_as_an_aspect() -> None:
    intelligence = analyze_product(title="Защитная наклейка Калачакра")

    assert "Калачакра" in intelligence.entities


def test_broad_aspect_query_returns_products_across_categories(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    products = [
        _product("statue", "Статуя Калачакры", "Статуи"),
        _product("thangka", "Тханка Калачакры", "Тханки"),
        _product("sticker", "Защитная наклейка Калачакра", "Наклейки"),
        _product("tara", "Статуя Белой Тары", "Статуи"),
    ]

    items = build_product_collection("Покажи что-нибудь с Калачакрой", products)

    assert {item.id for item in items} == {"statue", "thangka", "sticker"}
    assert {item.category for item in items} == {"Статуи", "Тханки", "Наклейки"}
    assert all(item.image_url for item in items)


def test_category_and_aspect_query_applies_both_facets(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.catalog.collection_builder.get_product_profile",
        lambda _product_id: None,
    )
    products = [
        _product("statue", "Статуя Калачакры", "Статуи"),
        _product("thangka", "Тханка Калачакры", "Тханки"),
        _product("sticker", "Защитная наклейка Калачакра", "Наклейки"),
    ]

    items = build_product_collection("Покажи тханки Калачакры", products)

    assert [item.id for item in items] == ["thangka"]
