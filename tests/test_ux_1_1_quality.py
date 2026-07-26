from backend.catalog.collection_builder import CollectionItem, build_product_collection
from backend.catalog.models import Product
from backend.rag.dynamic_query_router import route_query
from backend.sales_assistant.service import SalesAssistant
from backend.services.response_builder import BuiltResponse
from backend.structured_catalog.models import StructuredTour
from backend.tours.collection_builder import build_tour_collection, clean_tour_description


def test_bell_availability_routes_to_products():
    route = route_query("Колокольчик имеется?")
    assert route.intent == "product"
    assert route.reason in {"generic_product_request", "dynamic_product_match", "store_request_without_match"}



def test_bell_query_returns_bell_product_card():
    products = [
        Product(
            id="bell",
            title="Ритуальный колокольчик Ганта",
            url="https://svet-lotosa.tilda.ws/tproduct/2-bell",
        ),
        Product(
            id="tour-souvenir",
            title="Сувенир из Тибета",
            url="https://svet-lotosa.tilda.ws/tproduct/3-souvenir",
        ),
    ]

    items = build_product_collection("Колокольчик имеется?", products)

    assert [item.title for item in items] == ["Ритуальный колокольчик Ганта"]
    assert items[0].image_url


def test_tour_description_removes_tilda_navigation():
    description = """Путешествия
Магазин
Психолог-буддолог
Отзывы
Связаться с нами
Паломническое путешествие к священной горе Кайлас.
Контакты
"""
    assert clean_tour_description(description) == (
        "Паломническое путешествие к священной горе Кайлас."
    )


def test_tour_without_catalog_image_uses_safe_page_media_endpoint(monkeypatch):
    tour = StructuredTour(
        id="tibet",
        title="Тибет + Кайлас — 18 дней",
        url="https://svet-lotosa.tilda.ws/tibet-kailash",
        countries=("Тибет",),
    )
    monkeypatch.setattr(
        "backend.tours.collection_builder.StructuredTourRepository.list_all",
        lambda self: [tour],
    )

    item = build_tour_collection("В Тибет возите?")[0]

    assert item.image_url.startswith("/api/sales/page-image?source=")
    assert "svet-lotosa.tilda.ws" in item.image_url


def test_country_collection_remembers_single_tour_for_follow_up(monkeypatch):
    tour = StructuredTour(
        id="tibet",
        title="Тибет + Кайлас — 18 дней",
        url="https://svet-lotosa.tilda.ws/tibet-kailash",
        description="В программу входят переезды, проживание и сопровождение.",
        countries=("Тибет",),
    )
    assistant = SalesAssistant()
    monkeypatch.setattr(assistant._tours, "list_all", lambda: [tour])
    monkeypatch.setattr(
        "backend.sales_assistant.service.build_tour_collection",
        lambda query: [
            CollectionItem(
                id=tour.id,
                title=tour.title,
                url=tour.url,
                item_type="tour",
            )
        ],
    )
    monkeypatch.setattr(
        "backend.sales_assistant.service.answer_query",
        lambda query: BuiltResponse(kind="fallback", text="Не найдено"),
    )

    first = assistant.reply("В Тибет возите?", session_id="ux-1-1")
    second = assistant.reply("Что входит?", session_id="ux-1-1")

    assert first.kind == "tour_collection"
    assert second.topic == "tour"
    assert second.title == tour.title
    assert tour.title in second.answer
    assert second.kind == "tour"
