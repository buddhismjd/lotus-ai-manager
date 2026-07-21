from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from backend.integrations.catalog_completeness import build_catalog_completeness_report
from backend.integrations.product_page_snapshot import load_product_page_snapshot
from backend.integrations.tilda_store_api import StoreProduct, product_to_document
from backend.integrations.tilda_store_multi_sync import fetch_all_discovered_products_with_report
from backend.storage.database import get_connection, initialize_database, save_document


@dataclass(frozen=True, slots=True)
class SynchronizedProduct:
    uid: str
    title: str
    url: str
    category: str
    description: str
    price: Decimal | None
    currency: str | None
    sku: str
    image_url: str | None
    availability_status: str | None
    material: str | None
    source_hash: str
    synced_at: str


def _decimal(value: str) -> Decimal | None:
    text = str(value or "").replace(" ", "").replace(",", ".")
    try:
        return Decimal(text) if text else None
    except InvalidOperation:
        return None


def _enrich(product: StoreProduct) -> StoreProduct:
    snapshot = load_product_page_snapshot(product.url)
    return replace(
        product,
        description=snapshot.description or product.description,
        price=(str(snapshot.price) if snapshot.price is not None else product.price),
        currency=snapshot.currency or product.currency,
        image_url=snapshot.image_url or product.image_url,
        availability_status=snapshot.availability_status,
        material=snapshot.material or product.material,
    )


def _source_hash(product: StoreProduct) -> str:
    payload = {
        "uid": product.uid,
        "title": product.title,
        "url": product.url,
        "category": product.category,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "sku": product.sku,
        "image_url": product.image_url,
        "availability_status": product.availability_status,
        "material": product.material,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _save_catalog_item(product: StoreProduct) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO product_catalog_items (
                product_uid, document_id, title, url, category, description,
                price, currency, sku, image_url, availability_status,
                material, source_hash, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_uid) DO UPDATE SET
                document_id = excluded.document_id,
                title = excluded.title,
                url = excluded.url,
                category = excluded.category,
                description = excluded.description,
                price = excluded.price,
                currency = excluded.currency,
                sku = excluded.sku,
                image_url = excluded.image_url,
                availability_status = excluded.availability_status,
                material = excluded.material,
                source_hash = excluded.source_hash,
                synced_at = excluded.synced_at
            """,
            (
                product.uid,
                f"product-{product.uid}",
                product.title,
                product.url,
                product.category,
                product.description,
                str(_decimal(product.price)) if _decimal(product.price) is not None else None,
                product.currency or None,
                product.sku,
                product.image_url or None,
                product.availability_status,
                product.material,
                _source_hash(product),
                now,
            ),
        )


def sync_product_catalog() -> dict[str, Any]:
    initialize_database()
    products, part_results, discovery_report = fetch_all_discovered_products_with_report()
    synced = 0
    page_errors: list[dict[str, str]] = []

    for product in products:
        try:
            enriched = _enrich(product)
            save_document(product_to_document(enriched))
            _save_catalog_item(enriched)
            synced += 1
        except Exception as exc:
            page_errors.append({
                "uid": product.uid,
                "title": product.title,
                "url": product.url,
                "error": str(exc),
            })

    completeness = build_catalog_completeness_report(
        products,
        part_results,
        configured_store_blocks=discovery_report.total_candidates,
        duplicate_products_across_blocks=sum(part.duplicates for part in part_results),
        source_reports=getattr(discovery_report, "source_reports", ()),
    )

    return {
        "store_blocks": len(part_results),
        "discovered": len(products),
        "synced": synced,
        "errors_count": len(page_errors),
        "errors": page_errors,
        "parts": part_results,
        "discovery_report": discovery_report,
        "completeness": completeness,
        "success": bool(products) and synced > 0 and completeness.complete,
    }


def print_summary(result: dict[str, Any]) -> None:
    print("=" * 72)
    print("AI BODHI VERIFIED PRODUCT CATALOG SYNC")
    print("=" * 72)
    print(f"Store blocks: {result.get('store_blocks', 0)}")
    print(f"Discovered:   {result.get('discovered', 0)}")
    print(f"Synced:       {result.get('synced', 0)}")
    print(f"Errors:       {result.get('errors_count', 0)}")
    discovery = result.get("discovery_report")
    if discovery is not None:
        print("\nDiscovery:")
        print(f"- Shop URL:              {discovery.shop_url}")
        print(f"- HTML loaded:           {discovery.html_loaded}")
        print(f"- HTML size:             {discovery.html_size}")
        print(f"- HTML candidates:       {discovery.html_candidates}")
        print(f"- Configured candidates: {discovery.configured_candidates}")
        print(f"- Total candidates:      {discovery.total_candidates}")
        if discovery.error:
            print(f"- HTML error:            {discovery.error}")
        print("\nCatalog sources:")
        for source in getattr(discovery, "source_reports", ()):
            status = "OK" if source.html_loaded and not source.error else "ERROR"
            print(f"- {status} {source.name}: refs={source.product_references} blocks={source.store_blocks} url={source.url}")
            if source.error:
                print(f"  {source.error}")
    print("\nStore blocks:")
    for part in result.get("parts", []):
        status = "ERROR" if part.error else "OK"
        print(
            f"- {status} recid={part.recid} "
            f"storepartuid={part.storepartuid} "
            f"received={part.received_total} "
            f"expected={part.expected_total} "
            f"pages={part.pages} "
            f"unique_added={part.unique_added} "
            f"duplicates={part.duplicates}"
        )
        if part.error:
            print(f"  {part.error}")

    completeness = result.get("completeness")
    if completeness is not None:
        print("\nCompleteness:")
        print(f"- Unique products:       {completeness.unique_products}")
        print(f"- Received across parts: {completeness.received_products_total}")
        print(f"- Expected across parts: {completeness.expected_products_total}")
        print(f"- Complete:              {completeness.complete}")
        print("\nCategories:")
        for category, count in completeness.category_counts.items():
            print(f"- {category}: {count}")
        if completeness.warnings:
            print("\nWarnings:")
            for warning in completeness.warnings:
                print(f"- {warning}")

    for error in result.get("errors", []):
        print(f"- {error.get('title')}: {error.get('error')}")


if __name__ == "__main__":
    result = sync_product_catalog()
    print_summary(result)
    if not result.get("success"):
        raise SystemExit(1)
