from backend.sales_assistant.service import SalesAssistant


def main() -> None:
    reply = SalesAssistant().reply("Что по Индии?", "catalog-3-0-smoke")
    print(reply.answer)
    print(f"cards={len(reply.items)}")
    for item in reply.items:
        print(f"- {item.get('title')}")
    if len(reply.items) < 3:
        raise SystemExit("FAILED: India query must return the complete published collection")
    print("CATALOG-3.0 smoke: OK")


if __name__ == "__main__":
    main()
