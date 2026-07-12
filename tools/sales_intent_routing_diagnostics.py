from backend.rag.dynamic_query_router import route_query


CASES = (
    ("Хотела бы на кору в Тибет съездить", "tour"),
    ("В Тибет возите?", "tour"),
    ("Есть чётки из Тибета?", "product"),
    ("Хочу консультацию буддолога", "psychologist"),
)


def main() -> int:
    print("=" * 72)
    print("AI BODHI SALES INTENT ROUTING DIAGNOSTICS")
    print("=" * 72)
    failures = 0
    for query, expected in CASES:
        route = route_query(query)
        ok = route.intent == expected
        failures += int(not ok)
        print(f"[{ 'OK' if ok else 'FAIL' }] {query}")
        print(f"  intent={route.intent} confidence={route.confidence:.2f} reason={route.reason}")
    print(f"Failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
