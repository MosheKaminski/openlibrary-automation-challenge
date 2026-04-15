"""Build static Allure HTML from ``reports/allure-results`` (needs Allure CLI or Node ``npx``)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from utils.report_paths import ALLURE_REPORT_DIR, ALLURE_RESULTS_DIR

_RESULTS = ALLURE_RESULTS_DIR
_OUTPUT = ALLURE_REPORT_DIR


def _run(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, cwd=str(_REPO))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def main() -> int:
    if not _RESULTS.is_dir() or not any(_RESULTS.iterdir()):
        print(
            "No reports/allure-results found. Run: python -m pytest tests",
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
            print(f"Report folder: {_OUTPUT}")
            print(f"Served best via HTTP, e.g.: cd {_OUTPUT} && python -m http.server 8080")
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
            print(f"Report folder: {_OUTPUT}")
            print(f"Served best via HTTP, e.g.: cd {_OUTPUT} && python -m http.server 8080")
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
