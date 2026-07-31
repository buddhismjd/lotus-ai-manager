# ADR-0007: Decision Engine foundation

## Status

Accepted for CB-1.6A.

## Context

Commercial intent routing, catalogue search, cards, lead capture, and handoff
already exist in separate modules. Future recommendation and clarification
logic needs a stable coordination point, but moving current behaviour into a
large new service would create unnecessary regression risk.

## Decision

Introduce an independent `backend.decision` package with:

- immutable `DecisionContext` input;
- structured `DecisionResult` output;
- ordered `DecisionPolicy` extension point;
- deterministic `DecisionEngine` coordinator;
- passthrough fallback that preserves the current reply and cards.

CB-1.6A does not connect the engine to production request handling. Integration
will happen only after concrete policies are implemented and tested.

## Dependency rule

`backend.decision` must not import `sales_assistant`, catalogue, API, storage,
or widget modules. Existing orchestration layers may depend on `decision`, not
the reverse.

## Consequences

### Positive

- no production behaviour change in this stage;
- no circular dependency with existing commercial modules;
- policies can be added and tested independently;
- lead capture and escalation can later use the same result contract.

### Trade-offs

- one additional abstraction layer;
- production value appears in later policy/integration stages rather than in
  this foundation stage.
