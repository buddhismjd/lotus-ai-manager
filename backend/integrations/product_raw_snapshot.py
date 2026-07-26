from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen


_PRODUCT_ASSIGNMENT_RE = re.compile(r"\bvar\s+product\s*=\s*", re.IGNORECASE)
_PRODUCT_UID_FROM_URL_RE = re.compile(r"/tproduct/(?P<uid>\d+)(?:[-/]|$)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class RawProductSnapshot:
    product_uid: str
    page_url: str
    product_data: dict[str, Any]
    raw_json: str
    html_sha256: str
    snapshot_sha256: str
    captured_at: str
    source_kind: str = "product_page_script"
    extractor_version: str = "2.2"


def fetch_product_html(url: str, timeout: float = 30.0) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "AI-Bodhi-Product-Snapshot/2.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _balanced_json_object(text: str, start: int) -> str:
    if start >= len(text) or text[start] != "{":
        raise ValueError("Начало объекта product не найдено")

    depth = 0
    quote: str | None = None
    escaped = False

    for index in range(start, len(text)):
        character = text[index]

        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue

        if character in {'"', "'"}:
            quote = character
            continue

        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    raise ValueError("Объект product не закрыт")


def _product_objects(raw_html: str) -> list[tuple[dict[str, Any], str]]:
    objects: list[tuple[dict[str, Any], str]] = []
    for match in _PRODUCT_ASSIGNMENT_RE.finditer(raw_html):
        object_start = raw_html.find("{", match.end())
        if object_start < 0:
            continue
        try:
            raw_json = _balanced_json_object(raw_html, object_start)
            data = json.loads(raw_json)
        except (ValueError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and str(data.get("uid") or "").strip():
            objects.append((data, raw_json))
    return objects


def extract_product_object(
    raw_html: str,
    *,
    expected_uid: str | None = None,
) -> tuple[dict[str, Any], str]:
    objects = _product_objects(raw_html)
    if not objects:
        raise ValueError("На странице не найден валидный JavaScript-объект var product")

    expected = str(expected_uid or "").strip()
    if expected:
        for data, raw_json in objects:
            if str(data.get("uid") or "").strip() == expected:
                return data, raw_json
        raise ValueError(f"На странице не найден объект product с uid={expected}")

    if len(objects) > 1:
        raise ValueError(
            "На странице найдено несколько объектов product; требуется ожидаемый uid"
        )
    return objects[0]


def build_raw_snapshot(raw_html: str, page_url: str) -> RawProductSnapshot:
    uid_match = _PRODUCT_UID_FROM_URL_RE.search(page_url)
    expected_uid = uid_match.group("uid") if uid_match else None
    product_data, raw_json = extract_product_object(
        raw_html, expected_uid=expected_uid
    )
    normalized_json = json.dumps(
        product_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return RawProductSnapshot(
        product_uid=str(product_data["uid"]),
        page_url=page_url,
        product_data=product_data,
        raw_json=raw_json,
        html_sha256=hashlib.sha256(raw_html.encode("utf-8")).hexdigest(),
        snapshot_sha256=hashlib.sha256(normalized_json.encode("utf-8")).hexdigest(),
        captured_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source_kind="product_page_script",
        extractor_version="2.2",
    )


def load_raw_snapshot(url: str, timeout: float = 30.0) -> RawProductSnapshot:
    return build_raw_snapshot(fetch_product_html(url, timeout=timeout), url)


__all__ = [
    "RawProductSnapshot",
    "fetch_product_html",
    "extract_product_object",
    "build_raw_snapshot",
    "load_raw_snapshot",
]
