# AI Bodhi — Architecture

## Назначение

AI Bodhi — интеллектуальный помощник проекта «Свет Лотоса». Система консультирует посетителей сайта по товарам, турам и программам, использует структурированный каталог и передаёт диалог человеку при отсутствии надёжного ответа.

## Общая схема

```text
Пользователь
    ↓
Widget
    ↓
FastAPI API
    ↓
Dynamic Query Router
    ├── Product Search
    ├── Tour Search
    ├── Knowledge Search
    └── Human Fallback
          ↓
SQLite
    ├── documents
    ├── document_chunks
    ├── product_profiles
    ├── products
    ├── tours
    └── dialogs / messages / leads
```

## Основные подсистемы

### Backend API

`backend/main.py`

Отвечает за HTTP-маршруты, healthcheck, чат API и интеграцию с виджетом.

Ключевой endpoint:

```text
POST /api/bodhi/chat
```

### Каталог товаров

`backend/catalog/`

Содержит модели, репозитории и слой Product Intelligence.

Основные модули:

- `models.py`
- `repositories.py`
- `product_intelligence.py`
- `product_profiles.py`

### Интеграции Tilda

`backend/integrations/`

Источники данных:

- Tilda Store API — основной источник товаров;
- Tilda API/YML — резервные и вспомогательные источники;
- crawler — резервный способ импорта опубликованных карточек.

### Поисковое ядро

`backend/rag/dynamic_query_router.py`

Задачи:

- определить намерение пользователя;
- разделить товары и туры;
- определить тип товара;
- использовать структурированные признаки;
- не подменять отсутствующую сущность похожим товаром;
- возвращать безопасный fallback.

### Виджет

`widget/`

Содержит интерфейс AI Bodhi:

- плавающая кнопка;
- окно чата;
- отправка запроса;
- отображение ответа;
- адаптивная мобильная версия.

## Принципы архитектуры

1. Tilda Store API — основной источник товарного каталога.
2. SQLite — локальное хранилище и единый источник данных для поиска.
3. Структурированные профили предпочтительнее повторного анализа текста.
4. Отсутствие точного результата не должно приводить к случайной рекомендации.
5. Новая функциональность обязана иметь тесты и проверяться benchmark.
6. Существующая рабочая логика сохраняется как fallback.
7. Проект остаётся закрытым коммерческим продуктом.

## Поток синхронизации каталога

```text
Tilda Store API
    ↓
tilda_store_api.py
    ↓
Product Intelligence
    ↓
documents + product_profiles
    ↓
reload_catalog_index()
    ↓
Search Benchmark
```

## Поток пользовательского запроса

```text
Widget
    ↓
/api/bodhi/chat
    ↓
bodhi_service.answer_query()
    ↓
dynamic_query_router.route_query()
    ↓
Repositories / product_profiles
    ↓
Response Builder
    ↓
Ответ пользователю
```

## Definition of Done

Модуль считается завершённым, когда:

- код компилируется;
- тесты проходят;
- benchmark не ухудшился;
- документация обновлена;
- изменение проверено на реальном каталоге.
