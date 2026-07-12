from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

CatalogStatus = Literal["published", "planned", "draft", "unavailable"]


@dataclass(frozen=True, slots=True)
class TourSchedule:
    start_day: int
    start_month: int
    end_day: int
    end_month: int
    year: int | None = None
    source_text: str = ""

    def includes_month(self, month: int) -> bool:
        if not 1 <= month <= 12:
            return False
        if self.start_month <= self.end_month:
            return self.start_month <= month <= self.end_month
        return month >= self.start_month or month <= self.end_month


@dataclass(frozen=True, slots=True)
class StructuredTour:
    id: str
    title: str
    url: str
    description: str = ""
    status: CatalogStatus = "published"
    schedule: TourSchedule | None = None
    duration_days: int | None = None
    countries: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    destinations: tuple[str, ...] = ()
    aspects: tuple[str, ...] = ()
    practices: tuple[str, ...] = ()
    teachers: tuple[str, ...] = ()
    difficulty: str | None = None
    price: Decimal | None = None
    currency: str = "RUR"
    keywords: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def country(self) -> str | None:
        return self.countries[0] if self.countries else None

    @property
    def start_date(self) -> None:
        # Compatibility surface for existing formatters. Calendar years are
        # intentionally not invented when the source page omits a year.
        return None

    @property
    def end_date(self) -> None:
        return None

    def occurs_in_month(self, month: int) -> bool:
        return bool(self.schedule and self.schedule.includes_month(month))


@dataclass(frozen=True, slots=True)
class StructuredProduct:
    id: str
    title: str
    url: str
    description: str = ""
    status: CatalogStatus = "published"
    category: str | None = None
    price: Decimal | None = None
    currency: str = "RUR"
    available: bool = True
    materials: tuple[str, ...] = ()
    aspects: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StructuredService:
    id: str
    title: str
    url: str
    description: str = ""
    status: CatalogStatus = "published"
    specialist: str | None = None
    duration_minutes: int | None = None
    price: Decimal | None = None
    currency: str = "RUR"
    topics: tuple[str, ...] = ()
    booking_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
