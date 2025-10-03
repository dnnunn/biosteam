"""Helpers and BioSTEAM units for DSP01 concentration and buffer exchange."""

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
from .unit_specs import (
    UFConcentrationSpecs,
    DiafiltrationSpecs,
    SPTFFSpecs,
    ContinuousTFFSpecs,
)

__all__ = [
    "ConcentrationRoute",
    "ConcentrationChain",
    "build_concentration_chain",
    "UFConcentrationUnit",
    "DiafiltrationUnit",
    "SPTFFUnit",
    "ContinuousTFFUnit",
]


class ConcentrationRoute(str, Enum):
    """Available concentration/buffer-exchange configurations."""

    UF_DF = "uf_df"
    UF_ONLY = "uf_only"
    DF_ONLY = "df_only"
    SPTFF = "sptff"
    CONTINUOUS_TFF = "continuous_tff"
    AUTO = "auto"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "ConcentrationRoute":
        if isinstance(value, cls):
            return value
        normalized = (value or cls.AUTO.value).lower()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.UF_DF if value else cls.AUTO


@dataclass
class ConcentrationChain:
    """Description of the instantiated concentration train."""

    route: ConcentrationRoute
    units: List[bst.Unit]
    product_out_kg: Optional[float]
    output_volume_l: Optional[float]
    notes: List[str] = field(default_factory=list)


def _make_plan(spec_key: str, specs: object) -> UnitPlan:
    data = ModuleData(
        key=ModuleKey(module="DSP01", option=spec_key),
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
    try:
        return float(stream.imass[component])
    except (KeyError, AttributeError, TypeError):
        return 0.0


def _coerce(value: object | None) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _select_route(
    requested: Optional[str],
    *,
    feed_cfg: Mapping[str, object],
    config: Mapping[str, object],
) -> Tuple[ConcentrationRoute, List[str]]:
    notes: List[str] = []

    continuous_required = bool(
        feed_cfg.get("continuous_mode")
        or config.get("continuous_required")
        or feed_cfg.get("perfusion")
    )
    inline_capture = bool(feed_cfg.get("inline_capture") or config.get("inline_capture"))
    df_cfg = config.get("diafiltration", {}) if isinstance(config, Mapping) else {}
    df_enabled = bool(df_cfg.get("enabled", True))
    buffer_spec = config.get("target_conductivity_mscm") or feed_cfg.get("target_conductivity_mscm")
    target_vrr = _coerce(feed_cfg.get("target_vrr")) or _coerce(
        config.get("target_vrr")
    )

    requested_route = ConcentrationRoute.from_string(requested)

    if requested_route is not ConcentrationRoute.AUTO:
        route = requested_route
    else:
        if continuous_required:
            route = ConcentrationRoute.CONTINUOUS_TFF
        elif inline_capture:
            route = ConcentrationRoute.SPTFF
        elif not df_enabled and buffer_spec is None:
            route = ConcentrationRoute.UF_ONLY
        elif df_enabled and (buffer_spec is not None or (target_vrr and target_vrr >= 4)):
            route = ConcentrationRoute.UF_DF
        elif df_enabled and buffer_spec is not None:
            route = ConcentrationRoute.DF_ONLY
        else:
            route = ConcentrationRoute.UF_DF

    def _warn(reason: str) -> None:
        message = f"Concentration override '{route.value}' flagged: {reason}"
        notes.append(message)
        warnings.warn(message, RuntimeWarning, stacklevel=3)

    if route == ConcentrationRoute.UF_ONLY and df_enabled and buffer_spec is not None:
        _warn("diafiltration requested by specs, but route skips DF")
    if route == ConcentrationRoute.DF_ONLY and not df_enabled:
        _warn("DF-only selected but diafiltration configuration disabled; skipping stage")
    if route == ConcentrationRoute.SPTFF and target_vrr is not None and target_vrr > 6.0:
        _warn("SPTFF beyond 6× concentration may require staging or UF assist")
    if route == ConcentrationRoute.CONTINUOUS_TFF and not continuous_required:
        notes.append("Continuous TFF forced without continuous flag; verify intent")

    return route, notes


class UFConcentrationUnit(PlanBackedUnit):
    """Batch UF concentration stage."""

    _N_ins = 1
    _N_outs = 2
    line = "UF Concentration"

    _units = {
        "Flux": "LMH",
        "Membrane area": "m2",
        "VRR": "-",
        "Membrane cost per cycle": "USD",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        retentate, permeate = self.outs
        derived = self.plan.derived

        feed_T = feed.T
        feed_P = feed.P
        chemicals = getattr(feed, "chemicals", None)
        component_ids = chemicals.IDs if chemicals is not None else ()
        initial_masses = {component: float(feed.imass[component]) for component in component_ids}
        if 'Osteopontin' not in initial_masses:
            initial_masses['Osteopontin'] = _get_component_mass(feed, 'Osteopontin')
        if 'Water' not in initial_masses:
            initial_masses['Water'] = _get_component_mass(feed, 'Water')
        feed_total_mass = sum(initial_masses.values())

        retentate.empty()
        permeate.empty()

        density = derived.get("density_kg_per_l") or 1.0

        input_product = derived.get("input_product_kg")
        if input_product is None:
            input_product = initial_masses.get("Osteopontin", 0.0)
        input_product = max(float(input_product), 0.0)

        product_out = derived.get("product_out_kg")
        if product_out is None:
            recovery = derived.get("protein_recovery_fraction") or 1.0
            product_out = input_product * recovery
        product_out = max(float(product_out), 0.0)

        input_volume = derived.get("input_volume_l")
        if (input_volume is None or input_volume <= 0.0) and density > 0.0 and feed_total_mass > 0.0:
            input_volume = feed_total_mass / density
        if input_volume is not None and input_volume > 0.0:
            derived['input_volume_l'] = input_volume
        else:
            derived.pop('input_volume_l', None)

        vrr = derived.get("volume_reduction_ratio")
        output_volume = derived.get("output_volume_l")
        if (output_volume is None or output_volume <= 0.0) and input_volume:
            if vrr and vrr > 0.0:
                output_volume = input_volume / vrr
        if (output_volume is None or output_volume <= 0.0) and density > 0.0 and product_out > 0.0:
            output_volume = product_out / density
        if output_volume is not None and output_volume > 0.0:
            derived['output_volume_l'] = output_volume
        else:
            derived.pop('output_volume_l', None)

        if output_volume is not None and output_volume > 0.0:
            ret_mass = output_volume * density
        else:
            ret_mass = product_out

        for component, mass in initial_masses.items():
            if component in {"Osteopontin", "Water"}:
                continue
            if mass:
                retentate.imass[component] = mass

        retentate.imass['Osteopontin'] = product_out
        retentate.imass['Water'] = max(ret_mass - product_out, 0.0)

        permeate_product = max(input_product - product_out, 0.0)
        if permeate_product > 0.0:
            permeate.imass['Osteopontin'] = permeate_product

        permeate_mass = max(feed_total_mass - ret_mass, 0.0)
        permeate.imass['Water'] = max(permeate_mass - permeate_product, 0.0)

        retentate.T = feed_T
        retentate.P = feed_P
        permeate.T = feed_T
        permeate.P = feed_P

        handoff = getattr(self, "_handoff_stream", None)
        if handoff is not None:
            handoff.copy_like(retentate)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(retentate)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(retentate)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(retentate)

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Flux"] = derived.get("flux_lmh", 0.0)
        self.design_results["Membrane area"] = derived.get("membrane_area_m2", 0.0)
        self.design_results["VRR"] = derived.get("volume_reduction_ratio", 0.0)
        self.design_results["Membrane cost per cycle"] = derived.get("membrane_cost_per_cycle", 0.0)

    def _cost(self) -> None:
        cost = self.plan.derived.get("membrane_cost_per_cycle")
        if cost:
            self.material_costs = {"UF membranes": cost}
            self.operating_cost = cost
        else:
            self.material_costs = {}
            self.operating_cost = 0.0


class DiafiltrationUnit(PlanBackedUnit):
    """Constant-volume diafiltration stage."""

    _N_ins = 1
    _N_outs = 2
    line = "Diafiltration"

    _units = {
        "Diavolumes": "vol",
        "Membrane area": "m2",
        "Flux": "LMH",
        "Membrane cost per cycle": "USD",
        "Buffer volume": "L",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        retentate, permeate = self.outs
        derived = self.plan.derived

        feed_T = feed.T
        feed_P = feed.P
        chemicals = getattr(feed, "chemicals", None)
        component_ids = chemicals.IDs if chemicals is not None else ()
        initial_masses = {component: float(feed.imass[component]) for component in component_ids}
        if 'Osteopontin' not in initial_masses:
            initial_masses['Osteopontin'] = _get_component_mass(feed, 'Osteopontin')
        if 'Water' not in initial_masses:
            initial_masses['Water'] = _get_component_mass(feed, 'Water')
        feed_total_mass = sum(initial_masses.values())

        retentate.empty()
        permeate.empty()

        density = derived.get("density_kg_per_l") or 1.0

        input_product = derived.get("input_product_kg")
        if input_product is None:
            input_product = initial_masses.get("Osteopontin", 0.0)
        input_product = max(float(input_product), 0.0)

        product_out = derived.get("product_out_kg")
        if product_out is None:
            recovery = derived.get("protein_recovery_fraction") or 1.0
            product_out = input_product * recovery
        product_out = max(float(product_out), 0.0)

        for component, mass in initial_masses.items():
            if component in {"Osteopontin", "Water"}:
                continue
            if mass:
                retentate.imass[component] = mass

        retentate.imass['Osteopontin'] = product_out
        input_volume = derived.get('input_volume_l')
        if input_volume and density > 0.0:
            total_mass = float(input_volume) * density
        else:
            total_mass = product_out + max(initial_masses.get('Water', 0.0), 0.0)
        retentate.imass['Water'] = max(total_mass - product_out, 0.0)

        permeate_product = max(input_product - product_out, 0.0)
        if permeate_product > 0.0:
            permeate.imass['Osteopontin'] = permeate_product

        buffer_mass = max(float(derived.get('buffer_mass_kg') or 0.0), 0.0)
        permeate_mass = max(feed_total_mass - retentate.F_mass, 0.0)
        permeate_water = max(permeate_mass - permeate_product, 0.0)
        permeate.imass['Water'] = permeate_water + buffer_mass

        retentate.T = feed_T
        retentate.P = feed_P
        permeate.T = feed_T
        permeate.P = feed_P

        handoff = getattr(self, "_handoff_stream", None)
        if handoff is not None:
            handoff.copy_like(retentate)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(retentate)

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Diavolumes"] = derived.get("dia_volumes", 0.0)
        self.design_results["Membrane area"] = derived.get("membrane_area_m2", 0.0)
        self.design_results["Flux"] = derived.get("flux_lmh", 0.0)
        self.design_results["Membrane cost per cycle"] = derived.get("membrane_cost_per_cycle", 0.0)
        self.design_results["Buffer volume"] = derived.get("buffer_volume_l", 0.0)

    def _cost(self) -> None:
        cost = (self.plan.derived.get("membrane_cost_per_cycle") or 0.0) + (
            self.plan.derived.get("buffer_cost_usd") or 0.0
        )
        items: Dict[str, float] = {}
        if self.plan.derived.get("membrane_cost_per_cycle"):
            items["DF membranes"] = self.plan.derived["membrane_cost_per_cycle"]
        if self.plan.derived.get("buffer_cost_usd"):
            items["Dia-buffer"] = self.plan.derived["buffer_cost_usd"]
        self.material_costs = items
        self.operating_cost = cost


class SPTFFUnit(PlanBackedUnit):
    """Single-pass tangential flow filtration stage."""

    _N_ins = 1
    _N_outs = 2
    line = "SPTFF"

    _units = {
        "Flux": "LMH",
        "Membrane area": "m2",
        "Concentration factor": "-",
        "Membrane cost per cycle": "USD",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        retentate, permeate = self.outs

        retentate.empty()
        permeate.empty()

        derived = self.plan.derived
        density = derived.get("density_kg_per_l") or 1.0

        input_product = derived.get("input_product_kg")
        if input_product is None:
            input_product = _get_component_mass(feed, "Osteopontin")
        input_product = max(input_product, 0.0)

        conc_factor = derived.get("concentration_factor") or 1.0
        product_recovery = derived.get("protein_recovery_fraction") or 1.0
        product_out = input_product * product_recovery

        input_volume = derived.get("input_volume_l")
        if input_volume is None and density:
            input_volume = feed.F_mass / density if feed.F_mass is not None else None
        output_volume = derived.get("output_volume_l")
        if output_volume is None and conc_factor and conc_factor > 0:
            output_volume = input_volume / conc_factor if input_volume is not None else None

        total_mass = (output_volume * density) if (output_volume is not None and density) else product_out
        retentate.imass["Osteopontin"] = product_out
        if total_mass is not None:
            retentate.imass["Water"] = max(total_mass - product_out, 0.0)

        permeate_loss = max(input_product - product_out, 0.0)
        if permeate_loss:
            permeate.imass["Osteopontin"] = permeate_loss

        if input_volume is not None and density is not None:
            feed_mass = input_volume * density
        else:
            feed_mass = feed.F_mass or 0.0
        ret_mass = total_mass if total_mass is not None else product_out
        permeate_mass = max(feed_mass - ret_mass, 0.0)
        permeate.imass["Water"] = max(permeate_mass - permeate_loss, 0.0)

        for stream in (retentate, permeate):
            stream.T = feed.T
            stream.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Flux"] = derived.get("flux_lmh", 0.0)
        self.design_results["Membrane area"] = derived.get("membrane_area_m2", 0.0)
        self.design_results["Concentration factor"] = derived.get("concentration_factor", 0.0)
        self.design_results["Membrane cost per cycle"] = derived.get("membrane_cost_per_cycle", 0.0)

    def _cost(self) -> None:
        cost = self.plan.derived.get("membrane_cost_per_cycle")
        if cost:
            self.material_costs = {"SPTFF membranes": cost}
            self.operating_cost = cost
        else:
            self.material_costs = {}
            self.operating_cost = 0.0


class ContinuousTFFUnit(PlanBackedUnit):
    """Continuous tangential-flow filtration stage."""

    _N_ins = 1
    _N_outs = 2
    line = "Continuous TFF"

    _units = {
        "Flux": "LMH",
        "Membrane area": "m2",
        "Concentration factor": "-",
        "Operating hours": "h",
        "Membrane cost per cycle": "USD",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        retentate, permeate = self.outs

        retentate.empty()
        permeate.empty()

        derived = self.plan.derived
        density = derived.get("density_kg_per_l") or 1.0

        input_product = derived.get("input_product_kg")
        if input_product is None:
            input_product = _get_component_mass(feed, "Osteopontin")
        input_product = max(input_product, 0.0)

        conc_factor = derived.get("concentration_factor") or 1.0
        product_recovery = derived.get("protein_recovery_fraction") or 1.0
        product_out = input_product * product_recovery

        input_volume = derived.get("input_volume_l")
        if input_volume is None and density:
            input_volume = feed.F_mass / density if feed.F_mass is not None else None
        output_volume = derived.get("output_volume_l")
        if output_volume is None and conc_factor and conc_factor > 0:
            output_volume = input_volume / conc_factor if input_volume is not None else None

        total_mass = (output_volume * density) if (output_volume is not None and density) else product_out
        retentate.imass["Osteopontin"] = product_out
        if total_mass is not None:
            retentate.imass["Water"] = max(total_mass - product_out, 0.0)

        permeate_loss = max(input_product - product_out, 0.0)
        if permeate_loss:
            permeate.imass["Osteopontin"] = permeate_loss

        if input_volume is not None and density:
            feed_mass = input_volume * density
        else:
            feed_mass = feed.F_mass or 0.0
        ret_mass = total_mass if total_mass is not None else product_out
        permeate_mass = max(feed_mass - ret_mass, 0.0)
        permeate.imass["Water"] = max(permeate_mass - permeate_loss, 0.0)

        for stream in (retentate, permeate):
            stream.T = feed.T
            stream.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Flux"] = derived.get("flux_lmh", 0.0)
        self.design_results["Membrane area"] = derived.get("membrane_area_m2", 0.0)
        self.design_results["Concentration factor"] = derived.get("concentration_factor", 0.0)
        self.design_results["Operating hours"] = derived.get("operation_hours", 0.0)
        self.design_results["Membrane cost per cycle"] = derived.get("membrane_cost_per_cycle", 0.0)

    def _cost(self) -> None:
        cost = self.plan.derived.get("membrane_cost_per_cycle")
        if cost:
            self.material_costs = {"Continuous TFF membranes": cost}
            self.operating_cost = cost
        else:
            self.material_costs = {}
            self.operating_cost = 0.0


ROUTE_SEQUENCE: Mapping[ConcentrationRoute, Tuple[str, ...]] = {
    ConcentrationRoute.UF_DF: ("uf_concentration", "diafiltration"),
    ConcentrationRoute.UF_ONLY: ("uf_concentration",),
    ConcentrationRoute.DF_ONLY: ("diafiltration",),
    ConcentrationRoute.SPTFF: ("sptff",),
    ConcentrationRoute.CONTINUOUS_TFF: ("continuous_tff",),
}


def build_concentration_chain(
    *,
    method: Optional[str],
    config: Mapping[str, object],
    micro_plan: UnitPlan,
    product_mass_kg: Optional[float],
    volume_l: Optional[float],
    density_kg_per_l: float,
) -> ConcentrationChain:
    route, selection_notes = _select_route(method, feed_cfg=config.get("feed", {}), config=config)

    if route is ConcentrationRoute.AUTO:
        # If auto resolved to AUTO due to missing heuristics, default to UF/DF
        route = ConcentrationRoute.UF_DF

    sequence = ROUTE_SEQUENCE.get(route, ())
    if not sequence:
        return ConcentrationChain(
            route=ConcentrationRoute.UF_ONLY,
            units=[],
            product_out_kg=product_mass_kg,
            output_volume_l=volume_l,
            notes=selection_notes + [f"Unsupported concentration route '{method}', using UF only."],
        )

    feed_cfg = config.get("feed", {}) if isinstance(config, Mapping) else {}
    current_product = product_mass_kg
    current_volume = volume_l
    units: List[bst.Unit] = []
    notes: List[str] = list(selection_notes)

    def _membrane_cost(area_m2: Optional[float], cost_per_m2: Optional[float], life_batches: Optional[float]) -> Optional[float]:
        if not area_m2 or not cost_per_m2:
            return None
        cost = area_m2 * cost_per_m2
        if life_batches and life_batches > 0:
            return cost / life_batches
        return cost

    def _apply_uf(stage_key: str) -> None:
        nonlocal current_product, current_volume
        specs_cfg = config.get("uf_concentration", {}) if isinstance(config, Mapping) else {}
        specs = UFConcentrationSpecs(
            key=stage_key,
            mwco_kda=specs_cfg.get("mwco_kda"),
            flux_lmh=specs_cfg.get("flux_lmh"),
            tmp_bar=specs_cfg.get("tmp_bar"),
            crossflow_velocity_m_s=specs_cfg.get("crossflow_velocity_m_s"),
            volume_reduction_ratio=specs_cfg.get("volume_reduction_ratio"),
            protein_recovery_fraction=specs_cfg.get("product_recovery_fraction"),
            fouling_derate=specs_cfg.get("fouling_derate", 1.0),
            membrane_area_m2=specs_cfg.get("membrane_area_m2"),
            membrane_cost_per_m2=specs_cfg.get("membrane_cost_per_m2"),
            membrane_life_batches=specs_cfg.get("membrane_life_batches"),
        )
        plan = _make_plan(stage_key, specs)

        vrr = _safe_fraction(specs.volume_reduction_ratio, 1.0)
        if vrr <= 0:
            vrr = 1.0
        elif vrr > 6.0:
            notes.append(
                "UF VRR exceeds 6×; review viscosity/TMP limits before accepting this target"
            )
        if current_volume is None:
            current_volume_local = _coerce(feed_cfg.get("volume_l"))
        else:
            current_volume_local = current_volume

        output_volume = None
        if current_volume_local is not None:
            output_volume = current_volume_local / vrr

        recovery = _safe_fraction(specs.protein_recovery_fraction, 0.985)
        product_out = None if current_product is None else max(current_product * recovery, 0.0)

        membrane_cost_per_cycle = _membrane_cost(
            specs.membrane_area_m2,
            specs.membrane_cost_per_m2,
            specs.membrane_life_batches,
        )

        plan.derived.update(
            {
                "input_product_kg": current_product,
                "input_volume_l": current_volume_local,
                "output_volume_l": output_volume,
                "product_out_kg": product_out,
                "volume_reduction_ratio": vrr,
                "flux_lmh": specs.flux_lmh,
                "membrane_area_m2": specs.membrane_area_m2,
                "membrane_cost_per_cycle": membrane_cost_per_cycle,
                "protein_recovery_fraction": recovery,
                "density_kg_per_l": density_kg_per_l,
            }
        )

        unit = UFConcentrationUnit("DSP01_UF", plan=plan)
        units.append(unit)

        current_product = product_out
        current_volume = output_volume

    def _apply_df(stage_key: str) -> None:
        nonlocal current_product, current_volume
        specs_cfg = config.get("diafiltration", {}) if isinstance(config, Mapping) else {}
        if not specs_cfg.get("enabled", True):
            notes.append("Diafiltration disabled in config; skipping stage")
            return
        specs = DiafiltrationSpecs(
            key=stage_key,
            dia_volumes=specs_cfg.get("dia_volumes"),
            flux_lmh=specs_cfg.get("flux_lmh"),
            protein_recovery_fraction=specs_cfg.get("product_recovery_fraction"),
            sieving_fraction=specs_cfg.get("sieving_fraction"),
            buffer_cost_per_m3=specs_cfg.get("buffer_cost_per_m3"),
            membrane_area_m2=specs_cfg.get("membrane_area_m2"),
            membrane_cost_per_m2=specs_cfg.get("membrane_cost_per_m2"),
            membrane_life_batches=specs_cfg.get("membrane_life_batches"),
        )
        plan = _make_plan(stage_key, specs)

        dia_volumes = _safe_fraction(specs.dia_volumes, 0.0)
        if dia_volumes > 2.0:
            notes.append(
                "Diafiltration ND > 2; expect additional yield/time penalties"
            )
        recovery = _safe_fraction(specs.protein_recovery_fraction, 0.99)
        product_out = None if current_product is None else max(current_product * recovery, 0.0)
        buffer_volume_l = 0.0
        if current_volume is not None:
            buffer_volume_l = dia_volumes * current_volume
        buffer_cost = None
        if specs.buffer_cost_per_m3 is not None and buffer_volume_l:
            buffer_cost = (buffer_volume_l / 1000.0) * specs.buffer_cost_per_m3

        membrane_cost_per_cycle = _membrane_cost(
            specs.membrane_area_m2,
            specs.membrane_cost_per_m2,
            specs.membrane_life_batches,
        )

        plan.derived.update(
            {
                "input_product_kg": current_product,
                "input_volume_l": current_volume,
                "product_out_kg": product_out,
                "dia_volumes": dia_volumes,
                "flux_lmh": specs.flux_lmh,
                "membrane_area_m2": specs.membrane_area_m2,
                "membrane_cost_per_cycle": membrane_cost_per_cycle,
                "buffer_volume_l": buffer_volume_l,
                "buffer_cost_usd": buffer_cost,
                "protein_recovery_fraction": recovery,
                "density_kg_per_l": density_kg_per_l,
            }
        )

        unit = DiafiltrationUnit("DSP01_DF", plan=plan)
        units.append(unit)

        current_product = product_out
        # Constant-volume DF keeps retentate volume unchanged

    def _apply_sptff(stage_key: str) -> None:
        nonlocal current_product, current_volume
        specs_cfg = config.get("sptff", {}) if isinstance(config, Mapping) else {}
        specs = SPTFFSpecs(
            key=stage_key,
            concentration_factor=specs_cfg.get("concentration_factor"),
            flux_lmh=specs_cfg.get("flux_lmh"),
            protein_recovery_fraction=specs_cfg.get("product_recovery_fraction"),
            membrane_area_m2=specs_cfg.get("membrane_area_m2"),
            membrane_cost_per_m2=specs_cfg.get("membrane_cost_per_m2"),
            membrane_life_batches=specs_cfg.get("membrane_life_batches"),
        )
        plan = _make_plan(stage_key, specs)

        conc_factor = _safe_fraction(specs.concentration_factor, 2.0)
        if conc_factor > 4.0:
            notes.append(
                "SPTFF concentration factor > 4×; verify staged TMP/viscosity before proceeding"
            )
        recovery = _safe_fraction(specs.protein_recovery_fraction, 0.98)
        product_out = None if current_product is None else max(current_product * recovery, 0.0)
        output_volume = None
        if current_volume is not None:
            output_volume = current_volume / conc_factor

        membrane_cost_per_cycle = _membrane_cost(
            specs.membrane_area_m2,
            specs.membrane_cost_per_m2,
            specs.membrane_life_batches,
        )

        plan.derived.update(
            {
                "input_product_kg": current_product,
                "input_volume_l": current_volume,
                "output_volume_l": output_volume,
                "product_out_kg": product_out,
                "concentration_factor": conc_factor,
                "flux_lmh": specs.flux_lmh,
                "membrane_area_m2": specs.membrane_area_m2,
                "membrane_cost_per_cycle": membrane_cost_per_cycle,
                "protein_recovery_fraction": recovery,
                "density_kg_per_l": density_kg_per_l,
            }
        )

        unit = SPTFFUnit("DSP01_SPTFF", plan=plan)
        units.append(unit)

        current_product = product_out
        current_volume = output_volume

    def _apply_ctff(stage_key: str) -> None:
        nonlocal current_product, current_volume
        specs_cfg = config.get("continuous_tff", {}) if isinstance(config, Mapping) else {}
        specs = ContinuousTFFSpecs(
            key=stage_key,
            concentration_factor=specs_cfg.get("concentration_factor"),
            protein_recovery_fraction=specs_cfg.get("product_recovery_fraction"),
            flux_lmh=specs_cfg.get("flux_lmh"),
            membrane_area_m2=specs_cfg.get("membrane_area_m2"),
            membrane_cost_per_m2=specs_cfg.get("membrane_cost_per_m2"),
            membrane_life_batches=specs_cfg.get("membrane_life_batches"),
            operation_hours=specs_cfg.get("operation_hours"),
        )
        plan = _make_plan(stage_key, specs)

        conc_factor = _safe_fraction(specs.concentration_factor, 2.0)
        recovery = _safe_fraction(specs.protein_recovery_fraction, 0.98)
        product_out = None if current_product is None else max(current_product * recovery, 0.0)
        output_volume = None
        if current_volume is not None:
            output_volume = current_volume / conc_factor

        membrane_cost_per_cycle = _membrane_cost(
            specs.membrane_area_m2,
            specs.membrane_cost_per_m2,
            specs.membrane_life_batches,
        )

        plan.derived.update(
            {
                "input_product_kg": current_product,
                "input_volume_l": current_volume,
                "output_volume_l": output_volume,
                "product_out_kg": product_out,
                "concentration_factor": conc_factor,
                "flux_lmh": specs.flux_lmh,
                "membrane_area_m2": specs.membrane_area_m2,
                "membrane_cost_per_cycle": membrane_cost_per_cycle,
                "operation_hours": specs.operation_hours,
                "protein_recovery_fraction": recovery,
                "density_kg_per_l": density_kg_per_l,
            }
        )

        unit = ContinuousTFFUnit("DSP01_cTFF", plan=plan)
        units.append(unit)

        current_product = product_out
        current_volume = output_volume

    stage_dispatch = {
        "uf_concentration": (_apply_uf, "UF"),
        "diafiltration": (_apply_df, "DF"),
        "sptff": (_apply_sptff, "SPTFF"),
        "continuous_tff": (_apply_ctff, "cTFF"),
    }

    for stage in sequence:
        handler, stage_key = stage_dispatch.get(stage, (None, None))
        if handler is None:
            notes.append(f"Unrecognized DSP01 stage '{stage}', skipping")
            continue
        handler(stage_key)

    return ConcentrationChain(
        route=route,
        units=units,
        product_out_kg=current_product,
        output_volume_l=current_volume,
        notes=notes,
    )
