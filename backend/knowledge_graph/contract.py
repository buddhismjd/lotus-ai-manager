from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from backend.knowledge_graph.models import (
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)

# Knowledge 2.0 domain terminology. Aliases preserve compatibility with the
# already published graph storage and loader formats.
AspectType = EntityType
KnowledgeAspect = KnowledgeEntity
AspectRelation = KnowledgeRelation


@dataclass(frozen=True, slots=True)
class GraphNeighborhood:
    """Stable result of one-hop graph traversal around an aspect."""

    aspect: KnowledgeAspect
    outgoing: tuple[AspectRelation, ...] = ()
    incoming: tuple[AspectRelation, ...] = ()
    neighbors: tuple[KnowledgeAspect, ...] = ()


@runtime_checkable
class KnowledgeGraphContract(Protocol):
    """Read-only contract shared by semantic and service layers.

    Implementations may be in-memory, SQLite-backed or remote. Consumers
    depend on this protocol instead of a concrete storage implementation.
    """

    def get_aspect(self, aspect_id: str) -> KnowledgeAspect | None:
        ...

    def list_aspects(
        self,
        aspect_type: AspectType | None = None,
    ) -> tuple[KnowledgeAspect, ...]:
        ...

    def find_aspects(
        self,
        value: str,
        aspect_type: AspectType | None = None,
    ) -> tuple[KnowledgeAspect, ...]:
        ...

    def outgoing_relations(
        self,
        aspect_id: str,
        relation_type: RelationType | None = None,
    ) -> tuple[AspectRelation, ...]:
        ...

    def incoming_relations(
        self,
        aspect_id: str,
        relation_type: RelationType | None = None,
    ) -> tuple[AspectRelation, ...]:
        ...

    def neighborhood(self, aspect_id: str) -> GraphNeighborhood | None:
        ...


__all__ = [
    "AspectRelation",
    "AspectType",
    "GraphNeighborhood",
    "KnowledgeAspect",
    "KnowledgeGraphContract",
]
