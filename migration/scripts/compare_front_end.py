"""Compare BioSTEAM front-end outputs against a reference baseline snapshot."""

from __future__ import annotations

import argparse
from collections import defaultdict
import math
from pathlib import Path
from typing import Iterable, Mapping

import biosteam as bst
import numpy as np

from migration.baseline_metrics import BaselineMetrics, load_baseline_metrics
from migration.front_end import build_front_end_section


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("Revised Baseline Excel Model.xlsx"),
        help=(
            "Legacy workbook path. Only required for historical parity checks; "
            "the BioSTEAM baseline no longer consumes it by default."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("migration/baseline_metrics_map.yaml"),
        help=(
            "Mapping between workbook cells and metrics (used only when the workbook "
            "parity mode is explicitly requested)."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "excel"],
        default="baseline",
        help=(
            "Comparison mode. 'baseline' uses BioSTEAM-generated metrics as the reference; "
            "'excel' falls back to the legacy workbook mapping."
        ),
    )
    parser.add_argument(
        "--baseline-config",
        type=Path,
        help="Path to baseline YAML overrides (defaults to migration/baseline_defaults.yaml)",
    )
    parser.add_argument(
        "--baseline-metrics-json",
        type=Path,
        help="Optional JSON metrics snapshot (tests/opn/baseline_metrics.json) to use instead of reading the Excel workbook",
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


def _stream_component_mass(stream: bst.Stream, component: str) -> float | None:
    if stream is None or not hasattr(stream, "imass"):
        return None
    try:
        value = stream.imass[component]
    except Exception:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
    if stream is None or not hasattr(stream, "imass") or stream.imass is None:
        return {}

    data = defaultdict(float)

    sparse = getattr(stream.imass, "data", None)
    items = getattr(sparse, "dct", None) if sparse is not None else None
    if items is None:
        try:
            items = dict(stream.imass.items())
        except Exception:
            return {}

    chemicals = getattr(stream, "chemicals", None)
    for index, mass in items.items():
        try:
            value = float(mass)
        except (TypeError, ValueError):
            continue
        if abs(value) < min_mass:
            continue
        if chemicals and isinstance(index, int):
            component = chemicals.IDs[index]
        else:
            component = str(index)
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
    if args.mode == "baseline":
        metrics_path = args.baseline_metrics_json or Path("tests/opn/baseline_metrics.json")
        metrics = BaselineMetrics.from_json(metrics_path)
    else:
        metrics = load_baseline_metrics(
            workbook_path=args.workbook,
            config_path=args.config,
        )

    bst.main_flowsheet.clear()
    defaults_arg = str(args.workbook) if args.mode == "excel" else None
    section = build_front_end_section(
        defaults_arg,
        mode=args.mode,
        baseline_config=args.baseline_config,
    )
    section.system.simulate()

    spray_product = section.spray_dryer_unit.outs[0]
    try:
        dry_product_mass = float(spray_product.imass['Osteopontin'])
    except (KeyError, TypeError):
        dry_product_mass = spray_product.F_mass

    checkpoints = []

    # Final product – stream-based mass already available
    checkpoints.append(
        (
            "Final product",
            metrics.final_product_kg,
            section.spray_dryer_unit.plan.derived.get("product_out_kg"),
            dry_product_mass,
        )
    )

    checkpoints.append(
        (
            "Fermentation",
            metrics.mass_trail["product_preharvest_kg"],
            section.fermentation_unit.plan.derived.get("product_out_kg"),
            _stream_component_mass(section.fermentation_unit.outs[1], "Osteopontin"),
        )
    )

    checkpoints.append(
        (
            "Cell removal",
            metrics.mass_trail["product_after_microfiltration_kg"],
            section.microfiltration_unit.plan.derived.get("product_out_kg"),
            _stream_component_mass(section.microfiltration_unit.outs[0], "Osteopontin"),
        )
    )

    checkpoints.append(
        (
            "UF/DF",
            metrics.mass_trail["product_after_ufdf_kg"],
            section.ufdf_unit.plan.derived.get("product_out_kg"),
            _stream_component_mass(section.ufdf_unit.outs[0], "Osteopontin"),
        )
    )

    checkpoints.append(
        (
            "Chromatography",
            metrics.mass_trail["product_after_chromatography_kg"],
            section.chromatography_unit.plan.derived.get("product_out_kg"),
            _stream_component_mass(section.chromatography_unit.outs[0], "Osteopontin"),
        )
    )

    checkpoints.append(
        (
            "Predry",
            metrics.mass_trail["product_after_predry_kg"],
            section.predrying_unit.plan.derived.get("product_out_kg"),
            _stream_component_mass(section.predrying_unit.outs[0], "Osteopontin"),
        )
    )

    reference_label = "Baseline" if args.mode == "baseline" else "Excel"
    plan_label = "Plan target"
    stream_label = "Stream"

    if getattr(metrics, "workbook_path", None):
        print(f"Reference source: {metrics.workbook_path}")

    print(
        "NOTE: Plan targets currently reflect the configured baseline defaults. "
        "Stream values come from the simulated BioSTEAM unit outputs."
    )

    print("\nMass trail comparison (kg):")
    print(
        f"{'Stage':20} {reference_label:>12} {plan_label:>14} {stream_label:>12} "
        f"{'Plan Δ':>12} {'Stream Δ':>12}"
    )

    training_wheel_notes: list[str] = []
    for stage, baseline_value, plan_value, stream_value in checkpoints:
        if baseline_value is None:
            baseline_value = math.nan
        plan_delta = (
            plan_value - baseline_value
            if plan_value is not None and not math.isnan(baseline_value)
            else math.nan
        )
        stream_delta = (
            stream_value - baseline_value
            if stream_value is not None and not math.isnan(baseline_value)
            else math.nan
        )

        tolerance = 1e-3
        if (
            plan_value is not None
            and stream_value is not None
            and not math.isnan(plan_value)
            and not math.isnan(stream_value)
            and abs(plan_value - stream_value) > tolerance
        ):
            training_wheel_notes.append(
                f"{stage}: plan target {plan_value:.3f} kg vs. stream {stream_value:.3f} kg"
            )

        def _fmt(value: float | None) -> str:
            if value is None or math.isnan(value):
                return "   N/A"
            return f"{value:12.3f}"

        print(
            f"{stage:20} {_fmt(baseline_value)} {_fmt(plan_value)} {_fmt(stream_value)} "
            f"{_fmt(plan_delta)} {_fmt(stream_delta)}"
        )

    if training_wheel_notes:
        print(
            "\n⚠ Units still using plan targets: "
            + "; ".join(training_wheel_notes)
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

    print(
        f"{'Metric':25} {reference_label:>15} {plan_label:>15} {'Δ':>15} {'Δ%':>8}"
    )
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

    allocation = section.allocation_result
    allocation_rows = [
        (
            "CMO per unit",
            metrics.cmo_per_unit_usd,
            allocation.cmo_per_unit_usd if allocation else None,
        ),
        (
            "Resin per unit",
            metrics.resin_per_unit_usd,
            allocation.resin_per_unit_usd if allocation else None,
        ),
        (
            "Total per unit",
            metrics.total_per_unit_usd,
            allocation.total_per_unit_usd if allocation else None,
        ),
    ]

    if any(row[1] is not None or row[2] is not None for row in allocation_rows):
        print("\nAllocation per-unit (USD):")
        print(f"{'Metric':25} {reference_label:>15} {plan_label:>15} {'Δ':>15} {'Δ%':>8}")
        for label, excel_value, biosteam_value in allocation_rows:
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

        basis_excel = metrics.allocation_basis or "N/A"
        basis_bs = allocation.basis if allocation else "N/A"
        print(f"Basis: {basis_excel} (ref) vs {basis_bs} (BioSTEAM)")
        denom_excel = metrics.allocation_denominator
        denom_bs = allocation.denominator_value if allocation else None
        if denom_excel is not None or denom_bs is not None:
            excel_str = f"{denom_excel:,.3f}" if denom_excel is not None else "N/A"
            bs_str = f"{denom_bs:,.3f}" if denom_bs is not None else "N/A"
            print(f"Denominator: {excel_str} vs {bs_str}")

    if metrics.materials_cost_breakdown:
        print("\nMaterials cost breakdown (USD):")
        print(f"{'Component':25} {reference_label:>15} {plan_label:>15} {'Δ':>15} {'Δ%':>8}")
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

        conc_units = section.concentration_units
        if len(conc_units) == 1:
            units.append(("Concentration", conc_units[0]))
        else:
            for idx, unit in enumerate(conc_units, start=1):
                title = f"Concentration {idx}: {unit.line}"
                units.append((title, unit))

        capture_units: tuple[bst.Unit, ...] = getattr(section, "capture_units", ())
        if capture_units:
            if len(capture_units) == 1:
                units.append(("Capture", capture_units[0]))
            else:
                for idx, unit in enumerate(capture_units, start=1):
                    title = f"Capture {idx}: {unit.line}"
                    units.append((title, unit))

        dsp03_units: tuple[bst.Unit, ...] = getattr(section, "dsp03_units", ())
        if dsp03_units:
            if len(dsp03_units) == 1:
                units.append(("DSP03", dsp03_units[0]))
            else:
                for idx, unit in enumerate(dsp03_units, start=1):
                    title = f"DSP03 {idx}: {unit.line}"
                    units.append((title, unit))

        units.append(("Predrying", section.predrying_unit))

        dsp04_units: tuple[bst.Unit, ...] = getattr(section, "dsp04_units", ())
        if dsp04_units:
            if len(dsp04_units) == 1:
                units.append(("DSP04", dsp04_units[0]))
            else:
                for idx, unit in enumerate(dsp04_units, start=1):
                    title = f"DSP04 {idx}: {unit.line}"
                    units.append((title, unit))

        units.append(("Spray dryer", section.spray_dryer_unit))

        capture_summary_printed = False
        dsp04_summary_printed = False
        for title, unit in units:
            _print_unit_details(
                title,
                unit,
                component_threshold=args.component_threshold,
            )
            if (
                not capture_summary_printed
                and title.startswith("Capture")
                and getattr(section, "capture_handoff", None) is not None
            ):
                handoff = section.capture_handoff
                print("\nCapture handoff summary:")
                for key, value in handoff.as_dict().items():
                    if key == "notes":
                        if value:
                            print(f"  {key}: {', '.join(value)}")
                        continue
                    print(f"  {key}: {value}")
                capture_summary_printed = True
            if (
                not dsp04_summary_printed
                and title.startswith("DSP04")
                and getattr(section, "dsp04_handoff", None) is not None
            ):
                handoff = section.dsp04_handoff
                print("\nDSP04 handoff summary:")
                for key, value in handoff.as_dict().items():
                    if key == "notes":
                        if value:
                            print(f"  {key}: {', '.join(value)}")
                        continue
                    print(f"  {key}: {value}")
                dsp04_summary_printed = True

        if getattr(section, "dsp05_handoff", None) is not None:
            handoff = section.dsp05_handoff
            print("\nDSP05 final product summary:")
            for field in (
                "method",
                "product_form",
                "product_mass_kg",
                "product_volume_m3",
                "protein_concentration_g_per_l",
                "moisture_wt_pct",
                "bulk_density_kg_m3",
                "step_recovery_fraction",
                "cycle_time_h",
                "client_cost_usd",
                "capex_flagged_usd",
            ):
                value = getattr(handoff, field, None)
                if value is not None:
                    print(f"  {field}: {value}")
            if getattr(handoff, "notes", None):
                print(f"  notes: {', '.join(handoff.notes)}")


if __name__ == "__main__":
    main()
