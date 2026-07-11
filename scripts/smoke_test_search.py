from __future__ import annotations

from backend.rag.dynamic_query_router import (
    reload_catalog_index,
    route_query,
)


QUERIES = [
    "Хочу статую Будды",
    "Ищу амулет Будды",
    "Нужны четки",
    "Есть ваджра?",
    "Покажи тханку",
    "Нужна поющая чаша",
    "Хочу на Кайлас",
    "Есть поездка в Непал?",
    "Поход в Лапчи",
    "Статуя Зеленой Тары",
    "Амулет Ченрезига",
    "Хочу подарок буддисту",
    "Нужен подарок учителю",
    "Хочу защитный амулет",
    "Ищу предмет для домашнего алтаря",
    "Есть велосипед?",
    "стату будды",
    "четкии",
    "кайлос",
]


def main() -> None:
    reload_catalog_index()

    print("=" * 100)
    print("AI BODHI SEARCH SMOKE TEST")
    print("=" * 100)

    for query in QUERIES:
        result = route_query(query)

        print(f"\nЗапрос: {query}")
        print(f"Intent: {result.intent}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reason: {result.reason}")
        print(f"Matched: {result.matched_title or '-'}")
        print(f"URL: {result.matched_url or '-'}")


if __name__ == "__main__":
    main()
