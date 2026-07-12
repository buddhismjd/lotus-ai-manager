from __future__ import annotations

import re

from backend.semantic_engine.engine import answer_semantic_query
from backend.semantic_engine.models import SemanticIntent
from backend.services.response_builder import BuiltResponse


PRODUCT_INTENTS = {
    SemanticIntent.FIND_PRODUCTS,
    SemanticIntent.FIND_RELATED,
    SemanticIntent.DESCRIBE_ENTITY,
}

TOUR_INTENTS = {
    SemanticIntent.FIND_TOURS,
}

PRACTICE_INTENTS = {
    SemanticIntent.FIND_PRACTICES,
}


# Semantic Engine is a fallback knowledge layer, not a replacement for
# product/tour business routing.
_COMMERCIAL_PATTERNS = (
    r"\bу\s+вас\s+есть\b",
    r"\bесть\b",
    r"\bхочу\b",
    r"\bищу\b",
    r"\bнуж(?:ен|на|но|ны|на)\b",
    r"\bкупить\b",
    r"\bпокажи\b",
    r"\bстату(?:я|ю|и)\b",
    r"\bамулет\b",
    r"\bчетк(?:и|и|у)\b",
    r"\bтовар\b",
    r"\bтур\b",
    r"\bпоездк(?:а|у|и|е)\b",
    r"\bпоход\b",
    r"\bпутешеств(?:ие|ия|ий)\b",
)

_KNOWLEDGE_PATTERNS = (
    r"\bрасскажи\s+про\b",
    r"\bкто\s+так(?:ой|ая|ое)\b",
    r"\bчто\s+такое\b",
    r"\bчто\s+означает\b",
    r"\bчто\s+связано\s+с\b",
    r"\bкакие\s+практики\b",
    r"\bкакие\s+места\b",
    r"\bгде\s+практиковал\b",
)


def _normalize(query: str) -> str:
    return (query or "").lower().replace("ё", "е").strip()


def should_use_semantic_fallback(query: str) -> bool:
    """
    Allow Semantic Engine only for knowledge-style questions.

    Commercial/catalog/travel wording is deliberately rejected so the
    established product and tour handlers remain authoritative.
    """
    normalized = _normalize(query)

    if not normalized:
        return False

    if any(
        re.search(pattern, normalized, re.IGNORECASE)
        for pattern in _COMMERCIAL_PATTERNS
    ):
        return False

    return any(
        re.search(pattern, normalized, re.IGNORECASE)
        for pattern in _KNOWLEDGE_PATTERNS
    )


def semantic_built_response(query: str) -> BuiltResponse | None:
    if not should_use_semantic_fallback(query):
        return None

    semantic = answer_semantic_query(query)

    if not semantic.matched or not semantic.text.strip():
        return None

    if semantic.intent in TOUR_INTENTS:
        kind = "tour"
    elif semantic.intent in PRODUCT_INTENTS:
        kind = "product"
    elif semantic.intent in PRACTICE_INTENTS:
        kind = "product"
    else:
        kind = "product"

    return BuiltResponse(
        kind=kind,
        text=semantic.text,
        title=semantic.entity_id,
        url=None,
    )


__all__ = [
    "semantic_built_response",
    "should_use_semantic_fallback",
]
