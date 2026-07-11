from __future__ import annotations

from collections import Counter

from backend.knowledge.graph import build_knowledge_graph


def main() -> None:
    graph = build_knowledge_graph()
    node_types = Counter(
        node.node_type
        for node in graph.nodes.values()
    )
    relations = Counter(
        edge.relation
        for edge in graph.edges
    )

    print("=" * 72)
    print("AI BODHI UNIFIED KNOWLEDGE GRAPH")
    print("=" * 72)
    print(f"Узлов:  {len(graph.nodes)}")
    print(f"Связей: {len(graph.edges)}")

    print("\nТипы узлов:")
    for node_type, count in node_types.most_common():
        print(f"  {node_type}: {count}")

    print("\nТипы связей:")
    for relation, count in relations.most_common():
        print(f"  {relation}: {count}")

    for aspect_name in ("Белая Тара", "Дзамбала", "Миларепа"):
        matches = graph.find(
            aspect_name,
            node_type="aspect",
        )

        if not matches:
            continue

        node = matches[0]
        print(f"\nАспект: {node.label}")

        for related in graph.related(node.key):
            metadata = dict(related.metadata)
            suffix = ""

            if metadata.get("status"):
                suffix = f" [{metadata['status']}]"
            elif metadata.get("product_type_label"):
                suffix = (
                    f" [{metadata['product_type_label']}]"
                )

            print(
                f"  - {related.node_type}: "
                f"{related.label}{suffix}"
            )


if __name__ == "__main__":
    main()
