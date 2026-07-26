from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HandoffReason(StrEnum):
    """Structured reasons why a dialogue must be continued by a manager."""

    KNOWLEDGE_NOT_FOUND = "knowledge_not_found"
    MANAGER_REQUIRED = "manager_required"
    BOOKING_REQUEST = "booking_request"
    AVAILABILITY_REQUEST = "availability_request"
    PERSONAL_CONDITIONS = "personal_conditions"
    PAYMENT_QUESTION = "payment_question"
    EXPLICIT_HANDOFF_REQUEST = "explicit_handoff_request"


class HandoffPriority(StrEnum):
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class HandoffDecision:
    """Result of a handoff evaluation, independent from UI wording."""

    required: bool
    reason: HandoffReason | None = None
    priority: HandoffPriority = HandoffPriority.NORMAL
    user_message: str | None = None

    def __post_init__(self) -> None:
        if self.required and self.reason is None:
            raise ValueError("A required handoff must have a reason.")
        if not self.required and self.reason is not None:
            raise ValueError("A non-required handoff cannot have a reason.")

    @classmethod
    def continue_with_ai(cls) -> "HandoffDecision":
        return cls(required=False)

    @classmethod
    def transfer(
        cls,
        reason: HandoffReason,
        *,
        priority: HandoffPriority = HandoffPriority.NORMAL,
        user_message: str | None = None,
    ) -> "HandoffDecision":
        return cls(
            required=True,
            reason=reason,
            priority=priority,
            user_message=user_message,
        )


__all__ = [
    "HandoffDecision",
    "HandoffPriority",
    "HandoffReason",
]
