from __future__ import annotations

from dataclasses import dataclass

from backend.tours.planned import PLANNED_TOURS, PlannedTour


@dataclass(frozen=True, slots=True)
class TourKnowledgeNode:
    label: str
    node_type: str
    related: tuple[str, ...]


def build_planned_tour_knowledge() -> tuple[TourKnowledgeNode, ...]:
    nodes: dict[tuple[str, str], set[str]] = {}

    def add(node_type: str, label: str, related: tuple[str, ...]) -> None:
        key = (node_type, label)
        nodes.setdefault(key, set()).update(related)

    for tour in PLANNED_TOURS:
        tour_related = tuple(
            dict.fromkeys(
                [
                    *tour.countries,
                    *tour.destinations,
                    *tour.aspects,
                    *tour.practices,
                    tour.status,
                ]
            )
        )
        add("tour", tour.title, tour_related)

        for country in tour.countries:
            add(
                "country",
                country,
                tuple(
                    dict.fromkeys(
                        [
                            tour.title,
                            *tour.destinations,
                            *tour.aspects,
                            *tour.practices,
                            tour.status,
                        ]
                    )
                ),
            )

        for destination in tour.destinations:
            add(
                "destination",
                destination,
                tuple(
                    dict.fromkeys(
                        [
                            tour.title,
                            *tour.countries,
                            *tour.aspects,
                            *tour.practices,
                            tour.status,
                        ]
                    )
                ),
            )

        for aspect in tour.aspects:
            add(
                "aspect",
                aspect,
                tuple(
                    dict.fromkeys(
                        [
                            tour.title,
                            *tour.countries,
                            *tour.destinations,
                            *tour.practices,
                            tour.status,
                        ]
                    )
                ),
            )

    return tuple(
        TourKnowledgeNode(
            label=label,
            node_type=node_type,
            related=tuple(sorted(related)),
        )
        for (node_type, label), related in sorted(nodes.items())
    )


__all__ = [
    "TourKnowledgeNode",
    "build_planned_tour_knowledge",
]
