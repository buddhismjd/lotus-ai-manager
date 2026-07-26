from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


_CANONICAL = {
    "в наличии": "В наличии",
    "есть в наличии": "В наличии",
    "instock": "В наличии",
    "in stock": "В наличии",
    "нет в наличии": "Нет в наличии",
    "outofstock": "Нет в наличии",
    "out of stock": "Нет в наличии",
    "под заказ": "Под заказ",
    "на заказ": "Под заказ",
    "preorder": "Под заказ",
    "backorder": "Под заказ",
}


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def normalize_stock_status(value: Any) -> str | None:
    text = str(value or "").strip().casefold()
    if not text:
        return None
    compact = text.replace("https://schema.org/", "").replace("http://schema.org/", "")
    return _CANONICAL.get(compact) or _CANONICAL.get(text)


def status_from_quantity(value: Any) -> str | None:
    quantity = _decimal(value)
    if quantity is None:
        return None
    return "В наличии" if quantity > 0 else "Нет в наличии"


def resolve_stock_status(*, explicit_status: Any = None, quantity: Any = None) -> str | None:
    """Resolve stock truth using explicit product data first, then quantity.

    A zero quantity is authoritative and must never be replaced by a generic
    page label such as "В наличии" found elsewhere in Tilda markup.
    """
    quantity_status = status_from_quantity(quantity)
    if quantity_status == "Нет в наличии":
        return quantity_status
    explicit = normalize_stock_status(explicit_status)
    if explicit is not None:
        return explicit
    return quantity_status


__all__ = ["normalize_stock_status", "status_from_quantity", "resolve_stock_status"]
