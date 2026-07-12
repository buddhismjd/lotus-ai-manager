from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Iterable, Iterator
from urllib.request import Request, urlopen


DEFAULT_SHOP_URL = "https://svet-lotosa.tilda.ws/svet-lotosa-shop"

# Known category labels visible in the shop interface. They are used only
# for diagnostics; discovery itself does not depend on these names.
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
    "getproductslist_url": 30,
    "inline_config": 20,
    "proximity": 10,
}


def fetch_shop_html(
    url: str = DEFAULT_SHOP_URL,
    timeout: float = 30.0,
) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "AI-Bodhi/1.0",
            "Accept": "text/html,application/xhtml+xml",
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
    """
    Register one Tilda store block using deterministic source precedence.

    ``storepartuid`` is the stable block identifier. A lower-confidence
    source cannot duplicate or replace a block already resolved from a more
    structured source.
    """
    if not storepartuid or not recid:
        return

    if not storepartuid.isdigit() or not recid.isdigit():
        return

    candidate = StorePart(
        storepartuid=storepartuid,
        recid=recid,
        source=source,
    )
    current = result.get(storepartuid)

    if current is None:
        result[storepartuid] = candidate
        return

    if _SOURCE_PRIORITY.get(source, 0) > _SOURCE_PRIORITY.get(
        current.source,
        0,
    ):
        result[storepartuid] = candidate


def _iter_balanced_object_blocks(text: str) -> Iterator[str]:
    """
    Yield balanced JavaScript/JSON object blocks.

    Pair extraction is bounded by object braces. This prevents a ``recid``
    from one object being associated with ``storepartuid`` from the next.
    """
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
            continue

        if character == "}" and stack:
            start = stack.pop()
            yield text[start:index + 1]


def _extract_single_pair(segment: str) -> tuple[str, str] | None:
    """
    Extract one unambiguous pair from a bounded segment.

    Segments containing multiple distinct values are rejected instead of
    guessed. Nested object blocks are processed independently.
    """
    parts = {match.group("part") for match in _PART_ONLY_RE.finditer(segment)}
    recids = {match.group("recid") for match in _RECID_RE.finditer(segment)}

    if len(parts) != 1 or len(recids) != 1:
        return None

    return next(iter(parts)), next(iter(recids))


def _iter_structured_pairs(text: str) -> Iterator[tuple[str, str]]:
    seen_pairs: set[tuple[str, str]] = set()

    for block in _iter_balanced_object_blocks(text):
        pair = _extract_single_pair(block)
        if pair is not None and pair not in seen_pairs:
            seen_pairs.add(pair)
            yield pair

    for tag_match in _HTML_TAG_RE.finditer(text):
        pair = _extract_single_pair(tag_match.group(0))
        if pair is not None and pair not in seen_pairs:
            seen_pairs.add(pair)
            yield pair


def discover_store_parts_from_html(raw_html: str) -> list[StorePart]:
    """
    Discover all Tilda store blocks from published page source.

    Extraction order:
    1. Tilda ``getproductslist`` request URLs.
    2. Bounded JavaScript/JSON objects and individual HTML tags.
    3. Proximity matching only for still-unresolved store blocks.
    """
    text = html.unescape(raw_html)
    result: dict[str, StorePart] = {}

    for match in _GET_PRODUCTS_URL_RE.finditer(text):
        url = match.group(0)
        _add_part(
            result,
            _query_value(url, "storepartuid"),
            _query_value(url, "recid"),
            "getproductslist_url",
        )

    for storepartuid, recid in _iter_structured_pairs(text):
        _add_part(
            result,
            storepartuid,
            recid,
            "inline_config",
        )

    # Last-resort fallback for markup where no bounded structured pair can
    # be recovered. Already resolved store blocks are deliberately skipped.
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

        absolute_part_position = part_match.start() - start
        nearest = min(
            recids,
            key=lambda item: abs(
                item.start() - absolute_part_position
            ),
        )
        _add_part(
            result,
            part,
            nearest.group("recid"),
            "proximity",
        )

    return sorted(
        result.values(),
        key=lambda item: (
            int(item.recid),
            int(item.storepartuid),
        ),
    )


def discover_store_parts(
    url: str = DEFAULT_SHOP_URL,
) -> list[StorePart]:
    return discover_store_parts_from_html(fetch_shop_html(url))


def print_discovery(parts: Iterable[StorePart]) -> None:
    parts = list(parts)

    print("=" * 72)
    print("AI BODHI TILDA STORE DISCOVERY")
    print("=" * 72)
    print(f"Store blocks found: {len(parts)}")

    for index, part in enumerate(parts, start=1):
        print(
            f"{index:>2}. recid={part.recid} "
            f"storepartuid={part.storepartuid} "
            f"source={part.source}"
        )


if __name__ == "__main__":
    print_discovery(discover_store_parts())
