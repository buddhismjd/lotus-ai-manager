@echo off
setlocal
cd /d "%~dp0"

echo ========================================================================
echo AI BODHI CAT-003.1 - RAW SNAPSHOT SOURCE INTEGRITY
echo ========================================================================
python -m tools.raw_snapshot_integrity_diagnostics
if errorlevel 1 (
    echo.
    echo Integrity check finished with errors.
    pause
    exit /b 1
)

echo.
python -m tools.raw_snapshot_integrity_report
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Raw snapshot integrity inspection completed.
pause
endlocal
