@echo off
chcp 65001 > nul
echo Lotus AI Manager setup v0.5
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn requests beautifulsoup4 lxml python-dotenv jinja2
echo Setup complete.
echo Optional AI: install Ollama and run: ollama pull qwen2.5:3b
pause
