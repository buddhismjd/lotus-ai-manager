from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from backend.knowledge_graph.contract import GraphNeighborhood

from backend.knowledge_graph.models import (
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)


@dataclass(slots=True)
class KnowledgeGraphRepository:
    _entities: dict[str, KnowledgeEntity] = field(default_factory=dict)
    _relations: list[KnowledgeRelation] = field(default_factory=list)

    def add_entity(self, entity: KnowledgeEntity) -> None:
        existing = self._entities.get(entity.entity_id)

        if existing is not None and existing != entity:
            raise ValueError(
                f"Entity id {entity.entity_id!r} already exists "
                "with different content."
            )

        self._entities[entity.entity_id] = entity

    def add_relation(self, relation: KnowledgeRelation) -> None:
        if relation not in self._relations:
            self._relations.append(relation)

    def get_entity(self, entity_id: str) -> KnowledgeEntity | None:
        return self._entities.get(entity_id)

    def list_entities(self) -> tuple[KnowledgeEntity, ...]:
        return tuple(
            sorted(
                self._entities.values(),
                key=lambda item: (
                    item.entity_type.value,
                    item.name.lower(),
                ),
            )
        )

    def list_relations(self) -> tuple[KnowledgeRelation, ...]:
        return tuple(
            sorted(
                self._relations,
                key=lambda item: (
                    item.source_id,
                    item.relation_type.value,
                    item.target_id,
                ),
            )
        )

    def outgoing(
        self,
        source_id: str,
        relation_type: RelationType | None = None,
    ) -> tuple[KnowledgeRelation, ...]:
        return tuple(
            relation
            for relation in self.list_relations()
            if relation.source_id == source_id
            and (
                relation_type is None
                or relation.relation_type == relation_type
            )
        )

    def incoming(
        self,
        target_id: str,
        relation_type: RelationType | None = None,
    ) -> tuple[KnowledgeRelation, ...]:
        return tuple(
            relation
            for relation in self.list_relations()
            if relation.target_id == target_id
            and (
                relation_type is None
                or relation.relation_type == relation_type
            )
        )

    def neighbors(
        self,
        entity_id: str,
    ) -> tuple[KnowledgeEntity, ...]:
        ids = {
            relation.target_id
            for relation in self.outgoing(entity_id)
        }
        ids.update(
            relation.source_id
            for relation in self.incoming(entity_id)
        )

        return tuple(
            entity
            for entity_id in sorted(ids)
            if (entity := self.get_entity(entity_id)) is not None
        )

    def find_by_name(self, value: str) -> tuple[KnowledgeEntity, ...]:
        normalized = normalize(value)

        result = []

        for entity in self._entities.values():
            if any(
                normalize(candidate) == normalized
                for candidate in entity.all_names
            ):
                result.append(entity)

        return tuple(
            sorted(result, key=lambda item: item.name.lower())
        )

    # Knowledge 2.0 contract API. Legacy methods remain available so the
    # migration can be performed layer by layer without duplicated storage.
    def get_aspect(self, aspect_id: str) -> KnowledgeEntity | None:
        return self.get_entity(aspect_id)

    def list_aspects(
        self,
        aspect_type=None,
    ) -> tuple[KnowledgeEntity, ...]:
        entities = self.list_entities()
        if aspect_type is None:
            return entities
        return tuple(
            aspect for aspect in entities
            if aspect.entity_type is aspect_type
        )

    def find_aspects(
        self,
        value: str,
        aspect_type=None,
    ) -> tuple[KnowledgeEntity, ...]:
        aspects = self.find_by_name(value)
        if aspect_type is None:
            return aspects
        return tuple(
            aspect for aspect in aspects
            if aspect.entity_type is aspect_type
        )

    def outgoing_relations(
        self,
        aspect_id: str,
        relation_type: RelationType | None = None,
    ) -> tuple[KnowledgeRelation, ...]:
        return self.outgoing(aspect_id, relation_type)

    def incoming_relations(
        self,
        aspect_id: str,
        relation_type: RelationType | None = None,
    ) -> tuple[KnowledgeRelation, ...]:
        return self.incoming(aspect_id, relation_type)

    def neighborhood(
        self,
        aspect_id: str,
    ) -> GraphNeighborhood | None:
        aspect = self.get_aspect(aspect_id)
        if aspect is None:
            return None
        return GraphNeighborhood(
            aspect=aspect,
            outgoing=self.outgoing_relations(aspect_id),
            incoming=self.incoming_relations(aspect_id),
            neighbors=self.neighbors(aspect_id),
        )


def normalize(value: str | None) -> str:
    return (value or "").lower().replace("ё", "е").strip()


__all__ = [
    "KnowledgeGraphRepository",
    "normalize",
]
