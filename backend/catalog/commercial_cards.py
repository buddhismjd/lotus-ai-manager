from __future__ import annotations

from typing import Any

from backend.catalog.collection_builder import CollectionItem


_UNKNOWN_PRICE = "Цена уточняется"
_UNKNOWN_PRODUCT_STATUS = "Наличие уточняется"
_UNKNOWN_TOUR_DATES = "Даты уточняются"


def commercial_card(item: CollectionItem) -> dict[str, Any]:
    """Return the deterministic public card contract for the chat widget.

    The chat is navigation, not a replacement for the commercial page.  It
    therefore exposes only the fields required to identify an offer and open
    its canonical site page.  Catalog descriptions, material, dimensions and
    lead-capture actions intentionally stay outside this contract.
    """
    item_type = item.item_type if item.item_type in {"product", "tour", "service"} else "product"
    availability = item.availability
    if item_type == "product" and not availability:
        availability = _UNKNOWN_PRODUCT_STATUS
    elif item_type == "tour" and not availability:
        availability = _UNKNOWN_TOUR_DATES

    button_label = {
        "product": "Открыть товар",
        "tour": "Открыть тур",
        "service": "Открыть услугу",
    }[item_type]

    actions = (
        {
            "type": "link",
            "label": button_label,
            "url": item.url,
        },
    ) if item.url else ()

    return {
        "card_version": "2.0",
        "id": item.id,
        "item_type": item_type,
        "title": item.title,
        "image_url": item.image_url,
        "price": item.price or _UNKNOWN_PRICE,
        "availability": availability,
        "url": item.url,
        "button_label": button_label,
        "actions": actions,
        "status": item.status,
    }


def commercial_cards(items: list[CollectionItem] | tuple[CollectionItem, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(commercial_card(item) for item in items)


__all__ = ["commercial_card", "commercial_cards"]
