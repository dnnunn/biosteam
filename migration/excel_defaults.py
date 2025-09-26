"""Lean ingestion layer for default module parameters from the Excel cost model.

This module focuses on the ``Inputs and Assumptions`` worksheet used during the
BetterDairy BioSTEAM migration.  It provides typed containers to capture default
parameter values keyed by (module, module option) pairs so downstream code can
construct BioSTEAM units with minimal coupling to the Excel format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, Mapping, MutableMapping, Optional, Tuple

import pandas as pd

# Column labels used in the Excel workbook.  They are kept as constants so that we
# fail fast if the workbook structure changes.
PARAMETER_COL = "Parameter Name"
VALUE_COL = "Value"
UNIT_COL = "Unit"
NOTES_COL = "Notes"
MODULE_COL = "Module"
MODULE_OPTION_COL = "Module_Option"
DEFAULT_COL = "Default"

DEFAULT_SHEET_NAME = "Inputs and Assumptions"
DEFAULT_HEADER_ROW = 4  # 0-based offset applied via pandas ``header`` argument


@dataclass(frozen=True)
class ModuleKey:
    """Identifier for a module/option combination in the Excel workbook."""

    module: str
    option: Optional[str] = None

    def as_tuple(self) -> Tuple[str, Optional[str]]:
        return (self.module, self.option)


@dataclass
class ParameterRecord:
    """Container for a single Excel parameter row."""

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
    """Parse default parameters from the Excel model.

    Parameters
    ----------
    workbook_path:
        Path to the Excel workbook (``.xlsx``).
    sheet_name:
        Worksheet containing the parameter table.  Defaults to
        ``"Inputs and Assumptions"``.
    header_row:
        Zero-based row index passed to :func:`pandas.read_excel` for the sheet's
        header.  The default (4) matches the current workbook layout where the
        first four rows contain titles and metadata.
    """

    def __init__(
        self,
        workbook_path: Path | str,
        sheet_name: str = DEFAULT_SHEET_NAME,
        option_sheet_name: str = "Dropdown_Lookup",
        header_row: int = DEFAULT_HEADER_ROW,
    ) -> None:
        self.workbook_path = Path(workbook_path)
        self.sheet_name = sheet_name
        self.option_sheet_name = option_sheet_name
        self.header_row = header_row
        self._cache: Optional[Dict[ModuleKey, ModuleConfig]] = None
        self._option_status_cache: Optional[Dict[ModuleKey, bool]] = None

    def load_defaults(self) -> Mapping[ModuleKey, ModuleConfig]:
        """Load default parameter rows grouped by module.

        Returns
        -------
        Mapping[ModuleKey, ModuleConfig]
            Mapping from module keys to their default parameter collections.
        """

        if self._cache is not None:
            return self._cache

        frame = self._read_sheet()
        frame = self._normalize_columns(frame)
        option_status = self._load_option_status()

        grouped: MutableMapping[ModuleKey, ModuleConfig] = {}
        for idx, row in frame.iterrows():
            module = row.get(MODULE_COL)
            option = row.get(MODULE_OPTION_COL)
            name = row.get(PARAMETER_COL)

            if (module, option) == ("Module", "Module_Option"):
                continue

            if not name or not isinstance(name, str):
                continue  # Skip unnamed rows

            key = ModuleKey(module=module or "GLOBAL", option=_normalize_str(option))
            config = grouped.setdefault(key, ModuleConfig(key=key))
            record = ParameterRecord(
                name=name,
                value=_safe_numeric(row.get(VALUE_COL)),
                unit=_normalize_str(row.get(UNIT_COL)),
                notes=_normalize_str(row.get(NOTES_COL)),
                source_row=idx + 1,  # Excel rows are 1-based
            )
            config.add(record)
            status_flag = option_status.get(key)
            if status_flag is None and key.option is not None:
                status_flag = option_status.get(ModuleKey(key.module, None))
            config.mark_active(status_flag if status_flag is not None else bool(row.get(DEFAULT_COL)))

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

    def _load_option_status(self) -> Dict[ModuleKey, bool]:
        if self._option_status_cache is not None:
            return self._option_status_cache

        try:
            frame = pd.read_excel(
                self.workbook_path,
                sheet_name=self.option_sheet_name,
                engine="openpyxl",
            )
        except ValueError:
            self._option_status_cache = {}
            return self._option_status_cache

        frame = frame.dropna(axis=0, how="all")
        status: Dict[ModuleKey, bool] = {}
        for _, row in frame.iterrows():
            module = _normalize_module(row.get(MODULE_COL))
            option = _normalize_str(row.get(MODULE_OPTION_COL))
            if (module, option) == ("Module", "Module_Option"):
                continue
            key = ModuleKey(module=module or "GLOBAL", option=option)
            status[key] = _coerce_bool(row.get(DEFAULT_COL))

        self._option_status_cache = status
        return self._option_status_cache

    def _read_sheet(self) -> pd.DataFrame:
        if not self.workbook_path.exists():
            raise FileNotFoundError(f"Workbook not found: {self.workbook_path}")

        frame = pd.read_excel(
            self.workbook_path,
            sheet_name=self.sheet_name,
            header=self.header_row,
            engine="openpyxl",
        )
        frame = frame.dropna(axis=0, how="all").dropna(axis=1, how="all")
        return frame

    def _normalize_columns(self, frame: pd.DataFrame) -> pd.DataFrame:
        missing = [col for col in [
            PARAMETER_COL,
            VALUE_COL,
            MODULE_COL,
            MODULE_OPTION_COL,
            DEFAULT_COL,
        ] if col not in frame.columns]
        if missing:
            raise KeyError(
                "Worksheet is missing expected columns: " + ", ".join(missing)
            )

        frame[DEFAULT_COL] = frame[DEFAULT_COL].apply(_coerce_bool)
        frame[MODULE_COL] = frame[MODULE_COL].apply(_normalize_module)
        frame[MODULE_OPTION_COL] = frame[MODULE_OPTION_COL].apply(_normalize_str)
        frame[PARAMETER_COL] = frame[PARAMETER_COL].apply(_normalize_parameter_name)
        return frame


def _coerce_bool(value: object) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, (bool, int)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"true", "yes", "y", "1", "default"}
    return False


def _normalize_module(value: object) -> str:
    if not value or (isinstance(value, float) and pd.isna(value)):
        return "GLOBAL"
    return str(value).strip()


def _normalize_str(value: object) -> Optional[str]:
    if not value or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _normalize_parameter_name(value: object) -> str:
    if not value or (isinstance(value, float) and pd.isna(value)):
        return "(unnamed parameter)"
    return str(value).strip()


def _safe_numeric(value: object) -> Optional[float]:
    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)
    return None
