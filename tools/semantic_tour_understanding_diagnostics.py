from __future__ import annotations

from backend.sales_assistant.tour_discovery import understand_tour_query


def main() -> None:
    guru = understand_tour_query("А по местам Гуру Ринпоче возите?")
    new_year = understand_tour_query("Какие туры есть в новогодние праздники?")

    print("AI BODHI SEMANTIC TOUR UNDERSTANDING DIAGNOSTICS")
    print(f"Guru Rinpoche aspects: {guru.aspects}")
    print(f"New Year periods: {new_year.natural_periods}")
    print("Imposed questionnaire filters: False")


if __name__ == "__main__":
    main()
