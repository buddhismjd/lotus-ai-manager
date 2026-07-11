from types import SimpleNamespace

import backend.knowledge.answering as answering
import backend.services.bodhi_service as service
from backend.knowledge.graph import KnowledgeGraph


def build_test_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()

    milarepa = graph.add_node("aspect", "Миларепа")
    product = graph.add_node(
        "product",
        "Статуя Миларепы",
        key="product:milarepa",
        metadata={
            "url": "https://example.com/milarepa",
            "product_type_label": "Статуи",
        },
    )
    planned_tour = graph.add_node(
        "tour",
        "Лапчи — место силы Миларепы",
        key="planned_tour:lapchi",
        metadata={"status": "planned"},
    )
    nepal = graph.add_node("country", "Непал")
    meditation = graph.add_node("practice", "медитация")

    graph.add_edge(milarepa, "represented_by", product)
    graph.add_edge(milarepa, "has_planned_tour", planned_tour)
    graph.add_edge(nepal, "has_planned_tour", planned_tour)
    graph.add_edge(planned_tour, "includes_practice", meditation)

    return graph


def test_tell_me_about_aspect() -> None:
    answer = answering.answer_knowledge_query(
        "Расскажи про Миларепу",
        graph=build_test_graph(),
    )

    assert answer.matched is True
    assert "Статуя Миларепы" in answer.text
    assert "Лапчи" in answer.text


def test_where_can_i_go_for_aspect() -> None:
    answer = answering.answer_knowledge_query(
        "Куда можно поехать к Миларепе?",
        graph=build_test_graph(),
    )

    assert answer.matched is True
    assert "Планируемые программы" in answer.text
    assert "Лапчи" in answer.text


def test_practices_in_country() -> None:
    answer = answering.answer_knowledge_query(
        "Какие практики есть в Непале?",
        graph=build_test_graph(),
    )

    assert answer.matched is True
    assert "Медитация" in answer.text
    assert "Лапчи" in answer.text


def test_service_uses_knowledge_answer(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "answer_knowledge_query",
        lambda query: answering.KnowledgeAnswer(
            matched=True,
            text="Графовый ответ",
            title="Миларепа",
        ),
    )

    response = service.answer_query("Расскажи про Миларепу")

    assert response.text == "Графовый ответ"
    assert response.title == "Миларепа"


def test_russian_case_forms_match_graph_labels() -> None:
    graph = build_test_graph()

    milarepa = answering.answer_knowledge_query(
        "Расскажи про Миларепу",
        graph=graph,
    )
    nepal = answering.answer_knowledge_query(
        "Какие практики есть в Непале?",
        graph=graph,
    )

    assert milarepa.matched is True
    assert "Миларепа" in milarepa.text
    assert nepal.matched is True
    assert "Непал" in nepal.text


def test_where_to_go_does_not_fall_through_to_random_tour() -> None:
    answer = answering.answer_knowledge_query(
        "Куда можно поехать к Миларепе?",
        graph=build_test_graph(),
    )

    assert answer.matched is True
    assert "Лапчи" in answer.text


def test_multiword_aspect_case_form_matches() -> None:
    graph = KnowledgeGraph()
    white_tara = graph.add_node("aspect", "Белая Тара")
    product = graph.add_node(
        "product",
        "Статуя Белой Тары",
        key="product:white-tara",
        metadata={
            "url": "https://example.com/white-tara",
            "product_type_label": "Статуи",
        },
    )
    graph.add_edge(white_tara, "represented_by", product)

    answer = answering.answer_knowledge_query(
        "Что есть по Белой Таре?",
        graph=graph,
    )

    assert answer.matched is True
    assert "Белая Тара" in answer.text
    assert "Статуя Белой Тары" in answer.text
