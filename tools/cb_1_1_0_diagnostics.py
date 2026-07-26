from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.sales_assistant.handoff import HandoffPriority, HandoffReason
from backend.sales_assistant.handoff_engine import HandoffEngine
from backend.sales_assistant.lead_validator import LeadValidator


def main() -> None:
    engine = HandoffEngine()
    booking = engine.evaluate("Хочу забронировать место в туре")
    payment = engine.evaluate("Можно оплатить в рассрочку?")
    information = engine.evaluate("Какая программа тура?")
    validation = LeadValidator().validate(
        name="Анна",
        contact_channel="telegram",
        contact_value="@anna_lotus",
        email="anna@example.com",
    )

    assert booking.reason == HandoffReason.BOOKING_REQUEST
    assert booking.priority == HandoffPriority.HIGH
    assert payment.reason == HandoffReason.PAYMENT_QUESTION
    assert information.required is False
    assert validation.is_valid

    print("handoff_intent_detection=OK")
    print("handoff_priority=OK")
    print("mandatory_contact_contract=OK")


if __name__ == "__main__":
    main()
