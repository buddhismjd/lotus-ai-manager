from backend.structured_catalog import CatalogItemType, CatalogQuery, UnifiedCatalogRepository


def main() -> None:
    repository = UnifiedCatalogRepository()
    tours = repository.search(CatalogQuery(item_types=(CatalogItemType.TOUR,), text="Кайлас"))
    if not tours:
        raise SystemExit("SMOKE FAILED: Kailas tour not found")
    if any(item.item_type is not CatalogItemType.TOUR for item in tours):
        raise SystemExit("SMOKE FAILED: catalog boundary violated")
    print("SMOKE PASSED")
    print("Tour:", tours[0].title)


if __name__ == "__main__":
    main()
