from __future__ import annotations

from backend.knowledge.answering import (
    answer_knowledge_query,
    extract_knowledge_intent,
)


QUERIES = (
    "Расскажи про Миларепу",
    "Что есть по Белой Таре?",
    "Куда можно поехать к Миларепе?",
    "Какие практики есть в Непале?",
)


def main() -> None:
    print("=" * 72)
    print("AI BODHI KNOWLEDGE QUERY DIAGNOSTICS")
    print("=" * 72)

    for query in QUERIES:
        parsed = extract_knowledge_intent(query)
        answer = answer_knowledge_query(query)

        print(f"\nЗапрос: {query}")
        print(f"Разбор: {parsed}")
        print(f"Найдено: {answer.matched}")
        print(answer.text or "-")


if __name__ == "__main__":
    main()
