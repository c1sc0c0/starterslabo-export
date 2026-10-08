#!/usr/bin/env python3
"""Sync mijn.starterslabo.be Rapport tabs to CSV via the portal Excel export.

Logs in, opens Views/report.aspx (SilverEssence / Sumatra viewer), clicks each
requested tab, triggers the visible .DSExportExcel control(s), and converts the
downloaded .xlsx files to CSV.

Credentials: STARTERSLABO_EMAIL / STARTERSLABO_PASSWORD (env or scripts/.env).
Never logs the password.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook
from playwright.sync_api import Frame, Page, sync_playwright

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from session import (  # noqa: E402
    load_credentials,
    login,
    new_page,
    open_rapport,
    webclient_frame,
)

# Portal tab labels (exact visible text; &nbsp; normalized to space).
TABS: dict[str, str] = {
    "verkopen": "Verkopen",
    "aankopen": "Aankopen",
    "klantenhistoriek": "Klantenhistoriek",
    "leveranciershistoriek": "Leveranciershistoriek",
    "grootboekhistoriek": "Grootboekhistoriek",
    "resultatenrekening": "Resultatenrekening",
    "klanten-leveranciers": "Klanten & Leveranciers",
}

DEFAULT_TABS = (
    "verkopen",
    "aankopen",
    "klantenhistoriek",
    "leveranciershistoriek",
    "grootboekhistoriek",
    "resultatenrekening",
    "klanten-leveranciers",
)


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def slugify(value: str) -> str:
    value = value.lower().replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:80] or "sheet"


def normalize_tab_label(text: str) -> str:
    return (
        (text or "")
        .replace("\xa0", " ")
        .replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .strip()
    )


def click_tab(frame: Frame, label: str) -> None:
    want = normalize_tab_label(label)
    links = frame.locator("a.DStab")
    count = links.count()
    for i in range(count):
        got = normalize_tab_label(links.nth(i).inner_text())
        if got == want:
            links.nth(i).click()
            return
    raise RuntimeError(f"Rapport tab not found: {label!r}")


def wait_active_tab(frame: Frame, label: str, timeout_ms: int = 15_000) -> None:
    want = normalize_tab_label(label)
    waited = 0
    while waited <= timeout_ms:
        active = frame.evaluate(
            """() => {
              const a = document.querySelector('a.DStabActive');
              return a ? (a.textContent || '').replace(/\\u00a0/g, ' ').trim() : '';
            }"""
        )
        if normalize_tab_label(active) == want:
            frame.page.wait_for_timeout(800)
            return
        frame.page.wait_for_timeout(200)
        waited += 200
    raise TimeoutError(f"Tab did not become active: {label!r}")


def expand_toggles(frame: Frame) -> None:
    """Open collapsed crosstab groups (historiek / resultaten details)."""
    for _ in range(5):
        n = frame.evaluate(
            """() => {
              const els = [...document.querySelectorAll(
                '.DSctToggle:not(.DSctToggleOpen):not(.DSctToggleNone)'
              )];
              els.forEach((el) => el.click());
              return els.length;
            }"""
        )
        if not n:
            break
        frame.page.wait_for_timeout(400)


def visible_export_indexes(frame: Frame) -> list[int]:
    """Indexes of .DSExportExcel widgets that are currently laid out.

    The portal keeps the Excel icon at display:none until hover; reveal it first,
    then keep only controls with a real layout box (stale tabs stay 0×0).
    """
    return frame.evaluate(
        """() => {
          document.querySelectorAll('.DSExportExcel').forEach((el) => {
            el.style.display = 'block';
            el.style.opacity = '1';
          });
          return [...document.querySelectorAll('.DSExportExcel')]
            .map((el, i) => {
              const r = el.getBoundingClientRect();
              const parent = el.closest('[id^=FactoryContainer]');
              const pr = parent ? parent.getBoundingClientRect() : null;
              const parentOk = !!(pr && pr.width > 40 && pr.height > 40);
              return {i, w: r.width, h: r.height, parentOk};
            })
            .filter((x) => x.parentOk && x.w > 8 && x.h > 8)
            .map((x) => x.i);
        }"""
    )


def click_export(frame: Frame, index: int, page: Page, dest: Path) -> Path:
    """Show the Excel icon, click it, save the download to dest (.xlsx)."""
    with page.expect_download(timeout=30_000) as download_info:
        frame.evaluate(
            """(i) => {
              const el = document.querySelectorAll('.DSExportExcel')[i];
              if (!el) throw new Error('DSExportExcel missing at ' + i);
              el.style.display = 'block';
              el.style.opacity = '1';
              const r = el.getBoundingClientRect();
              const x = r.left + r.width / 2;
              const y = r.top + r.height / 2;
              for (const type of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
                el.dispatchEvent(new MouseEvent(type, {
                  bubbles: true, cancelable: true, view: window, clientX: x, clientY: y,
                }));
              }
            }""",
            index,
        )
    download = download_info.value
    dest.parent.mkdir(parents=True, exist_ok=True)
    download.save_as(dest)
    return dest


def cell_to_csv(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        # Keep portal-like decimal comma for Belgian tooling if needed?
        # Prefer machine-friendly dot for import into other software.
        return f"{value}"
    return str(value)


def xlsx_to_csv(xlsx_path: Path, csv_path: Path) -> dict:
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Workbook contains no default style",
            category=UserWarning,
        )
        wb = load_workbook(xlsx_path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    # Drop fully empty trailing columns/rows noise lightly
    while rows and all(c is None or str(c).strip() == "" for c in rows[-1]):
        rows.pop()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for row in rows:
            writer.writerow([cell_to_csv(c) for c in row])
    # Heuristic title from first non-empty header-ish row
    title = ""
    for row in rows[:3]:
        texts = [str(c).strip() for c in row if c is not None and str(c).strip()]
        if texts:
            title = texts[0]
            break
    return {
        "xlsx": str(xlsx_path.name),
        "csv": str(csv_path.name),
        "rows": len(rows),
        "title": title,
    }


def guess_suffix(xlsx_path: Path, index: int) -> str:
    """Name fragment from workbook content when a tab has multiple widgets."""
    try:
        import warnings

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Workbook contains no default style",
                category=UserWarning,
            )
            wb = load_workbook(xlsx_path, data_only=True)
        ws = wb[wb.sheetnames[0]]
        flat = " ".join(
            str(c).lower()
            for row in ws.iter_rows(max_row=3, values_only=True)
            for c in row
            if c is not None
        )
    except Exception:
        return f"widget-{index + 1}"
    if "omzet" in flat and "brutowinst" in flat:
        return "resultatenrekening"
    if "leverancier" in flat and "type kosten" in flat:
        return "aankopen"
    if "klant" in flat and "factuurbedrag" in flat:
        return "verkopen"
    if "btw-nummer" in flat or "btw nummer" in flat:
        return "relaties"
    if "rekening" in flat and "omschrijving" in flat:
        return "grootboek-or-details"
    if flat.startswith("details"):
        return "details"
    return f"widget-{index + 1}"


def existing_export_files(output_dir: Path) -> list[Path]:
    """CSV / XLSX / manifest already in the output dir (candidates to overwrite)."""
    if not output_dir.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(output_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith("_tmp_"):
            continue
        if path.suffix.lower() in {".csv", ".xlsx"} or path.name == "manifest.json":
            found.append(path)
    return found


def refuse_existing(output_dir: Path, existing: list[Path]) -> int:
    print(
        f"Refusing to overwrite {len(existing)} existing file(s) in {output_dir}.",
        file=sys.stderr,
    )
    for path in existing[:20]:
        print(f"  - {path.name}", file=sys.stderr)
    if len(existing) > 20:
        print(f"  … and {len(existing) - 20} more", file=sys.stderr)
    print(
        "Re-run with --force to overwrite in place "
        "(use git if you want history).",
        file=sys.stderr,
    )
    return 3


def sync_tabs(
    page: Page,
    tabs: list[str],
    output_dir: Path,
    keep_xlsx: bool,
    force: bool,
) -> list[dict]:
    open_rapport(page)
    frame = webclient_frame(page)
    results: list[dict] = []

    for key in tabs:
        label = TABS[key]
        print(f"Tab: {label}")
        click_tab(frame, label)
        wait_active_tab(frame, label)
        expand_toggles(frame)
        # Crosstab tabs (historiek / resultaten) need a beat to lay out export icons.
        page.wait_for_timeout(1500)

        indexes = visible_export_indexes(frame)
        if not indexes:
            print(f"  warning: no visible Excel export control on {label}", file=sys.stderr)
            results.append({"tab": key, "label": label, "files": [], "warning": "no-export"})
            continue

        files = []
        for n, idx in enumerate(indexes):
            tmp_xlsx = output_dir / f"_tmp_{key}_{n}.xlsx"
            click_export(frame, idx, page, tmp_xlsx)
            suffix = guess_suffix(tmp_xlsx, n)
            if len(indexes) == 1 or suffix == key:
                base = key
            else:
                base = f"{key}-{suffix}"
            if any(f.get("base") == base for f in files):
                base = f"{base}-{n + 1}"
            xlsx_path = output_dir / f"{base}.xlsx"
            csv_path = output_dir / f"{base}.csv"
            overwritten = csv_path.exists() or xlsx_path.exists()
            if overwritten and not force:
                # Should have been caught pre-flight; still refuse mid-run.
                tmp_xlsx.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Refusing to overwrite {csv_path.name} without --force"
                )
            if xlsx_path.exists():
                xlsx_path.unlink()
            tmp_xlsx.rename(xlsx_path)
            meta = xlsx_to_csv(xlsx_path, csv_path)
            meta["base"] = base
            meta["export_index"] = idx
            meta["overwritten"] = overwritten
            files.append(meta)
            flag = " (overwrote)" if overwritten else ""
            print(f"  → {csv_path.name} ({meta['rows']} rows){flag}")
            if not keep_xlsx:
                xlsx_path.unlink(missing_ok=True)
                meta.pop("xlsx", None)

        results.append({"tab": key, "label": label, "files": files})

    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sync Starters Labo Rapport tabs from the portal to CSV."
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: ./rapport-export under skill root)",
    )
    p.add_argument(
        "--tabs",
        default=",".join(DEFAULT_TABS),
        help=(
            "Comma-separated tab keys: "
            + ", ".join(TABS)
            + " (default: all)"
        ),
    )
    p.add_argument(
        "--keep-xlsx",
        action="store_true",
        help="Also keep the portal .xlsx downloads next to the CSVs",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite existing CSV/XLSX/manifest.json in the output directory. "
            "Needed for periodic sync into a fixed folder (git can version)."
        ),
    )
    p.add_argument(
        "--email",
        default=None,
        help="Portal username (else STARTERSLABO_EMAIL)",
    )
    p.add_argument(
        "--password",
        default=None,
        help="Portal password (else STARTERSLABO_PASSWORD)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.email:
        import os

        os.environ["STARTERSLABO_EMAIL"] = args.email
    if args.password:
        import os

        os.environ["STARTERSLABO_PASSWORD"] = args.password

    email, password = load_credentials()
    tab_keys = [t.strip().lower() for t in args.tabs.split(",") if t.strip()]
    unknown = [t for t in tab_keys if t not in TABS]
    if unknown:
        print(f"Unknown tab key(s): {', '.join(unknown)}", file=sys.stderr)
        print("Known:", ", ".join(TABS), file=sys.stderr)
        return 2

    output = args.output
    if output is None:
        # Stable folder for periodic overwrite-in-place (+ git for history).
        output = skill_root() / "rapport-export"
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    existing = existing_export_files(output)
    if existing and not args.force:
        return refuse_existing(output, existing)
    if existing and args.force:
        print(f"Overwriting {len(existing)} existing file(s) (--force):")
        for path in existing[:20]:
            print(f"  - {path.name}")
        if len(existing) > 20:
            print(f"  … and {len(existing) - 20} more")

    print(f"Output: {output}")
    with sync_playwright() as playwright:
        browser, page = new_page(playwright)
        try:
            login(page, email, password)
            print("Login OK")
            results = sync_tabs(
                page,
                tab_keys,
                output,
                keep_xlsx=args.keep_xlsx,
                force=args.force,
            )
        finally:
            browser.close()

    manifest = {
        "synced_at": datetime.now().isoformat(timespec="seconds"),
        "output": str(output),
        "force": bool(args.force),
        "tabs": results,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    n_csv = sum(len(t.get("files") or []) for t in results)
    n_ow = sum(
        1
        for t in results
        for f in (t.get("files") or [])
        if f.get("overwritten")
    )
    print(f"Done: {n_csv} CSV file(s) → {output}" + (f" ({n_ow} overwritten)" if n_ow else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
