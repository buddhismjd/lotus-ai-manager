@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m backend.integrations.tilda_store_api
pause
