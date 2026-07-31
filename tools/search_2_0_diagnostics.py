from backend.sales_assistant.intent_router import classify_commercial_intent


CASES = {
    "Непал": "tour",
    "Индия зимой": "tour",
    "Кайлас": "tour",
    "Лапчи": "tour",
    "Покажи поющие чаши": "product",
    "Нужна консультация психолога": "psychologist",
    "Как связаться с менеджером?": "contacts",
}


def main() -> None:
    failures: list[str] = []
    for query, expected in CASES.items():
        actual = classify_commercial_intent(query).primary
        status = "OK" if actual == expected else "FAIL"
        print(f"[{status}] {query!r}: {actual}")
        if actual != expected:
            failures.append(f"{query}: expected {expected}, got {actual}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("Search-2.0 diagnostics: OK")


if __name__ == "__main__":
    main()
