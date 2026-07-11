from backend.knowledge_graph.loader import load_graph
from backend.semantic_engine.registry_adapter import (
    resolve_graph_entity_id,
)


def test_registry_aliases_resolve_to_graph_ids() -> None:
    repository = load_graph()

    assert (
        resolve_graph_entity_id(
            "Белой Таре",
            repository=repository,
        )
        == "white_tara"
    )
    assert (
        resolve_graph_entity_id(
            "Миларепе",
            repository=repository,
        )
        == "milarepa"
    )


def test_direct_graph_alias_resolves() -> None:
    repository = load_graph()

    assert (
        resolve_graph_entity_id(
            "Дордже",
            repository=repository,
        )
        == "vajra"
    )
