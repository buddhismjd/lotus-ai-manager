from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from backend.integrations.product_catalog_sync import (
    canonical_product_url,
    discover_all_product_urls,
)
from backend.parser.site_parser import chunk_text, extract_page
from backend.storage.database import save_document


MANUAL_PRODUCT_URLS = {
    (
        "https://svet-lotosa.tilda.ws/statui-svet-lotosa/"
        "tproduct/384940676312-statuya-beloi-tari"
    ),
}

PRODUCT_ID_PATTERN = re.compile(
    r"/tproduct/(?P<product_id>\d+)",
    re.IGNORECASE,
)


def product_id_from_url(url: str) -> str:
    match = PRODUCT_ID_PATTERN.search(url)

    if not match:
        raise ValueError(f"Не удалось определить ID товара из URL: {url}")

    return match.group("product_id")


def normalized_product_urls(
    discovered_urls: Iterable[str],
) -> list[str]:
    """
    Combine automatically discovered and manually registered product URLs.

    Product ID is used for deduplication so several category paths pointing
    to the same Tilda product do not create duplicate SQLite documents.
    """
    by_product_id: dict[str, str] = {}

    for raw_url in [*discovered_urls, *MANUAL_PRODUCT_URLS]:
        canonical = canonical_product_url(raw_url)

        if not canonical:
            continue

        product_id = product_id_from_url(canonical)
        current = by_product_id.get(product_id)

        if current is None or len(canonical) < len(current):
            by_product_id[product_id] = canonical

    return [
        by_product_id[product_id]
        for product_id in sorted(by_product_id)
    ]


def page_to_document(page: dict, url: str) -> dict:
    title = str(page.get("title") or "").strip()
    content = str(
        page.get("text")
        or page.get("content")
        or ""
    ).strip()

    if not title:
        raise ValueError(f"У товара отсутствует название: {url}")

    if not content:
        content = title

    chunks = chunk_text(content)

    if not chunks and content:
        chunks = [content]

    product_id = product_id_from_url(url)

    return {
        "id": f"product-{product_id}",
        "source_type": "tilda_product_crawler",
        "type": "product",
        "title": title,
        "url": url,
        "summary": content[:600],
        "content": content,
        "enabled": True,
        "priority": 140,
        "content_hash": hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
        "chunks": chunks,
    }


def sync_crawled_products_to_sqlite() -> dict:
    """
    Discover product pages, fetch them, and upsert them into SQLite.

    This supplements the Tilda YML feed. It is especially useful for product
    collections that exist on published category pages but are absent from
    the current YML export.
    """
    discovered_urls, discovery_errors = discover_all_product_urls()
    product_urls = normalized_product_urls(discovered_urls)

    synced = 0
    errors: list[dict[str, str]] = [
        {
            "url": str(error.get("url") or ""),
            "stage": str(error.get("stage") or "discovery"),
            "error": str(error.get("error") or ""),
        }
        for error in discovery_errors
    ]

    for url in product_urls:
        try:
            page = extract_page(url)
            document = page_to_document(page, url)
            save_document(document)
            synced += 1
        except Exception as exc:
            errors.append(
                {
                    "url": url,
                    "stage": "product_sync",
                    "error": str(exc),
                }
            )

    return {
        "products_discovered": len(product_urls),
        "products_synced": synced,
        "errors_count": len(errors),
        "errors": errors,
    }


def print_summary(result: dict) -> None:
    print("SQLite product crawler sync completed")
    print("=" * 72)
    print(
        "Products discovered: "
        f"{result.get('products_discovered', 0)}"
    )
    print(
        "Products synced:     "
        f"{result.get('products_synced', 0)}"
    )
    print(
        "Errors:              "
        f"{result.get('errors_count', 0)}"
    )

    errors = result.get("errors", [])

    if errors:
        print("\nErrors:")

        for error in errors:
            print(
                f"- {error.get('url')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    print_summary(sync_crawled_products_to_sqlite())
