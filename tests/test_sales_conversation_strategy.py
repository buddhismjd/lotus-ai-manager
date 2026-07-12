from __future__ import annotations

from backend.catalog.models import Tour
from backend.sales_assistant.formatter import format_tour_list
from backend.sales_assistant.strategy import choose_strategy, filter_tours


def _tour(title: str, description: str, url: str = "https://example.test/tour") -> Tour:
    return Tour(id=title, title=title, url=url, description=description)


def test_plural_tour_question_uses_list_strategy() -> None:
    decision = choose_strategy("Какие есть туры в сентябре?", "tour")
    assert decision.strategy == "tour_list"
    assert decision.month == 9


def test_specific_tour_question_uses_details_strategy() -> None:
    decision = choose_strategy("Расскажите про тур на Кайлас", "tour")
    assert decision.strategy == "tour_details"


def test_price_question_has_own_strategy() -> None:
    assert choose_strategy("Сколько стоит тур на Кайлас?", "tour").strategy == "tour_price"


def test_month_filter_uses_structured_or_published_text() -> None:
    september = _tour("Кайлас", "22 сентября – 9 октября. Паломнический тур.")
    november = _tour("Лапчи", "4–11 ноября. Паломнический поход.")
    decision = choose_strategy("Какие туры в сентябре?", "tour")
    assert filter_tours([september, november], decision) == [september]


def test_tour_list_formats_multiple_cards_without_single_tour_confirmation() -> None:
    tours = [
        _tour("Долина Маркха", "3–14 сентября. Треккинг.", "https://example.test/markha"),
        _tour("Тибет + Кайлас", "22 сентября – 9 октября. Паломничество.", "https://example.test/kailash"),
    ]
    answer = format_tour_list(tours, month=9)
    assert "Вот опубликованные туры в сентябре" in answer
    assert "Долина Маркха" in answer
    assert "Тибет + Кайлас" in answer
    assert "Да, мы организуем это путешествие" not in answer


def test_empty_month_result_is_honest_and_requests_manager_follow_up() -> None:
    answer = format_tour_list([], month=2)
    assert "не нашёл опубликованных туров в феврале" in answer
    assert "менеджеру" in answer
