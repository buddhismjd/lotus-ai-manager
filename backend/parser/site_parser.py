from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from backend.config import BASE_DIR


HEADERS = {"User-Agent": "LotusAIManager/1.0"}
PAGE_TYPES_FILE = BASE_DIR / "backend" / "config" / "page_types.json"

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".zip", ".rar", ".css", ".js", ".xml", ".mp4", ".webm",
    ".woff", ".woff2", ".ttf",
)

BAD_TEXT_PARTS = (
    "li_ph", "li_req", "li_nm", "recaptcha", "window.",
    "function(", "document.", "jquery", "prototype",
)

KNOWN_TOUR_URLS = {
    "https://svet-lotosa.tilda.ws/india-tur-dolina-kullu-2-11-maya":
        "По стопам Рериха — Долина Куллу",
    "https://svet-lotosa.tilda.ws/altay-pohod-k-beluhe-18-28-iyunya":
        "Поход к подножию горы Белуха",
    "https://svet-lotosa.tilda.ws/tur-v-ladakh-zanskar-15-25-july":
        "Ладакх, королевство Занскар",
    "https://svet-lotosa.tilda.ws/altay-mongolia-28-july-4-august":
        "Алтай — Монголия",
    "https://svet-lotosa.tilda.ws/tropoy-inya-13-20-august":
        "Тропой Иня",
    "https://svet-lotosa.tilda.ws/trek-markha-kang-yatse-3-14-september":
        "Долина Маркха и Канг Ятсе 2",
    "https://svet-lotosa.tilda.ws/18-dney-tur-tibet-kailas-22-sent-9-oct":
        "Тибет + Кайлас — 18 дней",
    "https://svet-lotosa.tilda.ws/butan-vajrayogini-1-7-november":
        "Бутан с Гуру Ринпоче и Ваджрайогини",
}

KNOWN_PRODUCT_CATALOG_URLS = {
    "https://svet-lotosa.tilda.ws/statui-svet-lotosa": "Статуи",
    "https://svet-lotosa.tilda.ws/podveski-svet-lotosa": "Подвески",
    "https://svet-lotosa.tilda.ws/sergi-svet-lotosa": "Серьги",
    "https://svet-lotosa.tilda.ws/chetki-svet-lotosa": "Чётки",
    "https://svet-lotosa.tilda.ws/gau-svet-lotosa": "Гау",
    "https://svet-lotosa.tilda.ws/blago-svet-lotosa": "Благовония",
}

KNOWN_CORE_URLS = {
    "https://svet-lotosa.tilda.ws/",
    "https://svet-lotosa.tilda.ws/putretrit",
    "https://svet-lotosa.tilda.ws/svet-lotosa-shop",
    "https://svet-lotosa.tilda.ws/buddolog-consult",
    "https://svet-lotosa.tilda.ws/reviews",
    "https://svet-lotosa.tilda.ws/privacy",
}

RAW_URL_PATTERN = re.compile(
    r"""(?:
        https?://[a-zA-Z0-9.-]+/[^\s"'<>\\)]+
        |
        /[a-zA-Z0-9_./-]+
    )""",
    re.IGNORECASE | re.VERBOSE,
)


def normalize_url(url: str) -> str:
    url = url.replace("\\/", "/").strip()
    parsed = urlparse(url)
    cleaned = parsed._replace(query="", fragment="")
    value = urlunparse(cleaned).rstrip("/")
    return value or f"{parsed.scheme}://{parsed.netloc}"


def is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc == urlparse(base_url).netloc


def is_crawlable(url: str, base_url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    if not is_same_domain(url, base_url):
        return False

    path = urlparse(url).path.lower()
    if path.endswith(SKIP_EXTENSIONS):
        return False
    if path.startswith(("/page", "/projects/", "/favicon")):
        return False

    return True


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


def all_seed_urls(base_url: str) -> set[str]:
    seeds = {normalize_url(base_url)}
    seeds.update(normalize_url(url) for url in KNOWN_CORE_URLS)
    seeds.update(normalize_url(url) for url in KNOWN_TOUR_URLS)
    seeds.update(normalize_url(url) for url in KNOWN_PRODUCT_CATALOG_URLS)
    seeds.update(load_manual_page_types().keys())
    return {
        url for url in seeds
        if is_crawlable(url, base_url)
    }


def fetch_response(url: str) -> requests.Response:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=35,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response


def discover_sitemap_urls(base_url: str) -> set[str]:
    urls: set[str] = set()
    candidates = (
        urljoin(base_url + "/", "sitemap.xml"),
        urljoin(base_url + "/", "sitemap-pages.xml"),
    )

    processed_sitemaps: set[str] = set()
    sitemap_queue = deque(candidates)

    while sitemap_queue:
        sitemap_url = sitemap_queue.popleft()

        if sitemap_url in processed_sitemaps:
            continue

        processed_sitemaps.add(sitemap_url)

        try:
            response = fetch_response(sitemap_url)
            root = ET.fromstring(response.text)
        except Exception:
            continue

        for element in root.iter():
            if not element.tag.endswith("loc") or not element.text:
                continue

            discovered = normalize_url(element.text.strip())

            if discovered.endswith(".xml"):
                sitemap_queue.append(discovered)
            elif is_crawlable(discovered, base_url):
                urls.add(discovered)

    return urls


def extract_raw_links(
    html: str,
    current_url: str,
    base_url: str,
) -> set[str]:
    links: set[str] = set()
    cleaned_html = html.replace("\\/", "/")

    for match in RAW_URL_PATTERN.findall(cleaned_html):
        candidate = match.rstrip(".,;:)]}")
        full_url = normalize_url(urljoin(current_url + "/", candidate))

        if is_crawlable(full_url, base_url):
            links.add(full_url)

    return links


def extract_links(url: str, base_url: str) -> list[str]:
    response = fetch_response(url)
    soup = BeautifulSoup(response.text, "lxml")
    links: set[str] = set()

    for tag in soup.find_all(True):
        for attribute in (
            "href",
            "data-href",
            "data-url",
            "data-product-url",
            "data-product-lid",
        ):
            value = tag.get(attribute)

            if not value or not isinstance(value, str):
                continue

            value = value.strip()

            if value.startswith(
                ("mailto:", "tel:", "javascript:", "whatsapp:", "tg:", "#")
            ):
                continue

            full_url = normalize_url(urljoin(url + "/", value))

            if is_crawlable(full_url, base_url):
                links.add(full_url)

    links.update(
        extract_raw_links(
            response.text,
            current_url=url,
            base_url=base_url,
        )
    )

    return sorted(links)


def discover_links(
    base_url: str,
    limit: int = 1000,
    max_depth: int = 5,
) -> list[str]:
    base_url = normalize_url(base_url)

    seeds = all_seed_urls(base_url)
    seeds.update(discover_sitemap_urls(base_url))

    queue = deque((url, 0) for url in sorted(seeds))
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
    haystack = f"{title}\n{text}".lower()

    if normalized_url in {
        normalize_url(url) for url in KNOWN_TOUR_URLS
    }:
        page_type = "tour"
        display_title = KNOWN_TOUR_URLS.get(
            next(
                original
                for original in KNOWN_TOUR_URLS
                if normalize_url(original) == normalized_url
            ),
            title,
        )
    elif normalized_url in {
        normalize_url(url) for url in KNOWN_PRODUCT_CATALOG_URLS
    }:
        page_type = "product_catalog"
        display_title = KNOWN_PRODUCT_CATALOG_URLS.get(
            next(
                original
                for original in KNOWN_PRODUCT_CATALOG_URLS
                if normalize_url(original) == normalized_url
            ),
            title,
        )
    elif "/tproduct/" in path:
        page_type = "product"
        display_title = title
    elif path == "/putretrit":
        page_type = "tour_catalog"
        display_title = "Каталог путешествий"
    elif path == "/svet-lotosa-shop":
        page_type = "shop_catalog"
        display_title = "Магазин Свет Лотоса"
    elif path == "/buddolog-consult":
        page_type = "psychologist"
        display_title = "Консультация психолога-буддолога"
    elif path == "/reviews":
        page_type = "reviews"
        display_title = "Отзывы"
    elif path == "/privacy":
        page_type = "legal"
        display_title = "Политика обработки персональных данных"
    elif path in ("", "/"):
        page_type = "general"
        display_title = "Главная страница"
    else:
        tour_signals = (
            "план маршрута",
            "день 1",
            "отправить заявку",
            "в стоимость входит",
            "продолжительность тура",
        )
        product_signals = (
            "купить",
            "доставка по россии",
            "заказать",
            "каталог товаров",
        )

        if sum(signal in haystack for signal in tour_signals) >= 2:
            page_type = "tour"
        elif sum(signal in haystack for signal in product_signals) >= 2:
            page_type = "product_catalog"
        else:
            page_type = "general"

        display_title = title

    priorities = {
        "tour": 120,
        "product": 110,
        "psychologist": 100,
        "tour_catalog": 80,
        "shop_catalog": 80,
        "product_catalog": 70,
        "reviews": 50,
        "contacts": 40,
        "legal": 0,
        "general": 10,
    }

    return {
        "page_type": page_type,
        "display_title": display_title,
        "enabled": True,
        "priority": priorities.get(page_type, 0),
        "classification_source": "automatic",
    }


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


def chunk_text(
    text: str,
    chunk_size: int = 1100,
    overlap: int = 150,
) -> list[str]:
    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]

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
    limit: int = 1000,
    max_depth: int = 5,
) -> dict:
    pages: list[dict] = []
    chunks: list[dict] = []
    errors: list[dict] = []

    discovered_urls = discover_links(
        base_url,
        limit=limit,
        max_depth=max_depth,
    )

    for url in discovered_urls:
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
            errors.append(
                {
                    "url": url,
                    "error": str(exc),
                }
            )

    type_counts: dict[str, int] = {}

    for page in pages:
        page_type = page["page_type"]
        type_counts[page_type] = type_counts.get(page_type, 0) + 1

    return {
        "site": base_url,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "discovered_urls_count": len(discovered_urls),
        "pages_count": len(pages),
        "chunks_count": len(chunks),
        "type_counts": type_counts,
        "errors_count": len(errors),
        "pages": pages,
        "chunks": chunks,
        "errors": errors,
    }
