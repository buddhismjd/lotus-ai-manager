@echo off
chcp 65001 > nul
call .venv\Scripts\activate.bat

echo ==========================================
echo TILDA PAGES API
echo ==========================================
python -m backend.integrations.tilda_sync
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo ==========================================
echo TILDA YML PRODUCT CATALOG
echo ==========================================
python -m backend.integrations.tilda_yml_sync
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo ==========================================
echo SQLITE KNOWLEDGE
echo ==========================================
python -m backend.rag.knowledge_builder
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo ==========================================
echo PRODUCT TEST
echo ==========================================
python -c "from backend.services.ai_service import chat; print(chat('Мне нужна ваджра')['answer'])"

echo.
pause
