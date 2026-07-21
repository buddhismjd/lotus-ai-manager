from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

DEFAULT_SOURCES_PATH = Path("backend/config/product_catalog_sources.json")
_PRODUCT_UID_PATTERNS = (
    re.compile(r"/tproduct/(?P<uid>\d+)(?:[-/?\"'])", re.I),
    re.compile(r"data-product-(?:uid|id)=[\"'](?P<uid>\d+)[\"']", re.I),
    re.compile(r"(?:productuid|productid)[\"']?\s*[:=]\s*[\"']?(?P<uid>\d+)", re.I),
)

@dataclass(frozen=True, slots=True)
class CatalogSource:
    name: str
    url: str
    category: str | None
    required: bool
    fallback_store_parts: tuple[dict[str, str], ...] = ()

@dataclass(frozen=True, slots=True)
class CatalogSourceReport:
    name: str
    url: str
    category: str | None
    required: bool
    html_loaded: bool
    html_size: int
    product_references: int
    store_blocks: int
    error: str | None = None


def load_catalog_sources(path: Path = DEFAULT_SOURCES_PATH) -> list[CatalogSource]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        CatalogSource(
            name=str(item["name"]),
            url=str(item["url"]),
            category=item.get("category"),
            required=bool(item.get("required", True)),
            fallback_store_parts=tuple(item.get("fallback_store_parts", ())),
        )
        for item in payload.get("sources", [])
    ]


def fetch_source_html(url: str, timeout: float = 30.0) -> str:
    request = Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; AI-Bodhi/1.0)","Accept":"text/html"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_product_uids(raw_html: str) -> set[str]:
    result: set[str] = set()
    for pattern in _PRODUCT_UID_PATTERNS:
        result.update(match.group("uid") for match in pattern.finditer(raw_html))
    return result
