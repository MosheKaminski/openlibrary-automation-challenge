# Static analysis: buggy sample from the assignment

This document lists concrete bugs, why they are important, and a high-quality fix approach.

## 1. Constructor name breaks initialization (critical)

**Problem**  
`BookSearchPage` defines `_init_(self, page)` instead of `__init__`. Python only calls `__init__`, so page fields are never initialized and methods fail with `AttributeError`.

**Why it matters**  
The page object is unusable and every downstream flow fails immediately.

**Recommended fix**  
Rename to `__init__`, initialize all required locators there, and add a smoke test that instantiates the page object and calls a no-op method to catch constructor regressions.

## 2. Unsafe year parsing and wrong comparison boundary (major)

**Problem**  
`int(year_text.strip())` assumes pure numeric content, but Open Library labels often include extra text. It also uses `year < max_year` instead of `year <= max_year`.

**Why it matters**  
Can throw `ValueError` and silently exclude valid books from the expected year boundary.

**Recommended fix**  
Extract the first 4-digit year via regex, skip rows with no parseable year, and apply `<= max_year` for inclusive filtering. Add tests for mixed strings such as `"First published in 1999"` and `"1999, 2001"`.

## 3. Missing null checks and unstable pagination waits (major)

**Problem**  
`query_selector("a")` may return `None`; pagination selector may be absent or outdated; clicks do not wait for result stabilization.

**Why it matters**  
Causes intermittent `AttributeError`, early loop termination, or flaky behavior across runs.

**Recommended fix**  
Guard all optional elements, prefer resilient selectors (`get_by_role`/semantic locators), and wait with `wait_for_url`, `expect_response`, or a deterministic `wait_for_function` condition after pagination actions.

## 4. Screenshot path handling is unsafe (medium)

**Problem**  
Path generation from raw URL can produce invalid/too-long paths and parent folder may not exist.

**Why it matters**  
Test failures become filesystem errors instead of meaningful product assertions.

**Recommended fix**  
Use sanitized short names (e.g., UUID/hash), create parent directory explicitly, and centralize screenshot creation in `BasePage.save_screenshot`.

## 5. Assertion contradicts random shelf behavior (major)

**Problem**  
Flow randomly chooses **Want to Read** or **Already Read**, but assertion expects all books on Want shelf (`len(urls)`).

**Why it matters**  
Produces false failures even when the product behavior is correct.

**Recommended fix**  
Either make test runs deterministic (`random_shelves=False`) or assert against tracked per-shelf counters (`want_to_read`) rather than total URLs.
