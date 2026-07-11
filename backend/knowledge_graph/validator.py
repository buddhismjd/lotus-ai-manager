from __future__ import annotations

from dataclasses import dataclass

from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    level: str
    code: str
    message: str


def validate_graph(
    repository: KnowledgeGraphRepository,
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []

    entities = {
        entity.entity_id: entity
        for entity in repository.list_entities()
    }

    for relation in repository.list_relations():
        if relation.source_id not in entities:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="missing_source",
                    message=(
                        f"Relation source does not exist: "
                        f"{relation.source_id}"
                    ),
                )
            )

        if relation.target_id not in entities:
            issues.append(
                ValidationIssue(
                    level="error",
                    code="missing_target",
                    message=(
                        f"Relation target does not exist: "
                        f"{relation.target_id}"
                    ),
                )
            )

    for entity in entities.values():
        if not entity.description.strip():
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="missing_description",
                    message=(
                        f"{entity.entity_id}: description is empty"
                    ),
                )
            )

        if not entity.aliases:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="missing_aliases",
                    message=f"{entity.entity_id}: aliases are empty",
                )
            )

    return tuple(issues)


def has_errors(
    issues: tuple[ValidationIssue, ...],
) -> bool:
    return any(issue.level == "error" for issue in issues)


__all__ = [
    "ValidationIssue",
    "has_errors",
    "validate_graph",
]
