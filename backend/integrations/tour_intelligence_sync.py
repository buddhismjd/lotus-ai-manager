from __future__ import annotations

from typing import Any

from backend.catalog.repositories import TourRepository
from backend.tours.intelligence import build_tour_profile
from backend.tours.profiles import (
    get_tour_profile_stats,
    initialize_tour_profiles,
    save_tour_profile,
)


def sync_tour_profiles() -> dict[str, Any]:
    initialize_tour_profiles()
    tours = TourRepository().list_all()

    saved = 0
    errors: list[dict[str, str]] = []

    for tour in tours:
        try:
            save_tour_profile(build_tour_profile(tour))
            saved += 1
        except Exception as exc:
            errors.append(
                {
                    "title": str(getattr(tour, "title", "") or ""),
                    "url": str(getattr(tour, "url", "") or ""),
                    "error": str(exc),
                }
            )

    return {
        "repository_tours": len(tours),
        "profiles_saved": saved,
        "errors_count": len(errors),
        "errors": errors,
        "stats": get_tour_profile_stats(),
    }


def print_summary(result: dict[str, Any]) -> None:
    stats = result.get("stats") or {}

    print("=" * 72)
    print("AI BODHI TOUR INTELLIGENCE")
    print("=" * 72)
    print(f"Repository tours:  {result.get('repository_tours', 0)}")
    print(f"Profiles saved:    {result.get('profiles_saved', 0)}")
    print(f"Errors:            {result.get('errors_count', 0)}")
    print(f"With country:      {stats.get('with_country', 0)}")
    print(f"With destination:  {stats.get('with_destination', 0)}")
    print(f"With practice:     {stats.get('with_practice', 0)}")
    print(f"With altitude:     {stats.get('with_altitude', 0)}")

    if result.get("errors"):
        print("\nErrors:")

        for error in result["errors"]:
            print(
                f"- {error.get('title')} "
                f"{error.get('url')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    print_summary(sync_tour_profiles())
