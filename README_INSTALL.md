# AI Bodhi Knowledge Stabilization v1

Исправляет две блокирующие ошибки.

## 1. Knowledge Graph relations

Было:

```python
_relations: set[KnowledgeRelation]
```

`KnowledgeRelation` содержит `metadata: dict`, поэтому объект нельзя
поместить в `set`.

Стало:

```python
_relations: list[KnowledgeRelation]
```

Повторные связи не добавляются:

```python
if relation not in self._relations:
    self._relations.append(relation)
```

## 2. Knowledge Core compatibility

Загрузчик теперь понимает три формата:

```json
{"kind": "bodhisattva"}
```

```json
{"type": "bodhisattva"}
```

и старые registry JSON без обоих полей. Для известных ID тип безопасно
восстанавливается.

## Установка

Распакуйте архив в корень проекта с заменой:

```text
backend/knowledge_graph/repository.py
backend/knowledge/knowledge_core.py
```

## Проверка

```cmd
python -m py_compile backend\knowledge_graph\repository.py
python -m py_compile backend\knowledge\knowledge_core.py

python -m pytest tests\test_knowledge_graph_stabilization.py
python -m pytest tests\test_knowledge_core_compatibility.py

python -m pytest tests\test_knowledge_graph_models.py
python -m pytest tests\test_knowledge_graph_repository.py
python -m pytest tests\test_knowledge_graph_loader.py
python -m pytest tests\test_knowledge_core.py
```

## Отчёты

```cmd
python -m tools.knowledge_graph_v1_report
python -m tools.knowledge_core_report
```

## Быстрая проверка

```cmd
python -c "from backend.knowledge_graph.loader import load_graph; from backend.knowledge_graph.service import describe_entity; g=load_graph(); print(describe_entity('milarepa', repository=g))"
```

```cmd
python -c "from backend.knowledge.knowledge_advisor import advise_product_description; print(advise_product_description('vajra', existing_description='Ритуальный предмет.'))"
```

## Git

```cmd
git add backend/knowledge_graph/repository.py backend/knowledge/knowledge_core.py tests/test_knowledge_graph_stabilization.py tests/test_knowledge_core_compatibility.py
git commit -m "Stabilize knowledge graph and core loaders"
git push
```
