"""Simple placeholder BioSTEAM units that reference Excel-derived plans."""

from __future__ import annotations

from typing import Dict

import biosteam as bst

from .unit_builders import UnitPlan

__all__ = [
    "PlanBackedUnit",
    "SeedTrainUnit",
    "FermentationUnit",
    "MicrofiltrationUnit",
    "UFDFUnit",
    "ChromatographyUnit",
    "PreDryingUnit",
    "SprayDryerUnit",
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
        if summary is None:
            summary = {}
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
        broth = self.outs[0]
        broth.copy_like(feed)

        glucose_mass = feed.imass['Glucose']
        if glucose_mass <= 0:
            return

        # Placeholder assumption: 15% of glucose converted in seed stage
        seed_conversion = 0.15 * glucose_mass

        broth.imass['Glucose'] -= seed_conversion
        broth.imass['Yeast'] += seed_conversion * 0.5  # placeholder biomass gain

        # Nutrient supplements remain in broth
        derived = self.plan.derived
        total_nutrients = derived.get('total_nutrient_concentration_g_per_l') or 0.0
        if total_nutrients > 0:
            broth.imass['CornSteepLiquor'] += total_nutrients * 0.01
            broth.imass['YeastExtract'] += total_nutrients * 0.01

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
    _N_outs = 2
    line = "Fermentor"

    _units = {
        "Batch cycle": "h",
        "Product yield on glucose": "kg/kg",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        broth, vent = self.outs
        broth.copy_like(feed)
        vent.empty()

        glucose_mass = feed.imass['Glucose']
        if glucose_mass <= 0:
            return

        # Assume complete consumption of glucose in production stage
        consumed = glucose_mass
        product_yield = self.plan.derived.get('product_yield_glucose', 0.0)
        biomass_yield = self.plan.specs.biomass_yield_glucose or 0.0

        product_mass = consumed * product_yield
        biomass_mass = consumed * biomass_yield
        byproduct_mass = max(consumed - product_mass - biomass_mass, 0.0)

        broth.imass['Glucose'] -= consumed
        broth.imass['Osteopontin'] += product_mass
        broth.imass['Yeast'] += biomass_mass

        vent.imass['CO2'] = byproduct_mass * 0.7
        vent.imass['Water'] = byproduct_mass * 0.3
        vent.P = feed.P
        vent.T = feed.T

        broth.T = feed.T
        broth.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Batch cycle"] = derived.get("batch_cycle_hours", 0.0)
        self.design_results["Product yield on glucose"] = derived.get(
            "product_yield_glucose", 0.0
        )

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()


class MicrofiltrationUnit(PlanBackedUnit):
    """Placeholder microfiltration step using plan-derived throughput data."""

    _N_ins = 1
    _N_outs = 1
    line = "Microfiltration"

    _units = {
        "Throughput": "L/hr",
        "Membrane cost per cycle": "USD",
        "Dilution volume": "m3",
    }

    def _run(self) -> None:
        self.outs[0].copy_like(self.ins[0])

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Throughput"] = derived.get("throughput_l_per_hr", 0.0)
        self.design_results["Membrane cost per cycle"] = derived.get(
            "membrane_cost_per_cycle", 0.0
        )
        self.design_results["Dilution volume"] = derived.get("dilution_volume_m3", 0.0)

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()


class UFDFUnit(PlanBackedUnit):
    """Placeholder ultrafiltration/diafiltration step."""

    _N_ins = 1
    _N_outs = 1
    line = "UF/DF"

    _units = {
        "Throughput": "L/hr",
        "Diafiltration volumes": "vol",
        "Membrane cost per cycle": "USD",
    }

    def _run(self) -> None:
        self.outs[0].copy_like(self.ins[0])

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Throughput"] = derived.get("throughput_l_per_hr", 0.0)
        self.design_results["Diafiltration volumes"] = derived.get(
            "diafiltration_volumes", 0.0
        )
        self.design_results["Membrane cost per cycle"] = derived.get(
            "membrane_cost_per_cycle", 0.0
        )

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()


class ChromatographyUnit(PlanBackedUnit):
    """Placeholder chromatography step tracking resin and buffers."""

    _N_ins = 1
    _N_outs = 1
    line = "Chromatography"

    _units = {
        "Resin cost per batch": "USD",
        "Total buffer bed volumes": "CV",
    }

    def _run(self) -> None:
        self.outs[0].copy_like(self.ins[0])

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Resin cost per batch"] = derived.get(
            "resin_cost_per_batch", 0.0
        )
        self.design_results["Total buffer bed volumes"] = derived.get(
            "total_buffer_bv", 0.0
        )

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()


class PreDryingUnit(PlanBackedUnit):
    """Placeholder pre-drying TFF/UFF step."""

    _N_ins = 1
    _N_outs = 1
    line = "PreDrying"

    _units = {
        "Throughput": "L/hr",
    }

    def _run(self) -> None:
        self.outs[0].copy_like(self.ins[0])

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Throughput"] = derived.get("throughput_l_per_hr", 0.0)

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()


class SprayDryerUnit(PlanBackedUnit):
    """Placeholder spray dryer capturing key specs."""

    _N_ins = 1
    _N_outs = 1
    line = "SprayDryer"

    _units = {
        "Capacity": "kg/hr",
        "Final solids": "%",
    }

    def _run(self) -> None:
        self.outs[0].copy_like(self.ins[0])

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Capacity"] = derived.get("capacity_kg_per_hr", 0.0)
        self.design_results["Final solids"] = derived.get("final_solids_percent", 0.0)

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
