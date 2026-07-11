from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from typing import Iterable
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
    r"getproductslist/\?[^\"'<>\\s]+",
    re.IGNORECASE,
)

_PAIR_PATTERNS = (
    re.compile(
        r"storepartuid[\"']?\s*[:=]\s*[\"']?(?P<part>\d+)"
        r".{0,800}?"
        r"recid[\"']?\s*[:=]\s*[\"']?(?P<recid>\d+)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"recid[\"']?\s*[:=]\s*[\"']?(?P<recid>\d+)"
        r".{0,800}?"
        r"storepartuid[\"']?\s*[:=]\s*[\"']?(?P<part>\d+)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"data-storepartuid=[\"'](?P<part>\d+)[\"']"
        r".{0,800}?"
        r"(?:id=[\"']rec|data-record-type=[\"'])?"
        r"(?P<recid>\d{6,})",
        re.IGNORECASE | re.DOTALL,
    ),
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
    result: dict[tuple[str, str], StorePart],
    storepartuid: str | None,
    recid: str | None,
    source: str,
) -> None:
    if not storepartuid or not recid:
        return

    if not storepartuid.isdigit() or not recid.isdigit():
        return

    key = (storepartuid, recid)
    result.setdefault(
        key,
        StorePart(
            storepartuid=storepartuid,
            recid=recid,
            source=source,
        ),
    )


def discover_store_parts_from_html(raw_html: str) -> list[StorePart]:
    """
    Discover all Tilda store blocks from the published page source.

    Tilda may represent the same values in request URLs, inline JSON,
    escaped JavaScript or data attributes, so several extraction strategies
    are deliberately used.
    """
    text = html.unescape(raw_html)
    result: dict[tuple[str, str], StorePart] = {}

    for match in _GET_PRODUCTS_URL_RE.finditer(text):
        url = match.group(0)
        _add_part(
            result,
            _query_value(url, "storepartuid"),
            _query_value(url, "recid"),
            "getproductslist_url",
        )

    for pattern in _PAIR_PATTERNS:
        for match in pattern.finditer(text):
            _add_part(
                result,
                match.group("part"),
                match.group("recid"),
                "inline_config",
            )

    # Last-resort proximity matching: associate each storepartuid with the
    # nearest recid within the surrounding catalog block.
    for part_match in _PART_ONLY_RE.finditer(text):
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
            part_match.group("part"),
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
