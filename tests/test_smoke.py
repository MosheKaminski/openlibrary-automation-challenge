"""Smoke tests so pytest collects at least one item; extend with full E2E flows."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_open_library_home_loads(page) -> None:
    await page.goto("https://openlibrary.org", wait_until="domcontentloaded", timeout=30_000)
    title = await page.title()
    assert "Open Library" in title


def test_flow_helpers_are_importable() -> None:
    from flows import (  # noqa: PLC0415
        add_books_to_reading_list,
        assert_reading_list_count,
        measure_page_performance,
        search_books_by_title_under_year,
    )

    assert callable(search_books_by_title_under_year)
    assert callable(add_books_to_reading_list)
    assert callable(assert_reading_list_count)
    assert callable(measure_page_performance)
