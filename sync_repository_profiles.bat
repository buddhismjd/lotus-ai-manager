@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

python -m backend.integrations.catalog_intelligence_repository_sync
if errorlevel 1 goto error

python -m tools.catalog_health
if errorlevel 1 goto error

python -m tools.search_benchmark
if errorlevel 1 goto error

echo.
echo Repository profile synchronization completed.
pause
exit /b 0

:error
echo.
echo Synchronization failed.
pause
exit /b 1
