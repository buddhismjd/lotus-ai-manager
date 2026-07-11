from __future__ import annotations

from backend.catalog.repositories import TourRepository
from backend.tours.intelligence import build_tour_profile


def main() -> None:
    tours = TourRepository().list_all()

    print("=" * 72)
    print("AI BODHI TOUR DATA DIAGNOSTICS")
    print("=" * 72)
    print(f"Туров: {len(tours)}")

    for tour in tours:
        profile = build_tour_profile(tour)
        missing: list[str] = []

        if not profile.countries:
            missing.append("страна")
        if not profile.destinations:
            missing.append("направление")
        if not profile.practices:
            missing.append("практики")
        if profile.duration_days is None:
            missing.append("продолжительность")
        if profile.max_altitude_m is None:
            missing.append("высоты")

        if missing:
            print(f"\n- {tour.title}")
            print("  Не хватает: " + ", ".join(missing))
            print(f"  URL: {tour.url}")


if __name__ == "__main__":
    main()
