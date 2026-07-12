from backend.sales_assistant.strategy import choose_strategy

CASES = {
    "Какие есть туры в сентябре?": "tour_list",
    "Расскажите про Кайлас": "tour_details",
    "Сколько стоит Кайлас?": "tour_price",
    "Когда поездка на Кайлас?": "tour_date",
}


def main() -> None:
    print("=" * 72)
    print("AI BODHI SALES CONVERSATION STRATEGY DIAGNOSTICS")
    print("=" * 72)
    failures = 0
    for query, expected in CASES.items():
        actual = choose_strategy(query, "tour").strategy
        ok = actual == expected
        failures += int(not ok)
        print(f"{'OK' if ok else 'FAIL'} | {query} -> {actual}")
    print(f"Failures: {failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
