"""Helpers to load BioSTEAM-baseline defaults for the migration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import yaml

DEFAULT_BASELINE_CONFIG = Path(__file__).with_name("baseline_defaults.yaml")


def load_baseline_defaults(path: Path | str | None = None) -> Mapping[str, Any]:
    """Return baseline plan/spec overrides from ``path`` (YAML)."""

    config_path = Path(path) if path else DEFAULT_BASELINE_CONFIG
    if not config_path.exists():
        raise FileNotFoundError(f"Baseline config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise TypeError("Baseline config must deserialize into a mapping")
    return data


__all__ = ["load_baseline_defaults", "DEFAULT_BASELINE_CONFIG"]
