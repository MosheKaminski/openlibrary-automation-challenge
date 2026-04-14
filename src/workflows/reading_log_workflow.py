"""Add books to the reading log from URLs (orchestrates ``BookDetailPage``)."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from playwright.async_api import Page

from pages.book_detail_page import BookDetailPage
from shelf_add_stats import last_shelf_add_stats, reset_shelf_add_stats

logger = logging.getLogger(__name__)


class ReadingLogWorkflow:
    """Visits work URLs and updates shelves; tracks counts via :mod:`shelf_add_stats`."""

    _SCREENSHOT_DIR = Path("reports") / "screenshots"

    def __init__(self, page: Page) -> None:
        self._detail = BookDetailPage(page)

    async def add_urls(self, urls: list[str], *, random_shelves: bool = True) -> None:
        """For each URL: open book page, apply shelf action, save screenshot."""
        reset_shelf_add_stats()
        stats = last_shelf_add_stats()
        for url in urls:
            shot = self._SCREENSHOT_DIR / f"book_{uuid.uuid4().hex}.png"
            logger.info("Adding book from %s", url)
            await self._detail.goto(url)
            outcome = await self._detail.apply_reading_log_choice(
                random_shelves=random_shelves
            )
            if outcome == "want_to_read":
                stats.want_to_read += 1
            else:
                stats.already_read += 1
            logger.info("Shelf action: %s", outcome)
            await self._detail.save_screenshot(shot)
