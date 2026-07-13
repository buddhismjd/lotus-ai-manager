from backend.catalog.explorer.product_object_explorer import run_product_object_explorer


def main() -> None:
    exploration, paths, invalid = run_product_object_explorer()
    print("=" * 72)
    print("AI BODHI CAT-003 PRODUCT OBJECT EXPLORER DIAGNOSTICS")
    print("=" * 72)
    print(f"Raw products:     {exploration.total_products}")
    print(f"Valid products:   {exploration.valid_products}")
    print(f"Invalid products: {exploration.invalid_products}")
    print(f"Discovered paths: {len(exploration.field_coverage)}")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    if invalid:
        print("\nInvalid snapshots:")
        for item in invalid:
            print(f"- {item['product_uid']}: {item['error']}")
    if exploration.valid_products == 0 or invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
