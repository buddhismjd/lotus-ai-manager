from backend.catalog.collection_builder import CollectionItem
from backend.catalog.collection_ranking import rank_collection


def main() -> None:
    items = [
        CollectionItem(id="2", title="Статуя Зелёной Тары", url=None),
        CollectionItem(id="1", title="Статуя Белой Тары", url=None),
    ]
    ranked = rank_collection("Белая Тара", items)
    assert ranked[0].id == "1"
    assert CollectionItem(id="x", title="Товар", url=None).button_label == "Открыть товар"
    print("ranking: OK")
    print("rich_card_contract: OK")


if __name__ == "__main__":
    main()
