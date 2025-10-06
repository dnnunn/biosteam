"""Export Excel vs BioSTEAM checkpoints for carbon-source overrides."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import biosteam as bst
import numpy as np

from migration.baseline_metrics import load_baseline_metrics
from migration.front_end import build_front_end_section


@dataclass
class Row:
    label: str
    excel: float | None
    biosteam: float | None

    @property
    def delta(self) -> float | None:
        if self.excel is None or self.biosteam is None:
            return None
        return float(self.biosteam - self.excel)

    @property
    def delta_pct(self) -> float | None:
        if self.excel in (None, 0) or self.biosteam is None:
            return None
        return float((self.biosteam - self.excel) / self.excel)

    def as_serializable(self) -> dict[str, float | str | None]:
        return {
            "label": self.label,
            "excel": _float_or_none(self.excel),
            "biosteam": _float_or_none(self.biosteam),
            "delta": _float_or_none(self.delta),
            "delta_pct": _float_or_none(self.delta_pct),
        }


@dataclass
class ScenarioRow:
    scenario: str
    section: str
    row: Row

    def to_csv(self) -> list[str]:
        return [
            self.scenario,
            self.section,
            self.row.label,
            _format_float(self.row.excel),
            _format_float(self.row.biosteam),
            _format_float(self.row.delta),
            _format_float(self.row.delta_pct),
        ]


def _float_or_none(value: object | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, np.floating):
        return float(value)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6g}"


def collect_mass_rows(section, metrics) -> list[Row]:
    spray_product = section.spray_dryer_unit.outs[0]
    try:
        dry_product_mass = float(spray_product.imass["Osteopontin"])
    except Exception:
        dry_product_mass = float(spray_product.F_mass)

    def _plan_value(unit, key: str) -> float | None:
        if unit is None or getattr(unit, "plan", None) is None:
            return None
        return _float_or_none(unit.plan.derived.get(key))

    rows = [
        Row("Final product", metrics.final_product_kg, dry_product_mass),
        Row(
            "Fermentation",
            metrics.mass_trail.get("product_preharvest_kg"),
            _plan_value(section.fermentation_unit, "product_out_kg"),
        ),
        Row(
            "Cell removal",
            metrics.mass_trail.get("product_after_microfiltration_kg"),
            _plan_value(section.microfiltration_unit, "product_out_kg"),
        ),
        Row(
            "UF/DF",
            metrics.mass_trail.get("product_after_ufdf_kg"),
            _plan_value(section.ufdf_unit, "product_out_kg"),
        ),
        Row(
            "Chromatography",
            metrics.mass_trail.get("product_after_chromatography_kg"),
            _plan_value(section.chromatography_unit, "product_out_kg"),
        ),
        Row(
            "Predry",
            metrics.mass_trail.get("product_after_predry_kg"),
            _plan_value(section.predrying_unit, "product_out_kg"),
        ),
    ]
    return rows


def collect_cost_rows(section, metrics) -> list[Row]:
    rows = [
        Row("Total cost per batch", metrics.total_cost_per_batch_usd, section.total_cost_per_batch_usd),
        Row("CMO fees per batch", metrics.cmo_fees_usd, section.cmo_fees_usd),
        Row(
            "Materials cost per batch",
            metrics.materials_cost_per_batch_usd,
            section.computed_material_cost_per_batch_usd,
        ),
        Row("Cost per kg", metrics.cost_per_kg_usd, section.cost_per_kg_usd),
    ]

    allocation = getattr(section, "allocation_result", None)
    if allocation is not None or any(
        value is not None
        for value in (
            metrics.cmo_per_unit_usd,
            metrics.resin_per_unit_usd,
            metrics.total_per_unit_usd,
        )
    ):
        rows.extend(
            [
                Row(
                    "CMO per unit",
                    metrics.cmo_per_unit_usd,
                    allocation.cmo_per_unit_usd if allocation else None,
                ),
                Row(
                    "Resin per unit",
                    metrics.resin_per_unit_usd,
                    allocation.resin_per_unit_usd if allocation else None,
                ),
                Row(
                    "Total per unit",
                    metrics.total_per_unit_usd,
                    allocation.total_per_unit_usd if allocation else None,
                ),
            ]
        )

    return rows


def collect_material_rows(section, metrics) -> list[Row]:
    breakdown = metrics.materials_cost_breakdown or {}
    rows: list[Row] = []
    for key in sorted(breakdown):
        rows.append(
            Row(
                key,
                breakdown.get(key),
                (section.material_cost_breakdown or {}).get(key),
            )
        )
    return rows


def run_scenario(
    *,
    workbook_path: Path,
    baseline_config: Path,
    config_path: Path,
) -> dict[str, list[Row]]:
    metrics = load_baseline_metrics(workbook_path=workbook_path, config_path=config_path)

    bst.main_flowsheet.clear()
    section = build_front_end_section(
        str(workbook_path),
        mode="baseline",
        baseline_config=baseline_config,
    )
    section.system.simulate()

    return {
        "mass_trail": collect_mass_rows(section, metrics),
        "cost_summary": collect_cost_rows(section, metrics),
        "materials_cost": collect_material_rows(section, metrics),
    }


def _default_overrides() -> dict[str, Path]:
    base = Path("migration/overrides")
    overrides = {}
    for path in sorted(base.glob("usp00_*.yaml")):
        overrides[path.stem] = path
    return overrides


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("BaselineModel.xlsx"),
        help="Excel workbook path (default: %(default)s)",
    )
    parser.add_argument(
        "--config-map",
        type=Path,
        default=Path("migration/baseline_metrics_map.yaml"),
        help="Metrics mapping YAML (default: %(default)s)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write JSON output to this path (default: stdout)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Optional CSV output path listing scenario/section rows",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent level (default: %(default)s)",
    )
    parser.add_argument(
        "--max-delta",
        type=float,
        help="Fail if absolute delta exceeds this value",
    )
    parser.add_argument(
        "--max-delta-pct",
        type=float,
        help="Fail if absolute relative delta exceeds this fraction (e.g., 0.05 for 5%)",
    )
    parser.add_argument(
        "overrides",
        nargs="*",
        type=Path,
        help="Explicit override YAML paths. Defaults to all usp00_* overrides.",
    )
    args = parser.parse_args(argv)

    if args.overrides:
        override_paths = {path.stem: path for path in args.overrides}
    else:
        override_paths = _default_overrides()

    results: dict[str, dict[str, list[dict[str, float | str | None]]]] = {}
    flat_rows: list[ScenarioRow] = []
    violations: list[str] = []
    for name, path in override_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Override not found: {path}")
        data = run_scenario(
            workbook_path=args.workbook,
            baseline_config=path,
            config_path=args.config_map,
        )
        results[name] = {
            section: [row.as_serializable() for row in rows]
            for section, rows in data.items()
        }
        for section, rows in data.items():
            for row in rows:
                scenario_row = ScenarioRow(name, section, row)
                flat_rows.append(scenario_row)
                if args.max_delta is not None:
                    delta = row.delta
                    if delta is not None and abs(delta) > args.max_delta:
                        violations.append(
                            f"{name}:{section}:{row.label} | Δ {delta:.4g} exceeds {args.max_delta}"
                        )
                if args.max_delta_pct is not None:
                    rel = row.delta_pct
                    if rel is not None and abs(rel) > args.max_delta_pct:
                        violations.append(
                            f"{name}:{section}:{row.label} | Δ% {rel:.4g} exceeds {args.max_delta_pct}"
                        )

    payload = json.dumps(results, indent=args.indent, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["scenario", "section", "label", "excel", "biosteam", "delta", "delta_pct"])
            for scenario_row in flat_rows:
                writer.writerow(scenario_row.to_csv())

    if violations:
        print("Validation failures:")
        for entry in violations:
            print(f"  - {entry}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
