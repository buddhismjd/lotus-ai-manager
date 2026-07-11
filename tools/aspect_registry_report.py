from __future__ import annotations

from backend.catalog.product_profiles import list_product_profiles
from backend.knowledge.aspect_migration import canonicalize_profile_aspects
from backend.knowledge.aspect_registry import load_aspect_registry
from backend.tours.profiles import list_tour_profiles


def main() -> None:
    registry = load_aspect_registry()
    products = list_product_profiles()
    tours = list_tour_profiles()

    matched_product_profiles = 0
    unmatched_product_values: set[str] = set()

    for profile in products:
        canonical = canonicalize_profile_aspects(profile)

        if canonical:
            matched_product_profiles += 1
        else:
            values = getattr(profile, "aspects", None)

            if values is None:
                values = getattr(profile, "entities", ())

            unmatched_product_values.update(values or ())

    matched_tour_profiles = 0
    unmatched_tour_values: set[str] = set()

    for profile in tours:
        canonical = canonicalize_profile_aspects(profile)

        if canonical:
            matched_tour_profiles += 1
        elif profile.aspects:
            unmatched_tour_values.update(profile.aspects)

    print("=" * 72)
    print("AI BODHI ASPECT REGISTRY REPORT")
    print("=" * 72)
    print(f"Аспектов в реестре:               {len(registry)}")
    print(f"Профилей товаров с aspect_id:     {matched_product_profiles}")
    print(f"Профилей туров с aspect_id:       {matched_tour_profiles}")

    if unmatched_product_values:
        print("\nНеизвестные аспекты товаров:")
        for value in sorted(unmatched_product_values):
            print(f"  - {value}")

    if unmatched_tour_values:
        print("\nНеизвестные аспекты туров:")
        for value in sorted(unmatched_tour_values):
            print(f"  - {value}")


if __name__ == "__main__":
    main()
