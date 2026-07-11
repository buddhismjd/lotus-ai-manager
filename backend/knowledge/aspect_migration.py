from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from backend.knowledge.aspect_registry import (
    canonical_aspect_id,
    canonical_aspect_name,
)


@dataclass(frozen=True, slots=True)
class CanonicalAspect:
    aspect_id: str
    name: str


def canonicalize_aspect_values(
    values: Iterable[str],
) -> tuple[CanonicalAspect, ...]:
    result: list[CanonicalAspect] = []

    for value in values:
        aspect_id = canonical_aspect_id(value)
        name = canonical_aspect_name(value)

        if not aspect_id or not name:
            continue

        item = CanonicalAspect(
            aspect_id=aspect_id,
            name=name,
        )

        if item not in result:
            result.append(item)

    return tuple(result)


def canonicalize_profile_aspects(profile) -> tuple[CanonicalAspect, ...]:
    """
    Read either the new public field `aspects` or the legacy DB field
    `entities`, without changing the database schema yet.
    """
    values = getattr(profile, "aspects", None)

    if values is None:
        values = getattr(profile, "entities", ())

    return canonicalize_aspect_values(values or ())


__all__ = [
    "CanonicalAspect",
    "canonicalize_aspect_values",
    "canonicalize_profile_aspects",
]
