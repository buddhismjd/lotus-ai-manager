from __future__ import annotations

from backend.catalog.models import Tour
from backend.structured_catalog.date_parser import parse_duration_days, parse_tour_schedule
from backend.structured_catalog.models import StructuredTour
from backend.tours.profiles import TourProfile


def build_structured_tour(
    tour: Tour,
    profile: TourProfile | None = None,
) -> StructuredTour:
    source = "\n".join(part for part in (tour.title, tour.description) if part)
    schedule = parse_tour_schedule(source)
    duration = (
        profile.duration_days
        if profile and profile.duration_days is not None
        else tour.duration_days or parse_duration_days(tour.title, tour.description)
    )
    countries = profile.countries if profile else (() if not tour.country else (tour.country,))
    regions = profile.regions if profile else (() if not tour.region else (tour.region,))

    return StructuredTour(
        id=tour.id,
        title=tour.title,
        url=tour.url,
        description=tour.description,
        status="published" if tour.metadata.get("page_type") == "tour" else "draft",
        schedule=schedule,
        duration_days=duration,
        countries=countries,
        regions=regions,
        destinations=profile.destinations if profile else (),
        aspects=profile.aspects if profile else (),
        practices=profile.practices if profile else (),
        teachers=profile.teachers if profile else (),
        difficulty=(profile.difficulty if profile else None) or tour.difficulty,
        price=tour.price,
        currency=tour.currency,
        keywords=profile.keywords if profile else tuple(tour.keywords),
        metadata=dict(tour.metadata),
    )
