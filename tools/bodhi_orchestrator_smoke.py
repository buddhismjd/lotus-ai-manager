from __future__ import annotations

from backend.services.bodhi_service import answer_query


QUERIES = (
    "У вас есть Ваджра?",
    "Статуя Белой Тары",
    "Поход в Лапчи",
    "Есть поездка в Непал?",
    "Какие практики связаны с Миларепой?",
    "Расскажи про Ваджру",
)


def main() -> None:
    print("=" * 72)
    print("AI BODHI ORCHESTRATOR SMOKE TEST")
    print("=" * 72)

    for query in QUERIES:
        response = answer_query(query)
        print(f"\nВопрос: {query}")
        print(f"Kind: {response.kind}")
        print(f"Title: {response.title}")
        print(response.text)


if __name__ == "__main__":
    main()
