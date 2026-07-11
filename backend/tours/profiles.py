from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.storage.database import get_connection


TOUR_PROFILE_SCHEMA = """
CREATE TABLE IF NOT EXISTS tour_profiles (
    tour_id TEXT PRIMARY KEY,
    countries_json TEXT NOT NULL DEFAULT '[]',
    regions_json TEXT NOT NULL DEFAULT '[]',
    destinations_json TEXT NOT NULL DEFAULT '[]',
    aspects_json TEXT NOT NULL DEFAULT '[]',
    practices_json TEXT NOT NULL DEFAULT '[]',
    teachers_json TEXT NOT NULL DEFAULT '[]',
    difficulty TEXT,
    duration_days INTEGER,
    min_altitude_m INTEGER,
    max_altitude_m INTEGER,
    keywords_json TEXT NOT NULL DEFAULT '[]',
    source_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tour_profiles_difficulty
    ON tour_profiles(difficulty);
"""


@dataclass(frozen=True, slots=True)
class TourProfile:
    tour_id: str
    countries: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    destinations: tuple[str, ...] = ()
    aspects: tuple[str, ...] = ()
    practices: tuple[str, ...] = ()
    teachers: tuple[str, ...] = ()
    difficulty: str | None = None
    duration_days: int | None = None
    min_altitude_m: int | None = None
    max_altitude_m: int | None = None
    keywords: tuple[str, ...] = ()
    source_hash: str | None = None

    def to_search_text(self) -> str:
        parts: list[str] = []

        if self.countries:
            parts.append("Страны: " + ", ".join(self.countries))
        if self.regions:
            parts.append("Регионы: " + ", ".join(self.regions))
        if self.destinations:
            parts.append("Направления: " + ", ".join(self.destinations))
        if self.aspects:
            parts.append("Аспекты: " + ", ".join(self.aspects))
        if self.practices:
            parts.append("Практики: " + ", ".join(self.practices))
        if self.teachers:
            parts.append("Учителя: " + ", ".join(self.teachers))
        if self.difficulty:
            parts.append(f"Сложность: {self.difficulty}")
        if self.duration_days is not None:
            parts.append(f"Продолжительность: {self.duration_days} дней")
        if self.min_altitude_m is not None:
            parts.append(f"Минимальная высота: {self.min_altitude_m} м")
        if self.max_altitude_m is not None:
            parts.append(f"Максимальная высота: {self.max_altitude_m} м")
        if self.keywords:
            parts.append("Ключевые слова: " + ", ".join(self.keywords))

        return "\n".join(parts)


def initialize_tour_profiles() -> None:
    with get_connection() as connection:
        connection.executescript(TOUR_PROFILE_SCHEMA)


def _to_json(values: tuple[str, ...]) -> str:
    return json.dumps(
        list(dict.fromkeys(values)),
        ensure_ascii=False,
    )


def _from_json(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()

    loaded = json.loads(value)

    if not isinstance(loaded, list):
        return ()

    return tuple(
        str(item)
        for item in loaded
        if str(item).strip()
    )


def save_tour_profile(profile: TourProfile) -> None:
    initialize_tour_profiles()
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO tour_profiles (
                tour_id,
                countries_json,
                regions_json,
                destinations_json,
                aspects_json,
                practices_json,
                teachers_json,
                difficulty,
                duration_days,
                min_altitude_m,
                max_altitude_m,
                keywords_json,
                source_hash,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tour_id) DO UPDATE SET
                countries_json = excluded.countries_json,
                regions_json = excluded.regions_json,
                destinations_json = excluded.destinations_json,
                aspects_json = excluded.aspects_json,
                practices_json = excluded.practices_json,
                teachers_json = excluded.teachers_json,
                difficulty = excluded.difficulty,
                duration_days = excluded.duration_days,
                min_altitude_m = excluded.min_altitude_m,
                max_altitude_m = excluded.max_altitude_m,
                keywords_json = excluded.keywords_json,
                source_hash = excluded.source_hash,
                updated_at = excluded.updated_at
            """,
            (
                profile.tour_id,
                _to_json(profile.countries),
                _to_json(profile.regions),
                _to_json(profile.destinations),
                _to_json(profile.aspects),
                _to_json(profile.practices),
                _to_json(profile.teachers),
                profile.difficulty,
                profile.duration_days,
                profile.min_altitude_m,
                profile.max_altitude_m,
                _to_json(profile.keywords),
                profile.source_hash,
                now,
                now,
            ),
        )


def get_tour_profile(tour_id: str) -> TourProfile | None:
    initialize_tour_profiles()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM tour_profiles
            WHERE tour_id = ?
            LIMIT 1
            """,
            (tour_id,),
        ).fetchone()

    if row is None:
        return None

    return TourProfile(
        tour_id=row["tour_id"],
        countries=_from_json(row["countries_json"]),
        regions=_from_json(row["regions_json"]),
        destinations=_from_json(row["destinations_json"]),
        aspects=_from_json(row["aspects_json"]),
        practices=_from_json(row["practices_json"]),
        teachers=_from_json(row["teachers_json"]),
        difficulty=row["difficulty"],
        duration_days=row["duration_days"],
        min_altitude_m=row["min_altitude_m"],
        max_altitude_m=row["max_altitude_m"],
        keywords=_from_json(row["keywords_json"]),
        source_hash=row["source_hash"],
    )


def list_tour_profiles() -> list[TourProfile]:
    initialize_tour_profiles()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT tour_id
            FROM tour_profiles
            ORDER BY tour_id
            """
        ).fetchall()

    result: list[TourProfile] = []

    for row in rows:
        profile = get_tour_profile(row["tour_id"])

        if profile is not None:
            result.append(profile)

    return result


def get_tour_profile_stats() -> dict[str, Any]:
    profiles = list_tour_profiles()

    return {
        "total": len(profiles),
        "with_country": sum(1 for p in profiles if p.countries),
        "with_destination": sum(1 for p in profiles if p.destinations),
        "with_practice": sum(1 for p in profiles if p.practices),
        "with_altitude": sum(
            1 for p in profiles if p.max_altitude_m is not None
        ),
    }


__all__ = [
    "TourProfile",
    "initialize_tour_profiles",
    "save_tour_profile",
    "get_tour_profile",
    "list_tour_profiles",
    "get_tour_profile_stats",
]
