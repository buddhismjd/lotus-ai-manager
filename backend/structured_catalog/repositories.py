from __future__ import annotations

from backend.catalog.repositories import TourRepository
from backend.structured_catalog.builders import build_structured_tour
from backend.structured_catalog.models import StructuredTour
from backend.tours.profiles import get_tour_profile


class StructuredTourRepository:
    """Read model joining published tours with Tour Intelligence profiles."""

    def __init__(self, source: TourRepository | None = None) -> None:
        self._source = source or TourRepository()

    def list_all(self, published_only: bool = True) -> list[StructuredTour]:
        tours = [
            build_structured_tour(tour, get_tour_profile(tour.id))
            for tour in self._source.list_all(enabled_only=published_only)
        ]
        return sorted(tours, key=self._sort_key)

    def list_scheduled(self) -> list[StructuredTour]:
        """Return every published tour that has real schedule data."""
        return [tour for tour in self.list_all() if tour.schedule is not None]

    def search(self, query: str) -> list[StructuredTour]:
        """Natural-query discovery without imposed questionnaire filters."""
        from backend.sales_assistant.tour_discovery import filter_tours_for_query

        return filter_tours_for_query(self.list_all(), query)

    def list_by_month(self, month: int) -> list[StructuredTour]:
        if not 1 <= month <= 12:
            raise ValueError("month must be between 1 and 12")
        return [tour for tour in self.list_all() if tour.occurs_in_month(month)]

    def get_by_id(self, tour_id: str) -> StructuredTour | None:
        tour = self._source.get_by_id(tour_id)
        if tour is None:
            return None
        return build_structured_tour(tour, get_tour_profile(tour.id))

    @staticmethod
    def _sort_key(tour: StructuredTour) -> tuple[int, int, str]:
        if tour.schedule is None:
            return (13, 32, tour.title.casefold())
        return (
            tour.schedule.start_month,
            tour.schedule.start_day,
            tour.title.casefold(),
        )
