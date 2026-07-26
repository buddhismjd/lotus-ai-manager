from __future__ import annotations

import json
from pathlib import Path

from backend.integrations.tilda_knowledge_sync import (
    _atomic_write_json,
    page_content_hash,
    page_meta_fingerprint,
)


def test_page_meta_fingerprint_is_stable_and_ignores_presentation_order() -> None:
    left = {"id": "10", "alias": "tour", "title": "Тур", "sort": "20"}
    right = {"title": "Тур", "sort": "99", "alias": "tour", "id": "10"}
    assert page_meta_fingerprint(left) == page_meta_fingerprint(right)


def test_page_content_hash_changes_when_semantic_page_data_changes() -> None:
    page = {
        "url": "https://svet-lotosa.tilda.ws/tour",
        "title": "Тур",
        "page_type": "tour",
        "text": "Описание",
        "enabled": True,
        "priority": 10,
    }
    changed = dict(page, text="Новое описание")
    assert page_content_hash(page) != page_content_hash(changed)


def test_atomic_write_json_replaces_complete_document(tmp_path: Path) -> None:
    destination = tmp_path / "knowledge.json"
    destination.write_text('{"old": true}', encoding="utf-8")
    _atomic_write_json(destination, {"pages": [{"url": "new"}]})
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "pages": [{"url": "new"}]
    }
    assert not list(tmp_path.glob("*.tmp"))


def test_sync_schema_is_present_in_database_definition() -> None:
    from backend.storage.database import SCHEMA

    assert "CREATE TABLE IF NOT EXISTS tilda_page_snapshots" in SCHEMA
    assert "CREATE TABLE IF NOT EXISTS tilda_sync_runs" in SCHEMA
