import json

from backend.knowledge.knowledge_core import _read_definition


def test_reads_kind_format(tmp_path) -> None:
    path = tmp_path / "typed.json"
    path.write_text(
        json.dumps(
            {
                "id": "white_tara",
                "name": "Белая Тара",
                "kind": "bodhisattva",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    definition = _read_definition(path)

    assert definition.kind == "bodhisattva"


def test_reads_type_format(tmp_path) -> None:
    path = tmp_path / "modern.json"
    path.write_text(
        json.dumps(
            {
                "id": "white_tara",
                "name": "Белая Тара",
                "type": "bodhisattva",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    definition = _read_definition(path)

    assert definition.kind == "bodhisattva"


def test_infers_legacy_registry_kind(tmp_path) -> None:
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "id": "amitabha_buddha",
                "name": "Будда Амитабха",
                "aliases": ["Амитабха"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    definition = _read_definition(path)

    assert definition.kind == "buddha"
