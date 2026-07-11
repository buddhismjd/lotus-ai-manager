from types import SimpleNamespace

import backend.knowledge_graph.runtime as runtime
from backend.catalog.product_profiles import ProductProfile
from backend.semantic_engine.engine import answer_semantic_query


def test_semantic_engine_returns_real_product(monkeypatch) -> None:
    product = SimpleNamespace(
        title="Статуя Белой Тары",
        url="https://example.com/tproduct/100-white-tara",
        description="Высота 29 см.",
        category="",
        sku="",
        keywords=[],
        source_id="",
        id="",
    )

    monkeypatch.setattr(
        runtime.ProductRepository,
        "list_all",
        lambda self: [product],
    )
    monkeypatch.setattr(
        runtime.TourRepository,
        "list_all",
        lambda self: [],
    )
    monkeypatch.setattr(
        runtime,
        "get_product_profile",
        lambda profile_id: ProductProfile(
            product_id=profile_id,
            product_type="statue",
            entities=("Белая Тара",),
        ),
    )

    graph = runtime.build_runtime_graph(
        include_active_tours=False,
        include_planned_tours=False,
    )
    answer = answer_semantic_query(
        "Какие товары есть по Белой Таре?",
        repository=graph,
    )

    assert "Статуя Белой Тары" in answer.text
    assert "https://example.com" in answer.text


def test_semantic_engine_returns_planned_lapchi(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime.ProductRepository,
        "list_all",
        lambda self: [],
    )
    monkeypatch.setattr(
        runtime.TourRepository,
        "list_all",
        lambda self: [],
    )

    graph = runtime.build_runtime_graph()
    answer = answer_semantic_query(
        "Куда можно поехать к Миларепе?",
        repository=graph,
    )

    assert "Лапчи" in answer.text
    assert "planned" in answer.text
