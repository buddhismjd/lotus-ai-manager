# AI Bodhi — API

## Base URL

Локально:

```text
http://127.0.0.1:8000
```

## Chat API

### POST /api/bodhi/chat

Запрос:

```json
{
  "message": "Хочу статую Белой Тары"
}
```

Ответ:

```json
{
  "answer": "🌸 ...",
  "status": "bodhi_product",
  "kind": "product",
  "title": "Статуя Белой Тары",
  "url": "https://..."
}
```

Пустой запрос:

```json
{
  "answer": "Напишите вопрос.",
  "status": "empty"
}
```

## Старый Chat API

### POST /api/chat

Сохраняется для обратной совместимости.

## CORS

Локальная разработка:

```python
allow_origins=["*"]
```

Production:

```python
allow_origins=[
    "https://svet-lotosa.tilda.ws",
    "https://YOUR-DOMAIN",
]
```

В production не следует использовать `allow_origins=["*"]`.

## Проверка API

```cmd
curl -X POST http://127.0.0.1:8000/api/bodhi/chat ^
-H "Content-Type: application/json" ^
-d "{\"message\":\"Хочу на Кайлас\"}"
```

## Тесты

```cmd
python -m pytest tests	est_bodhi_api.py
```

## Формат ошибок

API не должен отдавать пользователю traceback.

Рекомендуемый формат:

```json
{
  "answer": "Сейчас не удалось подготовить ответ.",
  "status": "error",
  "kind": "fallback"
}
```

## Production requirements

- HTTPS;
- ограниченный CORS;
- таймауты внешних запросов;
- журналирование;
- healthcheck;
- ограничение размера запроса;
- rate limiting;
- скрытие внутренних исключений;
- мониторинг ошибок.
