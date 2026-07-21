from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from backend.integrations.product_catalog_sources import (
    CatalogSourceReport, extract_product_uids, fetch_source_html, load_catalog_sources,
)
from backend.integrations.tilda_store_api import StoreProduct, fetch_all_products, product_to_document
from backend.integrations.tilda_store_discovery import StorePart, discover_store_parts_from_html
from backend.storage.database import save_document

@dataclass(frozen=True, slots=True)
class StorePartResult:
    storepartuid: str
    recid: str
    expected_total: int | None
    received_total: int
    pages: int
    error: str | None = None
    unique_added: int = 0
    duplicates: int = 0
    source_name: str = ""


def fetch_all_discovered_products_with_report(shop_url: str | None = None):
    sources = load_catalog_sources()
    products_by_uid: dict[str, StoreProduct] = {}
    categories_by_uid: dict[str, str] = {}
    part_results: list[StorePartResult] = []
    source_reports: list[CatalogSourceReport] = []
    seen_parts: set[tuple[str, str]] = set()

    for source in sources:
        html = ""
        error = None
        parts: list[StorePart] = []
        refs: set[str] = set()
        try:
            html = fetch_source_html(source.url)
            refs = extract_product_uids(html)
            parts = discover_store_parts_from_html(html)
        except Exception as exc:
            error = str(exc)
        for item in source.fallback_store_parts:
            parts.append(StorePart(str(item["storepartuid"]), str(item["recid"]), "configured_fallback"))
        dedup_parts = {(part.storepartuid, part.recid): part for part in parts}
        source_reports.append(CatalogSourceReport(source.name, source.url, source.category, source.required, bool(html), len(html), len(refs), len(dedup_parts), error))
        if source.category:
            for uid in refs:
                categories_by_uid.setdefault(uid, source.category)
        for part in dedup_parts.values():
            key = (part.storepartuid, part.recid)
            if key in seen_parts:
                continue
            seen_parts.add(key)
            try:
                products, metadata = fetch_all_products(storepartuid=part.storepartuid, recid=part.recid)
                before = len(products_by_uid)
                duplicates = 0
                for product in products:
                    if product.uid in products_by_uid:
                        duplicates += 1
                    products_by_uid[product.uid] = product
                part_results.append(StorePartResult(part.storepartuid, part.recid, metadata.get("expected_total"), metadata.get("received_total",0), metadata.get("pages",0), unique_added=len(products_by_uid)-before, duplicates=duplicates, source_name=source.name))
            except Exception as exc:
                part_results.append(StorePartResult(part.storepartuid, part.recid, None, 0, 0, error=str(exc), source_name=source.name))

    products = []
    for uid, product in products_by_uid.items():
        category = product.category or categories_by_uid.get(uid, "")
        products.append(replace(product, category=category))
    products.sort(key=lambda p: p.title.lower())
    discovery_report = type("MultiSourceDiscoveryReport", (), {
        "shop_url": sources[0].url if sources else "",
        "html_loaded": any(r.html_loaded for r in source_reports),
        "html_size": sum(r.html_size for r in source_reports),
        "html_candidates": sum(r.store_blocks for r in source_reports),
        "configured_candidates": sum(len(s.fallback_store_parts) for s in sources),
        "total_candidates": len(seen_parts),
        "error": None,
        "source_reports": tuple(source_reports),
    })()
    return products, part_results, discovery_report


def fetch_all_discovered_products(shop_url: str | None = None):
    products, parts, _ = fetch_all_discovered_products_with_report(shop_url)
    return products, parts


def sync_all_discovered_products(shop_url: str | None = None) -> dict[str, Any]:
    products, parts, report = fetch_all_discovered_products_with_report(shop_url)
    synced = 0
    errors = []
    for product in products:
        try:
            save_document(product_to_document(product)); synced += 1
        except Exception as exc:
            errors.append({"uid":product.uid,"title":product.title,"error":str(exc)})
    return {"store_blocks":len(parts),"unique_products":len(products),"synced":synced,"errors_count":len(errors),"errors":errors,"parts":parts,"discovery_report":report}
