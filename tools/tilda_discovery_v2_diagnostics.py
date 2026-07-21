from backend.integrations.tilda_store_discovery import discover_store_parts_with_report


def main() -> None:
    parts, report = discover_store_parts_with_report()
    print("=" * 72)
    print("AI BODHI TILDA DISCOVERY 2.0 DIAGNOSTICS")
    print("=" * 72)
    print(f"Shop URL:              {report.shop_url}")
    print(f"HTML loaded:           {report.html_loaded}")
    print(f"HTML size:             {report.html_size}")
    print(f"HTML candidates:       {report.html_candidates}")
    print(f"Configured candidates: {report.configured_candidates}")
    print(f"Total candidates:      {report.total_candidates}")
    if report.error:
        print(f"HTML error:            {report.error}")
    for part in parts:
        print(f"- recid={part.recid} storepartuid={part.storepartuid} source={part.source}")
    if not parts:
        raise SystemExit("DISCOVERY FAILED: no store candidates")


if __name__ == "__main__":
    main()
