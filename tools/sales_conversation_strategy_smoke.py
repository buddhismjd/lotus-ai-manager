from backend.catalog.models import Tour
from backend.sales_assistant.formatter import format_tour_list
from backend.sales_assistant.strategy import choose_strategy, filter_tours


def main() -> None:
    tours = [
        Tour(id="1", title="Долина Маркха", url="https://example.test/1", description="3–14 сентября"),
        Tour(id="2", title="Лапчи", url="https://example.test/2", description="4–11 ноября"),
    ]
    decision = choose_strategy("Какие туры в сентябре?", "tour")
    answer = format_tour_list(filter_tours(tours, decision), decision.month)
    assert "Долина Маркха" in answer and "Лапчи" not in answer
    print("SMOKE PASSED")
    print(answer)


if __name__ == "__main__":
    main()
