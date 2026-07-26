from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    print("CB-1.2.0 — Widget Conversation Session")
    print("session_storage=SQLite")
    print("state_restore=DialogueState JSON")
    print("history_storage=dialogs,messages")
    print("widget_restore=GET /api/sales/session/{session_id}")
    print("handoff_state=persistent")


if __name__ == "__main__":
    main()
