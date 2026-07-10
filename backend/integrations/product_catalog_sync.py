from __future__ import annotations

import json
import re
from collections import deque
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from backend.config import KNOWLEDGE_FILE, SITE_URL
from backend.parser.site_parser import chunk_text, extract_page


HEADERS = {"User-Agent": "LotusAIManager-ProductCatalog/1.0"}

SHOP_SEEDS = {
    "https://svet-lotosa.tilda.ws/svet-lotosa-shop",
    "https://svet-lotosa.tilda.ws/statui-svet-lotosa",
    "https://svet-lotosa.tilda.ws/podveski-svet-lotosa",
    "https://svet-lotosa.tilda.ws/sergi-svet-lotosa",
    "https://svet-lotosa.tilda.ws/chetki-svet-lotosa",
    "https://svet-lotosa.tilda.ws/gau-svet-lotosa",
    "https://svet-lotosa.tilda.ws/blago-svet-lotosa",
}

PRODUCT_PATTERN = re.compile(
    r"""(?:
        https?://[a-zA-Z0-9.-]+/[^\s"'<>\\]*tproduct/[^\s"'<>\\]+
        |
        /[^\s"'<>\\]*tproduct/[^\s"'<>\\]+
    )""",
    re.IGNORECASE | re.VERBOSE,
)

PRODUCT_ID_PATTERN = re.compile(
    r"/tproduct/(?P<product_id>\d+)(?:-[^/?#]+)?",
    re.IGNORECASE,
)


def normalize_url(url: str) -> str:
    value = url.replace("\\/", "/").strip()
    parsed = urlparse(value)
    parsed = parsed._replace(query="", fragment="")
    return urlunparse(parsed).rstrip("/")


def canonical_product_url(url: str) -> str | None:
    """
    Keeps only the canonical product path and removes repeated suffixes.

    Examples:
      /tproduct/296122659532-vadzhra
      /svet-lotosa-shop/tproduct/260561911092-statuya-ushnishavidzhai
    """
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    path = parsed.path

    marker = "/tproduct/"
    marker_index = path.lower().find(marker)

    if marker_index < 0:
        return None

    prefix = path[:marker_index]
    remainder = path[marker_index + len(marker):].strip("/")

    if not remainder:
        return None

    product_slug = remainder.split("/")[0]
    match = re.match(r"^\d+(?:-[a-zA-Z0-9а-яА-ЯёЁ_-]+)?$", product_slug)

    if not match:
        return None

    canonical_path = f"{prefix}{marker}{product_slug}"
    result = parsed._replace(path=canonical_path, query="", fragment="")
    return urlunparse(result).rstrip("/")


def product_id_from_url(url: str) -> str | None:
    match = PRODUCT_ID_PATTERN.search(urlparse(url).path)
    return match.group("product_id") if match else None


def fetch(url: str) -> requests.Response:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=35,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response


def discover_category_urls() -> set[str]:
    categories = {normalize_url(url) for url in SHOP_SEEDS}

    try:
        response = fetch("https://svet-lotosa.tilda.ws/svet-lotosa-shop")
        soup = BeautifulSoup(response.text, "lxml")

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            full_url = normalize_url(
                urljoin(
                    "https://svet-lotosa.tilda.ws/",
                    href,
                )
            )

            if (
                urlparse(full_url).netloc == "svet-lotosa.tilda.ws"
                and full_url.endswith("-svet-lotosa")
            ):
                categories.add(full_url)
    except requests.RequestException:
        pass

    return categories


def extract_product_urls(html: str, source_url: str) -> set[str]:
    discovered: set[str] = set()
    cleaned = html.replace("\\/", "/")

    for match in PRODUCT_PATTERN.findall(cleaned):
        candidate = match.rstrip(".,;:)]}\"'")
        full_url = urljoin(source_url + "/", candidate)
        canonical = canonical_product_url(full_url)

        if canonical:
            discovered.add(canonical)

    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(True):
        for attribute in (
            "href",
            "data-href",
            "data-url",
            "data-product-url",
            "data-product-link",
        ):
            value = tag.get(attribute)

            if not isinstance(value, str) or "tproduct/" not in value:
                continue

            canonical = canonical_product_url(
                urljoin(source_url + "/", value)
            )

            if canonical:
                discovered.add(canonical)

    return discovered


def select_best_url(urls: set[str]) -> str:
    """
    If one product ID is available at several paths, prefer the shortest
    working canonical URL.
    """
    candidates = sorted(urls, key=lambda item: (len(item), item))

    for candidate in candidates:
        try:
            response = requests.get(
                candidate,
                headers=HEADERS,
                timeout=20,
                allow_redirects=True,
            )

            if response.status_code == 200:
                return canonical_product_url(response.url) or candidate
        except requests.RequestException:
            continue

    return candidates[0]


def discover_all_product_urls() -> tuple[list[str], list[dict]]:
    by_product_id: dict[str, set[str]] = {}
    errors: list[dict] = []

    for category_url in sorted(discover_category_urls()):
        try:
            response = fetch(category_url)
            product_urls = extract_product_urls(
                response.text,
                source_url=category_url,
            )

            for product_url in product_urls:
                product_id = product_id_from_url(product_url)

                if not product_id:
                    continue

                by_product_id.setdefault(product_id, set()).add(product_url)
        except Exception as exc:
            errors.append(
                {
                    "url": category_url,
                    "stage": "category_discovery",
                    "error": str(exc),
                }
            )

    selected = [
        select_best_url(urls)
        for _, urls in sorted(by_product_id.items())
    ]

    return selected, errors


def load_knowledge() -> dict:
    if not KNOWLEDGE_FILE.exists():
        return {
            "site": SITE_URL,
            "pages": [],
            "chunks": [],
            "errors": [],
        }

    return json.loads(
        KNOWLEDGE_FILE.read_text(encoding="utf-8")
    )


def remove_old_products(knowledge: dict) -> None:
    product_urls = {
        page.get("url")
        for page in knowledge.get("pages", [])
        if page.get("page_type") == "product"
    }

    knowledge["pages"] = [
        page
        for page in knowledge.get("pages", [])
        if page.get("page_type") != "product"
    ]

    knowledge["chunks"] = [
        chunk
        for chunk in knowledge.get("chunks", [])
        if chunk.get("page_url") not in product_urls
    ]


def sync_all_products() -> dict:
    knowledge = load_knowledge()
    remove_old_products(knowledge)

    product_urls, discovery_errors = discover_all_product_urls()
    errors = [
        error
        for error in knowledge.get("errors", [])
        if error.get("source") != "product_catalog"
    ]
    errors.extend(discovery_errors)

    pages = knowledge.setdefault("pages", [])
    chunks = knowledge.setdefault("chunks", [])
    synced = 0

    for product_url in product_urls:
        try:
            page = extract_page(product_url)
            page["page_type"] = "product"
            page["priority"] = 120
            page["enabled"] = True
            page["classification_source"] = "automatic_product_catalog"
            page["source"] = "product_catalog"

            page_chunks = chunk_text(page.get("text", ""))
            page["chunks_count"] = len(page_chunks)
            pages.append(page)

            for chunk_index, text in enumerate(page_chunks):
                chunks.append(
                    {
                        "id": "",
                        "page_url": page["url"],
                        "page_title": page["title"],
                        "page_type": "product",
                        "chunk_index": chunk_index,
                        "text": text,
                    }
                )

            synced += 1
        except Exception as exc:
            errors.append(
                {
                    "url": product_url,
                    "source": "product_catalog",
                    "stage": "product_fetch",
                    "error": str(exc),
                }
            )

    for index, chunk in enumerate(chunks, start=1):
        chunk["id"] = str(index)

    type_counts: dict[str, int] = {}

    for page in pages:
        page_type = page.get("page_type", "general")
        type_counts[page_type] = type_counts.get(page_type, 0) + 1

    knowledge.update(
        {
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "pages_count": len(pages),
            "chunks_count": len(chunks),
            "errors_count": len(errors),
            "type_counts": type_counts,
            "errors": errors,
            "products_discovered": len(product_urls),
            "products_synced": synced,
        }
    )

    KNOWLEDGE_FILE.write_text(
        json.dumps(
            knowledge,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return knowledge


def print_summary(result: dict) -> None:
    print("Full product catalog sync completed")
    print("=" * 70)
    print(f"Products discovered: {result.get('products_discovered', 0)}")
    print(f"Products synced:     {result.get('products_synced', 0)}")
    print(f"Total pages:         {result.get('pages_count', 0)}")
    print(f"Total chunks:        {result.get('chunks_count', 0)}")
    print(f"Errors:              {result.get('errors_count', 0)}")


if __name__ == "__main__":
    print_summary(sync_all_products())
