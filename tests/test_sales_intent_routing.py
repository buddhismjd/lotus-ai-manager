from backend.rag.dynamic_query_router import route_query


def test_travel_action_overrides_country_product_match() -> None:
    route = route_query("Хотела бы на кору в Тибет съездить")

    assert route.intent == "tour"
    assert route.reason in {"dynamic_tour_match", "generic_tour_request"}


def test_travel_variants_are_routed_to_tours() -> None:
    queries = (
        "Хочу поехать в Тибет",
        "В Тибет возите?",
        "Можно съездить на кору?",
        "Хочу ехать на Кайлас",
    )

    for query in queries:
        assert route_query(query).intent == "tour", query


def test_explicit_product_stays_product_even_with_country() -> None:
    route = route_query("Есть чётки из Тибета?")

    assert route.intent == "product"


def test_country_without_travel_or_product_is_not_forced_to_product() -> None:
    route = route_query("Расскажите про Тибет")

    assert route.intent != "product"
