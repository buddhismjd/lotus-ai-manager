@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

python -m backend.integrations.catalog_corrections
if errorlevel 1 goto error

python -m tools.search_benchmark
if errorlevel 1 goto error

echo.
echo Catalog corrections completed.
pause
exit /b 0

:error
echo.
echo Catalog corrections failed.
pause
exit /b 1
