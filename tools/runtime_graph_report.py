from __future__ import annotations

from collections import Counter

from backend.knowledge_graph.models import EntityType
from backend.knowledge_graph.runtime import build_runtime_graph
from backend.semantic_engine.engine import answer_semantic_query


QUERIES = (
    "Какие товары есть по Белой Таре?",
    "Куда можно поехать к Миларепе?",
    "Какие практики связаны с Миларепой?",
)


def main() -> None:
    graph = build_runtime_graph()
    counts = Counter(
        entity.entity_type.value
        for entity in graph.list_entities()
    )

    print("=" * 72)
    print("AI BODHI GRAPH INTEGRATION LAYER")
    print("=" * 72)
    print(f"Entities:  {len(graph.list_entities())}")
    print(f"Relations: {len(graph.list_relations())}")

    print("\nRuntime entity types:")
    for entity_type, count in counts.most_common():
        print(f"  {entity_type}: {count}")

    for query in QUERIES:
        answer = answer_semantic_query(
            query,
            repository=graph,
        )
        print(f"\nВопрос: {query}")
        print(answer.text or "Ответ не найден.")


if __name__ == "__main__":
    main()
