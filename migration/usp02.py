"""Production fermentation configuration utilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional

__all__ = [
    "ProductionMethod",
    "ProductionConfig",
    "determine_production_method",
]


class ProductionMethod(str, Enum):
    AUTO = "Auto"
    BATCH = "Batch"
    FEDBATCH = "FedBatch"
    CONTINUOUS = "Continuous"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "ProductionMethod":
        if isinstance(value, cls):
            return value
        normalized = (value or cls.AUTO.value).strip().lower()
        for member in cls:
            if member.value.lower() == normalized:
                return member
        return cls.AUTO


@dataclass
class ProductionConfig:
    method: ProductionMethod = ProductionMethod.AUTO

    @classmethod
    def from_mapping(cls, data: Mapping[str, object] | None) -> "ProductionConfig":
        if not isinstance(data, Mapping):
            return cls()
        return cls(method=ProductionMethod.from_string(data.get("method")))


def determine_production_method(config: ProductionConfig, target_titer_g_per_l: Optional[float]) -> ProductionMethod:
    if config.method is not ProductionMethod.AUTO:
        return config.method

    if target_titer_g_per_l is None:
        return ProductionMethod.FEDBATCH

    if target_titer_g_per_l > 60.0:
        return ProductionMethod.CONTINUOUS
    if target_titer_g_per_l >= 15.0:
        return ProductionMethod.FEDBATCH
    return ProductionMethod.BATCH

