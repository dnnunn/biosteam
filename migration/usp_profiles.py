"""Helpers to load predefined USP01/USP02 seed and fermentation profiles."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import yaml

PROFILE_FILES: Dict[str, str] = {
    "glucose_rich": "usp00_glucose_rich.yaml",
    "glucose_defined": "usp00_glucose_defined.yaml",
    "glycerol_rich": "usp00_glycerol_rich.yaml",
    "glycerol_defined": "usp00_glycerol_defined.yaml",
    "molasses_rich": "usp00_molasses_rich.yaml",
    "molasses_defined": "usp00_molasses_defined.yaml",
    "lactose_rich": "usp00_lactose_rich.yaml",
    "lactose_defined": "usp00_lactose_defined.yaml",
}

_OVERRIDES_DIR = Path(__file__).with_name("overrides")


@lru_cache(maxsize=None)
def load_seed_fermentation_profile(profile: str) -> Tuple[Dict[str, object], Dict[str, object]]:
    """Return (seed_override, fermentation_override) for the given profile name."""

    try:
        filename = PROFILE_FILES[profile]
    except KeyError as exc:
        raise KeyError(f"Unknown USP00 profile: {profile!r}") from exc

    path = _OVERRIDES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Profile override file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    seed = data.get("seed") or {}
    fermentation = data.get("fermentation") or {}
    return seed, fermentation


def available_profiles() -> Tuple[str, ...]:
    """Return the tuple of supported profile names."""

    return tuple(sorted(PROFILE_FILES.keys()))
