"""Seed train configuration utilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional

__all__ = [
    "SeedMethod",
    "SeedConfig",
    "determine_seed_method",
]


class SeedMethod(str, Enum):
    AUTO = "Auto"
    SHAKE_FLASK = "ShakeFlaskOnly"
    TWO_STAGE = "TwoStage_Bioreactor"
    THREE_STAGE = "ThreeStage_Bioreactor"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "SeedMethod":
        if isinstance(value, cls):
            return value
        normalized = (value or cls.AUTO.value).strip().lower()
        for member in cls:
            if member.value.lower() == normalized:
                return member
        return cls.AUTO


@dataclass
class SeedConfig:
    method: SeedMethod = SeedMethod.AUTO

    @classmethod
    def from_mapping(cls, data: Mapping[str, object] | None) -> "SeedConfig":
        if not isinstance(data, Mapping):
            return cls()
        return cls(method=SeedMethod.from_string(data.get("method")))


def determine_seed_method(config: SeedConfig, production_volume_l: Optional[float]) -> SeedMethod:
    if config.method is not SeedMethod.AUTO:
        return config.method

    if production_volume_l is None:
        return SeedMethod.TWO_STAGE

    production_volume_m3 = production_volume_l / 1_000.0
    if production_volume_m3 >= 100.0:
        return SeedMethod.THREE_STAGE
    if production_volume_m3 <= 5.0:
        return SeedMethod.SHAKE_FLASK
    return SeedMethod.TWO_STAGE

