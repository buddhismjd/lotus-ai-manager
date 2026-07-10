@echo off
chcp 65001 > nul
call .venv\Scripts\activate.bat
echo ==========================================
echo TOUR SEARCH
echo ==========================================
python -m backend.rag.retriever "Есть тур в Индию?"
echo.
echo ==========================================
echo PRODUCT SEARCH
echo ==========================================
python -m backend.rag.retriever "Хочу купить статую"
echo.
echo ==========================================
echo PSYCHOLOGIST SEARCH
echo ==========================================
python -m backend.rag.retriever "Есть консультация психолога?"
echo.
pause
