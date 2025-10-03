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
            285.696820699425,
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
        str(WORKBOOK_PATH),
        mode="baseline",
        baseline_config=str(override_path),
    )
    section.system.simulate()

    capture_unit = section.capture_units[0]
    derived = capture_unit.plan.derived

    assert capture_unit.line == "Chitosan Capture"
    assert np.isclose(derived.get("product_out_kg"), expected_output, rtol=0.01)
    assert np.isclose(derived.get("pool_volume_l"), expected_pool_volume, rtol=1e-6)
    assert np.isclose(
        derived.get("polymer_cost_per_batch"), expected_polymer_cost, rtol=0.01
    )

    assert section.capture_handoff is not None
    assert section.capture_handoff.route is CaptureRoute.CHITOSAN
    assert section.capture_handoff.needs_df
    assert section.capture_handoff.pool_volume_l == pytest.approx(expected_pool_volume)

    report_stream = section.handoff_streams[capture_unit.ID]
    assert np.isclose(
        _component_mass(report_stream, "Osteopontin"),
        expected_output,
        rtol=1e-6,
    )
