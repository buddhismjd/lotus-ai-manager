# AI Bodhi — Documentation

Основные документы проекта:

- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Database](DATABASE.md)
- [Search](SEARCH.md)
- [API](API.md)

## Текущая версия

Рабочая ветка:

```text
feature/structured-catalog
```

Основной приоритет:

```text
Product Profiles Integration → Tour Intelligence → Knowledge Graph
```

## Обязательные проверки перед коммитом

```cmd
python -m py_compile backendag\dynamic_query_router.py
python -m pytest tests	est_semantic_ranker.py
python -m pytest tests	est_search_intent_entities.py
python -m pytest tests	est_search_regression.py
python -m tools.search_benchmark
```
