from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import KNOWLEDGE_FILE, SITE_URL
from backend.integrations.tilda_api import TildaAPIClient
from backend.integrations.tilda_sync import build_api_page, load_existing_products
from backend.parser.site_parser import normalize_url
from backend.rag.knowledge_builder import synchronize_knowledge_documents
from backend.storage.database import (
    finish_tilda_sync_run,
    get_tilda_page_snapshots,
    initialize_database,
    replace_tilda_page_snapshots,
    start_tilda_sync_run,
)

SYNC_SCHEMA_VERSION = 1


@dataclass
class TildaSyncResult:
    run_id: str
    status: str
    pages_count: int = 0
    chunks_count: int = 0
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    retained_after_error: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    knowledge: dict[str, Any] = field(default_factory=dict)
    database: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "pages_count": self.pages_count,
            "chunks_count": self.chunks_count,
            "added_count": len(self.added),
            "changed_count": len(self.changed),
            "unchanged_count": len(self.unchanged),
            "removed_count": len(self.removed),
            "retained_after_error_count": len(self.retained_after_error),
            "added": self.added,
            "changed": self.changed,
            "unchanged": self.unchanged,
            "removed": self.removed,
            "retained_after_error": self.retained_after_error,
            "errors": self.errors,
            "database": self.database,
        }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def page_meta_fingerprint(page_meta: dict[str, Any]) -> str:
    """Stable fingerprint for page-list metadata used to avoid downloading unchanged pages."""
    ignored = {"sort", "img", "featureimg"}
    stable = {key: value for key, value in page_meta.items() if key not in ignored}
    return _sha256(_canonical_json(stable))


def page_content_hash(page: dict[str, Any]) -> str:
    payload = {
        "url": page.get("url", ""),
        "title": page.get("title", ""),
        "page_type": page.get("page_type", "general"),
        "text": page.get("text", ""),
        "enabled": bool(page.get("enabled", True)),
        "priority": int(page.get("priority", 0)),
    }
    return _sha256(_canonical_json(payload))


def _load_existing_knowledge() -> dict[str, Any]:
    if not KNOWLEDGE_FILE.exists():
        return {"pages": [], "chunks": []}
    try:
        return json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"pages": [], "chunks": []}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _chunks_by_url(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        url = normalize_url(str(chunk.get("page_url") or ""))
        if url:
            result.setdefault(url, []).append(dict(chunk))
    return result


def _page_map(pages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for page in pages:
        url = normalize_url(str(page.get("url") or ""))
        if url:
            item = dict(page)
            item["url"] = url
            result[url] = item
    return result


def _type_counts(pages: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for page in pages:
        page_type = str(page.get("page_type") or "general")
        counts[page_type] = counts.get(page_type, 0) + 1
    return counts


def synchronize_tilda_project(
    client: TildaAPIClient | None = None,
    project_id: str | None = None,
    *,
    force: bool = False,
) -> TildaSyncResult:
    """Synchronize the single Svet Lotosa Tilda project safely and incrementally.

    Unchanged pages are restored from the local mirror. A page that fails to download
    remains available from the previous successful mirror. The knowledge file is
    replaced atomically only after a consistent candidate mirror is built.
    """
    initialize_database()
    resolved_project_id = (project_id or os.getenv("TILDA_PROJECT_ID", "")).strip()
    if not resolved_project_id:
        raise RuntimeError("В .env не задан TILDA_PROJECT_ID")

    run_id = uuid.uuid4().hex
    start_tilda_sync_run(run_id, resolved_project_id)
    result = TildaSyncResult(run_id=run_id, status="running")

    try:
        api = client or TildaAPIClient()
        page_list = api.get_pages(resolved_project_id)
        existing_knowledge = _load_existing_knowledge()
        existing_pages = _page_map(list(existing_knowledge.get("pages", [])))
        existing_chunks = _chunks_by_url(list(existing_knowledge.get("chunks", [])))
        snapshots = get_tilda_page_snapshots()

        candidate_pages: dict[str, dict[str, Any]] = {}
        candidate_chunks: dict[str, list[dict[str, Any]]] = {}
        next_snapshots: dict[str, dict[str, str]] = {}
        listed_urls: set[str] = set()

        for page_meta in page_list:
            page_id = str(page_meta.get("id") or "").strip()
            if not page_id:
                continue

            alias = str(page_meta.get("alias") or "").strip().strip("/")
            page_url = normalize_url(
                f"{SITE_URL.rstrip('/')}/{alias}" if alias else f"{SITE_URL.rstrip('/')}/page{page_id}.html"
            )
            listed_urls.add(page_url)
            meta_hash = page_meta_fingerprint(page_meta)
            previous_snapshot = snapshots.get(page_id)
            can_reuse = (
                not force
                and previous_snapshot is not None
                and previous_snapshot.get("meta_hash") == meta_hash
                and page_url in existing_pages
            )

            if can_reuse:
                candidate_pages[page_url] = existing_pages[page_url]
                candidate_chunks[page_url] = existing_chunks.get(page_url, [])
                next_snapshots[page_id] = {
                    "page_url": page_url,
                    "meta_hash": meta_hash,
                    "content_hash": previous_snapshot.get("content_hash", ""),
                }
                result.unchanged.append(page_url)
                continue

            try:
                page_data = api.get_page(page_id)
                page, chunks = build_api_page(page_meta, page_data)
                if page is None:
                    continue
                page_url = normalize_url(str(page["url"]))
                listed_urls.add(page_url)
                content_hash = page_content_hash(page)
                page["content_hash"] = content_hash
                page["source_meta_hash"] = meta_hash
                candidate_pages[page_url] = page
                candidate_chunks[page_url] = chunks
                next_snapshots[page_id] = {
                    "page_url": page_url,
                    "meta_hash": meta_hash,
                    "content_hash": content_hash,
                }
                previous_hash = (previous_snapshot or {}).get("content_hash")
                if page_url not in existing_pages:
                    result.added.append(page_url)
                elif previous_hash != content_hash:
                    result.changed.append(page_url)
                else:
                    result.unchanged.append(page_url)
            except Exception as exc:
                result.errors.append({"page_id": page_id, "url": page_url, "error": str(exc)})
                if page_url in existing_pages:
                    candidate_pages[page_url] = existing_pages[page_url]
                    candidate_chunks[page_url] = existing_chunks.get(page_url, [])
                    result.retained_after_error.append(page_url)
                    if previous_snapshot:
                        next_snapshots[page_id] = dict(previous_snapshot)

        # Product crawler pages are maintained by their dedicated synchronizer.
        product_pages, product_chunks = load_existing_products()
        product_chunk_map = _chunks_by_url(product_chunks)
        for product_page in product_pages:
            source_name = str(product_page.get("source") or "")
            if source_name.startswith("tilda"):
                continue
            url = normalize_url(str(product_page.get("url") or ""))
            if url and url not in candidate_pages:
                item = dict(product_page)
                item["source"] = source_name or "catalog_crawler"
                candidate_pages[url] = item
                candidate_chunks[url] = product_chunk_map.get(url, [])

        tilda_existing_urls = {
            url for url, page in existing_pages.items()
            if str(page.get("source", "")).startswith("tilda")
        }
        result.removed = sorted(tilda_existing_urls - listed_urls)

        pages = sorted(candidate_pages.values(), key=lambda item: str(item.get("url", "")))
        chunks: list[dict[str, Any]] = []
        for page in pages:
            url = normalize_url(str(page.get("url") or ""))
            for chunk in candidate_chunks.get(url, []):
                item = dict(chunk)
                item["page_url"] = url
                item["id"] = str(len(chunks) + 1)
                chunks.append(item)

        knowledge = {
            "schema_version": SYNC_SCHEMA_VERSION,
            "site": SITE_URL,
            "project_id": resolved_project_id,
            "source": "tilda_incremental_mirror",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "sync_run_id": run_id,
            "pages_count": len(pages),
            "chunks_count": len(chunks),
            "type_counts": _type_counts(pages),
            "errors_count": len(result.errors),
            "pages": pages,
            "chunks": chunks,
            "errors": result.errors,
        }

        _atomic_write_json(KNOWLEDGE_FILE, knowledge)
        replace_tilda_page_snapshots(next_snapshots)
        database_result = synchronize_knowledge_documents(knowledge)

        result.status = "completed_with_errors" if result.errors else "completed"
        result.pages_count = len(pages)
        result.chunks_count = len(chunks)
        result.knowledge = knowledge
        result.database = database_result
        finish_tilda_sync_run(run_id, result.status, result.as_dict())
        return result
    except Exception as exc:
        result.status = "failed"
        result.errors.append({"error": str(exc)})
        finish_tilda_sync_run(run_id, "failed", result.as_dict())
        raise
