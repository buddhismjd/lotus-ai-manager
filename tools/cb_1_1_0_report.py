from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.sales_assistant.handoff_engine import HandoffEngine


def main() -> None:
    scenarios = {
        "booking": "Хочу забронировать место",
        "availability": "Есть ли свободные места?",
        "personal_conditions": "Нужен индивидуальный маршрут",
        "payment": "Можно оплатить в рассрочку?",
        "explicit_manager": "Свяжите меня с менеджером",
    }
    engine = HandoffEngine()
    detected = sum(engine.evaluate(message).required for message in scenarios.values())

    print("CB-1.1.0 — Conversation Handoff Engine")
    print("decision_mode=deterministic")
    print(f"handoff_scenarios={detected}")
    print("contact_contract=name,telegram_or_max,email")
    print("persistence=LeadRepository.save_handoff")
    print("manager_summary=deterministic")


if __name__ == "__main__":
    main()
