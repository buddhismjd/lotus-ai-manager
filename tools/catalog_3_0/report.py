from backend.tours.collection_builder import build_tour_collection


def main() -> None:
    print("CATALOG-3.0 — Country Collections")
    for country in ("Индия", "Непал", "Тибет", "Бутан", "Монголия", "Россия"):
        items = build_tour_collection(f"Что по {country}?")
        print(f"\n{country}: {len(items)}")
        for item in items:
            print(f"  - {item.title}")


if __name__ == "__main__":
    main()
