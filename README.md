# openlibrary-automation-challenge

End-to-end automation for [Open Library](https://openlibrary.org) using Python, Playwright (async), and a Page Object layout under `src/`.

## Setup

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Tests expect imports from `src` (`pytest.ini` sets `pythonpath = src`).

## Logged-in runs

Reading log actions require an Open Library session (Internet Archive email + password).

1. Set `OL_EMAIL` and `OL_PASSWORD` (do not commit real values).
2. Generate a storage file once:

   ```text
   set PYTHONPATH=src
   set OL_EMAIL=...
   set OL_PASSWORD=...
   python scripts/save_storage_state.py
   ```

3. Point tests at the file:

   ```text
   set STORAGE_STATE_PATH=storage_state.json
   ```

See `env.example` for variable names.

## Shelf assertions

`add_books_to_reading_list` is deterministic by default (`random_shelves=False`, Want shelf). If randomness is enabled, use `last_shelf_add_stats()` from `shelf_add_stats` and assert the **Want to Read** shelf count against `want_to_read`, not `len(urls)`.

## Architecture (OOP + POM)

The project uses a 3-layer OOP design: page objects in `src/pages/` handle UI interactions, workflows in `src/workflows/` orchestrate business scenarios, and `src/flows.py` exposes a thin stable API for tests. We chose this architecture to keep tests readable, reduce coupling to UI changes, and localize flaky-site handling (waits/fallbacks) in one place instead of spreading it across test files.

## Layout

- `src/pages/` — page objects (including `LoginPage`, `BookDetailPage`, search and shelf pages).
- `src/workflows/` — orchestration classes that compose page objects per use-case.
- `src/flows.py` — thin assignment-facing API functions.
- `src/reporting/performance.py` — timing helpers and JSON report writer.
- `data/` — external inputs (YAML/JSON/CSV via `DataLoader`).

## Assignment artifacts

- **Allure run report:** every `python -m pytest tests` writes raw results under `reports/allure-results/`. Build HTML with `python scripts/generate_allure_report.py` (needs a **JRE** plus [Allure CLI](https://docs.qameta.io/allure/#_installing_a_commandline) on `PATH`, or Node.js for `npx allure-commandline`). Serve `reports/allure-report/` over HTTP (e.g. `cd reports/allure-report` then `python -m http.server 8080`) — do not open `index.html` via `file://`. Quick view: `allure serve reports/allure-results` (same Java/CLI requirement).
- `performance_report.json` — produce via `write_performance_report` after collecting measurements.
- `ReadMeAIBugs.md` — static review of the intentionally buggy sample code from the brief.

## Limitations

- The target site is dynamic and occasionally inconsistent, so some shelf counts may settle with delay.
- Reading-list actions require a valid authenticated session (`storage_state.json`).
- Allure HTML generation requires Java and Allure CLI (or Node + `npx` path).
