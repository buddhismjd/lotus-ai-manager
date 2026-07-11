from __future__ import annotations

from backend.tours.profiles import list_tour_profiles


def main() -> None:
    profiles = list_tour_profiles()

    print("=" * 72)
    print("AI BODHI TOUR PROFILE REPORT")
    print("=" * 72)
    print(f"Профилей туров: {len(profiles)}")

    for profile in profiles:
        print(f"\n{profile.tour_id}")
        print(profile.to_search_text() or "Нет структурированных данных")


if __name__ == "__main__":
    main()
