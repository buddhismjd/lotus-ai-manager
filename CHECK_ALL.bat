@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo AI Bodhi CATALOG-3.0.1 Health Check
echo ========================================

echo.
echo [1/4] Pytest
python -m pytest -q
if errorlevel 1 goto :failed

echo.
echo [2/4] Diagnostic
python tools\catalog_3_0\diagnostic.py
if errorlevel 1 goto :failed

echo.
echo [3/4] Smoke
python tools\catalog_3_0\smoke.py
if errorlevel 1 goto :failed

echo.
echo [4/4] Report
python tools\catalog_3_0\report.py
if errorlevel 1 goto :failed

echo.
echo ========================================
echo SYSTEM HEALTH: OK
echo ========================================
exit /b 0

:failed
echo.
echo ========================================
echo SYSTEM HEALTH: FAILED
if defined errorlevel echo Exit code: %errorlevel%
echo ========================================
exit /b 1
