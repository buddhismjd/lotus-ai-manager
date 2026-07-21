from __future__ import annotations

import json
from pathlib import Path

from backend.integrations.tilda_store_discovery import (
    StorePart,
    discover_store_parts_with_report,
    load_configured_store_parts,
)


def _write_sources(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "shops": [
                    {
                        "url": "https://example.test/shop",
                        "fallback_store_parts": [
                            {"storepartuid": "200001", "recid": "100001"}
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_configured_fallback_is_loaded(tmp_path: Path) -> None:
    path = tmp_path / "sources.json"
    _write_sources(path)
    assert load_configured_store_parts("https://example.test/shop", path) == [
        StorePart("200001", "100001", "configured_fallback")
    ]


def test_discovery_uses_config_when_html_has_no_store_markers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "sources.json"
    _write_sources(path)
    monkeypatch.setattr(
        "backend.integrations.tilda_store_discovery.fetch_shop_html",
        lambda *_args, **_kwargs: "<html><body>Shop</body></html>",
    )

    parts, report = discover_store_parts_with_report(
        "https://example.test/shop",
        sources_path=path,
    )

    assert parts == [StorePart("200001", "100001", "configured_fallback")]
    assert report.html_loaded is True
    assert report.html_candidates == 0
    assert report.configured_candidates == 1
    assert report.total_candidates == 1


def test_html_candidate_has_priority_over_configured_fallback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "sources.json"
    _write_sources(path)
    monkeypatch.setattr(
        "backend.integrations.tilda_store_discovery.fetch_shop_html",
        lambda *_args, **_kwargs: (
            '<script>const x={"recid":100002,"storepartuid":200001};</script>'
        ),
    )

    parts, report = discover_store_parts_with_report(
        "https://example.test/shop",
        sources_path=path,
    )

    assert parts == [StorePart("200001", "100002", "inline_config")]
    assert report.html_candidates == 1
    assert report.total_candidates == 1


def test_discovery_preserves_fallback_when_html_fetch_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "sources.json"
    _write_sources(path)

    def fail(*_args, **_kwargs):
        raise OSError("network unavailable")

    monkeypatch.setattr(
        "backend.integrations.tilda_store_discovery.fetch_shop_html",
        fail,
    )

    parts, report = discover_store_parts_with_report(
        "https://example.test/shop",
        sources_path=path,
    )

    assert parts == [StorePart("200001", "100001", "configured_fallback")]
    assert report.html_loaded is False
    assert report.error == "network unavailable"
