from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Any, Iterable

from backend.catalog.models import Product
from backend.catalog.product_intelligence import analyze_product, normalize
from backend.catalog.product_profiles import get_product_profile
from backend.catalog.repositories import ProductRepository
from backend.rag.dynamic_query_router import analyze_query_semantics

_IMAGE_RE = re.compile(r"(?:Изображение|Фото|Image)\s*:\s*(https?://\S+)", re.IGNORECASE)
_PRODUCT_UID_RE = re.compile(r"/tproduct/(\d+)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class CollectionItem:
    id: str
    title: str
    url: str | None
    image_url: str | None = None
    price: str | None = None
    availability: str | None = None
    material: str | None = None
    size: str | None = None
    status: str = "published"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _profile_id(product: Product) -> str | None:
    match = _PRODUCT_UID_RE.search(product.url or "")
    return f"product-{match.group(1)}" if match else None


def _image_url(product: Product) -> str | None:
    explicit = product.metadata.get("image_url") if product.metadata else None
    if explicit:
        return str(explicit)
    match = _IMAGE_RE.search(product.description or "")
    return match.group(1).rstrip(".,;)]") if match else None


def _price(value: Decimal | None, currency: str) -> str | None:
    if value is None:
        return None
    amount = f"{value:,.0f}".replace(",", " ")
    symbol = {"RUR": "₽", "RUB": "₽", "USD": "$", "EUR": "€"}.get(currency.upper(), currency)
    return f"{amount} {symbol}".strip()


def _size(product: Product) -> str | None:
    if product.height_cm and product.width_cm:
        return f"{product.height_cm:g} × {product.width_cm:g} см"
    if product.height_cm:
        return f"высота {product.height_cm:g} см"
    if product.width_cm:
        return f"ширина {product.width_cm:g} см"
    return None


def _matches_product(product: Product, query: str) -> bool:
    requested = analyze_query_semantics(query)
    requested_kind = requested["product_kind"]
    requested_entities = set(requested["entities"])
    requested_materials = set(requested["materials"])

    profile = get_product_profile(_profile_id(product)) if _profile_id(product) else None
    intelligence = analyze_product(
        title=product.title,
        description=product.description,
        category=product.category or "",
    )

    product_kind = (profile.product_type if profile else None) or intelligence.product_type
    product_entities = {
        normalize(value)
        for value in ((profile.entities if profile else ()) or intelligence.entities)
    }
    product_materials = {
        normalize(value)
        for value in ((profile.materials if profile else ()) or intelligence.materials)
    }

    if requested_kind and product_kind != requested_kind:
        return False
    if requested_entities and not requested_entities.intersection(product_entities):
        return False
    if requested_materials and not requested_materials.intersection(product_materials):
        return False

    return bool(requested_kind or requested_entities or requested_materials)


def build_product_collection(query: str, products: Iterable[Product] | None = None) -> list[CollectionItem]:
    source = list(products) if products is not None else ProductRepository().list_all()
    matched = [product for product in source if _matches_product(product, query)]

    items: list[CollectionItem] = []
    seen: set[str] = set()
    for product in matched:
        identity = product.url or product.id
        if identity in seen:
            continue
        seen.add(identity)
        items.append(CollectionItem(
            id=product.id,
            title=product.title,
            url=product.url or None,
            image_url=_image_url(product),
            price=_price(product.price, product.currency),
            availability="В наличии" if product.available else "Под заказ / наличие уточняется",
            material=product.material,
            size=_size(product),
        ))
    return items


__all__ = ["CollectionItem", "build_product_collection"]
