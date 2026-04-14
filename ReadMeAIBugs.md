# Static analysis: buggy sample from the assignment

At least three concrete problems in the provided snippet:

## 1. Constructor name breaks initialization

`BookSearchPage` defines `_init_(self, page)` instead of `__init__`. Python only calls `__init__` automatically, so `self.page`, `self.search_input`, and related attributes are never set on instances. Any call to `search_page.search(...)` will fail with `AttributeError` before reaching Playwright.

## 2. Unsafe year parsing and fragile shelf filter

`year_text = await year_el.inner_text()` often contains more than a bare year (extra words, multiple dates, or edition notes). `int(year_text.strip())` raises `ValueError` on the first non-numeric token. Even when it works, the condition `if year < max_year` does not match the usual requirement “published in or before `max_year`” (typically `year <= max_year`). The buggy code excludes editions published exactly in `max_year`.

## 3. Missing null checks on links and pagination

`link = await item.query_selector("a")` can be `None`. Calling `await link.get_attribute("href")` then raises `AttributeError`. Pagination uses `next_btn = await page.query_selector(".next-page")` without verifying that this selector exists on Open Library’s current markup; if it is wrong, the loop stops early or never advances. There is also no explicit wait for navigation or results to stabilize after `click()`, which causes flaky timing.

## 4. Screenshots and paths (extra)

`path=f"screenshots/{url.replace('/', '_')}"` can exceed OS path limits, embed characters that are awkward on Windows, and does not create the parent directory. Failures appear as `FileNotFoundError` or invalid path errors rather than test assertion failures.

## 5. Assertion vs. random shelf choice (extra)

`add_books_to_reading_list` is specified to pick **Want to Read** or **Already Read** at random, but `assert_reading_list_count(page, len(urls))` assumes every book lands on the **Want to Read** shelf. Books marked “Already Read” will not be counted there, so the assertion fails even when behavior is correct.
