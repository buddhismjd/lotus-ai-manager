import backend.services.bodhi_service as service
from backend.tours.knowledge import build_planned_tour_knowledge
from backend.tours.planned import find_planned_tour


def test_nepal_query_returns_planned_tour() -> None:
    planned = find_planned_tour("Есть поездка в Непал?")

    assert planned is not None
    assert planned.status == "planned"
    assert "Лапчи" in planned.destinations


def test_lapchi_query_returns_planned_response() -> None:
    response = service.answer_query("Поход в Лапчи")
    text = response.text.lower()

    assert response.kind == "tour"
    assert (
        "подготовк" in text
        or "план" in text
        or "скоро" in text
    )
    assert "лапчи" in text
    assert "миларепа" in text


def test_nepal_query_returns_planned_response() -> None:
    response = service.answer_query("Есть поездка в Непал?")
    text = response.text.lower()

    assert response.kind == "tour"
    assert "непал" in text
    assert "даты" in text
    assert "не опубликованы" in text


def test_planned_tour_knowledge_contains_country_destination_and_aspect() -> None:
    nodes = build_planned_tour_knowledge()
    labels = {(node.node_type, node.label) for node in nodes}

    assert ("country", "Непал") in labels
    assert ("destination", "Лапчи") in labels
    assert ("aspect", "Миларепа") in labels
