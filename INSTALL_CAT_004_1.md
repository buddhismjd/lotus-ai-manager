# Установка CAT-004.1

1. Остановите сервер сочетанием `Ctrl+C`.
2. Распакуйте архив в корень `D:\Lotus-AI-Manager-v0.5` с заменой файлов.
3. Обновите каталог и фотографии:

```cmd
cd /d D:\Lotus-AI-Manager-v0.5
REFRESH_CATALOG_MEDIA.bat
```

4. Запустите профильную регрессию:

```cmd
python -m pytest tests\test_catalog_collection_builder.py tests\test_commercial_beta_tour_discovery.py tests\test_commercial_buttons_email_consent.py tests\test_noble_tone_email_followup.py tests\test_sales_conversation_strategy.py
```

5. Запустите полный набор:

```cmd
python -m pytest
```

6. Запустите бот:

```cmd
python -m uvicorn backend.main:app --reload
```

Откройте `http://127.0.0.1:8000/chat-ui`.
