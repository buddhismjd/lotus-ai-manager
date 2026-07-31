from pathlib import Path

from backend.catalog.collection_builder import CollectionItem
from backend.catalog.commercial_cards import commercial_card
from backend.config import BASE_DIR


WIDGET_DIR = Path(BASE_DIR) / "widget"


def test_rich_card_v2_exposes_versioned_action_contract() -> None:
    card = commercial_card(CollectionItem(
        id="service-1",
        title="Консультация психолога-буддолога",
        url="https://example.test/service",
        price="5 000 ₽",
        availability="По записи",
        item_type="service",
    ))

    assert card["card_version"] == "2.0"
    assert card["item_type"] == "service"
    assert card["actions"] == ({
        "type": "link",
        "label": "Открыть услугу",
        "url": "https://example.test/service",
    },)


def test_rich_card_v2_widget_has_one_unified_renderer() -> None:
    js = (WIDGET_DIR / "widget.js").read_text(encoding="utf-8")
    css = (WIDGET_DIR / "widget.css").read_text(encoding="utf-8")

    assert "const appendCard" in js
    assert "normalizedCardActions" in js
    assert "cardMeta" in js
    assert "groupItems.forEach((item) => appendCard(item, collection))" in js
    assert "ai-bodhi__card-badge" in css
    assert "ai-bodhi__card-actions" in css
    assert "ai-bodhi__card-meta-label" in css
    assert "item.description" not in js
