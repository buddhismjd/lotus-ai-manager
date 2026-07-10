from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from backend.config import KNOWLEDGE_FILE, SITE_URL
from backend.parser.site_parser import chunk_text, normalize_url


load_dotenv()

DEFAULT_YML_URL = (
    "https://svet-lotosa.tilda.ws/tstore/yml/"
    "08ed63f766046f5373d7e3cf36a017a3.yml"
)

HEADERS = {
    "User-Agent": "LotusAIManager-YML/1.0",
    "Accept": "application/xml,text/xml,*/*",
}


def clean_html(value: str | None) -> str:
    if not value:
        return ""

    soup = BeautifulSoup(unescape(value), "lxml")
    text = soup.get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def child_text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text.strip() if child is not None and child.text else ""


def load_knowledge() -> dict:
    if not KNOWLEDGE_FILE.exists():
        return {
            "site": SITE_URL,
            "pages": [],
            "chunks": [],
            "errors": [],
        }

    return json.loads(
        KNOWLEDGE_FILE.read_text(encoding="utf-8")
    )


def fetch_yml(url: str) -> ET.Element:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=45,
    )
    response.raise_for_status()

    content = response.content

    try:
        return ET.fromstring(content)
    except ET.ParseError as exc:
        raise RuntimeError(
            "Не удалось прочитать YML-каталог Tilda"
        ) from exc


def category_map(root: ET.Element) -> dict[str, str]:
    categories: dict[str, str] = {}

    for category in root.findall(".//categories/category"):
        category_id = str(category.get("id", "")).strip()
        category_name = (
            category.text.strip()
            if category.text
            else ""
        )

        if category_id:
            categories[category_id] = category_name

    return categories


def offer_url(offer: ET.Element, offer_id: str) -> str:
    direct_url = child_text(offer, "url")

    if direct_url:
        return normalize_url(direct_url)

    return normalize_url(
        f"{SITE_URL.rstrip('/')}/tproduct/{offer_id}"
    )


def offer_to_page(
    offer: ET.Element,
    categories: dict[str, str],
) -> tuple[dict, list[dict]]:
    offer_id = str(offer.get("id", "")).strip()
    title = (
        child_text(offer, "name")
        or child_text(offer, "model")
        or child_text(offer, "vendor")
        or f"Товар {offer_id}"
    )

    url = offer_url(offer, offer_id)
    price = child_text(offer, "price")
    old_price = child_text(offer, "oldprice")
    currency = child_text(offer, "currencyId")
    category_id = child_text(offer, "categoryId")
    category = categories.get(category_id, "")
    vendor = child_text(offer, "vendor")
    description = clean_html(
        child_text(offer, "description")
    )

    available = str(
        offer.get("available", "true")
    ).lower() not in {"false", "0", "no"}

    pictures = [
        picture.text.strip()
        for picture in offer.findall("picture")
        if picture.text
    ]

    params: dict[str, str] = {}

    for param in offer.findall("param"):
        name = str(param.get("name", "")).strip()
        value = param.text.strip() if param.text else ""

        if name and value:
            params[name] = value

    lines = [title]

    if category:
        lines.append(f"Категория: {category}")

    if price:
        price_line = f"Цена: {price}"

        if currency:
            price_line += f" {currency}"

        lines.append(price_line)

    if old_price:
        lines.append(f"Старая цена: {old_price} {currency}".strip())

    if vendor:
        lines.append(f"Производитель: {vendor}")

    if description:
        lines.append(description)

    for name, value in params.items():
        lines.append(f"{name}: {value}")

    content = "\n".join(lines).strip()
    chunks_text = chunk_text(content)

    page = {
        "id": offer_id,
        "url": url,
        "title": title,
        "original_title": title,
        "text": content,
        "chars": len(content),
        "page_type": "product",
        "enabled": available,
        "priority": 130,
        "classification_source": "tilda_yml",
        "source": "tilda_yml",
        "chunks_count": len(chunks_text),
        "product_id": offer_id,
        "price": price,
        "old_price": old_price,
        "currency": currency,
        "category": category,
        "category_id": category_id,
        "vendor": vendor,
        "available": available,
        "pictures": pictures,
        "params": params,
    }

    chunks = [
        {
            "id": "",
            "page_url": url,
            "page_title": title,
            "page_type": "product",
            "chunk_index": index,
            "text": text,
        }
        for index, text in enumerate(chunks_text)
    ]

    return page, chunks


def sync_yml_products() -> dict:
    yml_url = os.getenv(
        "TILDA_YML_URL",
        DEFAULT_YML_URL,
    ).strip()

    if not yml_url:
        raise RuntimeError(
            "Не задан TILDA_YML_URL"
        )

    root = fetch_yml(yml_url)
    categories = category_map(root)
    knowledge = load_knowledge()

    knowledge["pages"] = [
        page
        for page in knowledge.get("pages", [])
        if page.get("page_type") != "product"
    ]

    product_urls = {
        page.get("url")
        for page in knowledge.get("pages", [])
        if page.get("page_type") == "product"
    }

    knowledge["chunks"] = [
        chunk
        for chunk in knowledge.get("chunks", [])
        if chunk.get("page_url") not in product_urls
        and chunk.get("page_type") != "product"
    ]

    pages = knowledge.setdefault("pages", [])
    chunks = knowledge.setdefault("chunks", [])
    errors = [
        error
        for error in knowledge.get("errors", [])
        if error.get("source") != "tilda_yml"
    ]

    synced = 0

    for offer in root.findall(".//offers/offer"):
        try:
            page, page_chunks = offer_to_page(
                offer,
                categories,
            )
            pages.append(page)
            chunks.extend(page_chunks)
            synced += 1
        except Exception as exc:
            errors.append(
                {
                    "source": "tilda_yml",
                    "offer_id": offer.get("id"),
                    "error": str(exc),
                }
            )

    for index, chunk in enumerate(chunks, start=1):
        chunk["id"] = str(index)

    type_counts: dict[str, int] = {}

    for page in pages:
        page_type = page.get("page_type", "general")
        type_counts[page_type] = (
            type_counts.get(page_type, 0) + 1
        )

    knowledge.update(
        {
            "updated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
            "source": "tilda_api_plus_yml",
            "yml_url": yml_url,
            "pages_count": len(pages),
            "chunks_count": len(chunks),
            "errors_count": len(errors),
            "type_counts": type_counts,
            "products_synced": synced,
            "errors": errors,
        }
    )

    KNOWLEDGE_FILE.write_text(
        json.dumps(
            knowledge,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return knowledge


def print_summary(result: dict) -> None:
    print("Tilda YML product sync completed")
    print("=" * 70)
    print(
        f"Products synced: "
        f"{result.get('products_synced', 0)}"
    )
    print(
        f"Total pages:     "
        f"{result.get('pages_count', 0)}"
    )
    print(
        f"Total chunks:    "
        f"{result.get('chunks_count', 0)}"
    )
    print(
        f"Errors:          "
        f"{result.get('errors_count', 0)}"
    )


if __name__ == "__main__":
    print_summary(sync_yml_products())
