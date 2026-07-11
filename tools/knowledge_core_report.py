from __future__ import annotations

from collections import Counter

from backend.knowledge.knowledge_core import (
    load_knowledge_core,
)


def main() -> None:
    core = load_knowledge_core()
    kinds = Counter(
        definition.kind_label
        for definition in core.values()
    )

    print("=" * 72)
    print("AI BODHI KNOWLEDGE CORE REPORT")
    print("=" * 72)
    print(f"Объектов знаний: {len(core)}")

    print("\nТипы:")
    for label, count in kinds.most_common():
        print(f"  {label}: {count}")

    print("\nОбъекты:")
    for definition in sorted(
        core.values(),
        key=lambda item: item.name.lower(),
    ):
        print(
            f"- {definition.name} "
            f"[{definition.kind_label}]"
        )


if __name__ == "__main__":
    main()
