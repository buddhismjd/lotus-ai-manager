from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class Product:
    id: str
    title: str
    url: str
    category: str | None = None
    description: str = ""
    price: Decimal | None = None
    currency: str = "RUR"
    available: bool = True
    material: str | None = None
    height_cm: float | None = None
    width_cm: float | None = None
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Tour:
    id: str
    title: str
    url: str
    description: str = ""
    country: str | None = None
    region: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_days: int | None = None
    price: Decimal | None = None
    currency: str = "RUR"
    difficulty: str | None = None
    guide: str | None = None
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Consultation:
    id: str
    title: str
    url: str
    specialist: str | None = None
    description: str = ""
    duration_minutes: int | None = None
    price: Decimal | None = None
    currency: str = "RUR"
    topics: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)