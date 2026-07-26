# UX-1.1 — Search and card quality

This stage fixes defects found during manual widget testing:

- product requests such as «Колокольчик имеется?» no longer fall through to tours;
- bell / ganta products are classified consistently by the router and catalog intelligence;
- Tilda navigation and footer lines are removed from tour card descriptions;
- tours without stored media receive a safe lazy image URL through `/api/sales/page-image`;
- the existing `/api/sales/product-image` endpoint remains backward compatible;
- a single tour returned by a country request is stored in dialogue context for follow-up questions.

Regression coverage is in `tests/test_ux_1_1_quality.py`.
