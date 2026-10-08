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

**Never commit or print** `STARTERSLABO_PASSWORD`, `scripts/.env`, or `rapport-export/*.csv` (real customer/supplier data).

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
- [ ] 2. Sync: first run plain; later runs need --force if CSVs exist
- [ ] 3. Show user rapport-export/*.csv + mention overwrite / git history
- [ ] 4. Do not commit exports or .env to the public skill repo
```

### First sync

```bash
.venv/bin/python scripts/sync_rapport.py
```

Writes `rapport-export/` (stable path, gitignored).

### Periodic re-sync

If `rapport-export/` already has CSV/XLSX/`manifest.json`, the script **exits 3** unless:

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
| PII | Never commit `rapport-export/` or real CSVs to the public skill repo |

Details: [`reference.md`](reference.md).

## Scripts

| File | Role |
|------|------|
| `scripts/sync_rapport.py` | Login → Rapport → Excel export → CSV |
| `scripts/session.py` | Login + WebClient iframe helpers |

## Install this skill

```bash
git clone https://github.com/c1sc0c0/starterslabo-export.git .cursor/skills/starterslabo-export
git clone https://github.com/c1sc0c0/starterslabo-export.git ~/.cursor/skills/starterslabo-export
git clone https://github.com/c1sc0c0/starterslabo-export.git .claude/skills/starterslabo-export
git clone https://github.com/c1sc0c0/starterslabo-export.git ~/.claude/skills/starterslabo-export
```
