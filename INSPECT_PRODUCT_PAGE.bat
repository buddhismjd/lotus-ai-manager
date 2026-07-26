@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo AI BODHI - PRODUCT PAGE INSPECTOR
echo ========================================================

if "%~1"=="" (
    set /p PRODUCT_URL=Paste published product URL: 
) else (
    set PRODUCT_URL=%~1
)

if "%PRODUCT_URL%"=="" (
    echo ERROR: Product URL is required.
    pause
    exit /b 1
)

python -m tools.product_page_inspector "%PRODUCT_URL%"
set EXIT_CODE=%ERRORLEVEL%

echo.
if not "%EXIT_CODE%"=="0" echo Inspector failed with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
