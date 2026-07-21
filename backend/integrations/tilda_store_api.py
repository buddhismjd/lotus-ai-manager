from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.catalog.product_intelligence import analyze_product
from backend.parser.site_parser import chunk_text
from backend.storage.database import save_document


STORE_API_URL = "https://store.tildaapi.com/api/getproductslist/"
DEFAULT_STORE_PART_UID = "979629845002"
DEFAULT_RECID = "2234421481"
DEFAULT_PAGE_SIZE = 36
DEFAULT_SHOP_URL = "https://svet-lotosa.tilda.ws/svet-lotosa-shop"


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_SLUG_RE = re.compile(r"[^a-z0-9а-яё]+", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class StoreProduct:
    uid: str
    title: str
    description: str
    price: str
    currency: str
    sku: str
    url: str
    category: str
    image_url: str
    raw: dict[str, Any]
    availability_status: str | None = None
    material: str | None = None


def _clean_html(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = _TAG_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def _first_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)

        if value not in (None, "", [], {}):
            return value

    return None


def _slugify(value: str) -> str:
    value = value.lower().replace("ё", "е")
    value = _SLUG_RE.sub("-", value)
    return value.strip("-")


def _normalize_url(value: Any, uid: str, title: str) -> str:
    url = str(value or "").strip()

    if url.startswith("//"):
        return f"https:{url}"

    if url.startswith("/"):
        return f"https://svet-lotosa.tilda.ws{url}"

    if url.startswith("http://") or url.startswith("https://"):
        return url

    slug = _slugify(title) or "product"
    return f"{DEFAULT_SHOP_URL}/tproduct/{uid}-{slug}"


def _extract_image_url(product: dict[str, Any]) -> str:
    direct = _first_value(
        product,
        "img",
        "image",
        "image_url",
        "photo",
        "cover",
    )

    if isinstance(direct, str):
        return _normalize_image_url(direct)

    gallery = _first_value(
        product,
        "gallery",
        "images",
        "photos",
    )

    if isinstance(gallery, list) and gallery:
        first = gallery[0]

        if isinstance(first, str):
            return _normalize_image_url(first)

        if isinstance(first, dict):
            nested = _first_value(
                first,
                "img",
                "url",
                "src",
                "image",
            )

            if nested:
                return _normalize_image_url(str(nested))

    return ""


def _normalize_image_url(value: str) -> str:
    value = value.strip()

    if value.startswith("//"):
        return f"https:{value}"

    return value




def _extract_availability_status(product: dict[str, Any]) -> str | None:
    """Return only an explicitly published stock status; never infer made-to-order."""
    text_values: list[str] = []
    for key in (
        "availability", "availability_status", "stock_status", "status",
        "badge", "label", "inventory_status", "store_label",
    ):
        value = product.get(key)
        if value not in (None, "", [], {}):
            text_values.append(_clean_html(value).lower())

    joined = " ".join(text_values)
    published_text = _clean_html(
        json.dumps(product, ensure_ascii=False, default=str)
    ).lower()
    status_text = f"{joined} {published_text}"
    if re.search(r"под\s*заказ|на\s*заказ", status_text):
        return "Под заказ"
    if re.search(r"нет\s+в\s+наличии|нет\s+в\s+наличие|распродан|продан", status_text):
        return "Нет в наличии"
    if re.search(r"в\s+наличии|в\s+наличие", status_text):
        return "В наличии"

    for key in ("in_stock", "instock", "is_available"):
        value = product.get(key)
        if isinstance(value, bool):
            return "В наличии" if value else "Нет в наличии"

    quantity = _first_value(product, "quantity", "qty", "stock_quantity")
    try:
        if quantity not in (None, "") and float(str(quantity).replace(",", ".")) > 0:
            return "В наличии"
    except (TypeError, ValueError):
        pass

    return None


def _extract_material(product: dict[str, Any], description: str) -> str | None:
    direct = _clean_html(_first_value(product, "material", "materials", "composition"))
    if direct:
        return direct
    intelligence = analyze_product(
        title=_clean_html(_first_value(product, "title", "name")),
        description=description,
        category=_clean_html(_first_value(product, "category", "category_title", "group")),
    )
    return intelligence.materials[0] if intelligence.materials else None


def parse_store_product(product: dict[str, Any]) -> StoreProduct:
    uid = str(
        _first_value(
            product,
            "uid",
            "id",
            "productid",
            "product_id",
        )
        or ""
    ).strip()

    title = _clean_html(
        _first_value(
            product,
            "title",
            "name",
        )
    )

    if not uid:
        raise ValueError("В товаре отсутствует uid")

    if not title:
        raise ValueError(f"В товаре {uid} отсутствует название")

    description = _clean_html(
        _first_value(
            product,
            "descr",
            "description",
            "text",
            "html",
        )
    )

    price = _clean_html(
        _first_value(
            product,
            "price",
            "pricevalue",
            "amount",
        )
    )

    currency = _clean_html(
        _first_value(
            product,
            "currency",
            "currencycode",
        )
    )

    sku = _clean_html(
        _first_value(
            product,
            "sku",
            "article",
            "vendorcode",
        )
    )

    category = _clean_html(
        _first_value(
            product,
            "category",
            "category_title",
            "group",
        )
    )

    url = _normalize_url(
        _first_value(
            product,
            "url",
            "link",
            "product_url",
        ),
        uid,
        title,
    )

    return StoreProduct(
        uid=uid,
        title=title,
        description=description,
        price=price,
        currency=currency,
        sku=sku,
        url=url,
        category=category,
        image_url=_extract_image_url(product),
        availability_status=_extract_availability_status(product),
        material=_extract_material(product, description),
        raw=product,
    )


def build_request_url(
    *,
    storepartuid: str,
    recid: str,
    slice_number: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> str:
    query = urlencode(
        {
            "storepartuid": storepartuid,
            "recid": recid,
            "getallparts": "true",
            "getoptions": "true",
            "slice": slice_number,
            "size": page_size,
        }
    )

    return f"{STORE_API_URL}?{query}"


def fetch_store_slice(
    *,
    storepartuid: str,
    recid: str,
    slice_number: int,
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: float = 30.0,
) -> dict[str, Any]:
    url = build_request_url(
        storepartuid=storepartuid,
        recid=recid,
        slice_number=slice_number,
        page_size=page_size,
    )

    request = Request(
        url,
        headers={
            "User-Agent": "AI-Bodhi/0.9",
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")

    data = json.loads(payload)

    if not isinstance(data, dict):
        raise ValueError("Tilda Store API вернул неожиданный формат")

    return data


def fetch_all_products(
    *,
    storepartuid: str = DEFAULT_STORE_PART_UID,
    recid: str = DEFAULT_RECID,
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: float = 30.0,
    max_slices: int = 100,
) -> tuple[list[StoreProduct], dict[str, Any]]:
    products_by_uid: dict[str, StoreProduct] = {}
    raw_pages = 0
    expected_total: int | None = None
    slice_number = 1

    while slice_number and raw_pages < max_slices:
        data = fetch_store_slice(
            storepartuid=storepartuid,
            recid=recid,
            slice_number=slice_number,
            page_size=page_size,
            timeout=timeout,
        )

        raw_pages += 1

        if expected_total is None:
            raw_total = data.get("total")

            if isinstance(raw_total, int):
                expected_total = raw_total
            elif str(raw_total or "").isdigit():
                expected_total = int(raw_total)

        raw_products = data.get("products") or []

        if not isinstance(raw_products, list):
            raise ValueError("Поле products должно быть списком")

        for raw_product in raw_products:
            if not isinstance(raw_product, dict):
                continue

            product = parse_store_product(raw_product)
            products_by_uid[product.uid] = product

        next_slice = data.get("nextslice")

        if next_slice in (None, "", False, 0, "0"):
            break

        try:
            next_slice_number = int(next_slice)
        except (TypeError, ValueError):
            break

        if next_slice_number == slice_number:
            break

        slice_number = next_slice_number

        if expected_total is not None and len(products_by_uid) >= expected_total:
            break

    products = sorted(
        products_by_uid.values(),
        key=lambda product: product.title.lower(),
    )

    return products, {
        "expected_total": expected_total,
        "received_total": len(products),
        "pages": raw_pages,
        "storepartuid": storepartuid,
        "recid": recid,
    }


def product_to_document(product: StoreProduct) -> dict[str, Any]:
    intelligence = analyze_product(
        title=product.title,
        description=product.description,
        category=product.category,
        sku=product.sku,
    )

    details = [
        product.title,
        product.description,
        f"Категория: {product.category}" if product.category else "",
        (
            f"Цена: {product.price} {product.currency}".strip()
            if product.price
            else ""
        ),
        f"SKU: {product.sku}" if product.sku else "",
        f"Изображение: {product.image_url}" if product.image_url else "",
        f"Материал: {product.material}" if product.material else "",
        f"Статус: {product.availability_status}" if product.availability_status else "",
        intelligence.to_search_text(),
    ]

    content = "\n".join(
        detail
        for detail in details
        if detail
    ).strip()

    chunks = chunk_text(content)

    if not chunks and content:
        chunks = [content]

    return {
        "id": f"product-{product.uid}",
        "source_type": "tilda_store_api",
        "type": "product",
        "title": product.title,
        "url": product.url,
        "summary": "\n".join(
            part
            for part in [
                product.description[:500],
                intelligence.to_search_text(),
            ]
            if part
        )[:1000],
        "content": content,
        "enabled": True,
        "priority": 160,
        "content_hash": hashlib.sha256(
            json.dumps(
                product.raw,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        ).hexdigest(),
        "chunks": chunks,
    }


def sync_store_api_to_sqlite(
    *,
    storepartuid: str = DEFAULT_STORE_PART_UID,
    recid: str = DEFAULT_RECID,
) -> dict[str, Any]:
    products, metadata = fetch_all_products(
        storepartuid=storepartuid,
        recid=recid,
    )

    synced = 0
    errors: list[dict[str, str]] = []

    for product in products:
        try:
            save_document(product_to_document(product))
            synced += 1
        except Exception as exc:
            errors.append(
                {
                    "uid": product.uid,
                    "title": product.title,
                    "error": str(exc),
                }
            )

    return {
        **metadata,
        "synced": synced,
        "errors_count": len(errors),
        "errors": errors,
    }


def print_sync_summary(result: dict[str, Any]) -> None:
    print("=" * 72)
    print("AI BODHI TILDA STORE API SYNC")
    print("=" * 72)
    print(f"Expected total: {result.get('expected_total')}")
    print(f"Received total: {result.get('received_total')}")
    print(f"Pages:          {result.get('pages')}")
    print(f"Synced:         {result.get('synced')}")
    print(f"Errors:         {result.get('errors_count')}")

    errors = result.get("errors") or []

    if errors:
        print("\nErrors:")

        for error in errors:
            print(
                f"- {error.get('uid')} "
                f"{error.get('title')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    print_sync_summary(sync_store_api_to_sqlite())
