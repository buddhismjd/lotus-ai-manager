from __future__ import annotations

import re
from dataclasses import dataclass

from backend.knowledge.graph import (
    KnowledgeGraph,
    KnowledgeNode,
    aspect_overview,
    build_knowledge_graph,
)
from backend.knowledge.aspect_registry import canonical_aspect_name


@dataclass(frozen=True, slots=True)
class KnowledgeAnswer:
    matched: bool
    text: str = ""
    title: str | None = None


def _normalize(value: str | None) -> str:
    return (
        (value or "")
        .lower()
        .replace("ё", "е")
        .strip()
    )


_RUSSIAN_CASE_ENDINGS = (
    "иями",
    "ами",
    "ями",
    "ого",
    "его",
    "ему",
    "ому",
    "ыми",
    "ими",
    "ую",
    "юю",
    "ая",
    "яя",
    "ое",
    "ее",
    "ые",
    "ие",
    "ых",
    "их",
    "ах",
    "ях",
    "ов",
    "ев",
    "ам",
    "ям",
    "ом",
    "ем",
    "ой",
    "ей",
    "ы",
    "и",
    "а",
    "я",
    "у",
    "ю",
    "е",
    "о",
)



def _word_stem(value: str) -> str:
    normalized = _normalize(value)

    for ending in _RUSSIAN_CASE_ENDINGS:
        if normalized.endswith(ending) and len(normalized) - len(ending) >= 4:
            return normalized[:-len(ending)]

    return normalized


def _label_stems(value: str) -> tuple[str, ...]:
    return tuple(
        _word_stem(token)
        for token in _normalize(value).split()
        if token
    )


def _labels_match(left: str, right: str) -> bool:
    left_normalized = _normalize(left)
    right_normalized = _normalize(right)

    if left_normalized == right_normalized:
        return True

    return _label_stems(left_normalized) == _label_stems(right_normalized)


def _find_node(
    graph: KnowledgeGraph,
    label: str,
    node_type: str,
) -> KnowledgeNode | None:
    exact = graph.find(label, node_type=node_type)

    if exact:
        return exact[0]

    if node_type == "aspect":
        canonical_name = canonical_aspect_name(label)

        if canonical_name:
            canonical = graph.find(
                canonical_name,
                node_type=node_type,
            )

            if canonical:
                return canonical[0]

    for node in graph.nodes.values():
        if node.node_type != node_type:
            continue

        if _labels_match(label, node.label):
            return node

    return None


def _metadata(node: KnowledgeNode) -> dict[str, str]:
    return dict(node.metadata)


def _format_product(node: KnowledgeNode) -> str:
    metadata = _metadata(node)
    label = metadata.get("product_type_label") or "Товар"
    url = metadata.get("url") or ""

    if url:
        return f"• {label}: {node.label}\n  {url}"

    return f"• {label}: {node.label}"


def _format_tour(node: KnowledgeNode) -> str:
    metadata = _metadata(node)
    status = metadata.get("status") or "active"

    if status == "planned":
        return f"• Планируется: {node.label}"

    return f"• Доступно: {node.label}"


def answer_about_aspect(
    aspect: str,
    *,
    graph: KnowledgeGraph | None = None,
) -> KnowledgeAnswer:
    graph = graph or build_knowledge_graph()
    aspect_node = _find_node(
        graph,
        aspect,
        node_type="aspect",
    )

    if aspect_node is None:
        return KnowledgeAnswer(matched=False)

    aspect = aspect_node.label
    products = graph.related(
        aspect_node.key,
        relation="represented_by",
    )
    active_tours = graph.related(
        aspect_node.key,
        relation="has_tour",
    )
    planned_tours = graph.related(
        aspect_node.key,
        relation="has_planned_tour",
    )

    lines = [f"🌸 По аспекту **«{aspect}»** сейчас есть такая информация:"]

    if products:
        lines.append("\n**Товары:**")
        lines.extend(_format_product(node) for node in products[:6])

    if active_tours:
        lines.append("\n**Активные путешествия:**")
        lines.extend(_format_tour(node) for node in active_tours[:5])

    if planned_tours:
        lines.append("\n**Планируемые путешествия:**")
        lines.extend(_format_tour(node) for node in planned_tours[:5])

    if not products and not active_tours and not planned_tours:
        return KnowledgeAnswer(matched=False)

    lines.append(
        "\nУточните, что Вас интересует больше: "
        "товар, путешествие или практика."
    )

    return KnowledgeAnswer(
        matched=True,
        text="\n".join(lines),
        title=aspect,
    )


def answer_where_to_go(
    aspect: str,
    *,
    graph: KnowledgeGraph | None = None,
) -> KnowledgeAnswer:
    graph = graph or build_knowledge_graph()
    aspect_node = _find_node(
        graph,
        aspect,
        node_type="aspect",
    )

    if aspect_node is None:
        return KnowledgeAnswer(matched=False)

    aspect = aspect_node.label
    active_tours = graph.related(
        aspect_node.key,
        relation="has_tour",
    )
    planned_tours = graph.related(
        aspect_node.key,
        relation="has_planned_tour",
    )

    if not active_tours and not planned_tours:
        return KnowledgeAnswer(matched=False)

    lines = [f"🌸 По аспекту **«{aspect}»** есть такие направления:"]

    if active_tours:
        lines.append("\n**Активные программы:**")
        lines.extend(_format_tour(node) for node in active_tours[:5])

    if planned_tours:
        lines.append("\n**Планируемые программы:**")
        lines.extend(_format_tour(node) for node in planned_tours[:5])

    return KnowledgeAnswer(
        matched=True,
        text="\n".join(lines),
        title=aspect,
    )


def answer_practices_in_country(
    country: str,
    *,
    graph: KnowledgeGraph | None = None,
) -> KnowledgeAnswer:
    graph = graph or build_knowledge_graph()
    country_node = _find_node(
        graph,
        country,
        node_type="country",
    )

    if country_node is None:
        return KnowledgeAnswer(matched=False)

    country = country_node.label
    tour_nodes = [
        *graph.related(country_node.key, relation="has_tour"),
        *graph.related(country_node.key, relation="has_planned_tour"),
    ]

    practices: dict[str, list[str]] = {}

    for tour in tour_nodes:
        practice_nodes = graph.related(
            tour.key,
            relation="includes_practice",
        )

        for practice in practice_nodes:
            practices.setdefault(
                practice.label,
                [],
            ).append(tour.label)

    if not practices:
        return KnowledgeAnswer(matched=False)

    lines = [f"🌸 В направлении **«{country}»** доступны такие практики:"]

    for practice, tours in sorted(practices.items()):
        lines.append(f"\n**{practice.capitalize()}**")
        for tour in sorted(set(tours)):
            lines.append(f"• {tour}")

    return KnowledgeAnswer(
        matched=True,
        text="\n".join(lines),
        title=country,
    )


def extract_knowledge_intent(
    query: str,
) -> tuple[str, str] | None:
    normalized = _normalize(query)

    patterns = (
        (
            "where_to_go",
            r"(?:куда\s+можно\s+поехать\s+к|куда\s+поехать\s+к)\s+(.+?)[?.!]*$",
        ),
        (
            "practices_in_country",
            r"какие\s+практики\s+(?:есть|доступны)\s+в\s+(.+?)[?.!]*$",
        ),
        (
            "about_aspect",
            r"(?:расскажи\s+про|что\s+есть\s+по|что\s+у\s+вас\s+есть\s+по)\s+(.+?)[?.!]*$",
        ),
    )

    for intent, pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)

        if match:
            value = match.group(1).strip(" ?.!")

            if value:
                return intent, value

    return None


def answer_knowledge_query(
    query: str,
    *,
    graph: KnowledgeGraph | None = None,
) -> KnowledgeAnswer:
    parsed = extract_knowledge_intent(query)

    if parsed is None:
        return KnowledgeAnswer(matched=False)

    intent, value = parsed

    if intent == "where_to_go":
        return answer_where_to_go(value, graph=graph)

    if intent == "practices_in_country":
        return answer_practices_in_country(value, graph=graph)

    return answer_about_aspect(value, graph=graph)


__all__ = [
    "KnowledgeAnswer",
    "answer_about_aspect",
    "answer_knowledge_query",
    "answer_practices_in_country",
    "answer_where_to_go",
    "extract_knowledge_intent",
]
