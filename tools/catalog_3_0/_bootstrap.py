"""Bootstrap direct tool execution from the repository root.

The diagnostic tools are intentionally runnable both as modules and as files:

    python -m tools.catalog_3_0.diagnostic
    python tools/catalog_3_0/diagnostic.py
"""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_root() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    root_text = str(project_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    return project_root
