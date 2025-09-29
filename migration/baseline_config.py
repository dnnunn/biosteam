"""Helpers to load BioSTEAM-baseline defaults for the migration."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml

DEFAULT_BASELINE_CONFIG = Path(__file__).with_name("baseline_defaults.yaml")


def _deep_update(base: Dict[str, Any], updates: Mapping[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, Mapping)
        ):
            base[key] = _deep_update(dict(base[key]), value)
        else:
            base[key] = value
    return base


def load_baseline_defaults(
    path: Path | str | None = None,
    *,
    merge_with: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Return baseline plan/spec overrides from ``path`` (YAML).

    Parameters
    ----------
    path:
        YAML file to load. Defaults to ``baseline_defaults.yaml`` next to this module.
    merge_with:
        Optional mapping to merge with. When provided, the loaded YAML entries
        overlay ``merge_with`` recursively, returning the merged dictionary.
    """

    config_path = Path(path) if path else DEFAULT_BASELINE_CONFIG
    if not config_path.exists():
        raise FileNotFoundError(f"Baseline config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise TypeError("Baseline config must deserialize into a mapping")
    if merge_with is None:
        return data
    merged = _deep_update(dict(deepcopy(merge_with)), data)
    return merged


__all__ = ["load_baseline_defaults", "DEFAULT_BASELINE_CONFIG"]
