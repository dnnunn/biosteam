"""Helpers and simple BioSTEAM units for cell-removal staging."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import warnings
from typing import Dict, List, Mapping, Optional, Tuple

import biosteam as bst

from .excel_defaults import ModuleKey
from .module_builders import ModuleData
from .simple_units import PlanBackedUnit
from .unit_builders import UnitPlan
from .unit_specs import DepthFilterSpecs, DiscStackSpecs, MFTFFSpecs

__all__ = [
    "ClarificationRoute",
    "CellRemovalChain",
    "build_cell_removal_chain",
    "DiscStackCentrifuge",
    "DepthFiltrationUnit",
    "MFTFFPolishUnit",
    "ContinuousCentrifuge",
]


class ClarificationRoute(str, Enum):
    """Enumeration of supported clarification module configurations."""

    MICROFILTRATION = "microfiltration"
    DISC_STACK = "disc_stack"
    DISC_STACK_DEPTH = "disc_stack_depth"
    DEPTH_ONLY = "depth_only"
    MF_TFF_POLISH = "mf_tff_polish"
    CONTINUOUS_CENTRIFUGE = "continuous_centrifuge"
    AUTO = "auto"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "ClarificationRoute":
        if isinstance(value, cls):
            return value
        normalized = (value or cls.AUTO.value).lower()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.MICROFILTRATION if value else cls.AUTO


@dataclass
class CellRemovalChain:
    """Description of the instantiated clarification train."""

    route: ClarificationRoute
    units: List[bst.Unit]
    product_out_kg: Optional[float]
    output_volume_l: Optional[float]
    notes: List[str] = field(default_factory=list)


def _make_plan(spec_key: str, specs: object) -> UnitPlan:
    """Create a :class:`UnitPlan` wrapper for manually specified specs."""

    data = ModuleData(
        key=ModuleKey(module="USP03", option=spec_key),
        records={},
        values={},
        field_map={},
    )
    return UnitPlan(key=data.key, data=data, specs=specs, derived={})


def _safe_fraction(value: Optional[float], default: float) -> float:
    try:
        if value is None:
            raise TypeError
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_positive(value: Optional[float], default: float = 0.0) -> float:
    result = _safe_fraction(value, default)
    return result if result >= 0.0 else default


def _get_component_mass(stream: bst.Stream, component: str) -> float:
    """Return component mass or zero when missing."""

    try:
        return float(stream.imass[component])
    except (KeyError, AttributeError, TypeError):
        return 0.0


def _select_route(
    requested: Optional[str],
    *,
    feed_cfg: Mapping[str, object],
    config: Mapping[str, object],
) -> tuple[ClarificationRoute, List[str]]:
    """Determine the clarification route based on specs and overrides."""

    notes: List[str] = []

    def _coerce(value: object | None) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    solids_vv = _coerce(feed_cfg.get("solids_vv"))
    feed_volume_m3 = _coerce(feed_cfg.get("volume_m3"))
    turbidity_spec = _coerce(config.get("post_turbidity_spec"))
    membranes_required = bool(config.get("membranes_required"))

    requested_route = ClarificationRoute.from_string(requested)

    if requested_route is not ClarificationRoute.AUTO:
        route = requested_route
    else:
        if solids_vv is not None and solids_vv >= 0.03:
            route = (
                ClarificationRoute.MF_TFF_POLISH
                if membranes_required
                else ClarificationRoute.DISC_STACK_DEPTH
            )
        elif feed_volume_m3 is not None and feed_volume_m3 >= 30.0:
            route = ClarificationRoute.DISC_STACK_DEPTH
        elif membranes_required:
            route = ClarificationRoute.MF_TFF_POLISH
        else:
            route = ClarificationRoute.DEPTH_ONLY

        if turbidity_spec is not None and turbidity_spec <= 50.0:
            if route == ClarificationRoute.DEPTH_ONLY and (solids_vv or 0.0) >= 0.03:
                route = ClarificationRoute.DISC_STACK_DEPTH
            elif route not in {
                ClarificationRoute.DISC_STACK_DEPTH,
                ClarificationRoute.MF_TFF_POLISH,
            }:
                route = ClarificationRoute.DISC_STACK_DEPTH

    def _warn(reason: str) -> None:
        message = f"Clarification override '{route.value}' flagged: {reason}"
        notes.append(message)
        warnings.warn(message, RuntimeWarning, stacklevel=3)

    if route == ClarificationRoute.DEPTH_ONLY and solids_vv is not None and solids_vv > 0.02:
        _warn("depth filtration only is unsuitable above 2% v/v solids; expect fouling/cost blowout")
    if route in {ClarificationRoute.MICROFILTRATION, ClarificationRoute.MF_TFF_POLISH} and solids_vv is not None and solids_vv >= 0.03:
        _warn("membrane-only clarification at ≥3% v/v solids risks severe fouling")
    if route == ClarificationRoute.DISC_STACK and feed_volume_m3 is not None and feed_volume_m3 < 5.0:
        notes.append("Disc-stack selected below 5 m³; verify small-scale feasibility")

    return route, notes


class DiscStackCentrifuge(PlanBackedUnit):
    """Simple disc-stack centrifuge that references plan-derived splits."""

    _N_ins = 1
    _N_outs = 2
    line = "DiscStack"

    _units = {
        "Wet cake mass": "kg",
        "Power": "kWh",
    }

    def __init__(self, ID: str, plan: UnitPlan) -> None:
        super().__init__(ID, plan=plan)
        self.design_results: Dict[str, float] = {}
        self.performance_results: Dict[str, float] = {}
        self.cost_results: Dict[str, float] = {}

    def _run(self) -> None:
        feed = self.ins[0]
        clarified, wet_cake = self.outs

        clarified.copy_like(feed)
        wet_cake.empty()

        derived = self.plan.derived

        product_in = _get_component_mass(feed, "Osteopontin")
        solids_in = _get_component_mass(feed, "Yeast")
        water_in = _get_component_mass(feed, "Water")

        target_product = derived.get("product_out_kg")
        if target_product is None:
            product_to_supernatant = product_in
        else:
            product_to_supernatant = min(max(target_product, 0.0), product_in)
        product_to_cake = max(product_in - product_to_supernatant, 0.0)

        carryover_fraction = _safe_fraction(
            derived.get("solids_carryover_fraction"),
            0.0,
        )
        solids_to_supernatant = min(solids_in, solids_in * carryover_fraction)
        solids_to_cake = max(solids_in - solids_to_supernatant, 0.0)

        wet_cake_mass = _safe_positive(derived.get("wet_cake_mass_kg"), solids_to_cake)
        cake_water = max(wet_cake_mass - solids_to_cake - product_to_cake, 0.0)
        cake_water = min(cake_water, water_in)

        clarified.imass["Osteopontin"] = product_to_supernatant
        clarified.imass["Yeast"] = solids_to_supernatant
        clarified.imass["Water"] = max(water_in - cake_water, 0.0)

        wet_cake.imass["Osteopontin"] = product_to_cake
        wet_cake.imass["Yeast"] = solids_to_cake
        if cake_water:
            wet_cake.imass["Water"] = cake_water

        # Preserve remaining dissolved species in clarified stream.
        for index, mass in feed.imass.data.dct.items():
            component = feed.chemicals.IDs[index]
            if component in {"Osteopontin", "Yeast", "Water"}:
                continue
            clarified.imass[component] = mass

        self.performance_results.update(
            {
                "product_recovery": (
                    product_to_supernatant / product_in if product_in else 1.0
                ),
                "solids_carryover": (
                    solids_to_supernatant / solids_in if solids_in else 0.0
                ),
            }
        )

    def _design(self) -> None:
        specs = self.plan.specs
        if isinstance(specs, DiscStackSpecs):
            if specs.sigma_m2 is not None:
                self.design_results["Sigma area"] = float(specs.sigma_m2)
            if specs.power_kwh_per_m3 is not None:
                volume = _safe_positive(self.plan.derived.get("input_volume_l"), 0.0) / 1000.0
                self.design_results["Power"] = float(specs.power_kwh_per_m3 or 0.0) * volume
            if specs.parallel_trains:
                self.design_results["Parallel trains"] = float(specs.parallel_trains)
        self.design_results["Wet cake mass"] = _safe_positive(
            self.plan.derived.get("wet_cake_mass_kg"),
            0.0,
        )

    def _cost(self) -> None:
        specs = self.plan.specs
        if isinstance(specs, DiscStackSpecs) and specs.power_kwh_per_m3:
            volume_m3 = _safe_positive(
                self.plan.derived.get("input_volume_l"),
                0.0,
            ) / 1000.0
            self.cost_results["Power kWh"] = specs.power_kwh_per_m3 * volume_m3
        else:
            self.cost_results.clear()


class DepthFiltrationUnit(PlanBackedUnit):
    """Depth filtration step removing fines and incurring holdup losses."""

    _N_ins = 1
    _N_outs = 2
    line = "DepthFiltration"

    _units = {
        "Holdup loss": "kg",
    }

    def __init__(self, ID: str, plan: UnitPlan) -> None:
        super().__init__(ID, plan=plan)
        self.design_results: Dict[str, float] = {}
        self.performance_results: Dict[str, float] = {}
        self.cost_results: Dict[str, float] = {}

    def _run(self) -> None:
        feed = self.ins[0]
        filtrate, waste = self.outs

        filtrate.copy_like(feed)
        waste.empty()

        product_in = _get_component_mass(feed, "Osteopontin")
        target_out = self.plan.derived.get("product_out_kg")
        if target_out is None:
            product_out = product_in
        else:
            product_out = min(max(target_out, 0.0), product_in)
        product_loss = max(product_in - product_out, 0.0)

        filtrate.imass["Osteopontin"] = product_out
        waste.imass["Osteopontin"] = product_loss

        holdup_loss = _safe_positive(self.plan.derived.get("holdup_loss_kg"), 0.0)
        if holdup_loss:
            water_in = _get_component_mass(feed, "Water")
            transfer = min(holdup_loss, water_in)
            filtrate.imass["Water"] = max(water_in - transfer, 0.0)
            waste.imass["Water"] = transfer

        # Ensure mass balance by moving remaining deficit as water to waste.
        mass_deficit = feed.F_mass - (filtrate.F_mass + waste.F_mass)
        if mass_deficit > 1e-9:
            waste.imass["Water"] += mass_deficit
        elif mass_deficit < -1e-9:
            # Correct slight excess by reducing filtrate water.
            current_water = _get_component_mass(filtrate, "Water")
            correction = min(-mass_deficit, current_water)
            if correction:
                filtrate.imass["Water"] = max(current_water - correction, 0.0)

        self.performance_results.update(
            {
                "product_recovery": (
                    product_out / product_in if product_in else 1.0
                ),
                "holdup_loss": holdup_loss,
            }
        )

    def _design(self) -> None:
        self.design_results["Holdup loss"] = _safe_positive(
            self.plan.derived.get("holdup_loss_kg"),
            0.0,
        )

    def _cost(self) -> None:
        self.cost_results.clear()
        specs = self.plan.specs
        if isinstance(specs, DepthFilterSpecs) and specs.media_cost_per_m2:
            area = 0.0
            capacities = specs.specific_capacity_l_per_m2 or []
            throughput = _safe_positive(self.plan.derived.get("input_volume_l"), 0.0)
            for capacity in capacities:
                if not capacity:
                    continue
                area += throughput / capacity
            media_cost = area * float(specs.media_cost_per_m2)
            if media_cost:
                self.cost_results["Media cost"] = media_cost


class MFTFFPolishUnit(PlanBackedUnit):
    """Tangential-flow microfiltration polish stage."""

    _N_ins = 1
    _N_outs = 2
    line = "MF-TFF"

    _units = {
        "Membrane cost": "USD",
    }

    def __init__(self, ID: str, plan: UnitPlan) -> None:
        super().__init__(ID, plan=plan)
        self.design_results: Dict[str, float] = {}
        self.performance_results: Dict[str, float] = {}
        self.cost_results: Dict[str, float] = {}

    def _run(self) -> None:
        feed = self.ins[0]
        permeate, retentate = self.outs

        permeate.copy_like(feed)
        retentate.empty()

        product_in = _get_component_mass(feed, "Osteopontin")
        target_out = self.plan.derived.get("product_out_kg")
        if target_out is None:
            product_out = product_in
        else:
            product_out = min(max(target_out, 0.0), product_in)
        product_loss = max(product_in - product_out, 0.0)

        permeate.imass["Osteopontin"] = product_out
        retentate.imass["Osteopontin"] = product_loss

        feed_mass = feed.F_mass
        permeate_mass = permeate.F_mass
        deficit = feed_mass - (permeate_mass + product_loss)
        if deficit > 1e-9:
            retentate.imass["Water"] = deficit

        self.performance_results.update(
            {
                "product_recovery": (
                    product_out / product_in if product_in else 1.0
                ),
            }
        )

    def _design(self) -> None:
        specs = self.plan.specs
        if isinstance(specs, MFTFFSpecs):
            if specs.flux_lmh is not None and specs.membrane_cost_per_m2 is not None:
                throughput = _safe_positive(self.plan.derived.get("input_volume_l"), 0.0)
                flux = max(specs.flux_lmh, 1e-6)
                area = throughput / flux
                self.design_results["Membrane area"] = area
                self.cost_results["Membrane cost"] = area * specs.membrane_cost_per_m2

    def _cost(self) -> None:
        # Costs already set in design step due to static placeholders.
        if "Membrane cost" not in self.cost_results:
            self.cost_results.clear()


class ContinuousCentrifuge(DiscStackCentrifuge):
    """Continuous centrifuge variant with higher shear defaults."""

    line = "ContinuousCentrifuge"


ROUTE_SEQUENCE: Mapping[ClarificationRoute, Tuple[str, ...]] = {
    ClarificationRoute.MICROFILTRATION: ("microfiltration",),
    ClarificationRoute.DISC_STACK: ("disc_stack",),
    ClarificationRoute.DISC_STACK_DEPTH: ("disc_stack", "depth_filter"),
    ClarificationRoute.DEPTH_ONLY: ("depth_filter",),
    ClarificationRoute.MF_TFF_POLISH: ("disc_stack", "mf_tff"),
    ClarificationRoute.CONTINUOUS_CENTRIFUGE: ("continuous",),
}


def build_cell_removal_chain(
    *,
    method: Optional[str],
    config: Mapping[str, object],
    fermentation_plan: UnitPlan,
    micro_plan: UnitPlan,
    harvested_volume_l: Optional[float],
) -> CellRemovalChain:
    """Create a clarification train based on baseline configuration."""

    feed_cfg = config.get("feed", {}) if isinstance(config, Mapping) else {}

    route, selection_notes = _select_route(method, feed_cfg=feed_cfg, config=config)
    if route is ClarificationRoute.MICROFILTRATION:
        return CellRemovalChain(
            route=route,
            units=[],
            product_out_kg=micro_plan.derived.get("product_out_kg"),
            output_volume_l=micro_plan.derived.get("output_volume_l"),
            notes=selection_notes,
        )

    sequence = ROUTE_SEQUENCE.get(route, ())
    if not sequence:
        return CellRemovalChain(
            route=ClarificationRoute.MICROFILTRATION,
            units=[],
            product_out_kg=micro_plan.derived.get("product_out_kg"),
            output_volume_l=micro_plan.derived.get("output_volume_l"),
            notes=selection_notes
            + [f"Unsupported route '{method}', defaulting to microfiltration."],
        )

    density_kg_per_m3 = _safe_positive(feed_cfg.get("density_kg_per_m3"), 1040.0)
    density_kg_per_l = density_kg_per_m3 / 1000.0

    current_product = micro_plan.derived.get("input_product_kg")
    if current_product is None:
        current_product = fermentation_plan.derived.get("product_out_kg")

    current_volume_l = micro_plan.derived.get("input_volume_l")
    if current_volume_l is None:
        current_volume_l = harvested_volume_l
    if current_volume_l is None:
        current_volume_l = _safe_positive(feed_cfg.get("volume_m3"), 0.0) * 1000.0

    dcw_conc = fermentation_plan.derived.get("dcw_concentration_g_per_l")
    current_solids = None
    if dcw_conc is not None and current_volume_l is not None:
        current_solids = (dcw_conc / 1000.0) * current_volume_l

    units: List[bst.Unit] = []
    notes: List[str] = list(selection_notes)

    def _apply_disc_stack(
        stage_key: str,
        *,
        unit_cls: type[DiscStackCentrifuge] = DiscStackCentrifuge,
        unit_id: str = "CR_DiscStack",
    ) -> None:
        nonlocal current_product, current_volume_l, current_solids
        specs_cfg = config.get("disc_stack", {}) if isinstance(config, Mapping) else {}
        specs = DiscStackSpecs(
            key=stage_key,
            sigma_m2=specs_cfg.get("sigma_m2"),
            product_recovery_fraction=specs_cfg.get("product_recovery_fraction"),
            solids_carryover_fraction=specs_cfg.get("solids_carryover_fraction"),
            wet_cake_moisture_fraction=specs_cfg.get("wet_cake_moisture_fraction"),
            power_kwh_per_m3=specs_cfg.get("power_kwh_per_m3"),
            parallel_trains=specs_cfg.get("parallel_trains"),
        )
        plan = _make_plan(stage_key, specs)

        recovery = _safe_fraction(specs.product_recovery_fraction, 0.99)
        carryover = _safe_fraction(specs.solids_carryover_fraction, 0.0)
        moisture = _safe_fraction(specs.wet_cake_moisture_fraction, 0.8)
        moisture = min(max(moisture, 0.0), 0.995)

        if current_product is not None:
            product_out = max(current_product * recovery, 0.0)
        else:
            product_out = None
        if current_solids is not None:
            solids_supernatant = max(current_solids * carryover, 0.0)
            solids_cake = max(current_solids - solids_supernatant, 0.0)
        else:
            solids_supernatant = None
            solids_cake = None

        wet_cake_mass = None
        if solids_cake is not None and solids_cake > 0.0:
            wet_cake_mass = solids_cake / max(1.0 - moisture, 1e-6)
        elif current_product is not None and current_product > 0 and moisture > 0:
            wet_cake_mass = current_product * moisture

        power = None
        if specs.power_kwh_per_m3 is not None and current_volume_l is not None:
            power = specs.power_kwh_per_m3 * (current_volume_l / 1000.0)

        plan.derived.update(
            {
                "input_product_kg": current_product,
                "product_out_kg": product_out,
                "input_volume_l": current_volume_l,
                "density_kg_per_l": density_kg_per_l,
                "solids_carryover_fraction": carryover,
                "wet_cake_mass_kg": wet_cake_mass,
                "solids_cake_kg": solids_cake,
                "solids_supernatant_kg": solids_supernatant,
                "power_kwh_per_batch": power,
            }
        )

        unit = unit_cls(unit_id, plan=plan)
        units.append(unit)

        current_product = product_out
        if solids_supernatant is not None:
            current_solids = solids_supernatant
        if wet_cake_mass is not None and current_volume_l is not None:
            removed_mass = wet_cake_mass
            delta_volume = removed_mass / density_kg_per_l if density_kg_per_l else 0.0
            current_volume_l = max(current_volume_l - delta_volume, 0.0)

    def _apply_depth(stage_key: str) -> None:
        nonlocal current_product, current_volume_l
        specs_cfg = config.get("depth_filter", {}) if isinstance(config, Mapping) else {}
        specs = DepthFilterSpecs(
            key=stage_key,
            product_recovery_fraction=specs_cfg.get("product_recovery_fraction"),
            holdup_loss_kg=specs_cfg.get("holdup_loss_kg"),
            specific_capacity_l_per_m2=specs_cfg.get("specific_capacity_l_per_m2"),
            flux_lmh=specs_cfg.get("flux_lmh"),
            terminal_delta_p_bar=specs_cfg.get("terminal_delta_p_bar"),
            media_cost_per_m2=specs_cfg.get("media_cost_per_m2"),
        )
        plan = _make_plan(stage_key, specs)
        recovery = _safe_fraction(specs.product_recovery_fraction, 0.99)
        holdup = _safe_positive(specs.holdup_loss_kg, 0.0)

        if current_product is not None:
            product_after_recovery = max(current_product * recovery, 0.0)
            product_out = max(product_after_recovery - holdup, 0.0)
        else:
            product_out = None

        plan.derived.update(
            {
                "input_product_kg": current_product,
                "product_out_kg": product_out,
                "input_volume_l": current_volume_l,
                "holdup_loss_kg": holdup,
            }
        )

        unit = DepthFiltrationUnit(f"CR_Depth", plan=plan)
        units.append(unit)
        current_product = product_out

    def _apply_mf_tff(stage_key: str) -> None:
        nonlocal current_product, current_volume_l
        specs_cfg = config.get("mf_tff", {}) if isinstance(config, Mapping) else {}
        specs = MFTFFSpecs(
            key=stage_key,
            product_recovery_fraction=specs_cfg.get("product_recovery_fraction"),
            flux_lmh=specs_cfg.get("flux_lmh"),
            membrane_cost_per_m2=specs_cfg.get("membrane_cost_per_m2"),
            membrane_life_batches=specs_cfg.get("membrane_life_batches"),
        )
        plan = _make_plan(stage_key, specs)
        recovery = _safe_fraction(specs.product_recovery_fraction, 0.995)

        if current_product is not None:
            product_out = max(current_product * recovery, 0.0)
        else:
            product_out = None

        plan.derived.update(
            {
                "input_product_kg": current_product,
                "product_out_kg": product_out,
                "input_volume_l": current_volume_l,
            }
        )

        unit = MFTFFPolishUnit(f"CR_MFTFF", plan=plan)
        units.append(unit)
        current_product = product_out

    def _apply_continuous(stage_key: str) -> None:
        _apply_disc_stack(
            stage_key,
            unit_cls=ContinuousCentrifuge,
            unit_id="CR_Continuous",
        )

    for stage in sequence:
        if stage == "disc_stack":
            _apply_disc_stack("DiscStack")
        elif stage == "depth_filter":
            _apply_depth("DepthFilter")
        elif stage == "mf_tff":
            _apply_mf_tff("MF_TFF")
        elif stage == "continuous":
            _apply_continuous("ContinuousCentrifuge")

    return CellRemovalChain(
        route=route,
        units=units,
        product_out_kg=current_product,
        output_volume_l=current_volume_l,
        notes=notes,
    )
