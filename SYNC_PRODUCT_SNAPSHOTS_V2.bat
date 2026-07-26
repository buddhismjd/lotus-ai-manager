@echo off
chcp 65001 >nul
echo ========================================================
echo AI BODHI - PRODUCT SNAPSHOT SYNCHRONIZER V2
echo ========================================================
python -m backend.integrations.product_snapshot_synchronizer_v2
set EXIT_CODE=%ERRORLEVEL%
echo.
if not "%EXIT_CODE%"=="0" (
  echo Synchronization failed.
  pause
  exit /b %EXIT_CODE%
)
echo Product snapshots synchronized from confirmed Tilda product objects.
pause
