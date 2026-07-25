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
    EMAIL_VALUE = "email_value"
    ARTISAN_SOCIAL_METHOD = "artisan_social_method"
    ARTISAN_SOCIAL_VALUE = "artisan_social_value"
    ARTISAN_EMAIL = "artisan_email"


@dataclass(slots=True)
class LeadDraft:
    interest: str | None = None
    name: str | None = None
    contact_method: str | None = None
    contact_value: str | None = None
    comment: str | None = None
    conversation_summary: str | None = None
    subscription_topic: str | None = None
    consent_text: str | None = None
    selection_category: str | None = None
    selection_aspect: str | None = None
    requested_height_min_cm: float | None = None
    requested_height_max_cm: float | None = None
    social_channel: str | None = None
    social_contact: str | None = None

    def clear(self) -> None:
        self.interest = None
        self.name = None
        self.contact_method = None
        self.contact_value = None
        self.comment = None
        self.conversation_summary = None
        self.subscription_topic = None
        self.consent_text = None
        self.selection_category = None
        self.selection_aspect = None
        self.requested_height_min_cm = None
        self.requested_height_max_cm = None
        self.social_channel = None
        self.social_contact = None


@dataclass(slots=True)
class DialogueState:
    """Session-scoped conversation context for the sales assistant."""

    topic: str = "unknown"
    goal: str | None = None
    stage: DialogueStage = DialogueStage.DISCOVERY
    last_query: str = ""
    month: int | None = None
    active_tour_id: str | None = None
    active_title: str | None = None
    active_url: str | None = None
    candidate_tour_ids: tuple[str, ...] = ()
    candidate_tour_titles: tuple[str, ...] = ()
    product_selection_category: str | None = None
    product_selection_aspect: str | None = None
    product_selection_height_min_cm: float | None = None
    product_selection_height_max_cm: float | None = None
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
        self.active_tour_id = tours[0].id if len(tours) == 1 else None
        self.active_title = tours[0].title if len(tours) == 1 else None
        self.active_url = tours[0].url if len(tours) == 1 else None

    def remember_active_tour(self, tour: StructuredTour) -> None:
        self.topic = "tour"
        self.goal = "tour_details"
        self.active_tour_id = tour.id
        self.active_title = tour.title
        self.active_url = tour.url

    def start_lead_capture(self) -> None:
        self.goal = "leave_contact"
        self.stage = DialogueStage.LEAD_NAME
        self.lead.clear()
        self.lead.interest = self.active_title or self.topic

    def start_email_followup(self) -> None:
        self.goal = "email_followup"
        self.stage = DialogueStage.EMAIL_VALUE
        self.lead.clear()
        self.lead.interest = self.active_title or self.topic
        self.lead.conversation_summary = self.last_query or self.lead.interest
        if self.topic == "tour":
            self.lead.subscription_topic = "new_tours"
            self.lead.consent_text = (
                "Согласие получать на email информацию о новых турах и путешествиях "
                "студии «Свет Лотоса»."
            )
        elif self.topic == "product":
            self.lead.subscription_topic = "new_products"
            self.lead.consent_text = (
                "Согласие получать на email информацию о новых товарах "
                "магазина «Свет Лотоса»."
            )
        elif self.topic == "psychologist":
            self.lead.subscription_topic = "psychologist_service_information"
            self.lead.consent_text = (
                "Согласие получить на email информацию о консультации "
                "психолога-буддолога и способах записи."
            )
        else:
            self.lead.subscription_topic = "requested_information"
            self.lead.consent_text = (
                "Согласие получить на email информацию по текущему запросу."
            )


    def remember_product_selection(
        self,
        *,
        category: str,
        aspect: str | None,
        height_min_cm: float | None,
        height_max_cm: float | None,
    ) -> None:
        self.topic = "product"
        self.goal = "product_selection"
        self.product_selection_category = category
        self.product_selection_aspect = aspect
        self.product_selection_height_min_cm = height_min_cm
        self.product_selection_height_max_cm = height_max_cm

    def start_artisan_selection(self) -> None:
        self.goal = "artisan_selection"
        self.stage = DialogueStage.ARTISAN_SOCIAL_METHOD
        self.lead.clear()
        self.lead.interest = self.active_title or self.product_selection_aspect or self.product_selection_category
        self.lead.selection_category = self.product_selection_category
        self.lead.selection_aspect = self.product_selection_aspect
        self.lead.requested_height_min_cm = self.product_selection_height_min_cm
        self.lead.requested_height_max_cm = self.product_selection_height_max_cm
        self.lead.consent_text = (
            "Согласие передать контакт в социальной сети и email для уточнения "
            "актуального наличия у мастеров и отправки персональной подборки."
        )

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
                active_tour_id=state.active_tour_id,
                active_title=state.active_title,
                active_url=state.active_url,
                candidate_tour_ids=state.candidate_tour_ids,
                candidate_tour_titles=state.candidate_tour_titles,
                product_selection_category=state.product_selection_category,
                product_selection_aspect=state.product_selection_aspect,
                product_selection_height_min_cm=state.product_selection_height_min_cm,
                product_selection_height_max_cm=state.product_selection_height_max_cm,
                lead=LeadDraft(
                    interest=state.lead.interest,
                    name=state.lead.name,
                    contact_method=state.lead.contact_method,
                    contact_value=state.lead.contact_value,
                    comment=state.lead.comment,
                    conversation_summary=state.lead.conversation_summary,
                    subscription_topic=state.lead.subscription_topic,
                    consent_text=state.lead.consent_text,
                    selection_category=state.lead.selection_category,
                    selection_aspect=state.lead.selection_aspect,
                    requested_height_min_cm=state.lead.requested_height_min_cm,
                    requested_height_max_cm=state.lead.requested_height_max_cm,
                    social_channel=state.lead.social_channel,
                    social_contact=state.lead.social_contact,
                ),
            )


__all__ = ["DialogueStage", "DialogueState", "DialogueStateStore", "LeadDraft"]
