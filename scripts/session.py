"""Browser session helpers for mijn.starterslabo.be."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Browser, Frame, Page, Playwright

LOGIN_URL = "https://mijn.starterslabo.be/login.aspx"
REPORT_URL = "https://mijn.starterslabo.be/Views/report.aspx"


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_credentials() -> tuple[str, str]:
    # Prefer scripts/.env, then skill-root .env, then process env / cwd.
    load_dotenv(_skill_root() / "scripts" / ".env")
    load_dotenv(_skill_root() / ".env")
    load_dotenv()
    email = os.environ.get("STARTERSLABO_EMAIL")
    password = os.environ.get("STARTERSLABO_PASSWORD")
    if not email or not password:
        print(
            "Missing STARTERSLABO_EMAIL or STARTERSLABO_PASSWORD. "
            "Copy scripts/.env.example to scripts/.env (or export the vars) "
            "and fill in your portal credentials.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return email, password


def is_headed() -> bool:
    return os.environ.get("HEADED", "").lower() in ("1", "true", "yes")


def new_page(playwright: Playwright) -> tuple[Browser, Page]:
    browser = playwright.chromium.launch(headless=not is_headed())
    context = browser.new_context(accept_downloads=True)
    return browser, context.new_page()


def login(page: Page, email: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.fill("#InputUsername", email)
    page.fill("#InputPassword", password)
    page.click("#BtnSubmit")
    page.wait_for_url(lambda url: "login.aspx" not in url.lower(), timeout=30_000)
    if "login.aspx" in page.url.lower():
        raise RuntimeError(f"Login failed; still on {page.url}")


def open_rapport(page: Page) -> None:
    """Open Rapport (SilverEssence viewer in nested iframes)."""
    page.goto(REPORT_URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_selector("iframe#frmSumatra", timeout=30_000)


def webclient_frame(page: Page, timeout_ms: int = 60_000) -> Frame:
    """Return the nested WebClientForEmbedding frame that hosts the report tabs."""
    page.wait_for_timeout(500)
    deadline = timeout_ms
    waited = 0
    while waited <= deadline:
        for frame in page.frames:
            if "WebClientForEmbedding" in (frame.url or ""):
                try:
                    text = frame.evaluate(
                        "() => (document.body && document.body.innerText) || ''"
                    )
                except Exception:
                    text = ""
                if "Verkopen" in text and "Aankopen" in text:
                    return frame
        page.wait_for_timeout(500)
        waited += 500
    raise TimeoutError(
        "Rapport WebClient iframe did not load "
        "(expected tabs Verkopen / Aankopen)."
    )
