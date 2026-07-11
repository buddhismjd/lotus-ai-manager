from __future__ import annotations

import re

from backend.catalog.repositories import ProductRepository
from backend.rag.dynamic_query_router import (
    reload_catalog_index,
    route_query,
)


QUERIES = [
    "У Вас есть Дзамбала?",
    "Восьмиконечная вадра нужна",
    "Ищу статую Будду около 45 см.",
]


def normalize(text: str) -> str:
    return (text or "").lower().replace("ё", "е")


def find_catalog_evidence() -> None:
    products = ProductRepository().list_all()

    print("\n" + "=" * 72)
    print("CATALOG EVIDENCE")
    print("=" * 72)

    dzambala = [
        product
        for product in products
        if "дзамб" in normalize(
            " ".join(
                [
                    product.title or "",
                    product.description or "",
                    product.category or "",
                ]
            )
        )
    ]

    print("\nДзамбала:")
    if dzambala:
        for product in dzambala[:20]:
            print(f"- {product.title} | {product.url}")
    else:
        print("- Совпадений в каталоге нет")

    vajra = [
        product
        for product in products
        if any(
            token in normalize(
                " ".join(
                    [
                        product.title or "",
                        product.description or "",
                        product.category or "",
                    ]
                )
            )
            for token in ("ваджр", "вадр", "дордж")
        )
    ]

    print("\nВаджра / вадра / дордже:")
    if vajra:
        for product in vajra[:20]:
            print(f"- {product.title} | {product.url}")
    else:
        print("- Совпадений в каталоге нет")

    buddha_45 = []

    for product in products:
        searchable = normalize(
            " ".join(
                [
                    product.title or "",
                    product.description or "",
                    product.category or "",
                ]
            )
        )

        if "стату" not in searchable:
            continue

        if "будд" not in searchable:
            continue

        dimensions = [
            int(value)
            for value in re.findall(
                r"(?<!\d)(\d{1,3})\s*(?:см|cm)\b",
                searchable,
            )
        ]

        if any(abs(value - 45) <= 5 for value in dimensions):
            buddha_45.append((product, dimensions))

    print("\nСтатуи Будды около 45 см (допуск ±5 см):")
    if buddha_45:
        for product, dimensions in buddha_45[:20]:
            print(
                f"- {product.title} | размеры={dimensions} | "
                f"{product.url}"
            )
    else:
        print("- Подходящих размеров в описаниях не найдено")


def main() -> None:
    reload_catalog_index()

    print("=" * 72)
    print("AI BODHI USER QUERY TEST")
    print("=" * 72)

    for query in QUERIES:
        result = route_query(query)

        print(f"\nЗапрос: {query}")
        print(f"Intent: {result.intent}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reason: {result.reason}")
        print(f"Matched: {result.matched_title or '-'}")
        print(f"URL: {result.matched_url or '-'}")

    find_catalog_evidence()


if __name__ == "__main__":
    main()
