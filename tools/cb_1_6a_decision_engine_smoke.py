from dataclasses import dataclass

from backend.decision import DecisionContext, DecisionEngine, DecisionResult


@dataclass(frozen=True)
class DemoPolicy:
    name: str = "demo"
    priority: int = 100

    def decide(self, context: DecisionContext) -> DecisionResult | None:
        if context.intent != "tour":
            return None
        return DecisionResult(
            reply_text=context.current_reply,
            cards=context.cards,
            policy=self.name,
            reasons=("tour_intent",),
        )


def main() -> None:
    context = DecisionContext(
        user_message="Непал",
        intent="tour",
        current_reply="Туры найдены.",
        cards=({"type": "tour", "title": "Непал"},),
    )
    result = DecisionEngine((DemoPolicy(),)).decide(context)
    assert result.policy == "demo"
    assert result.cards[0]["type"] == "tour"
    print("CB-1.6A Decision Engine smoke: OK")


if __name__ == "__main__":
    main()
