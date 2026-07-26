DATA-1.1 — точная привязка статуса к конкретному товару

Распакуйте содержимое архива в корень проекта с заменой файлов.
Затем выполните:

.venv\Scripts\activate.bat
python -m pytest -q
python tools\data_1_1_stock_source_diagnostics.py
python -m backend.integrations.product_snapshot_synchronizer_v2
REFRESH_PRODUCT_CATALOG.bat

После синхронизации полностью перезапустите сервер и откройте новый диалог.
