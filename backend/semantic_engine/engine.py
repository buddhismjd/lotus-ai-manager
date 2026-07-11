from __future__ import annotations

from backend.knowledge_graph.models import (
    EntityType,
    RelationType,
)
from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)
from backend.knowledge_graph.runtime import build_runtime_graph
from backend.semantic_engine.models import (
    SemanticAnswer,
    SemanticIntent,
)
from backend.semantic_engine.parser import parse_semantic_query


TYPE_LABELS = {
    EntityType.BUDDHA: "Будда",
    EntityType.BODHISATTVA: "Бодхисаттва",
    EntityType.TEACHER: "Учитель",
    EntityType.PROTECTOR: "Защитник",
    EntityType.PRACTICE_ITEM: "Предмет для практики",
    EntityType.PLACE: "Место",
    EntityType.COUNTRY: "Страна",
    EntityType.REGION: "Регион",
    EntityType.TRADITION: "Традиция",
    EntityType.PRACTICE: "Практика",
    EntityType.TOUR: "Путешествие",
    EntityType.PRODUCT: "Товар",
    EntityType.ARTICLE: "Статья",
    EntityType.VIDEO: "Видео",
    EntityType.BOOK: "Книга",
}

RELATION_LABELS = {
    RelationType.RELATED_TO: "Связано с",
    RelationType.REPRESENTED_BY: "Представлено товарами",
    RelationType.PRACTICED_AT: "Место практики",
    RelationType.DISCIPLE_OF: "Учитель",
    RelationType.BELONGS_TO_TRADITION: "Традиция",
    RelationType.LOCATED_IN: "Находится в",
    RelationType.INCLUDES_PRACTICE: "Практики",
    RelationType.ASSOCIATED_WITH: "Связано с",
    RelationType.AVAILABLE_AS: "Доступно как",
}


def _format_entity_header(entity) -> list[str]:
    lines = [
        f"🌸 **{entity.name}**",
        f"Тип: {TYPE_LABELS.get(entity.entity_type, entity.entity_type.value)}",
    ]

    if entity.description:
        lines.append(entity.description)

    return lines


def _related_entities(
    repository: KnowledgeGraphRepository,
    entity_id: str,
):
    result = []

    for relation in repository.outgoing(entity_id):
        target = repository.get_entity(relation.target_id)

        if target is not None:
            result.append((relation, target))

    for relation in repository.incoming(entity_id):
        source = repository.get_entity(relation.source_id)

        if source is not None:
            result.append((relation, source))

    return tuple(result)


def _answer_describe(
    repository: KnowledgeGraphRepository,
    entity_id: str,
) -> str:
    entity = repository.get_entity(entity_id)

    if entity is None:
        return ""

    lines = _format_entity_header(entity)
    related = _related_entities(repository, entity_id)

    if related:
        lines.append("\n**Связанные знания:**")

        for relation, target in related[:12]:
            relation_label = RELATION_LABELS.get(
                relation.relation_type,
                relation.relation_type.value,
            )
            status = dict(target.metadata).get("status", "")
            suffix = f" ({status})" if status else ""
            lines.append(
                f"• {relation_label}: {target.name}{suffix}"
            )

    return "\n".join(lines)


def _filter_related_by_type(
    repository: KnowledgeGraphRepository,
    entity_id: str,
    allowed_types: set[EntityType],
):
    seen: set[str] = set()
    result = []

    for _, target in _related_entities(repository, entity_id):
        if target.entity_type not in allowed_types:
            continue
        if target.entity_id in seen:
            continue

        seen.add(target.entity_id)
        result.append(target)

    return tuple(result)


def _format_collection_item(item) -> str:
    metadata = dict(item.metadata)
    url = metadata.get("url", "")
    status = metadata.get("status", "")
    suffix = f" — {status}" if status else ""

    if url:
        return f"• {item.name}{suffix}\n  {url}"

    return f"• {item.name}{suffix}"


def _answer_collection(
    repository: KnowledgeGraphRepository,
    entity_id: str,
    *,
    title: str,
    allowed_types: set[EntityType],
) -> str:
    entity = repository.get_entity(entity_id)

    if entity is None:
        return ""

    related = _filter_related_by_type(
        repository,
        entity_id,
        allowed_types,
    )

    lines = [f"🌸 **{title}: {entity.name}**"]

    if not related:
        lines.append(
            "В графе знаний пока нет связанных объектов этого типа."
        )
        return "\n\n".join(lines)

    lines.extend(_format_collection_item(item) for item in related)
    return "\n".join(lines)


def answer_semantic_query(
    query: str,
    *,
    repository: KnowledgeGraphRepository | None = None,
) -> SemanticAnswer:
    repository = repository or build_runtime_graph()
    parsed = parse_semantic_query(
        query,
        repository=repository,
    )

    if parsed.intent is SemanticIntent.UNKNOWN or not parsed.entity_id:
        return SemanticAnswer(
            matched=False,
            text="",
            intent=SemanticIntent.UNKNOWN,
            confidence=0.0,
        )

    if parsed.intent is SemanticIntent.FIND_PRODUCTS:
        text = _answer_collection(
            repository,
            parsed.entity_id,
            title="Товары по теме",
            allowed_types={EntityType.PRODUCT},
        )
    elif parsed.intent is SemanticIntent.FIND_TOURS:
        text = _answer_collection(
            repository,
            parsed.entity_id,
            title="Путешествия по теме",
            allowed_types={EntityType.TOUR},
        )
    elif parsed.intent is SemanticIntent.FIND_PRACTICES:
        text = _answer_collection(
            repository,
            parsed.entity_id,
            title="Практики по теме",
            allowed_types={EntityType.PRACTICE},
        )
    elif parsed.intent is SemanticIntent.FIND_RELATED:
        text = _answer_collection(
            repository,
            parsed.entity_id,
            title="Что связано с темой",
            allowed_types=set(EntityType),
        )
    else:
        text = _answer_describe(
            repository,
            parsed.entity_id,
        )

    return SemanticAnswer(
        matched=bool(text),
        text=text,
        intent=parsed.intent,
        entity_id=parsed.entity_id,
        confidence=parsed.confidence,
    )


__all__ = ["answer_semantic_query"]
