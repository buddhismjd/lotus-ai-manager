from backend.rag.dynamic_query_router import route_query


QUERIES = (
    "Хотела бы на кору в Тибет съездить",
    "Хочу поехать в Непал",
    "На Кайлас возите?",
    "Есть чётки из Тибета?",
    "Есть ваджра?",
    "Хочу консультацию буддолога",
)


def main() -> int:
    print("AI BODHI MVP-1.2 — INTENT ROUTING REPORT")
    totals: dict[str, int] = {}
    for query in QUERIES:
        route = route_query(query)
        totals[route.intent] = totals.get(route.intent, 0) + 1
        print(f"- {route.intent:12} | {route.confidence:.2f} | {route.reason:24} | {query}")
    print("Totals:")
    for intent, count in sorted(totals.items()):
        print(f"- {intent}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
