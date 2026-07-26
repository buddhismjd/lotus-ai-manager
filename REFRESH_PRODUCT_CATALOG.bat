@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo AI BODHI - VERIFIED PRODUCT CATALOG SYNC FROM TILDA
echo ========================================================
python -m backend.integrations.product_catalog_synchronizer
if errorlevel 1 (
  echo.
  echo Product catalog synchronization failed.
  pause
  exit /b 1
)
echo.
echo Product catalog synchronized from published product pages.
pause
