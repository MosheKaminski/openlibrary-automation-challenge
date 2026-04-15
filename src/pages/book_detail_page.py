"""Work edition page: reading list actions."""

from __future__ import annotations

import random
import re

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from pages.base_page import BasePage

# Labels
_WANT_LABEL = "Want to Read"
_ALREADY_LABELS = ("Already Read", "Have read")

# Dropdown forms use hidden bookshelf_id (see ReadingLogForms.js / dropdown_content.html).
_BOOKSHELF_ID_BY_LABEL: dict[str, str] = {
    _WANT_LABEL: "1",
    "Currently Reading": "2",
    "Already Read": "3",
    "Have read": "3",
}


class BookDetailPage(BasePage):
    """Actions on a single book/work page (Want to Read / Already Read)."""

    _DROPPER = ".my-books-dropper"
    _DROPPER_DISABLED = ".generic-dropper--disabled"
    _DROPCLICK = ".generic-dropper__dropclick, .dropclick"
    _MENU = ".generic-dropper__dropdown"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    async def add_to_reading_list_random(self) -> str:
        """Pick Want to Read or Already Read at random; return which label was used."""
        choice = random.choice(["want", "already"])
        if choice == "want":
            await self._pick_shelf_status(_WANT_LABEL)
            return "want_to_read"
        await self._pick_already_read()
        return "already_read"

    async def add_want_to_read_only(self) -> None:
        """Always add (or keep) on the Want to Read shelf via the reading-log dropdown."""
        await self._pick_shelf_status(_WANT_LABEL)

    async def apply_reading_log_choice(self, *, random_shelves: bool) -> str:
        """Run one shelf interaction after navigation; returns ``want_to_read`` or ``already_read``."""
        if random_shelves:
            return await self.add_to_reading_list_random()
        await self.add_want_to_read_only()
        return "want_to_read"

    async def _pick_already_read(self) -> None:
        last_error: Exception | None = None
        for label in _ALREADY_LABELS:
            try:
                await self._pick_shelf_status(label)
                return
            except (PlaywrightTimeoutError, RuntimeError) as exc:
                last_error = exc
        if last_error:
            raise last_error
        raise RuntimeError("Could not select an Already Read option.")

    async def _pick_shelf_status(self, label: str) -> None:
        dropper = (
            self.page.locator(self._DROPPER)
            .filter(has_not=self.page.locator(self._DROPPER_DISABLED))
            .first
        )
        await dropper.wait_for(state="visible", timeout=20_000)
    
        loading = dropper.locator(".list-loading-indicator")
        if await loading.count() > 0:
            await loading.first.wait_for(state="hidden", timeout=45_000)
        else:
            await self.page.wait_for_load_state("networkidle", timeout=30_000)
        trigger = dropper.locator(self._DROPCLICK).first
        await trigger.wait_for(state="visible", timeout=10_000)
        # Opening via UI click is flaky (async webpack init + jQuery slideToggle). Mirror Dropper.toggleDropper.
        await dropper.evaluate(
            """el => {
                const $ = window.jQuery;
                if (!$) throw new Error('jQuery missing');
                const $e = $(el);
                $e.find('.generic-dropper__dropdown').show();
                $e.find('.arrow').addClass('up');
                el.classList.add('generic-dropper-wrapper--active');
            }"""
        )
        menu = dropper.locator(self._MENU).first
        shelf_id = _BOOKSHELF_ID_BY_LABEL.get(label)
        if shelf_id:
            form = menu.locator(
                f'form.reading-log:has(input[name="bookshelf_id"][value="{shelf_id}"])'
            ).first
            submit = form.locator("button[type=submit]")
            if await submit.count() > 0:
                async with self.page.expect_response(
                    lambda r: "bookshelves.json" in r.url
                    and r.request.method.upper() == "POST",
                    timeout=30_000,
                ) as resp_waiter:
                    # Hidden shelf buttons still have click handlers (preventDefault + fetch).
                    await submit.evaluate("b => b.click()")
                resp = await resp_waiter.value
                try:
                    payload = await resp.json()
                except Exception:
                    payload = {}
                if not resp.ok or (isinstance(payload, dict) and "error" in payload):
                    raise RuntimeError(
                        f"Reading log update failed: HTTP {resp.status} body={payload!r}"
                    )
                return
        pattern = re.compile(rf"^\s*{re.escape(label)}\s*$", re.I)
        btn = menu.get_by_role("button", name=pattern)
        if await btn.count() > 0:
            await expect(btn.first).to_be_visible(timeout=15_000)
            await btn.first.click()
            return
        link = menu.get_by_role("link", name=pattern)
        if await link.count() > 0:
            await expect(link.first).to_be_visible(timeout=15_000)
            await link.first.click()
            return
        raise RuntimeError(f"No control matched shelf label {label!r}")

    async def _click_want_to_read(self) -> None:
        await self._pick_shelf_status(_WANT_LABEL)

    async def _click_already_read(self) -> None:
        await self._pick_already_read()
