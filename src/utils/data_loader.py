"""Load test inputs from JSON, YAML, or CSV (data-driven layer)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


def _coerce_value(raw: str) -> Any:
    text = raw.strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.lower() in {"none", "null", ""}:
        return None
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _assign_dotted_key(target: dict[str, Any], dotted_key: str, value: Any) -> None:
    keys = [k.strip() for k in dotted_key.split(".") if k.strip()]
    if not keys:
        return
    cur = target
    for key in keys[:-1]:
        nxt = cur.get(key)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[key] = nxt
        cur = nxt
    cur[keys[-1]] = value


def _load_csv_mapping(text: str) -> dict[str, Any]:
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        return {}
    headers = {h.lower().strip() for h in rows[0].keys() if h}
    if not {"key", "value"}.issubset(headers):
        raise ValueError("CSV data file must have 'key,value' headers")
    data: dict[str, Any] = {}
    for row in rows:
        key = str(row.get("key", "")).strip()
        if not key:
            continue
        value = _coerce_value(str(row.get("value", "")))
        _assign_dotted_key(data, key, value)
    return data


def _validate_data_shape(data: dict[str, Any]) -> None:
    if "search" in data:
        search = data["search"]
        if not isinstance(search, dict):
            raise TypeError("'search' must be a mapping")
        for req in ("query", "max_year"):
            if req not in search:
                raise ValueError(f"Missing required key: search.{req}")


def load_data_file(path: Path) -> dict[str, Any]:
    """Load a supported config file based on suffix."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    elif suffix == ".csv":
        data = _load_csv_mapping(text)
    else:
        msg = f"Unsupported data file type: {suffix}"
        raise ValueError(msg)
    if not isinstance(data, dict):
        msg = "Root of data file must be a mapping"
        raise TypeError(msg)
    _validate_data_shape(data)
    return data
