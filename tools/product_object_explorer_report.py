from backend.catalog.explorer.product_object_explorer import run_product_object_explorer


KEY_PATHS = (
    "uid",
    "title",
    "brand",
    "price",
    "quantity",
    "gallery",
    "gallery[].img",
    "characteristics",
    "properties",
    "editions",
    "editions[].price",
    "editions[].quantity",
    "partuids",
)


def main() -> None:
    exploration, paths, invalid = run_product_object_explorer()
    total = exploration.valid_products

    print("AI BODHI CAT-003 PRODUCT OBJECT EXPLORER REPORT")
    print(f"Products: {total}")
    print(f"Invalid snapshots: {len(invalid)}")
    print(f"Discovered paths: {len(exploration.field_coverage)}")
    print("\nFIELD COVERAGE")
    for path in KEY_PATHS:
        item = exploration.field_coverage.get(path)
        count = item["products"] if item else 0
        print(f"- {path}: {count}/{total}")

    statistics = exploration.catalog_statistics
    for field in ("characteristics", "properties"):
        section = statistics[field]
        print(f"\n{field.upper()} LABELS")
        if section["labels"]:
            for label, count in section["labels"].items():
                print(f"- {label}: {count}")
        else:
            print("- no named entries found")

    print("\nARTIFACTS")
    for name, path in paths.items():
        print(f"- {name}: {path}")

    if total == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
