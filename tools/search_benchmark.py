from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.catalog.text_normalization import normalize_search_text
from backend.rag.dynamic_query_router import reload_catalog_index, route_query


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = PROJECT_ROOT / "benchmark" / "search_cases.json"
DEFAULT_CSV = PROJECT_ROOT / "data" / "search_benchmark.csv"
DEFAULT_HTML = PROJECT_ROOT / "data" / "search_benchmark.html"


def normalize(value: str | None) -> str:
    return normalize_search_text(value)


def evaluate(
    case: dict[str, Any],
    result: Any,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    expected_intent = case.get("expected_intent")

    if expected_intent and result.intent != expected_intent:
        errors.append(
            "intent: ожидалось "
            f"{expected_intent}, получено {result.intent}"
        )

    expected_title = normalize(
        case.get("expected_title_contains")
    )
    actual_title = normalize(result.matched_title)
    allow_no_match = bool(case.get("allow_no_match", False))

    if expected_title:
        if expected_title not in actual_title:
            errors.append(
                "title: ожидалось вхождение "
                f"{case['expected_title_contains']!r}, "
                f"получено {result.matched_title!r}"
            )
    elif not allow_no_match and result.matched_title is None:
        errors.append("title: совпадение не найдено")

    if allow_no_match and result.matched_title is not None:
        errors.append(
            "title: ожидалось отсутствие случайного совпадения, "
            f"получено {result.matched_title!r}"
        )

    return not errors, errors


def write_csv(
    rows: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "query",
        "passed",
        "intent",
        "confidence",
        "reason",
        "matched_title",
        "matched_url",
        "errors",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_html(
    rows: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total = len(rows)
    passed = sum(1 for row in rows if row["passed"])
    failed = total - passed

    body_rows = []

    for row in rows:
        status = "✅" if row["passed"] else "❌"
        body_rows.append(
            "<tr>"
            f"<td>{status}</td>"
            f"<td>{html.escape(row['query'])}</td>"
            f"<td>{html.escape(row['intent'])}</td>"
            f"<td>{row['confidence']:.2f}</td>"
            f"<td>{html.escape(row['matched_title'] or '-')}</td>"
            f"<td>{html.escape(row['errors'] or '-')}</td>"
            "</tr>"
        )

    document = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>AI Bodhi Search Benchmark</title>
</head>
<body>
<h1>AI Bodhi Search Benchmark</h1>
<p>Создан: {datetime.now().isoformat(timespec="seconds")}</p>
<p>Всего: {total}; успешно: {passed}; ошибки: {failed}</p>
<table border="1" cellpadding="6">
<thead>
<tr>
<th>Статус</th>
<th>Запрос</th>
<th>Intent</th>
<th>Confidence</th>
<th>Результат</th>
<th>Ошибки</th>
</tr>
</thead>
<tbody>
{''.join(body_rows)}
</tbody>
</table>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run AI Bodhi search benchmark "
            "on the real SQLite catalog."
        )
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES,
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=DEFAULT_HTML,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
    )
    args = parser.parse_args()

    cases = json.loads(
        args.cases.read_text(encoding="utf-8")
    )
    reload_catalog_index()
    rows: list[dict[str, Any]] = []

    for case in cases:
        result = route_query(case["query"])
        passed, errors = evaluate(case, result)
        rows.append(
            {
                "query": case["query"],
                "passed": passed,
                "intent": result.intent,
                "confidence": result.confidence,
                "reason": result.reason,
                "matched_title": result.matched_title or "",
                "matched_url": result.matched_url or "",
                "errors": " | ".join(errors),
            }
        )

    write_csv(rows, args.csv)
    write_html(rows, args.html)

    passed_count = sum(
        1
        for row in rows
        if row["passed"]
    )
    failed_count = len(rows) - passed_count

    print("=" * 72)
    print("AI BODHI SEARCH BENCHMARK")
    print("=" * 72)
    print(f"Всего:    {len(rows)}")
    print(f"Успешно:  {passed_count}")
    print(f"Ошибки:   {failed_count}")
    print(f"CSV:      {args.csv}")
    print(f"HTML:     {args.html}")

    if failed_count:
        print("\nПроблемные запросы:")

        for row in rows:
            if not row["passed"]:
                print(f"- {row['query']}: {row['errors']}")

    if args.strict and failed_count:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
