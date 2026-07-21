from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.integrations.product_raw_snapshot import load_raw_snapshot
from backend.integrations.product_snapshot_normalizer import normalize_raw_snapshot
from backend.integrations.product_snapshot_storage import (
    save_normalized_snapshot,
    save_raw_snapshot,
    snapshot_quality_counts,
)
from backend.integrations.tilda_store_multi_sync import (
    fetch_all_discovered_products_with_report,
)
from backend.storage.database import initialize_database


@dataclass(frozen=True, slots=True)
class SnapshotSyncError:
    uid: str
    title: str
    url: str
    error: str


def sync_product_snapshots_v2() -> dict[str, Any]:
    initialize_database()
    products, part_results, discovery_report = (
        fetch_all_discovered_products_with_report()
    )

    synced = 0
    unchanged = 0
    errors: list[SnapshotSyncError] = []

    for product in products:
        try:
            raw = load_raw_snapshot(product.url)
            normalized = normalize_raw_snapshot(raw)
            save_raw_snapshot(raw)
            save_normalized_snapshot(normalized)
            synced += 1
        except Exception as exc:
            errors.append(
                SnapshotSyncError(
                    uid=product.uid,
                    title=product.title,
                    url=product.url,
                    error=str(exc),
                )
            )

    quality = snapshot_quality_counts()

    return {
        "discovered": len(products),
        "synced": synced,
        "unchanged": unchanged,
        "errors_count": len(errors),
        "errors": errors,
        "parts": part_results,
        "discovery_report": discovery_report,
        "quality": quality,
        "success": bool(products) and synced == len(products) and not errors,
    }


def print_snapshot_sync_report(result: dict[str, Any]) -> None:
    print("=" * 72)
    print("AI BODHI PRODUCT SNAPSHOT SYNCHRONIZER V2")
    print("=" * 72)
    print(f"Discovered: {result['discovered']}")
    print(f"Synced:     {result['synced']}")
    print(f"Errors:     {result['errors_count']}")

    quality = result["quality"]
    total = quality.get("total", 0)
    print("\nConfirmed fields:")
    for field in (
        "title", "description", "brand", "sku", "price",
        "primary_image", "quantity",
    ):
        print(f"- {field}: {quality.get(field, 0)}/{total}")

    print("\nUnconfirmed fields:")
    for field in ("category", "material", "height_cm", "availability_status"):
        print(f"- {field}: {quality.get(field, 0)}/{total}")

    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"- {error.uid} {error.title}: {error.error}")


if __name__ == "__main__":
    result = sync_product_snapshots_v2()
    print_snapshot_sync_report(result)
    if not result["success"]:
        raise SystemExit(1)
