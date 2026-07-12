# SDM-1 — Guided Sales Dialogue

## Цель

Превратить ответ Sales Assistant в управляемый коммерческий диалог без изменения Knowledge Graph, Semantic Engine и каталогов.

## Архитектура

```text
Semantic Parser
    ↓
Semantic Engine
    ↓
Structured Catalog / Bodhi Service
    ↓
Sales Response Formatter
    ↓
Sales Dialogue Manager
    ↓
answer + next_action + suggestions + needs_manager
```

`SalesDialogueManager` не ищет факты и не изменяет ответ. Он выбирает следующий полезный шаг на основе уже определённой стратегии, темы разговора и полноты данных.

## Контракт

Ответ `/api/sales/chat` дополнен полями:

- `next_action` — типизированное основное действие;
- `suggestions` — варианты продолжения с `action`, `label` и `message`;
- `needs_manager` — необходимость участия человека.

Существующие поля API сохранены.

## Защита от галлюцинаций

Если цена тура отсутствует в структурированном каталоге, AI Bodhi прямо сообщает, что цена не опубликована, не придумывает значение и предлагает заявку или связь с менеджером.

## Граница этапа

SDM-1 не сохраняет контактные данные и не отправляет заявки. Эти операции относятся к следующему этапу Lead Capture.
