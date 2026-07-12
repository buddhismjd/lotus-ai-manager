from __future__ import annotations

from backend.services.bodhi_service import answer_query


QUERIES = (
    "Какие товары есть по Белой Таре?",
    "Куда можно поехать к Миларепе?",
    "Какие практики связаны с Миларепой?",
    "Расскажи про Ваджру",
)


def main() -> None:
    print("=" * 72)
    print("AI BODHI SEMANTIC SERVICE SMOKE TEST")
    print("=" * 72)

    for query in QUERIES:
        response = answer_query(query)
        print(f"\nВопрос: {query}")
        print(f"Kind: {response.kind}")
        print(response.text)


if __name__ == "__main__":
    main()
