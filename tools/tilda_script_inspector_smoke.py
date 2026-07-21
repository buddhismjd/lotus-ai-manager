from backend.integrations.tilda_script_inspector import inspect_tilda_scripts


def main() -> int:
    html = '''<html><script>window.storeConfig = {"recid":123,"storepartuid":456,"productuid":789,"price":100};</script></html>'''
    inspection = inspect_tilda_scripts(html, "https://example.test/tproduct/789-item")
    assert inspection.aggregate_identifiers["recid"] == ["123"]
    assert inspection.aggregate_identifiers["storepartuid"] == ["456"]
    assert inspection.aggregate_identifiers["productuid"] == ["789"]
    assert inspection.scripts[0].assignments[0].name == "window.storeConfig"
    print("SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
