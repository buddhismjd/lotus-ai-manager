from backend.catalog.collection_builder import CollectionItem
from backend.catalog.commercial_cards import commercial_card


def main() -> None:
    print("CB-1.5 Rich Cards 2.0 report")
    for item_type in ("tour", "product", "service"):
        card = commercial_card(CollectionItem(
            id=item_type,
            title=f"Demo {item_type}",
            url=f"https://example.test/{item_type}",
            item_type=item_type,
        ))
        action = card["actions"][0]
        print(f"- {item_type}: version={card['card_version']}; action={action['label']}")


if __name__ == "__main__":
    main()
