"""Baseline BioSTEAM system builder using Excel-derived defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Mapping, MutableMapping, Optional

from .excel_defaults import ExcelModuleDefaults, ModuleKey, ModuleConfig
from .module_registry import ModuleRegistry, require_registered

# Default module sequence derived from the known baseline path.
DEFAULT_MODULE_SEQUENCE: List[ModuleKey] = [
    ModuleKey("USP00", "USP00a"),
    ModuleKey("USP01", "USP01a"),
    ModuleKey("USP02", "USP02a"),
    ModuleKey("DSP01", "DSP01a"),
    ModuleKey("DSP02", "DSP02a"),
    ModuleKey("DSP03", "DSP03a"),
    ModuleKey("DSP05", "DSP05a"),
    ModuleKey("PROJ00", "PROJ00c"),
    ModuleKey("PROJ01", "PROJ01a"),
    ModuleKey("PROJ02", "PROJ02a"),
]


@dataclass
class BaselineSystem:
    """Container for the assembled BioSTEAM objects."""

    units: MutableMapping[ModuleKey, object] = field(default_factory=dict)

    def add(self, key: ModuleKey, unit: object) -> None:
        self.units[key] = unit


def build_baseline_system(
    workbook_path: str,
    *,
    registry: ModuleRegistry,
    module_sequence: Optional[Iterable[ModuleKey]] = None,
    defaults_loader: Optional[ExcelModuleDefaults] = None,
) -> BaselineSystem:
    """Build the baseline BioSTEAM system from Excel defaults.

    Parameters
    ----------
    workbook_path:
        Path to the Excel workbook.
    registry:
        Module registry containing builder callables for the modules we plan to
        instantiate.
    module_sequence:
        Optional explicit sequence of module keys.  Defaults to
        ``DEFAULT_MODULE_SEQUENCE``.
    defaults_loader:
        Optional pre-constructed :class:`ExcelModuleDefaults` instance.  If
        omitted, one is created internally using *workbook_path*.
    """

    loader = defaults_loader or ExcelModuleDefaults(workbook_path)
    system = BaselineSystem()

    sequence = list(module_sequence or DEFAULT_MODULE_SEQUENCE)
    for key in sequence:
        config = loader.get_module_config(key)
        if config is None:
            continue  # Skip modules missing from the defaults table
        builder_entry = require_registered(registry, config)
        unit = builder_entry.build(config)
        system.add(key, unit)

    return system


__all__ = [
    "DEFAULT_MODULE_SEQUENCE",
    "BaselineSystem",
    "build_baseline_system",
]
