# RDI-2 — Tilda Script Inspector

## Goal

Inspect inline JavaScript published on one Tilda product page without executing it and without modifying catalog data.

## Outputs

The tool saves:

- `script_inspection.txt` — readable structural report;
- `script_inspection.json` — machine-readable report;
- `scripts/script_XXX.js` — every inline script exactly as published.

## Safety

The inspector never evaluates JavaScript. It performs static extraction only:

- balanced object and array assignments;
- `storepartuid`, `recid`, and `productuid` values;
- API and product URLs;
- snippets around known Tilda and commercial tokens.

## Usage

```powershell
.\INSPECT_TILDA_SCRIPTS.bat "https://svet-lotosa.tilda.ws/tproduct/..."
```

Upload `script_inspection.txt` for architectural analysis. Raw scripts remain available locally if deeper inspection is required.
