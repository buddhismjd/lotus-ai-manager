from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.request import Request, urlopen


DEFAULT_SHOP_URL = "https://svet-lotosa.tilda.ws/svet-lotosa-shop"
DEFAULT_SOURCES_PATH = Path("backend/config/tilda_store_sources.json")

KNOWN_CATEGORY_LABELS = (
    "Все",
    "Статуи",
    "Алтарь",
    "Серьги",
    "Подвески",
    "Малы (четки)",
    "Гау",
    "Благовония",
    "Остальное",
)


@dataclass(frozen=True, slots=True)
class StorePart:
    storepartuid: str
    recid: str
    source: str = "html"


@dataclass(frozen=True, slots=True)
class DiscoveryReport:
    shop_url: str
    html_loaded: bool
    html_size: int
    html_candidates: int
    configured_candidates: int
    total_candidates: int
    error: str | None = None


_GET_PRODUCTS_URL_RE = re.compile(
    r"getproductslist/\?[^\"'<>\s]+",
    re.IGNORECASE,
)
_PART_ONLY_RE = re.compile(
    r"(?:storepartuid|storepart-uid|data-storepartuid)"
    r"[\"']?\s*[:=]\s*[\"']?(?P<part>\d+)",
    re.IGNORECASE,
)
_RECID_RE = re.compile(
    r"(?:recid|recordid|data-record-id)"
    r"[\"']?\s*[:=]\s*[\"']?(?P<recid>\d+)",
    re.IGNORECASE,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
_SOURCE_PRIORITY = {
    "getproductslist_url": 40,
    "inline_config": 30,
    "proximity": 20,
    "configured_fallback": 10,
}


def fetch_shop_html(url: str = DEFAULT_SHOP_URL, timeout: float = 30.0) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AI-Bodhi/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ru,en;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _query_value(url: str, key: str) -> str | None:
    match = re.search(
        rf"(?:\?|&amp;|&){re.escape(key)}=(\d+)",
        url,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def _add_part(
    result: dict[str, StorePart],
    storepartuid: str | None,
    recid: str | None,
    source: str,
) -> None:
    if not storepartuid or not recid:
        return
    if not storepartuid.isdigit() or not recid.isdigit():
        return
    candidate = StorePart(storepartuid=storepartuid, recid=recid, source=source)
    current = result.get(storepartuid)
    if current is None or _SOURCE_PRIORITY.get(source, 0) > _SOURCE_PRIORITY.get(current.source, 0):
        result[storepartuid] = candidate


def _iter_balanced_object_blocks(text: str) -> Iterator[str]:
    stack: list[int] = []
    quote: str | None = None
    escaped = False
    for index, character in enumerate(text):
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {'"', "'", "`"}:
            quote = character
            continue
        if character == "{":
            stack.append(index)
        elif character == "}" and stack:
            start = stack.pop()
            yield text[start:index + 1]


def _extract_single_pair(segment: str) -> tuple[str, str] | None:
    parts = {match.group("part") for match in _PART_ONLY_RE.finditer(segment)}
    recids = {match.group("recid") for match in _RECID_RE.finditer(segment)}
    if len(parts) != 1 or len(recids) != 1:
        return None
    return next(iter(parts)), next(iter(recids))


def _iter_structured_pairs(text: str) -> Iterator[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    for block in _iter_balanced_object_blocks(text):
        pair = _extract_single_pair(block)
        if pair is not None and pair not in seen:
            seen.add(pair)
            yield pair
    for tag in _HTML_TAG_RE.finditer(text):
        pair = _extract_single_pair(tag.group(0))
        if pair is not None and pair not in seen:
            seen.add(pair)
            yield pair


def discover_store_parts_from_html(raw_html: str) -> list[StorePart]:
    text = html.unescape(raw_html)
    result: dict[str, StorePart] = {}
    for match in _GET_PRODUCTS_URL_RE.finditer(text):
        url = match.group(0)
        _add_part(result, _query_value(url, "storepartuid"), _query_value(url, "recid"), "getproductslist_url")
    for storepartuid, recid in _iter_structured_pairs(text):
        _add_part(result, storepartuid, recid, "inline_config")
    for part_match in _PART_ONLY_RE.finditer(text):
        part = part_match.group("part")
        if part in result:
            continue
        start = max(0, part_match.start() - 1200)
        end = min(len(text), part_match.end() + 1200)
        window = text[start:end]
        recids = list(_RECID_RE.finditer(window))
        if not recids:
            continue
        position = part_match.start() - start
        nearest = min(recids, key=lambda item: abs(item.start() - position))
        _add_part(result, part, nearest.group("recid"), "proximity")
    return sorted(result.values(), key=lambda item: (int(item.recid), int(item.storepartuid)))


def load_configured_store_parts(
    shop_url: str = DEFAULT_SHOP_URL,
    sources_path: Path = DEFAULT_SOURCES_PATH,
) -> list[StorePart]:
    if not sources_path.exists():
        return []
    payload = json.loads(sources_path.read_text(encoding="utf-8"))
    result: dict[str, StorePart] = {}
    for shop in payload.get("shops", []):
        if str(shop.get("url", "")).rstrip("/") != shop_url.rstrip("/"):
            continue
        for item in shop.get("fallback_store_parts", []):
            _add_part(
                result,
                str(item.get("storepartuid", "")),
                str(item.get("recid", "")),
                "configured_fallback",
            )
    return list(result.values())


def discover_store_parts_with_report(
    url: str = DEFAULT_SHOP_URL,
    *,
    timeout: float = 30.0,
    sources_path: Path = DEFAULT_SOURCES_PATH,
) -> tuple[list[StorePart], DiscoveryReport]:
    configured = load_configured_store_parts(url, sources_path)
    html_text = ""
    html_parts: list[StorePart] = []
    error: str | None = None
    try:
        html_text = fetch_shop_html(url, timeout=timeout)
        html_parts = discover_store_parts_from_html(html_text)
    except Exception as exc:  # diagnostics must preserve fallback operation
        error = str(exc)

    merged: dict[str, StorePart] = {}
    for part in configured:
        _add_part(merged, part.storepartuid, part.recid, part.source)
    for part in html_parts:
        _add_part(merged, part.storepartuid, part.recid, part.source)

    parts = sorted(merged.values(), key=lambda item: (int(item.recid), int(item.storepartuid)))
    report = DiscoveryReport(
        shop_url=url,
        html_loaded=bool(html_text),
        html_size=len(html_text),
        html_candidates=len(html_parts),
        configured_candidates=len(configured),
        total_candidates=len(parts),
        error=error,
    )
    return parts, report


def discover_store_parts(url: str = DEFAULT_SHOP_URL) -> list[StorePart]:
    parts, _ = discover_store_parts_with_report(url)
    return parts


def print_discovery(parts: Iterable[StorePart]) -> None:
    parts = list(parts)
    print("=" * 72)
    print("AI BODHI TILDA STORE DISCOVERY")
    print("=" * 72)
    print(f"Store blocks found: {len(parts)}")
    for index, part in enumerate(parts, start=1):
        print(f"{index:>2}. recid={part.recid} storepartuid={part.storepartuid} source={part.source}")


if __name__ == "__main__":
    found, diagnostics = discover_store_parts_with_report()
    print_discovery(found)
    print(f"HTML loaded: {diagnostics.html_loaded}")
    print(f"HTML candidates: {diagnostics.html_candidates}")
    print(f"Configured candidates: {diagnostics.configured_candidates}")
    if diagnostics.error:
        print(f"HTML error: {diagnostics.error}")
