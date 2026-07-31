from backend.sales_assistant.intent_router import classify_commercial_intent


def test_bare_country_routes_to_tours() -> None:
    decision = classify_commercial_intent("Непал")
    assert decision.primary == "tour"
    assert decision.is_catalog_query is True
    assert decision.label == "Непал"


def test_destination_routes_to_tours_without_country_word() -> None:
    decision = classify_commercial_intent("Лапчи")
    assert decision.primary == "tour"
    assert decision.is_catalog_query is True
    assert decision.label == "Лапчи"


def test_journey_query_routes_to_tours() -> None:
    decision = classify_commercial_intent("Хочу поехать на Кайлас")
    assert decision.primary == "tour"
    assert decision.is_catalog_query is True


def test_explicit_product_language_wins_over_geography() -> None:
    decision = classify_commercial_intent("Покажи статуи из Непала")
    assert decision.primary == "product"


def test_product_query_routes_to_product_catalogue() -> None:
    assert classify_commercial_intent("Покажи поющие чаши").primary == "product"


def test_psychologist_query_routes_to_service() -> None:
    assert classify_commercial_intent("Нужна консультация психолога").primary == "psychologist"


def test_contact_query_routes_to_contacts() -> None:
    assert classify_commercial_intent("Как связаться с менеджером?").primary == "contacts"


def test_unrelated_query_remains_unknown() -> None:
    assert classify_commercial_intent("Добрый день").primary == "unknown"
