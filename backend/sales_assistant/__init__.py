"""Public sales-assistant API without eager service imports.

Submodules such as tour discovery are used by lower-level catalogue code.  The
service is therefore loaded lazily to keep the package dependency graph acyclic.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.sales_assistant.service import SalesAssistant

__all__ = ["SalesAssistant", "get_sales_assistant"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from backend.sales_assistant.service import SalesAssistant, get_sales_assistant

        exports = {
            "SalesAssistant": SalesAssistant,
            "get_sales_assistant": get_sales_assistant,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
