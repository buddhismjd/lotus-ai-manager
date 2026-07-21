from __future__ import annotations

from backend.sales_assistant.service import SalesAssistant


SCENARIOS = (
    ("exact_tour", "Есть тур на Кайлас?"),
    ("tour_price", "Сколько стоит тур на Кайлас?"),
    ("country_collection", "В Непал возите?"),
    ("tour_list", "Какие есть туры в сентябре?"),
)


def build_report() -> str:
    assistant = SalesAssistant()
    lines = ["AI Bodhi — Collection Compatibility Report"]
    for index, (name, query) in enumerate(SCENARIOS, start=1):
        reply = assistant.reply(query, f"compatibility-{index}")
        lines.extend(
            (
                "",
                f"[{name}] {query}",
                f"kind={reply.kind}",
                f"topic={reply.topic}",
                f"items={len(reply.items)}",
                f"needs_manager={reply.needs_manager}",
            )
        )
    return "\n".join(lines)


def main() -> None:
    print(build_report())


if __name__ == "__main__":
    main()
