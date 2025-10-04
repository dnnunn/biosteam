"""Tests for capture-route overrides in the front-end baseline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from migration.capture import CaptureRoute
from migration.front_end import build_front_end_section


WORKBOOK_PATH = Path("Revised Baseline Excel Model.xlsx")


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
            247.29184299488622,
            6_500.0,
            18_541.094132699996,
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
        str(WORKBOOK_PATH),
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
