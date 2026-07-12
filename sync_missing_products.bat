@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m backend.integrations.sqlite_product_crawler_sync
pause
