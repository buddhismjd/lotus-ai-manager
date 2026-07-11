from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from backend.catalog.aspect_catalog import list_aspect_groups
from backend.tours.planned import PLANNED_TOURS
from backend.tours.profiles import list_tour_profiles


@dataclass(frozen=True, slots=True)
class KnowledgeNode:
    key: str
    node_type: str
    label: str
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeEdge:
    source: str
    relation: str
    target: str


@dataclass(slots=True)
class KnowledgeGraph:
    nodes: dict[str, KnowledgeNode] = field(default_factory=dict)
    edges: set[KnowledgeEdge] = field(default_factory=set)

    def add_node(
        self,
        node_type: str,
        label: str,
        *,
        key: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        node_key = key or make_key(node_type, label)

        self.nodes.setdefault(
            node_key,
            KnowledgeNode(
                key=node_key,
                node_type=node_type,
                label=label,
                metadata=tuple(
                    sorted((metadata or {}).items())
                ),
            ),
        )
        return node_key

    def add_edge(
        self,
        source: str,
        relation: str,
        target: str,
    ) -> None:
        if source == target:
            return

        self.edges.add(
            KnowledgeEdge(
                source=source,
                relation=relation,
                target=target,
            )
        )

    def related(
        self,
        node_key: str,
        relation: str | None = None,
    ) -> tuple[KnowledgeNode, ...]:
        target_keys = {
            edge.target
            for edge in self.edges
            if edge.source == node_key
            and (relation is None or edge.relation == relation)
        }

        return tuple(
            sorted(
                (
                    self.nodes[key]
                    for key in target_keys
                    if key in self.nodes
                ),
                key=lambda node: (
                    node.node_type,
                    node.label.lower(),
                ),
            )
        )

    def find(
        self,
        label: str,
        node_type: str | None = None,
    ) -> tuple[KnowledgeNode, ...]:
        normalized = normalize(label)

        return tuple(
            node
            for node in self.nodes.values()
            if normalize(node.label) == normalized
            and (
                node_type is None
                or node.node_type == node_type
            )
        )


def normalize(value: str | None) -> str:
    return (
        (value or "")
        .lower()
        .replace("ё", "е")
        .strip()
    )


def make_key(node_type: str, label: str) -> str:
    normalized = normalize(label)
    return f"{node_type}:{normalized}"


def _add_product_knowledge(graph: KnowledgeGraph) -> None:
    for group in list_aspect_groups():
        aspect_key = graph.add_node(
            "aspect",
            group.aspect,
        )

        for product in group.products:
            product_key = graph.add_node(
                "product",
                product.title,
                key=f"product:{product.url}",
                metadata={
                    "url": product.url,
                    "product_type": product.product_type,
                    "product_type_label": product.product_type_label,
                },
            )
            type_key = graph.add_node(
                "product_type",
                product.product_type_label,
            )

            graph.add_edge(
                aspect_key,
                "represented_by",
                product_key,
            )
            graph.add_edge(
                product_key,
                "represents_aspect",
                aspect_key,
            )
            graph.add_edge(
                product_key,
                "has_product_type",
                type_key,
            )
            graph.add_edge(
                type_key,
                "contains_product",
                product_key,
            )


def _add_active_tour_knowledge(graph: KnowledgeGraph) -> None:
    for profile in list_tour_profiles():
        tour_key = graph.add_node(
            "tour",
            profile.tour_id,
            key=f"tour:{profile.tour_id}",
            metadata={
                "status": "active",
                "difficulty": profile.difficulty or "",
                "duration_days": (
                    str(profile.duration_days)
                    if profile.duration_days is not None
                    else ""
                ),
                "max_altitude_m": (
                    str(profile.max_altitude_m)
                    if profile.max_altitude_m is not None
                    else ""
                ),
            },
        )

        for country in profile.countries:
            country_key = graph.add_node(
                "country",
                country,
            )
            graph.add_edge(
                tour_key,
                "takes_place_in",
                country_key,
            )
            graph.add_edge(
                country_key,
                "has_tour",
                tour_key,
            )

        for destination in profile.destinations:
            destination_key = graph.add_node(
                "destination",
                destination,
            )
            graph.add_edge(
                tour_key,
                "visits",
                destination_key,
            )
            graph.add_edge(
                destination_key,
                "has_tour",
                tour_key,
            )

        for aspect in profile.aspects:
            aspect_key = graph.add_node(
                "aspect",
                aspect,
            )
            graph.add_edge(
                tour_key,
                "related_to_aspect",
                aspect_key,
            )
            graph.add_edge(
                aspect_key,
                "has_tour",
                tour_key,
            )

        for practice in profile.practices:
            practice_key = graph.add_node(
                "practice",
                practice,
            )
            graph.add_edge(
                tour_key,
                "includes_practice",
                practice_key,
            )
            graph.add_edge(
                practice_key,
                "available_in_tour",
                tour_key,
            )


def _add_planned_tour_knowledge(graph: KnowledgeGraph) -> None:
    for planned in PLANNED_TOURS:
        tour_key = graph.add_node(
            "tour",
            planned.title,
            key=f"planned_tour:{planned.slug}",
            metadata={
                "status": planned.status,
                "note": planned.note,
            },
        )

        for country in planned.countries:
            country_key = graph.add_node(
                "country",
                country,
            )
            graph.add_edge(
                tour_key,
                "takes_place_in",
                country_key,
            )
            graph.add_edge(
                country_key,
                "has_planned_tour",
                tour_key,
            )

        for destination in planned.destinations:
            destination_key = graph.add_node(
                "destination",
                destination,
            )
            graph.add_edge(
                tour_key,
                "visits",
                destination_key,
            )
            graph.add_edge(
                destination_key,
                "has_planned_tour",
                tour_key,
            )

        for aspect in planned.aspects:
            aspect_key = graph.add_node(
                "aspect",
                aspect,
            )
            graph.add_edge(
                tour_key,
                "related_to_aspect",
                aspect_key,
            )
            graph.add_edge(
                aspect_key,
                "has_planned_tour",
                tour_key,
            )

        for practice in planned.practices:
            practice_key = graph.add_node(
                "practice",
                practice,
            )
            graph.add_edge(
                tour_key,
                "includes_practice",
                practice_key,
            )
            graph.add_edge(
                practice_key,
                "available_in_planned_tour",
                tour_key,
            )


def build_knowledge_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    _add_product_knowledge(graph)
    _add_active_tour_knowledge(graph)
    _add_planned_tour_knowledge(graph)
    return graph


def aspect_overview(
    aspect: str,
    *,
    graph: KnowledgeGraph | None = None,
) -> dict[str, tuple[KnowledgeNode, ...]]:
    graph = graph or build_knowledge_graph()
    matches = graph.find(aspect, node_type="aspect")

    if not matches:
        return {}

    node = matches[0]

    return {
        "products": graph.related(
            node.key,
            relation="represented_by",
        ),
        "active_tours": graph.related(
            node.key,
            relation="has_tour",
        ),
        "planned_tours": graph.related(
            node.key,
            relation="has_planned_tour",
        ),
    }


__all__ = [
    "KnowledgeEdge",
    "KnowledgeGraph",
    "KnowledgeNode",
    "aspect_overview",
    "build_knowledge_graph",
    "make_key",
]
