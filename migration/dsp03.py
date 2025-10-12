"""Baseline DSP03 UF→DF→UF conditioning chain prior to final concentration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping, Optional, List, Dict

import math
import biosteam as bst

from .capture import CaptureHandoff
from .buffer_tools import (
    compute_nd_from_ionic_strength,
    BestPracticeRules,
    water_viscosity_mPa_s,
    relative_viscosity,
    apply_viscosity_flux_derate,
)
from .buffer_tools.costing import estimate_cost_per_m3_for_buffer_id
from .simple_units import PlanBackedUnit
from .unit_builders import UnitPlan

__all__ = [
    "DSP03Route",
    "DSP03Parameters",
    "DSP03Config",
    "DSP03Chain",
    "build_dsp03_chain",
]


class DSP03Route(str, Enum):
    """Route enumeration for the baseline UF→DF→UF implementation."""

    BASELINE = "ufdfuf"


@dataclass
class DSP03Parameters:
    vr_preuf: float = 3.0
    nd: float = 5.0
    flux_lmh: float = 85.0
    tmp_bar_cap: float = 1.5
    sieving_uf: float = 0.01
    sieving_df: float = 0.007
    adsorption_loss_per_100_m2: float = 0.002
    df_time_h: float = 10.0
    area_headroom_fraction: float = 0.2
    membrane_cost_per_m2: float = 260.0
    membrane_life_batches: float = 30.0
    buffer_cost_per_m3: float = 220.0
    labor_hours_per_batch: float = 8.0
    labor_rate_per_hour: float = 80.0
    waste_cost_per_tonne: float = 220.0
    antifoam_flux_derate_fraction: float = 0.25
    antifoam_adsorption_addition_fraction: float = 0.003
    mwco_kda: float = 30.0
    cfv_ms: float = 2.0

    def with_overrides(self, mapping: Mapping[str, object]) -> "DSP03Parameters":
        values = dict(mapping or {})
        params = self
        for field_name in self.__dataclass_fields__:
            if field_name not in values:
                continue
            raw = values[field_name]
            try:
                numeric = float(raw)
            except (TypeError, ValueError):
                continue
            params = replace(params, **{field_name: numeric})
        return params


DEFAULT_PARAMETERS = DSP03Parameters()


@dataclass
class DSP03Config:
    parameters: DSP03Parameters = DEFAULT_PARAMETERS
    buffers: dict | None = None
    apply_flux_derate: bool = False
    auto_plan: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, object] | None) -> "DSP03Config":
        if not isinstance(data, Mapping):
            return cls()
        params_data = data.get("parameters", data)
        if not isinstance(params_data, Mapping):
            params_data = {}
        params = DEFAULT_PARAMETERS.with_overrides(params_data)
        buffers = data.get("buffers") if isinstance(data, Mapping) else None
        try:
            buffers = dict(buffers) if isinstance(buffers, Mapping) else None
        except Exception:
            buffers = None
        apply_flux_derate = False
        try:
            apply_flux_derate = bool(data.get("apply_flux_derate", False))
        except Exception:
            apply_flux_derate = False
        auto_plan = False
        try:
            auto_plan = bool(data.get("auto_plan", False))
        except Exception:
            auto_plan = False
        return cls(
            parameters=params,
            buffers=buffers,
            apply_flux_derate=apply_flux_derate,
            auto_plan=auto_plan,
        )


@dataclass
class DSP03Chain:
    """Description of instantiated DSP03 unit(s)."""

    route: DSP03Route
    units: List[bst.Unit]
    handoff: CaptureHandoff
    notes: List[str]


class DSP03UFDFUnit(PlanBackedUnit):
    """UF→DF→UF baseline implementation tracking design and operating costs."""

    _N_ins = 1
    _N_outs = 1
    line = "DSP03 UF-DF-UF"

    def __init__(self, ID: str, plan: UnitPlan) -> None:
        super().__init__(ID, plan=plan)
        self.performance_results: Dict[str, float] = {}
        self.design_results: Dict[str, float] = {}
        self.cost_results: Dict[str, float] = {}
        self.material_costs: Dict[str, float] = {}
        self.operating_cost: float = 0.0

    def _run(self) -> None:
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)

        derived = self.plan.derived
        output_product = max(float(derived.get("output_product_kg", 0.0)), 0.0)
        output_volume_l = max(float(derived.get("output_volume_l", 0.0)), 0.0)
        density = float(derived.get("retentate_density_kg_per_l", 1.0))
        total_mass = max(float(derived.get("output_total_mass_kg", output_volume_l * density)), 0.0)
        water_mass = max(total_mass - output_product, 0.0)

        product.empty()
        if output_product > 0.0:
            product.imass["Osteopontin"] = output_product
        if water_mass > 0.0:
            product.imass["Water"] = water_mass
        product.F_vol = output_volume_l / 1_000.0

        handoff = getattr(self, "_handoff_stream", None)
        if handoff is not None:
            handoff.copy_like(product)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(product)

        recovery = derived.get("step_recovery_fraction")
        if recovery is None:
            feed_product = _component_mass(feed, "Osteopontin")
            recovery = output_product / feed_product if feed_product else 1.0
        self.performance_results["Recovery"] = float(recovery)
        self.performance_results["Output product (kg)"] = output_product
        self.performance_results["Output volume (L)"] = output_volume_l
        self.performance_results["Buffer volume (m3)"] = float(derived.get("df_buffer_volume_m3", 0.0))

        self.design_results["Installed area (m2)"] = float(derived.get("installed_area_m2", 0.0))
        self.design_results["DF time (h)"] = float(derived.get("df_time_h", 0.0))
        self.design_results["Pre-UF time (h)"] = float(derived.get("preuf_time_h", 0.0))
        self.design_results["Total cycle time (h)"] = float(derived.get("cycle_time_h", 0.0))
        self.design_results["Membrane MWCO (kDa)"] = float(derived.get("mwco_kda", 30.0))
        self.design_results["Cross-flow velocity (m/s)"] = float(derived.get("cfv_ms", 2.0))

        membrane_cost = float(derived.get("membrane_cost_per_batch_usd", 0.0))
        buffer_cost = float(derived.get("buffer_cost_per_batch_usd", 0.0))
        labor_cost = float(derived.get("labor_cost_per_batch_usd", 0.0))
        waste_cost = float(derived.get("waste_cost_per_batch_usd", 0.0))
        total_cost = float(derived.get("total_cost_per_batch_usd", membrane_cost + buffer_cost + labor_cost + waste_cost))

        self.material_costs = {}
        if buffer_cost:
            self.material_costs["DF buffers"] = buffer_cost
        if membrane_cost:
            self.material_costs["Membrane amortization"] = membrane_cost
        if labor_cost:
            self.material_costs["Labor"] = labor_cost
        if waste_cost:
            self.material_costs["Waste disposal"] = waste_cost

        self.operating_cost = total_cost
        self.cost_results = {
            "Total cost": total_cost,
            "Membrane": membrane_cost,
            "Buffer": buffer_cost,
            "Labor": labor_cost,
            "Waste": waste_cost,
        }


def _component_mass(stream: bst.Stream, component: str) -> float:
    try:
        return float(stream.imass[component])
    except (AttributeError, KeyError, TypeError, ValueError):
        return 0.0


def _optional(value: object | None, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_dsp03_chain(
    *,
    capture_handoff: CaptureHandoff,
    config_mapping: Mapping[str, object] | None = None,
    upstream_plan: UnitPlan | None = None,
) -> DSP03Chain:
    """Instantiate the baseline UF→DF→UF stage after capture."""

    config = DSP03Config.from_mapping(config_mapping)
    params = config.parameters

    volume_l = capture_handoff.pool_volume_l
    concentration = capture_handoff.opn_concentration_g_per_l
    if volume_l is None or concentration is None:
        volume_l = volume_l or _optional(getattr(upstream_plan, "derived", {}).get("eluate_volume_l"), 0.0)
        concentration = concentration or _optional(getattr(upstream_plan, "derived", {}).get("eluate_concentration_g_per_l"), 0.0)

    volume_l = max(volume_l or 0.0, 0.0)
    volume_m3 = volume_l / 1_000.0
    product_in = (concentration or 0.0) * volume_l / 1_000.0

    vr = max(params.vr_preuf, 1.0)
    nd = max(params.nd, 0.0)
    # Apply best-practice flux derate when antifoam present
    antifoam_flag = bool(getattr(capture_handoff, "needs_fines_polish", False))
    rules = BestPracticeRules(
        max_tmp_bar=params.tmp_bar_cap,
        antifoam_flux_derate_fraction=params.antifoam_flux_derate_fraction,
    )
    if config.apply_flux_derate:
        flux = rules.apply_flux_derate(params.flux_lmh, antifoam_flag)
    else:
        flux = params.flux_lmh
    if flux <= 0.0:
        flux = max(params.flux_lmh, 1.0)
    df_time = max(params.df_time_h, 1.0)
    headroom = max(params.area_headroom_fraction, 0.0)

    volume_preuf_m3 = volume_m3 / vr
    volume_preuf_l = volume_preuf_m3 * 1_000.0
    permeate_preuf_m3 = max(volume_m3 - volume_preuf_m3, 0.0)
    # Optional: compute ND from buffer targets if configured
    use_planner = False
    target_I_mM = None
    use_cond = False
    initial_k_mScm = None
    target_k_mScm = None
    df_time_target = None
    nd_max = None
    buf_multiple_max = None
    area_max_m2 = None
    headroom_override = None
    viscosity_mPa_s = None
    viscosity_temp_C = None
    cost_from_registry = False
    cost_buffer_id = None
    if config.buffers and isinstance(config.buffers.get("df"), Mapping):
        df_cfg = config.buffers.get("df")  # type: ignore[assignment]
        try:
            use_planner = bool(df_cfg.get("use_planner", False))  # type: ignore[attr-defined]
        except Exception:
            use_planner = False
        try:
            target_I_mM = float(df_cfg.get("target_ionic_strength_mM"))  # type: ignore[attr-defined]
        except Exception:
            target_I_mM = None
        # Optional conductivity planning if initial and target are provided
        try:
            use_cond = bool(df_cfg.get("use_conductivity", False))  # type: ignore[attr-defined]
        except Exception:
            use_cond = False
        if use_cond:
            try:
                initial_k_mScm = float(df_cfg.get("initial_conductivity_mScm"))  # type: ignore[attr-defined]
            except Exception:
                initial_k_mScm = None
            try:
                target_k_mScm = float(df_cfg.get("target_conductivity_mScm"))  # type: ignore[attr-defined]
            except Exception:
                target_k_mScm = None
        # Auto planning guardrails and options
        try:
            df_time_target = float(df_cfg.get("df_time_h_target"))  # type: ignore[attr-defined]
        except Exception:
            df_time_target = None
        try:
            nd_max = float(df_cfg.get("nd_max"))  # type: ignore[attr-defined]
        except Exception:
            nd_max = None
        try:
            buf_multiple_max = float(df_cfg.get("buffer_multiple_max"))  # type: ignore[attr-defined]
        except Exception:
            buf_multiple_max = None
        try:
            area_max_m2 = float(df_cfg.get("area_max_m2"))  # type: ignore[attr-defined]
        except Exception:
            area_max_m2 = None
        try:
            headroom_override = float(df_cfg.get("headroom_fraction"))  # type: ignore[attr-defined]
        except Exception:
            headroom_override = None
        try:
            viscosity_mPa_s = float(df_cfg.get("viscosity_mPa_s"))  # type: ignore[attr-defined]
        except Exception:
            viscosity_mPa_s = None
        try:
            viscosity_temp_C = float(df_cfg.get("viscosity_temp_C"))  # type: ignore[attr-defined]
        except Exception:
            viscosity_temp_C = None
        try:
            cost_from_registry = bool(df_cfg.get("cost_from_registry", False))  # type: ignore[attr-defined]
        except Exception:
            cost_from_registry = False
        try:
            cost_buffer_id = df_cfg.get("cost_buffer_id")  # type: ignore[attr-defined]
        except Exception:
            cost_buffer_id = None
    if use_planner and target_I_mM is not None:
        nd = compute_nd_from_ionic_strength(
            initial_mM=(capture_handoff.conductivity_mM or 0.0),
            target_mM=target_I_mM,
        )
    elif use_planner and use_cond and initial_k_mScm and target_k_mScm and target_k_mScm > 0.0:
        try:
            if initial_k_mScm > 0.0 and initial_k_mScm > target_k_mScm:
                nd = max(math.log(initial_k_mScm / target_k_mScm), 0.0)
        except Exception:
            pass
    # Auto planner mode: recompute ND, df_time, and area with guardrails
    planner_notes: list[str] = []
    if config.auto_plan and use_planner:
        # Compute ND from ionic strength or conductivity
        nd_calc = nd
        if target_I_mM is not None:
            nd_calc = compute_nd_from_ionic_strength(
                initial_mM=(capture_handoff.conductivity_mM or 0.0),
                target_mM=target_I_mM,
            )
            planner_notes.append(f"Auto ND from ionic strength: {nd_calc:.2f}")
        elif use_cond and initial_k_mScm and target_k_mScm and target_k_mScm > 0.0:
            try:
                if initial_k_mScm > 0.0 and initial_k_mScm > target_k_mScm:
                    import math as _m
                    nd_calc = max(_m.log(initial_k_mScm / target_k_mScm), 0.0)
                    planner_notes.append(f"Auto ND from conductivity: {nd_calc:.2f}")
            except Exception:
                pass
        # Apply caps
        if nd_max is not None and nd_calc > nd_max:
            planner_notes.append(f"ND capped from {nd_calc:.2f} to nd_max={nd_max:.2f}")
            nd_calc = nd_max
        if buf_multiple_max is not None:
            # buffer_multiple = ND (since volume_preUF defines the DF loop volume)
            if nd_calc > buf_multiple_max:
                planner_notes.append(
                    f"ND capped by buffer_multiple_max from {nd_calc:.2f} to {buf_multiple_max:.2f}"
                )
                nd_calc = buf_multiple_max
        nd = nd_calc

        # DF time target
        if df_time_target is not None and df_time_target > 0.0:
            df_time = df_time_target
        # Headroom override
        if headroom_override is not None and headroom_override >= 0.0:
            headroom = headroom_override

        # Apply viscosity-based flux derate if provided
        if viscosity_mPa_s is not None and viscosity_mPa_s > 0.0:
            base_mu = water_viscosity_mPa_s(viscosity_temp_C if viscosity_temp_C is not None else 25.0)
            rv = relative_viscosity(viscosity_mPa_s, base_mu)
            flux = apply_viscosity_flux_derate(flux, rv)
            planner_notes.append(f"Flux derated by viscosity (rv={rv:.2f}) to {flux:.2f} LMH")

    df_buffer_m3 = nd * volume_preuf_m3
    df_permeate_m3 = df_buffer_m3
    flux_m3_m2_h = flux / 1_000.0
    required_area_m2 = df_permeate_m3 / (flux_m3_m2_h * df_time) if flux_m3_m2_h > 0 else 0.0
    installed_area_m2 = required_area_m2 * (1.0 + headroom)
    # Area cap: keep installed area under cap by increasing time
    if config.auto_plan and area_max_m2 and area_max_m2 > 0.0:
        max_required = area_max_m2 / (1.0 + headroom)
        if required_area_m2 > max_required and flux_m3_m2_h > 0.0:
            new_df_time = df_permeate_m3 / (flux_m3_m2_h * max_required)
            planner_notes.append(
                f"DF time increased from {df_time:.2f} h to {new_df_time:.2f} h to hold area ≤ {area_max_m2:.1f} m²"
            )
            df_time = new_df_time
            required_area_m2 = max_required
            installed_area_m2 = area_max_m2

    adsorption_fraction = params.adsorption_loss_per_100_m2 * installed_area_m2 / 100.0
    if adsorption_fraction < 0.0:
        adsorption_fraction = 0.0

    product_after_preuf = product_in * max(1.0 - params.sieving_uf, 0.0)
    product_after_df = product_after_preuf * max(1.0 - params.sieving_df, 0.0)
    product_after_adsorption = product_after_df * max(1.0 - adsorption_fraction, 0.0)

    recovery_fraction = product_after_adsorption / product_in if product_in else 1.0
    output_concentration = product_after_adsorption * 1_000.0 / volume_preuf_l if volume_preuf_l else None

    feed_conductivity = capture_handoff.conductivity_mM or 0.0
    # Optional: infer initial buffer properties from registry if the config provides an ID
    if config.buffers and isinstance(config.buffers.get("df"), Mapping):
        df_cfg = config.buffers.get("df")  # type: ignore[assignment]
        try:
            buffer_id = df_cfg.get("initial_buffer_id")  # type: ignore[attr-defined]
        except Exception:
            buffer_id = None
        if buffer_id and (not feed_conductivity or feed_conductivity <= 0.0):
            try:
                from .buffer_tools.registry import infer_properties
                I_mM, _ = infer_properties(str(buffer_id))
                if I_mM and I_mM > 0.0:
                    feed_conductivity = I_mM
            except Exception:
                pass
    conductivity_out = feed_conductivity * math.exp(-nd) if feed_conductivity else 0.0
    ph_out = capture_handoff.ph if capture_handoff.ph is not None else 7.0

    preuf_time_h = permeate_preuf_m3 / (flux_m3_m2_h * installed_area_m2) if installed_area_m2 > 0 else 0.0

    adsorption_extra = params.antifoam_adsorption_addition_fraction if antifoam_flag else 0.0
    if adsorption_extra:
        product_after_adsorption *= max(1.0 - adsorption_extra, 0.0)
        recovery_fraction = product_after_adsorption / product_in if product_in else 1.0

    total_permeate_m3 = permeate_preuf_m3 + df_permeate_m3
    total_permeate_tonnes = total_permeate_m3  # assume 1 tonne per m3 water

    membrane_cost = 0.0
    if params.membrane_life_batches > 0:
        membrane_cost = installed_area_m2 * params.membrane_cost_per_m2 / params.membrane_life_batches
    # Buffer cost: optionally estimate from curated registry if requested
    buffer_cost_per_m3 = params.buffer_cost_per_m3
    registry_note = None
    if cost_from_registry and cost_buffer_id:
        est = estimate_cost_per_m3_for_buffer_id(str(cost_buffer_id))
        if isinstance(est, (int, float)) and est >= 0.0:
            buffer_cost_per_m3 = float(est)
            registry_note = f"Buffer cost estimated from registry '{cost_buffer_id}': ${buffer_cost_per_m3:.2f}/m³"
    buffer_cost = df_buffer_m3 * buffer_cost_per_m3
    labor_cost = params.labor_hours_per_batch * params.labor_rate_per_hour
    waste_cost = total_permeate_tonnes * params.waste_cost_per_tonne
    total_cost = membrane_cost + buffer_cost + labor_cost + waste_cost

    retentate_density = 1.05
    total_mass_out = volume_preuf_l * retentate_density

    derived = {
        "input_volume_l": volume_l,
        "output_volume_l": volume_preuf_l,
        "input_product_kg": product_in,
        "output_product_kg": product_after_adsorption,
        "output_total_mass_kg": total_mass_out,
        "output_opn_concentration_g_per_l": output_concentration,
        "retentate_density_kg_per_l": retentate_density,
        "df_buffer_volume_m3": df_buffer_m3,
        "df_buffer_volume_l": df_buffer_m3 * 1_000.0,
        "preuf_permeate_volume_m3": permeate_preuf_m3,
        "installed_area_m2": installed_area_m2,
        "required_area_m2": required_area_m2,
        "df_time_h": df_time,
        "preuf_time_h": preuf_time_h,
        "cycle_time_h": preuf_time_h + df_time,
        "step_recovery_fraction": recovery_fraction,
        "output_conductivity_mM": conductivity_out,
        "output_ph": ph_out,
        "membrane_cost_per_batch_usd": membrane_cost,
        "buffer_cost_per_batch_usd": buffer_cost,
        "labor_cost_per_batch_usd": labor_cost,
        "waste_cost_per_batch_usd": waste_cost,
        "total_cost_per_batch_usd": total_cost,
        "mwco_kda": params.mwco_kda,
        "cfv_ms": params.cfv_ms,
    }

    plan = UnitPlan(key=None, data=None, specs=None, derived=derived)
    if upstream_plan and upstream_plan.notes:
        for note in upstream_plan.notes:
            plan.add_note(note)

    notes = [
        f"DSP03 UF→DF→UF baseline: VRR={params.vr_preuf:.1f}×, ND={params.nd:.1f}, flux={params.flux_lmh:.0f} LMH.",
        f"Installed membrane area ≈ {installed_area_m2:.1f} m²; DF buffer ≈ {df_buffer_m3:.2f} m³.",
        f"Step recovery ≈ {recovery_fraction * 100.0:.2f} %.",
    ]
    if planner_notes:
        notes.extend(planner_notes)
    if adsorption_extra:
        notes.append("Antifoam flag detected; applied additional adsorption penalty.")
    if registry_note:
        notes.append(registry_note)

    unit = DSP03UFDFUnit("DSP03_UFDFUF", plan=plan)
    for note in notes:
        unit.plan.add_note(note)

    handoff = CaptureHandoff(
        route=capture_handoff.route,
        pool_volume_l=volume_preuf_l,
        opn_concentration_g_per_l=output_concentration,
        conductivity_mM=conductivity_out,
        ph=ph_out,
        dna_mg_per_l=capture_handoff.dna_mg_per_l,
        chitosan_ppm=capture_handoff.chitosan_ppm,
        polyp_mM=0.0,
        step_recovery_fraction=recovery_fraction,
        needs_df=False,
        needs_fines_polish=False,
        cycle_time_h=preuf_time_h + df_time,
        cost_per_batch=total_cost if capture_handoff.cost_per_batch is None else capture_handoff.cost_per_batch + total_cost,
        notes=list(dict.fromkeys(capture_handoff.notes + notes)),
    )

    return DSP03Chain(
        route=DSP03Route.BASELINE,
        units=[unit],
        handoff=handoff,
        notes=list(dict.fromkeys(notes)),
    )
