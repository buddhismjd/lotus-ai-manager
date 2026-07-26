# CB-1.9.0 — Conversational Sales Engine

## Goal

Move AI Bodhi from a passive catalog search toward a concise commercial consultation flow without turning it into a general information assistant.

## Deterministic decision

Before product selection, `Conversation Decision Engine` chooses one of two actions:

1. show commercial results immediately;
2. ask one useful clarification question.

Specific product, aspect, category, country, and tour requests are never delayed by an unnecessary question.

## One-question contract

Broad requests currently covered by the contract:

- `Хочу подарок`;
- `Хочу что-нибудь домой`.

The original request is stored in the session state. The user's next message is joined with it and processed as one commercial query. The engine is explicitly told that a clarification has already been asked, so a second clarification question cannot be produced in that turn.

## Boundaries

- no free-form LLM-generated clarification questions;
- no practice or encyclopedic recommendations;
- no changes to the CB-1.7.0 card contract;
- no cross-session personalization.
