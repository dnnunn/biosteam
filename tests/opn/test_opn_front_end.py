"""Regression tests for the OPN front-end migration."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import biosteam as bst

from migration.front_end import build_front_end_section
from migration.baseline_metrics import BaselineMetrics


def _component_mass(stream: bst.Stream, component: str) -> float:
    try:
        value = stream.imass[component]
    except (KeyError, TypeError, AttributeError):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

FIXTURE_PATH = Path(__file__).with_name("baseline_metrics.json")
WORKBOOK_PATH = Path("Revised Baseline Excel Model.xlsx")
BASELINE_CONFIG_PATH = Path("migration/baseline_defaults.yaml")

@pytest.fixture(scope="module")
def baseline_metrics() -> BaselineMetrics:
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return BaselineMetrics(
        workbook_path=Path(data["workbook"]),
        mass_trail=data["mass_trail"],
        final_product_kg=data["final_product_kg"],
        cost_per_kg_usd=data.get("cost_per_kg_usd"),
        total_cost_per_batch_usd=data.get("total_cost_per_batch_usd"),
        cmo_fees_usd=data.get("cmo_fees_usd"),
        materials_cost_per_batch_usd=data.get("materials_cost_per_batch_usd"),
        materials_cost_breakdown=data.get("materials_cost_breakdown", {}),
    )


@pytest.fixture(scope="module")
def front_end_section(baseline_metrics: BaselineMetrics):
    bst.main_flowsheet.clear()
    section = build_front_end_section(
        str(WORKBOOK_PATH),
        mode="baseline",
        baseline_config=str(BASELINE_CONFIG_PATH),
    )
    section.system.simulate()
    return section


def test_fermentation_glucose_balance(front_end_section):
    plan = front_end_section.fermentation_unit.plan
    total = plan.derived.get("total_glucose_feed_kg")
    growth = plan.derived.get("glucose_for_growth_kg")
    maintenance = plan.derived.get("glucose_for_maintenance_kg")
    loss_fraction = plan.derived.get("glucose_losses_fraction") or 0.0
    assert total is not None
    assert growth is not None
    assert maintenance is not None
    expected_total = (growth + maintenance) * (1.0 + loss_fraction)
    assert np.isclose(total, expected_total, rtol=0.02)
    assert np.isclose(total, plan.derived.get("glucose_consumed_kg"), rtol=0.001)


def test_cost_metrics(front_end_section, baseline_metrics):
    if baseline_metrics.cost_per_kg_usd is not None:
        assert np.isclose(
            front_end_section.cost_per_kg_usd,
            baseline_metrics.cost_per_kg_usd,
            rtol=0.02,
        )

    if baseline_metrics.total_cost_per_batch_usd is not None:
        assert np.isclose(
            front_end_section.total_cost_per_batch_usd,
            baseline_metrics.total_cost_per_batch_usd,
            rtol=0.02,
        )

    if baseline_metrics.cmo_fees_usd is not None:
        assert np.isclose(
            front_end_section.cmo_fees_usd,
            baseline_metrics.cmo_fees_usd,
            rtol=0.02,
        )

    if baseline_metrics.materials_cost_per_batch_usd is not None:
        assert np.isclose(
            front_end_section.computed_material_cost_per_batch_usd,
            baseline_metrics.materials_cost_per_batch_usd,
            rtol=0.02,
        )
        assert np.isclose(
            front_end_section.materials_cost_per_kg_usd,
            baseline_metrics.materials_cost_per_batch_usd / baseline_metrics.final_product_kg,
            rtol=0.02,
        )


def test_material_cost_breakdown(front_end_section, baseline_metrics):
    if not baseline_metrics.materials_cost_breakdown:
        pytest.skip("Baseline materials breakdown not recorded")

    for key, expected in baseline_metrics.materials_cost_breakdown.items():
        observed = front_end_section.material_cost_breakdown.get(key)
        assert np.isclose(observed, expected, rtol=0.02), f"Mismatch for {key}"


def test_cmo_contract_breakdown(front_end_section):
    expected_stage_totals = {
        "usp02_fermentation": 74418.09374999999,
        "dsp_suite": 17964.685329861106,
        "spray_dryer": 882.749361,
        "labor": 5154.5,
        "documentation": 1353.05625,
        "qa_review": 2706.1125,
        "qc_testing": 4059.16875,
        "consumables": 12452.894831780239,
        "campaign_setup": 41666.666666666664,
        "facility_reservation": 16666.666666666668,
        "validation": 991.593839772011,
    }

    for key, expected_value in expected_stage_totals.items():
        observed = front_end_section.cmo_stage_costs[key].total_usd
        assert np.isclose(observed, expected_value, rtol=0.02), f"CMO stage mismatch for {key}"

    assert np.isclose(
        front_end_section.cmo_standard_batch_usd,
        sum(
            expected_stage_totals[k]
            for k in (
                "usp02_fermentation",
                "dsp_suite",
                "spray_dryer",
                "labor",
                "documentation",
                "qa_review",
                "qc_testing",
                "consumables",
            )
        ),
        rtol=0.02,
    )
    assert np.isclose(
        front_end_section.cmo_campaign_adders_usd,
        expected_stage_totals["campaign_setup"]
        + expected_stage_totals["facility_reservation"]
        + expected_stage_totals["validation"],
        rtol=0.02,
    )


def test_aex_cycle_profile(front_end_section):
    plan = front_end_section.chromatography_unit.plan

    assert plan.derived.get("cycles_per_batch") == 25
    assert np.isclose(plan.derived.get("cycle_time_h"), 2.2135171655354773, rtol=0.05)
    assert np.isclose(plan.derived.get("processing_time_h"), 55.33792913838693, rtol=0.05)
    assert np.isclose(plan.derived.get("pool_volume_l"), 21205.750411731104, rtol=0.02)
    final_mass = front_end_section.spray_dryer_unit.plan.derived.get("product_out_kg")
    assert final_mass and final_mass > 0
    assert np.isclose(
        front_end_section.cmo_cost_per_kg_usd,
        front_end_section.cmo_total_fee_usd / final_mass,
        rtol=0.02,
    )
    assert np.isclose(
        front_end_section.cmo_standard_cost_per_kg_usd,
        front_end_section.cmo_standard_batch_usd / final_mass,
        rtol=0.02,
    )
    assert np.isclose(
        front_end_section.cmo_campaign_cost_per_kg_usd,
        front_end_section.cmo_campaign_adders_usd / final_mass,
        rtol=0.02,
    )


def test_fermentation_profile_switch(tmp_path):
    baseline_section = build_front_end_section(
        "Revised Baseline Excel Model.xlsx",
        mode="baseline",
        baseline_config="migration/baseline_defaults.yaml",
    )
    baseline_section.system.simulate()

    override_path = tmp_path / "glucose_defined.yaml"
    override_path.write_text(
        "seed:\n  profile: glucose_defined\nfermentation:\n  profile: glucose_defined\n",
        encoding="utf-8",
    )

    defined_section = build_front_end_section(
        "Revised Baseline Excel Model.xlsx",
        mode="baseline",
        baseline_config=str(override_path),
    )
    defined_section.system.simulate()

    base_totals = baseline_section.fermentation_unit.plan.derived.get("_profile_carbon_totals", {})
    defined_totals = defined_section.fermentation_unit.plan.derived.get("_profile_carbon_totals", {})

    assert base_totals.get("glucose") == pytest.approx(8125.0)
    assert defined_totals.get("glucose") == pytest.approx(7000.0)

    base_carbon_cost = baseline_section.material_cost_breakdown.get("carbon_source")
    defined_carbon_cost = defined_section.material_cost_breakdown.get("carbon_source")
    assert defined_carbon_cost < base_carbon_cost

    assert defined_section.material_cost_breakdown.get("media", 0.0) >= 0.0
    assert baseline_section.fermentation_unit.plan.derived.get("media_type") == "rich"
    assert defined_section.fermentation_unit.plan.derived.get("media_type") == "defined"
