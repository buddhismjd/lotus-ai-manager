from __future__ import annotations

from typing import Any

from backend.catalog.product_profiles import (
    get_profile_stats,
    initialize_product_profiles,
    save_product_profile,
)
from backend.integrations.catalog_intelligence_sync import (
    build_product_profile,
)
from backend.integrations.tilda_store_multi_sync import (
    fetch_all_discovered_products,
)


def sync_all_catalog_intelligence() -> dict[str, Any]:
    initialize_product_profiles()
    products, part_results = fetch_all_discovered_products()

    saved = 0
    errors: list[dict[str, str]] = []

    for product in products:
        try:
            save_product_profile(build_product_profile(product))
            saved += 1
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
        "profiles_saved": saved,
        "errors_count": len(errors),
        "errors": errors,
        "profile_stats": get_profile_stats(),
        "parts": part_results,
    }


def print_summary(result: dict[str, Any]) -> None:
    stats = result.get("profile_stats") or {}

    print("=" * 72)
    print("AI BODHI FULL CATALOG INTELLIGENCE")
    print("=" * 72)
    print(f"Store blocks:     {result.get('store_blocks', 0)}")
    print(f"Unique products:  {result.get('unique_products', 0)}")
    print(f"Profiles saved:   {result.get('profiles_saved', 0)}")
    print(f"Errors:           {result.get('errors_count', 0)}")
    print(f"Typed profiles:   {stats.get('typed', 0)}")
    print(f"Unknown type:     {stats.get('unknown_type', 0)}")
    print(f"With entity:      {stats.get('with_entity', 0)}")

    print("\nProfiles by type:")

    for product_type, count in (stats.get("by_type") or {}).items():
        print(f"  {product_type}: {count}")


if __name__ == "__main__":
    print_summary(sync_all_catalog_intelligence())
