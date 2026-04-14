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

`add_books_to_reading_list` picks **Want to Read** or **Already Read** at random. After a run, use `last_shelf_add_stats()` from `shelf_add_stats` and assert the **Want to Read** shelf count against `want_to_read`, not `len(urls)`.

## Layout

- `src/pages/` — page objects (including `LoginPage`, `BookDetailPage`, search and shelf pages).
- `src/flows.py` — assignment-facing flows.
- `src/reporting/performance.py` — timing helpers and JSON report writer.
- `data/` — external inputs (YAML/JSON).

## Assignment artifacts

- **Allure run report:** every `python -m pytest tests` writes raw results under `allure-results/`. Build HTML with `python scripts/generate_allure_report.py` (needs a **JRE** plus [Allure CLI](https://docs.qameta.io/allure/#_installing_a_commandline) on `PATH`, or Node.js for `npx allure-commandline`). Open `allure-report/index.html`. For a quick view without generating files: `allure serve allure-results` (same Java/CLI requirement).
- `performance_report.json` — produce via `write_performance_report` after collecting measurements.
- `ReadMeAIBugs.md` — static review of the intentionally buggy sample code from the brief.
