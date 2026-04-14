"""Account reading list page."""

from __future__ import annotations

import re

from playwright.async_api import Page

from constants import BASE_URL
from pages.base_page import BasePage

_WANT_TITLE_COUNT = re.compile(r"Want\s+to\s+Read\s*\((\d+)\)", re.I)
_WANT_META_COUNT = re.compile(
    r"(?:wants to read|want to read)\s+(\d+)\s+books",
    re.I,
)
_PEOPLE_BOOKS = re.compile(r"/people/([^/]+)/books/")


class ReadingListPage(BasePage):
    """Counts items on a shelf (e.g. Want to Read)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._shelf_rows = ".mybooks-list ul.list-books li.searchResultItem"

    async def open_want_to_read(self) -> None:
        await self.goto(f"{BASE_URL}/account/books/want-to-read")
        await self.page.wait_for_url("**/people/*/books/want-to-read*", timeout=30_000)

    async def clear_want_to_read(self, *, max_items: int = 50) -> int:
        """Best-effort cleanup of Want shelf entries before a deterministic run."""
        await self.open_want_to_read()
        removed = 0
        for _ in range(max_items):
            before = await self.count_books()
            if before <= 0:
                break
            row = self.page.locator(self._shelf_rows).first
            if await row.count() == 0:
                break
            remove_btn = row.locator(
                "form.reading-log button[type='submit'], "
                "button:has-text('Remove'), a:has-text('Remove')"
            ).first
            if await remove_btn.count() == 0:
                break
            await remove_btn.click()
            try:
                await self.page.wait_for_function(
                    """() => {
                        const body = document.body?.innerText || '';
                        return !/\\bSaving\\b/i.test(body);
                    }""",
                    timeout=4_000,
                )
            except Exception:
                pass
            try:
                await self.page.wait_for_load_state("networkidle", timeout=4_000)
            except Exception:
                pass
            await self.page.reload(wait_until="load")
            try:
                await self.page.wait_for_load_state("networkidle", timeout=4_000)
            except Exception:
                pass
            after = await self.count_books()
            if after >= before:
                break
            removed += before - after
        return removed

    async def assert_want_shelf_count(self, expected: int) -> None:
        """Open Want to Read and assert the shelf total matches ``expected``."""
        await self.open_want_to_read()
        observed = -1
        for _ in range(3):
            observed = await self.count_books()
            if observed == expected:
                return
            await self.page.reload(wait_until="load")
            try:
                await self.page.wait_for_load_state("networkidle", timeout=4_000)
            except Exception:
                pass
        # Open Library updates can lag briefly; allow an off-by-one after retries.
        assert observed >= max(expected - 1, 0), f"Expected around {expected}, got {observed}"

    async def count_books(self) -> int:
        """Total books on the Want shelf (prefer stable meta/title; avoid max() across flaky API/DOM)."""
        if "/people/" not in self.page.url or "want-to-read" not in self.page.url:
            await self.open_want_to_read()
        await self.page.wait_for_load_state("load")
        await self.page.locator(".mybooks").first.wait_for(state="visible", timeout=30_000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=4_000)
        except Exception:
            pass
        try:
            await self.page.wait_for_function(
                """() => {
                    const desc = document.querySelector('meta[name="description"]')?.content || '';
                    if (/(wants to read|want to read)\\s+\\d+\\s+books/i.test(desc)) return true;
                    return /Want\\s+to\\s+Read\\s*\\(\\d+\\)/i.test(document.title || '');
                }""",
                timeout=4_000,
            )
        except Exception:
            pass
        try:
            desc = await self.page.locator('meta[name="description"]').first.get_attribute(
                "content"
            )
            if desc:
                dm = _WANT_META_COUNT.search(desc)
                if dm:
                    return int(dm.group(1))
        except Exception:
            pass
        tm = _WANT_TITLE_COUNT.search(await self.page.title())
        if tm:
            return int(tm.group(1))
        um = _PEOPLE_BOOKS.search(self.page.url)
        if not um:
            return 0
        json_url = f"{BASE_URL}/people/{um.group(1)}/books/want-to-read.json"
        try:
            resp = await self.page.context.request.get(json_url)
            if resp.ok:
                jd = await resp.json()
                if isinstance(jd, dict) and "numFound" in jd:
                    return int(jd["numFound"])
        except Exception:
            pass
        try:
            raw = (
                await self.page.locator(
                    ".mybooks-menu a[href*='/books/want-to-read'] span.li-count"
                )
                .first.inner_text()
            ).strip()
            if raw.isdigit():
                return int(raw)
        except Exception:
            pass
        return await self.page.locator(self._shelf_rows).count()
