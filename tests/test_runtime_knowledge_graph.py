from types import SimpleNamespace

import backend.knowledge_graph.runtime as runtime
from backend.catalog.product_profiles import ProductProfile
from backend.knowledge_graph.models import EntityType


def product(title: str, url: str, description: str = ""):
    return SimpleNamespace(
        title=title,
        url=url,
        description=description,
        category="",
        sku="",
        keywords=[],
        source_id="",
        id="",
    )


def test_runtime_graph_connects_product_to_aspect(monkeypatch) -> None:
    item = product(
        "Статуя Белой Тары",
        "https://example.com/tproduct/100-white-tara",
        "Латунная статуя.",
    )

    monkeypatch.setattr(
        runtime.ProductRepository,
        "list_all",
        lambda self: [item],
    )
    monkeypatch.setattr(
        runtime.TourRepository,
        "list_all",
        lambda self: [],
    )
    monkeypatch.setattr(
        runtime,
        "PLANNED_TOURS",
        (),
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

    graph = runtime.build_runtime_graph()
    products = [
        entity
        for entity in graph.neighbors("white_tara")
        if entity.entity_type is EntityType.PRODUCT
    ]

    assert [item.name for item in products] == [
        "Статуя Белой Тары"
    ]


def test_runtime_graph_connects_planned_lapchi_tour(monkeypatch) -> None:
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
    tours = [
        entity
        for entity in graph.neighbors("milarepa")
        if entity.entity_type is EntityType.TOUR
    ]

    assert any("Лапчи" in item.name for item in tours)
    assert any(
        dict(item.metadata).get("status") == "planned"
        for item in tours
    )
