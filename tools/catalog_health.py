from __future__ import annotations

from collections import Counter
from pathlib import Path

from backend.catalog.product_profiles import (
    get_profile_stats,
    list_product_profiles,
)
from backend.catalog.repositories import ProductRepository


def main() -> None:
    products = ProductRepository().list_all()
    profiles = list_product_profiles()
    stats = get_profile_stats()

    product_ids = {
        str(getattr(product, "source_id", "") or "")
        for product in products
    }

    profile_types = Counter(
        profile.product_type or "unknown"
        for profile in profiles
    )

    entity_count = sum(
        1
        for profile in profiles
        if profile.primary_entity
    )
    usage_count = sum(
        1
        for profile in profiles
        if profile.usages
    )
    material_count = sum(
        1
        for profile in profiles
        if profile.materials
    )

    print("=" * 72)
    print("AI BODHI CATALOG HEALTH")
    print("=" * 72)
    print(f"Repository products: {len(products)}")
    print(f"Product profiles:    {len(profiles)}")
    print(f"Typed profiles:      {stats.get('typed', 0)}")
    print(f"Unknown type:        {stats.get('unknown_type', 0)}")
    print(f"With entity:         {entity_count}")
    print(f"With usage:          {usage_count}")
    print(f"With material:       {material_count}")

    print("\nProfiles by type:")
    for product_type, count in profile_types.most_common():
        print(f"  {product_type}: {count}")

    if len(profiles) and profile_types:
        dominant_type, dominant_count = profile_types.most_common(1)[0]
        share = dominant_count / len(profiles)

        if share >= 0.80:
            print(
                "\nWARNING: one product type dominates "
                f"{share:.0%} of profiles: {dominant_type}"
            )
            print(
                "This may mean the connector is reading only one "
                "Tilda store block/storepartuid."
            )


if __name__ == "__main__":
    main()
