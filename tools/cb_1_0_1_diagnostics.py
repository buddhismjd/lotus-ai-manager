from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.sales_assistant.handoff import HandoffDecision, HandoffReason
from backend.sales_assistant.lead_summary import LeadSummaryBuilder, LeadSummaryContext
from backend.sales_assistant.lead_validator import LeadValidator


def main() -> int:
    decision = HandoffDecision.transfer(HandoffReason.AVAILABILITY_REQUEST)
    validation = LeadValidator().validate(
        name="Анна",
        contact_channel="telegram",
        contact_value="anna_lotus",
        email="anna@example.com",
    )
    summary = LeadSummaryBuilder().build(
        LeadSummaryContext(
            interest_title="Тур в Лапчи",
            last_question="Есть ли свободные места?",
            handoff_reason=HandoffReason.AVAILABILITY_REQUEST,
        )
    )

    checks = {
        "handoff_contract": decision.required and decision.reason is not None,
        "lead_validation": validation.is_valid,
        "deterministic_summary": summary.startswith("Клиент интересуется:"),
    }
    for name, ok in checks.items():
        print(f"{name}={'OK' if ok else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
