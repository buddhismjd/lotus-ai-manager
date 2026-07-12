# MVP-1.1 — Sales Response Formatter

## Цель

Преобразовать сырые тексты страниц Tilda в короткие ответы AI-менеджера.

## Архитектура

`SalesAssistant` не форматирует HTML самостоятельно. После `Bodhi Service` ответ проходит через отдельный `Sales Response Formatter`, который использует существующие `TourRepository` и `ProductRepository`.

## Правила

- меню сайта, CTA и маршрут по дням не выводятся в первом ответе;
- факты берутся из структурированных полей и исходного текста;
- неизвестные цена, дата или материал не придумываются;
- ответы не содержат сырой Markdown;
- исходная ссылка сохраняется;
- существующие Product/Tour Intelligence не дублируются.

## Поток

`Semantic Parser → Bodhi Service → Repository → Sales Response Formatter → SalesAssistant → API/UI`
