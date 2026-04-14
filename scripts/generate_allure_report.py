#!/usr/bin/env python3
"""Build static Allure HTML from ``allure-results`` (needs Allure CLI or Node ``npx``)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_RESULTS = _REPO / "allure-results"
_OUTPUT = _REPO / "allure-report"


def _run(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, cwd=str(_REPO))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def main() -> int:
    if not _RESULTS.is_dir() or not any(_RESULTS.iterdir()):
        print(
            "No allure-results found. Run: python -m pytest tests",
            file=sys.stderr,
        )
        return 1

    if shutil.which("allure"):
        if _run(
            [
                "allure",
                "generate",
                str(_RESULTS),
                "-o",
                str(_OUTPUT),
                "--clean",
            ]
        ):
            print(f"Opened report folder: {_OUTPUT}")
            print(f"Open in browser: {_OUTPUT / 'index.html'}")
            return 0

    npx = shutil.which("npx")
    if npx:
        if _run(
            [
                npx,
                "--yes",
                "allure-commandline",
                "generate",
                str(_RESULTS),
                "-o",
                str(_OUTPUT),
                "--clean",
            ]
        ):
            print(f"Open in browser: {_OUTPUT / 'index.html'}")
            return 0

    print(
        "Could not build the HTML report. Allure needs a working JRE (Java 8+) on PATH "
        "or JAVA_HOME set, plus either the `allure` command "
        "(https://docs.qameta.io/allure/#_installing_a_commandline) "
        "or Node.js so `npx allure-commandline` can run.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
