from backend.sales_assistant.service import SalesAssistant


def main() -> int:
    reply = SalesAssistant().reply(
        "Хотела бы на кору в Тибет съездить",
        "intent-routing-smoke",
    )
    assert reply.topic == "tour", reply
    assert reply.kind != "product", reply
    print("SMOKE PASSED")
    print(f"Topic: {reply.topic}")
    print(f"Kind: {reply.kind}")
    print(f"Title: {reply.title or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
