# Starters Labo — Rapport → CSV

Unofficial [Cursor](https://cursor.com) / [Claude Code](https://code.claude.com) skill that syncs **Rapport** accounting tables from [mijn.starterslabo.be](https://mijn.starterslabo.be) to **UTF-8 CSV**.

It uses the same Excel export the portal documents (SilverEssence / Sumatra viewer inside **Rapport**), then converts each download to CSV so you can import or analyse the data elsewhere.

Not affiliated with Starterslabo. You need your own portal login. **Credentials and exported CSVs are never stored in this repo.**

## Install

Clone this repo **as the skill folder** (it must contain `SKILL.md` at the root):

```bash
# Cursor — this project
git clone https://github.com/c1sc0c0/starterslabo-export.git .cursor/skills/starterslabo-export

# Cursor — all projects
git clone https://github.com/c1sc0c0/starterslabo-export.git ~/.cursor/skills/starterslabo-export

# Claude Code — this project
git clone https://github.com/c1sc0c0/starterslabo-export.git .claude/skills/starterslabo-export

# Claude Code — all projects
git clone https://github.com/c1sc0c0/starterslabo-export.git ~/.claude/skills/starterslabo-export
```

Start a new agent chat so the skill is picked up.

**Claude.ai:** zip this folder (with `SKILL.md` at the zip root) and upload it as a custom skill.

## Setup (once)

```bash
cd /path/to/starterslabo-export
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/playwright install chromium
cp scripts/.env.example scripts/.env
```

Put your portal login in `scripts/.env` (gitignored) **or** export env vars:

```bash
export STARTERSLABO_EMAIL='you@example.com'
export STARTERSLABO_PASSWORD='your-password'
```

Prefer env vars / `.env` over CLI `--password` so the secret does not appear in shell history.

## Use

Tell the agent something like:

> Sync my Starters Labo Rapport accounting data to CSV.

Or run manually:

```bash
cd /path/to/starterslabo-export

# First pull → writes rapport-export/*.csv + manifest.json
.venv/bin/python scripts/sync_rapport.py

# Periodic refresh into the same folder (overwrite in place)
.venv/bin/python scripts/sync_rapport.py --force
```

### Overwrite safety

Default output is the **stable** folder `rapport-export/` (good for cron / agent re-runs).

| Situation | Behaviour |
|-----------|-----------|
| Folder empty / no prior CSVs | Sync writes files |
| Folder already has CSV, XLSX, or `manifest.json` | **Exit code 3** — refuses to overwrite |
| Same + `--force` | Overwrites in place |

Use **git** (locally or in a **private** data repo) if you want history of the CSVs. Do **not** commit real exports to this public skill repo.

### Subset / options

```bash
# Only sales + P&L
.venv/bin/python scripts/sync_rapport.py --tabs verkopen,resultatenrekening

# Custom output dir + keep portal Excel files
.venv/bin/python scripts/sync_rapport.py --output ./my-export --keep-xlsx

# Visible browser (debug)
HEADED=1 .venv/bin/python scripts/sync_rapport.py --tabs verkopen
```

### Tabs

| `--tabs` key | Portal tab |
|--------------|------------|
| `verkopen` | Verkopen |
| `aankopen` | Aankopen |
| `klantenhistoriek` | Klantenhistoriek |
| `leveranciershistoriek` | Leveranciershistoriek |
| `grootboekhistoriek` | Grootboekhistoriek |
| `resultatenrekening` | Resultatenrekening |
| `klanten-leveranciers` | Klanten & Leveranciers |

Default: all tabs. Some tabs expose more than one Excel widget (summary + details) → multiple CSVs.

See [`reference.md`](reference.md) for columns, architecture, and exit codes.

## What this is / isn’t

**Is:** a faithful dump of the portal Rapport Excel exports as CSV (UTF-8), suitable for spreadsheets or a custom import mapping.

**Isn’t:** a native Exact Online / Winbooks / Yuki / Octopus package, and it does not change invoices on the portal (read-only download).

## Privacy & security

This repository must stay free of real credentials and accounting data.

| Path | Status |
|------|--------|
| `scripts/.env.example` | Placeholder only (`you@example.com`) |
| `scripts/.env` | **Gitignored** — your real login |
| `rapport-export/` | **Gitignored** — real CSVs with customer/supplier data |
| `*.csv` / `*.xlsx` | **Gitignored** |

Before every push, confirm:

```bash
git status   # no .env, no rapport-export/, no *.csv
git grep -i 'password-here\|@gmail\|BE0' -- ':!LICENSE' || true
```

Never paste portal passwords or export CSVs into public issues/PRs.

## Related

- [starterslabo-skills](https://github.com/c1sc0c0/starterslabo-skills) — index of all skills  
- [starterlabo-invoices](https://github.com/c1sc0c0/starterlabo-invoices) — verkoopfactuur drafts  
- [starterslabo-expenses](https://github.com/c1sc0c0/starterslabo-expenses) — aankoopfactuur SL  
- [starterslabo-faq](https://github.com/c1sc0c0/starterslabo-faq) — crawl portal FAQ  

## License

MIT for this skill’s code and instructions. Starterslabo’s website and portal remain theirs.
