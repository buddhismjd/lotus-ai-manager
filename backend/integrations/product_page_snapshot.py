from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from backend.integrations.product_raw_snapshot import extract_product_object
from backend.integrations.product_stock_status import resolve_stock_status


_SPACE_RE = re.compile(r"\s+")
_MATERIAL_RE = re.compile(
    r"(?:материал|изготовлен(?:а|о|ы)?\s+из)\s*[:\-]?\s*"
    r"(?P<value>[^.;\n]{2,80})",
    re.IGNORECASE,
)
_STATUS_PATTERNS = (
    (re.compile(r"\bнет\s+в\s+наличии\b", re.IGNORECASE), "Нет в наличии"),
    (re.compile(r"\bпод\s+заказ\b|\bна\s+заказ\b", re.IGNORECASE), "Под заказ"),
    (re.compile(r"\bв\s+наличии\b", re.IGNORECASE), "В наличии"),
)
_SCHEMA_STATUS = {
    "https://schema.org/InStock": "В наличии",
    "http://schema.org/InStock": "В наличии",
    "https://schema.org/OutOfStock": "Нет в наличии",
    "http://schema.org/OutOfStock": "Нет в наличии",
    "https://schema.org/PreOrder": "Под заказ",
    "http://schema.org/PreOrder": "Под заказ",
    "https://schema.org/BackOrder": "Под заказ",
    "http://schema.org/BackOrder": "Под заказ",
}


@dataclass(frozen=True, slots=True)
class ProductPageSnapshot:
    url: str
    image_url: str | None = None
    availability_status: str | None = None
    material: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    description: str | None = None


def fetch_product_page(url: str, timeout: float = 30.0) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "AI-Bodhi-Catalog-Synchronizer/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _clean_text(value: Any) -> str:
    return _SPACE_RE.sub(" ", html.unescape(str(value or ""))).strip()


def _json_ld_objects(soup: BeautifulSoup) -> Iterable[dict[str, Any]]:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            continue
        values = loaded if isinstance(loaded, list) else [loaded]
        for value in values:
            if not isinstance(value, dict):
                continue
            graph = value.get("@graph")
            if isinstance(graph, list):
                for item in graph:
                    if isinstance(item, dict):
                        yield item
            yield value


def _product_schema(soup: BeautifulSoup) -> dict[str, Any] | None:
    for item in _json_ld_objects(soup):
        item_type = item.get("@type")
        types = item_type if isinstance(item_type, list) else [item_type]
        if any(str(value).lower() == "product" for value in types):
            return item
    return None


def _first_image(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list):
        for item in value:
            image = _first_image(item)
            if image:
                return image
    if isinstance(value, dict):
        for key in ("url", "contentUrl", "src"):
            image = _first_image(value.get(key))
            if image:
                return image
    return None


def _normalize_url(value: str | None, page_url: str) -> str | None:
    if not value:
        return None
    return urljoin(page_url, html.unescape(value.strip()))


def _extract_image(soup: BeautifulSoup, schema: dict[str, Any] | None, page_url: str) -> str | None:
    if schema:
        image = _first_image(schema.get("image"))
        if image:
            return _normalize_url(image, page_url)
    for selector in (
        ('meta', {'property': 'og:image'}),
        ('meta', {'name': 'twitter:image'}),
        ('link', {'rel': 'image_src'}),
    ):
        tag = soup.find(selector[0], attrs=selector[1])
        if tag:
            value = tag.get("content") or tag.get("href")
            if value:
                return _normalize_url(str(value), page_url)
    return None


def _offers(schema: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not schema:
        return []
    value = schema.get("offers")
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _extract_status(soup: BeautifulSoup, schema: dict[str, Any] | None) -> str | None:
    for offer in _offers(schema):
        availability = str(offer.get("availability") or "").strip()
        if availability in _SCHEMA_STATUS:
            return _SCHEMA_STATUS[availability]
    visible_text = _clean_text(soup.get_text(" ", strip=True))
    # Full-page Tilda markup contains generic shop labels such as
    # "В наличии" that are not proof for the current product.  Negative and
    # preorder labels are safe fallbacks; a positive status must come from the
    # selected product object or Product schema.
    for pattern, status in _STATUS_PATTERNS:
        if status == "В наличии":
            continue
        if pattern.search(visible_text):
            return status
    return None


def _decimal(value: Any) -> Decimal | None:
    text = re.sub(r"[^0-9,.-]", "", str(value or "")).replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _extract_price(schema: dict[str, Any] | None) -> tuple[Decimal | None, str | None]:
    for offer in _offers(schema):
        price = _decimal(offer.get("price") or offer.get("lowPrice"))
        currency = _clean_text(offer.get("priceCurrency")) or None
        if price is not None or currency:
            return price, currency
    return None, None


def _extract_description(soup: BeautifulSoup, schema: dict[str, Any] | None) -> str | None:
    if schema:
        description = _clean_text(schema.get("description"))
        if description:
            return description
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return _clean_text(tag.get("content")) or None
    return None


def _extract_material(schema: dict[str, Any] | None, description: str | None, visible_text: str) -> str | None:
    if schema:
        material = _clean_text(schema.get("material"))
        if material:
            return material
    for source in (description or "", visible_text):
        match = _MATERIAL_RE.search(source)
        if match:
            value = _clean_text(match.group("value"))
            if value:
                return value
    return None


def _script_product_status(raw_html: str, page_url: str) -> str | None:
    uid_match = re.search(r"/tproduct/(?P<uid>\d+)(?:[-/]|$)", page_url, re.IGNORECASE)
    expected_uid = uid_match.group("uid") if uid_match else None
    try:
        product, _ = extract_product_object(raw_html, expected_uid=expected_uid)
    except ValueError:
        return None
    return resolve_stock_status(
        explicit_status=(
            product.get("availability_status")
            or product.get("availability")
            or product.get("stock_status")
        ),
        quantity=product.get("quantity"),
    )


def parse_product_page(raw_html: str, page_url: str) -> ProductPageSnapshot:
    soup = BeautifulSoup(raw_html, "lxml")
    schema = _product_schema(soup)
    description = _extract_description(soup, schema)
    visible_text = _clean_text(soup.get_text(" ", strip=True))
    price, currency = _extract_price(schema)
    visible_status = _extract_status(soup, schema)
    script_status = _script_product_status(raw_html, page_url)
    # A visible, product-page label such as «Под заказ» or «Нет в наличии»
    # is more specific than Tilda's generic quantity=0 flag. Positive
    # availability is still accepted only from Product schema or product data.
    availability_status = visible_status or script_status
    return ProductPageSnapshot(
        url=page_url,
        image_url=_extract_image(soup, schema, page_url),
        availability_status=availability_status,
        material=_extract_material(schema, description, visible_text),
        price=price,
        currency=currency,
        description=description,
    )


def load_product_page_snapshot(url: str, timeout: float = 30.0) -> ProductPageSnapshot:
    return parse_product_page(fetch_product_page(url, timeout=timeout), url)


__all__ = [
    "ProductPageSnapshot",
    "fetch_product_page",
    "parse_product_page",
    "load_product_page_snapshot",
]
