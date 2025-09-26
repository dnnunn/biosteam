"""Simple placeholder BioSTEAM units that reference Excel-derived plans."""

from __future__ import annotations

from typing import Dict

import biosteam as bst

from .unit_builders import UnitPlan

__all__ = [
    "PlanBackedUnit",
    "SeedTrainUnit",
    "FermentationUnit",
]


class PlanBackedUnit(bst.Unit):
    """Base class that stores a UnitPlan for design/analysis reference."""

    _ins_size_is_fixed = False

    def __init__(self, ID: str, plan: UnitPlan, **kwargs) -> None:
        super().__init__(ID, **kwargs)
        self.plan = plan
        self.notes = list(plan.notes)

    def _summary(self) -> Dict[str, str]:  # pragma: no cover - convenience only
        summary = super()._summary()
        summary.update({
            "module": self.plan.key.module,
            "option": self.plan.key.option or "<default>",
        })
        return summary


class SeedTrainUnit(PlanBackedUnit):
    """Minimal seed-train placeholder that passes feed through unchanged."""

    _N_ins = 1
    _N_outs = 1
    line = "SeedTrain"

    _units = {
        "Yeast extract concentration": "g/L",
        "Peptone concentration": "g/L",
        "Total nutrient concentration": "g/L",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)

    def _design(self) -> None:
        specs = self.plan.specs
        derived = self.plan.derived
        self.design_results["Yeast extract concentration"] = (
            specs.yeast_extract_concentration_g_per_l or 0.0
        )
        self.design_results["Peptone concentration"] = (
            specs.peptone_concentration_g_per_l or 0.0
        )
        self.design_results["Total nutrient concentration"] = (
            derived.get("total_nutrient_concentration_g_per_l") or 0.0
        )

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()


class FermentationUnit(PlanBackedUnit):
    """Minimal fermentation placeholder capturing cycle information."""

    _N_ins = 1
    _N_outs = 1
    line = "Fermentor"

    _units = {
        "Batch cycle": "h",
        "Product yield on glucose": "kg/kg",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)
        product.T = feed.T
        product.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Batch cycle"] = derived.get("batch_cycle_hours", 0.0)
        self.design_results["Product yield on glucose"] = derived.get(
            "product_yield_glucose", 0.0
        )

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
