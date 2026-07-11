from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.storage.database import get_connection


PROFILE_SCHEMA = """
CREATE TABLE IF NOT EXISTS product_profiles (
    product_id TEXT PRIMARY KEY,
    product_type TEXT,
    primary_entity TEXT,
    entities_json TEXT NOT NULL DEFAULT '[]',
    materials_json TEXT NOT NULL DEFAULT '[]',
    usages_json TEXT NOT NULL DEFAULT '[]',
    traditions_json TEXT NOT NULL DEFAULT '[]',
    synonyms_json TEXT NOT NULL DEFAULT '[]',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    source_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_profiles_type
    ON product_profiles(product_type);

CREATE INDEX IF NOT EXISTS idx_product_profiles_entity
    ON product_profiles(primary_entity);
"""


@dataclass(frozen=True, slots=True)
class ProductProfile:
    product_id: str
    product_type: str | None = None
    primary_entity: str | None = None
    entities: tuple[str, ...] = ()
    materials: tuple[str, ...] = ()
    usages: tuple[str, ...] = ()
    traditions: tuple[str, ...] = ()
    synonyms: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    source_hash: str | None = None

    def to_search_text(self) -> str:
        parts: list[str] = []

        if self.product_type:
            parts.append(f"Тип товара: {self.product_type}")
        if self.primary_entity:
            parts.append(f"Основная сущность: {self.primary_entity}")
        if self.entities:
            parts.append("Сущности: " + ", ".join(self.entities))
        if self.materials:
            parts.append("Материалы: " + ", ".join(self.materials))
        if self.usages:
            parts.append("Назначение: " + ", ".join(self.usages))
        if self.traditions:
            parts.append("Традиции: " + ", ".join(self.traditions))
        if self.synonyms:
            parts.append("Синонимы: " + ", ".join(self.synonyms))
        if self.keywords:
            parts.append("Ключевые слова: " + ", ".join(self.keywords))

        return "\n".join(parts)


def initialize_product_profiles() -> None:
    with get_connection() as connection:
        connection.executescript(PROFILE_SCHEMA)


def _json_tuple(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()

    loaded = json.loads(value)

    if not isinstance(loaded, list):
        return ()

    return tuple(str(item) for item in loaded if str(item).strip())


def _to_json(values: tuple[str, ...]) -> str:
    return json.dumps(
        list(dict.fromkeys(values)),
        ensure_ascii=False,
    )


def save_product_profile(profile: ProductProfile) -> None:
    initialize_product_profiles()
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO product_profiles (
                product_id,
                product_type,
                primary_entity,
                entities_json,
                materials_json,
                usages_json,
                traditions_json,
                synonyms_json,
                keywords_json,
                source_hash,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                product_type = excluded.product_type,
                primary_entity = excluded.primary_entity,
                entities_json = excluded.entities_json,
                materials_json = excluded.materials_json,
                usages_json = excluded.usages_json,
                traditions_json = excluded.traditions_json,
                synonyms_json = excluded.synonyms_json,
                keywords_json = excluded.keywords_json,
                source_hash = excluded.source_hash,
                updated_at = excluded.updated_at
            """,
            (
                profile.product_id,
                profile.product_type,
                profile.primary_entity,
                _to_json(profile.entities),
                _to_json(profile.materials),
                _to_json(profile.usages),
                _to_json(profile.traditions),
                _to_json(profile.synonyms),
                _to_json(profile.keywords),
                profile.source_hash,
                now,
                now,
            ),
        )


def get_product_profile(product_id: str) -> ProductProfile | None:
    initialize_product_profiles()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM product_profiles
            WHERE product_id = ?
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()

    if row is None:
        return None

    return ProductProfile(
        product_id=row["product_id"],
        product_type=row["product_type"],
        primary_entity=row["primary_entity"],
        entities=_json_tuple(row["entities_json"]),
        materials=_json_tuple(row["materials_json"]),
        usages=_json_tuple(row["usages_json"]),
        traditions=_json_tuple(row["traditions_json"]),
        synonyms=_json_tuple(row["synonyms_json"]),
        keywords=_json_tuple(row["keywords_json"]),
        source_hash=row["source_hash"],
    )


def list_product_profiles() -> list[ProductProfile]:
    initialize_product_profiles()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT product_id
            FROM product_profiles
            ORDER BY product_id
            """
        ).fetchall()

    profiles: list[ProductProfile] = []

    for row in rows:
        profile = get_product_profile(row["product_id"])

        if profile is not None:
            profiles.append(profile)

    return profiles


def get_profile_stats() -> dict[str, Any]:
    initialize_product_profiles()

    with get_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS count FROM product_profiles"
        ).fetchone()["count"]

        typed = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM product_profiles
            WHERE product_type IS NOT NULL
              AND product_type != ''
            """
        ).fetchone()["count"]

        entities = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM product_profiles
            WHERE primary_entity IS NOT NULL
              AND primary_entity != ''
            """
        ).fetchone()["count"]

        by_type_rows = connection.execute(
            """
            SELECT product_type, COUNT(*) AS count
            FROM product_profiles
            GROUP BY product_type
            ORDER BY count DESC, product_type ASC
            """
        ).fetchall()

    return {
        "total": int(total),
        "typed": int(typed),
        "with_entity": int(entities),
        "unknown_type": int(total - typed),
        "by_type": {
            (row["product_type"] or "unknown"): int(row["count"])
            for row in by_type_rows
        },
    }


__all__ = [
    "ProductProfile",
    "initialize_product_profiles",
    "save_product_profile",
    "get_product_profile",
    "list_product_profiles",
    "get_profile_stats",
]
