from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from backend.integrations.product_page_snapshot import fetch_product_page

_SPACE_RE = re.compile(r"\s+")
_MEASUREMENT_RE = re.compile(
    r"(?P<label>высота|ширина|глубина|диаметр|размер|вес)\s*[:\-]?\s*"
    r"(?P<value>\d+(?:[.,]\d+)?(?:\s*[xх×]\s*\d+(?:[.,]\d+)?)*)\s*"
    r"(?P<unit>мм|см|м|г|кг)?",
    re.IGNORECASE,
)
_MATERIAL_RE = re.compile(
    r"(?:материал|изготовлен(?:а|о|ы)?\s+из)\s*[:\-]?\s*(?P<value>[^.;\n]{2,100})",
    re.IGNORECASE,
)
_STATUS_PATTERNS = (
    (re.compile(r"\bнет\s+в\s+наличии\b", re.IGNORECASE), "Нет в наличии"),
    (re.compile(r"\bпод\s+заказ\b|\bна\s+заказ\b", re.IGNORECASE), "Под заказ"),
    (re.compile(r"\bв\s+наличии\b", re.IGNORECASE), "В наличии"),
)
_TILDA_TOKENS = (
    "storepartuid",
    "recid",
    "productuid",
    "t-store",
    "t-product",
    "tilda",
    "getproductslist",
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", html.unescape(str(value or ""))).strip()


def _type_values(value: Any) -> set[str]:
    values = value if isinstance(value, list) else [value]
    return {_clean(item).lower() for item in values if item is not None}


def _json_values(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict):
                    yield from _json_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _json_values(item)


def _absolute_url(value: str | None, page_url: str) -> str | None:
    value = _clean(value)
    if not value or value.startswith("data:"):
        return None
    return urljoin(page_url, value)


@dataclass(frozen=True, slots=True)
class Evidence:
    field: str
    value: Any
    source: str
    confidence: str
    selector: str | None = None


@dataclass(frozen=True, slots=True)
class ScriptArtifact:
    index: int
    script_type: str
    size: int
    sha256: str
    json_valid: bool
    detected_tokens: tuple[str, ...] = ()
    parse_error: str | None = None


@dataclass(frozen=True, slots=True)
class ImageArtifact:
    url: str
    source: str
    alt: str | None = None
    width: str | None = None
    height: str | None = None


@dataclass(slots=True)
class ProductPageInspection:
    url: str
    inspected_at: str
    html_size: int
    html_sha256: str
    title: str | None = None
    canonical_url: str | None = None
    language: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    open_graph: dict[str, str] = field(default_factory=dict)
    meta: dict[str, str] = field(default_factory=dict)
    json_ld: list[Any] = field(default_factory=list)
    json_ld_errors: list[str] = field(default_factory=list)
    breadcrumb_candidates: list[list[str]] = field(default_factory=list)
    images: list[ImageArtifact] = field(default_factory=list)
    characteristics: dict[str, list[str]] = field(default_factory=dict)
    data_attributes: dict[str, list[str]] = field(default_factory=dict)
    scripts: list[ScriptArtifact] = field(default_factory=list)
    tilda_tokens: dict[str, int] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _append_evidence(
    inspection: ProductPageInspection,
    field_name: str,
    value: Any,
    source: str,
    confidence: str,
    selector: str | None = None,
) -> None:
    if value is None or value == "" or value == []:
        return
    key = (field_name, json.dumps(value, ensure_ascii=False, sort_keys=True, default=str), source)
    existing = {
        (
            item.field,
            json.dumps(item.value, ensure_ascii=False, sort_keys=True, default=str),
            item.source,
        )
        for item in inspection.evidence
    }
    if key not in existing:
        inspection.evidence.append(Evidence(field_name, value, source, confidence, selector))


def _extract_meta(soup: BeautifulSoup, inspection: ProductPageInspection) -> None:
    for tag in soup.find_all("meta"):
        key = _clean(tag.get("property") or tag.get("name") or tag.get("itemprop"))
        value = _clean(tag.get("content"))
        if not key or not value:
            continue
        inspection.meta.setdefault(key, value)
        if key.lower().startswith("og:"):
            inspection.open_graph.setdefault(key.lower(), value)

    title = soup.title.get_text(" ", strip=True) if soup.title else None
    inspection.title = _clean(title) or None
    canonical = soup.find("link", attrs={"rel": "canonical"})
    inspection.canonical_url = _absolute_url(canonical.get("href"), inspection.url) if canonical else None
    html_tag = soup.find("html")
    inspection.language = _clean(html_tag.get("lang")) or None if html_tag else None

    if inspection.title:
        _append_evidence(inspection, "title", inspection.title, "html.title", "medium", "title")
    if inspection.open_graph.get("og:title"):
        _append_evidence(inspection, "title", inspection.open_graph["og:title"], "open_graph", "high", "meta[property='og:title']")
    if inspection.open_graph.get("og:description"):
        _append_evidence(inspection, "description", inspection.open_graph["og:description"], "open_graph", "medium", "meta[property='og:description']")
    if inspection.open_graph.get("og:image"):
        _append_evidence(
            inspection,
            "image",
            _absolute_url(inspection.open_graph["og:image"], inspection.url),
            "open_graph",
            "high",
            "meta[property='og:image']",
        )


def _extract_json_ld(soup: BeautifulSoup, inspection: ProductPageInspection) -> None:
    for index, script in enumerate(soup.find_all("script", attrs={"type": "application/ld+json"}), start=1):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            loaded = json.loads(raw)
            inspection.json_ld.append(loaded)
        except json.JSONDecodeError as exc:
            inspection.json_ld_errors.append(f"JSON-LD #{index}: {exc}")
            continue

        for item in _json_values(loaded):
            types = _type_values(item.get("@type"))
            if "product" in types:
                for field_name, key in (
                    ("title", "name"),
                    ("description", "description"),
                    ("sku", "sku"),
                    ("material", "material"),
                    ("category", "category"),
                    ("brand", "brand"),
                ):
                    value = item.get(key)
                    if isinstance(value, dict):
                        value = value.get("name") or value.get("@id")
                    _append_evidence(inspection, field_name, value, "json_ld.Product", "high")
                images = item.get("image")
                if images:
                    values = images if isinstance(images, list) else [images]
                    for value in values:
                        if isinstance(value, dict):
                            value = value.get("url") or value.get("contentUrl")
                        _append_evidence(inspection, "image", _absolute_url(value, inspection.url), "json_ld.Product", "high")
                offers = item.get("offers")
                offers = offers if isinstance(offers, list) else [offers]
                for offer in offers:
                    if not isinstance(offer, dict):
                        continue
                    _append_evidence(inspection, "price", offer.get("price") or offer.get("lowPrice"), "json_ld.Offer", "high")
                    _append_evidence(inspection, "currency", offer.get("priceCurrency"), "json_ld.Offer", "high")
                    _append_evidence(inspection, "availability", offer.get("availability"), "json_ld.Offer", "high")
            if "breadcrumblist" in types:
                names: list[str] = []
                elements = item.get("itemListElement")
                if isinstance(elements, list):
                    for element in elements:
                        if not isinstance(element, dict):
                            continue
                        nested = element.get("item")
                        name = element.get("name")
                        if isinstance(nested, dict):
                            name = name or nested.get("name")
                        cleaned = _clean(name)
                        if cleaned:
                            names.append(cleaned)
                if names and names not in inspection.breadcrumb_candidates:
                    inspection.breadcrumb_candidates.append(names)
                    _append_evidence(inspection, "breadcrumb", names, "json_ld.BreadcrumbList", "high")


def _extract_dom_breadcrumbs(soup: BeautifulSoup, inspection: ProductPageInspection) -> None:
    candidates: list[Tag] = []
    for tag in soup.find_all(True):
        class_text = " ".join(tag.get("class", []))
        identifier = _clean(tag.get("id"))
        aria = _clean(tag.get("aria-label"))
        marker = f"{class_text} {identifier} {aria}".lower()
        if "breadcrumb" in marker or "хлебн" in marker:
            candidates.append(tag)
    for tag in candidates[:20]:
        values = [_clean(node.get_text(" ", strip=True)) for node in tag.find_all(["a", "span", "li"])]
        values = [value for value in values if value]
        if not values:
            text = _clean(tag.get_text(" > ", strip=True))
            values = [part.strip() for part in text.split(">") if part.strip()]
        deduplicated = list(dict.fromkeys(values))
        if len(deduplicated) >= 2 and deduplicated not in inspection.breadcrumb_candidates:
            inspection.breadcrumb_candidates.append(deduplicated)
            _append_evidence(inspection, "breadcrumb", deduplicated, "dom.breadcrumb", "medium")


def _extract_images(soup: BeautifulSoup, inspection: ProductPageInspection) -> None:
    seen: set[str] = set()

    def add(value: Any, source: str, tag: Tag | None = None) -> None:
        url = _absolute_url(_clean(value), inspection.url)
        if not url or url in seen:
            return
        seen.add(url)
        inspection.images.append(
            ImageArtifact(
                url=url,
                source=source,
                alt=_clean(tag.get("alt")) or None if tag else None,
                width=_clean(tag.get("width")) or None if tag else None,
                height=_clean(tag.get("height")) or None if tag else None,
            )
        )

    for key in ("og:image", "twitter:image"):
        if key in inspection.meta:
            add(inspection.meta[key], f"meta.{key}")
    for tag in soup.find_all("img"):
        for attr in ("src", "data-src", "data-original", "data-lazy", "data-lazy-src"):
            add(tag.get(attr), f"img[{attr}]", tag)
        srcset = _clean(tag.get("srcset") or tag.get("data-srcset"))
        for part in srcset.split(","):
            add(part.strip().split(" ")[0] if part.strip() else None, "img[srcset]", tag)


def _extract_characteristics(soup: BeautifulSoup, inspection: ProductPageInspection) -> None:
    visible_text = _clean(soup.get_text(" ", strip=True))
    for match in _MEASUREMENT_RE.finditer(visible_text):
        label = match.group("label").lower()
        value = _clean(f"{match.group('value')} {match.group('unit') or ''}")
        inspection.characteristics.setdefault(label, [])
        if value not in inspection.characteristics[label]:
            inspection.characteristics[label].append(value)
            _append_evidence(inspection, label, value, "visible_text", "medium")

    for source_name, source in (("visible_text", visible_text),):
        match = _MATERIAL_RE.search(source)
        if match:
            material = _clean(match.group("value"))
            inspection.characteristics.setdefault("материал", [])
            if material and material not in inspection.characteristics["материал"]:
                inspection.characteristics["материал"].append(material)
                _append_evidence(inspection, "material", material, source_name, "medium")

    for pattern, status in _STATUS_PATTERNS:
        if pattern.search(visible_text):
            inspection.characteristics.setdefault("статус", [])
            if status not in inspection.characteristics["статус"]:
                inspection.characteristics["статус"].append(status)
                _append_evidence(inspection, "availability", status, "visible_text", "medium")
            break

    # Key/value structures commonly used for product characteristics.
    for row in soup.find_all(["tr", "li", "dl", "div"]):
        text = _clean(row.get_text(" ", strip=True))
        if len(text) > 200 or ":" not in text:
            continue
        key, value = [part.strip() for part in text.split(":", 1)]
        if not key or not value or len(key) > 50 or len(value) > 120:
            continue
        if any(token in key.lower() for token in ("высот", "ширин", "глубин", "материал", "размер", "вес", "статус", "налич")):
            inspection.characteristics.setdefault(key, [])
            if value not in inspection.characteristics[key]:
                inspection.characteristics[key].append(value)


def _extract_data_attributes(soup: BeautifulSoup, inspection: ProductPageInspection) -> None:
    values: dict[str, list[str]] = {}
    for tag in soup.find_all(True):
        for key, value in tag.attrs.items():
            if not key.startswith("data-"):
                continue
            if isinstance(value, list):
                cleaned = " ".join(_clean(item) for item in value)
            else:
                cleaned = _clean(value)
            if not cleaned:
                continue
            bucket = values.setdefault(key, [])
            if cleaned not in bucket and len(bucket) < 30:
                bucket.append(cleaned[:500])
    inspection.data_attributes = dict(sorted(values.items()))


def _extract_scripts(soup: BeautifulSoup, inspection: ProductPageInspection) -> None:
    for index, script in enumerate(soup.find_all("script"), start=1):
        raw = script.string or script.get_text(" ", strip=False) or ""
        script_type = _clean(script.get("type")) or "text/javascript"
        lowered = raw.lower()
        tokens = tuple(token for token in _TILDA_TOKENS if token in lowered)
        json_valid = False
        parse_error = None
        if script_type in {"application/json", "application/ld+json"} and raw.strip():
            try:
                json.loads(raw)
                json_valid = True
            except json.JSONDecodeError as exc:
                parse_error = str(exc)
        inspection.scripts.append(
            ScriptArtifact(
                index=index,
                script_type=script_type,
                size=len(raw),
                sha256=hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest(),
                json_valid=json_valid,
                detected_tokens=tokens,
                parse_error=parse_error,
            )
        )


def inspect_product_page(raw_html: str, page_url: str) -> ProductPageInspection:
    soup = BeautifulSoup(raw_html, "lxml")
    inspection = ProductPageInspection(
        url=page_url,
        inspected_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        html_size=len(raw_html.encode("utf-8", errors="replace")),
        html_sha256=hashlib.sha256(raw_html.encode("utf-8", errors="replace")).hexdigest(),
    )
    _extract_meta(soup, inspection)
    _extract_json_ld(soup, inspection)
    _extract_dom_breadcrumbs(soup, inspection)
    _extract_images(soup, inspection)
    _extract_characteristics(soup, inspection)
    _extract_data_attributes(soup, inspection)
    _extract_scripts(soup, inspection)
    lowered = raw_html.lower()
    inspection.tilda_tokens = {token: lowered.count(token) for token in _TILDA_TOKENS if token in lowered}

    if not inspection.json_ld:
        inspection.diagnostics.append("На странице не найден валидный JSON-LD.")
    if not inspection.breadcrumb_candidates:
        inspection.diagnostics.append("Breadcrumb не обнаружен ни в JSON-LD, ни в DOM.")
    if not inspection.images:
        inspection.diagnostics.append("Не обнаружены URL изображений.")
    if not any(item.field == "availability" for item in inspection.evidence):
        inspection.diagnostics.append("Статус наличия не подтверждён ни одним исследованным источником.")
    return inspection


def _best_values(inspection: ProductPageInspection, field_name: str) -> list[Evidence]:
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        [item for item in inspection.evidence if item.field == field_name],
        key=lambda item: (order.get(item.confidence, 9), item.source),
    )


def render_text_report(inspection: ProductPageInspection) -> str:
    lines = [
        "=" * 78,
        "AI BODHI PRODUCT PAGE INSPECTOR",
        "=" * 78,
        f"URL:          {inspection.url}",
        f"Inspected at: {inspection.inspected_at}",
        f"HTML bytes:   {inspection.html_size}",
        f"HTML SHA256:  {inspection.html_sha256}",
        "",
        "CONFIRMED FIELD CANDIDATES",
        "-" * 78,
    ]
    fields = (
        "title", "category", "breadcrumb", "availability", "price", "currency",
        "material", "height", "width", "depth", "diameter", "weight", "sku", "image",
    )
    for field_name in fields:
        candidates = _best_values(inspection, field_name)
        lines.append(f"{field_name}:")
        if not candidates:
            lines.append("  NOT FOUND")
        else:
            for item in candidates[:10]:
                value = json.dumps(item.value, ensure_ascii=False, default=str)
                lines.append(f"  [{item.confidence.upper()}] {value} <- {item.source}")

    lines.extend([
        "",
        "STRUCTURAL INVENTORY",
        "-" * 78,
        f"JSON-LD documents:       {len(inspection.json_ld)}",
        f"JSON-LD errors:          {len(inspection.json_ld_errors)}",
        f"Breadcrumb candidates:   {len(inspection.breadcrumb_candidates)}",
        f"Images:                  {len(inspection.images)}",
        f"Data attribute names:    {len(inspection.data_attributes)}",
        f"Scripts:                 {len(inspection.scripts)}",
        f"Scripts with Tilda data: {sum(bool(item.detected_tokens) for item in inspection.scripts)}",
        "",
        "TILDA TOKENS",
        "-" * 78,
    ])
    if inspection.tilda_tokens:
        for token, count in inspection.tilda_tokens.items():
            lines.append(f"{token}: {count}")
    else:
        lines.append("No known Tilda tokens detected.")

    lines.extend(["", "DIAGNOSTICS", "-" * 78])
    if inspection.diagnostics:
        lines.extend(f"- {item}" for item in inspection.diagnostics)
    else:
        lines.append("No structural warnings.")
    return "\n".join(lines) + "\n"


def _safe_stem(url: str) -> str:
    path = urlparse(url).path.strip("/").split("/")[-1] or "product"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path).strip("-._") or "product"
    return stem[:100]


def write_inspection_bundle(
    inspection: ProductPageInspection,
    raw_html: str,
    output_root: str | Path = "data/product_page_inspections",
) -> Path:
    bundle = Path(output_root) / f"{_safe_stem(inspection.url)}-{inspection.html_sha256[:10]}"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "page.html").write_text(raw_html, encoding="utf-8")
    (bundle / "inspection.json").write_text(
        json.dumps(inspection.to_dict(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    (bundle / "inspection.txt").write_text(render_text_report(inspection), encoding="utf-8")
    return bundle


def inspect_url(url: str, output_root: str | Path = "data/product_page_inspections", timeout: float = 30.0) -> Path:
    raw_html = fetch_product_page(url, timeout=timeout)
    inspection = inspect_product_page(raw_html, url)
    return write_inspection_bundle(inspection, raw_html, output_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect one published Tilda product page without modifying the catalog.")
    parser.add_argument("url", help="Published product page URL")
    parser.add_argument("--output", default="data/product_page_inspections", help="Directory for the inspection bundle")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)
    bundle = inspect_url(args.url, args.output, args.timeout)
    print("=" * 78)
    print("AI BODHI PRODUCT PAGE INSPECTOR")
    print("=" * 78)
    print(f"Inspection bundle: {bundle.resolve()}")
    print(f"Text report:       {(bundle / 'inspection.txt').resolve()}")
    print(f"JSON report:       {(bundle / 'inspection.json').resolve()}")
    print(f"Raw HTML:          {(bundle / 'page.html').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "Evidence",
    "ImageArtifact",
    "ProductPageInspection",
    "ScriptArtifact",
    "inspect_product_page",
    "inspect_url",
    "render_text_report",
    "write_inspection_bundle",
]
