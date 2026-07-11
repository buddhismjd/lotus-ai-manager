# Semantic Engine 1.0

The Semantic Engine is the integration layer between:

- Aspect Registry
- Knowledge Graph
- future Product Graph Adapter
- future Tour Graph Adapter
- Answer Engine

## Processing pipeline

1. Parse the user question.
2. Detect semantic intent.
3. Resolve wording to a canonical graph entity ID.
4. Traverse typed graph relations.
5. Build a grounded response.

## Current supported intents

- describe entity
- find related objects
- find products
- find tours
- find practices

## Current limitations

Product and Tour nodes are not connected yet. The engine reports that no
related objects exist instead of inventing results.
