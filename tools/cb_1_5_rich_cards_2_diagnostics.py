from backend.catalog.collection_builder import CollectionItem
from backend.catalog.commercial_cards import commercial_card


def main() -> None:
    cases = (
        ("product", "Открыть товар"),
        ("tour", "Открыть тур"),
        ("service", "Открыть услугу"),
    )
    for item_type, expected_label in cases:
        card = commercial_card(CollectionItem(
            id=item_type,
            title=item_type,
            url=f"https://example.test/{item_type}",
            item_type=item_type,
        ))
        assert card["card_version"] == "2.0"
        assert card["actions"][0]["label"] == expected_label
        print(f"[OK] {item_type}: {expected_label}")
    print("CB-1.5 Rich Cards 2.0 diagnostics: OK")


if __name__ == "__main__":
    main()
