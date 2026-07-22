from backend.catalog.collection_builder import CollectionItem


def main() -> None:
    product = CollectionItem(
        id="product",
        title="Статуя Белой Тары",
        url="https://example.com/product",
        image_url="https://example.com/image.jpg",
        description="Бронзовая статуя.",
        availability="В наличии",
        button_label="Открыть товар",
        group="В наличии",
    )
    payload = product.to_dict()
    required = {"title", "url", "image_url", "description", "availability", "button_label", "group"}
    assert required <= payload.keys()
    assert all(payload[key] for key in required)
    print("rich_product_card=OK")


if __name__ == "__main__":
    main()
