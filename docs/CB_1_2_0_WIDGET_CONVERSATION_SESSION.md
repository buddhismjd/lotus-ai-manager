# CB-1.2.0 — Widget Conversation Session

Диалог посетителя хранится в существующих таблицах `dialogs` и `messages`.
Сериализованное состояние `DialogueState` сохраняется в `dialogs.state_json`.
Виджет восстанавливает историю через `GET /api/sales/session/{session_id}`.
Сброс закрывает активный диалог и не удаляет историю.
