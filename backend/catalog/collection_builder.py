from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from decimal import Decimal
from typing import Any, Iterable
from urllib.parse import quote, urlparse

from backend.integrations.product_page_snapshot import load_product_page_snapshot

from backend.catalog.models import Product
from backend.catalog.collection_ranking import rank_collection
from backend.catalog.product_intelligence import analyze_product, normalize
from backend.catalog.product_profiles import get_product_profile
from backend.catalog.repositories import ProductRepository
from backend.rag.dynamic_query_router import analyze_query_semantics, detect_product_kind

_IMAGE_RE = re.compile(r"(?:Изображение|Фото|Image)\s*:\s*(https?://\S+)", re.IGNORECASE)
_PRODUCT_UID_RE = re.compile(r"/tproduct/(\d+)", re.IGNORECASE)

_QUERY_TOKEN_RE = re.compile(r"[0-9a-zа-яё]+", re.IGNORECASE)
_QUERY_STOPWORDS = {
    "в", "во", "и", "на", "по", "для", "с", "со", "из", "к", "ко",
    "а", "ли", "есть", "имеется", "нужен", "нужна", "нужны", "хочу",
    "купить", "заказать", "покажи", "покажите", "найди", "найдите",
    "товар", "товары", "у", "вас", "мне", "подскажите", "все", "весь",
}
_KIND_WORD_PREFIXES = {
    "стату", "статуй", "скульптур", "фигур", "амулет", "подвес", "кулон",
    "медальон", "четк", "чётк", "мала", "ваджр", "дордж", "танк",
    "тханк", "чаш", "благовон", "аромапал", "колоколь", "колокол",
    "гант", "гхант",
}
_RUSSIAN_SUFFIXES = (
    "иями", "ями", "ами", "ого", "ему", "ому", "ыми", "ими", "ая", "яя",
    "ое", "ее", "ий", "ый", "ой", "ую", "юю", "ым", "им", "ам", "ям", "ах", "ях",
    "ом", "ем", "ов", "ев", "ы", "и", "а", "я", "у", "ю", "е", "о",
)

def _stem_token(token: str) -> str:
    value = normalize(token)
    for suffix in _RUSSIAN_SUFFIXES:
        if value.endswith(suffix) and len(value) - len(suffix) >= 3:
            return value[:-len(suffix)]
    return value

def _lexical_query_terms(query: str) -> tuple[str, ...]:
    terms: list[str] = []
    for token in _QUERY_TOKEN_RE.findall(normalize(query)):
        if token in _QUERY_STOPWORDS or token.isdigit():
            continue
        stem = _stem_token(token)
        if any(stem.startswith(prefix) or prefix.startswith(stem) for prefix in _KIND_WORD_PREFIXES):
            continue
        if len(stem) >= 3 and stem not in terms:
            terms.append(stem)
    return tuple(terms)

def _contains_stem(text: str, stem: str) -> bool:
    for word in _QUERY_TOKEN_RE.findall(normalize(text)):
        candidate = _stem_token(word)
        if len(candidate) < 3:
            continue
        if word.startswith(stem) or stem.startswith(candidate):
            return True
        if SequenceMatcher(None, stem, candidate).ratio() >= 0.78:
            return True
    return False


_SURFACE_KIND_PREFIX_GROUPS = (
    ("подвес",),
    ("кулон",),
    ("амулет",),
    ("медальон",),
    ("гау",),
    ("колоколь", "гант", "гхант"),
)

def _required_surface_kind_prefixes(query: str) -> tuple[str, ...]:
    words = tuple(_QUERY_TOKEN_RE.findall(normalize(query)))
    for group in _SURFACE_KIND_PREFIX_GROUPS:
        if any(any(word.startswith(prefix) for prefix in group) for word in words):
            return group
    return ()

def _matches_surface_kind(product: Product, query: str) -> bool:
    prefixes = _required_surface_kind_prefixes(query)
    if not prefixes:
        return True
    text = normalize(" ".join((product.title, product.category or "")))
    words = _QUERY_TOKEN_RE.findall(text)
    return any(any(word.startswith(prefix) for prefix in prefixes) for word in words)

def _matches_lexical_constraints(product: Product, query: str) -> bool:
    terms = _lexical_query_terms(query)
    if not terms:
        return True
    searchable = " ".join((product.title, product.description or "", product.category or ""))
    return all(_contains_stem(searchable, term) for term in terms)

def _resolve_availability(product: Product, *, live_lookup: bool) -> str | None:
    if product.availability_status:
        return product.availability_status
    if not live_lookup or not product.url:
        return None
    if urlparse(product.url).hostname != "svet-lotosa.tilda.ws":
        return None
    try:
        return load_product_page_snapshot(product.url, timeout=12.0).availability_status
    except Exception:
        return None


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
    description: str | None = None
    button_label: str = "Открыть товар"
    group: str | None = None
    item_type: str = "product"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _profile_id(product: Product) -> str | None:
    match = _PRODUCT_UID_RE.search(product.url or "")
    return f"product-{match.group(1)}" if match else None


def _image_url(product: Product) -> str | None:
    if product.image_url:
        return product.image_url
    explicit = product.metadata.get("image_url") if product.metadata else None
    if explicit:
        return str(explicit)
    match = _IMAGE_RE.search(product.description or "")
    if match:
        return match.group(1).rstrip(".,;)]")
    if product.url:
        return f"/api/sales/product-image?source={quote(product.url, safe='')}"
    return None


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

    product_kind = (
        (profile.product_type if profile else None)
        or detect_product_kind(product.title)
        or intelligence.product_type
    )
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
    if not _matches_surface_kind(product, query):
        return False

    semantic_match = bool(requested_kind or requested_entities or requested_materials)
    return semantic_match and _matches_lexical_constraints(product, query)


def build_product_collection(query: str, products: Iterable[Product] | None = None) -> list[CollectionItem]:
    source = list(products) if products is not None else ProductRepository().list_all()
    matched = [product for product in source if _matches_product(product, query)]
    live_lookup = len(matched) <= 8 and bool(_lexical_query_terms(query))

    items: list[CollectionItem] = []
    seen: set[str] = set()
    for product in matched:
        identity = product.url or product.id
        if identity in seen:
            continue
        seen.add(identity)
        availability = _resolve_availability(product, live_lookup=live_lookup)
        items.append(CollectionItem(
            id=product.id,
            title=product.title,
            url=product.url or None,
            image_url=_image_url(product),
            price=_price(product.price, product.currency),
            # Never convert an unknown stock state into ``В наличии``.
            # Publication in the catalog and physical availability are
            # independent facts.
            availability=availability,
            material=product.material,
            size=_size(product),
            description=(product.description or "").strip() or None,
            button_label="Открыть товар",
            group=(
                "В наличии"
                if (availability or "").strip().casefold() == "в наличии"
                else "Нет в наличии"
                if (availability or "").strip().casefold() == "нет в наличии"
                else "Под заказ"
                if (availability or "").strip().casefold() == "под заказ"
                else "Наличие уточняется"
            ),
            item_type="product",
        ))
    return rank_collection(query, items)


__all__ = ["CollectionItem", "build_product_collection"]
