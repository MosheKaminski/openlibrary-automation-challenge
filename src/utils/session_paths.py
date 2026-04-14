"""Resolve Playwright storage_state.json location for tests and tooling."""

from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_storage_state_path() -> Path | None:
    """First existing path: STORAGE_STATE_PATH env, else repo-root storage_state.json."""
    env = os.environ.get("STORAGE_STATE_PATH", "").strip()
    candidates = [Path(env)] if env else []
    candidates.append(_REPO_ROOT / "storage_state.json")
    for path in candidates:
        if path.is_file():
            return path
    return None
