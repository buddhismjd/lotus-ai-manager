from backend.catalog.collection_builder import build_product_collection
from backend.tours.collection_builder import build_tour_collection


def main() -> None:
    scenarios = (
        ("products", "Есть ли у вас Белая Тара?", build_product_collection),
        ("products", "Есть Ваджра?", build_product_collection),
        ("tours", "Есть поездка в Непал?", build_tour_collection),
    )
    print("AI Bodhi — Catalog Collection Report")
    for kind, query, builder in scenarios:
        items = builder(query)
        print(f"\n[{kind}] {query}\ncount={len(items)}")
        for item in items:
            print(f"- {item.title} | {item.url or 'planned'} | image={bool(item.image_url)}")


if __name__ == "__main__":
    main()
