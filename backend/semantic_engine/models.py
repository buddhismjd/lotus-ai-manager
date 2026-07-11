from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SemanticIntent(StrEnum):
    DESCRIBE_ENTITY = "describe_entity"
    FIND_RELATED = "find_related"
    FIND_PRODUCTS = "find_products"
    FIND_TOURS = "find_tours"
    FIND_PRACTICES = "find_practices"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SemanticQuery:
    raw_query: str
    intent: SemanticIntent
    entity_id: str | None = None
    confidence: float = 0.0
    reason: str = ""


@dataclass(frozen=True, slots=True)
class SemanticAnswer:
    matched: bool
    text: str
    intent: SemanticIntent
    entity_id: str | None = None
    confidence: float = 0.0


__all__ = [
    "SemanticAnswer",
    "SemanticIntent",
    "SemanticQuery",
]
