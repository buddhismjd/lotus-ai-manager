from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.decision.models import DecisionContext, DecisionResult


@runtime_checkable
class DecisionPolicy(Protocol):
    """Extension point for recommendation, clarification, lead, and escalation."""

    name: str
    priority: int

    def decide(self, context: DecisionContext) -> DecisionResult | None:
        """Return a decision when applicable, otherwise defer to next policy."""
