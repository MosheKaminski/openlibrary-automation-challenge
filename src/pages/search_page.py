"""Search results: navigation, DOM + search.json collection (Page Object)."""

from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from playwright.async_api import Page

from constants import BASE_URL, DEFAULT_NAVIGATION_TIMEOUT_MS
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

_WORK_HREF = re.compile(r"/works/(OL\d+W)", re.I)
_FIRST_PUBLISHED = re.compile(
    r"(?:first\s+published\s+in|originally\s+published\s+in|published\s+in)\s*(\d{4})",
    re.I,
)
_YEAR_FALLBACK = re.compile(r"\b(19|20)\d{2}\b")


def _work_id(href: str) -> str | None:
    m = _WORK_HREF.search(href or "")
    return m.group(1) if m else None


def _absolute_url(href: str) -> str:
    base = href.split("#")[0]
    return base if base.startswith("http") else f"{BASE_URL}{base}"


class SearchPage(BasePage):
    """Catalog search: results listing, legacy + modern DOM, and search.json fallback."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_input = "input[name='q']"
        self.result_item = ".searchResultItem"

    async def open_home(self) -> None:
        await self.goto(BASE_URL)

    async def search(self, query: str) -> None:
        """
        Run a catalog search. Uses /search?q=... because the header UI often has no
        visible button[type='submit'] (icon / JS-only controls), which breaks click().
        """
        encoded = quote_plus(query)
        await self.goto(f"{BASE_URL}/search?q={encoded}")
        await self.page.wait_for_load_state("domcontentloaded")

    async def collect_work_urls_under_year(
        self,
        query: str,
        max_year: int,
        limit: int = 5,
    ) -> list[str]:
        """
        Search by query, keep works with publish year <= max_year, collect up to ``limit`` URLs.
        Paginates until enough matches or no next page.
        """
        await self.open_home()
        search_url = f"{BASE_URL}/search?q={quote_plus(query)}"
        await self.page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=DEFAULT_NAVIGATION_TIMEOUT_MS,
        )
        await self.page.wait_for_load_state("domcontentloaded")
        try:
            await self.page.get_by_text(re.compile(r"first published", re.I)).first.wait_for(
                timeout=20_000
            )
        except Exception:  # noqa: BLE001
            logger.warning("Timed out waiting for 'First published' snippet; continuing.")

        collected: list[str] = []
        seen_works: set[str] = set()

        while len(collected) < limit:
            await self.page.locator('a[href*="/works/OL"]').first.wait_for(timeout=25_000)

            used_search_json = False
            legacy = await self.page.query_selector_all(self.result_item)
            if legacy:
                for item in legacy:
                    if len(collected) >= limit:
                        break
                    year_text = (await item.inner_text()).strip()
                    match = _YEAR_FALLBACK.search(year_text)
                    if not match:
                        continue
                    year = int(match.group(0))
                    if year > max_year:
                        continue
                    link = await item.query_selector('a[href*="/works/OL"]')
                    if not link:
                        link = await item.query_selector("a[href]")
                    if not link:
                        continue
                    href = await link.get_attribute("href")
                    if not href:
                        continue
                    wid = _work_id(href)
                    if not wid or wid in seen_works:
                        continue
                    seen_works.add(wid)
                    collected.append(_absolute_url(href))

            if len(collected) < limit:
                await self._collect_modern_hits(max_year, limit, collected, seen_works)

            if len(collected) < limit:
                n_before = len(collected)
                logger.info(
                    "search.json fallback (same ranking as /search): need %s more (have %s).",
                    limit - len(collected),
                    len(collected),
                )
                await self._fill_from_search_json(
                    query, max_year, limit, seen_works, collected
                )
                if len(collected) > n_before:
                    used_search_json = True

            if used_search_json:
                break

            next_handle = await self.page.query_selector(
                "a.ChoosePage[data-ol-link-track='Pager|Next']"
            )
            if not next_handle:
                next_handle = await self.page.query_selector(
                    "a[title='Next'], a[aria-label='Next'], .pagination a:has-text('Next')"
                )
            if not next_handle:
                next_handle = await self.page.query_selector("a.next, .next-page")
            if next_handle and len(collected) < limit:
                await next_handle.click()
                await self.page.wait_for_load_state("domcontentloaded")
            else:
                break

        return collected[:limit]

    async def _collect_modern_hits(
        self,
        max_year: int,
        limit: int,
        collected: list[str],
        seen_works: set[str],
    ) -> None:
        """Parse current search results (non-legacy DOM) via work links + ancestor text."""
        links = self.page.locator("main").locator('a[href*="/works/OL"]')
        if await links.count() == 0:
            links = self.page.locator("[role='main']").locator('a[href*="/works/OL"]')
        if await links.count() == 0:
            links = self.page.locator("#content").locator('a[href*="/works/OL"]')
        if await links.count() == 0:
            links = self.page.locator('a[href*="/works/OL"]')
        total = await links.count()
        logger.info("Search results: %s work links in primary scope", total)
        for i in range(total):
            if len(collected) >= limit:
                break
            link = links.nth(i)
            href = await link.get_attribute("href")
            if not href:
                continue
            wid = _work_id(href)
            if not wid or wid in seen_works:
                continue
            card_text = await link.evaluate(
                """(a) => {
                    for (const sel of ['li', 'article', 'section', '[class*="card"]', '[class*="result"]']) {
                        const block = a.closest(sel);
                        if (block && block.innerText && block.innerText.length > 25) {
                            return block.innerText.substring(0, 2000);
                        }
                    }
                    let n = a, depth = 0;
                    while (n && depth++ < 10) {
                        n = n.parentElement;
                        if (n && n.innerText && n.innerText.length > 30) {
                            return n.innerText.substring(0, 2000);
                        }
                    }
                    return '';
                }"""
            )
            if not card_text.strip():
                continue
            pub = _FIRST_PUBLISHED.search(card_text)
            if pub:
                year = int(pub.group(1))
            else:
                y2 = _YEAR_FALLBACK.search(card_text)
                if not y2:
                    continue
                year = int(y2.group(0))
            if year > max_year:
                continue
            seen_works.add(wid)
            collected.append(_absolute_url(href))

    async def _fill_from_search_json(
        self,
        query: str,
        max_year: int,
        limit: int,
        seen_works: set[str],
        collected: list[str],
    ) -> None:
        """Same relevance order as the site search, using the public search.json API."""
        url = f"{BASE_URL}/search.json?q={quote_plus(query)}&limit=100"
        resp = await self.page.context.request.get(url)
        if not resp.ok:
            logger.error("search.json HTTP %s", resp.status)
            return
        data = await resp.json()
        for doc in data.get("docs", []):
            if len(collected) >= limit:
                break
            key = doc.get("key") or ""
            year = doc.get("first_publish_year")
            if not key.startswith("/works/") or year is None:
                continue
            if int(year) > max_year:
                continue
            wid = _work_id(key)
            if not wid or wid in seen_works:
                continue
            seen_works.add(wid)
            collected.append(BASE_URL + key)
