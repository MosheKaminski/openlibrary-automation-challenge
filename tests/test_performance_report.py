"""Writes performance_report.json (assignment deliverable) after a sample navigation."""

from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest

from constants import BASE_URL
from flows import measure_page_performance
from reporting.performance import write_performance_report
from utils.data_loader import load_data_file


@pytest.mark.asyncio
async def test_performance_report_json_is_written() -> None:
    data = load_data_file(Path("data/test_data.yaml"))
    perf_points = data.get("performance_points")
    if not isinstance(perf_points, list) or not perf_points:
        perf_points = [
            {"name": "search", "url": f"{BASE_URL}/search?q=dune", "threshold_ms": 3000},
            {"name": "book", "url": f"{BASE_URL}/works/OL82563W", "threshold_ms": 2500},
            {
                "name": "reading-list",
                "url": f"{BASE_URL}/account/books/want-to-read",
                "threshold_ms": 2000,
            },
        ]

    rows = []
    for point in perf_points:
        name = str(point["name"])
        url = str(point["url"])
        threshold_ms = int(point["threshold_ms"])
        with allure.step(f"Measure performance for {name}"):
            row = await measure_page_performance(url, threshold_ms)
            row["name"] = name
            rows.append(row)
        allure.attach(
            json.dumps(rows, indent=2),
            name="performance_rows",
            attachment_type=allure.attachment_type.JSON,
        )
    out = Path("performance_report.json")
    with allure.step("Write performance report"):
        write_performance_report(rows, out)

    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "measurements" in payload
    assert len(payload["measurements"]) >= 3
    names = {m.get("name") for m in payload["measurements"]}
    assert {"search", "book", "reading-list"}.issubset(names)
    assert "runs" in payload
