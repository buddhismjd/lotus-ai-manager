# CB-0.9.13 — Rich Cards and Ranking

## Goal

Improve commercial collection responses without introducing a second search mechanism.
Existing semantic filtering remains responsible for inclusion; the new ranking layer only orders already relevant results.

## Changes

- Added deterministic collection ranking.
- Extended the shared collection-card contract with description, button label, group and item type.
- Product collections are grouped by availability.
- Tour cards use tour-specific labels and structured metadata.
- The dialogue wrapper preserves collection items.
- The widget renders group headings and rich cards.

## Safety constraints

- No unrelated recommendations are injected.
- Search and ranking remain separate responsibilities.
- Ranking is deterministic and does not use LLM-specific exceptions.
