# Semantic Adapter 2.0

Semantic Engine is a guarded fallback.

## Rejected by the adapter

Commercial and operational wording:

- "У вас есть Ваджра?"
- "Статуя Белой Тары"
- "Поход в Лапчи"
- "Есть поездка в Непал?"
- "Хочу на Кайлас"
- "Покажи товары"

These queries remain with the established catalog and tour handlers.

## Accepted by the adapter

Knowledge-style wording:

- "Расскажи про Ваджру"
- "Какие практики связаны с Миларепой?"
- "Что означает..."
- "Какие места связаны с..."

## Orchestrator repair

The previous semantic integration remained inside
`_answer_query_legacy()` because it was located after the function
docstring. The repair tool removes that interception while preserving the
semantic fallback in the public wrapper.
