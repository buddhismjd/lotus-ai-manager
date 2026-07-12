# AI Bodhi Orchestrator v1

The orchestrator preserves the established business handlers and uses the
Semantic Engine only when they return a fallback response.

## Priority

1. Existing product handling
2. Existing tour handling
3. Planned tours
4. Aspect responses
5. Existing knowledge answers
6. Semantic Engine
7. Original fallback

The current `answer_query()` is renamed to `_answer_query_legacy()`.
A small wrapper becomes the public `answer_query()`.

This avoids duplicating or rewriting the established routing logic.
