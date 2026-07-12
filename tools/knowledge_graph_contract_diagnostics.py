from __future__ import annotations

from backend.knowledge_graph.contract import KnowledgeGraphContract
from backend.knowledge_graph.runtime import build_runtime_graph


def run() -> int:
    graph = build_runtime_graph()
    print("=" * 72)
    print("AI BODHI KNOWLEDGE GRAPH CONTRACT DIAGNOSTICS")
    print("=" * 72)
    print(f"Contract compatible: {isinstance(graph, KnowledgeGraphContract)}")
    print(f"Aspects: {len(graph.list_aspects())}")
    print(f"Relations: {len(graph.list_relations())}")

    if not isinstance(graph, KnowledgeGraphContract):
        return 1

    unresolved = [
        relation
        for relation in graph.list_relations()
        if graph.get_aspect(relation.source_id) is None
        or graph.get_aspect(relation.target_id) is None
    ]
    print(f"Unresolved relation endpoints: {len(unresolved)}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(run())
