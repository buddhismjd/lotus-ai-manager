AI Bodhi UX-1.2 — truthful product availability

Copy the folders backend, tests, tools and docs into the project root with replacement.

Checks:
  .venv\Scripts\activate.bat
  python -m pytest -q
  python tools\ux_1_2_stock_truth_diagnostics.py

Expected:
  327 passed
  UX-1.2 diagnostic: PASS
