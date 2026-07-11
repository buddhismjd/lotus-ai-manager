from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable


KNOWLEDGE_DIR = Path(__file__).resolve().parent / "aspects"

ALLOWED_KINDS = {
    "buddha",
    "bodhisattva",
    "protector",
    "teacher",
    "practice_item",
}

KIND_LABELS = {
    "buddha": "Будда",
    "bodhisattva": "Бодхисаттва",
    "protector": "Защитник",
    "teacher": "Учитель",
    "practice_item": "Предмет для практики",
}


@dataclass(frozen=True, slots=True)
class KnowledgeDefinition:
    knowledge_id: str
    name: str
    kind: str
    aliases: tuple[str, ...] = ()
    short_description: str = ""
    keywords: tuple[str, ...] = ()
    related_knowledge_ids: tuple[str, ...] = ()
    related_practices: tuple[str, ...] = ()
    related_places: tuple[str, ...] = ()
    product_description_fields: tuple[str, ...] = ()

    @property
    def kind_label(self) -> str:
        return KIND_LABELS.get(self.kind, self.kind)

    @property
    def all_names(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.name, *self.aliases)))


LEGACY_KIND_BY_ID = {
    "amitabha_buddha": "buddha",
    "shakyamuni_buddha": "buddha",
    "medicine_buddha": "buddha",
    "white_tara": "bodhisattva",
    "green_tara": "bodhisattva",
    "chenrezig": "bodhisattva",
    "manjushri": "bodhisattva",
    "milarepa": "teacher",
    "guru_rinpoche": "teacher",
    "mahakala": "protector",
    "garuda": "protector",
    "vajra": "practice_item",
    "phurba": "practice_item",
}


def _infer_kind(payload: dict) -> str:
    knowledge_id = str(payload.get("id", "") or "").strip()
    inferred = LEGACY_KIND_BY_ID.get(knowledge_id)

    if inferred:
        return inferred

    name = str(payload.get("name", "") or "").lower()

    if "будда" in name:
        return "buddha"
    if "тара" in name or "ченрезиг" in name or "манджушри" in name:
        return "bodhisattva"
    if "махакал" in name or "гаруд" in name:
        return "protector"
    if "милареп" in name or "гуру ринпоче" in name:
        return "teacher"
    if "ваджр" in name or "пхурб" in name:
        return "practice_item"

    # Unknown legacy entries remain readable instead of crashing.
    return "teacher"


def _read_definition(path: Path) -> KnowledgeDefinition:
    payload = json.loads(path.read_text(encoding="utf-8"))

    knowledge_id = str(payload["id"]).strip()
    name = str(payload["name"]).strip()
    kind = str(
        payload.get("kind")
        or payload.get("type")
        or _infer_kind(payload)
    ).strip()

    if kind not in ALLOWED_KINDS:
        raise ValueError(
            f"{path.name}: unsupported kind {kind!r}. "
            f"Allowed: {sorted(ALLOWED_KINDS)}"
        )

    return KnowledgeDefinition(
        knowledge_id=knowledge_id,
        name=name,
        kind=kind,
        aliases=tuple(payload.get("aliases", ())),
        short_description=str(
            payload.get("short_description", "") or ""
        ).strip(),
        keywords=tuple(payload.get("keywords", ())),
        related_knowledge_ids=tuple(
            payload.get("related_knowledge_ids", ())
        ),
        related_practices=tuple(
            payload.get("related_practices", ())
        ),
        related_places=tuple(payload.get("related_places", ())),
        product_description_fields=tuple(
            payload.get("product_description_fields", ())
        ),
    )


@lru_cache(maxsize=1)
def load_knowledge_core() -> dict[str, KnowledgeDefinition]:
    definitions: dict[str, KnowledgeDefinition] = {}

    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        definition = _read_definition(path)

        if definition.knowledge_id in definitions:
            raise ValueError(
                f"Duplicate knowledge id: {definition.knowledge_id}"
            )

        definitions[definition.knowledge_id] = definition

    _validate_relations(definitions)
    return definitions


def _validate_relations(
    definitions: dict[str, KnowledgeDefinition],
) -> None:
    known_ids = set(definitions)

    for definition in definitions.values():
        missing = set(definition.related_knowledge_ids) - known_ids

        if missing:
            raise ValueError(
                f"{definition.knowledge_id}: unknown related ids "
                f"{sorted(missing)}"
            )


def get_knowledge_definition(
    knowledge_id: str,
) -> KnowledgeDefinition | None:
    return load_knowledge_core().get(knowledge_id)


def list_by_kind(kind: str) -> tuple[KnowledgeDefinition, ...]:
    return tuple(
        sorted(
            (
                definition
                for definition in load_knowledge_core().values()
                if definition.kind == kind
            ),
            key=lambda item: item.name.lower(),
        )
    )


def description_recommendations(
    knowledge_id: str,
) -> tuple[str, ...]:
    definition = get_knowledge_definition(knowledge_id)

    if definition is None:
        return ()

    return definition.product_description_fields


__all__ = [
    "ALLOWED_KINDS",
    "KIND_LABELS",
    "KnowledgeDefinition",
    "description_recommendations",
    "get_knowledge_definition",
    "list_by_kind",
    "load_knowledge_core",
]
