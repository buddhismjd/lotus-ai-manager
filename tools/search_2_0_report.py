from backend.sales_assistant.intent_router import classify_commercial_intent


def main() -> None:
    queries = (
        "Непал",
        "Индия зимой",
        "Кайлас",
        "Лапчи",
        "Покажи поющие чаши",
        "Покажи статуи из Непала",
        "Нужна консультация психолога",
    )
    print("Search-2.0 intent routing report")
    for query in queries:
        decision = classify_commercial_intent(query)
        print(
            f"- {query}: primary={decision.primary}; "
            f"catalog={decision.is_catalog_query}; label={decision.label or '-'}"
        )


if __name__ == "__main__":
    main()
