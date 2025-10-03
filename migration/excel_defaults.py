"""Static loader for module defaults used by the migration front end.

The historical Excel-based migration relied on scraping the
``Inputs and Assumptions`` worksheet and associated dropdown metadata to obtain
module defaults.  To make the toolchain reproducible without the workbook, we
capture that information in ``module_defaults.yaml`` and expose the same helper
objects that the rest of the migration code expects.

This module now reads the YAML snapshot at import time and materialises
``ModuleConfig`` objects that mirror the original Excel-driven structures.
The public API is unchanged so downstream code can continue to call
``ExcelModuleDefaults`` even though the implementation no longer touches Excel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Mapping, MutableMapping, Optional, Tuple

import math
import yaml


@dataclass(frozen=True)
class ModuleKey:
    """Identifier for a module/option combination."""

    module: str
    option: Optional[str] = None

    def as_tuple(self) -> Tuple[str, Optional[str]]:
        return (self.module, self.option)


@dataclass
class ParameterRecord:
    """Container for a single parameter entry."""

    name: str
    value: Optional[float]
    unit: Optional[str] = None
    notes: Optional[str] = None
    source_row: Optional[int] = None


@dataclass
class ModuleConfig:
    """Collection of default parameters for a module/option pair."""

    key: ModuleKey
    parameters: Dict[str, ParameterRecord] = field(default_factory=dict)
    active: bool = False

    def add(self, record: ParameterRecord) -> None:
        self.parameters[record.name] = record

    def mark_active(self, is_active: bool) -> None:
        if is_active:
            self.active = True

    def __iter__(self) -> Iterator[ParameterRecord]:
        return iter(self.parameters.values())


class ExcelModuleDefaults:
    """Loader that hydrates module defaults from the static YAML snapshot."""

    def __init__(
        self,
        data_source: Path | str | None = None,
        *,
        workbook_path: Path | str | None = None,
    ) -> None:
        if data_source is None:
            data_source = Path(__file__).with_name("module_defaults.yaml")
        self.data_path = Path(data_source)
        # ``workbook_path`` is kept for backward compatibility with callers that
        # still pass an Excel path; the attribute now simply records the provided
        # path (or the YAML path when omitted).
        if workbook_path is not None:
            self.workbook_path = Path(workbook_path)
        else:
            self.workbook_path = self.data_path
        self._cache: Optional[Dict[ModuleKey, ModuleConfig]] = None

    def load_defaults(self) -> Mapping[ModuleKey, ModuleConfig]:
        """Load default parameter rows grouped by module.

        Returns
        -------
        Mapping[ModuleKey, ModuleConfig]
            Mapping from module keys to their default parameter collections.
        """

        if self._cache is not None:
            return self._cache

        if not self.data_path.exists():
            raise FileNotFoundError(f"Module defaults snapshot not found: {self.data_path}")

        with self.data_path.open("r", encoding="utf-8") as handle:
            raw_data = yaml.safe_load(handle) or {}

        grouped: MutableMapping[ModuleKey, ModuleConfig] = {}
        for module_name, options in raw_data.items():
            if not isinstance(options, Mapping):
                continue
            for option_key, payload in options.items():
                option = _normalize_option(option_key)
                key = ModuleKey(module=str(module_name), option=option)
                config = ModuleConfig(key=key)
                if isinstance(payload, Mapping):
                    config.mark_active(_coerce_bool(payload.get("active")))
                    parameters = payload.get("parameters", {})
                else:
                    parameters = {}

                if isinstance(parameters, Mapping):
                    for name, record in parameters.items():
                        if not isinstance(record, Mapping):
                            continue
                        value = _safe_numeric(record.get("value"))
                        unit = _normalize_str(record.get("unit"))
                        notes = _normalize_str(record.get("notes"))
                        source_row = _safe_int(record.get("source_row"))
                        config.add(
                            ParameterRecord(
                                name=str(name),
                                value=value,
                                unit=unit,
                                notes=notes,
                                source_row=source_row,
                            )
                        )

                grouped[key] = config

        self._cache = dict(grouped)
        return self._cache

    def get_module_config(
        self,
        key: ModuleKey,
        *,
        include_module_defaults: bool = True,
    ) -> Optional[ModuleConfig]:
        """Return the configuration for ``key`` with optional module-level merge."""

        defaults = self.load_defaults()
        specific = defaults.get(key)
        if not include_module_defaults or key.option is None:
            return specific

        base_key = ModuleKey(key.module, None)
        base_config = defaults.get(base_key)

        if specific is None and base_config is None:
            return None

        if base_config is None:
            return specific

        if specific is None:
            combined = ModuleConfig(key=key, active=base_config.active)
            for record in base_config:
                combined.add(record)
            return combined

        combined = ModuleConfig(
            key=key,
            active=specific.active or base_config.active,
        )
        for record in base_config:
            combined.add(record)
        for record in specific:
            combined.add(record)
        return combined

    def iter_module_keys(self, *, active_only: bool = False) -> Iterator[ModuleKey]:
        """Yield module keys, optionally filtering to active options."""

        for key, config in self.load_defaults().items():
            if active_only and not config.active:
                continue
            yield key

    def iter_defaults(self) -> Iterator[Tuple[ModuleKey, ParameterRecord]]:
        """Yield ``(ModuleKey, ParameterRecord)`` pairs for default rows."""

        for key, config in self.load_defaults().items():
            for record in config:
                yield key, record


def _normalize_option(option: Any) -> Optional[str]:
    if option in (None, "<default>"):
        return None
    return str(option)


def _normalize_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_numeric(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if not math.isnan(parsed) else None


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"true", "yes", "y", "1", "default"}
    return False


__all__ = [
    "ExcelModuleDefaults",
    "ModuleConfig",
    "ModuleKey",
    "ParameterRecord",
]
