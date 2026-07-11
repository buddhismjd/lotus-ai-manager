from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class EntityType(StrEnum):
    BUDDHA = "buddha"
    BODHISATTVA = "bodhisattva"
    TEACHER = "teacher"
    PROTECTOR = "protector"
    PRACTICE_ITEM = "practice_item"
    PLACE = "place"
    COUNTRY = "country"
    REGION = "region"
    TRADITION = "tradition"
    PRACTICE = "practice"
    TOUR = "tour"
    PRODUCT = "product"
    ARTICLE = "article"
    VIDEO = "video"
    BOOK = "book"


class RelationType(StrEnum):
    RELATED_TO = "related_to"
    REPRESENTED_BY = "represented_by"
    PRACTICED_AT = "practiced_at"
    DISCIPLE_OF = "disciple_of"
    BELONGS_TO_TRADITION = "belongs_to_tradition"
    LOCATED_IN = "located_in"
    INCLUDES_PRACTICE = "includes_practice"
    ASSOCIATED_WITH = "associated_with"
    AVAILABLE_AS = "available_as"


@dataclass(frozen=True, slots=True)
class KnowledgeEntity:
    entity_id: str
    entity_type: EntityType
    name: str
    aliases: tuple[str, ...] = ()
    description: str = ""
    keywords: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def all_names(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.name, *self.aliases)))


@dataclass(frozen=True, slots=True)
class KnowledgeRelation:
    source_id: str
    relation_type: RelationType
    target_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)


__all__ = [
    "EntityType",
    "KnowledgeEntity",
    "KnowledgeRelation",
    "RelationType",
]
