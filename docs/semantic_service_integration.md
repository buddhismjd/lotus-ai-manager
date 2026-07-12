# Semantic Engine → Bodhi Service Integration

The adapter gives Semantic Engine first priority for grounded semantic
questions.

Processing order:

1. Semantic Engine
2. Existing planned-tour handler
3. Existing aspect grouping
4. Dynamic query router
5. Existing fallback logic

If Semantic Engine cannot resolve the question, it returns `None` and the
old pipeline continues unchanged.

## Why a patch tool is included

`backend/services/bodhi_service.py` has evolved through several releases.
The patch tool modifies the current local version instead of replacing it
with an older snapshot.
