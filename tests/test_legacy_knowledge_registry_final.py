from backend.knowledge.answering import (
    answer_knowledge_query,
)
from backend.knowledge.graph import (
    KnowledgeGraph,
)


def test_white_tara_case_form_uses_registry() -> None:
    graph = KnowledgeGraph()
    white_tara = graph.add_node(
        "aspect",
        "Белая Тара",
    )
    product = graph.add_node(
        "product",
        "Статуя Белой Тары",
        key="product:white-tara",
        metadata={
            "url": (
                "https://example.com/"
                "white-tara"
            ),
            "product_type_label": "Статуи",
        },
    )
    graph.add_edge(
        white_tara,
        "represented_by",
        product,
    )

    answer = answer_knowledge_query(
        "Что есть по Белой Таре?",
        graph=graph,
    )

    assert answer.matched is True
    assert answer.title == "Белая Тара"
    assert "Статуя Белой Тары" in answer.text


def test_existing_milarepa_form_still_works() -> None:
    graph = KnowledgeGraph()
    milarepa = graph.add_node(
        "aspect",
        "Миларепа",
    )
    planned = graph.add_node(
        "tour",
        "Лапчи",
        key="tour:lapchi",
        metadata={
            "status": "planned",
        },
    )
    graph.add_edge(
        milarepa,
        "has_planned_tour",
        planned,
    )

    answer = answer_knowledge_query(
        "Расскажи про Миларепу",
        graph=graph,
    )

    assert answer.matched is True
    assert "Миларепа" in answer.text
