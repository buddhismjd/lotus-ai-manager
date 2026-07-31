from backend.decision import DecisionContext, DecisionEngine


def main() -> None:
    result = DecisionEngine().decide(
        DecisionContext(
            user_message="Покажи поющие чаши",
            intent="product",
            current_reply="Вот товары по вашему запросу.",
            cards=({"type": "product", "title": "Поющая чаша"},),
        )
    )
    print("CB-1.6A Decision Engine report")
    print(f"- policy={result.policy}")
    print(f"- next_action={result.next_action.value}")
    print(f"- cards={len(result.cards)}")
    print(f"- confidence={result.confidence:.2f}")
    print("- behaviour_change=no")


if __name__ == "__main__":
    main()
