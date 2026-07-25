@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m backend.sync
if errorlevel 1 (
  echo.
  echo Synchronization failed. See the error above.
  pause
  exit /b 1
)
echo.
echo Synchronization completed successfully.
pause
