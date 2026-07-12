import backend.services.bodhi_service as service
from backend.services.response_builder import BuiltResponse


def test_catalog_response_wins_over_semantic(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "_answer_query_legacy",
        lambda query: BuiltResponse(
            kind="product",
            text="catalog response",
            title="Ваджра",
            url="https://example.com/vajra",
        ),
    )
    monkeypatch.setattr(
        service,
        "semantic_built_response",
        lambda query: BuiltResponse(
            kind="product",
            text="semantic response",
            title="vajra",
            url=None,
        ),
    )

    response = service.answer_query("У вас есть Ваджра?")

    assert response.text == "catalog response"


def test_planned_tour_wins_over_semantic(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "_answer_query_legacy",
        lambda query: BuiltResponse(
            kind="tour",
            text="Программа находится в подготовке. Даты позже.",
            title="Лапчи",
            url=None,
        ),
    )
    monkeypatch.setattr(
        service,
        "semantic_built_response",
        lambda query: BuiltResponse(
            kind="tour",
            text="semantic tour",
            title="milarepa",
            url=None,
        ),
    )

    response = service.answer_query("Поход в Лапчи")

    assert "Даты" in response.text


def test_semantic_handles_only_legacy_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "_answer_query_legacy",
        lambda query: BuiltResponse(
            kind="fallback",
            text="legacy fallback",
            title=None,
            url=None,
        ),
    )
    monkeypatch.setattr(
        service,
        "semantic_built_response",
        lambda query: BuiltResponse(
            kind="product",
            text="semantic knowledge",
            title="milarepa",
            url=None,
        ),
    )

    response = service.answer_query(
        "Какие практики связаны с Миларепой?"
    )

    assert response.text == "semantic knowledge"


def test_legacy_fallback_remains_when_semantic_unmatched(
    monkeypatch,
) -> None:
    fallback = BuiltResponse(
        kind="fallback",
        text="legacy fallback",
        title=None,
        url=None,
    )
    monkeypatch.setattr(
        service,
        "_answer_query_legacy",
        lambda query: fallback,
    )
    monkeypatch.setattr(
        service,
        "semantic_built_response",
        lambda query: None,
    )

    assert service.answer_query("неизвестно") is fallback
