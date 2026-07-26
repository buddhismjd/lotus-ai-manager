@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo AI BODHI - VERIFY MULTI-SOURCE PRODUCT CATALOG
echo ========================================================
python -m tools.multi_source_catalog_diagnostics
set EXIT_CODE=%ERRORLEVEL%
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Multi-source catalog verification FAILED.
  pause
  exit /b %EXIT_CODE%
)
echo.
python -m tools.multi_source_catalog_report
echo.
echo Multi-source catalog verification PASSED.
pause
