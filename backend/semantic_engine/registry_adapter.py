from __future__ import annotations

from functools import lru_cache

from backend.knowledge.aspect_registry import (
    load_aspect_registry,
    normalize_text,
    normalized_signature,
)
from backend.knowledge_graph.loader import load_graph
from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)


@lru_cache(maxsize=1)
def _registry_alias_index() -> dict[tuple[str, ...], str]:
    index: dict[tuple[str, ...], str] = {}

    for aspect_id, definition in load_aspect_registry().items():
        for candidate in definition.all_names:
            signature = normalized_signature(candidate)

            if signature:
                index.setdefault(signature, aspect_id)

    return index


def resolve_graph_entity_id(
    value: str | None,
    *,
    repository: KnowledgeGraphRepository | None = None,
) -> str | None:
    repository = repository or load_graph()
    normalized = normalize_text(value)

    if not normalized:
        return None

    # Direct graph lookup first.
    direct = repository.find_by_name(normalized)

    if direct:
        return direct[0].entity_id

    signature = normalized_signature(normalized)
    aspect_id = _registry_alias_index().get(signature)

    if aspect_id and repository.get_entity(aspect_id) is not None:
        return aspect_id

    # Safe fallback for a phrase containing a known alias.
    for candidate_signature, candidate_id in _registry_alias_index().items():
        candidate = " ".join(candidate_signature)

        if not candidate or len(candidate) < 4:
            continue

        query_signature = " ".join(signature)

        if candidate in query_signature or query_signature in candidate:
            if repository.get_entity(candidate_id) is not None:
                return candidate_id

    return None


def clear_registry_adapter_cache() -> None:
    _registry_alias_index.cache_clear()


__all__ = [
    "clear_registry_adapter_cache",
    "resolve_graph_entity_id",
]
