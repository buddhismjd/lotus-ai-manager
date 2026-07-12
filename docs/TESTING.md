# Testing

## Key regression suite

```cmd
python -m pytest tests\test_bodhi_service.py
python -m pytest tests\test_bodhi_api.py
python -m pytest tests\test_aspect_responses.py
python -m pytest tests\test_planned_tours.py
python -m pytest tests\test_knowledge_answers.py
python -m pytest tests\test_semantic_service_adapter.py
python -m pytest tests\test_semantic_service_adapter_v2.py
python -m pytest tests\test_semantic_engine.py
python -m pytest tests\test_semantic_engine_runtime.py
```

## Knowledge Graph

```cmd
python -m pytest tests\test_knowledge_graph_models.py
python -m pytest tests\test_knowledge_graph_repository.py
python -m pytest tests\test_knowledge_graph_loader.py
python -m pytest tests\test_runtime_knowledge_graph.py
```

## Catalog

```cmd
python -m pytest tests\test_search_intent_entities.py
python -m pytest tests\test_search_regression.py
python -m tools.search_benchmark
python -m tools.catalog_health
```

## Tours

```cmd
python -m pytest tests\test_tour_intelligence.py
python -m tools.tour_profile_report
python -m tools.tour_data_diagnostics
```

## Repository health

```cmd
python -m pytest tests\test_repository_health.py
python -m tools.repository_health
```

The repository-health check prevents tracked caches, local databases, backup
directories, and temporary patch scripts from returning to Git history.

## Full suite

```cmd
python -m pytest
```

## Completion rule

A feature is not complete until:

- profile tests pass;
- regression suite passes;
- smoke/report output is reviewed;
- documentation is updated.
