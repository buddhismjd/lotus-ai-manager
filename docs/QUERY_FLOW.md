# Query Flow

## Public entry point

```python
backend.services.bodhi_service.answer_query(query)
```

## Required order

```text
1. Product handling
2. Active tour handling
3. Planned tour handling
4. Aspect responses
5. Legacy Knowledge Answer
6. Semantic Engine fallback
7. Safe fallback
```

## Why order matters

An earlier Semantic Engine implementation intercepted business queries.

Examples of incorrect behaviour:

```text
У вас есть Ваджра?
→ generic graph description

Поход в Лапчи
→ place node instead of planned-tour response
```

The orchestrator exists specifically to prevent this class of regression.

## Semantic Adapter v2

Allowed knowledge-style queries include:

```text
Расскажи про Ваджру
Какие практики связаны с Миларепой?
Что означает...
Какие места связаны с...
```

Rejected commercial/travel wording includes:

```text
У вас есть...
Хочу...
Ищу...
Купить...
Статуя...
Амулет...
Тур...
Поездка...
Поход...
```

## Response contract

All handlers return a `BuiltResponse`.

Typical fields:

```text
kind
text
title
url
```
