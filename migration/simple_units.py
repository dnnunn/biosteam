"""Simple placeholder BioSTEAM units that reference Excel-derived plans."""

from __future__ import annotations

from typing import Dict

import biosteam as bst

from .unit_builders import UnitPlan
from biosteam.units.nrel_bioreactor import NRELBatchBioreactor
from biosteam.units.design_tools.batch import size_batch

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


def _component_mass(stream: bst.Stream, component: str) -> float:
    """Safely fetch component mass from a stream."""

    try:
        return float(stream.imass[component])
    except (KeyError, AttributeError, TypeError):
        return 0.0


def _total_mass(stream: bst.Stream) -> float:
    """Return total mass flow for convenience."""

    try:
        mass = float(stream.F_mass)
        if mass:
            return mass
    except (AttributeError, TypeError, ValueError):
        pass

    total = 0.0
    imass = getattr(stream, "imass", None)
    if imass is None:
        return 0.0

    if hasattr(imass, "items"):
        for _, value in imass.items():
            try:
                total += float(value)
            except (TypeError, ValueError):
                continue
    elif hasattr(imass, "sum"):
        try:
            total = float(imass.sum())
        except (TypeError, ValueError):
            total = 0.0
    return total


def _infer_density(stream: bst.Stream, default: float | None = None) -> float:
    """Estimate broth density (kg/L) from plan hints or stream data."""

    if default and default > 0.0:
        return default

    try:
        mass = float(stream.F_mass)
        volume = float(stream.F_vol)
        if volume > 0.0:
            return max(mass / volume, 1e-6)
    except (AttributeError, TypeError, ZeroDivisionError):
        pass

    return 1.0


def _membrane_cost(cost_per_area: float | None, area_m2: float | None, lifetime: float | None) -> float | None:
    """Return per-cycle membrane cost if enough data is available."""

    if not cost_per_area or not area_m2 or cost_per_area <= 0.0 or area_m2 <= 0.0:
        return None
    if not lifetime or lifetime <= 0.0:
        return cost_per_area * area_m2
    return (cost_per_area * area_m2) / lifetime


def _fallback_volumetric_flow(
    derived: Dict[str, float],
    *,
    volume_key: str,
    cycle_keys: tuple[str, ...],
    default_tau: float,
) -> float | None:
    """Compute a positive volumetric flow rate (m3/hr) from plan metadata."""

    working_volume_l = derived.get(volume_key)
    if not working_volume_l:
        return None

    cycle_hours = None
    for key in cycle_keys:
        value = derived.get(key)
        if value:
            cycle_hours = value
            break

    if not cycle_hours:
        cycle_hours = default_tau if default_tau else None

    if not cycle_hours or cycle_hours <= 0.0:
        return None

    return (working_volume_l / 1_000.0) / cycle_hours


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
        module = option = "<placeholder>"
        if getattr(self, "plan", None) is not None and getattr(self.plan, "key", None) is not None:
            module = self.plan.key.module or module
            option = self.plan.key.option or option
        summary.update({
            "module": module,
            "option": option,
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
        self.autoselect_N = False

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
        glucose_feed = _component_mass(feed, "Glucose")
        biomass_yield = derived.get("biomass_yield_glucose")
        if not biomass_yield:
            # Fallback to the fermentation default if the plan did not carry the value.
            biomass_yield = 0.48

        initial_biomass = _component_mass(feed, "Yeast")
        working_volume_l = derived.get("working_volume_l")
        if working_volume_l is None:
            working_volume_l = feed.F_vol or feed.F_mass or 0.0
        dcw_concentration = derived.get("dcw_concentration_g_per_l")
        if dcw_concentration and working_volume_l:
            target_biomass = dcw_concentration * working_volume_l / 1_000.0
        else:
            target_biomass = initial_biomass

        growth_needed = max(target_biomass - initial_biomass, 0.0)
        converted = 0.0
        produced_biomass = 0.0
        if biomass_yield and biomass_yield > 0.0 and glucose_feed > 0.0:
            glucose_required = growth_needed / biomass_yield
            converted = min(glucose_feed, glucose_required)
            produced_biomass = converted * biomass_yield
        final_biomass = initial_biomass + produced_biomass

        residual_glucose_mass = max(glucose_feed - converted, 0.0)

        if residual_glucose_mass > 0.0:
            broth.imass["Glucose"] = residual_glucose_mass
        if final_biomass > 0.0:
            broth.imass["Yeast"] = final_biomass

        co2_mass = max(converted - produced_biomass, 0.0)
        if co2_mass > 0.0:
            vent.imass["CO2"] = co2_mass

        # Nutrient additions default to the concentrations carried in the plan specs.
        specs = self.plan.specs

        yeast_extract_batch = derived.get("yeast_extract_per_batch_kg")
        if yeast_extract_batch is None:
            conc = getattr(specs, "yeast_extract_concentration_g_per_l", None)
            if conc and working_volume_l:
                yeast_extract_batch = conc * working_volume_l / 1_000.0
            else:
                yeast_extract_batch = _component_mass(feed, "YeastExtract")
        if yeast_extract_batch:
            broth.imass["YeastExtract"] = yeast_extract_batch

        peptone_batch = derived.get("peptone_per_batch_kg")
        if peptone_batch is None:
            conc = getattr(specs, "peptone_concentration_g_per_l", None)
            if conc and working_volume_l:
                peptone_batch = conc * working_volume_l / 1_000.0
            else:
                peptone_batch = _component_mass(feed, "Peptone")
        if peptone_batch:
            broth.imass["Peptone"] = peptone_batch

        density = derived.get("broth_density_kg_per_l") or 1.0
        target_mass = working_volume_l * density if working_volume_l else 0.0
        if not target_mass:
            target_mass = (
                yeast_extract_batch
                + peptone_batch
                + final_biomass
                + residual_glucose_mass
            )

        chemicals = broth.chemicals
        non_water_mass = 0.0
        if chemicals is not None and hasattr(broth.imass, "data"):
            for index, value in broth.imass.data.dct.items():
                component = chemicals.IDs[index]
                if component == "Water":
                    continue
                non_water_mass += float(value)
        else:
            for component, value in broth.imass.items():
                if component == "Water":
                    continue
                try:
                    non_water_mass += float(value)
                except (TypeError, ValueError):
                    continue

        water_mass = max(target_mass - non_water_mass, 0.0)
        if water_mass:
            broth.imass["Water"] = water_mass

        vent.T = broth.T = feed.T
        vent.P = broth.P = feed.P

        derived["working_volume_l"] = working_volume_l
        derived["broth_density_kg_per_l"] = density
        derived["yeast_extract_per_batch_kg"] = _component_mass(broth, "YeastExtract")
        derived["peptone_per_batch_kg"] = _component_mass(broth, "Peptone")
        derived["seed_glucose_consumed_kg"] = converted
        derived["seed_residual_glucose_kg"] = residual_glucose_mass
        derived["biomass_out_kg"] = _component_mass(broth, "Yeast")
        if glucose_feed > 0.0:
            derived["seed_glucose_conversion_fraction"] = converted / glucose_feed

    def _design(self) -> None:
        derived = self.plan.derived
        specs = self.plan.specs
        if derived.get("seed_train_duration_hours"):
            self.tau = derived["seed_train_duration_hours"]
        if derived.get("working_volume_l"):
            self.V = derived["working_volume_l"] / 1_000.0
        try:
            super()._design()
        except ZeroDivisionError:
            fallback_F_vol = _fallback_volumetric_flow(
                derived,
                volume_key="working_volume_l",
                cycle_keys=("seed_train_duration_hours", "batch_cycle_hours", "tau_hours"),
                default_tau=self.tau,
            )
            v_0 = fallback_F_vol or 1e-6
            tau = self._tau or self.tau or 1.0
            tau_cleaning = self.tau_0
            V_wf = self.V_wf or 0.75
            N = max(int(self._N or 2), 2)
            design = size_batch(v_0, tau, tau_cleaning, N, V_wf)
            self.design_results.update(design)
            self.design_results["Number of reactors"] = N
            self.design_results["Recirculation flow rate"] = v_0 / N
            duty = self.Hnet
            self.design_results["Reactor duty"] = duty
            self.add_heat_utility(duty, self.T)
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
        if working_volume_l is None or working_volume_l <= 0.0:
            working_volume_l = feed.F_vol or feed.F_mass or 1_000.0

        cycle_hours = derived.get("batch_cycle_hours") or derived.get("tau_hours")
        if cycle_hours is None or cycle_hours <= 0.0:
            cycle_hours = self.tau or 1.0
        avg_feed_vol_m3_per_hr = (working_volume_l / 1_000.0) / cycle_hours if working_volume_l else 0.0

        density = derived.get("broth_density_kg_per_l")
        if density is None or density <= 0.0:
            density = 1.05
            derived.setdefault("broth_density_kg_per_l", density)
        total_mass = working_volume_l * density

        specs = self.plan.specs

        od_to_dcw = derived.get("od_to_dcw_g_per_l_per_od")
        od_target = derived.get("od600_target")
        dcw_conc = derived.get("dcw_concentration_g_per_l")
        if od_target and od_to_dcw:
            dcw_conc = od_target * od_to_dcw
            derived["dcw_concentration_g_per_l"] = dcw_conc
        final_biomass = 0.0
        if dcw_conc and working_volume_l:
            final_biomass = dcw_conc * working_volume_l / 1_000.0

        initial_biomass = derived.get("initial_biomass_kg")
        if initial_biomass is None:
            initial_biomass = _component_mass(feed, "Yeast")
            derived["initial_biomass_kg"] = initial_biomass

        delta_x = max(final_biomass - (initial_biomass or 0.0), 0.0)
        x_avg = 0.5 * (final_biomass + (initial_biomass or 0.0))

        biomass_yield = getattr(specs, "biomass_yield_glucose", None)
        if not biomass_yield:
            biomass_yield = derived.get("biomass_yield_glucose")
        if not biomass_yield or biomass_yield <= 0.0:
            biomass_yield = 0.48

        maintenance_coeff = derived.get("maintenance_coefficient_g_glucose_per_gdcw_h")
        if maintenance_coeff is None:
            maintenance_coeff = 0.0

        loss_fraction = derived.get("loss_fraction_glucose") or 0.0

        s_growth = delta_x / biomass_yield if biomass_yield > 0.0 else 0.0
        s_maint = maintenance_coeff * x_avg * cycle_hours if maintenance_coeff else 0.0
        s_total = (s_growth + s_maint) * (1.0 + loss_fraction)

        product_model = (derived.get("product_model") or "").lower()
        yp_x = derived.get("product_yield_biomass")
        if yp_x is None:
            yp_x = getattr(specs, "product_yield_biomass", None)
        qp = derived.get("specific_productivity_g_per_gdcw_h")
        if qp is None:
            qp = getattr(specs, "specific_productivity_g_per_gdcw_h", None)

        product_mass_growth = (yp_x or 0.0) * delta_x if yp_x else 0.0
        product_mass_qp = (qp or 0.0) * x_avg * cycle_hours if qp else 0.0

        if product_model in {"specific_productivity", "qp"} and qp:
            product_mass = product_mass_qp
            selected_model = "specific_productivity"
        elif product_model in {"growth_associated", "yield"} and yp_x:
            product_mass = product_mass_growth
            selected_model = "growth_associated"
        elif qp:
            product_mass = product_mass_qp
            selected_model = "specific_productivity"
        else:
            product_mass = product_mass_growth
            selected_model = "growth_associated"

        if product_mass > 0.0:
            broth.imass["Osteopontin"] = product_mass
        if final_biomass > 0.0:
            broth.imass["Yeast"] = final_biomass

        non_water_mass = product_mass + final_biomass
        water_mass = max(total_mass - non_water_mass, 0.0)
        if water_mass > 0.0:
            broth.imass["Water"] = water_mass

        derived["product_out_kg"] = product_mass
        derived["product_mass_growth_model_kg"] = product_mass_growth
        derived["product_mass_qp_model_kg"] = product_mass_qp
        derived["product_model"] = selected_model
        derived["glucose_for_growth_kg"] = s_growth
        derived["glucose_for_maintenance_kg"] = s_maint
        derived["glucose_losses_fraction"] = loss_fraction
        derived["total_glucose_feed_kg"] = s_total
        derived["glucose_consumed_kg"] = s_total
        derived["glucose_for_product_kg"] = 0.0
        derived["working_volume_l"] = working_volume_l
        derived["broth_density_kg_per_l"] = density
        derived["biomass_out_kg"] = final_biomass
        derived["delta_biomass_kg"] = delta_x
        derived["average_biomass_kg"] = x_avg

        titer = (
            product_mass * 1_000.0 / working_volume_l
            if working_volume_l
            else 0.0
        )
        derived["product_titer_g_per_l"] = titer
        derived["residual_glucose_after_fermentation_g_per_l"] = 0.0

        nitrogen_req = derived.get("nitrogen_requirement_g_per_gdcw") or 0.0
        nh4oh_ratio = derived.get("nh4oh_kg_per_kg_n") or 1.0
        nitrogen_required_kg = nitrogen_req * delta_x
        nh4oh_consumption_kg = nitrogen_required_kg * nh4oh_ratio
        derived["nitrogen_required_kg"] = nitrogen_required_kg
        derived["nh3_consumption_kg"] = nh4oh_consumption_kg
        derived["pH_base_consumption_kg"] = nh4oh_consumption_kg
        derived["validator_titer_decoupled"] = "Titer is not used in glucose calc (decoupled)."
        derived["validator_maintenance_note"] = (
            f"Maintenance term included: m_s = {maintenance_coeff:g} g/(gDCW·h)."
        )
        if qp:
            derived["validator_productivity_note"] = (
                f"Specific productivity model active (qp = {qp:g} g/(gDCW·h))."
            )
        else:
            derived.pop("validator_productivity_note", None)

        # Ensure downstream units see the plan-aligned composition even if upstream
        # overrides were applied before simulation.
        original_product = _component_mass(broth, "Osteopontin")
        derived["debug_original_broth_opn_kg"] = original_product

        final_product = derived.get("product_out_kg")
        if final_product is not None:
            broth.empty()
            broth.imass["Osteopontin"] = final_product
            broth.imass["Yeast"] = final_biomass
            broth.imass["Water"] = max(total_mass - (final_product + final_biomass), 0.0)
            derived["debug_stream_product_kg"] = float(final_product)
            derived["debug_broth_opn_after_kg"] = float(broth.imass["Osteopontin"])
        else:
            derived.pop("debug_stream_product_kg", None)
            derived.pop("debug_broth_opn_after_kg", None)
        if avg_feed_vol_m3_per_hr > 0.0:
            self._F_vol_in = avg_feed_vol_m3_per_hr

        handoff_stream = getattr(self, "_handoff_stream", None)
        if handoff_stream is not None:
            handoff_stream.copy_like(broth)
        report_stream = getattr(self, "_handoff_report_stream", None)
        if report_stream is not None:
            report_stream.copy_like(broth)

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
        try:
            super()._design()
        except ZeroDivisionError:
            fallback_F_vol = _fallback_volumetric_flow(
                derived,
                volume_key="working_volume_l",
                cycle_keys=("batch_cycle_hours", "tau_hours"),
                default_tau=self.tau,
            )
            v_0 = fallback_F_vol or 1e-6
            tau = self._tau or self.tau or 1.0
            tau_cleaning = self.tau_0
            V_wf = self.V_wf or 0.75
            N = max(int(self._N or 2), 2)
            design = size_batch(v_0, tau, tau_cleaning, N, V_wf)
            self.design_results.update(design)
            self.design_results["Number of reactors"] = N
            self.design_results["Recirculation flow rate"] = v_0 / N
            duty = self.Hnet
            self.design_results["Reactor duty"] = duty
            self.add_heat_utility(duty, self.T)
        self.design_results.update(
            {
                "Glucose for growth": derived.get("glucose_for_growth_kg", 0.0),
                "Glucose for maintenance": derived.get("glucose_for_maintenance_kg", 0.0),
                "Total glucose demand": derived.get("total_glucose_feed_kg", 0.0),
                "Working volume": derived.get("working_volume_l", 0.0),
                "Target titer": derived.get("target_titer_g_per_l", 0.0),
                "DCW concentration": derived.get("dcw_concentration_g_per_l", 0.0),
            }
        )

    def _cost(self) -> None:
        super()._cost()


class MicrofiltrationUnit(PlanBackedUnit):
    """Microfiltration step with permeate and retentate streams."""

    _N_ins = 1
    _N_outs = 2
    line = "Microfiltration"

    _units = {
        "Throughput": "L/hr",
        "Membrane cost per cycle": "USD",
        "Dilution volume": "m3",
        "Input volume": "L",
        "Output volume": "L",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        permeate, retentate = self.outs
        derived = self.plan.derived
        specs = self.plan.specs

        permeate.empty()
        retentate.empty()

        density = _infer_density(feed, derived.get('broth_density_kg_per_l'))

        input_product = _component_mass(feed, 'Osteopontin')
        derived['input_product_kg'] = input_product

        recovery_fraction = None
        if specs is not None:
            recovery = getattr(specs, 'product_recovery_fraction', None)
            if recovery is not None:
                recovery_fraction = max(min(recovery, 1.0), 0.0)
            if recovery_fraction is None:
                loss = getattr(specs, 'target_product_loss', None)
                if loss is not None:
                    recovery_fraction = max(1.0 - max(loss, 0.0), 0.0)
            if recovery_fraction is None:
                efficiency = getattr(specs, 'efficiency', None)
                if efficiency is not None:
                    recovery_fraction = max(min(max(efficiency, 0.0), 1.0), 0.0)
        if recovery_fraction is None:
            recovery_fraction = 1.0

        product_mass = max(input_product * recovery_fraction, 0.0)

        holdup_loss = None
        if specs is not None:
            holdup_loss = getattr(specs, 'holdup_loss_kg', None)
        if holdup_loss is None:
            holdup_loss = derived.get('holdup_loss_kg')
        if holdup_loss is not None and holdup_loss > 0.0:
            product_mass = max(product_mass - holdup_loss, 0.0)
            derived['holdup_loss_kg'] = holdup_loss
        else:
            derived.pop('holdup_loss_kg', None)

        residual_glucose = _component_mass(feed, 'Glucose')
        derived['residual_glucose_after_mf_kg'] = residual_glucose

        yeast_mass = _component_mass(feed, 'Yeast')

        area = getattr(specs, 'membrane_area_m2', None) if specs is not None else None
        flux = getattr(specs, 'flux_l_m2_h', None) if specs is not None else None
        if area and flux:
            derived['throughput_l_per_hr'] = area * flux
        else:
            derived.pop('throughput_l_per_hr', None)

        dilution_l = getattr(specs, 'dilution_volume_l', None) if specs is not None else None
        if dilution_l is not None:
            derived['dilution_volume_m3'] = dilution_l / 1_000.0
        else:
            derived.pop('dilution_volume_m3', None)

        cost_per_cycle = _membrane_cost(
            getattr(specs, 'membrane_cost', None) if specs is not None else None,
            area,
            getattr(specs, 'membrane_lifetime', None) if specs is not None else None,
        )
        if cost_per_cycle is not None:
            derived['membrane_cost_per_cycle'] = cost_per_cycle
        else:
            derived.pop('membrane_cost_per_cycle', None)

        feed_total_mass = _total_mass(feed)
        input_volume_l = derived.get('input_volume_l') or derived.get('harvest_volume_l')
        if (input_volume_l is None or input_volume_l <= 0.0) and density > 0.0 and feed_total_mass > 0.0:
            input_volume_l = feed_total_mass / density
        if input_volume_l is not None and input_volume_l > 0.0:
            derived['input_volume_l'] = input_volume_l
        else:
            derived.pop('input_volume_l', None)

        output_volume_l = derived.get('output_volume_l')
        if dilution_l is not None and input_volume_l is not None:
            output_volume_l = input_volume_l + dilution_l
        if output_volume_l is not None and output_volume_l > 0.0:
            derived['output_volume_l'] = output_volume_l
        else:
            derived.pop('output_volume_l', None)

        derived['product_out_kg'] = product_mass
        derived['harvested_product_kg'] = product_mass
        derived['broth_density_kg_per_l'] = density

        if product_mass > 0.0:
            permeate.imass['Osteopontin'] = product_mass
        if residual_glucose > 0.0:
            permeate.imass['Glucose'] = residual_glucose

        permeate_total_mass = None
        if output_volume_l is not None:
            permeate_total_mass = output_volume_l * density
        if not permeate_total_mass or permeate_total_mass <= 0.0:
            permeate_total_mass = product_mass + residual_glucose

        known_permeate = product_mass + residual_glucose
        permeate_water = max(permeate_total_mass - known_permeate, 0.0)
        if permeate_water > 0.0:
            permeate.imass['Water'] = permeate_water

        retentate_product = max(input_product - product_mass, 0.0)
        if retentate_product > 0.0:
            retentate.imass['Osteopontin'] = retentate_product
        if yeast_mass > 0.0:
            retentate.imass['Yeast'] = yeast_mass

        retentate_total_mass = max(feed_total_mass - permeate_total_mass, 0.0)
        known_retentate = retentate_product + yeast_mass
        retentate_water = max(retentate_total_mass - known_retentate, 0.0)
        if retentate_water > 0.0:
            retentate.imass['Water'] = retentate_water

        permeate.T = feed.T
        permeate.P = feed.P
        retentate.T = feed.T
        retentate.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results['Throughput'] = derived.get('throughput_l_per_hr', 0.0)
        self.design_results['Membrane cost per cycle'] = derived.get('membrane_cost_per_cycle', 0.0)
        self.design_results['Dilution volume'] = derived.get('dilution_volume_m3', 0.0)
        self.design_results['Input volume'] = derived.get('input_volume_l', 0.0)
        self.design_results['Output volume'] = derived.get('output_volume_l', 0.0)
        self.design_results['Product out'] = derived.get('product_out_kg', 0.0)
        self.design_results['Harvested product'] = derived.get('harvested_product_kg', 0.0)

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
        cost_per_cycle = self.plan.derived.get('membrane_cost_per_cycle')
        if cost_per_cycle:
            self.operating_cost = cost_per_cycle
            self.material_costs = {'MF membranes': cost_per_cycle}
        else:
            self.operating_cost = 0.0
            self.material_costs = {}


class UFDFUnit(PlanBackedUnit):
    """Ultrafiltration / diafiltration step with waste and product streams."""

    _N_ins = 1
    _N_outs = 2
    line = "UF/DF"

    _units = {
        "Throughput": "L/hr",
        "Diafiltration volumes": "vol",
        "Membrane cost per cycle": "USD",
        "Input volume": "L",
        "Output volume": "L",
        "Concentration factor": "-",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product_stream, waste_stream = self.outs
        derived = self.plan.derived
        specs = self.plan.specs

        feed_T = feed.T
        feed_P = feed.P
        chemicals = getattr(feed, 'chemicals', None)
        component_ids = chemicals.IDs if chemicals is not None else ()
        initial_masses = {component: float(feed.imass[component]) for component in component_ids}
        feed_total_mass = sum(initial_masses.values())

        feed_snapshot = feed.copy()
        feed_snapshot.mol = feed_snapshot.mol.copy()

        product_snapshot = feed_snapshot.copy()
        product_snapshot.mol = product_snapshot.mol.copy()
        product_snapshot.empty()

        waste_snapshot = feed_snapshot.copy()
        waste_snapshot.mol = waste_snapshot.mol.copy()
        waste_snapshot.empty()

        density = _infer_density(feed, derived.get('broth_density_kg_per_l'))

        input_product = derived.get('input_product_kg')
        if input_product is None:
            input_product = initial_masses.get('Osteopontin', 0.0)
        input_product = max(float(input_product or 0.0), 0.0)
        derived['input_product_kg'] = input_product

        efficiency = None
        if specs is not None:
            eff = getattr(specs, 'efficiency', None)
            if eff is not None:
                efficiency = max(min(max(eff, 0.0), 1.0), 0.0)
        if efficiency is None:
            efficiency = 1.0

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = input_product * efficiency
        product_mass = max(float(product_mass or 0.0), 0.0)

        input_volume_l = derived.get('input_volume_l')
        if (input_volume_l is None or input_volume_l <= 0.0) and density > 0.0:
            if feed_total_mass > 0.0:
                input_volume_l = feed_total_mass / density
        if input_volume_l is not None and input_volume_l > 0.0:
            derived['input_volume_l'] = input_volume_l
        else:
            derived.pop('input_volume_l', None)

        concentration_factor = getattr(specs, 'concentration_factor', None) if specs is not None else None
        output_volume_l = derived.get('output_volume_l')
        if concentration_factor and concentration_factor > 0.0 and input_volume_l:
            output_volume_l = input_volume_l / concentration_factor
        if output_volume_l is not None and output_volume_l > 0.0:
            derived['output_volume_l'] = output_volume_l
        else:
            derived.pop('output_volume_l', None)

        area = getattr(specs, 'membrane_area_m2', None) if specs is not None else None
        flux = getattr(specs, 'flux_l_m2_h', None) if specs is not None else None
        if area and flux:
            derived['throughput_l_per_hr'] = area * flux
        else:
            derived.pop('throughput_l_per_hr', None)

        dia_volumes = getattr(specs, 'diafiltration_volumes', None) if specs is not None else None
        if dia_volumes is not None:
            derived['diafiltration_volumes'] = dia_volumes
        else:
            derived.pop('diafiltration_volumes', None)

        cost_per_cycle = _membrane_cost(
            getattr(specs, 'membrane_cost', None) if specs is not None else None,
            area,
            getattr(specs, 'membrane_lifetime', None) if specs is not None else None,
        )
        if cost_per_cycle is not None:
            derived['membrane_cost_per_cycle'] = cost_per_cycle
        else:
            derived.pop('membrane_cost_per_cycle', None)

        if output_volume_l is not None and output_volume_l > 0.0:
            product_total_mass = output_volume_l * density
        else:
            product_total_mass = product_mass

        for component, mass in initial_masses.items():
            if component in {'Osteopontin', 'Water'}:
                continue
            if mass:
                product_snapshot.imass[component] = mass

        product_snapshot.imass['Osteopontin'] = product_mass
        product_snapshot.imass['Water'] = max(product_total_mass - product_mass, 0.0)

        waste_product = max(input_product - product_mass, 0.0)
        if waste_product > 0.0:
            waste_snapshot.imass['Osteopontin'] = waste_product

        waste_total_mass = max(feed_total_mass - product_total_mass, 0.0)
        waste_snapshot.imass['Water'] = max(waste_total_mass - waste_product, 0.0)

        derived['product_out_kg'] = product_mass
        derived['broth_density_kg_per_l'] = density

        for stream in (product_snapshot, waste_snapshot):
            stream.T = feed_T
            stream.P = feed_P

        product_stream.copy_like(product_snapshot)
        waste_stream.copy_like(waste_snapshot)

    def _design(self) -> None:
        derived = self.plan.derived
        specs = self.plan.specs
        self.design_results['Throughput'] = derived.get('throughput_l_per_hr', 0.0)
        self.design_results['Diafiltration volumes'] = derived.get('diafiltration_volumes', 0.0)
        self.design_results['Membrane cost per cycle'] = derived.get('membrane_cost_per_cycle', 0.0)
        self.design_results['Input volume'] = derived.get('input_volume_l', 0.0)
        self.design_results['Output volume'] = derived.get('output_volume_l', 0.0)
        self.design_results['Product out'] = derived.get('product_out_kg', 0.0)
        if getattr(specs, 'concentration_factor', None) is not None:
            self.design_results['Concentration factor'] = specs.concentration_factor

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
        cost_per_cycle = self.plan.derived.get('membrane_cost_per_cycle')
        if cost_per_cycle:
            self.operating_cost = cost_per_cycle
            self.material_costs = {'UF/DF membranes': cost_per_cycle}
        else:
            self.operating_cost = 0.0
            self.material_costs = {}


class ChromatographyUnit(PlanBackedUnit):
    """Chromatography step with product and waste streams, tracking buffer usage."""

    _N_ins = 1
    _N_outs = 2
    line = "Chromatography"

    _units = {
        "Resin cost per batch": "USD",
        "Total buffer bed volumes": "CV",
        "Eluate volume": "L",
        "Output volume": "L",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product_stream, waste_stream = self.outs
        derived = self.plan.derived
        specs = self.plan.specs

        product_stream.empty()
        waste_stream.empty()

        density = derived.get('broth_density_kg_per_l') or 1.0

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = _component_mass(feed, 'Osteopontin')
        product_mass = max(product_mass or 0.0, 0.0)

        output_volume_l = derived.get('output_volume_l') or derived.get('post_elution_conc_volume_l')
        if output_volume_l is not None:
            product_total_mass = output_volume_l * density
        else:
            product_total_mass = product_mass

        product_stream.imass['Osteopontin'] = product_mass
        product_water = max(product_total_mass - product_mass, 0.0)
        if product_water:
            product_stream.imass['Water'] = product_water

        input_product = derived.get('input_product_kg')
        if input_product is None:
            input_product = _component_mass(feed, 'Osteopontin')
        waste_product = max((input_product or 0.0) - product_mass, 0.0)
        if waste_product:
            waste_stream.imass['Osteopontin'] = waste_product

        eluate_volume_l = derived.get('eluate_volume_l')
        if eluate_volume_l is None and getattr(specs, 'resin_column_volume_l', None) is not None:
            total_buffer_bv = derived.get('total_buffer_bv')
            if total_buffer_bv is not None:
                eluate_volume_l = specs.resin_column_volume_l * total_buffer_bv
        if eluate_volume_l is not None:
            eluate_total_mass = eluate_volume_l * density
        else:
            eluate_total_mass = product_total_mass + waste_product

        waste_water = max(eluate_total_mass - (product_total_mass + waste_product), 0.0)
        if waste_water:
            waste_stream.imass['Water'] = waste_water

        product_stream.T = feed.T
        product_stream.P = feed.P
        waste_stream.T = feed.T
        waste_stream.P = feed.P

        handoff = getattr(self, "_handoff_stream", None)
        if handoff is not None:
            handoff.copy_like(product_stream)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(product_stream)

    def _design(self) -> None:
        derived = self.plan.derived
        specs = self.plan.specs
        self.design_results['Resin cost per batch'] = derived.get('resin_cost_per_batch', 0.0)
        self.design_results['Total buffer bed volumes'] = derived.get('total_buffer_bv', 0.0)
        self.design_results['Eluate volume'] = derived.get('eluate_volume_l', 0.0)
        self.design_results['Output volume'] = derived.get('output_volume_l', 0.0)
        if getattr(specs, 'resin_column_volume_l', None) is not None:
            self.design_results['Resin column volume'] = specs.resin_column_volume_l
        if derived.get('buffer_cost_per_batch') is not None:
            self.design_results['Buffer cost per batch'] = derived['buffer_cost_per_batch']

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
        resin_cost = self.plan.derived.get('resin_cost_per_batch') or 0.0
        buffer_cost = self.plan.derived.get('buffer_cost_per_batch') or 0.0
        total_cost = resin_cost + buffer_cost
        self.operating_cost = total_cost
        self.material_costs = {}
        if resin_cost:
            self.material_costs['Resin'] = resin_cost
        if buffer_cost:
            self.material_costs['Buffers'] = buffer_cost


class PreDryingUnit(PlanBackedUnit):
    """Pre-drying TFF step with concentrate and waste streams."""

    _N_ins = 1
    _N_outs = 2
    line = "PreDrying"

    _units = {
        "Throughput": "L/hr",
        "Membrane cost per cycle": "USD",
        "Input volume": "L",
        "Output volume": "L",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product_stream, waste_stream = self.outs
        derived = self.plan.derived

        product_stream.empty()
        waste_stream.empty()

        product_mass = derived.get('product_out_kg')
        if product_mass is None:
            product_mass = _component_mass(feed, 'Osteopontin')
        product_mass = max(product_mass or 0.0, 0.0)

        volume_l = derived.get('output_volume_l')
        density = derived.get('broth_density_kg_per_l', 1.0)
        if volume_l is not None:
            total_mass = float(volume_l) * density
        else:
            total_mass = _total_mass(feed)
            if total_mass <= 0.0:
                total_mass = product_mass

        product_stream.imass['Osteopontin'] = product_mass
        product_stream.imass['Water'] = max(total_mass - product_mass, 0.0)

        input_product = derived.get('input_product_kg')
        if input_product is None:
            input_product = _component_mass(feed, 'Osteopontin')
        input_product = max(input_product or 0.0, 0.0)

        waste_product = max(input_product - product_mass, 0.0)
        if waste_product:
            waste_stream.imass['Osteopontin'] = waste_product

        input_volume_l = derived.get('input_volume_l')
        if input_volume_l is not None:
            feed_mass = float(input_volume_l) * density
        else:
            feed_mass = _total_mass(feed)
            if feed_mass <= 0.0:
                feed_mass = product_stream.F_mass + waste_product

        waste_water = max(feed_mass - product_stream.F_mass - waste_product, 0.0)
        if waste_water:
            waste_stream.imass['Water'] = waste_water

        product_stream.T = feed.T
        product_stream.P = feed.P
        waste_stream.T = feed.T
        waste_stream.P = feed.P

        handoff = getattr(self, "_handoff_stream", None)
        if handoff is not None:
            handoff.copy_like(product_stream)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(product_stream)

    def _design(self) -> None:
        derived = self.plan.derived
        specs = self.plan.specs
        self.design_results["Throughput"] = derived.get("throughput_l_per_hr", 0.0)
        self.design_results["Product out"] = derived.get("product_out_kg", 0.0)
        self.design_results["Input volume"] = derived.get("input_volume_l", 0.0)
        self.design_results["Output volume"] = derived.get("output_volume_l", 0.0)
        if getattr(specs, 'concentration_factor', None) is not None:
            self.design_results['Concentration factor'] = specs.concentration_factor

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
        cost_per_cycle = self.plan.derived.get('membrane_cost_per_cycle')
        if cost_per_cycle:
            self.operating_cost = cost_per_cycle
            self.material_costs = {'PreDry TFF membranes': cost_per_cycle}
        else:
            self.operating_cost = 0.0
            self.material_costs = {}


class SprayDryerUnit(PlanBackedUnit):
    """Spray dryer with product and exhaust streams."""

    _N_ins = 1
    _N_outs = 2
    line = "SprayDryer"

    _units = {
        "Capacity": "kg/hr",
        "Final solids": "%",
        "Final solids mass fraction": "-",
        "Input density": "kg/L",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product_stream, exhaust_stream = self.outs
        derived = self.plan.derived

        feed_T = feed.T
        feed_P = feed.P
        feed_snapshot = feed.copy()
        feed_snapshot.mol = feed_snapshot.mol.copy()

        product_snapshot = feed_snapshot.copy()
        product_snapshot.mol = product_snapshot.mol.copy()
        product_snapshot.empty()

        exhaust_snapshot = feed_snapshot.copy()
        exhaust_snapshot.mol = exhaust_snapshot.mol.copy()
        exhaust_snapshot.empty()

        feed_product_measured = _component_mass(feed, 'Osteopontin')
        feed_total_measured = _total_mass(feed)
        feed_water_measured = _component_mass(feed, 'Water')

        input_product = derived.get('input_product_kg')
        if input_product is None:
            input_product = feed_product_measured
        if input_product is None:
            input_product = 0.0
        input_product = max(float(input_product), 0.0)

        feed_total = feed_total_measured
        if feed_total <= 0.0:
            input_volume_l = derived.get('input_volume_l')
            density = derived.get('solution_density')
            try:
                if input_volume_l is not None and density is not None:
                    feed_total = float(input_volume_l) * float(density)
            except (TypeError, ValueError):
                feed_total = 0.0
        feed_total = max(feed_total, input_product)

        feed_water = feed_water_measured
        if feed_water <= 0.0:
            feed_water = max(feed_total - input_product, 0.0)

        recovery = 1.0
        eff = derived.get('spray_dryer_efficiency')
        target_recovery = derived.get('target_recovery_rate')
        for value in (eff, target_recovery):
            if value is None:
                continue
            try:
                frac = float(value)
            except (TypeError, ValueError):
                continue
            if frac <= 0.0:
                continue
            recovery *= frac
        recovery = max(min(recovery, 1.0), 0.0)

        recovered_product = input_product * recovery if input_product else 0.0

        solids_fraction = derived.get('final_solids_content')
        if solids_fraction is None or solids_fraction <= 0.0:
            percent = derived.get('final_solids_percent')
            try:
                solids_fraction = float(percent) / 100.0 if percent else None
            except (TypeError, ValueError):
                solids_fraction = None
        if solids_fraction is None or solids_fraction <= 0.0:
            solids_fraction = 1.0
        solids_fraction = min(solids_fraction, 1.0)

        other_solids = 0.0
        other_components: Dict[str, float] = {}
        chemicals = getattr(feed, 'chemicals', None)
        component_ids = chemicals.IDs if chemicals is not None else ()
        for component in component_ids:
            if component in {'Osteopontin', 'Water'}:
                continue
            mass = _component_mass(feed, component)
            if mass <= 0.0:
                continue
            other_components[component] = mass
            other_solids += mass

        total_solids = recovered_product + other_solids
        if total_solids <= 0.0:
            total_solids = recovered_product

        if solids_fraction <= 0.0:
            product_total_mass = total_solids
        else:
            product_total_mass = total_solids / solids_fraction
        if feed_total > 0.0:
            product_total_mass = min(product_total_mass, feed_total)
        product_total_mass = max(product_total_mass, total_solids)

        product_water = max(product_total_mass - total_solids, 0.0)
        product_water = min(product_water, feed_water)

        product_snapshot.imass['Osteopontin'] = recovered_product
        for component, mass in other_components.items():
            product_snapshot.imass[component] = mass
        if product_water:
            product_snapshot.imass['Water'] = product_water

        lost_product = max(input_product - recovered_product, 0.0)
        remaining_mass = max(feed_total - product_total_mass, 0.0)
        exhaust_water = max(remaining_mass - lost_product, 0.0)

        if lost_product:
            exhaust_snapshot.imass['Osteopontin'] = lost_product
        if exhaust_water:
            exhaust_snapshot.imass['Water'] = exhaust_water

        for stream in (product_snapshot, exhaust_snapshot):
            stream.T = feed_T
            stream.P = feed_P

        derived['input_product_kg'] = input_product
        derived['product_out_kg'] = recovered_product
        derived['product_total_mass_kg'] = product_total_mass
        derived['product_water_kg'] = product_water
        derived['lost_product_kg'] = lost_product
        derived['evaporated_water_kg'] = exhaust_water
        if input_product > 0.0:
            derived['spray_recovery_fraction'] = recovered_product / input_product
        else:
            derived['spray_recovery_fraction'] = 1.0

        product_stream.copy_like(product_snapshot)
        exhaust_stream.copy_like(exhaust_snapshot)

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Capacity"] = derived.get("capacity_kg_per_hr", 0.0)
        self.design_results["Final solids"] = derived.get("final_solids_percent", 0.0)
        self.design_results["Final solids mass fraction"] = derived.get("final_solids_content", 0.0)
        self.design_results["Product out"] = derived.get("product_out_kg", 0.0)
        self.design_results["Input density"] = derived.get("solution_density", 0.0)

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
