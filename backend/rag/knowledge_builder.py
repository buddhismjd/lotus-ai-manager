from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from backend.config import BASE_DIR
from backend.services.knowledge_service import load_knowledge
from backend.storage.database import (
    clear_knowledge_documents,
    get_database_stats,
    initialize_database,
    save_document,
)


KNOWLEDGE_DIR = BASE_DIR / "knowledge"

TYPE_DIRECTORIES = {
    "tour": KNOWLEDGE_DIR / "tours",
    "tour_catalog": KNOWLEDGE_DIR / "tour_catalogs",
    "psychologist": KNOWLEDGE_DIR / "psychologist",
    "product": KNOWLEDGE_DIR / "products",
    "shop_catalog": KNOWLEDGE_DIR / "shop_catalogs",
    "reviews": KNOWLEDGE_DIR / "reviews",
    "contacts": KNOWLEDGE_DIR / "contacts",
    "legal": KNOWLEDGE_DIR / "legal",
    "general": KNOWLEDGE_DIR / "general",
}


def slugify(value: str) -> str:
    value = value.lower().strip()

    transliteration = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
        "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
        "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
        "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
        "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch",
        "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
        "э": "e", "ю": "yu", "я": "ya",
    }

    value = "".join(transliteration.get(char, char) for char in value)
    value = re.sub(r"[^a-z0-9]+", "-", value)

    return value.strip("-") or "page"


def page_id_from_url(url: str, title: str) -> str:
    path = urlparse(url).path.strip("/")

    if path:
        return slugify(path.replace("/", "-"))

    return slugify(title)


def prepare_directories() -> None:
    for directory in TYPE_DIRECTORIES.values():
        directory.mkdir(parents=True, exist_ok=True)


def clear_generated_files() -> None:
    for directory in TYPE_DIRECTORIES.values():
        if not directory.exists():
            continue

        for file_path in directory.glob("*.json"):
            file_path.unlink()


def page_chunks(page_url: str, chunks: list[dict]) -> list[str]:
    return [
        chunk.get("text", "").strip()
        for chunk in chunks
        if chunk.get("page_url") == page_url
        and chunk.get("text", "").strip()
    ]


def build_page_document(page: dict, chunks: list[dict]) -> dict:
    page_type = page.get("page_type", "general")
    title = page.get("title") or page.get("url") or "Без названия"
    url = page.get("url", "")
    content = page.get("text", "").strip()
    hash_payload = json.dumps(
        {
            "title": title,
            "url": url,
            "type": page_type,
            "enabled": bool(page.get("enabled", True)),
            "priority": int(page.get("priority", 0)),
            "content": content,
            "chunks": page_chunks(url, chunks),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    content_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

    return {
        "id": page_id_from_url(url, title),
        "source_type": "tilda",
        "type": page_type,
        "title": title,
        "url": url,
        "enabled": bool(page.get("enabled", True)),
        "priority": int(page.get("priority", 0)),
        "summary": content[:500],
        "content": content,
        "content_hash": content_hash,
        "chunks": page_chunks(url, chunks),
        "metadata": {
            "chars": page.get("chars", 0),
            "chunks_count": page.get("chunks_count", 0),
            "classification_source": page.get(
                "classification_source",
                "automatic",
            ),
        },
    }


def save_page_document(document: dict) -> Path:
    page_type = document.get("type", "general")
    output_directory = TYPE_DIRECTORIES.get(
        page_type,
        TYPE_DIRECTORIES["general"],
    )
    output_path = output_directory / f"{document['id']}.json"

    output_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_path


def build_knowledge_files(clear_existing: bool = True) -> dict:
    prepare_directories()
    initialize_database()

    if clear_existing:
        clear_generated_files()
        clear_knowledge_documents()

    source = load_knowledge()
    pages = source.get("pages", [])
    chunks = source.get("chunks", [])

    created_files: list[str] = []
    counters: dict[str, int] = {}

    for page in pages:
        document = build_page_document(page, chunks)
        output_path = save_page_document(document)
        save_document(document)

        created_files.append(str(output_path))

        page_type = document["type"]
        counters[page_type] = counters.get(page_type, 0) + 1

    return {
        "created_count": len(created_files),
        "types": counters,
        "files": created_files,
        "database": get_database_stats(),
    }


if __name__ == "__main__":
    result = build_knowledge_files()

    print("Knowledge Builder completed")
    print(f"Created files: {result['created_count']}")

    for page_type, count in sorted(result["types"].items()):
        print(f"{page_type}: {count}")

    print("Database:")

    for key, value in result["database"].items():
        print(f"  {key}: {value}")


def synchronize_knowledge_documents(source: dict | None = None) -> dict:
    """Incrementally align generated JSON files and SQLite documents with a mirror."""
    from backend.storage.database import get_connection

    prepare_directories()
    initialize_database()
    source = source or load_knowledge()
    pages = list(source.get("pages", []))
    chunks = list(source.get("chunks", []))

    documents = [build_page_document(page, chunks) for page in pages]
    incoming_ids = {document["id"] for document in documents}
    with get_connection() as connection:
        rows = connection.execute("SELECT id, content_hash FROM documents").fetchall()
    existing_hashes = {row["id"]: row["content_hash"] for row in rows}

    created = 0
    updated = 0
    unchanged = 0
    for document in documents:
        previous_hash = existing_hashes.get(document["id"])
        if previous_hash == document["content_hash"]:
            unchanged += 1
            continue
        save_page_document(document)
        save_document(document)
        if previous_hash is None:
            created += 1
        else:
            updated += 1

    removed_ids = set(existing_hashes) - incoming_ids
    if removed_ids:
        with get_connection() as connection:
            connection.executemany(
                "DELETE FROM documents WHERE id = ?",
                [(document_id,) for document_id in sorted(removed_ids)],
            )
        for directory in TYPE_DIRECTORIES.values():
            for file_path in directory.glob("*.json"):
                try:
                    payload = json.loads(file_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if payload.get("id") in removed_ids:
                    file_path.unlink(missing_ok=True)

    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "removed": len(removed_ids),
        "database": get_database_stats(),
    }
