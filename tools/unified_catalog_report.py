from backend.structured_catalog import CatalogItemType, CatalogQuery, UnifiedCatalogRepository


def main() -> None:
    repository = UnifiedCatalogRepository()
    counts: dict[str, int] = {}

    for item_type in CatalogItemType:
        counts[item_type.value] = len(
            repository.list_items(
                CatalogQuery(item_types=(item_type,), limit=100)
            )
        )

    print("AI BODHI UNIFIED CATALOG REPORT")
    print("Total items inspected:", sum(counts.values()))
    for item_type, count in sorted(counts.items()):
        print(f"- {item_type}: {count}")
    print("Knowledge boundary: products, tours, psychologist service only")


if __name__ == "__main__":
    main()
