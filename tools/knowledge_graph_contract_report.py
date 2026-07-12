from __future__ import annotations

from collections import Counter

from backend.knowledge_graph.runtime import build_runtime_graph


def run() -> int:
    graph = build_runtime_graph()
    counts = Counter(aspect.entity_type.value for aspect in graph.list_aspects())

    print("AI BODHI KNOWLEDGE 2.0 — GRAPH CONTRACT REPORT")
    print(f"Total aspects: {sum(counts.values())}")
    for aspect_type, count in sorted(counts.items()):
        print(f"- {aspect_type}: {count}")
    print(f"Total relations: {len(graph.list_relations())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
