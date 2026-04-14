"""Performance metrics collection and JSON report output."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)


def _normalize_non_negative(value: Any, *, allow_nan: bool = False) -> float:
    """Return a non-negative float; keep NaN only when explicitly allowed."""
    num = float(value)
    if num != num:
        return num if allow_nan else 0.0
    if num < 0:
        return 0.0
    return num


async def measure_page_performance(page: Page, url: str, threshold_ms: int) -> dict[str, Any]:
    """
    Measure navigation timing. If any metric exceeds threshold_ms, log a warning only.
    Returns a dict suitable for merging into performance_report.json.
    """
    start = time.perf_counter()
    response = await page.goto(url, wait_until="load")
    load_time_ms = (time.perf_counter() - start) * 1000.0

    timing = await page.evaluate(
        """() => {
            const nav = performance.getEntriesByType('navigation')[0];
            if (nav) {
                return {
                    dom_content_loaded_ms: nav.domContentLoadedEventEnd,
                    load_event_ms: nav.loadEventEnd,
                    source: 'navigation-entry',
                };
            }
            // Legacy fallback for environments that do not expose Navigation Timing L2.
            const p = performance.timing;
            return {
                dom_content_loaded_ms: p.domContentLoadedEventEnd - p.navigationStart,
                load_event_ms: p.loadEventEnd - p.navigationStart,
                source: 'performance.timing',
            };
        }"""
    )

    # first_paint is not always in performance.timing; use Paint Timing if available
    first_paint_ms = await page.evaluate(
        """() => {
            const entries = performance.getEntriesByType('paint');
            const fp = entries.find(e => e.name === 'first-paint');
            return fp ? fp.startTime : null;
        }"""
    )

    first_paint_val = (
        _normalize_non_negative(first_paint_ms, allow_nan=True)
        if first_paint_ms is not None
        else float("nan")
    )
    dom_loaded = _normalize_non_negative(timing["dom_content_loaded_ms"])
    load_event_ms = _normalize_non_negative(timing["load_event_ms"])
    load_time_ms = _normalize_non_negative(load_time_ms)

    row: dict[str, Any] = {
        "url": url,
        "first_paint_ms": first_paint_val,
        "dom_content_loaded_ms": dom_loaded,
        "load_event_ms": load_event_ms,
        "timing_source": str(timing["source"]),
        "load_time_ms": load_time_ms,
        "threshold_ms": threshold_ms,
        "http_status": response.status if response else None,
    }

    for key in ("first_paint_ms", "dom_content_loaded_ms", "load_time_ms"):
        val = row[key]
        if isinstance(val, float) and val != val:  # NaN
            continue
        if val > threshold_ms:
            logger.warning("Performance threshold exceeded for %s: %s=%s (threshold=%s)", url, key, val, threshold_ms)

    return row


def write_performance_report(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    if output_path.is_file():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            maybe_runs = existing.get("runs", [])
            if isinstance(maybe_runs, list):
                history = maybe_runs
        except Exception:
            history = []
    run = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "measurements": rows,
    }
    history.append(run)
    payload = {
        "measurements": rows,
        "runs": history,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Wrote performance report to %s", output_path)
