"""
High-level flows required by the assignment.
Thin delegates to workflow classes (OOP) that compose page objects (POM).
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from playwright.async_api import Page, async_playwright

from pages.reading_list_page import ReadingListPage
from utils.session_paths import resolve_storage_state_path
from workflows.catalog_search_workflow import CatalogSearchWorkflow
from workflows.reading_log_workflow import ReadingLogWorkflow

T = TypeVar("T")


def _playwright_headless() -> bool:
    raw = os.getenv("PLAYWRIGHT_HEADLESS", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


async def _run_with_page(fn: Callable[[Page], Awaitable[T]]) -> T:
    """Create isolated browser/page for spec-facing flow functions."""
    state_path = resolve_storage_state_path()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=_playwright_headless())
        context_kwargs: dict[str, Any] = {}
        if state_path is not None:
            context_kwargs["storage_state"] = str(state_path)
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        try:
            return await fn(page)
        finally:
            await context.close()
            await browser.close()


async def search_books_by_title_under_year(
    query: str,
    max_year: int,
    limit: int = 5,
) -> list[str]:
    """Search by query, keep works with publish year <= max_year, collect up to ``limit`` URLs."""
    async def _impl(page: Page) -> list[str]:
        return await CatalogSearchWorkflow(page).collect_work_urls_under_max_year(
            query, max_year, limit
        )

    return await _run_with_page(_impl)


async def add_books_to_reading_list(
    urls: list[str],
    *,
    random_shelves: bool = False,
) -> None:
    """Visit each URL, add to reading log (Want-only by default), log and screenshot."""
    async def _impl(page: Page) -> None:
        await ReadingLogWorkflow(page).add_urls(urls, random_shelves=random_shelves)

    await _run_with_page(_impl)


async def assert_reading_list_count(
    expected_count: int,
    *,
    shelf: str = "want-to-read",
    include_already_read: bool = False,
) -> None:
    """Assert shelf count; can validate combined Want+Already when requested."""
    async def _impl(page: Page) -> None:
        shelf_page = ReadingListPage(page)
        if include_already_read:
            want = await shelf_page.count_books(shelf="want-to-read")
            already = await shelf_page.count_books(shelf="already-read")
            assert (want + already) == expected_count, (
                f"Expected total {expected_count}, got want={want}, already={already}"
            )
            return
        await shelf_page.assert_shelf_count(expected_count, shelf=shelf)

    await _run_with_page(_impl)


async def clear_reading_lists() -> int:
    """Best-effort cleanup for deterministic runs; returns removed Want entries."""
    async def _impl(page: Page) -> int:
        return await ReadingListPage(page).clear_want_to_read()

    return await _run_with_page(_impl)


async def clear_already_read_list() -> int:
    """Best-effort cleanup of Already Read shelf; returns removed entry count."""
    async def _impl(page: Page) -> int:
        return await ReadingListPage(page).clear_already_read()

    return await _run_with_page(_impl)


async def measure_page_performance(url: str, threshold_ms: int) -> dict:
    """Delegate to reporting module (single place for metrics + JSON schema)."""
    from reporting import performance as perf

    async def _impl(page: Page) -> dict:
        return await perf.measure_page_performance(page, url, threshold_ms)

    return await _run_with_page(_impl)
