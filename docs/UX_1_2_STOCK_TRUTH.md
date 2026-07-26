# UX-1.2 — Truthful product availability

## Defect

A published product with no explicit stock status was displayed as **«В наличии»**.
The legacy `available` flag describes catalog publication, not physical inventory.

## Rule

- `В наличии` is shown only when `availability_status` explicitly equals `В наличии`.
- `Под заказ` and `Нет в наличии` are grouped as `Под заказ`.
- Missing status is grouped as `Наличие уточняется` and no invented status is printed on the card.
