from __future__ import annotations

from collections import Counter

from backend.structured_catalog.repositories import StructuredTourRepository


def main() -> int:
    tours = StructuredTourRepository().list_all()
    months: Counter[int] = Counter()
    for tour in tours:
        if tour.schedule:
            for month in range(1, 13):
                if tour.schedule.includes_month(month):
                    months[month] += 1

    print("AI BODHI MVP-2.0 — STRUCTURED TOUR CATALOG REPORT")
    print(f"Total published tours: {len(tours)}")
    print(f"Tours with schedule: {sum(1 for tour in tours if tour.schedule)}")
    print(f"Tours with duration: {sum(1 for tour in tours if tour.duration_days)}")
    for month, count in sorted(months.items()):
        print(f"- month {month}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
