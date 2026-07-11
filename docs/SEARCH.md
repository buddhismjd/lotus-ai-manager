# AI Bodhi — Search

## Цель

Поиск должен возвращать релевантный товар или тур и никогда не подменять отсутствующий объект случайным совпадением.

## Основные компоненты

### Dynamic Query Router

Файл:

```text
backend/rag/dynamic_query_router.py
```

Функции:

- нормализация;
- исправление частых опечаток;
- определение intent;
- определение типа товара;
- разделение product/tour;
- фильтрация кандидатов;
- ранжирование;
- безопасный fallback.

### Product Intelligence

Файл:

```text
backend/catalog/product_intelligence.py
```

Определяет:

- тип товара;
- буддийскую сущность;
- материал;
- назначение;
- ключевые слова.

### Product Profiles

Файл:

```text
backend/catalog/product_profiles.py
```

Хранит нормализованные структурированные признаки.

## Принцип ранжирования

Приоритеты:

1. точный тип товара;
2. точная сущность;
3. назначение;
4. материал;
5. совпадение названия;
6. совпадение описания;
7. fuzzy match.

## Правила безопасности

- Запрос «статуя Будды» не должен возвращать амулет.
- Запрос «амулет Ченрезига» не должен возвращать амулет другой сущности.
- Запрос «есть велосипед?» не должен возвращать случайный товар.
- Географический туристический запрос не должен возвращать товар из той же страны.
- При отсутствии точного совпадения должен возвращаться fallback.

## Тесты

```cmd
python -m pytest tests	est_semantic_ranker.py
python -m pytest tests	est_search_intent_entities.py
python -m pytest tests	est_search_regression.py
```

## Benchmark

```cmd
python -m tools.search_benchmark
```

Результаты:

```text
data/search_benchmark.csv
data/search_benchmark.html
```

## Диагностика

```cmd
python -m tools.search_diagnostics
```

Отчёты:

```text
data/search_diagnostics.csv
data/search_diagnostics.html
```

## Известные ограничения

- Tour Intelligence ещё не завершён.
- Некоторые товары отсутствуют как самостоятельные позиции.
- Назначение товара может не определяться, если описание слишком краткое.
- Product Profiles ещё должны стать главным источником признаков роутера.
