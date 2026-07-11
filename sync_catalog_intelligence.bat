@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m backend.integrations.catalog_intelligence_sync
pause
