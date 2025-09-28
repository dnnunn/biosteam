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
        feed_state = feed.copy()
        broth.copy_like(feed)

        glucose_mass = feed.imass['Glucose']
        if glucose_mass <= 0:
            feed.copy_like(feed_state)
            return

        derived = self.plan.derived
        conversion_fraction = derived.get('seed_glucose_conversion_fraction', 0.15)
        seed_conversion = glucose_mass * conversion_fraction

        broth.imass['Glucose'] -= seed_conversion

        biomass_yield = derived.get('biomass_yield_glucose')
        if biomass_yield is None:
            biomass_yield = 0.5  # fallback assumption
        broth.imass['Yeast'] += seed_conversion * biomass_yield

        # Nutrient supplements remain in broth
        total_nutrients = derived.get('total_nutrient_concentration_g_per_l') or 0.0
        if total_nutrients > 0:
            broth.imass['CornSteepLiquor'] += total_nutrients * 0.01
            broth.imass['YeastExtract'] += total_nutrients * 0.01

        feed.copy_like(feed_state)

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
        derived = self.plan.derived

        working_volume_l = derived.get('working_volume_l')
        if working_volume_l is None:
            working_volume_l = feed.F_vol or feed.F_mass or 1_000.0

        density = derived.get('broth_density_kg_per_l', 1.0)
        total_mass = working_volume_l * density

        target_titer = derived.get('target_titer_g_per_l') or 0.0
        product_mass = target_titer * working_volume_l / 1e3

        dcw_conc = derived.get('dcw_concentration_g_per_l') or 0.0
        biomass_mass = dcw_conc * working_volume_l / 1e3

        residual_glucose = derived.get('residual_glucose_g_per_l') or 0.0
        residual_glucose_mass = residual_glucose * working_volume_l / 1e3

        broth.empty()
        vent.empty()

        if product_mass > 0:
            broth.imass['Osteopontin'] = product_mass
        if biomass_mass > 0:
            broth.imass['Yeast'] = biomass_mass
        if residual_glucose_mass > 0:
            broth.imass['Glucose'] = residual_glucose_mass

        known_mass = product_mass + biomass_mass + residual_glucose_mass
        water_mass = max(total_mass - known_mass, 0.0)
        broth.imass['Water'] = water_mass

        broth.T = feed.T
        broth.P = feed.P
        vent.T = feed.T
        vent.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Batch cycle"] = derived.get("batch_cycle_hours", 0.0)
        self.design_results["Product yield on glucose"] = derived.get(
            "product_yield_glucose", 0.0
        )
        self.design_results["Working volume"] = derived.get("working_volume_l", 0.0)
        self.design_results["Target titer"] = derived.get("target_titer_g_per_l", 0.0)
        self.design_results["DCW concentration"] = derived.get(
            "dcw_concentration_g_per_l", 0.0
        )
        self.design_results["Glucose feed per batch"] = derived.get(
            "total_glucose_feed_kg", 0.0
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
        feed = self.ins[0]
        filtrate = self.outs[0]
        derived = self.plan.derived

        filtrate.empty()

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = float(feed.imass['Osteopontin'])
        product_mass = max(product_mass, 0.0)

        volume_l = derived.get('output_volume_l') or derived.get('harvest_volume_l')
        density = derived.get('broth_density_kg_per_l', 1.0)
        if volume_l is not None:
            total_mass = volume_l * density
        else:
            total_mass = feed.F_mass

        residual_glucose = derived.get('residual_glucose_after_mf_kg') or 0.0

        filtrate.imass['Osteopontin'] = product_mass
        filtrate.imass['Yeast'] = 0.0
        filtrate.imass['Glucose'] = residual_glucose

        known_mass = product_mass + residual_glucose
        water_mass = max(total_mass - known_mass, 0.0)
        filtrate.imass['Water'] = water_mass

        filtrate.T = feed.T
        filtrate.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Throughput"] = derived.get("throughput_l_per_hr", 0.0)
        self.design_results["Membrane cost per cycle"] = derived.get(
            "membrane_cost_per_cycle", 0.0
        )
        self.design_results["Dilution volume"] = derived.get("dilution_volume_m3", 0.0)
        self.design_results["Product out"] = derived.get("product_out_kg", 0.0)
        self.design_results["Output volume"] = derived.get("output_volume_l", 0.0)

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
        feed = self.ins[0]
        permeate = self.outs[0]
        derived = self.plan.derived

        permeate.empty()

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = float(feed.imass['Osteopontin'])
        product_mass = max(product_mass, 0.0)

        volume_l = derived.get('output_volume_l')
        density = derived.get('broth_density_kg_per_l', 1.0)
        if volume_l is not None:
            total_mass = volume_l * density
        else:
            total_mass = feed.F_mass

        permeate.imass['Osteopontin'] = product_mass
        permeate.imass['Yeast'] = 0.0
        permeate.imass['Glucose'] = 0.0

        water_mass = max(total_mass - product_mass, 0.0)
        permeate.imass['Water'] = water_mass

        permeate.T = feed.T
        permeate.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Throughput"] = derived.get("throughput_l_per_hr", 0.0)
        self.design_results["Diafiltration volumes"] = derived.get(
            "diafiltration_volumes", 0.0
        )
        self.design_results["Membrane cost per cycle"] = derived.get(
            "membrane_cost_per_cycle", 0.0
        )
        self.design_results["Product out"] = derived.get("product_out_kg", 0.0)
        self.design_results["Output volume"] = derived.get("output_volume_l", 0.0)

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
        feed = self.ins[0]
        eluate = self.outs[0]
        derived = self.plan.derived

        eluate.empty()

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = float(feed.imass['Osteopontin'])
        product_mass = max(product_mass, 0.0)

        volume_l = derived.get('output_volume_l') or derived.get('eluate_volume_l')
        density = derived.get('broth_density_kg_per_l', 1.0)
        if volume_l is not None:
            total_mass = volume_l * density
        else:
            total_mass = feed.F_mass

        eluate.imass['Osteopontin'] = product_mass
        eluate.imass['Yeast'] = 0.0
        eluate.imass['Glucose'] = 0.0

        water_mass = max(total_mass - product_mass, 0.0)
        eluate.imass['Water'] = water_mass

        eluate.T = feed.T
        eluate.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Resin cost per batch"] = derived.get(
            "resin_cost_per_batch", 0.0
        )
        self.design_results["Total buffer bed volumes"] = derived.get(
            "total_buffer_bv", 0.0
        )
        self.design_results["Product out"] = derived.get("product_out_kg", 0.0)
        self.design_results["Output volume"] = derived.get("output_volume_l", 0.0)

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
        feed = self.ins[0]
        concentrated = self.outs[0]
        derived = self.plan.derived

        concentrated.empty()

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = float(feed.imass['Osteopontin'])
        product_mass = max(product_mass, 0.0)

        volume_l = derived.get('output_volume_l')
        density = derived.get('broth_density_kg_per_l', 1.0)
        if volume_l is not None:
            total_mass = volume_l * density
        else:
            total_mass = feed.F_mass

        concentrated.imass['Osteopontin'] = product_mass
        concentrated.imass['Yeast'] = 0.0
        concentrated.imass['Glucose'] = 0.0

        water_mass = max(total_mass - product_mass, 0.0)
        concentrated.imass['Water'] = water_mass

        concentrated.T = feed.T
        concentrated.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Throughput"] = derived.get("throughput_l_per_hr", 0.0)
        self.design_results["Product out"] = derived.get("product_out_kg", 0.0)
        self.design_results["Output volume"] = derived.get("output_volume_l", 0.0)

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
        feed = self.ins[0]
        product = self.outs[0]
        derived = self.plan.derived

        product.empty()

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = float(feed.imass['Osteopontin'])
        product_mass = max(product_mass, 0.0)

        product.imass['Osteopontin'] = product_mass
        product.imass['Water'] = 0.0
        product.imass['Yeast'] = 0.0
        product.imass['Glucose'] = 0.0

        product.T = feed.T
        product.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Capacity"] = derived.get("capacity_kg_per_hr", 0.0)
        self.design_results["Final solids"] = derived.get("final_solids_percent", 0.0)
        self.design_results["Product out"] = derived.get("product_out_kg", 0.0)

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
