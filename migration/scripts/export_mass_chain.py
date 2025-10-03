"""Export per-stage mass efficiencies for the OPN baseline."""

from __future__ import annotations

import json
from pathlib import Path

from migration.front_end import build_front_end_section


def _component_mass(stream, component: str) -> float:
    try:
        return float(stream.imass[component])
    except (KeyError, AttributeError, TypeError):
        return 0.0


def compute_mass_chain() -> dict[str, object]:
    section = build_front_end_section(mode="baseline")
    section.system.simulate()

    stage_units: list = []
    stage_units.extend(section.cell_removal_units)
    stage_units.extend(section.concentration_units)
    stage_units.append(section.chromatography_unit)
    stage_units.extend(section.capture_units)
    stage_units.extend(section.dsp03_units)
    stage_units.append(section.predrying_unit)
    stage_units.extend(section.dsp04_units)
    stage_units.append(section.spray_dryer_unit)

    seen_ids: set[str] = set()
    ordered_units = []
    for unit in stage_units:
        if unit.ID in seen_ids:
            continue
        seen_ids.add(unit.ID)
        ordered_units.append(unit)

    baseline_chain: list[dict[str, float | str]] = []
    start_mass = 350.0
    cumulative = start_mass

    for unit in ordered_units:
        plan = getattr(unit, "plan", None)
        derived = plan.derived if plan is not None else {}
        input_mass = float(derived.get("input_product_kg") or 0.0)
        output_mass = float(derived.get("product_out_kg") or 0.0)
        efficiency = (output_mass / input_mass) if input_mass else None
        if efficiency is not None and efficiency > 0.0:
            cumulative *= efficiency
        stream_mass = _component_mass(unit.outs[0], 'Osteopontin')

        baseline_chain.append(
            {
                "unit_id": unit.ID,
                "unit_line": unit.line,
                "plan_input_kg": input_mass,
                "plan_output_kg": output_mass,
                "stage_efficiency": efficiency if efficiency is not None else 0.0,
                "baseline_mass_from_350_kg": cumulative,
                "stream_output_kg": stream_mass,
            }
        )

    return {
        "start_mass_kg": start_mass,
        "stage_chain": baseline_chain,
    }


def main() -> None:
    data = compute_mass_chain()
    output_path = Path("tests/opn/baseline_mass_chain.json")
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Baseline mass chain written to {output_path}")


if __name__ == "__main__":
    main()
