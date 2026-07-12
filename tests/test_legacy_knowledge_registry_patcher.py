import ast
from pathlib import Path

from tools.patch_legacy_knowledge_registry import (
    patch_answering,
)


SOURCE = """from __future__ import annotations

from backend.knowledge.graph import (
    KnowledgeGraph,
    KnowledgeNode,
)


def _labels_match(left: str, right: str) -> bool:
    return left == right


def _find_node(
    graph: KnowledgeGraph,
    label: str,
    node_type: str,
) -> KnowledgeNode | None:
    exact = graph.find(label, node_type=node_type)

    if exact:
        return exact[0]

    for node in graph.nodes.values():
        if node.node_type != node_type:
            continue

        if _labels_match(label, node.label):
            return node

    return None
"""


def test_patcher_adds_registry_resolution(
    tmp_path: Path,
) -> None:
    path = tmp_path / "answering.py"
    path.write_text(SOURCE, encoding="utf-8")

    patch_answering(path)
    result = path.read_text(
        encoding="utf-8"
    )

    assert (
        "from backend.knowledge.aspect_registry "
        "import canonical_aspect_name"
        in result
    )
    assert (
        "canonical_name = "
        "canonical_aspect_name(label)"
        in result
    )
    ast.parse(result)


def test_patcher_is_idempotent(
    tmp_path: Path,
) -> None:
    path = tmp_path / "answering.py"
    path.write_text(SOURCE, encoding="utf-8")

    patch_answering(path)
    first = path.read_text(encoding="utf-8")

    patch_answering(path)
    second = path.read_text(encoding="utf-8")

    assert first == second
