"""Pytest fixtures: async Playwright page, logging, optional saved session."""

from __future__ import annotations

import logging
import os
import platform
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import Page, async_playwright

from utils.report_paths import ALLURE_RESULTS_DIR
from utils.session_paths import resolve_storage_state_path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

_REPO_ROOT = Path(__file__).resolve().parents[1]


def pytest_configure() -> None:
    if load_dotenv is not None:
        load_dotenv(_REPO_ROOT / ".env")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Append Allure environment metadata after result files are written."""
    out = ALLURE_RESULTS_DIR
    if not out.is_dir():
        return
    lines = [
        f"os_platform={platform.system()}",
        f"os_release={platform.release()}",
        f"python_version={sys.version.split()[0]}",
    ]
    (out / "environment.properties").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest_asyncio.fixture
async def page() -> Page:
    """One browser context per test; loads session from resolve_storage_state_path()."""
    state_path = resolve_storage_state_path()
    headless_raw = os.getenv("PLAYWRIGHT_HEADLESS", "true").strip().lower()
    headless = headless_raw not in {"0", "false", "no", "off"}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context_kwargs = {}
        if state_path is not None:
            context_kwargs["storage_state"] = str(state_path)
        context = await browser.new_context(**context_kwargs)
        pg = await context.new_page()
        yield pg
        await context.close()
        await browser.close()


@pytest.fixture(autouse=True)
def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
