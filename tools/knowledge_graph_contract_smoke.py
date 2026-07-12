from __future__ import annotations

from backend.knowledge_graph.runtime import build_runtime_graph


def run() -> int:
    graph = build_runtime_graph()
    aspects = graph.find_aspects("Белая Тара")

    if not aspects:
        print("SMOKE FAILED: Белая Тара not resolved")
        return 1

    neighborhood = graph.neighborhood(aspects[0].entity_id)
    if neighborhood is None:
        print("SMOKE FAILED: neighborhood unavailable")
        return 1

    print("SMOKE PASSED")
    print(f"Aspect: {neighborhood.aspect.name}")
    print(f"Neighbors: {len(neighborhood.neighbors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
