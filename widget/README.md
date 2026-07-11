# AI Бодхи — Widget MVP

Первая рабочая версия чат-виджета.

## Локальная проверка

1. Запустите backend:

```cmd
run.bat
```

2. Откройте `widget/demo.html` в браузере.

По умолчанию запросы отправляются на:

```text
http://127.0.0.1:8000/api/bodhi/chat
```

## Подключение к Tilda

Используйте файл:

```text
widget/tilda_embed.html
```

Замените:

- `https://YOUR-DOMAIN/widget/widget.css`
- `https://YOUR-DOMAIN/widget/widget.js`
- `https://YOUR-API-DOMAIN/api/bodhi/chat`

Затем вставьте код в блок T123.

## Важно для production

Backend должен:

- работать по HTTPS;
- разрешать CORS для домена сайта «Свет Лотоса»;
- быть доступен из интернета, а не только по `127.0.0.1`.

## Git

```cmd
git status
git add widget
git commit -m "Add AI Bodhi website widget MVP"
git push
```
