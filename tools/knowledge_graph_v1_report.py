from __future__ import annotations

from collections import Counter

from backend.knowledge_graph.loader import load_graph
from backend.knowledge_graph.validator import validate_graph


def main() -> None:
    repository = load_graph()
    entities = repository.list_entities()
    relations = repository.list_relations()
    issues = validate_graph(repository)

    type_counts = Counter(
        entity.entity_type.value
        for entity in entities
    )
    relation_counts = Counter(
        relation.relation_type.value
        for relation in relations
    )

    print("=" * 72)
    print("AI BODHI KNOWLEDGE GRAPH 1.0")
    print("=" * 72)
    print(f"Entities:  {len(entities)}")
    print(f"Relations: {len(relations)}")
    print(f"Issues:    {len(issues)}")

    print("\nEntity types:")
    for name, count in type_counts.most_common():
        print(f"  {name}: {count}")

    print("\nRelation types:")
    for name, count in relation_counts.most_common():
        print(f"  {name}: {count}")

    if issues:
        print("\nValidation issues:")
        for issue in issues:
            print(
                f"  [{issue.level}] {issue.code}: "
                f"{issue.message}"
            )


if __name__ == "__main__":
    main()
