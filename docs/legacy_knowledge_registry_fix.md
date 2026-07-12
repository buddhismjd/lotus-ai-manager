# Legacy Knowledge Registry Fix

The legacy `backend/knowledge/answering.py` now resolves aspect wording
through the canonical Aspect Registry before falling back to its original
string matcher.

Processing order inside `_find_node()`:

1. exact graph lookup;
2. canonical aspect lookup through `canonical_aspect_name()`;
3. old `_labels_match()` fallback.

Example:

```text
Белой Таре
    ↓
canonical_aspect_name()
    ↓
Белая Тара
    ↓
KnowledgeGraph.find()
```

The fix is intentionally limited to nodes whose type is `aspect`.
Country and other legacy matching behaviour is unchanged.
