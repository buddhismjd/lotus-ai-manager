from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from threading import RLock

from backend.structured_catalog.models import StructuredTour


class DialogueStage(StrEnum):
    DISCOVERY = "discovery"
    LEAD_NAME = "lead_name"
    LEAD_CONTACT_METHOD = "lead_contact_method"
    LEAD_CONTACT_VALUE = "lead_contact_value"
    LEAD_COMPLETE = "lead_complete"
    HANDOFF_NAME = "handoff_name"
    HANDOFF_CONTACT_METHOD = "handoff_contact_method"
    HANDOFF_CONTACT_VALUE = "handoff_contact_value"
    HANDOFF_EMAIL = "handoff_email"
    HANDOFF_COMPLETE = "handoff_complete"
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
    email: str | None = None
    handoff_reason: str | None = None
    handoff_priority: str | None = None

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
        self.email = None
        self.handoff_reason = None
        self.handoff_priority = None


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
    pending_clarification_query: str | None = None
    pending_clarification_type: str | None = None
    active_collection_topic: str | None = None
    active_collection_items: tuple[dict, ...] = ()
    lead: LeadDraft = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.lead is None:
            self.lead = LeadDraft()

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["stage"] = self.stage.value
        payload["candidate_tour_ids"] = list(self.candidate_tour_ids)
        payload["candidate_tour_titles"] = list(self.candidate_tour_titles)
        payload["active_collection_items"] = list(self.active_collection_items)
        return payload

    @classmethod
    def from_dict(cls, payload: dict | None) -> "DialogueState":
        if not isinstance(payload, dict):
            return cls()
        lead_payload = payload.get("lead") if isinstance(payload.get("lead"), dict) else {}
        stage_value = payload.get("stage", DialogueStage.DISCOVERY.value)
        try:
            stage = DialogueStage(stage_value)
        except ValueError:
            stage = DialogueStage.DISCOVERY
        return cls(
            topic=str(payload.get("topic") or "unknown"),
            goal=payload.get("goal"),
            stage=stage,
            last_query=str(payload.get("last_query") or ""),
            month=payload.get("month"),
            active_tour_id=payload.get("active_tour_id"),
            active_title=payload.get("active_title"),
            active_url=payload.get("active_url"),
            candidate_tour_ids=tuple(payload.get("candidate_tour_ids") or ()),
            candidate_tour_titles=tuple(payload.get("candidate_tour_titles") or ()),
            product_selection_category=payload.get("product_selection_category"),
            product_selection_aspect=payload.get("product_selection_aspect"),
            product_selection_height_min_cm=payload.get("product_selection_height_min_cm"),
            product_selection_height_max_cm=payload.get("product_selection_height_max_cm"),
            pending_clarification_query=payload.get("pending_clarification_query"),
            pending_clarification_type=payload.get("pending_clarification_type"),
            active_collection_topic=payload.get("active_collection_topic"),
            active_collection_items=tuple(
                item for item in (payload.get("active_collection_items") or ())
                if isinstance(item, dict)
            ),
            lead=LeadDraft(**{
                key: lead_payload.get(key)
                for key in LeadDraft.__dataclass_fields__
            }),
        )

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


    def start_handoff_capture(
        self,
        *,
        reason: str,
        priority: str,
        user_message: str,
    ) -> None:
        self.goal = "manager_handoff"
        self.stage = DialogueStage.HANDOFF_NAME
        self.lead.clear()
        self.lead.interest = self.active_title or self.topic
        self.lead.conversation_summary = user_message
        self.lead.handoff_reason = reason
        self.lead.handoff_priority = priority

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



    def start_commercial_clarification(self, *, query: str, clarification_type: str) -> None:
        self.goal = "commercial_clarification"
        self.pending_clarification_query = query
        self.pending_clarification_type = clarification_type

    def consume_commercial_clarification(self, answer: str) -> str | None:
        if not self.pending_clarification_query:
            return None
        combined = f"{self.pending_clarification_query}. {answer}"
        self.pending_clarification_query = None
        self.pending_clarification_type = None
        self.goal = None
        return combined

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


    def remember_collection(self, *, topic: str, items: tuple[dict, ...]) -> None:
        """Keep the exact public cards shown to the visitor for follow-up turns."""
        self.active_collection_topic = topic
        self.active_collection_items = tuple(dict(item) for item in items)
        self.active_title = None
        self.active_url = None

    def clear_collection(self) -> None:
        self.active_collection_topic = None
        self.active_collection_items = ()

    def clear_candidates(self) -> None:
        self.candidate_tour_ids = ()
        self.candidate_tour_titles = ()

    def clear_tour_context(self) -> None:
        """Forget a previously selected/listed tour before a new direction query."""
        self.month = None
        self.active_tour_id = None
        self.active_title = None
        self.active_url = None
        self.clear_candidates()


class DialogueStateStore:
    """Thread-safe state cache with optional persistent backing repository."""

    def __init__(self, repository=None) -> None:
        self._states: dict[str, DialogueState] = {}
        self._repository = repository
        self._lock = RLock()

    def get(self, session_id: str) -> DialogueState:
        with self._lock:
            if session_id not in self._states:
                payload = self._repository.get_state(session_id) if self._repository else None
                self._states[session_id] = DialogueState.from_dict(payload)
            return self._states[session_id]

    def persist(self, session_id: str) -> None:
        if self._repository is None:
            return
        with self._lock:
            state = self._states.setdefault(session_id, DialogueState())
            handoff_status = (
                "complete" if state.stage == DialogueStage.HANDOFF_COMPLETE
                else "collecting" if state.stage.value.startswith("handoff_")
                else "none"
            )
            self._repository.save_state(
                session_id, state.to_dict(), handoff_status=handoff_status
            )

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._states.pop(session_id, None)
            if self._repository is not None:
                self._repository.reset(session_id)

    def snapshot(self, session_id: str) -> DialogueState:
        with self._lock:
            return DialogueState.from_dict(self.get(session_id).to_dict())


__all__ = ["DialogueStage", "DialogueState", "DialogueStateStore", "LeadDraft"]
