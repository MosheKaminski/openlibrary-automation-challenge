"""Writes performance_report.json (assignment deliverable) after a sample navigation."""

from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest

from reporting.performance import measure_page_performance, write_performance_report
from utils.data_loader import load_data_file


@pytest.mark.asyncio
async def test_performance_report_json_is_written(page) -> None:
    data = load_data_file(Path("data/test_data.yaml"))
    perf = data.get("performance", {})
    url = str(perf.get("sample_url", "https://openlibrary.org"))
    threshold_ms = int(perf.get("threshold_ms", 5000))

    with allure.step("Measure performance for sample URL"):
        row = await measure_page_performance(page, url, threshold_ms)
        allure.attach(
            json.dumps(row, indent=2),
            name="performance_row",
            attachment_type=allure.attachment_type.JSON,
        )
    out = Path("performance_report.json")
    with allure.step("Write performance report"):
        write_performance_report([row], out)

    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "measurements" in payload
    assert len(payload["measurements"]) >= 1
    assert payload["measurements"][-1]["url"] == url
    assert "runs" in payload
