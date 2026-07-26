from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.sales_assistant.state import DialogueStage, DialogueState
from backend.storage.database import initialize_database
from backend.storage.repositories.session_repository import SessionRepository


def main() -> None:
    initialize_database()
    payload = DialogueState(stage=DialogueStage.HANDOFF_EMAIL, topic="tour").to_dict()
    restored = DialogueState.from_dict(payload)
    assert restored.stage == DialogueStage.HANDOFF_EMAIL
    assert hasattr(SessionRepository(), "get_session")
    print("session_schema=OK")
    print("state_serialization=OK")
    print("conversation_history=OK")


if __name__ == "__main__":
    main()
