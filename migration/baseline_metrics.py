"""Helpers to snapshot key KPIs from the Excel baseline for regression tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional

import json
import math

import pandas as pd
import yaml

__all__ = [
    "BaselineMetrics",
    "load_baseline_metrics",
    "export_baseline_metrics",
]


@dataclass(frozen=True)
class BaselineMetrics:
    """Container for the KPIs we care about for regression checks."""

    workbook_path: Path
    mass_trail: Mapping[str, float]
    final_product_kg: float
    cost_per_kg_usd: Optional[float] = None
    total_cost_per_batch_usd: Optional[float] = None
    cmo_fees_usd: Optional[float] = None
    materials_cost_per_batch_usd: Optional[float] = None
    materials_cost_breakdown: Mapping[str, float] = field(default_factory=dict)

    @property
    def product_per_batch_kg(self) -> float:
        return self.final_product_kg

    def as_dict(self) -> Dict[str, object]:
        return {
            "workbook": str(self.workbook_path),
            "mass_trail": dict(self.mass_trail),
            "final_product_kg": self.final_product_kg,
            "product_per_batch_kg": self.product_per_batch_kg,
            "cost_per_kg_usd": self.cost_per_kg_usd,
            "total_cost_per_batch_usd": self.total_cost_per_batch_usd,
            "cmo_fees_usd": self.cmo_fees_usd,
            "materials_cost_per_batch_usd": self.materials_cost_per_batch_usd,
            "materials_cost_breakdown": dict(self.materials_cost_breakdown),
        }


def export_baseline_metrics(
    *,
    workbook_path: Path | str = Path("BaselineModel.xlsx"),
    config_path: Path | str = Path("migration/baseline_metrics_map.yaml"),
    output_path: Path | str = Path("tests/opn/baseline_metrics.json"),
) -> BaselineMetrics:
    """Dump the baseline KPIs from ``workbook_path`` into ``output_path``."""

    metrics = load_baseline_metrics(workbook_path=workbook_path, config_path=config_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics.as_dict(), f, indent=2, sort_keys=True)
    return metrics


def load_baseline_metrics(
    *,
    workbook_path: Path | str,
    config_path: Path | str = Path("migration/baseline_metrics_map.yaml"),
) -> BaselineMetrics:
    """Read KPI values from the Excel baseline according to ``config_path``."""

    workbook_path = Path(workbook_path)
    if not workbook_path.exists():
        raise FileNotFoundError(f"Baseline workbook not found: {workbook_path}")

    config = _load_config(config_path)
    mass_trail = {}
    for name, cell in config["mass_trail"].items():
        value = _read_cell(workbook_path, cell)
        if value is None:
            raise ValueError(f"Failed to read mass-trail cell {cell!r} for {name}")
        mass_trail[name] = value

    final_product_cell = config["final_product"]["cell"]
    final_product = _read_cell(workbook_path, final_product_cell)
    if final_product is None:
        raise ValueError(
            f"Failed to read final product cell {final_product_cell!r}; update the map"
        )

    cost_per_kg_cell = config.get("cost_per_kg", {}).get("cell")
    cost_per_kg = _read_cell(workbook_path, cost_per_kg_cell) if cost_per_kg_cell else None

    total_cost_cell = config.get("total_cost_per_batch", {}).get("cell")
    total_cost_per_batch = (
        _read_cell(workbook_path, total_cost_cell) if total_cost_cell else None
    )

    cmo_fees_cell = config.get("cmo_fees", {}).get("cell")
    cmo_fees = _read_cell(workbook_path, cmo_fees_cell) if cmo_fees_cell else None

    material_breakdown: Dict[str, float] = {}
    for key, cell in config.get("materials_costs", {}).items():
        value = _read_cell(workbook_path, cell)
        if value is not None:
            material_breakdown[key] = value

    return BaselineMetrics(
        workbook_path=workbook_path,
        mass_trail=mass_trail,
        final_product_kg=final_product,
        cost_per_kg_usd=cost_per_kg,
        total_cost_per_batch_usd=total_cost_per_batch,
        cmo_fees_usd=cmo_fees,
        materials_cost_per_batch_usd=(
            total_cost_per_batch - cmo_fees
            if total_cost_per_batch is not None and cmo_fees is not None
            else None
        ),
        materials_cost_breakdown=material_breakdown,
    )


# ---------------------------------------------------------------------------
# Internal helpers


def _load_config(config_path: Path | str) -> Mapping[str, object]:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Baseline config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _validate_config(data)
    return data


def _validate_config(data: Mapping[str, object]) -> None:
    required_sections = {"mass_trail", "final_product"}
    missing = required_sections - data.keys()
    if missing:
        raise ValueError(f"Baseline config missing keys: {sorted(missing)}")


def _read_cell(workbook: Path, descriptor: Optional[str]) -> Optional[float]:
    if not descriptor:
        return None
    sheet, row, col = _parse_cell_descriptor(descriptor)
    try:
        df = pd.read_excel(
            workbook,
            sheet_name=sheet,
            header=None,
            skiprows=row,
            nrows=1,
            usecols=[col],
        )
    except Exception:
        return None
    try:
        raw = df.iloc[0, 0]
    except (IndexError, ValueError):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if math.isnan(value):
        return None
    return value


def _parse_cell_descriptor(descriptor: str) -> tuple[str, int, int]:
    """Parse strings like ``Calculations!B121`` into sheet / 0-based row/col."""

    if "!" not in descriptor:
        raise ValueError(f"Expected SHEET!CELL format, got {descriptor!r}")
    sheet, cell = descriptor.split("!", 1)
    cell = cell.strip().upper()
    col_letters = ""
    row_digits = ""
    for ch in cell:
        if ch.isalpha():
            col_letters += ch
        elif ch.isdigit():
            row_digits += ch
        else:
            raise ValueError(f"Unsupported character {ch!r} in cell {descriptor!r}")
    if not col_letters or not row_digits:
        raise ValueError(f"Invalid cell reference {descriptor!r}")
    col_index = _letters_to_index(col_letters)
    row_index = int(row_digits) - 1
    return sheet, row_index, col_index


def _letters_to_index(letters: str) -> int:
    total = 0
    for ch in letters:
        total = total * 26 + (ord(ch) - ord("A") + 1)
    return total - 1
