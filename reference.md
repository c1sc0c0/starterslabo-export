# Rapport → CSV — reference

## Portal paths

| Item | Value |
|------|--------|
| Menu | **Rapport** |
| URL | `https://mijn.starterslabo.be/Views/report.aspx` |
| Outer iframe | `#frmSumatra` → `Portal/SumatraViewer.ashx?DefinitionID=…` |
| Inner frame | `Portal/WebClientForEmbedding/` (SilverEssence) |
| Tab links | `a.DStab` / active `a.DStabActive` |
| Excel export | `.DSExportExcel` (hidden until revealed; one per widget) |

The skill does **not** scrape HTML tables as the primary path. It triggers the same Excel control the portal handleiding describes, then converts `.xlsx` → CSV.

## CLI

```text
.venv/bin/python scripts/sync_rapport.py
  [--output DIR]          default: <skill-root>/rapport-export
  [--tabs k1,k2,…]        default: all (see SKILL.md)
  [--force]               overwrite existing CSV/XLSX/manifest.json
  [--keep-xlsx]           keep portal .xlsx next to CSV
  [--email EMAIL]         prefer STARTERSLABO_EMAIL env instead
  [--password PASS]       prefer STARTERSLABO_PASSWORD env instead
```

`HEADED=1` → visible Chromium.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `2` | Bad args / unknown tab / missing credentials |
| `3` | Output dir already has exports and `--force` was not set |

## Overwrite model

Intended periodic pattern:

1. Keep a **fixed** `--output` (default `rapport-export/`).
2. Version that folder with **git** if you want history (ideally a **private** data repo — not this public skill).
3. Re-run with `--force` to refresh files in place.

Without `--force`, any of these in the output directory blocks the run:

- `*.csv`
- `*.xlsx` (non-`_tmp_*`)
- `manifest.json`

## Typical CSV shapes

Portal widgets differ; first rows are often a title (`Details`) then a header row. Amounts use `.` as decimal in CSV (converted from Excel). Dates are `YYYY-MM-DD`.

### `verkopen.csv`

| Column | Notes |
|--------|--------|
| Factuurdatum | |
| Factuurbedrag | Incl. context from portal |
| Klant | |
| Boekstuknr | May be empty while *In behandeling* |
| Status | e.g. In behandeling |
| Type | e.g. Verkoopfactuur |
| Nog openstaand | |

### `aankopen.csv`

| Column | Notes |
|--------|--------|
| Factuurdatum | |
| Leverancier | |
| Factuurbedrag | |
| Type kosten | Ledger hint, e.g. `612125 - …` |
| Boekstuknr | |
| Status | |
| Te betalen a. leverancier | |
| Nog openstaand | |

### `resultatenrekening.csv`

Pivot-style P&L. Columns typically include:

`Jaar & maand`, `Omzet`, `Variabele kost (60-)`, `Brutowinst`, `Cumul Brutowinst`, `Werkingsbijdrage`, `Vaste kosten (61-)`, `Overige kosten (62- 65-)`, `Belasting VU`, `Verzekering`, `Resultaat`.

Indicative only (same caveats as the portal handleiding: not a full closing package).

### Historiek / relaties

`klantenhistoriek-*`, `leveranciershistoriek-*`, `grootboekhistoriek`, `klanten-leveranciers` vary by widget (tree/crosstab). Empty detail sheets can appear when no lines exist under a group. Treat filenames from `manifest.json` as authoritative for a given run.

## `manifest.json`

Written after each successful sync:

```json
{
  "synced_at": "ISO-8601 local",
  "output": "/absolute/path/to/rapport-export",
  "force": true,
  "tabs": [
    {
      "tab": "verkopen",
      "label": "Verkopen",
      "files": [
        {
          "csv": "verkopen.csv",
          "rows": 5,
          "title": "Details",
          "base": "verkopen",
          "export_index": 0,
          "overwritten": true
        }
      ]
    }
  ]
}
```

## Credentials

| Source | Priority |
|--------|----------|
| `--email` / `--password` | Highest (avoid; argv visible) |
| `scripts/.env` | Via python-dotenv |
| Skill-root `.env` | Via python-dotenv |
| Process environment | `STARTERSLABO_EMAIL`, `STARTERSLABO_PASSWORD` |

The password is never printed. Login failure leaves you on `login.aspx` and raises.

## Privacy checklist (before `git push`)

- [ ] `git status` shows **no** `scripts/.env`
- [ ] `git status` shows **no** `rapport-export/`
- [ ] `git status` shows **no** `*.csv` / real `*.xlsx`
- [ ] Only placeholders in `.env.example` (`you@example.com`, `your-password-here`)
- [ ] No screenshots of the logged-in portal in the commit

## Related portal docs

Portal FAQ / handleiding (after login): **Rapport** section — tables can be exported to Excel via the icon in the bottom-right of each table. This skill automates that control.
