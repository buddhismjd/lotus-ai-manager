from __future__ import annotations

from backend.integrations.tilda_store_discovery import (
    discover_store_parts_from_html,
)


def test_structured_pairs_are_not_cross_linked_between_objects() -> None:
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
    assert {part.source for part in parts} == {"inline_config"}


def test_url_source_has_precedence_over_inline_config() -> None:
    source = """
    <script>
      const url =
        "getproductslist/?storepartuid=200001&recid=100001";
      const nearby = {"recid":999999,"storepartuid":200001};
    </script>
    """

    parts = discover_store_parts_from_html(source)

    assert len(parts) == 1
    assert parts[0].storepartuid == "200001"
    assert parts[0].recid == "100001"
    assert parts[0].source == "getproductslist_url"


def test_single_html_tag_is_a_structured_pair() -> None:
    source = """
    <div
      data-record-id="100001"
      data-storepartuid="200001"
    ></div>
    """

    parts = discover_store_parts_from_html(source)

    assert len(parts) == 1
    assert parts[0].storepartuid == "200001"
    assert parts[0].recid == "100001"
    assert parts[0].source == "inline_config"


def test_proximity_remains_available_for_separate_markup() -> None:
    source = """
    <div data-record-id="100001"></div>
    <span>catalog marker</span>
    <div data-storepartuid="200001"></div>
    """

    parts = discover_store_parts_from_html(source)

    assert len(parts) == 1
    assert parts[0].storepartuid == "200001"
    assert parts[0].recid == "100001"
    assert parts[0].source == "proximity"
