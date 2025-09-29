"""Compare BioSTEAM front-end outputs against Excel baseline checkpoints."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping

import biosteam as bst
import numpy as np

from migration.baseline_metrics import load_baseline_metrics
from migration.front_end import build_front_end_section


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("BaselineModel.xlsx"),
        help="Path to the Excel baseline workbook (default: %(default)s)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("migration/baseline_metrics_map.yaml"),
        help="Cell mapping config (default: %(default)s)",
    )
    parser.add_argument(
        "--mode",
        choices=["excel", "baseline"],
        default="excel",
        help="Data source mode: Excel parity or BioSTEAM baseline (default: %(default)s)",
    )
    parser.add_argument(
        "--baseline-config",
        type=Path,
        help="Path to baseline YAML overrides (defaults to migration/baseline_defaults.yaml)",
    )
    parser.add_argument(
        "--detailed",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include plan/spec values and stream compositions (default: on)",
    )
    parser.add_argument(
        "--component-threshold",
        type=float,
        default=1e-6,
        help="Skip component lines below this mass [kg] when printing streams",
    )
    return parser.parse_args()


def _sorted_items(mapping: Mapping[str, object]) -> Iterable[tuple[str, object]]:
    return sorted(mapping.items(), key=lambda item: item[0])


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _print_plan_details(unit: bst.Unit) -> None:
    plan = getattr(unit, "plan", None)
    if plan is None:
        print("  Plan data unavailable for this unit")
        return

    print("  Plan-derived targets:")
    if plan.derived:
        for key, value in _sorted_items(plan.derived):
            print(f"    {key}: {_format_value(value)}")
    else:
        print("    <none>")

    specs = getattr(plan, "specs", None)
    print("  Plan specs:")
    if specs is None:
        print("    <none>")
    else:
        for key, value in _sorted_items(
            {k: v for k, v in vars(specs).items() if k != "key"}
        ):
            print(f"    {key}: {_format_value(value)}")


def _collect_stream_components(stream: bst.Stream, min_mass: float) -> Mapping[str, float]:
    data = defaultdict(float)
    # Access sparse vector directly to avoid triggering alias lookups repeatedly.
    for index, mass in stream.imass.data.dct.items():
        value = float(mass)
        if abs(value) < min_mass:
            continue
        component = stream.chemicals.IDs[index]
        data[component] += value
    return dict(sorted(data.items(), key=lambda item: (-abs(item[1]), item[0])))


def _print_stream(summary: str, stream: bst.Stream, *, min_mass: float) -> None:
    print(f"    {summary}: F_mass={stream.F_mass:.6g} kg")
    components = _collect_stream_components(stream, min_mass)
    if not components:
        print("      <no components above threshold>")
        return
    for name, mass in components.items():
        print(f"      {name}: {mass:.6g} kg")


def _print_unit_details(
    title: str,
    unit: bst.Unit,
    *,
    component_threshold: float,
) -> None:
    print(f"\n=== {title} ({unit.ID}) ===")
    _print_plan_details(unit)
    print("  Streams:")
    for idx, stream in enumerate(unit.ins, start=1):
        _print_stream(f"in{idx}", stream, min_mass=component_threshold)
    for idx, stream in enumerate(unit.outs, start=1):
        _print_stream(f"out{idx}", stream, min_mass=component_threshold)


def main() -> None:
    args = parse_args()
    metrics = load_baseline_metrics(workbook_path=args.workbook, config_path=args.config)

    bst.main_flowsheet.clear()
    section = build_front_end_section(
        str(args.workbook),
        mode=args.mode,
        baseline_config=args.baseline_config,
    )
    section.system.simulate()

    spray_product = section.spray_dryer_unit.outs[0]
    try:
        dry_product_mass = float(spray_product.imass['Osteopontin'])
    except (KeyError, TypeError):
        dry_product_mass = spray_product.F_mass

    checkpoints = [
        ("Final product", dry_product_mass, metrics.final_product_kg),
        (
            "Fermentation",
            section.fermentation_unit.plan.derived.get("product_out_kg"),
            metrics.mass_trail["product_preharvest_kg"],
        ),
        (
            "Cell removal",
            section.microfiltration_unit.plan.derived.get("product_out_kg"),
            metrics.mass_trail["product_after_microfiltration_kg"],
        ),
        (
            "UF/DF",
            section.ufdf_unit.plan.derived.get("product_out_kg"),
            metrics.mass_trail["product_after_ufdf_kg"],
        ),
        (
            "Chromatography",
            section.chromatography_unit.plan.derived.get("product_out_kg"),
            metrics.mass_trail["product_after_chromatography_kg"],
        ),
        (
            "Predry",
            section.predrying_unit.plan.derived.get("product_out_kg"),
            metrics.mass_trail["product_after_predry_kg"],
        ),
    ]

    print(f"Excel baseline: {metrics.workbook_path}")
    print("\nMass trail comparison (kg):")
    print(f"{'Stage':20} {'Excel':>12} {'BioSTEAM':>12} {'Δ':>12} {'Δ%':>8}")
    for stage, observed, expected in checkpoints:
        if expected is None or observed is None:
            delta = rel = np.nan
        else:
            delta = observed - expected
            rel = delta / expected if expected else np.nan
        print(
            f"{stage:20} {expected:12.3f} {observed:12.3f} "
            f"{delta:12.3f} {rel:8.2%}"
        )

    print("\nCost summary (USD):")
    cost_rows = [
        (
            "Total cost per batch",
            metrics.total_cost_per_batch_usd,
            section.total_cost_per_batch_usd,
        ),
        ("CMO fees per batch", metrics.cmo_fees_usd, section.cmo_fees_usd),
        (
            "Materials cost per batch",
            metrics.materials_cost_per_batch_usd,
            section.computed_material_cost_per_batch_usd,
        ),
        ("Cost per kg", metrics.cost_per_kg_usd, section.cost_per_kg_usd),
    ]

    print(f"{'Metric':25} {'Excel':>15} {'BioSTEAM':>15} {'Δ':>15} {'Δ%':>8}")
    for label, excel_value, biosteam_value in cost_rows:
        if excel_value is None or biosteam_value is None:
            delta = rel = np.nan
        else:
            delta = biosteam_value - excel_value
            rel = delta / excel_value if excel_value else np.nan
        excel_str = f"${excel_value:,.2f}" if excel_value is not None else "N/A"
        bs_str = f"${biosteam_value:,.2f}" if biosteam_value is not None else "N/A"
        delta_str = f"${delta:,.2f}" if not np.isnan(delta) else "N/A"
        rel_str = f"{rel:.2%}" if not np.isnan(rel) else "N/A"
        print(f"{label:25} {excel_str:>15} {bs_str:>15} {delta_str:>15} {rel_str:>8}")

    if metrics.materials_cost_breakdown:
        print("\nMaterials cost breakdown (USD):")
        print(f"{'Component':25} {'Excel':>15} {'BioSTEAM':>15} {'Δ':>15} {'Δ%':>8}")
        for key, excel_value in sorted(metrics.materials_cost_breakdown.items()):
            bs_value = section.material_cost_breakdown.get(key)
            if excel_value is None or bs_value is None:
                delta = rel = np.nan
            else:
                delta = bs_value - excel_value
                rel = delta / excel_value if excel_value else np.nan
            excel_str = f"${excel_value:,.2f}" if excel_value is not None else "N/A"
            bs_str = f"${bs_value:,.2f}" if bs_value is not None else "N/A"
            delta_str = f"${delta:,.2f}" if not np.isnan(delta) else "N/A"
            rel_str = f"{rel:.2%}" if not np.isnan(rel) else "N/A"
            print(f"{key:25} {excel_str:>15} {bs_str:>15} {delta_str:>15} {rel_str:>8}")

    if args.detailed:
        units = [
            ("Seed", section.seed_unit),
            ("Fermentation", section.fermentation_unit),
        ]

        cr_units = section.cell_removal_units
        if len(cr_units) == 1:
            units.append(("Cell removal", cr_units[0]))
        else:
            for idx, unit in enumerate(cr_units, start=1):
                title = f"Cell removal {idx}: {unit.line}"
                units.append((title, unit))

        units.extend(
            [
                ("UF/DF", section.ufdf_unit),
                ("Chromatography", section.chromatography_unit),
                ("Predrying", section.predrying_unit),
                ("Spray dryer", section.spray_dryer_unit),
            ]
        )
        for title, unit in units:
            _print_unit_details(
                title,
                unit,
                component_threshold=args.component_threshold,
            )


if __name__ == "__main__":
    main()
