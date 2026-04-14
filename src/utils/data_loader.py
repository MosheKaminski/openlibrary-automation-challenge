"""Load test inputs from JSON, YAML, or CSV (data-driven layer)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_data_file(path: Path) -> dict[str, Any]:
    """Load a supported config file based on suffix."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        msg = f"Unsupported data file type: {suffix}"
        raise ValueError(msg)
    if not isinstance(data, dict):
        msg = "Root of data file must be a mapping"
        raise TypeError(msg)
    return data
