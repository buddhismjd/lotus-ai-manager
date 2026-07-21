# CB-0.9.7 — Premium Product Experience

## Goal

Turn exact statue and thangka selections into complete commercial cards based on current Tilda catalog data.

## Product card contract

Every card renders:

- product photograph from Tilda;
- title;
- height;
- material;
- published availability status;
- **Открыть товар** button.

Unknown fields are never invented. If the source does not publish a status, the UI states that the status is being clarified.

## Data flow

Tilda Store API → product document metadata → Product repository → exact selection page.

After installing this stage, run the existing Tilda Store synchronization so image, material and status metadata are refreshed from the website.

## Artisan selection copy

> Мы также можем уточнить актуальное наличие у мастеров Тибета и Непала и прислать Вам персональную подборку.
