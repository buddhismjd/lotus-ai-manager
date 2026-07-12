# AI Bodhi MVP Sales Assistant 1.0

The MVP adds a small stateful sales layer over the established Bodhi service.
It supports tours, products, the Buddhist-psychologist service and contacts.
Existing Product Intelligence, Tour Intelligence, Semantic Engine and Knowledge Graph remain unchanged.

## Safety

Unknown prices or facts are never invented. The response marks the request for manager follow-up.
Conversation state is isolated by `session_id` and stored only in process memory in MVP 1.0.

## API

`POST /api/sales/chat`

```json
{"message": "Хочу консультацию", "session_id": "browser-session"}
```

`POST /api/sales/reset` clears one session.
