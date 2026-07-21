from backend.integrations.tilda_store_discovery import discover_store_parts_with_report


def main() -> None:
    parts, report = discover_store_parts_with_report()
    print("AI BODHI TILDA DISCOVERY 2.0 REPORT")
    print(f"HTML discovery: {report.html_candidates}")
    print(f"Configured fallback: {report.configured_candidates}")
    print(f"Effective candidates: {len(parts)}")
    for part in parts:
        print(f"- {part.source}: {part.storepartuid}/{part.recid}")


if __name__ == "__main__":
    main()
