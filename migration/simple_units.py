"""Simple placeholder BioSTEAM units that reference Excel-derived plans."""

from __future__ import annotations

from typing import Dict

import biosteam as bst

from .unit_builders import UnitPlan
from biosteam.units.nrel_bioreactor import NRELBatchBioreactor

__all__ = [
    "PlanBackedUnit",
    "SeedTrainBioreactor",
    "FermentationBioreactor",
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


class SeedTrainBioreactor(NRELBatchBioreactor):
    """BioSTEAM batch bioreactor seeded from Excel-derived plan targets."""

    _N_ins = 1
    _N_outs = 2  # vent + broth
    line = "SeedTrain"

    def __init__(self, ID: str, plan: UnitPlan, **kwargs) -> None:
        self.plan = plan
        self.notes = list(plan.notes)
        derived = plan.derived
        tau = derived.get("seed_train_duration_hours") or derived.get("batch_cycle_hours") or 24.0
        working_volume_l = derived.get("working_volume_l") or 3_500.0
        super().__init__(
            ID,
            tau=tau,
            V=working_volume_l / 1_000.0,
            outs=(f"{ID}_vent", f"{ID}_broth"),
            **kwargs,
        )

    def _setup(self) -> None:
        super()._setup()
        vent, broth = self.outs
        vent.phase = "g"
        vent.P = broth.P = self.P
        vent.T = broth.T = self.T

    def _run(self) -> None:
        feed = self.ins[0]
        vent, broth = self.outs
        vent.empty()
        broth.empty()

        derived = self.plan.derived
        conversion_fraction = derived.get("seed_glucose_conversion_fraction") or 0.0
        biomass_yield = derived.get("biomass_yield_glucose") or 0.5

        broth.copy_like(feed)

        try:
            glucose_mass = float(broth.imass["Glucose"])
        except (KeyError, TypeError):
            glucose_mass = 0.0
        converted = max(min(glucose_mass, glucose_mass * conversion_fraction), 0.0)
        if converted > 0.0:
            broth.imass["Glucose"] -= converted
            produced_biomass = converted * biomass_yield
            broth.imass["Yeast"] += produced_biomass
            co2_mass = max(converted - produced_biomass, 0.0)
            if co2_mass > 0.0:
                vent.imass["CO2"] += co2_mass
            broth.imass["Water"] += converted - produced_biomass - co2_mass

        # Ensure nutrient additions match plan-derived totals
        yeast_extract_batch = derived.get("yeast_extract_per_batch_kg")
        if yeast_extract_batch is not None:
            broth.imass["YeastExtract"] = yeast_extract_batch

        peptone_batch = derived.get("peptone_per_batch_kg")
        if peptone_batch is not None:
            broth.imass["Peptone"] = peptone_batch

        working_volume_l = derived.get("working_volume_l")
        if working_volume_l is not None:
            target_mass = working_volume_l
            chemicals = broth.chemicals
            non_water_mass = 0.0
        for index, value in broth.imass.data.dct.items():
            if chemicals.IDs[index] == "Water":
                continue
            non_water_mass += float(value)
        broth.imass["Water"] = max(target_mass - non_water_mass, 0.0)

        vent.T = broth.T = feed.T
        vent.P = broth.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        specs = self.plan.specs
        if derived.get("seed_train_duration_hours"):
            self.tau = derived["seed_train_duration_hours"]
        if derived.get("working_volume_l"):
            self.V = derived["working_volume_l"] / 1_000.0
        super()._design()
        self.design_results.update(
            {
                "Yeast extract concentration": specs.yeast_extract_concentration_g_per_l or 0.0,
                "Peptone concentration": specs.peptone_concentration_g_per_l or 0.0,
                "Total nutrient concentration": derived.get("total_nutrient_concentration_g_per_l") or 0.0,
            }
        )

    def _cost(self) -> None:
        super()._cost()
        specs = self.plan.specs
        derived = self.plan.derived

        volume_l = derived.get("working_volume_l")
        if volume_l is None:
            feed = self.ins[0]
            volume_l = feed.F_mass or feed.F_vol or 0.0

        yeast_mass_kg = derived.get("yeast_extract_per_batch_kg")
        if yeast_mass_kg is None:
            yeast_c = specs.yeast_extract_concentration_g_per_l or 0.0
            yeast_mass_kg = yeast_c * volume_l / 1e3

        peptone_mass_kg = derived.get("peptone_per_batch_kg")
        if peptone_mass_kg is None:
            peptone_c = specs.peptone_concentration_g_per_l or 0.0
            peptone_mass_kg = peptone_c * volume_l / 1e3

        yeast_cost_total = (yeast_mass_kg or 0.0) * (specs.yeast_extract_cost_per_kg or 0.0)
        peptone_cost_total = (peptone_mass_kg or 0.0) * (specs.peptone_cost_per_kg or 0.0)

        self.operating_cost = yeast_cost_total + peptone_cost_total
        self.material_costs = {
            "Yeast extract": yeast_cost_total,
            "Peptone": peptone_cost_total,
        }


class FermentationBioreactor(NRELBatchBioreactor):
    """Batch fermentation unit driven by Excel-derived plan targets."""

    _N_ins = 1
    _N_outs = 2
    line = "Fermentation"

    def __init__(self, ID: str, plan: UnitPlan, **kwargs) -> None:
        self.plan = plan
        self.notes = list(plan.notes)
        derived = plan.derived
        tau = derived.get("batch_cycle_hours") or derived.get("tau_hours") or 72.0
        working_volume_l = derived.get("working_volume_l") or 70_000.0
        super().__init__(
            ID,
            tau=tau,
            V=working_volume_l / 1_000.0,
            outs=(f"{ID}_vent", f"{ID}_broth"),
            **kwargs,
        )

    def _setup(self) -> None:
        super()._setup()
        vent, broth = self.outs
        vent.phase = "g"
        vent.P = broth.P = self.P
        vent.T = broth.T = self.T

    def _run(self) -> None:
        feed = self.ins[0]
        vent, broth = self.outs
        vent.empty()
        broth.empty()

        derived = self.plan.derived

        working_volume_l = derived.get("working_volume_l")
        if working_volume_l is None:
            working_volume_l = feed.F_vol or feed.F_mass or 1_000.0

        density = derived.get("broth_density_kg_per_l", 1.0)
        total_mass = working_volume_l * density

        product_mass = derived.get("product_out_kg")
        if product_mass is None:
            target_titer = derived.get("target_titer_g_per_l") or 0.0
            product_mass = target_titer * working_volume_l / 1_000.0
        product_mass = max(product_mass or 0.0, 0.0)

        dcw_conc = derived.get("dcw_concentration_g_per_l") or 0.0
        biomass_mass = dcw_conc * working_volume_l / 1_000.0

        residual_glucose = (
            derived.get("residual_glucose_g_per_l")
            or derived.get("residual_glucose_after_fermentation_g_per_l")
            or 0.0
        )
        residual_glucose_mass = residual_glucose * working_volume_l / 1_000.0

        if product_mass > 0.0:
            broth.imass["Osteopontin"] = product_mass
        if biomass_mass > 0.0:
            broth.imass["Yeast"] = biomass_mass
        if residual_glucose_mass > 0.0:
            broth.imass["Glucose"] = residual_glucose_mass

        known_mass = product_mass + biomass_mass + residual_glucose_mass
        water_mass = max(total_mass - known_mass, 0.0)
        broth.imass["Water"] = water_mass

        broth.T = feed.T
        broth.P = feed.P
        vent.T = feed.T
        vent.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        if derived.get("batch_cycle_hours"):
            self.tau = derived["batch_cycle_hours"]
        if derived.get("working_volume_l"):
            self.V = derived["working_volume_l"] / 1_000.0
        super()._design()
        self.design_results.update(
            {
                "Product yield on glucose": derived.get("product_yield_glucose", 0.0),
                "Working volume": derived.get("working_volume_l", 0.0),
                "Target titer": derived.get("target_titer_g_per_l", 0.0),
                "DCW concentration": derived.get("dcw_concentration_g_per_l", 0.0),
                "Glucose feed per batch": derived.get("total_glucose_feed_kg", 0.0),
            }
        )

    def _cost(self) -> None:
        super()._cost()


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
