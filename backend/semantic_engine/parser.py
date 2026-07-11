from __future__ import annotations

import re

from backend.knowledge_graph.loader import load_graph
from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)
from backend.semantic_engine.models import (
    SemanticIntent,
    SemanticQuery,
)
from backend.semantic_engine.registry_adapter import (
    resolve_graph_entity_id,
)


INTENT_PATTERNS: tuple[
    tuple[SemanticIntent, tuple[str, ...]],
    ...
] = (
    (
        SemanticIntent.FIND_TOURS,
        (
            r"\bкуда\s+(?:можно\s+)?поехать\b",
            r"\bкакие\s+(?:есть\s+)?туры\b",
            r"\bкакие\s+(?:есть\s+)?путешествия\b",
            r"\bпоездк[аи]\b",
        ),
    ),
    (
        SemanticIntent.FIND_PRODUCTS,
        (
            r"\bкакие\s+(?:есть\s+)?товары\b",
            r"\bчто\s+есть\s+в\s+магазине\b",
            r"\bпокажи\s+товары\b",
        ),
    ),
    (
        SemanticIntent.FIND_PRACTICES,
        (
            r"\bкакие\s+(?:есть\s+)?практики\b",
            r"\bс\s+какими\s+практиками\b",
            r"\bпрактик(?:а|и|у|ой)\b",
        ),
    ),
    (
        SemanticIntent.FIND_RELATED,
        (
            r"\bчто\s+связано\s+с\b",
            r"\bчто\s+есть\s+по\b",
            r"\bчто\s+у\s+вас\s+есть\s+по\b",
        ),
    ),
    (
        SemanticIntent.DESCRIBE_ENTITY,
        (
            r"\bрасскажи\s+про\b",
            r"\bкто\s+так(?:ой|ая|ое)\b",
            r"\bчто\s+такое\b",
            r"\bкто\s+это\b",
        ),
    ),
)


def _detect_intent(query: str) -> tuple[SemanticIntent, float, str]:
    normalized = query.lower().replace("ё", "е")

    for intent, patterns in INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                return intent, 0.95, f"pattern:{pattern}"

    return SemanticIntent.DESCRIBE_ENTITY, 0.65, "entity_only_fallback"


def _entity_candidates(
    query: str,
    repository: KnowledgeGraphRepository,
) -> tuple[str, ...]:
    candidates: list[tuple[int, str]] = []

    for entity in repository.list_entities():
        for alias in entity.all_names:
            if not alias.strip():
                continue

            start = query.lower().replace("ё", "е").find(
                alias.lower().replace("ё", "е")
            )

            if start >= 0:
                candidates.append((len(alias), entity.entity_id))

    return tuple(
        entity_id
        for _, entity_id in sorted(
            candidates,
            key=lambda item: (-item[0], item[1]),
        )
    )


def parse_semantic_query(
    query: str,
    *,
    repository: KnowledgeGraphRepository | None = None,
) -> SemanticQuery:
    repository = repository or load_graph()
    clean_query = (query or "").strip()

    if not clean_query:
        return SemanticQuery(
            raw_query=query,
            intent=SemanticIntent.UNKNOWN,
            confidence=0.0,
            reason="empty_query",
        )

    intent, confidence, reason = _detect_intent(clean_query)

    entity_id = resolve_graph_entity_id(
        clean_query,
        repository=repository,
    )

    if entity_id is None:
        candidates = _entity_candidates(clean_query, repository)

        if candidates:
            entity_id = candidates[0]

    if entity_id is None:
        return SemanticQuery(
            raw_query=query,
            intent=SemanticIntent.UNKNOWN,
            confidence=0.0,
            reason="entity_not_found",
        )

    return SemanticQuery(
        raw_query=query,
        intent=intent,
        entity_id=entity_id,
        confidence=confidence,
        reason=reason,
    )


__all__ = ["parse_semantic_query"]
