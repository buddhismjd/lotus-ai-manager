from backend.sales_assistant.intent_router import classify_commercial_intent


def main() -> None:
    country = classify_commercial_intent("Хочу в Непал")
    product = classify_commercial_intent("Покажи статуи из Непала")
    destination = classify_commercial_intent("Лапчи")

    assert country.primary == "tour" and country.is_catalog_query
    assert destination.primary == "tour" and destination.is_catalog_query
    assert product.primary == "product"
    print("Search-2.0 smoke: OK")


if __name__ == "__main__":
    main()
