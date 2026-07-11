from __future__ import annotations

import json
from pathlib import Path

from backend.knowledge_graph.models import (
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    RelationType,
)
from backend.knowledge_graph.repository import (
    KnowledgeGraphRepository,
)


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


def load_graph(
    data_dir: Path | None = None,
) -> KnowledgeGraphRepository:
    base = data_dir or DEFAULT_DATA_DIR
    repository = KnowledgeGraphRepository()

    entities_dir = base / "entities"
    relations_dir = base / "relations"

    for path in sorted(entities_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))

        repository.add_entity(
            KnowledgeEntity(
                entity_id=str(payload["id"]),
                entity_type=EntityType(str(payload["type"])),
                name=str(payload["name"]),
                aliases=tuple(payload.get("aliases", ())),
                description=str(payload.get("description", "") or ""),
                keywords=tuple(payload.get("keywords", ())),
                metadata={
                    str(key): str(value)
                    for key, value in payload.get(
                        "metadata",
                        {},
                    ).items()
                },
            )
        )

    for path in sorted(relations_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))

        items = payload if isinstance(payload, list) else [payload]

        for item in items:
            repository.add_relation(
                KnowledgeRelation(
                    source_id=str(item["source_id"]),
                    relation_type=RelationType(
                        str(item["relation_type"])
                    ),
                    target_id=str(item["target_id"]),
                    metadata={
                        str(key): str(value)
                        for key, value in item.get(
                            "metadata",
                            {},
                        ).items()
                    },
                )
            )

    return repository


__all__ = ["DEFAULT_DATA_DIR", "load_graph"]
