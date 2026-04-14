"""Search catalog and collect work URLs (orchestrates ``SearchPage``)."""

from __future__ import annotations

from playwright.async_api import Page

from pages.search_page import SearchPage


class CatalogSearchWorkflow:
    """Application-level search flow; delegates UI to :class:`SearchPage`."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._search = SearchPage(page)

    async def collect_work_urls_under_max_year(
        self,
        query: str,
        max_year: int,
        limit: int = 5,
    ) -> list[str]:
        """Return up to ``limit`` work URLs with first publish year <= ``max_year``."""
        return await self._search.collect_work_urls_under_year(query, max_year, limit)
