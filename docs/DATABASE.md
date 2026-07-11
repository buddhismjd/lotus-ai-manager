# AI Bodhi — Database

## Хранилище

Основное локальное хранилище — SQLite.

Ожидаемый путь:

```text
data/lotus_ai.db
```

Файл базы данных не должен добавляться в Git.

## Основные таблицы

### documents

Универсальные документы из сайта и интеграций.

Примерные поля:

- `id`
- `source_type`
- `type`
- `title`
- `url`
- `summary`
- `content`
- `enabled`
- `priority`
- `content_hash`
- timestamps

### document_chunks

Фрагменты документов для поиска.

Связь:

```text
documents 1 → N document_chunks
```

### product_profiles

Структурированные товарные профили.

Поля:

- `product_id`
- `product_type`
- `primary_entity`
- `entities_json`
- `materials_json`
- `usages_json`
- `traditions_json`
- `synonyms_json`
- `keywords_json`
- `source_hash`
- `created_at`
- `updated_at`

### products

Структурированная модель товара, используемая `ProductRepository`.

Типичные поля:

- title;
- description;
- category;
- material;
- keywords;
- price;
- currency;
- URL;
- source ID.

### tours

Структурированная модель тура.

Типичные поля:

- title;
- country;
- region;
- description;
- difficulty;
- guide;
- keywords;
- URL.

### dialogs / messages / leads

Используются для диалогов и лидов:

- `dialogs` — сессии;
- `messages` — сообщения;
- `leads` — контакты и квалификация;
- `settings` — настройки системы.

## Правила данных

1. Tilda UID должен использоваться как стабильный идентификатор товара.
2. Повторная синхронизация должна выполнять upsert.
3. Дубли по одному UID недопустимы.
4. JSON-поля должны хранить списки, а не строки с разделителями.
5. `source_hash` используется для обнаружения изменений.
6. Удаление товара из Tilda не должно автоматически удалять историю без отдельного правила.
7. Пустой короткий текст должен сохраняться хотя бы одним chunk.

## Проверки

Статистика профилей:

```cmd
python -c "from backend.catalog.product_profiles import get_profile_stats; print(get_profile_stats())"
```

Профиль конкретного товара:

```cmd
python -c "from backend.catalog.product_profiles import get_product_profile; print(get_product_profile('product-384940676312'))"
```

Количество товаров:

```cmd
python -c "from backend.catalog.repositories import ProductRepository; print(len(ProductRepository().list_all()))"
```

## Миграции

Пока проект локальный, допустимы идемпотентные `CREATE TABLE IF NOT EXISTS`.

Перед production-релизом рекомендуется выделить версионированные миграции:

```text
backend/storage/migrations/
```

Каждая миграция должна:

- иметь номер;
- быть повторно безопасной;
- создавать резервную копию перед изменением;
- проходить тест на чистой и существующей базе.
