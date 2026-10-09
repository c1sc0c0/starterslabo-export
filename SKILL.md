---
name: starterslabo-export
description: >-
  Sync accounting Rapport tables from mijn.starterslabo.be to CSV (portal Excel
  export → CSV). Use when the user mentions Rapport export, boekhouding CSV,
  sync verkopen/aankopen/grootboek/resultatenrekening, or pulling Starters Labo
  accounting data into other software.
---

# Starters Labo — Rapport → CSV sync

Unofficial. Not affiliated with Starterslabo.

Pull **Rapport** tabs from [mijn.starterslabo.be](https://mijn.starterslabo.be) into UTF-8 CSV via the portal’s Excel export (SilverEssence viewer), then convert with openpyxl.

**Never commit or print** `STARTERSLABO_PASSWORD`, `scripts/.env`, or real export CSVs (customer/supplier data).

**Docs:** [docs/OVERVIEW.md](docs/OVERVIEW.md) (human pipeline) · [docs/PATHS.md](docs/PATHS.md) (where files land) · [reference.md](reference.md) (CLI / columns).

## Tabs

| Key | Portal |
|-----|--------|
| `verkopen` | Verkopen |
| `aankopen` | Aankopen |
| `klantenhistoriek` | Klantenhistoriek |
| `leveranciershistoriek` | Leveranciershistoriek |
| `grootboekhistoriek` | Grootboekhistoriek |
| `resultatenrekening` | Resultatenrekening |
| `klanten-leveranciers` | Klanten & Leveranciers |

Some tabs yield **multiple** CSVs (one per visible Excel widget).

Not a native Exact/Winbooks/Yuki export — spreadsheet dumps for custom import.

## Output directory (important)

Do **not** hardcode paths. Resolve with `scripts/paths.py`:

1. `--output DIR`
2. `STARTERSLABO_EXPORT_DIR`
3. `STARTERSLABO_DATA` / `starterslabo.yaml` (`export_dir`)
4. Legacy default: `<skill-root>/rapport-export/`

```bash
.venv/bin/python scripts/sync_rapport.py --print-paths
```

Copy [`starterslabo.yaml.example`](starterslabo.yaml.example) beside the user’s data root. Same config is shared with `starterslabo-beancount` (`books_dir`). Full rules: [docs/PATHS.md](docs/PATHS.md).

## Setup (first run)

From this skill’s clone root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/playwright install chromium
cp scripts/.env.example scripts/.env   # STARTERSLABO_EMAIL, STARTERSLABO_PASSWORD
```

## Workflow

```
Progress:
- [ ] 1. Credentials in scripts/.env or env vars (never print password)
- [ ] 2. Confirm output dir via --print-paths (yaml / env / default)
- [ ] 3. Sync: first run plain; later runs need --force if CSVs exist
- [ ] 4. Show user the CSV paths + mention overwrite / private git history
- [ ] 5. Do not commit exports or .env to the public skill repo
```

### First sync

```bash
.venv/bin/python scripts/sync_rapport.py
```

Writes the resolved `export_dir` (stable path; gitignore in the **data** repo).

### Periodic re-sync

If the output dir already has CSV/XLSX/`manifest.json`, the script **exits 3** unless:

```bash
.venv/bin/python scripts/sync_rapport.py --force
```

Overwrite in place; use **git** (private) for versioning if the user wants history.

### Subset

```bash
.venv/bin/python scripts/sync_rapport.py \
  --tabs verkopen,aankopen,resultatenrekening \
  --output ./my-export \
  --keep-xlsx
```

`HEADED=1` for a visible browser. Prefer env vars over `--password` (argv leakage).

## Safety

| Rule | Detail |
|------|--------|
| Portal | Read-only Excel download — no invoice create/edit |
| Local overwrite | Existing exports blocked without `--force` |
| Secrets | Never echo password; never commit `scripts/.env` |
| PII | Never commit real CSVs to the public skill repo |

## Scripts

| File | Role |
|------|------|
| `scripts/sync_rapport.py` | Login → Rapport → Excel export → CSV |
| `scripts/session.py` | Login + WebClient iframe helpers |
| `scripts/paths.py` | Shared export/books path resolver |

## Install this skill

```bash
git clone https://github.com/c1sc0c0/starterslabo-export.git .cursor/skills/starterslabo-export
git clone https://github.com/c1sc0c0/starterslabo-export.git ~/.cursor/skills/starterslabo-export
git clone https://github.com/c1sc0c0/starterslabo-export.git .claude/skills/starterslabo-export
git clone https://github.com/c1sc0c0/starterslabo-export.git ~/.claude/skills/starterslabo-export
```
