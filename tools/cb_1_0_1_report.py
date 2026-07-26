from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.sales_assistant.handoff import HandoffReason
from backend.sales_assistant.lead_validator import LeadContactChannel


def main() -> int:
    print("CB-1.0.1 — Lead Domain Contract")
    print(f"handoff_reasons={len(HandoffReason)}")
    print("contact_channels=" + ",".join(channel.value for channel in LeadContactChannel))
    print("mandatory_fields=name,contact_channel,contact_value,email")
    print("summary_mode=deterministic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
