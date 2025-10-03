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


def test_material_cost_breakdown(front_end_section, baseline_metrics):
    if not baseline_metrics.materials_cost_breakdown:
        pytest.skip("Baseline materials breakdown not recorded")

    for key, expected in baseline_metrics.materials_cost_breakdown.items():
        observed = front_end_section.material_cost_breakdown.get(key)
        assert np.isclose(observed, expected, rtol=0.02), f"Mismatch for {key}"


