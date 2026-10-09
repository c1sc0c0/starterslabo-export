# How Rapport export works (human overview)

This skill downloads **accounting Rapport** tables from [mijn.starterslabo.be](https://mijn.starterslabo.be) and saves them as **UTF-8 CSV** flat files. A sister skill, [`starterslabo-beancount`](https://github.com/c1sc0c0/starterslabo-beancount), can turn those CSVs into a Beancount ledger.

Unofficial. Not affiliated with Starterslabo.

---

## Big picture

```text
You (or an agent)
        │
        ▼
starterslabo-export          ← this skill (Playwright + openpyxl)
        │  login, open Rapport, click Excel export per tab
        ▼
export/*.csv                 ← your chosen directory (see PATHS.md)
        │
        ├── spreadsheets / other software
        └── starterslabo-beancount → books/ → bean-query / Fava
```

The portal does **not** offer Exact/Winbooks packages here. We use the same **Excel** button the handleiding describes (SilverEssence viewer), then convert `.xlsx` → CSV.

---

## What you get

| Tab (portal) | Typical files |
|--------------|---------------|
| Verkopen | `verkopen.csv` |
| Aankopen | `aankopen.csv` |
| Resultatenrekening | `resultatenrekening.csv` (+ sometimes an extra widget) |
| Grootboekhistoriek | `grootboekhistoriek.csv` (often header-only on live portals) |
| Klanten / Leveranciers historiek | several `*-widget-*.csv` files |
| Klanten & Leveranciers | master list CSV |

A `manifest.json` lists what was written and when.

---

## Where files land

**Configurable** — do not assume `rapport-export/` forever.

| Mode | Where |
|------|--------|
| Zero config | `<this-skill>/rapport-export/` |
| Recommended | Directory from `starterslabo.yaml` / `STARTERSLABO_DATA` / `STARTERSLABO_EXPORT_DIR` |
| One-off | `--output /path/to/dir` |

Full rules: [PATHS.md](PATHS.md).

**Example (Nexus / private vault):** put CSVs under something like `…/nexus/starterslabo/export/` and point config there. Skills stay public; data stays private.

---

## Day-to-day

```bash
# Inspect paths
.venv/bin/python scripts/sync_rapport.py --print-paths

# First pull
.venv/bin/python scripts/sync_rapport.py

# Refresh (overwrite CSVs in place)
.venv/bin/python scripts/sync_rapport.py --force
```

Without `--force`, if the output folder already has CSV/XLSX/`manifest.json`, the script **exits 3** so agents cannot silently clobber data.

Credentials: `STARTERSLABO_EMAIL` + `STARTERSLABO_PASSWORD` (or `scripts/.env`). Never commit them.

---

## Safety model

| Layer | Behaviour |
|-------|-----------|
| Portal | Read-only Excel download — no invoice create/edit |
| Local | Existing exports blocked unless `--force` |
| Git | Real CSVs gitignored; keep history in a **private** data repo if you want versioning |
| Agents | Must not print passwords or paste customer rows into public issues |

---

## Next step: ledger

If you want double-entry books and LLM-friendly queries:

1. Keep exporting here into a stable `export/` folder.
2. Install [`starterslabo-beancount`](https://github.com/c1sc0c0/starterslabo-beancount).
3. Point both skills at the same data root ([PATHS.md](PATHS.md)).
4. Run `sync_books.py` → `bean-query`.

Pipeline narrative for that side: beancount skill `docs/OVERVIEW.md`.

---

## Docs map

| Audience | File |
|----------|------|
| Agents (short) | [`SKILL.md`](../SKILL.md) |
| Humans (install) | [`README.md`](../README.md) |
| Paths | [`PATHS.md`](PATHS.md) |
| Columns / CLI / architecture | [`reference.md`](../reference.md) |
