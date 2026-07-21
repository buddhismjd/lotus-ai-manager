from backend.integrations.tilda_store_discovery import discover_store_parts_with_report


def main() -> None:
    parts, report = discover_store_parts_with_report()
    assert parts, "No Tilda store candidates found"
    assert all(part.storepartuid.isdigit() and part.recid.isdigit() for part in parts)
    print("SMOKE PASSED")
    print(f"Candidates: {len(parts)}")
    print(f"Configured fallback available: {report.configured_candidates > 0}")


if __name__ == "__main__":
    main()
