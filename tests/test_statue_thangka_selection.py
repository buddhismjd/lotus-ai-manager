from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from backend.catalog.models import Product
from backend.sales_assistant.dialogue import NextActionType
from backend.sales_assistant.product_selection import (
    ProductSelectionService,
    parse_product_selection_request,
)
from backend.sales_assistant.service import SalesAssistant


class FakeProductRepository:
    def __init__(self, products: list[Product]) -> None:
        self._products = products

    def list_all(self) -> list[Product]:
        return list(self._products)


class FakeLeadRepository:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save_artisan_selection(self, **payload):
        self.saved.append(payload)
        return SimpleNamespace(id=501)


def _products() -> list[Product]:
    return [
        Product(
            id="statue-chenrezig-18",
            title="Статуя Ченрезига",
            url="https://example.com/chenrezig-18",
            description="Высота 18 см. Латунь.",
            available=True,
            price=Decimal("100"),
        ),
        Product(
            id="statue-chenrezig-22",
            title="Статуя Ченрезига",
            url="https://example.com/chenrezig-22",
            description="Высота 22 см. Ширина 12 см.",
            available=True,
        ),
        Product(
            id="statue-tara-18",
            title="Статуя Белой Тары",
            url="https://example.com/tara-18",
            description="Высота 18 см.",
            available=True,
        ),
        Product(
            id="thangka-tara",
            title="Тханка Зелёной Тары",
            url="https://example.com/thangka-tara",
            description="Буддийская живопись.",
            available=True,
        ),
    ]


def test_parses_statue_height_range_and_aspect() -> None:
    request = parse_product_selection_request("Есть статуя Ченрезига 15–20 см?")
    assert request is not None
    assert request.category == "statue"
    assert request.aspect == "Ченрезиг"
    assert request.height_min_cm == 15
    assert request.height_max_cm == 20


def test_selection_matches_height_and_aspect_only() -> None:
    request = parse_product_selection_request("Покажите статуи Ченрезига 15-20 см")
    assert request is not None
    result = ProductSelectionService(FakeProductRepository(_products())).select(request)
    assert [item.id for item in result.products] == ["statue-chenrezig-18"]


def test_width_does_not_count_as_requested_height() -> None:
    request = parse_product_selection_request("Нужна статуя Ченрезига 12 см")
    assert request is not None
    result = ProductSelectionService(FakeProductRepository(_products())).select(request)
    assert result.products == ()


def test_thangka_request_stays_in_thangka_category() -> None:
    request = parse_product_selection_request("Покажите тханки Зелёной Тары")
    assert request is not None
    result = ProductSelectionService(FakeProductRepository(_products())).select(request)
    assert [item.id for item in result.products] == ["thangka-tara"]


def test_selection_reply_offers_category_and_artisan_buttons() -> None:
    assistant = SalesAssistant()
    assistant._product_selection = ProductSelectionService(FakeProductRepository(_products()))
    reply = assistant.reply("Есть статуя Ченрезига 15-20 см?", "selection")

    assert "точную подборку" in reply.answer.lower()
    assert "1 подходящих" in reply.answer
    urls = [item.url for item in reply.suggestions if item.action == NextActionType.OPEN_URL]
    assert len(urls) == 1
    assert urls[0] is not None
    assert urls[0].startswith("/api/sales/product-selection?")
    assert "height_min_cm=15" in urls[0]
    assert "height_max_cm=20" in urls[0]
    assert any(item.action == NextActionType.ARTISAN_SELECTION for item in reply.suggestions)


def test_artisan_workflow_collects_social_and_email() -> None:
    assistant = SalesAssistant()
    assistant._product_selection = ProductSelectionService(FakeProductRepository(_products()))
    repository = FakeLeadRepository()
    assistant._leads = repository  # type: ignore[assignment]

    assistant.reply("Есть статуя Ченрезига 15-20 см?", "artisan")
    start = assistant.reply("Хочу персональную подборку от мастеров", "artisan")
    assert start.dialogue_stage == "artisan_social_method"

    social = assistant.reply("Telegram", "artisan")
    assert social.dialogue_stage == "artisan_social_value"

    email_step = assistant.reply("@client_name", "artisan")
    assert email_step.dialogue_stage == "artisan_email"

    completed = assistant.reply("client@example.com", "artisan")
    assert completed.kind == "artisan_saved"
    assert completed.lead_id == 501
    payload = repository.saved[0]
    assert payload["social_channel"] == "telegram"
    assert payload["social_contact"] == "@client_name"
    assert payload["email"] == "client@example.com"
    assert payload["selection_category"] == "statue"
    assert payload["selection_aspect"] == "Ченрезиг"
    assert payload["requested_height_min_cm"] == 15
    assert payload["requested_height_max_cm"] == 20


def test_selection_reply_returns_every_matching_product_as_complete_card() -> None:
    products = [
        Product(
            id="tara-1",
            title="Статуя Белой Тары 18 см",
            url="https://example.com/tara-1",
            description="Высота 18 см. Латунь.",
            available=True,
            availability_status="В наличии",
            material="Латунь",
            height_cm=18,
            image_url="https://example.com/tara-1.jpg",
        ),
        Product(
            id="tara-2",
            title="Статуя Белой Тары 22 см",
            url="https://example.com/tara-2",
            description="Высота 22 см. Бронза.",
            available=False,
            availability_status="Под заказ",
            material="Бронза",
            height_cm=22,
            image_url="https://example.com/tara-2.jpg",
        ),
    ]
    assistant = SalesAssistant()
    assistant._product_selection = ProductSelectionService(FakeProductRepository(products))

    reply = assistant.reply("Покажите статуи Белой Тары", "all-tara-products")

    assert reply.kind == "product_selection"
    assert len(reply.items) == 2
    assert [item["id"] for item in reply.items] == ["tara-1", "tara-2"]
    assert all(item["image_url"] for item in reply.items)
    assert "material" not in reply.items[0]
    assert "size" not in reply.items[0]
    assert "description" not in reply.items[0]
    assert reply.items[0]["price"] == "Цена уточняется"
    assert reply.items[0]["availability"] == "В наличии"
    assert reply.items[0]["button_label"] == "Открыть товар"
    assert reply.items[1]["availability"] == "Под заказ"
