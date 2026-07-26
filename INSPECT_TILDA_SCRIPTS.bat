@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
  echo Usage:
  echo   INSPECT_TILDA_SCRIPTS.bat "https://svet-lotosa.tilda.ws/tproduct/..."
  exit /b 2
)

python -m tools.tilda_script_inspector "%~1"
set EXIT_CODE=%ERRORLEVEL%
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Tilda script inspection failed with exit code %EXIT_CODE%.
)
exit /b %EXIT_CODE%
