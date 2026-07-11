from __future__ import annotations

from backend.knowledge_graph.loader import load_graph
from backend.knowledge_graph.models import RelationType
from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)


def describe_entity(
    entity_id: str,
    *,
    repository: KnowledgeGraphRepository | None = None,
) -> str:
    repository = repository or load_graph()
    entity = repository.get_entity(entity_id)

    if entity is None:
        return ""

    lines = [
        f"{entity.name}",
        f"Тип: {entity.entity_type.value}",
    ]

    if entity.description:
        lines.append(entity.description)

    relations = repository.outgoing(entity_id)

    if relations:
        lines.append("Связи:")

        for relation in relations:
            target = repository.get_entity(relation.target_id)
            target_label = (
                target.name
                if target is not None
                else relation.target_id
            )
            lines.append(
                f"- {relation.relation_type.value}: "
                f"{target_label}"
            )

    return "\n".join(lines)


__all__ = ["describe_entity"]
