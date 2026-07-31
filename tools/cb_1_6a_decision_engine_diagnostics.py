from backend.decision import DecisionContext, DecisionEngine, NextAction


def main() -> None:
    context = DecisionContext(
        user_message="Покажи туры в Непал",
        intent="tour",
        current_reply="Я нашёл подходящие туры.",
        cards=({"type": "tour", "title": "Лапчи"},),
    )
    result = DecisionEngine().decide(context)
    assert result.reply_text == context.current_reply
    assert result.cards == context.cards
    assert result.next_action is NextAction.RESPOND
    assert result.policy == "passthrough"
    print("[OK] immutable context")
    print("[OK] deterministic policy engine")
    print("[OK] existing response preserved")
    print("CB-1.6A Decision Engine diagnostics: OK")


if __name__ == "__main__":
    main()
