from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tempfile

import backend.storage.database as database
from backend.sales_assistant.handoff import HandoffPriority, HandoffReason
from backend.sales_assistant.lead_summary import LeadSummaryBuilder, LeadSummaryContext
from backend.sales_assistant.lead_validator import LeadValidator
from backend.storage.repositories import LeadRepository


def main() -> None:
    validation = LeadValidator().validate(
        name="Евгения",
        contact_channel="Telegram",
        contact_value="evgenia_lotus",
        email="evgenia@example.com",
    )
    assert validation.data is not None
    summary = LeadSummaryBuilder().build(
        LeadSummaryContext(
            interest_title="Путешествие в Непал",
            last_question="Можно ли забронировать место?",
            handoff_reason=HandoffReason.BOOKING_REQUEST,
        )
    )

    original_dir = database.DATA_DIR
    original_file = database.DATABASE_FILE
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database.DATA_DIR = root
            database.DATABASE_FILE = root / "smoke.db"
            saved = LeadRepository().save_handoff(
                contact=validation.data,
                reason=HandoffReason.BOOKING_REQUEST,
                priority=HandoffPriority.HIGH,
                manager_summary=summary,
                interest="Путешествие в Непал",
                session_id="smoke-session",
            )
            assert saved.id == 1
    finally:
        database.DATA_DIR = original_dir
        database.DATABASE_FILE = original_file

    print("lead_repository_smoke=OK")
    print(summary)


if __name__ == "__main__":
    main()
