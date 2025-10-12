"""Tests for TEA materials integration with DSP03 registry-based buffer costing."""

from __future__ import annotations

import yaml
import numpy as np

from migration.buffer_tools.costing import estimate_cost_per_m3_for_buffer_id
from migration.front_end import build_front_end_section


def test_dsp03_registry_buffer_cost_integration(tmp_path):
    # Enable registry-based costing for DSP03 and set a known buffer ID
    override = {
        "dsp03": {
            "buffers": {
                "df": {
                    "use_planner": True,
                    "auto_plan": False,
                    "cost_from_registry": True,
                    "cost_buffer_id": "tris_hcl_pH7p5_50mM",
                }
            }
        }
    }
    override_path = tmp_path / "baseline_override.yaml"
    override_path.write_text(yaml.safe_dump(override), encoding="utf-8")

    section = build_front_end_section(
        None,
        mode="baseline",
        baseline_config=str(override_path),
    )
    section.system.simulate()

    # Derive the expected buffer cost from the plan volume and registry price
    dsp03_units = section.dsp03_units
    assert dsp03_units, "DSP03 unit not found in section"
    plan = dsp03_units[0].plan
    df_buffer_m3 = float(plan.derived.get("df_buffer_volume_m3", 0.0))
    assert df_buffer_m3 > 0.0

    unit_price = estimate_cost_per_m3_for_buffer_id("tris_hcl_pH7p5_50mM")
    assert unit_price is not None and unit_price > 0.0

    expected_total = df_buffer_m3 * unit_price

    obs = section.material_cost_breakdown.get("dsp03_buffers")
    assert obs is not None
    assert np.isclose(obs, expected_total, rtol=1e-6)

