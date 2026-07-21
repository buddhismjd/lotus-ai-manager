@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo AI Bodhi - refresh product catalog, images and profiles
echo ============================================================
python -m backend.integrations.product_catalog_synchronizer
if errorlevel 1 goto :error
python -m backend.integrations.catalog_intelligence_repository_sync
if errorlevel 1 goto :error
python -m tools.catalog_collection_report
if errorlevel 1 goto :error
echo.
echo Catalog media refresh completed successfully.
exit /b 0
:error
echo.
echo Catalog media refresh failed. Copy the complete log to the development chat.
exit /b 1
