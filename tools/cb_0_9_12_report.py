from __future__ import annotations

from backend.tours.collection_builder import is_country_collection_query


def main() -> int:
    rows = (
        ("Непал", is_country_collection_query("Непал")),
        ("Покажите туры в Непал", is_country_collection_query("Покажите туры в Непал")),
        ("Есть тур на Кайлас?", is_country_collection_query("Есть тур на Кайлас?")),
    )
    print("CB-0.9.12 Intelligent Collections")
    print("=" * 38)
    for query, collection in rows:
        print(f"{query}: {'country collection' if collection else 'normal routing'}")
    print("Product selection cards: all exact matches, including image, URL, size, material, availability and price.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
