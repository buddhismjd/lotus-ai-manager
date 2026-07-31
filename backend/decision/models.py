from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence


class NextAction(str, Enum):
    """High-level action selected by the decision layer."""

    RESPOND = "respond"
    CLARIFY = "clarify"
    CAPTURE_LEAD = "capture_lead"
    ESCALATE = "escalate"


def _immutable_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """Read-only input for decision policies.

    The model deliberately uses generic values so the decision package does
    not import sales, catalogue, widget, or API modules. This keeps dependency
    direction one-way and prevents circular imports.
    """

    user_message: str
    intent: str = "unknown"
    search_results: tuple[Any, ...] = ()
    current_reply: str = ""
    cards: tuple[Mapping[str, Any], ...] = ()
    conversation_state: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "search_results", tuple(self.search_results))
        object.__setattr__(
            self,
            "cards",
            tuple(_immutable_mapping(card) for card in self.cards),
        )
        object.__setattr__(
            self,
            "conversation_state",
            _immutable_mapping(self.conversation_state),
        )
        object.__setattr__(self, "metadata", _immutable_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """Structured decision returned to the existing response pipeline."""

    reply_text: str
    cards: tuple[Mapping[str, Any], ...] = ()
    follow_up_question: str | None = None
    next_action: NextAction = NextAction.RESPOND
    confidence: float = 1.0
    policy: str = "passthrough"
    reasons: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        object.__setattr__(
            self,
            "cards",
            tuple(_immutable_mapping(card) for card in self.cards),
        )
        object.__setattr__(self, "reasons", tuple(self.reasons))
        object.__setattr__(self, "metadata", _immutable_mapping(self.metadata))

    @classmethod
    def passthrough(cls, context: DecisionContext) -> "DecisionResult":
        """Preserve current behaviour while the policy layer is introduced."""

        return cls(
            reply_text=context.current_reply,
            cards=context.cards,
            next_action=NextAction.RESPOND,
            confidence=1.0,
            policy="passthrough",
            reasons=("existing_response_preserved",),
        )
