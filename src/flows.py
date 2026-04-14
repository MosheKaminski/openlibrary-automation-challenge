"""
High-level flows required by the assignment.
Thin delegates to workflow classes (OOP) that compose page objects (POM).
"""

from __future__ import annotations

from playwright.async_api import Page

from pages.reading_list_page import ReadingListPage
from workflows.catalog_search_workflow import CatalogSearchWorkflow
from workflows.reading_log_workflow import ReadingLogWorkflow


async def search_books_by_title_under_year(
    page: Page,
    query: str,
    max_year: int,
    limit: int = 5,
) -> list[str]:
    """Search by query, keep works with publish year <= max_year, collect up to ``limit`` URLs."""
    return await CatalogSearchWorkflow(page).collect_work_urls_under_max_year(
        query, max_year, limit
    )


async def add_books_to_reading_list(
    page: Page,
    urls: list[str],
    *,
    random_shelves: bool = False,
) -> None:
    """Visit each URL, add to reading log (Want-only by default), log and screenshot."""
    await ReadingLogWorkflow(page).add_urls(urls, random_shelves=random_shelves)


async def assert_reading_list_count(
    page: Page,
    expected_count: int,
    *,
    shelf: str = "want-to-read",
) -> None:
    """Open selected shelf and assert visible book count."""
    await ReadingListPage(page).assert_shelf_count(expected_count, shelf=shelf)


async def clear_reading_lists(page: Page) -> int:
    """Best-effort cleanup for deterministic runs; returns removed Want entries."""
    return await ReadingListPage(page).clear_want_to_read()


async def measure_page_performance(page: Page, url: str, threshold_ms: int) -> dict:
    """Delegate to reporting module (single place for metrics + JSON schema)."""
    from reporting import performance as perf

    return await perf.measure_page_performance(page, url, threshold_ms)
