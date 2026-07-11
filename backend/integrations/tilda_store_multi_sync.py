from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.integrations.tilda_store_api import (
    StoreProduct,
    fetch_all_products,
    product_to_document,
)
from backend.integrations.tilda_store_discovery import (
    DEFAULT_SHOP_URL,
    StorePart,
    discover_store_parts,
)
from backend.storage.database import save_document


@dataclass(frozen=True, slots=True)
class StorePartResult:
    storepartuid: str
    recid: str
    expected_total: int | None
    received_total: int
    pages: int
    error: str | None = None


def fetch_all_discovered_products(
    shop_url: str = DEFAULT_SHOP_URL,
) -> tuple[list[StoreProduct], list[StorePartResult]]:
    parts = discover_store_parts(shop_url)

    products_by_uid: dict[str, StoreProduct] = {}
    part_results: list[StorePartResult] = []

    for part in parts:
        try:
            products, metadata = fetch_all_products(
                storepartuid=part.storepartuid,
                recid=part.recid,
            )

            for product in products:
                products_by_uid[product.uid] = product

            part_results.append(
                StorePartResult(
                    storepartuid=part.storepartuid,
                    recid=part.recid,
                    expected_total=metadata.get("expected_total"),
                    received_total=metadata.get("received_total", 0),
                    pages=metadata.get("pages", 0),
                )
            )
        except Exception as exc:
            part_results.append(
                StorePartResult(
                    storepartuid=part.storepartuid,
                    recid=part.recid,
                    expected_total=None,
                    received_total=0,
                    pages=0,
                    error=str(exc),
                )
            )

    products = sorted(
        products_by_uid.values(),
        key=lambda product: product.title.lower(),
    )

    return products, part_results


def sync_all_discovered_products(
    shop_url: str = DEFAULT_SHOP_URL,
) -> dict[str, Any]:
    products, part_results = fetch_all_discovered_products(shop_url)

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
        "store_blocks": len(part_results),
        "unique_products": len(products),
        "synced": synced,
        "errors_count": len(errors),
        "errors": errors,
        "parts": part_results,
    }


def print_summary(result: dict[str, Any]) -> None:
    print("=" * 72)
    print("AI BODHI MULTI-STORE SYNC")
    print("=" * 72)
    print(f"Store blocks:    {result.get('store_blocks', 0)}")
    print(f"Unique products: {result.get('unique_products', 0)}")
    print(f"Synced:          {result.get('synced', 0)}")
    print(f"Errors:          {result.get('errors_count', 0)}")

    print("\nBlocks:")

    for part in result.get("parts", []):
        status = "ERROR" if part.error else "OK"
        print(
            f"- {status} recid={part.recid} "
            f"storepartuid={part.storepartuid} "
            f"received={part.received_total} "
            f"expected={part.expected_total} "
            f"pages={part.pages}"
        )

        if part.error:
            print(f"  {part.error}")

    errors = result.get("errors", [])

    if errors:
        print("\nProduct save errors:")

        for error in errors:
            print(
                f"- {error.get('uid')} "
                f"{error.get('title')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    print_summary(sync_all_discovered_products())
