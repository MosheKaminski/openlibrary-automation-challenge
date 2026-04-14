"""Internet Archive / Open Library web login."""

from __future__ import annotations

import logging
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from constants import BASE_URL
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Fills the standard Open Library login form (IA email + password)."""

    LOGIN_PATH = "/account/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    async def login_with_email(self, email: str, password: str) -> None:
        login_url = f"{BASE_URL}{self.LOGIN_PATH}"
        await self.goto(login_url, wait_until="domcontentloaded")

        user = self.page.locator('input[name="username"]')
        pwd = self.page.locator('input[name="password"]')
        await user.wait_for(state="visible", timeout=20_000)
        await user.fill(email)
        await pwd.fill(password)

        form = self.page.locator("form").filter(has=pwd).first
        submit = form.locator('input[type="submit"], button[type="submit"]')

        async def _do_submit() -> None:
            if await submit.count() > 0:
                await submit.first.click()
            else:
                await self.page.get_by_role("button", name="Log In").click()

        try:
            async with self.page.expect_navigation(timeout=60_000):
                await _do_submit()
        except PlaywrightTimeoutError:
            await _do_submit()
            await self.page.wait_for_load_state("networkidle")

        try:
            await self.page.wait_for_function(
                """() => {
                    const isLoginUrl = /\\/account\\/login/.test(window.location.pathname || '');
                    const hasUserInput = !!document.querySelector('input[name="username"]');
                    return !(isLoginUrl && hasUserInput);
                }""",
                timeout=3_000,
            )
        except Exception:
            pass

        if await self._still_on_login_form():
            await self._raise_login_failed()

    async def _still_on_login_form(self) -> bool:
        url = self.page.url
        if "archive.org" in url and "/account/login" in url:
            return True
        if "openlibrary.org" in url and "/account/login" in url:
            return True
        return await self.page.locator('input[name="username"]').is_visible()

    async def _raise_login_failed(self) -> None:
        note = ""
        for sel in (".note", ".flash-message", '[role="alert"]', ".alert"):
            loc = self.page.locator(sel).first
            if await loc.count() > 0:
                try:
                    note = (await loc.inner_text()).strip()
                    if note:
                        break
                except Exception:  # noqa: BLE001
                    pass

        shot = Path("reports") / "login_failure.png"
        try:
            shot.parent.mkdir(parents=True, exist_ok=True)
            await self.page.screenshot(path=str(shot), full_page=True)
            logger.error("Saved login failure screenshot to %s", shot)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not save screenshot: %s", exc)

        logger.error("Login failed. url=%s note=%s", self.page.url, note or "(none)")
        msg = f"Login did not succeed (still on login). url={self.page.url}"
        if note:
            msg += f" page_note={note!r}"
        raise RuntimeError(msg)
