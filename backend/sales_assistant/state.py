from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import RLock

from backend.structured_catalog.models import StructuredTour


class DialogueStage(StrEnum):
    DISCOVERY = "discovery"
    LEAD_NAME = "lead_name"
    LEAD_CONTACT_METHOD = "lead_contact_method"
    LEAD_CONTACT_VALUE = "lead_contact_value"
    LEAD_COMPLETE = "lead_complete"


@dataclass(slots=True)
class LeadDraft:
    interest: str | None = None
    name: str | None = None
    contact_method: str | None = None
    contact_value: str | None = None
    comment: str | None = None

    def clear(self) -> None:
        self.interest = None
        self.name = None
        self.contact_method = None
        self.contact_value = None
        self.comment = None


@dataclass(slots=True)
class DialogueState:
    """Session-scoped conversation context for the sales assistant."""

    topic: str = "unknown"
    goal: str | None = None
    stage: DialogueStage = DialogueStage.DISCOVERY
    last_query: str = ""
    month: int | None = None
    active_title: str | None = None
    active_url: str | None = None
    candidate_tour_ids: tuple[str, ...] = ()
    candidate_tour_titles: tuple[str, ...] = ()
    lead: LeadDraft = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.lead is None:
            self.lead = LeadDraft()

    def remember_tour_list(self, tours: list[StructuredTour], *, month: int | None) -> None:
        self.topic = "tour"
        self.goal = "choose_tour"
        self.month = month
        self.candidate_tour_ids = tuple(tour.id for tour in tours)
        self.candidate_tour_titles = tuple(tour.title for tour in tours)
        self.active_title = tours[0].title if len(tours) == 1 else None
        self.active_url = tours[0].url if len(tours) == 1 else None

    def remember_active_tour(self, tour: StructuredTour) -> None:
        self.topic = "tour"
        self.goal = "tour_details"
        self.active_title = tour.title
        self.active_url = tour.url

    def start_lead_capture(self) -> None:
        self.goal = "leave_contact"
        self.stage = DialogueStage.LEAD_NAME
        self.lead.clear()
        self.lead.interest = self.active_title or self.topic

    def clear_candidates(self) -> None:
        self.candidate_tour_ids = ()
        self.candidate_tour_titles = ()


class DialogueStateStore:
    """Thread-safe in-memory state store keyed by chat session."""

    def __init__(self) -> None:
        self._states: dict[str, DialogueState] = {}
        self._lock = RLock()

    def get(self, session_id: str) -> DialogueState:
        with self._lock:
            return self._states.setdefault(session_id, DialogueState())

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._states.pop(session_id, None)

    def snapshot(self, session_id: str) -> DialogueState:
        with self._lock:
            state = self._states.setdefault(session_id, DialogueState())
            return DialogueState(
                topic=state.topic,
                goal=state.goal,
                stage=state.stage,
                last_query=state.last_query,
                month=state.month,
                active_title=state.active_title,
                active_url=state.active_url,
                candidate_tour_ids=state.candidate_tour_ids,
                candidate_tour_titles=state.candidate_tour_titles,
                lead=LeadDraft(
                    interest=state.lead.interest,
                    name=state.lead.name,
                    contact_method=state.lead.contact_method,
                    contact_value=state.lead.contact_value,
                    comment=state.lead.comment,
                ),
            )


__all__ = ["DialogueStage", "DialogueState", "DialogueStateStore", "LeadDraft"]
