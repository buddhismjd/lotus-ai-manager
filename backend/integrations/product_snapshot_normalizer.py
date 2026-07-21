from __future__ import annotations

import html
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from backend.integrations.product_raw_snapshot import RawProductSnapshot


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def _clean(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = _TAG_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def _decimal(value: Any) -> Decimal | None:
    text = re.sub(r"[^0-9,.-]", "", str(value or "")).replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _gallery(data: dict[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for item in data.get("gallery") or []:
        if isinstance(item, str):
            url = item
        elif isinstance(item, dict):
            url = item.get("img") or item.get("url") or item.get("src")
        else:
            continue
        url = str(url or "").strip()
        if url and url not in values:
            values.append(url)
    return tuple(values)


def _quantity(data: dict[str, Any]) -> Decimal | None:
    value = data.get("quantity")
    if value in (None, ""):
        return None
    return _decimal(value)


@dataclass(frozen=True, slots=True)
class NormalizedProductSnapshot:
    product_uid: str
    url: str
    title: str
    description: str
    brand: str | None
    sku: str | None
    price: Decimal | None
    currency: str | None
    gallery: tuple[str, ...]
    primary_image: str | None
    quantity: Decimal | None
    characteristics: tuple[dict[str, Any], ...]
    properties: tuple[dict[str, Any], ...]
    partuids: tuple[str, ...]
    source_hash: str
    captured_at: str

    # Deliberately unconfirmed until a separate source is proven.
    category: str | None = None
    material: str | None = None
    height_cm: Decimal | None = None
    width_cm: Decimal | None = None
    depth_cm: Decimal | None = None
    availability_status: str | None = None


def normalize_raw_snapshot(snapshot: RawProductSnapshot) -> NormalizedProductSnapshot:
    data = snapshot.product_data
    gallery = _gallery(data)
    characteristics = tuple(
        item for item in (data.get("characteristics") or []) if isinstance(item, dict)
    )
    properties = tuple(
        item for item in (data.get("properties") or []) if isinstance(item, dict)
    )
    partuids = tuple(str(value) for value in (data.get("partuids") or []))

    return NormalizedProductSnapshot(
        product_uid=snapshot.product_uid,
        url=str(data.get("url") or snapshot.page_url).replace("\\/", "/"),
        title=_clean(data.get("title")),
        description=_clean(data.get("text") or data.get("description")),
        brand=_clean(data.get("brand")) or None,
        sku=_clean(data.get("sku")) or None,
        price=_decimal(data.get("price")),
        currency=_clean(data.get("currency")) or "RUB",
        gallery=gallery,
        primary_image=gallery[0] if gallery else None,
        quantity=_quantity(data),
        characteristics=characteristics,
        properties=properties,
        partuids=partuids,
        source_hash=snapshot.snapshot_sha256,
        captured_at=snapshot.captured_at,
    )


__all__ = ["NormalizedProductSnapshot", "normalize_raw_snapshot"]
