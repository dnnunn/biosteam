"""Fallback parameter overrides for Excel modules.

Values are stored in ``default_overrides.yaml`` alongside this module. They
capture industry-standard assumptions for options that are not parameterized in
the Excel workbook but still appear in the module catalogue.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback when PyYAML missing
    yaml = None

from .excel_defaults import ModuleKey


_OVERRIDES_PATH = Path(__file__).with_name("default_overrides.yaml")
_CACHE: Dict[str, Dict[str, Dict[str, Any]]] | None = None


def load_default_overrides(path: Path | None = None) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Return the default override mapping (module → option → fields)."""

    global _CACHE
    target = path or _OVERRIDES_PATH
    if path is None and _CACHE is not None:
        return _CACHE

    if yaml is None or not target.exists():
        data = {}
    else:
        with target.open() as stream:
            data = yaml.safe_load(stream) or {}

    if path is None:
        _CACHE = data
    return data


def get_overrides_for(key: ModuleKey) -> Dict[str, Any]:
    """Return override entries for ``key`` (canonical field names)."""

    overrides = load_default_overrides()
    module_overrides = overrides.get(key.module, {})
    option_key = key.option or "<default>"
    entry = module_overrides.get(option_key)
    if entry is None:
        entry = module_overrides.get("defaults")
    return entry or {}


__all__ = [
    "load_default_overrides",
    "get_overrides_for",
]
