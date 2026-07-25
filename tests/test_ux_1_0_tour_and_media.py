from backend.catalog.collection_builder import build_product_collection
from backend.catalog.models import Product
from backend.structured_catalog.models import StructuredTour
from backend.tours.collection_builder import build_tour_collection


def test_tibet_country_is_inferred_from_legacy_tour_title(monkeypatch):
    tour = StructuredTour(id="tibet", title="Тибет + Кайлас — 18 дней", url="https://example.test/tibet")
    monkeypatch.setattr("backend.tours.collection_builder.StructuredTourRepository.list_all", lambda self: [tour])
    items = build_tour_collection("В Тибет возите?")
    assert [item.title for item in items] == ["Тибет + Кайлас — 18 дней"]


def test_product_without_catalog_image_uses_safe_media_endpoint():
    product = Product(id="vajra", title="Ваджра", url="https://svet-lotosa.tilda.ws/tproduct/1-vadzhra")
    item = build_product_collection("Есть ли ваджра?", [product])[0]
    assert item.image_url.startswith("/api/sales/product-image?source=")
    assert "svet-lotosa.tilda.ws" in item.image_url


def test_india_country_collection_returns_every_matching_tour(monkeypatch):
    tours = [
        StructuredTour(id="kullu", title="По стопам Рериха — Долина Куллу", url="https://example.test/kullu"),
        StructuredTour(id="ladakh", title="Ладакх, королевство Занскар", url="https://example.test/ladakh"),
        StructuredTour(id="markha", title="Долина Маркха и Канг Ятсе 2", url="https://example.test/markha"),
        StructuredTour(id="tibet", title="Тибет + Кайлас", url="https://example.test/tibet"),
    ]
    monkeypatch.setattr(
        "backend.tours.collection_builder.StructuredTourRepository.list_all",
        lambda self: tours,
    )

    items = build_tour_collection("Что по Индии?")

    assert {item.id for item in items} == {"kullu", "ladakh", "markha"}
    assert len(items) == 3
    assert all(item.material == "Индия" for item in items)


def test_country_collection_does_not_stop_after_first_match(monkeypatch):
    tours = [
        StructuredTour(
            id=f"india-{index}",
            title=f"Ладакх маршрут {index}",
            url=f"https://example.test/india-{index}",
        )
        for index in range(1, 7)
    ]
    monkeypatch.setattr(
        "backend.tours.collection_builder.StructuredTourRepository.list_all",
        lambda self: tours,
    )

    items = build_tour_collection("Покажи туры в Индию")

    assert len(items) == 6
