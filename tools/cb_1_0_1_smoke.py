from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.sales_assistant.handoff import HandoffReason
from backend.sales_assistant.lead_summary import LeadSummaryBuilder, LeadSummaryContext
from backend.sales_assistant.lead_validator import LeadValidator


def main() -> int:
    validation = LeadValidator().validate(
        name="Елена",
        contact_channel="MAX",
        contact_value="elena-max",
        email="elena@example.com",
    )
    if not validation.is_valid:
        print("lead_domain_smoke=FAIL")
        return 1

    summary = LeadSummaryBuilder().build(
        LeadSummaryContext(
            interest_title="Путешествие в Непал",
            last_question="Можно ли забронировать место?",
            handoff_reason=HandoffReason.BOOKING_REQUEST,
        )
    )
    print("lead_domain_smoke=OK")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
