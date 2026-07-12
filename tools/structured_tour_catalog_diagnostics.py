from __future__ import annotations

from backend.structured_catalog.repositories import StructuredTourRepository


def main() -> int:
    repository = StructuredTourRepository()
    tours = repository.list_all()
    september = repository.list_by_month(9)
    without_schedule = [tour for tour in tours if tour.schedule is None]

    print("=" * 72)
    print("AI BODHI STRUCTURED TOUR CATALOG DIAGNOSTICS")
    print("=" * 72)
    print(f"Published tours: {len(tours)}")
    print(f"September tours: {len(september)}")
    print(f"Without schedule: {len(without_schedule)}")
    print("September titles:")
    for tour in september:
        print(f"- {tour.title}: {tour.schedule.source_text if tour.schedule else '-'}")

    return 0 if len(september) >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
