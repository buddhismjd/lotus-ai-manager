from __future__ import annotations

from collections.abc import Iterable

from backend.decision.models import DecisionContext, DecisionResult
from backend.decision.policies import DecisionPolicy


class DecisionEngine:
    """Evaluate independent policies in deterministic priority order.

    CB-1.6A intentionally ships with no active production policies, so an
    engine without policies returns the existing reply and cards unchanged.
    """

    def __init__(self, policies: Iterable[DecisionPolicy] = ()) -> None:
        self._policies = tuple(
            sorted(policies, key=lambda policy: (-policy.priority, policy.name))
        )
        self._validate_policies()

    @property
    def policies(self) -> tuple[DecisionPolicy, ...]:
        return self._policies

    def decide(self, context: DecisionContext) -> DecisionResult:
        for policy in self._policies:
            decision = policy.decide(context)
            if decision is not None:
                return decision
        return DecisionResult.passthrough(context)

    def _validate_policies(self) -> None:
        names: set[str] = set()
        for policy in self._policies:
            if not isinstance(policy, DecisionPolicy):
                raise TypeError("policy must implement DecisionPolicy")
            if not policy.name.strip():
                raise ValueError("policy name must not be empty")
            if policy.name in names:
                raise ValueError(f"duplicate decision policy: {policy.name}")
            names.add(policy.name)
