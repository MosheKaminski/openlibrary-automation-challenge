from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from constants import BASE_URL
from pages.login_page import LoginPage


async def main() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env")
    email = os.environ.get("OL_EMAIL", "").strip()
    password = os.environ.get("OL_PASSWORD", "")
    if not email or not password:
        raise SystemExit("Set OL_EMAIL and OL_PASSWORD in the environment.")

    out = Path(os.environ.get("STORAGE_STATE_PATH", ROOT / "storage_state.json"))
    out.parent.mkdir(parents=True, exist_ok=True)

    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "1") not in {"0", "false", "False"}

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(BASE_URL)
        login = LoginPage(page)
        await login.login_with_email(email, password)
        await context.storage_state(path=str(out))
        await browser.close()

    raw = json.loads(out.read_text(encoding="utf-8"))
    out.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
