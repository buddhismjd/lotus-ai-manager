from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from backend.integrations.product_page_snapshot import fetch_product_page

_SPACE_RE = re.compile(r"\s+")
_ASSIGNMENT_RE = re.compile(
    r"(?P<name>(?:window\.)?[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*=\s*",
)
_URL_RE = re.compile(r"https?://[^\s\"'<>\\]+|(?:getproductslist|tproduct|tilda)/[^\s\"'<>\\]+", re.IGNORECASE)
_ID_PATTERNS = {
    "storepartuid": re.compile(r"storepartuid[\"']?\s*[:=]\s*[\"']?(\d+)", re.IGNORECASE),
    "recid": re.compile(r"recid[\"']?\s*[:=]\s*[\"']?(\d+)", re.IGNORECASE),
    "productuid": re.compile(r"productuid[\"']?\s*[:=]\s*[\"']?(\d+)", re.IGNORECASE),
}
_TOKENS = (
    "storepartuid",
    "recid",
    "productuid",
    "getproductslist",
    "t-store",
    "t-product",
    "tilda",
    "availability",
    "price",
    "material",
    "image",
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", html.unescape(str(value or ""))).strip()


def _safe_stem(url: str) -> str:
    leaf = urlparse(url).path.strip("/").split("/")[-1] or "product"
    return re.sub(r"[^A-Za-z0-9._-]+", "-", leaf).strip("-._")[:100] or "product"


def _balanced_fragment(text: str, start: int) -> tuple[str, int] | None:
    if start >= len(text) or text[start] not in "[{":
        return None
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'", "`"}:
            quote = char
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[start:index + 1], index + 1
    return None


def _extract_json_candidate(fragment: str) -> Any | None:
    try:
        return json.loads(fragment)
    except json.JSONDecodeError:
        return None


def _snippets(text: str, token: str, radius: int = 320, limit: int = 20) -> list[str]:
    result: list[str] = []
    lowered = text.lower()
    needle = token.lower()
    offset = 0
    while len(result) < limit:
        index = lowered.find(needle, offset)
        if index < 0:
            break
        start = max(0, index - radius)
        end = min(len(text), index + len(token) + radius)
        snippet = _clean(text[start:end])
        if snippet and snippet not in result:
            result.append(snippet)
        offset = index + len(token)
    return result


@dataclass(frozen=True, slots=True)
class AssignmentArtifact:
    name: str
    value_kind: str
    size: int
    sha256: str
    json_valid: bool
    preview: str
    source_script: int


@dataclass(frozen=True, slots=True)
class ScriptInspection:
    index: int
    src: str | None
    script_type: str
    size: int
    sha256: str
    tokens: tuple[str, ...]
    urls: tuple[str, ...]
    identifiers: dict[str, tuple[str, ...]]
    assignments: tuple[AssignmentArtifact, ...]
    snippets: dict[str, tuple[str, ...]]


@dataclass(slots=True)
class TildaScriptInspection:
    url: str
    inspected_at: str
    html_size: int
    html_sha256: str
    scripts: list[ScriptInspection] = field(default_factory=list)
    external_scripts: list[str] = field(default_factory=list)
    aggregate_identifiers: dict[str, list[str]] = field(default_factory=dict)
    aggregate_urls: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _extract_assignments(raw: str, script_index: int) -> tuple[AssignmentArtifact, ...]:
    artifacts: list[AssignmentArtifact] = []
    seen: set[tuple[str, str]] = set()
    for match in _ASSIGNMENT_RE.finditer(raw):
        cursor = match.end()
        while cursor < len(raw) and raw[cursor].isspace():
            cursor += 1
        if cursor >= len(raw) or raw[cursor] not in "[{":
            continue
        balanced = _balanced_fragment(raw, cursor)
        if balanced is None:
            continue
        fragment, _ = balanced
        digest = hashlib.sha256(fragment.encode("utf-8", errors="replace")).hexdigest()
        key = (match.group("name"), digest)
        if key in seen:
            continue
        seen.add(key)
        parsed = _extract_json_candidate(fragment)
        artifacts.append(
            AssignmentArtifact(
                name=match.group("name"),
                value_kind="object" if fragment.startswith("{") else "array",
                size=len(fragment),
                sha256=digest,
                json_valid=parsed is not None,
                preview=_clean(fragment[:600]),
                source_script=script_index,
            )
        )
    return tuple(artifacts)


def inspect_tilda_scripts(raw_html: str, page_url: str) -> TildaScriptInspection:
    soup = BeautifulSoup(raw_html, "lxml")
    inspection = TildaScriptInspection(
        url=page_url,
        inspected_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        html_size=len(raw_html.encode("utf-8", errors="replace")),
        html_sha256=hashlib.sha256(raw_html.encode("utf-8", errors="replace")).hexdigest(),
    )
    aggregate_urls: list[str] = []
    aggregate_ids: dict[str, list[str]] = {name: [] for name in _ID_PATTERNS}

    for index, script in enumerate(soup.find_all("script"), start=1):
        raw = script.string or script.get_text(" ", strip=False) or ""
        src = _clean(script.get("src")) or None
        if src:
            src = urljoin(page_url, src)
            if src not in inspection.external_scripts:
                inspection.external_scripts.append(src)
        script_type = _clean(script.get("type")) or "text/javascript"
        lowered = raw.lower()
        tokens = tuple(token for token in _TOKENS if token in lowered)
        urls = tuple(dict.fromkeys(_URL_RE.findall(raw)))
        identifiers: dict[str, tuple[str, ...]] = {}
        for name, pattern in _ID_PATTERNS.items():
            values = tuple(dict.fromkeys(pattern.findall(raw)))
            identifiers[name] = values
            for value in values:
                if value not in aggregate_ids[name]:
                    aggregate_ids[name].append(value)
        for value in urls:
            if value not in aggregate_urls:
                aggregate_urls.append(value)
        snippets = {
            token: tuple(_snippets(raw, token))
            for token in tokens
        }
        inspection.scripts.append(
            ScriptInspection(
                index=index,
                src=src,
                script_type=script_type,
                size=len(raw),
                sha256=hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest(),
                tokens=tokens,
                urls=urls,
                identifiers=identifiers,
                assignments=_extract_assignments(raw, index),
                snippets=snippets,
            )
        )

    inspection.aggregate_identifiers = aggregate_ids
    inspection.aggregate_urls = aggregate_urls
    inline_with_tilda = [item for item in inspection.scripts if item.tokens]
    if not inline_with_tilda:
        inspection.diagnostics.append("Inline-скрипты с маркерами Tilda не обнаружены.")
    if inline_with_tilda and not any(item.assignments for item in inline_with_tilda):
        inspection.diagnostics.append(
            "Маркеры Tilda обнаружены, но присваивания сбалансированных объектов/массивов не найдены. "
            "Изучите сохранённые сырые скрипты и snippets."
        )
    if not any(inspection.aggregate_identifiers.values()):
        inspection.diagnostics.append("Не найдены storepartuid, recid или productuid внутри inline-скриптов.")
    return inspection


def render_script_report(inspection: TildaScriptInspection) -> str:
    lines = [
        "=" * 78,
        "AI BODHI TILDA SCRIPT INSPECTOR",
        "=" * 78,
        f"URL:          {inspection.url}",
        f"Inspected at: {inspection.inspected_at}",
        f"HTML bytes:   {inspection.html_size}",
        f"HTML SHA256:  {inspection.html_sha256}",
        "",
        "AGGREGATE IDENTIFIERS",
        "-" * 78,
    ]
    for name, values in inspection.aggregate_identifiers.items():
        lines.append(f"{name}: {', '.join(values) if values else 'NOT FOUND'}")
    lines.extend(["", "DISCOVERED URLS", "-" * 78])
    if inspection.aggregate_urls:
        lines.extend(f"- {value}" for value in inspection.aggregate_urls)
    else:
        lines.append("No API/product URLs found in inline scripts.")
    lines.extend(["", "SCRIPT INVENTORY", "-" * 78])
    for script in inspection.scripts:
        if not script.tokens and not script.assignments and not script.urls:
            continue
        lines.append(
            f"Script #{script.index}: type={script.script_type} size={script.size} "
            f"tokens={','.join(script.tokens) or '-'} assignments={len(script.assignments)} urls={len(script.urls)}"
        )
        if script.src:
            lines.append(f"  src: {script.src}")
        for assignment in script.assignments:
            lines.append(
                f"  assignment {assignment.name}: kind={assignment.value_kind} size={assignment.size} "
                f"json_valid={assignment.json_valid} sha256={assignment.sha256[:12]}"
            )
            lines.append(f"    preview: {assignment.preview}")
        for token, snippets in script.snippets.items():
            for number, snippet in enumerate(snippets[:3], start=1):
                lines.append(f"  snippet[{token}#{number}]: {snippet}")
    lines.extend(["", "EXTERNAL SCRIPTS", "-" * 78])
    if inspection.external_scripts:
        lines.extend(f"- {value}" for value in inspection.external_scripts)
    else:
        lines.append("No external scripts.")
    lines.extend(["", "DIAGNOSTICS", "-" * 78])
    if inspection.diagnostics:
        lines.extend(f"- {value}" for value in inspection.diagnostics)
    else:
        lines.append("No structural warnings.")
    return "\n".join(lines) + "\n"


def write_script_bundle(
    inspection: TildaScriptInspection,
    raw_html: str,
    output_root: str | Path = "data/tilda_script_inspections",
) -> Path:
    root = Path(output_root) / f"{_safe_stem(inspection.url)}-{inspection.html_sha256[:10]}"
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    soup = BeautifulSoup(raw_html, "lxml")
    for index, script in enumerate(soup.find_all("script"), start=1):
        raw = script.string or script.get_text(" ", strip=False) or ""
        (scripts_dir / f"script_{index:03d}.js").write_text(raw, encoding="utf-8")
    (root / "script_inspection.json").write_text(
        json.dumps(inspection.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "script_inspection.txt").write_text(render_script_report(inspection), encoding="utf-8")
    return root


def inspect_script_url(
    url: str,
    output_root: str | Path = "data/tilda_script_inspections",
    timeout: float = 30.0,
) -> Path:
    raw_html = fetch_product_page(url, timeout=timeout)
    inspection = inspect_tilda_scripts(raw_html, url)
    return write_script_bundle(inspection, raw_html, output_root)


__all__ = [
    "AssignmentArtifact",
    "ScriptInspection",
    "TildaScriptInspection",
    "inspect_script_url",
    "inspect_tilda_scripts",
    "render_script_report",
    "write_script_bundle",
]
