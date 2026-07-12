from __future__ import annotations

import ast
from pathlib import Path


IMPORT_LINE = (
    "from backend.knowledge.aspect_registry "
    "import canonical_aspect_name\n"
)

NEW_FUNCTION = """def _find_node(
    graph: KnowledgeGraph,
    label: str,
    node_type: str,
) -> KnowledgeNode | None:
    exact = graph.find(label, node_type=node_type)

    if exact:
        return exact[0]

    if node_type == "aspect":
        canonical_name = canonical_aspect_name(label)

        if canonical_name:
            canonical = graph.find(
                canonical_name,
                node_type=node_type,
            )

            if canonical:
                return canonical[0]

    for node in graph.nodes.values():
        if node.node_type != node_type:
            continue

        if _labels_match(label, node.label):
            return node

    return None
"""


def _function_span(
    text: str,
    function_name: str,
) -> tuple[int, int]:
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)

    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == function_name
        ):
            start = sum(
                len(line)
                for line in lines[: node.lineno - 1]
            )
            end_lineno = node.end_lineno or node.lineno
            end = sum(
                len(line)
                for line in lines[:end_lineno]
            )
            return start, end

    raise RuntimeError(
        f"{function_name}() was not found"
    )


def _insert_import(text: str) -> str:
    if IMPORT_LINE in text:
        return text

    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    insert_after = 0

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end_lineno = node.end_lineno or node.lineno
            insert_after = max(insert_after, end_lineno)
        elif not isinstance(node, ast.Expr):
            break

    position = sum(
        len(line)
        for line in lines[:insert_after]
    )
    return text[:position] + IMPORT_LINE + text[position:]


def patch_answering(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _insert_import(text)

    start, end = _function_span(
        text,
        "_find_node",
    )

    current = text[start:end]

    if (
        "canonical_name = canonical_aspect_name(label)"
        not in current
    ):
        replacement = NEW_FUNCTION
        if end < len(text) and text[end:end + 1] != "\n":
            replacement += "\n"

        text = text[:start] + replacement + text[end:]

    ast.parse(text)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    path = Path(
        "backend/knowledge/answering.py"
    )

    if not path.exists():
        raise FileNotFoundError(path)

    patch_answering(path)
    print(f"Patched: {path}")


if __name__ == "__main__":
    main()
