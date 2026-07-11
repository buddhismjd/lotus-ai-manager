# AI Bodhi Platform Architecture

AI Bodhi is organized into independent layers:

1. Registry layer — resolves user wording to canonical IDs.
2. Knowledge Graph — stores typed entities and relations.
3. Product Intelligence — structures catalog products.
4. Tour Intelligence — structures travel programs.
5. Answer Engine — builds grounded responses.
6. Recommendation Engine — suggests related objects.
7. Advisor Engine — audits product and tour content.

The Knowledge Graph is additive and does not replace existing modules yet.
Migration should happen in small, tested stages.
