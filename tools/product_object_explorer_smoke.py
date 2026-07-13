from backend.catalog.explorer.product_object_explorer import explore_product_objects


def main() -> None:
    exploration = explore_product_objects(
        [
            {
                "uid": 1,
                "title": "Smoke product",
                "gallery": [{"img": "image.jpg"}],
                "editions": [{"price": "100", "quantity": "1"}],
            }
        ]
    )
    required = {"uid", "title", "gallery[].img", "editions[].price"}
    missing = sorted(required - set(exploration.field_coverage))
    if missing:
        raise SystemExit(f"SMOKE FAILED: missing paths {missing}")
    print("SMOKE PASSED")
    print(f"Paths: {len(exploration.field_coverage)}")


if __name__ == "__main__":
    main()
