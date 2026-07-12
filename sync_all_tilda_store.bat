@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo [1/4] Discovering Tilda store blocks...
python -m backend.integrations.tilda_store_discovery
if errorlevel 1 goto error

echo.
echo [2/4] Synchronizing all discovered products...
python -m backend.integrations.tilda_store_multi_sync
if errorlevel 1 goto error

echo.
echo [3/4] Building profiles for the full catalog...
python -m backend.integrations.catalog_intelligence_full_sync
if errorlevel 1 goto error

echo.
echo [4/4] Catalog health...
python -m tools.catalog_health
if errorlevel 1 goto error

echo.
echo Full catalog synchronization completed.
pause
exit /b 0

:error
echo.
echo Synchronization failed.
pause
exit /b 1
