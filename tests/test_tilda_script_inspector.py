from backend.integrations.tilda_script_inspector import (
    inspect_tilda_scripts,
    render_script_report,
)


def test_extracts_ids_and_balanced_assignment() -> None:
    html = '''
    <script>
      window.t_store = {
        "recid": 100001,
        "storepartuid": 200001,
        "productuid": 300001,
        "image": "https://static.example/item.jpg"
      };
    </script>
    '''
    result = inspect_tilda_scripts(html, "https://example.test/tproduct/300001-item")
    assert result.aggregate_identifiers["recid"] == ["100001"]
    assert result.aggregate_identifiers["storepartuid"] == ["200001"]
    assert result.aggregate_identifiers["productuid"] == ["300001"]
    assignment = result.scripts[0].assignments[0]
    assert assignment.name == "window.t_store"
    assert assignment.json_valid is True


def test_does_not_cross_string_boundaries() -> None:
    html = '''<script>const text = "storepartuid=999"; window.cfg = {"recid":1};</script>'''
    result = inspect_tilda_scripts(html, "https://example.test/item")
    assert result.aggregate_identifiers["storepartuid"] == ["999"]
    assert result.scripts[0].assignments[0].name == "window.cfg"


def test_collects_urls_and_snippets() -> None:
    html = '''<script>fetch("https://example.test/getproductslist/?recid=1&storepartuid=2");</script>'''
    result = inspect_tilda_scripts(html, "https://example.test/item")
    assert any("getproductslist" in value for value in result.aggregate_urls)
    assert result.scripts[0].snippets["storepartuid"]


def test_report_contains_structural_sections() -> None:
    result = inspect_tilda_scripts(
        '<script>window.cfg={"recid":1,"storepartuid":2,"productuid":3};</script>',
        "https://example.test/item",
    )
    report = render_script_report(result)
    assert "AGGREGATE IDENTIFIERS" in report
    assert "SCRIPT INVENTORY" in report
    assert "window.cfg" in report
