from backend.structured_catalog import (
    ALLOWED_CATALOG_ITEM_TYPES,
    CatalogItemType,
    CatalogQuery,
    UnifiedCatalogRepository,
)


def main() -> None:
    repository = UnifiedCatalogRepository()
    items = []
    for item_type in CatalogItemType:
        items.extend(
            repository.list_items(
                CatalogQuery(item_types=(item_type,), limit=100)
            )
        )

    actual_types = {item.item_type for item in items}
    outside = actual_types - ALLOWED_CATALOG_ITEM_TYPES

    print("=" * 72)
    print("AI BODHI UNIFIED CATALOG DIAGNOSTICS")
    print("=" * 72)
    print("Allowed types:", ", ".join(sorted(item.value for item in ALLOWED_CATALOG_ITEM_TYPES)))
    print("Items inspected:", len(items))
    print("Outside boundary:", len(outside))

    if outside:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
