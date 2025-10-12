"""Tests for capture-route overrides in the front-end baseline."""

from __future__ import annotations

import numpy as np
import pytest
import yaml

from migration.capture import CaptureRoute
from migration.front_end import build_front_end_section


def _component_mass(stream, component: str) -> float:
    try:
        value = stream.imass[component]
    except (KeyError, TypeError, AttributeError):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@pytest.mark.not_slow
@pytest.mark.parametrize(
    "override, expected_output, expected_pool_volume, expected_polymer_cost",
    [
        (
            {"capture": {"method": "chitosan"}},
            283.61921433854366,
            6_500.0,
            21_637.627374150004,
        ),
    ],
)
def test_capture_chitosan_override(
    tmp_path,
    override,
    expected_output,
    expected_pool_volume,
    expected_polymer_cost,
):
    override_path = tmp_path / "baseline_override.yaml"
    override_path.write_text(yaml.safe_dump(override), encoding="utf-8")

    section = build_front_end_section(
        None,
        mode="baseline",
        baseline_config=str(override_path),
    )
    section.system.simulate()

    assert section.capture_units == tuple()
    capture_unit = section.chromatography_unit
    derived = capture_unit.plan.derived

    assert section.concentration_units == tuple()
    assert not section.ufdf_in_system
    assert capture_unit.line == "Chitosan Capture"
    assert np.isclose(derived.get("product_out_kg"), expected_output, rtol=0.01)
    assert np.isclose(derived.get("pool_volume_l"), expected_pool_volume, rtol=1e-6)
    assert np.isclose(
        derived.get("polymer_cost_per_batch"), expected_polymer_cost, rtol=0.01
    )

    assert section.capture_handoff is not None
    assert section.capture_handoff.route is CaptureRoute.CHITOSAN
    assert not section.capture_handoff.needs_df
    assert section.capture_handoff.pool_volume_l == pytest.approx(expected_pool_volume)

    report_stream = section.handoff_streams[capture_unit.ID]
    assert np.isclose(
        _component_mass(report_stream, "Osteopontin"),
        expected_output,
        rtol=1e-6,
    )

    breakdown = section.material_cost_breakdown
    polymer_cost = breakdown.get("capture_polymer")
    assert polymer_cost is not None
    assert np.isclose(polymer_cost, expected_polymer_cost, rtol=0.01)
    reagents_cost = breakdown.get("capture_reagents")
    assert reagents_cost is not None
    assert np.isclose(reagents_cost, 0.18525, rtol=0.05)
    utilities_cost = breakdown.get("capture_utilities")
    assert utilities_cost is not None
    assert np.isclose(utilities_cost, 0.6678479567307694, rtol=0.05)

    dsp04_units = section.dsp04_units
    assert len(dsp04_units) == 2

    polish_unit = dsp04_units[0]
    assert polish_unit.line == "CEX Negative FT"
    polish_plan = polish_unit.plan.derived
    initial_chitosan = section.capture_handoff.chitosan_ppm
    assert initial_chitosan is not None
    assert np.isclose(
        polish_plan.get("effective_recovery_fraction", 1.0),
        0.992,
        rtol=1e-3,
    )
    final_chitosan = section.dsp04_handoff.chitosan_ppm
    assert final_chitosan is not None
    assert final_chitosan <= initial_chitosan * 0.11
    assert polish_plan.get("estimated_chitosan_ppm_out") == pytest.approx(
        final_chitosan,
        rel=1e-3,
    )

    sterile_unit = dsp04_units[1]
    assert sterile_unit.line == "Sterile Filter 0.2 µm"
    sterile_plan = sterile_unit.plan.derived
    input_volume = sterile_plan.get("input_volume_l")
    assert input_volume is not None and input_volume > 0.0
    assert sterile_plan.get("filter_area_m2") == pytest.approx(
        input_volume / 1_500.0,
        rel=1e-6,
    )
    assert sterile_plan.get("adsorption_loss_fraction") == pytest.approx(
        5e-4,
        rel=1e-6,
    )

    poly_buffers = breakdown.get("dsp04_buffers")
    assert poly_buffers is not None
    assert np.isclose(poly_buffers, 260.0, rtol=1e-6)
    poly_labor = breakdown.get("dsp04_labor")
    assert poly_labor is not None
    assert np.isclose(poly_labor, 480.0, rtol=1e-6)
    assert "dsp04_resin" not in breakdown
    sterile_media_cost = breakdown.get("sterile_filter_media")
    assert sterile_media_cost is not None
    assert np.isclose(sterile_media_cost, 505.55555555555554, rtol=1e-6)
    sterile_labor_cost = breakdown.get("sterile_filter_labor")
    assert sterile_labor_cost is not None
    assert np.isclose(sterile_labor_cost, 160.0, rtol=1e-6)
    assert "sterile_prefilter_media" not in breakdown

    dsp03_membranes_cost = breakdown.get("dsp03_membranes")
    assert dsp03_membranes_cost is not None
    assert np.isclose(dsp03_membranes_cost, 132.5490196078431, rtol=1e-6)
    dsp03_buffers_cost = breakdown.get("dsp03_buffers")
    assert dsp03_buffers_cost is not None
    assert np.isclose(dsp03_buffers_cost, 2383.333333333333, rtol=1e-6)
    dsp03_labor_cost = breakdown.get("dsp03_labor")
    assert dsp03_labor_cost is not None
    assert np.isclose(dsp03_labor_cost, 640.0, rtol=1e-6)
    dsp03_waste_cost = breakdown.get("dsp03_waste_disposal")
    assert dsp03_waste_cost is not None
    assert np.isclose(dsp03_waste_cost, 3336.6666666666665, rtol=1e-6)
