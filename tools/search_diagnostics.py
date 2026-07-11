from __future__ import annotations

import csv
import html
from collections import Counter
from datetime import datetime
from pathlib import Path

from backend.rag.dynamic_query_router import (
    catalog_index,
    detect_product_kind,
    reload_catalog_index,
    route_query,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "search_diagnostics.csv"
HTML_PATH = PROJECT_ROOT / "data" / "search_diagnostics.html"

QUERIES = [
    "Хочу статую Будды",
    "Есть ваджра?",
    "Покажи тханку",
    "Нужна поющая чаша",
    "Поход в Лапчи",
    "Есть поездка в Непал?",
    "Хочу защитный амулет",
    "Статуя Зеленой Тары",
    "Амулет Ченрезига",
    "Есть велосипед?",
    "стату будды",
]


def matching_kind_titles(kind: str | None) -> list[str]:
    if not kind:
        return []

    return [
        item["title"]
        for item in catalog_index().get("product", [])
        if item.get("product_kind") == kind
    ]


def write_csv(rows: list[dict[str, str]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "query",
                "detected_kind",
                "intent",
                "matched_title",
                "reason",
                "same_kind_candidates",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_html(
    rows: list[dict[str, str]],
    kind_counts: Counter,
    unknown_products: list[str],
) -> None:
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)

    kind_table = "".join(
        f"<tr><td>{html.escape(kind or 'unknown')}</td><td>{count}</td></tr>"
        for kind, count in sorted(kind_counts.items(), key=lambda item: str(item[0]))
    )

    query_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['query'])}</td>"
        f"<td>{html.escape(row['detected_kind'] or '-')}</td>"
        f"<td>{html.escape(row['intent'])}</td>"
        f"<td>{html.escape(row['matched_title'] or '-')}</td>"
        f"<td>{html.escape(row['reason'])}</td>"
        f"<td>{html.escape(row['same_kind_candidates'] or '-')}</td>"
        "</tr>"
        for row in rows
    )

    unknown_list = "".join(
        f"<li>{html.escape(title)}</li>"
        for title in unknown_products
    )

    document = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Bodhi Search Diagnostics</title>
<style>
body {{
  margin: 0;
  padding: 32px;
  font-family: Arial, sans-serif;
  background: #f7f4fa;
  color: #30243b;
}}
main {{
  max-width: 1300px;
  margin: 0 auto;
}}
.card {{
  background: #fff;
  border: 1px solid #e8dfef;
  border-radius: 18px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 12px 36px rgba(48,36,59,.07);
}}
table {{
  width: 100%;
  border-collapse: collapse;
}}
th, td {{
  padding: 11px;
  border-bottom: 1px solid #eee7f2;
  text-align: left;
  vertical-align: top;
}}
th {{
  background: #f1eafa;
}}
code {{
  background: #f3edf8;
  padding: 2px 5px;
  border-radius: 5px;
}}
</style>
</head>
<body>
<main>
<section class="card">
  <h1>AI Bodhi Search Diagnostics</h1>
  <p>Создан: {datetime.now().isoformat(timespec="seconds")}</p>
</section>

<section class="card">
  <h2>Распределение типов товаров</h2>
  <table>
    <thead><tr><th>Тип</th><th>Количество</th></tr></thead>
    <tbody>{kind_table}</tbody>
  </table>
</section>

<section class="card">
  <h2>Диагностика проблемных запросов</h2>
  <table>
    <thead>
      <tr>
        <th>Запрос</th>
        <th>Распознанный тип</th>
        <th>Intent</th>
        <th>Результат</th>
        <th>Причина</th>
        <th>Товары того же типа</th>
      </tr>
    </thead>
    <tbody>{query_rows}</tbody>
  </table>
</section>

<section class="card">
  <h2>Товары без определённого типа</h2>
  <p>Если нужные статуи, тханки или чаши находятся здесь, словарь типов нужно расширить.</p>
  <ul>{unknown_list or '<li>Нет</li>'}</ul>
</section>
</main>
</body>
</html>
"""
    HTML_PATH.write_text(document, encoding="utf-8")


def main() -> None:
    reload_catalog_index()
    products = catalog_index().get("product", [])

    kind_counts = Counter(
        item.get("product_kind") or "unknown"
        for item in products
    )

    unknown_products = [
        item["title"]
        for item in products
        if not item.get("product_kind")
    ]

    rows: list[dict[str, str]] = []

    for query in QUERIES:
        detected_kind = detect_product_kind(query)
        route = route_query(query)
        candidates = matching_kind_titles(detected_kind)

        rows.append(
            {
                "query": query,
                "detected_kind": detected_kind or "",
                "intent": route.intent,
                "matched_title": route.matched_title or "",
                "reason": route.reason,
                "same_kind_candidates": " | ".join(candidates[:20]),
            }
        )

    write_csv(rows)
    write_html(rows, kind_counts, unknown_products)

    print("=" * 72)
    print("AI BODHI SEARCH DIAGNOSTICS")
    print("=" * 72)
    print(f"Товаров в индексе: {len(products)}")
    print("Типы товаров:")

    for kind, count in sorted(kind_counts.items()):
        print(f"  {kind}: {count}")

    print(f"\nCSV:  {CSV_PATH}")
    print(f"HTML: {HTML_PATH}")


if __name__ == "__main__":
    main()
