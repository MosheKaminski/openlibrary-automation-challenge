"""Shared page primitives: navigation, waits, screenshots."""

from __future__ import annotations

import logging
from pathlib import Path

from playwright.async_api import Page

from constants import DEFAULT_NAVIGATION_TIMEOUT_MS

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all page objects. Holds the Playwright Page and common helpers."""

    def __init__(self, page: Page) -> None:
        self._page = page

    @property
    def page(self) -> Page:
        return self._page

    async def goto(self, url: str, *, wait_until: str = "domcontentloaded") -> None:
        await self._page.goto(url, wait_until=wait_until, timeout=DEFAULT_NAVIGATION_TIMEOUT_MS)

    async def save_screenshot(self, path: Path, *, full_page: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        await self._page.screenshot(path=str(path), full_page=full_page)
        logger.info("Saved screenshot to %s", path)
