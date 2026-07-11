from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable


ASPECTS_DIR = Path(__file__).resolve().parent / "aspects"


@dataclass(frozen=True, slots=True)
class AspectDefinition:
    aspect_id: str
    name: str
    aliases: tuple[str, ...]
    description: str = ""
    keywords: tuple[str, ...] = ()

    @property
    def all_names(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.name, *self.aliases)))


def normalize_text(value: str | None) -> str:
    text = (value or "").lower().replace("ё", "е")
    text = re.sub(r"[^a-zа-я0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _token_stem(token: str) -> str:
    endings = (
        "иями", "ами", "ями",
        "ого", "его", "ему", "ому",
        "ыми", "ими",
        "ую", "юю", "ая", "яя", "ое", "ее", "ые", "ие",
        "ых", "их",
        "ах", "ях", "ов", "ев",
        "ам", "ям", "ом", "ем", "ой", "ей",
        "ы", "и", "а", "я", "у", "ю", "е", "о",
    )

    for ending in endings:
        if token.endswith(ending) and len(token) - len(ending) >= 4:
            return token[:-len(ending)]

    return token


def normalized_signature(value: str | None) -> tuple[str, ...]:
    return tuple(
        _token_stem(token)
        for token in normalize_text(value).split()
        if token
    )


@lru_cache(maxsize=1)
def load_aspect_registry() -> dict[str, AspectDefinition]:
    result: dict[str, AspectDefinition] = {}

    for path in sorted(ASPECTS_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        definition = AspectDefinition(
            aspect_id=str(payload["id"]),
            name=str(payload["name"]),
            aliases=tuple(
                str(value)
                for value in payload.get("aliases", [])
                if str(value).strip()
            ),
            description=str(payload.get("description", "") or ""),
            keywords=tuple(
                str(value)
                for value in payload.get("keywords", [])
                if str(value).strip()
            ),
        )
        result[definition.aspect_id] = definition

    return result


def resolve_aspect(
    value: str | None,
    *,
    registry: dict[str, AspectDefinition] | None = None,
) -> AspectDefinition | None:
    registry = registry or load_aspect_registry()
    normalized = normalize_text(value)

    if not normalized:
        return None

    signature = normalized_signature(normalized)

    for definition in registry.values():
        for candidate in definition.all_names:
            if normalize_text(candidate) == normalized:
                return definition

    for definition in registry.values():
        for candidate in definition.all_names:
            if normalized_signature(candidate) == signature:
                return definition

    # Safe containment fallback for longer aliases only.
    for definition in registry.values():
        for candidate in definition.all_names:
            candidate_normalized = normalize_text(candidate)

            if len(candidate_normalized) < 5:
                continue

            if (
                candidate_normalized in normalized
                or normalized in candidate_normalized
            ):
                return definition

    return None


def resolve_aspects_in_text(
    value: str | None,
    *,
    registry: dict[str, AspectDefinition] | None = None,
) -> tuple[AspectDefinition, ...]:
    registry = registry or load_aspect_registry()
    normalized = normalize_text(value)

    matches: list[AspectDefinition] = []

    for definition in registry.values():
        for candidate in definition.all_names:
            candidate_normalized = normalize_text(candidate)

            if candidate_normalized and candidate_normalized in normalized:
                matches.append(definition)
                break

    return tuple(dict.fromkeys(matches))


def canonical_aspect_id(value: str | None) -> str | None:
    definition = resolve_aspect(value)
    return definition.aspect_id if definition else None


def canonical_aspect_name(value: str | None) -> str | None:
    definition = resolve_aspect(value)
    return definition.name if definition else None


__all__ = [
    "AspectDefinition",
    "canonical_aspect_id",
    "canonical_aspect_name",
    "load_aspect_registry",
    "normalize_text",
    "normalized_signature",
    "resolve_aspect",
    "resolve_aspects_in_text",
]
