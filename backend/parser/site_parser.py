from __future__ import annotations

import json
import re
from collections import deque
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from backend.config import BASE_DIR


HEADERS = {"User-Agent": "LotusAIManager/0.8"}
PAGE_TYPES_FILE = BASE_DIR / "backend" / "config" / "page_types.json"

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".zip", ".rar", ".css", ".js", ".xml", ".mp4", ".webm",
)

BAD_TEXT_PARTS = (
    "li_ph", "li_req", "li_nm", "recaptcha", "window.",
    "function(", "document.", "jquery", "prototype",
)

TPRODUCT_PATTERN = re.compile(
    r"""(?:
        https?://[^\s"'<>]+/tproduct/[^\s"'<>\\]+
        |
        /[^\s"'<>]*/tproduct/[^\s"'<>\\]+
    )""",
    re.IGNORECASE | re.VERBOSE,
)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    cleaned = parsed._replace(query="", fragment="")
    value = urlunparse(cleaned).rstrip("/")
    return value or f"{parsed.scheme}://{parsed.netloc}"


def is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc == urlparse(base_url).netloc


def is_crawlable(url: str, base_url: str) -> bool:
    if not is_same_domain(url, base_url):
        return False

    path = urlparse(url).path.lower()
    return not path.endswith(SKIP_EXTENSIONS)


def load_manual_page_types() -> dict:
    if not PAGE_TYPES_FILE.exists():
        return {}

    try:
        data = json.loads(PAGE_TYPES_FILE.read_text(encoding="utf-8"))
        return {
            normalize_url(url): settings
            for url, settings in data.items()
        }
    except (json.JSONDecodeError, OSError):
        return {}


def manual_seed_urls(base_url: str) -> list[str]:
    return [
        url
        for url in load_manual_page_types()
        if is_crawlable(url, base_url)
    ]


def clean_text(text: str) -> str:
    lines: list[str] = []
    seen: set[str] = set()

    for raw in text.splitlines():
        line = re.sub(r"\s{2,}", " ", raw.strip())

        if len(line) < 3:
            continue
        if any(bad in line.lower() for bad in BAD_TEXT_PARTS):
            continue
        if line.count("{") + line.count("}") + line.count("[") + line.count("]") > 2:
            continue
        if re.search(r"\\u[0-9a-fA-F]{4}", line):
            continue

        key = line.lower()
        if key in seen and len(line) < 100:
            continue

        seen.add(key)
        lines.append(line)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def classify_page(url: str, title: str, text: str) -> dict:
    normalized_url = normalize_url(url)
    manual = load_manual_page_types().get(normalized_url)

    if manual:
        return {
            "page_type": manual.get("type", "general"),
            "display_title": manual.get("title") or title,
            "enabled": bool(manual.get("enabled", True)),
            "priority": int(manual.get("priority", 0)),
            "classification_source": "manual",
        }

    path = urlparse(normalized_url).path.lower().rstrip("/")
    hay = f"{title}\n{text}".lower()

    if "/tproduct/" in path:
        page_type = "product"
    elif path == "/svet-lotosa-shop":
        page_type = "shop_catalog"
    elif path == "/buddolog-consult":
        page_type = "psychologist"
    elif path == "/reviews":
        page_type = "reviews"
    elif path == "/privacy":
        page_type = "legal"
    elif path == "/putretrit":
        page_type = "tour_catalog"
    elif path in ("", "/"):
        page_type = "general"
    else:
        tour_signals = (
            "план маршрута",
            "день 1",
            "забронировать тур",
            "бронирование тура",
            "в стоимость входит",
        )
        tour_signal_count = sum(signal in hay for signal in tour_signals)

        url_tour_signal = any(
            marker in path
            for marker in (
                "-tur-", "tour-", "-tour", "kailas", "kailash",
                "lapchi", "tibet", "butan", "bhutan", "ladakh",
                "altai", "beluha", "markha", "kullu",
            )
        )

        if tour_signal_count >= 2 or (
            url_tour_signal and tour_signal_count >= 1
        ):
            page_type = "tour"
        else:
            page_type = "general"

    return {
        "page_type": page_type,
        "display_title": title,
        "enabled": True,
        "priority": 0,
        "classification_source": "automatic",
    }


def fetch_response(url: str) -> requests.Response:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response


def extract_page(url: str) -> dict:
    response = fetch_response(url)
    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    for tag in soup.select(
        '[aria-hidden="true"], [style*="display:none"], [style*="display: none"]'
    ):
        tag.decompose()

    original_title = soup.title.get_text(strip=True) if soup.title else url
    text = clean_text(soup.get_text("\n", strip=True))
    classification = classify_page(url, original_title, text)

    return {
        "url": normalize_url(url),
        "title": classification["display_title"],
        "original_title": original_title,
        "text": text,
        "chars": len(text),
        "page_type": classification["page_type"],
        "enabled": classification["enabled"],
        "priority": classification["priority"],
        "classification_source": classification["classification_source"],
    }


def extract_tproduct_links(
    html: str,
    current_url: str,
    base_url: str,
) -> set[str]:
    links: set[str] = set()

    for match in TPRODUCT_PATTERN.findall(html):
        candidate = match.replace("\\/", "/").rstrip("\\,;)")
        full_url = normalize_url(urljoin(current_url + "/", candidate))

        if is_crawlable(full_url, base_url):
            links.add(full_url)

    return links


def extract_links(url: str, base_url: str) -> list[str]:
    response = fetch_response(url)
    soup = BeautifulSoup(response.text, "lxml")
    links: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()

        if not href or href.startswith(
            ("mailto:", "tel:", "javascript:", "whatsapp:", "tg:", "#")
        ):
            continue

        full_url = normalize_url(urljoin(url + "/", href))

        if is_crawlable(full_url, base_url):
            links.add(full_url)

    links.update(
        extract_tproduct_links(
            response.text,
            current_url=url,
            base_url=base_url,
        )
    )

    return sorted(links)


def discover_links(
    base_url: str,
    limit: int = 300,
    max_depth: int = 3,
) -> list[str]:
    base_url = normalize_url(base_url)

    queue = deque([(base_url, 0)])

    # Принудительно добавляем известные страницы из page_types.json.
    for seed_url in manual_seed_urls(base_url):
        if seed_url != base_url:
            queue.append((seed_url, 0))

    visited: set[str] = set()
    discovered: list[str] = []

    while queue and len(discovered) < limit:
        current_url, depth = queue.popleft()

        if current_url in visited:
            continue

        visited.add(current_url)
        discovered.append(current_url)

        if depth >= max_depth:
            continue

        try:
            child_links = extract_links(current_url, base_url)
        except requests.RequestException:
            continue

        for child_url in child_links:
            if child_url not in visited:
                queue.append((child_url, depth + 1))

    return discovered


def chunk_text(
    text: str,
    chunk_size: int = 1100,
    overlap: int = 150,
) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}".strip()

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if len(current) > 100:
            chunks.append(current)

        current = paragraph

    if len(current) > 100:
        chunks.append(current)

    final_chunks: list[str] = []

    for chunk in chunks:
        if len(chunk) <= chunk_size + 200:
            final_chunks.append(chunk)
            continue

        start = 0

        while start < len(chunk):
            part = chunk[start:start + chunk_size].strip()

            if len(part) > 100:
                final_chunks.append(part)

            start += chunk_size - overlap

    return final_chunks


def parse_site(
    base_url: str,
    limit: int = 300,
    max_depth: int = 3,
) -> dict:
    pages: list[dict] = []
    chunks: list[dict] = []
    errors: list[dict] = []

    for url in discover_links(base_url, limit=limit, max_depth=max_depth):
        try:
            page = extract_page(url)

            if page["chars"] <= 100 or not page["enabled"]:
                continue

            page_chunks = chunk_text(page["text"])
            page["chunks_count"] = len(page_chunks)
            pages.append(page)

            for index, chunk in enumerate(page_chunks):
                chunks.append(
                    {
                        "id": str(len(chunks) + 1),
                        "page_url": page["url"],
                        "page_title": page["title"],
                        "page_type": page["page_type"],
                        "chunk_index": index,
                        "text": chunk,
                    }
                )
        except Exception as exc:
            errors.append({"url": url, "error": str(exc)})

    type_counts: dict[str, int] = {}

    for page in pages:
        page_type = page["page_type"]
        type_counts[page_type] = type_counts.get(page_type, 0) + 1

    return {
        "site": base_url,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "pages_count": len(pages),
        "chunks_count": len(chunks),
        "type_counts": type_counts,
        "errors_count": len(errors),
        "pages": pages,
        "chunks": chunks,
        "errors": errors,
    }
