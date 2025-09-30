"""Regression tests for the OPN front-end migration."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import biosteam as bst

from migration.front_end import build_front_end_section
from migration.baseline_metrics import BaselineMetrics

FIXTURE_PATH = Path(__file__).with_name("baseline_metrics.json")
WORKBOOK_PATH = Path("BaselineModel.xlsx")
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


def test_front_end_mass_trail(front_end_section, baseline_metrics):
    spray_product = front_end_section.spray_dryer_unit.outs[0]
    assert np.isclose(
        spray_product.F_mass,
        baseline_metrics.final_product_kg,
        rtol=0.02,
    ), "Final product mass deviates from Excel baseline"


@pytest.mark.parametrize(
    "unit_name,column",
    [
        ("fermentation", "product_preharvest_kg"),
        ("microfiltration", "product_after_microfiltration_kg"),
        ("ufdf", "product_after_ufdf_kg"),
        ("chromatography", "product_after_chromatography_kg"),
        ("predrying", "product_after_predry_kg"),
    ],
)
def test_intermediate_product_matches(unit_name, column, front_end_section, baseline_metrics):
    unit_plan = getattr(front_end_section, f"{unit_name}_unit").plan
    observed = unit_plan.derived.get("product_out_kg")
    expected = baseline_metrics.mass_trail[column]
    assert np.isclose(observed, expected, rtol=0.05)


@pytest.mark.parametrize(
    "plan_attr,plan_key,baseline_key",
    [
        ("fermentation_unit", "total_glucose_feed_kg", "total_glucose_feed_kg"),
        ("fermentation_unit", "total_glycerol_feed_kg", "total_glycerol_feed_kg"),
        ("fermentation_unit", "total_molasses_feed_kg", "total_molasses_feed_kg"),
        ("fermentation_unit", "antifoam_volume_l", "antifoam_volume_l"),
        ("seed_unit", "yeast_extract_per_batch_kg", "yeast_extract_per_batch_kg"),
        ("seed_unit", "peptone_per_batch_kg", "peptone_per_batch_kg"),
    ],
)
def test_feed_and_additive_inputs_match(plan_attr, plan_key, baseline_key, front_end_section, baseline_metrics):
    plan = getattr(front_end_section, plan_attr).plan
    observed = plan.derived.get(plan_key)
    expected = baseline_metrics.mass_trail[baseline_key]
    assert np.isclose(observed, expected, rtol=0.02)


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


def test_material_cost_breakdown(front_end_section, baseline_metrics):
    if not baseline_metrics.materials_cost_breakdown:
        pytest.skip("Baseline materials breakdown not recorded")

    for key, expected in baseline_metrics.materials_cost_breakdown.items():
        observed = front_end_section.material_cost_breakdown.get(key)
        assert np.isclose(observed, expected, rtol=0.02), f"Mismatch for {key}"
