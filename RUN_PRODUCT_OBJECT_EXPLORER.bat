@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo AI BODHI - CAT-003 PRODUCT OBJECT EXPLORER
echo ========================================================
python -m tools.product_object_explorer_diagnostics
if errorlevel 1 (
  echo.
  echo Product Object Explorer failed.
  pause
  exit /b 1
)
echo.
python -m tools.product_object_explorer_report
if errorlevel 1 (
  pause
  exit /b 1
)
echo.
echo Product object artifacts created successfully.
pause
