from backend.knowledge.answering import answer_knowledge_query
from backend.knowledge.graph import KnowledgeGraph


def test_registry_resolves_multiword_aspect_case_form() -> None:
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
