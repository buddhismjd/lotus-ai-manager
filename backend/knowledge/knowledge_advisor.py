from __future__ import annotations

from dataclasses import dataclass

from backend.knowledge.knowledge_core import (
    description_recommendations,
    get_knowledge_definition,
)


@dataclass(frozen=True, slots=True)
class KnowledgeAdvisorResult:
    knowledge_id: str
    name: str
    kind_label: str
    missing_fields: tuple[str, ...]


def advise_product_description(
    knowledge_id: str,
    *,
    existing_description: str = "",
) -> KnowledgeAdvisorResult | None:
    definition = get_knowledge_definition(knowledge_id)

    if definition is None:
        return None

    description = (existing_description or "").lower()

    missing = tuple(
        field
        for field in description_recommendations(knowledge_id)
        if not _field_is_present(field, description)
    )

    return KnowledgeAdvisorResult(
        knowledge_id=knowledge_id,
        name=definition.name,
        kind_label=definition.kind_label,
        missing_fields=missing,
    )


def _field_is_present(field: str, description: str) -> bool:
    keywords = {
        "материал": ("материал", "бронз", "латун", "медь", "дерев"),
        "размер": ("размер", "высота", "длина", "см", "мм"),
        "происхождение": ("непал", "тибет", "индия", "бутан", "мастер"),
        "назначение": ("назначение", "практик", "алтар", "медитац"),
        "количество концов": ("конечн", "зубц", "спиц"),
        "аспект": ("аспект", "бодхисаттв", "будд", "защитник"),
        "символика": ("символ", "значение", "олицетвор"),
    }

    aliases = keywords.get(field, (field,))
    return any(alias in description for alias in aliases)


__all__ = [
    "KnowledgeAdvisorResult",
    "advise_product_description",
]
