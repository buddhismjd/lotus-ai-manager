from backend.integrations.tilda_store_discovery import (
    discover_store_parts_from_html,
)


def test_discovers_getproductslist_urls() -> None:
    source = """
    <script>
    fetch(
      "https://store.tildaapi.com/api/getproductslist/?" +
      "storepartuid=111111&recid=222222&slice=1"
    );
    </script>
    """

    parts = discover_store_parts_from_html(source)

    assert [(p.storepartuid, p.recid) for p in parts] == [
        ("111111", "222222"),
    ]


def test_discovers_inline_configs_and_deduplicates() -> None:
    source = """
    <div id="rec333333"></div>
    <script>
      var config = {"recid":333333,"storepartuid":444444};
      var duplicate = {
        "storepartuid": "444444",
        "recid": "333333"
      };
    </script>
    """

    parts = discover_store_parts_from_html(source)

    assert len(parts) == 1
    assert parts[0].storepartuid == "444444"
    assert parts[0].recid == "333333"


def test_discovers_multiple_store_blocks() -> None:
    source = """
    <script>
      var first = {"recid":100001,"storepartuid":200001};
      var second = {"recid":100002,"storepartuid":200002};
      var third = {"recid":100003,"storepartuid":200003};
    </script>
    """

    parts = discover_store_parts_from_html(source)

    assert {
        (part.storepartuid, part.recid)
        for part in parts
    } == {
        ("200001", "100001"),
        ("200002", "100002"),
        ("200003", "100003"),
    }
