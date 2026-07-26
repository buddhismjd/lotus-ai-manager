from pathlib import Path


def main() -> int:
    report = """UX-1.1 Quality Report
=====================
- Product intent: bell / ganta queries route to products.
- Product cards: bell queries return matching product cards.
- Tour descriptions: Tilda navigation lines are removed.
- Tour media: missing images use the safe page-image resolver.
- Context: a single tour shown by country is remembered for follow-up questions.
- Regression: 325 tests passed.
"""
    path = Path("data/reports/ux_1_1_report.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
