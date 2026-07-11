from __future__ import annotations

from backend.knowledge.answering import answer_knowledge_query


QUERIES = (
    "Расскажи про Миларепу",
    "Что есть по Белой Таре?",
    "Куда можно поехать к Миларепе?",
    "Какие практики есть в Непале?",
)


def main() -> None:
    print("=" * 72)
    print("AI BODHI KNOWLEDGE ANSWER DEMO")
    print("=" * 72)

    for query in QUERIES:
        answer = answer_knowledge_query(query)

        print(f"\nВопрос: {query}")

        if answer.matched:
            print(answer.text)
        else:
            print("Граф знаний пока не нашёл ответа.")


if __name__ == "__main__":
    main()
