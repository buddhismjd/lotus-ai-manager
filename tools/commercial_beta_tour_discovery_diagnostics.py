from __future__ import annotations

from backend.sales_assistant.tour_discovery import understand_tour_query


def main() -> None:
    samples = (
        "Какие туры есть?",
        "Хочу в Непал",
        "Хочу на Кайлас",
    )
    print("=" * 72)
    print("AI BODHI COMMERCIAL BETA TOUR DISCOVERY DIAGNOSTICS")
    print("=" * 72)
    for sample in samples:
        parsed = understand_tour_query(sample)
        print(f"Query: {sample}")
        print(f"Directions: {parsed.directions or '-'}")
        print(f"Destinations: {parsed.destinations or '-'}")
    print("Imposed month/season questions: False")
    print("Imposed trekking/difficulty questions: False")


if __name__ == "__main__":
    main()
