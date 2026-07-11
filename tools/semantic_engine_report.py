from __future__ import annotations

from backend.semantic_engine.engine import answer_semantic_query


QUERIES = (
    "Расскажи про Миларепу",
    "Куда можно поехать к Миларепе?",
    "Какие практики связаны с Миларепой?",
    "Что есть по Белой Таре?",
    "Расскажи про Ваджру",
)


def main() -> None:
    print("=" * 72)
    print("AI BODHI SEMANTIC ENGINE 1.0")
    print("=" * 72)

    for query in QUERIES:
        answer = answer_semantic_query(query)

        print(f"\nВопрос: {query}")
        print(f"Intent: {answer.intent.value}")
        print(f"Entity: {answer.entity_id}")
        print(f"Confidence: {answer.confidence:.2f}")
        print(answer.text or "Ответ не найден.")


if __name__ == "__main__":
    main()
