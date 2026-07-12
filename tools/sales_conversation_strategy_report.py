from backend.catalog.repositories import TourRepository
from backend.sales_assistant.strategy import choose_strategy, filter_tours


def main() -> None:
    tours = TourRepository().list_all()
    print("AI BODHI MVP-1.3 — SALES CONVERSATION STRATEGY REPORT")
    print(f"Published tours: {len(tours)}")
    for month in range(1, 13):
        decision = choose_strategy(f"Какие туры в {month} месяце", "tour")
        # Numeric month phrasing is not semantic input; construct explicit decision.
        from backend.sales_assistant.strategy import StrategyDecision
        count = len(filter_tours(tours, StrategyDecision("tour_list", month=month)))
        if count:
            print(f"- month {month}: {count}")


if __name__ == "__main__":
    main()
