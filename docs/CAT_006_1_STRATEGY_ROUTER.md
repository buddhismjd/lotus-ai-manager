# CAT-006.1 — Strategy Router

The tour strategy now distinguishes a request for details from travel intent.

- Detail markers such as “расскажите” and “подробнее” select `tour_details`.
- Constrained travel intent such as “хочу на Кайлас” and “по местам Гуру Ринпоче возите?” selects `tour_list`.
- Exact availability wording such as “Есть тур на Кайлас?” remains compatible with the existing Bodhi response path.

Regression coverage is provided by the existing tests:

- `test_kailas_query_matches_destination_without_questionnaire`
- `test_guru_rinpoche_places_are_understood_as_tour_constraint`
