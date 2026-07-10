from __future__ import annotations

import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from backend.config import DATA_DIR, KNOWLEDGE_FILE, SITE_URL
from backend.integrations.tilda_api import TildaAPIClient
from backend.parser.site_parser import (
    chunk_text,
    classify_page,
    clean_text,
    normalize_url,
)


load_dotenv()


def page_url(alias: str | None, page_id: str) -> str:
    alias = (alias or "").strip().strip("/")

    if alias:
        return normalize_url(urljoin(SITE_URL.rstrip("/") + "/", alias))

    return normalize_url(
        urljoin(SITE_URL.rstrip("/") + "/", f"page{page_id}.html")
    )


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "lxml")

    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    for tag in soup.select(
        '[aria-hidden="true"], [style*="display:none"], [style*="display: none"]'
    ):
        tag.decompose()

    return clean_text(soup.get_text("\n", strip=True))


def load_existing_products() -> tuple[list[dict], list[dict]]:
    if not KNOWLEDGE_FILE.exists():
        return [], []

    try:
        existing = json.loads(
            KNOWLEDGE_FILE.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return [], []

    allowed_types = {
        "product",
        "product_catalog",
        "shop_catalog",
    }

    pages = [
        page
        for page in existing.get("pages", [])
        if page.get("page_type") in allowed_types
    ]

    page_urls = {
        page.get("url")
        for page in pages
        if page.get("url")
    }

    chunks = [
        chunk
        for chunk in existing.get("chunks", [])
        if chunk.get("page_url") in page_urls
    ]

    return pages, chunks


def build_api_page(
    page_meta: dict,
    page_data: dict,
) -> tuple[dict | None, list[dict]]:
    page_id = str(
        page_meta.get("id")
        or page_data.get("id")
        or ""
    )

    alias = (
        page_meta.get("alias")
        or page_data.get("alias")
        or page_meta.get("filename")
        or page_data.get("filename")
        or ""
    )

    url = page_url(alias, page_id)

    title = str(
        page_data.get("title")
        or page_meta.get("title")
        or url
    ).strip()

    html = str(
        page_data.get("html")
        or page_data.get("htmlbody")
        or page_data.get("body")
        or ""
    )

    text = html_to_text(html)

    if len(text) <= 100:
        return None, []

    classification = classify_page(
        url=url,
        title=title,
        text=text,
    )

    if not classification.get("enabled", True):
        return None, []

    page_type = classification["page_type"]
    display_title = classification.get("display_title") or title
    page_chunks = chunk_text(text)

    page = {
        "url": url,
        "title": display_title,
        "original_title": title,
        "text": text,
        "chars": len(text),
        "page_type": page_type,
        "enabled": True,
        "priority": int(
            classification.get("priority", 0)
        ),
        "classification_source": (
            classification.get(
                "classification_source",
                "automatic",
            )
        ),
        "chunks_count": len(page_chunks),
        "tilda_page_id": page_id,
        "source": "tilda_api",
    }

    chunks = [
        {
            "id": "",
            "page_url": url,
            "page_title": display_title,
            "page_type": page_type,
            "chunk_index": index,
            "text": chunk,
        }
        for index, chunk in enumerate(page_chunks)
    ]

    return page, chunks


def sync_tilda_project() -> dict:
    project_id = os.getenv("TILDA_PROJECT_ID", "").strip()

    if not project_id:
        raise RuntimeError(
            "В .env не задан TILDA_PROJECT_ID"
        )

    client = TildaAPIClient()
    page_list = client.get_pages(project_id)

    pages: list[dict] = []
    chunks: list[dict] = []
    errors: list[dict] = []

    existing_product_pages, existing_product_chunks = (
        load_existing_products()
    )

    for page_meta in page_list:
        page_id = str(page_meta.get("id", ""))

        if not page_id:
            continue

        try:
            page_data = client.get_page(page_id)
            page, page_chunks = build_api_page(
                page_meta,
                page_data,
            )

            if page is None:
                continue

            pages.append(page)
            chunks.extend(page_chunks)
        except Exception as exc:
            errors.append(
                {
                    "page_id": page_id,
                    "title": page_meta.get("title"),
                    "error": str(exc),
                }
            )

    existing_urls = {
        page.get("url")
        for page in pages
        if page.get("url")
    }

    for product_page in existing_product_pages:
        if product_page.get("url") not in existing_urls:
            product_page = dict(product_page)
            product_page["source"] = "catalog_crawler"
            pages.append(product_page)

    chunk_urls = {
        chunk.get("page_url")
        for chunk in chunks
    }

    for product_chunk in existing_product_chunks:
        if product_chunk.get("page_url") not in chunk_urls:
            chunks.append(dict(product_chunk))

    for index, chunk in enumerate(chunks, start=1):
        chunk["id"] = str(index)

    type_counts: dict[str, int] = {}

    for page in pages:
        page_type = page.get("page_type", "general")
        type_counts[page_type] = (
            type_counts.get(page_type, 0) + 1
        )

    knowledge = {
        "site": SITE_URL,
        "project_id": project_id,
        "source": "tilda_api_hybrid",
        "updated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "pages_count": len(pages),
        "chunks_count": len(chunks),
        "type_counts": type_counts,
        "errors_count": len(errors),
        "pages": pages,
        "chunks": chunks,
        "errors": errors,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)

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
    print("Tilda API sync completed")
    print("=" * 70)
    print(f"Project ID: {result.get('project_id')}")
    print(f"Pages:      {result.get('pages_count', 0)}")
    print(f"Chunks:     {result.get('chunks_count', 0)}")
    print(f"Errors:     {result.get('errors_count', 0)}")
    print()

    print("Types:")

    for page_type, count in sorted(
        result.get("type_counts", {}).items()
    ):
        print(f"  {page_type:20} {count}")

    errors = result.get("errors", [])

    if errors:
        print()
        print("Errors:")

        for error in errors:
            print(
                f"  Page {error.get('page_id')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    print_summary(sync_tilda_project())
