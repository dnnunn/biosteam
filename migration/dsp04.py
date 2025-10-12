"""DSP04 polish and sterile filtration routing after DSP03."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Mapping, Optional

import math

import biosteam as bst

from .capture import CaptureHandoff
from .simple_units import PlanBackedUnit, SterileFilterUnit
from .unit_builders import UnitPlan

__all__ = [
    "DSP04Stage",
    "DSP04Config",
    "DSP04Chain",
    "build_dsp04_chain",
]

LABOR_RATE_PER_HOUR = 80.0


class DSP04Stage(str, Enum):
    """Available DSP04 polish stages."""

    NONE = "none"
    AEX_REPEAT = "aex_repeat"
    CEX_NEGATIVE = "cex_negative"
    HIC_FLOWTHROUGH = "hic_flowthrough"
    MIXEDBED_IEX = "mixedbed_iex"
    ENZYMATIC = "enzymatic_tidyup"


_STAGE_LINE_MAP = {
    DSP04Stage.NONE: "DSP04",
    DSP04Stage.AEX_REPEAT: "AEX Polish",
    DSP04Stage.CEX_NEGATIVE: "CEX Negative FT",
    DSP04Stage.HIC_FLOWTHROUGH: "HIC FlowThrough",
    DSP04Stage.MIXEDBED_IEX: "MixedBed IEX",
    DSP04Stage.ENZYMATIC: "Enzymatic Tidy-up",
}


def _optional_float(value: object | None) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _non_negative(value: object | None) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(numeric) or numeric < 0.0:
        return 0.0
    return numeric


@dataclass
class DSP04StageConfig:
    """Configuration for an individual DSP04 stage."""

    enabled: bool = True
    base_recovery_fraction: Optional[float] = None
    ft_capacity_mg_per_ml: Optional[float] = None
    lin_vel_cm_per_h: Optional[float] = None
    max_dp_bar: Optional[float] = None
    dna_log_reduction: Optional[float] = None
    chitosan_binding_eff_fraction: Optional[float] = None
    aggregate_removal_fraction: Optional[float] = None
    resin_fee_per_l_cycle: Optional[float] = None
    buffer_cost_per_m3: Optional[float] = None
    labor_hours_per_batch: Optional[float] = None
    mode: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    # Optional conductivity window for stages like HIC (in mM, proxy for ionic strength)
    cond_min_mM: Optional[float] = None
    cond_max_mM: Optional[float] = None


@dataclass
class SterileFilterConfig:
    flux_lmh: Optional[float] = None
    max_dp_bar: Optional[float] = None
    adsorption_loss_fraction: Optional[float] = None
    capacity_l_per_m2: Optional[float] = None
    adsorption_loss_fraction_per_m2: Optional[float] = None
    material_cost_per_m2: Optional[float] = None
    prefilter_material_cost_per_m2: Optional[float] = None
    labor_hours_per_batch: Optional[float] = None
    prefilter_enabled: bool = False


@dataclass
class DSP04Config:
    """Serialized configuration for DSP04 routing."""

    stage_order: List[DSP04Stage] = field(default_factory=list)
    stages: Mapping[DSP04Stage, DSP04StageConfig] = field(default_factory=dict)
    sterile_filter: SterileFilterConfig = field(default_factory=SterileFilterConfig)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "DSP04Config":
        if not isinstance(data, Mapping):
            return cls()

        order = []
        for name in data.get("stage_order", []):
            try:
                order.append(DSP04Stage(name))
            except ValueError:
                continue

        stages: dict[DSP04Stage, DSP04StageConfig] = {}
        stage_map = data.get("stages") if isinstance(data.get("stages"), Mapping) else {}
        for stage_name, cfg in stage_map.items():
            try:
                stage = DSP04Stage(stage_name)
            except ValueError:
                continue
            if not isinstance(cfg, Mapping):
                stages[stage] = DSP04StageConfig()
            else:
                stages[stage] = DSP04StageConfig(
                    enabled=bool(cfg.get("enabled", True)),
                    base_recovery_fraction=_optional_float(cfg.get("base_recovery_fraction")),
                    ft_capacity_mg_per_ml=_optional_float(cfg.get("ft_capacity_mg_per_ml")),
                    lin_vel_cm_per_h=_optional_float(cfg.get("lin_vel_cm_per_h")),
                    max_dp_bar=_optional_float(cfg.get("max_dp_bar")),
                    dna_log_reduction=_optional_float(cfg.get("dna_log_reduction")),
                    chitosan_binding_eff_fraction=_optional_float(cfg.get("chitosan_binding_eff_fraction")),
                    aggregate_removal_fraction=_optional_float(cfg.get("aggregate_removal_fraction")),
                    resin_fee_per_l_cycle=_optional_float(cfg.get("resin_fee_per_l_cycle")),
                    buffer_cost_per_m3=_optional_float(cfg.get("buffer_cost_per_m3")),
                    labor_hours_per_batch=_optional_float(cfg.get("labor_hours_per_batch")),
                    mode=str(cfg.get("mode")) if cfg.get("mode") is not None else None,
                    notes=[str(item) for item in cfg.get("notes", [])] if isinstance(cfg.get("notes"), list) else [],
                    cond_min_mM=_optional_float(cfg.get("cond_min_mM")),
                    cond_max_mM=_optional_float(cfg.get("cond_max_mM")),
                )

        sterile_cfg = data.get("sterile_filter") if isinstance(data.get("sterile_filter"), Mapping) else {}
        sterile = SterileFilterConfig(
            flux_lmh=_as_float(sterile_cfg.get("flux_lmh")),
            max_dp_bar=_as_float(sterile_cfg.get("max_dp_bar")),
            adsorption_loss_fraction=_as_float(sterile_cfg.get("adsorption_loss_fraction")),
            capacity_l_per_m2=_optional_float(sterile_cfg.get("capacity_l_per_m2")),
            adsorption_loss_fraction_per_m2=_optional_float(sterile_cfg.get("adsorption_loss_fraction_per_m2")),
            material_cost_per_m2=_optional_float(sterile_cfg.get("material_cost_per_m2")),
            prefilter_material_cost_per_m2=_optional_float(sterile_cfg.get("prefilter_material_cost_per_m2")),
            labor_hours_per_batch=_optional_float(sterile_cfg.get("labor_hours_per_batch")),
            prefilter_enabled=bool(sterile_cfg.get("prefilter_enabled", False)),
        )

        return cls(stage_order=order, stages=stages, sterile_filter=sterile)


def _as_float(value: object | None) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _calculate_pool_properties(handoff: CaptureHandoff) -> tuple[Optional[float], Optional[float]]:
    volume_l = handoff.pool_volume_l
    concentration = handoff.opn_concentration_g_per_l
    if volume_l is not None and concentration is not None:
        try:
            product = float(volume_l) * float(concentration) / 1_000.0
        except (TypeError, ValueError):
            product = None
    else:
        product = None
    return volume_l, product


@dataclass
class DSP04Chain:
    """DSP04 stage sequence plus sterile filtration."""

    stages: List[bst.Unit]
    sterile_filter: bst.Unit
    handoff: CaptureHandoff
    notes: List[str] = field(default_factory=list)


class DSP04StageUnit(PlanBackedUnit):
    """Polishing placeholder that applies spec-driven recoveries."""

    _N_ins = 1
    _N_outs = 1
    line = "DSP04"

    def __init__(self, ID: str, plan: UnitPlan) -> None:
        super().__init__(ID, plan=plan)
        self.performance_results: dict[str, float] = {}
        self.design_results: dict[str, float] = {}
        self.cost_results: dict[str, float] = {}
        self.material_costs: dict[str, float] = {}
        self.operating_cost: float = 0.0

    def _run(self) -> None:
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)

        try:
            product_in = float(feed.imass["Osteopontin"])
        except (KeyError, TypeError, AttributeError):
            product_in = 0.0
        derived = self.plan.derived

        if derived.get("input_product_kg") is None:
            derived["input_product_kg"] = product_in

        recovery = derived.get("effective_recovery_fraction")
        recovery = _optional_float(recovery) if recovery is not None else None
        if recovery is None or recovery < 0.0:
            recovery = 1.0
        recovery = min(recovery, 1.0)

        target_out = derived.get("product_out_kg")
        target_out = _optional_float(target_out) if target_out is not None else None
        if target_out is None:
            target_out = product_in * recovery

        target_out = max(min(target_out, product_in), 0.0)
        product.imass["Osteopontin"] = target_out

        loss = max(product_in - target_out, 0.0)
        derived["product_out_kg"] = target_out
        derived["stage_loss_kg"] = loss
        derived["stage_recovery_fraction"] = target_out / product_in if product_in else 1.0

        self.performance_results["Product recovery"] = derived["stage_recovery_fraction"]
        self.performance_results["Product loss (kg)"] = loss

        handoff = getattr(self, "_handoff_stream", None)
        if handoff is not None:
            handoff.copy_like(product)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(product)

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results["Recovery"] = derived.get("effective_recovery_fraction", 1.0)
        self.design_results["Input product (kg)"] = derived.get("input_product_kg", 0.0)
        self.design_results["Output product (kg)"] = derived.get("product_out_kg", 0.0)
        if derived.get("ft_capacity_mg_per_ml") is not None:
            self.design_results["FT capacity (mg/mL)"] = derived.get("ft_capacity_mg_per_ml", 0.0)
        if derived.get("lin_vel_cm_per_h") is not None:
            self.design_results["Linear velocity (cm/h)"] = derived.get("lin_vel_cm_per_h", 0.0)
        if derived.get("max_dp_bar") is not None:
            self.design_results["Max ΔP (bar)"] = derived.get("max_dp_bar", 0.0)

    def _cost(self) -> None:
        derived = self.plan.derived
        buffer_cost = _non_negative(derived.get("buffer_cost_per_batch_usd"))
        resin_cost = _non_negative(derived.get("resin_cost_per_batch_usd"))
        labor_cost = _non_negative(derived.get("labor_cost_per_batch_usd"))
        stage_cost = _non_negative(derived.get("stage_cost_per_batch_usd"))
        other_cost = max(stage_cost - (buffer_cost + resin_cost + labor_cost), 0.0)

        self.material_costs = {}
        if buffer_cost:
            self.material_costs["Buffers"] = buffer_cost
        if resin_cost:
            self.material_costs["Resin/consumables"] = resin_cost
        if labor_cost:
            self.material_costs["Labor"] = labor_cost
        if other_cost:
            self.material_costs["Other polish spend"] = other_cost

        self.operating_cost = stage_cost
        self.cost_results = {
            "Stage cost": stage_cost,
            "Buffer cost": buffer_cost,
            "Resin cost": resin_cost,
            "Labor cost": labor_cost,
        }


def _default_stage_order(handoff: CaptureHandoff) -> List[DSP04Stage]:
    route_value = ""
    if getattr(handoff, "route", None) is not None:
        try:
            route_value = handoff.route.value.lower()
        except AttributeError:
            route_value = str(handoff.route).lower()
    if "chitosan" in route_value:
        if (handoff.polyp_mM or 0) > 0:
            return [DSP04Stage.CEX_NEGATIVE, DSP04Stage.AEX_REPEAT]
        return [DSP04Stage.CEX_NEGATIVE]
    return [DSP04Stage.NONE]


def build_dsp04_chain(
    *,
    capture_handoff: CaptureHandoff,
    dsp03_handoff: CaptureHandoff,
    config_mapping: Mapping[str, object] | None = None,
) -> DSP04Chain:
    config = DSP04Config.from_mapping(config_mapping or {})
    order = config.stage_order or _default_stage_order(capture_handoff)

    stages: List[bst.Unit] = []
    notes: List[str] = []

    base_handoff = dsp03_handoff
    volume_l, product_kg = _calculate_pool_properties(base_handoff)
    if volume_l is None or product_kg is None:
        fallback_volume, fallback_product = _calculate_pool_properties(capture_handoff)
        if volume_l is None:
            volume_l = fallback_volume
        if product_kg is None:
            product_kg = fallback_product
    if volume_l is None:
        volume_l = capture_handoff.pool_volume_l

    initial_product = product_kg or 0.0
    current_product = max(initial_product, 0.0)

    current_dna = (
        base_handoff.dna_mg_per_l
        if base_handoff.dna_mg_per_l is not None
        else capture_handoff.dna_mg_per_l
    )
    current_chitosan = (
        base_handoff.chitosan_ppm
        if base_handoff.chitosan_ppm is not None
        else capture_handoff.chitosan_ppm
    )
    current_cost = base_handoff.cost_per_batch
    cost_initialized = current_cost is not None or capture_handoff.cost_per_batch is not None
    if current_cost is None:
        current_cost = capture_handoff.cost_per_batch or 0.0

    current_conductivity = (
        base_handoff.conductivity_mM
        if base_handoff.conductivity_mM is not None
        else capture_handoff.conductivity_mM
    )
    current_ph = base_handoff.ph if base_handoff.ph is not None else capture_handoff.ph
    current_cycle_time = (
        base_handoff.cycle_time_h
        if base_handoff.cycle_time_h is not None
        else capture_handoff.cycle_time_h
    )
    current_notes = list(set((base_handoff.notes or []) + (capture_handoff.notes or [])))

    current_step_recovery = 1.0
    added_stage_cost = False

    for stage in order:
        if stage is DSP04Stage.NONE:
            continue
        stage_cfg = config.stages.get(stage, DSP04StageConfig())
        if not stage_cfg.enabled:
            continue

        product_in = max(current_product, 0.0)
        recovery = stage_cfg.base_recovery_fraction
        if recovery is None or recovery <= 0.0:
            recovery = 1.0
        recovery = max(min(recovery, 1.0), 0.0)
        product_out = product_in * recovery

        volume_m3 = (volume_l or 0.0) / 1_000.0 if volume_l else 0.0
        buffer_cost = (stage_cfg.buffer_cost_per_m3 or 0.0) * volume_m3
        labor_hours = stage_cfg.labor_hours_per_batch or 0.0
        labor_cost = labor_hours * LABOR_RATE_PER_HOUR if labor_hours else 0.0
        resin_cost = stage_cfg.resin_fee_per_l_cycle or 0.0
        stage_cost = buffer_cost + labor_cost + resin_cost

        stage_notes = list(stage_cfg.notes)
        if recovery not in {None, 0.0, 1.0}:
            stage_notes.append(f"{stage.value} recovery {recovery:.4f}")
        if stage_cfg.aggregate_removal_fraction:
            stage_notes.append(
                f"{stage.value} aggregate removal {stage_cfg.aggregate_removal_fraction * 100:.1f}%"
            )
        # Conductivity window advisories (e.g., HIC salt window)
        if (stage_cfg.cond_min_mM is not None or stage_cfg.cond_max_mM is not None) and current_conductivity is not None:
            low = stage_cfg.cond_min_mM
            high = stage_cfg.cond_max_mM
            if low is not None and current_conductivity < low:
                stage_notes.append(
                    f"{stage.value} advisory: feed conductivity ({current_conductivity:.1f} mM) below recommended minimum ({low:.1f} mM)."
                )
            if high is not None and current_conductivity > high:
                stage_notes.append(
                    f"{stage.value} advisory: feed conductivity ({current_conductivity:.1f} mM) above recommended maximum ({high:.1f} mM)."
                )
        if stage_cfg.dna_log_reduction:
            stage_notes.append(
                f"{stage.value} DNA log reduction ≥{stage_cfg.dna_log_reduction:.2f}"
            )
        if stage_cfg.chitosan_binding_eff_fraction:
            stage_notes.append(
                f"{stage.value} chitosan capture ≥{stage_cfg.chitosan_binding_eff_fraction * 100:.1f}%"
            )

        derived: dict[str, object] = {
            "route": stage.value,
            "input_volume_l": volume_l,
            "input_product_kg": product_in,
            "input_dna_mg_per_l": current_dna,
            "input_chitosan_ppm": current_chitosan,
            "base_recovery_fraction": stage_cfg.base_recovery_fraction,
            "effective_recovery_fraction": recovery,
            "product_out_kg": product_out,
            "stage_cost_per_batch_usd": stage_cost if stage_cost else None,
            "buffer_cost_per_batch_usd": buffer_cost if buffer_cost else None,
            "labor_cost_per_batch_usd": labor_cost if labor_cost else None,
            "labor_hours_per_batch": labor_hours if labor_hours else None,
            "resin_cost_per_batch_usd": resin_cost if resin_cost else None,
        }

        if stage_cfg.ft_capacity_mg_per_ml is not None:
            derived["ft_capacity_mg_per_ml"] = stage_cfg.ft_capacity_mg_per_ml
        if stage_cfg.lin_vel_cm_per_h is not None:
            derived["lin_vel_cm_per_h"] = stage_cfg.lin_vel_cm_per_h
        if stage_cfg.max_dp_bar is not None:
            derived["max_dp_bar"] = stage_cfg.max_dp_bar
        if stage_cfg.mode:
            derived["mode"] = stage_cfg.mode

        if stage_cfg.dna_log_reduction is not None:
            derived["dna_log_reduction"] = stage_cfg.dna_log_reduction
            if current_dna is not None and stage_cfg.dna_log_reduction > 0.0:
                reduction_factor = 10 ** max(stage_cfg.dna_log_reduction, 0.0)
                if reduction_factor > 0:
                    current_dna = current_dna / reduction_factor
        if current_dna is not None:
            derived["estimated_dna_mg_per_l_out"] = current_dna

        if stage_cfg.chitosan_binding_eff_fraction is not None:
            eff = max(min(stage_cfg.chitosan_binding_eff_fraction, 1.0), 0.0)
            derived["chitosan_binding_eff_fraction"] = eff
            if current_chitosan is not None:
                current_chitosan = max(current_chitosan * (1.0 - eff), 0.0)
                derived["estimated_chitosan_ppm_out"] = current_chitosan

        if stage_cfg.aggregate_removal_fraction is not None:
            eff = max(min(stage_cfg.aggregate_removal_fraction, 1.0), 0.0)
            derived["aggregate_removal_fraction"] = eff


        plan = UnitPlan(None, None, None, derived=derived, notes=stage_notes)
        unit = DSP04StageUnit(f"DSP04_{stage.value}", plan=plan)
        unit.line = _STAGE_LINE_MAP.get(stage, unit.line)
        stages.append(unit)
        notes.extend(stage_notes)

        current_product = product_out
        current_cost += stage_cost
        current_step_recovery *= recovery
        if stage_cost:
            added_stage_cost = True

    sterile_plan = UnitPlan(None, None, None, derived={}, notes=[])
    sterile_cfg = config.sterile_filter
    sterile_derived = sterile_plan.derived
    sterile_derived.update(
        {
            "flux_lmh": sterile_cfg.flux_lmh,
            "max_dp_bar": sterile_cfg.max_dp_bar,
            "prefilter_enabled": sterile_cfg.prefilter_enabled,
            "input_volume_l": volume_l,
            "input_product_kg": current_product,
        }
    )

    filter_area_m2: Optional[float] = None
    if sterile_cfg.capacity_l_per_m2 and volume_l:
        try:
            filter_area_m2 = max(float(volume_l) / float(sterile_cfg.capacity_l_per_m2), 0.0)
        except (TypeError, ValueError, ZeroDivisionError):
            filter_area_m2 = None

    # Prefer explicit fixed adsorption fraction if provided; otherwise derive
    # from area and optional prefilter multiplier.
    sterile_loss = sterile_cfg.adsorption_loss_fraction
    if sterile_loss is None and sterile_cfg.adsorption_loss_fraction_per_m2 is not None and filter_area_m2 is not None:
        multiplier = 1.0 + (1.0 if sterile_cfg.prefilter_enabled else 0.0)
        sterile_loss = sterile_cfg.adsorption_loss_fraction_per_m2 * filter_area_m2 * multiplier
    if sterile_loss is None:
        sterile_loss = 0.0
    sterile_loss = max(min(float(sterile_loss), 1.0), 0.0)

    recovery = max(1.0 - sterile_loss, 0.0)

    product_in = current_product
    product_out = product_in * recovery

    sterile_derived["adsorption_loss_fraction"] = sterile_loss
    sterile_derived["effective_recovery_fraction"] = recovery
    sterile_derived["product_out_kg"] = product_out
    sterile_derived["stage_loss_kg"] = max(product_in - product_out, 0.0)
    sterile_derived["filter_area_m2"] = filter_area_m2

    filter_cost = 0.0
    prefilter_cost = 0.0
    if filter_area_m2 is not None and sterile_cfg.material_cost_per_m2 is not None:
        filter_cost = sterile_cfg.material_cost_per_m2 * filter_area_m2
    if sterile_cfg.prefilter_enabled and filter_area_m2 is not None and sterile_cfg.prefilter_material_cost_per_m2 is not None:
        prefilter_cost = sterile_cfg.prefilter_material_cost_per_m2 * filter_area_m2
    labor_hours = sterile_cfg.labor_hours_per_batch or 0.0
    labor_cost = labor_hours * LABOR_RATE_PER_HOUR if labor_hours else 0.0

    sterile_stage_cost = filter_cost + prefilter_cost + labor_cost
    sterile_derived["material_cost_per_batch_usd"] = filter_cost if filter_cost else None
    sterile_derived["prefilter_cost_per_batch_usd"] = prefilter_cost if prefilter_cost else None
    sterile_derived["labor_hours_per_batch"] = labor_hours if labor_hours else None
    sterile_derived["labor_cost_per_batch_usd"] = labor_cost if labor_cost else None
    sterile_derived["stage_cost_per_batch_usd"] = sterile_stage_cost if sterile_stage_cost else None

    sterile_unit = SterileFilterUnit("DSP04_SterileFilter", plan=sterile_plan)
    sterile_unit.line = "Sterile Filter 0.2 µm"

    current_product = product_out
    current_cost += sterile_stage_cost
    current_step_recovery *= recovery
    if sterile_stage_cost:
        added_stage_cost = True

    new_concentration = None
    if volume_l and current_product is not None:
        try:
            if volume_l > 0:
                new_concentration = current_product * 1_000.0 / volume_l
        except (TypeError, ValueError, ZeroDivisionError):
            new_concentration = None

    final_cost = current_cost if (cost_initialized or added_stage_cost) else None

    dsp04_handoff = CaptureHandoff(
        route=capture_handoff.route,
        pool_volume_l=volume_l,
        opn_concentration_g_per_l=new_concentration,
        conductivity_mM=current_conductivity,
        ph=current_ph,
        dna_mg_per_l=current_dna,
        chitosan_ppm=current_chitosan,
        polyp_mM=capture_handoff.polyp_mM,
        step_recovery_fraction=current_step_recovery,
        needs_df=False,
        needs_fines_polish=False,
        cycle_time_h=current_cycle_time,
        cost_per_batch=final_cost,
        notes=list(set(notes + current_notes)),
    )

    return DSP04Chain(stages=stages, sterile_filter=sterile_unit, handoff=dsp04_handoff, notes=notes)
