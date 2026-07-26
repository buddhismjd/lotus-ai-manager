from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.sales_assistant.conversation_decision import ConversationDecisionType, decide_conversation_action
from backend.sales_assistant.state import DialogueState


def main() -> None:
    gift = decide_conversation_action("Хочу подарок")
    direct = decide_conversation_action("Покажи тханки Калачакры")
    state = DialogueState()
    state.start_commercial_clarification(query="Хочу подарок", clarification_type="gift_purpose")
    combined = state.consume_commercial_clarification("Для практики")

    assert gift.action == ConversationDecisionType.ASK_CLARIFICATION
    print("single_clarification_decision=OK")
    assert direct.action == ConversationDecisionType.SHOW_RESULTS
    print("direct_selection_without_question=OK")
    assert combined == "Хочу подарок. Для практики"
    assert state.pending_clarification_query is None
    print("clarification_state_round_trip=OK")


if __name__ == "__main__":
    main()
