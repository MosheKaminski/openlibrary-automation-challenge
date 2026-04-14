"""End-to-end: search (year filter) -> add to shelf -> verify Want to Read count."""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.session_paths import resolve_storage_state_path
from pages.reading_list_page import ReadingListPage
from flows import (
    add_books_to_reading_list,
    assert_reading_list_count,
    search_books_by_title_under_year,
)
from shelf_add_stats import last_shelf_add_stats
from utils.data_loader import load_data_file

_DATA = Path("data/test_data.yaml")


@pytest.mark.asyncio
async def test_search_add_books_verify_want_to_read_shelf(page) -> None:
    if resolve_storage_state_path() is None:
        pytest.skip(
            "No session file. Run: python scripts/save_storage_state.py "
            "(or set STORAGE_STATE_PATH to your JSON).",
        )

    data = load_data_file(_DATA)
    search_cfg = data["search"]
    query = str(search_cfg["query"])
    max_year = int(search_cfg["max_year"])
    limit = int(search_cfg.get("limit", 5))

    urls = await search_books_by_title_under_year(page, query, max_year, limit=limit)
    assert urls, "No URLs matched filters — check search/year selectors or data file."

    # Want-only keeps this test deterministic.
    await add_books_to_reading_list(page, urls, random_shelves=False)
    assert last_shelf_add_stats().want_to_read == len(urls)
    expected_visible = await ReadingListPage(page).count_books()
    await assert_reading_list_count(page, expected_count=expected_visible)
