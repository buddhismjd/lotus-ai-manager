from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.sales_assistant.service import SalesAssistant
from backend.sales_assistant.state import DialogueStage
from backend.storage.repositories.session_repository import SessionRepository


def main() -> None:
    session_id = f"cb-1.2.0-smoke-{uuid.uuid4().hex}"
    first = SalesAssistant(SessionRepository())
    started = first.reply("Свяжите меня с менеджером", session_id)
    assert started.dialogue_stage == DialogueStage.HANDOFF_NAME.value
    second = SalesAssistant(SessionRepository())
    continued = second.reply("Анна", session_id)
    assert continued.dialogue_stage == DialogueStage.HANDOFF_CONTACT_METHOD.value
    history = second.session(session_id)
    assert len(history.messages) == 4
    print("widget_session_smoke=OK")
    print(f"restored_stage={continued.dialogue_stage}")
    print(f"persisted_messages={len(history.messages)}")


if __name__ == "__main__":
    main()
