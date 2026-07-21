# Аудит репозитория

Дата: 2026-07-12
Ветка: `feature/structured-catalog`

## Положительное

- хорошее разделение `backend`, `tests`, `tools`, `widget`, `docs`;
- широкий набор профильных тестов;
- отдельные модули графа, runtime graph и semantic adapter;
- есть `.env.example`, setup/run batch-файлы.

## Проблемы

### Корневой README устарел

Он описывает только маршрутизацию туров и не отражает текущую архитектуру.

### Главные архитектурные документы слишком короткие

`05_ARCHITECTURE.md`, `06_ROADMAP.md`, `07_CHANGELOG.md` не отражают
фактическое состояние.

### Документация дублируется

Нужен единый индекс и точка входа. Новый `docs/README.md` решает это.

### В Git виден `__pycache__`

Проверить:

```cmd
git ls-files | findstr /I "__pycache__ .pyc"
```

В `.gitignore` должны быть:

```text
__pycache__/
*.py[cod]
```

### Нет очевидного CI

Проверить:

```cmd
dir .github\workflows
```

Рекомендуется GitHub Actions для Python 3.12.

## Общая оценка

Кодовая база сильнее своей документации. Основные риски:

- дублирующиеся knowledge layers;
- устаревшие точки входа;
- Python cache в Git;
- отсутствие CI.
