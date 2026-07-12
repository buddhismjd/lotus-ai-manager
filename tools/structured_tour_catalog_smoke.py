from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant


def main() -> int:
    reply = SalesAssistant().reply("Какие есть туры в сентябре?", "structured-catalog-smoke")
    passed = (
        reply.kind == "tour_list"
        and "Долина Маркха" in reply.answer
        and "Тибет + Кайлас" in reply.answer
    )
    print("SMOKE PASSED" if passed else "SMOKE FAILED")
    print(reply.answer)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
