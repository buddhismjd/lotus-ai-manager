from __future__ import annotations

from backend.tours.knowledge import build_planned_tour_knowledge


def main() -> None:
    nodes = build_planned_tour_knowledge()

    print("=" * 72)
    print("AI BODHI PLANNED TOUR KNOWLEDGE")
    print("=" * 72)
    print(f"Узлов: {len(nodes)}")

    for node in nodes:
        print(f"\n[{node.node_type}] {node.label}")
        for related in node.related:
            print(f"  - {related}")


if __name__ == "__main__":
    main()
