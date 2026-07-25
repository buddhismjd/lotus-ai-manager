from backend.sales_assistant.state import DialogueState
from backend.structured_catalog.models import StructuredTour


def test_dialogue_state_remembers_exact_active_tour_id():
    state = DialogueState()
    tour = StructuredTour(
        id="lapchi",
        title="Непал — Лапчи, место силы Миларепы",
        url="https://example.test/lapchi",
        description="Программа Лапчи",
    )
    state.remember_active_tour(tour)
    assert state.active_tour_id == tour.id
    assert (state.active_title, state.active_url) == (tour.title, tour.url)
