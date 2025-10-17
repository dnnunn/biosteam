"""Factories that translate scenario templates into migration-backed units."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, Tuple

import biosteam as bst

from migration.excel_defaults import ExcelModuleDefaults, ModuleKey
from migration.unit_builders import PLAN_BUILDERS, UnitPlan, set_defaults_loader
from migration.unit_factories import PLAN_UNIT_CLASSES

TemplateDefaults = Dict[str, Any]


@dataclass(frozen=True)
class TemplatePlanConfig:
    """Mapping from scenario template to migration plan metadata."""

    module: str
    option: str


_TEMPLATE_TO_PLAN: Dict[str, TemplatePlanConfig] = {
    "SeedFermenter_v1": TemplatePlanConfig(module="USP01", option="USP01a"),
    "ProdFermenter_v2": TemplatePlanConfig(module="USP00", option="USP00a"),
    # Disk stack centrifuge / cell separation
    "DiskStack_v1": TemplatePlanConfig(module="USP03", option="USP03c"),
    # Cell-separation MF polish belongs to USP03 in the baseline model.
    "MF_Polishing_v1": TemplatePlanConfig(module="USP03", option="USP03a"),
    "UFDF_v1": TemplatePlanConfig(module="DSP01", option="DSP01a"),
    "AEX_Column_v1": TemplatePlanConfig(module="DSP02", option="DSP02a"),
    # Chitosan capture is modeled as a DSP02 variant (option 'DSP02e').
    "ChitosanCapture_v1": TemplatePlanConfig(module="DSP02", option="DSP02e"),
    "PreDry_TFF_v1": TemplatePlanConfig(module="DSP03", option="DSP03a"),
    "SterileFilter_v1": TemplatePlanConfig(module="DSP04", option="DSP04d"),
    "SprayDry_v1": TemplatePlanConfig(module="DSP05", option="DSP05a"),
}

SUPPORTED_TEMPLATES: Tuple[str, ...] = tuple(_TEMPLATE_TO_PLAN.keys())


def supports(template: str) -> bool:
    """Return True when ``template`` is backed by the migration plan map."""

    return template in _TEMPLATE_TO_PLAN


@lru_cache
def _load_defaults() -> ExcelModuleDefaults:
    defaults = ExcelModuleDefaults()
    set_defaults_loader(defaults)
    return defaults


def _build_plan(module: str, option: str) -> UnitPlan:
    defaults = _load_defaults()
    config = defaults.get_module_config(ModuleKey(module, option))
    if config is None:
        raise KeyError(f"No module defaults for {module} option {option}")
    builder, _ = PLAN_BUILDERS[module]
    return builder(config)


def _coerce_float(value: Any, fallback: float | None = None) -> float | None:
    if value is None:
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    return None


def _record_overrides(plan: UnitPlan, applied: Dict[str, Any]) -> None:
    if applied:
        plan.add_note("Overrides applied: " + ", ".join(sorted(applied.keys())))
    plan.derived.setdefault("ui_overrides", dict(applied))


def _apply_seed_overrides(plan: UnitPlan, values: TemplateDefaults, applied: Dict[str, Any]) -> None:
    derived = plan.derived
    volume_m3 = _coerce_float(values.get("working_volume_m3"), 7.0)
    if volume_m3 is not None:
        derived["working_volume_l"] = volume_m3 * 1_000.0
    duration_h = _coerce_float(values.get("time_h"))
    if duration_h is not None:
        derived["seed_train_duration_hours"] = duration_h
    biomass_conc = _coerce_float(values.get("dcw_concentration_g_L"), 10.0)
    if biomass_conc is not None:
        derived["dcw_concentration_g_per_l"] = biomass_conc
    density = _coerce_float(values.get("broth_density_kg_per_l"), 1.05)
    if density is not None:
        derived["broth_density_kg_per_l"] = density

    volume_l = derived.get("working_volume_l")
    if volume_l:
        final_biomass = (biomass_conc or 0.0) * volume_l / 1_000.0
        derived.setdefault("initial_biomass_kg", max(final_biomass * 0.1, 0.0))
        derived["target_seed_biomass_kg"] = final_biomass

    biomass_yield = _coerce_float(derived.get("biomass_yield_glucose"), 0.48)
    initial_biomass = _coerce_float(derived.get("initial_biomass_kg"), 0.0) or 0.0
    if biomass_yield and biomass_yield > 0.0:
        delta_biomass = max((derived.get("target_seed_biomass_kg") or 0.0) - initial_biomass, 0.0)
        glucose_required = delta_biomass / biomass_yield
        derived["glucose_required_per_batch_kg"] = glucose_required
        duration = _coerce_float(derived.get("seed_train_duration_hours"))
        if duration and duration > 0.0:
            derived["glucose_feed_rate_kg_per_hr"] = glucose_required / duration
            derived["initial_biomass_feed_rate_kg_per_hr"] = initial_biomass / duration if initial_biomass else 0.0

    _record_overrides(plan, applied)


def _apply_fermentation_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    derived = plan.derived
    specs = plan.specs

    volume_m3 = _coerce_float(values.get("working_volume_m3"), 70.0)
    if volume_m3 is not None:
        derived["working_volume_l"] = volume_m3 * 1_000.0
    cycle_h = _coerce_float(values.get("time_h"))
    if cycle_h is not None:
        derived["batch_cycle_hours"] = cycle_h

    titer = _coerce_float(values.get("titer_g_L"), 5.0) or 0.0
    volume_l = derived.get("working_volume_l") or (volume_m3 or 0.0) * 1_000.0
    product_mass = (titer * volume_l) / 1_000.0 if volume_l else 0.0
    derived["target_product_mass_kg"] = product_mass
    derived["target_titer_g_per_l"] = titer

    yp_x = getattr(specs, "product_yield_biomass", None) or 0.2
    delta_biomass = product_mass / yp_x if yp_x else 0.0
    if volume_l:
        derived["dcw_concentration_g_per_l"] = (delta_biomass * 1_000.0) / volume_l
    derived["initial_biomass_kg"] = max(delta_biomass * 0.1, 0.0)
    derived["product_model"] = "growth_associated"

    biomass_yield_glucose = getattr(specs, "biomass_yield_glucose", None) or 0.48
    if biomass_yield_glucose and biomass_yield_glucose > 0.0:
        glucose_required = delta_biomass / biomass_yield_glucose
        derived["glucose_required_per_batch_kg"] = glucose_required
        # Use provided duration, or fall back to plan defaults, or use 72-hour baseline
        duration = cycle_h or _coerce_float(derived.get("batch_cycle_hours")) or _coerce_float(derived.get("tau_hours")) or 72.0
        if duration and duration > 0.0:
            # Ensure batch_cycle_hours is set for downstream calculations
            derived.setdefault("batch_cycle_hours", duration)
            derived["glucose_feed_rate_kg_per_hr"] = glucose_required / duration
            initial_biomass = derived.get("initial_biomass_kg") or 0.0
            derived["initial_biomass_feed_rate_kg_per_hr"] = initial_biomass / duration if initial_biomass else 0.0

    od_gain = _coerce_float(values.get("od_to_dcw_g_per_l_per_od"), 0.4)
    if od_gain:
        derived["od_to_dcw_g_per_l_per_od"] = od_gain
        dcw = derived.get("dcw_concentration_g_per_l")
        if dcw:
            derived["od600_target"] = dcw / od_gain

    glucose_conc = _coerce_float(values.get("glucose_g_L"))
    if glucose_conc is not None:
        derived["feed_carbon_concentration_g_per_l"] = glucose_conc

    density = _coerce_float(values.get("broth_density_kg_per_l"), 1.05)
    if density is not None:
        derived["broth_density_kg_per_l"] = density

    _record_overrides(plan, applied)


def _apply_microfiltration_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    derived = plan.derived
    specs = getattr(plan, "specs", None)

    area = _coerce_float(values.get("area_m2"))
    flux = _coerce_float(values.get("flux_L_m2_h"))
    efficiency = _coerce_float(values.get("yield_fraction"))
    dilution_m3 = _coerce_float(values.get("dilution_volume_m3"))
    dilution_l = _coerce_float(values.get("dilution_volume_l")) if dilution_m3 is None else None
    membrane_cost_per_m2 = _coerce_float(values.get("membrane_cost_usd_m2"))
    lifetime_cycles = _coerce_float(values.get("lifetime_cycles"))

    # Default MF efficiency (90% baseline for polishing step)
    if efficiency is None:
        efficiency = 0.90

    if specs is not None:
        if area is not None:
            setattr(specs, "membrane_area_m2", area)
        if flux is not None:
            setattr(specs, "flux_l_m2_h", flux)
        setattr(specs, "efficiency", max(min(efficiency, 1.0), 0.0))
        if dilution_m3 is not None:
            setattr(specs, "dilution_volume_l", dilution_m3 * 1_000.0)
            derived["dilution_volume_m3"] = dilution_m3
        elif dilution_l is not None:
            setattr(specs, "dilution_volume_l", dilution_l)
            derived["dilution_volume_m3"] = dilution_l / 1_000.0
        if lifetime_cycles is not None:
            setattr(specs, "membrane_lifetime", lifetime_cycles)
        if membrane_cost_per_m2 is not None:
            effective_area = getattr(specs, "membrane_area_m2", area) or area
            total_cost = membrane_cost_per_m2 * (effective_area or 1.0)
            setattr(specs, "membrane_cost", total_cost)
        if getattr(specs, "flux_l_m2_h", None) and getattr(specs, "membrane_area_m2", None):
            derived["throughput_l_per_hr"] = specs.flux_l_m2_h * specs.membrane_area_m2
        cost = getattr(specs, "membrane_cost", None)
        life = getattr(specs, "membrane_lifetime", None)
        if cost is not None and life not in (None, 0.0):
            derived["membrane_cost_per_cycle"] = cost / life

    density = _coerce_float(values.get("broth_density_kg_per_l"), derived.get("broth_density_kg_per_l"))
    if density is not None:
        derived["broth_density_kg_per_l"] = density
    _record_overrides(plan, applied)


def _apply_ufdf_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    derived = plan.derived
    specs = getattr(plan, "specs", None)

    area = _coerce_float(values.get("area_m2"))
    flux = _coerce_float(values.get("flux_L_m2_h"))
    concentration_factor = _coerce_float(values.get("cff"))
    efficiency = _coerce_float(values.get("yield_fraction"))
    dia_volumes = _coerce_float(values.get("diafiltration_volumes"))
    membrane_cost_per_m2 = _coerce_float(values.get("membrane_cost_usd_m2"))
    lifetime_cycles = _coerce_float(values.get("lifetime_cycles"))

    if specs is not None:
        if area is not None:
            setattr(specs, "membrane_area_m2", area)
        if flux is not None:
            setattr(specs, "flux_l_m2_h", flux)
        if concentration_factor is not None:
            setattr(specs, "concentration_factor", max(concentration_factor, 1.0))
        if efficiency is not None:
            setattr(specs, "efficiency", max(min(efficiency, 1.0), 0.0))
        if dia_volumes is not None:
            setattr(specs, "diafiltration_volumes", max(dia_volumes, 0.0))
        if lifetime_cycles is not None:
            setattr(specs, "membrane_lifetime", lifetime_cycles)
        if membrane_cost_per_m2 is not None:
            effective_area = getattr(specs, "membrane_area_m2", area) or area
            total_cost = membrane_cost_per_m2 * (effective_area or 1.0)
            setattr(specs, "membrane_cost", total_cost)
        if getattr(specs, "flux_l_m2_h", None) and getattr(specs, "membrane_area_m2", None):
            derived["throughput_l_per_hr"] = specs.flux_l_m2_h * specs.membrane_area_m2
        if getattr(specs, "diafiltration_volumes", None) is not None:
            derived["diafiltration_volumes"] = specs.diafiltration_volumes
        cost = getattr(specs, "membrane_cost", None)
        life = getattr(specs, "membrane_lifetime", None)
        if cost is not None and life not in (None, 0.0):
            derived["membrane_cost_per_cycle"] = cost / life

    density = _coerce_float(values.get("broth_density_kg_per_l"), derived.get("broth_density_kg_per_l"))
    if density is not None:
        derived["broth_density_kg_per_l"] = density
    _record_overrides(plan, applied)


def _apply_chromatography_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    derived = plan.derived
    specs = getattr(plan, "specs", None)

    resin_capacity = _coerce_float(values.get("resin_capacity_g_L"))
    bed_volume = _coerce_float(values.get("bed_volume_L"))
    flow_bv_h = _coerce_float(values.get("flow_BV_h"))
    yield_fraction = _coerce_float(values.get("yield_fraction"))
    resin_cost = _coerce_float(values.get("resin_cost_usd_per_L"))
    lifetime_cycles = _coerce_float(values.get("lifetime_cycles"))

    # Default AEX chromatography yield (85% baseline)
    if yield_fraction is None:
        yield_fraction = 0.85

    if specs is not None:
        if resin_capacity is not None:
            setattr(specs, "dynamic_binding_capacity_g_per_l", resin_capacity)
            setattr(specs, "dbc_g_per_l", resin_capacity)
        if bed_volume is not None:
            setattr(specs, "resin_column_volume_l", bed_volume)
        setattr(specs, "chromatography_yield", max(min(yield_fraction, 1.0), 0.0))
        if resin_cost is not None:
            setattr(specs, "resin_cost_per_l", resin_cost)
        if lifetime_cycles is not None:
            setattr(specs, "resin_lifetime_cycles", lifetime_cycles)
        resin_batch = specs.resin_cost_per_batch()
        if resin_batch is not None:
            derived["resin_cost_per_batch"] = resin_batch

    if flow_bv_h is not None:
        derived["processing_flow_BV_per_hr"] = flow_bv_h
    _record_overrides(plan, applied)


def _apply_chitosan_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    """Map UI overrides for Chitosan capture into plan hints.

    Chitosan capture rides on the DSP02 plan machinery but uses different
    parameters than packed-bed chromatography. We record its key values in
    ``plan.derived`` and reuse ``chromatography_yield`` as overall recovery
    so runtime units can apply a recovery fraction consistently.
    """
    derived = plan.derived
    specs = getattr(plan, "specs", None)

    overall_yield = _coerce_float(values.get("yield_fraction"))
    # Default chitosan capture yield (80% baseline)
    if overall_yield is None:
        overall_yield = 0.80

    overall_yield = max(min(overall_yield, 1.0), 0.0)
    if specs is not None:
        # Reuse chromatography_yield field so the runtime step can apply recovery.
        setattr(specs, "chromatography_yield", overall_yield)
    derived["overall_recovery"] = overall_yield

    # Record process conditions and economics for downstream reporting.
    polymer_type = values.get("polymer_type")
    if polymer_type is not None:
        derived["polymer_type"] = str(polymer_type)
    pct_wv = _coerce_float(values.get("polymer_pct_wv"))
    if pct_wv is not None:
        derived["polymer_pct_wv"] = pct_wv
    target_pH = _coerce_float(values.get("target_pH"))
    if target_pH is not None:
        derived["adsorption_pH"] = target_pH
    nacl_mM = _coerce_float(values.get("NaCl_mM"))
    if nacl_mM is not None:
        derived["adsorption_NaCl_mM"] = nacl_mM
    ratio = _coerce_float(values.get("stoichiometry_mass_ratio"))
    if ratio is not None:
        derived["polymer_opn_ratio"] = ratio
    contact_min = _coerce_float(values.get("contact_time_min"))
    if contact_min is not None:
        derived["contact_time_min"] = contact_min
    dna_log = _coerce_float(values.get("dna_reduction_log"))
    if dna_log is not None:
        derived["dna_reduction_log"] = dna_log
    recycle = _coerce_float(values.get("recycle_fraction"))
    if recycle is not None:
        derived["polymer_recycle_fraction"] = max(min(recycle, 1.0), 0.0)
    polymer_cost = _coerce_float(values.get("polymer_cost_usd_per_kg"))
    if polymer_cost is not None:
        derived["polymer_cost_per_kg"] = polymer_cost

    _record_overrides(plan, applied)


def _apply_predrying_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    derived = plan.derived
    specs = getattr(plan, "specs", None)

    area = _coerce_float(values.get("area_m2"))
    flux = _coerce_float(values.get("flux_L_m2_h"))
    concentration_factor = _coerce_float(values.get("cff"))
    efficiency = _coerce_float(values.get("yield_fraction"))
    membrane_cost_per_m2 = _coerce_float(values.get("membrane_cost_usd_m2"))
    lifetime_cycles = _coerce_float(values.get("lifetime_cycles"))

    if specs is not None:
        if area is not None:
            setattr(specs, "membrane_area_m2", area)
        if flux is not None:
            setattr(specs, "flux_l_m2_h", flux)
        if concentration_factor is not None:
            setattr(specs, "concentration_factor", max(concentration_factor, 1.0))
        if efficiency is not None:
            setattr(specs, "efficiency", max(min(efficiency, 1.0), 0.0))

    if lifetime_cycles is not None and membrane_cost_per_m2 is not None:
        effective_area = area
        if specs is not None:
            effective_area = getattr(specs, "membrane_area_m2", area)
        if effective_area:
            total_cost = membrane_cost_per_m2 * effective_area
            derived["membrane_cost_per_cycle"] = total_cost / max(lifetime_cycles, 1.0)
    if specs is not None and getattr(specs, "flux_l_m2_h", None) and getattr(specs, "membrane_area_m2", None):
        derived["throughput_l_per_hr"] = specs.flux_l_m2_h * specs.membrane_area_m2
    density = _coerce_float(values.get("broth_density_kg_per_l"), derived.get("broth_density_kg_per_l"))
    if density is not None:
        derived["broth_density_kg_per_l"] = density
    _record_overrides(plan, applied)


def _apply_sterile_filter_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    derived = plan.derived
    specs = getattr(plan, "specs", None)

    flux = _coerce_float(values.get("flux_lmh"))
    max_dp = _coerce_float(values.get("max_dp_bar"))
    loss_fraction = _coerce_float(values.get("adsorption_loss_fraction"))
    prefilter = _coerce_bool(values.get("prefilter_enabled"))

    # Default adsorption loss for sterile filtration (0.05% baseline)
    if loss_fraction is None:
        loss_fraction = 0.0005
    loss_fraction = max(min(loss_fraction, 1.0), 0.0)

    if specs is not None:
        if flux is not None:
            setattr(specs, "flux_lmh", flux)
        if max_dp is not None:
            setattr(specs, "max_delta_p_bar", max_dp)
        setattr(specs, "adsorption_loss_fraction", loss_fraction)
        if prefilter is not None:
            setattr(specs, "prefilter_enabled", prefilter)

    if flux is not None:
        derived["flux_lmh"] = flux
    if max_dp is not None:
        derived["max_delta_p_bar"] = max_dp
    derived["adsorption_loss_fraction"] = loss_fraction
    derived["sterile_filter_yield"] = max(1.0 - loss_fraction, 0.0)
    if prefilter is not None:
        derived["prefilter_enabled"] = prefilter

    _record_overrides(plan, applied)


def _apply_spray_dryer_overrides(
    plan: UnitPlan,
    values: TemplateDefaults,
    applied: Dict[str, Any],
) -> None:
    derived = plan.derived
    specs = getattr(plan, "specs", None)

    efficiency = _coerce_float(values.get("yield_fraction"))
    capacity = _coerce_float(values.get("evap_rate_kg_h"))
    final_solids = _coerce_float(values.get("final_solids_fraction"))
    if final_solids is None:
        solids_percent = _coerce_float(values.get("final_solids_percent"))
        if solids_percent is not None:
            final_solids = solids_percent / 100.0
    density = _coerce_float(values.get("solution_density"))

    if specs is not None:
        if efficiency is not None:
            setattr(specs, "spray_dryer_efficiency", max(min(efficiency, 1.0), 0.0))
        if capacity is not None:
            setattr(specs, "spray_dryer_capacity_kg_per_hr", capacity)
        if final_solids is not None:
            setattr(specs, "final_solids_content", max(min(final_solids, 1.0), 0.0))
        if density is not None:
            setattr(specs, "solution_density", density)

    if final_solids is not None:
        derived["final_solids_mass_fraction"] = final_solids
        derived["final_solids_percent"] = final_solids * 100.0
    if density is not None:
        derived["input_density_kg_per_l"] = density
    if capacity is not None:
        derived["dryer_capacity_kg_per_hr"] = capacity
    _record_overrides(plan, applied)


def _plan_overrides(template: str, defaults: TemplateDefaults, overrides: Dict[str, Any]) -> Dict[str, Any]:
    applied: Dict[str, Any] = {}
    for key, value in overrides.items():
        if value is None:
            continue
        default_value = defaults.get(key)
        if default_value != value:
            applied[key] = value
    return applied


def _apply_overrides(template: str, plan: UnitPlan, defaults: TemplateDefaults, overrides: Dict[str, Any]) -> None:
    merged = dict(defaults)
    merged.update(overrides)
    applied = _plan_overrides(template, defaults, overrides)
    if template == "SeedFermenter_v1":
        _apply_seed_overrides(plan, merged, applied)
    elif template == "ProdFermenter_v2":
        _apply_fermentation_overrides(plan, merged, applied)
    elif template == "MF_Polishing_v1":
        _apply_microfiltration_overrides(plan, merged, applied)
    elif template == "UFDF_v1":
        _apply_ufdf_overrides(plan, merged, applied)
    elif template == "AEX_Column_v1":
        _apply_chromatography_overrides(plan, merged, applied)
    elif template == "ChitosanCapture_v1":
        _apply_chitosan_overrides(plan, merged, applied)
    elif template == "PreDry_TFF_v1":
        _apply_predrying_overrides(plan, merged, applied)
    elif template == "SterileFilter_v1":
        _apply_sterile_filter_overrides(plan, merged, applied)
    elif template == "SprayDry_v1":
        _apply_spray_dryer_overrides(plan, merged, applied)
    else:
        _record_overrides(plan, applied)


def _build_unit(template: str, unit_id: str, plan: UnitPlan) -> bst.Unit:
    plan_config = _TEMPLATE_TO_PLAN[template]
    cls, _ = PLAN_UNIT_CLASSES[plan_config.module]
    unit = cls(unit_id, plan=plan)
    if not hasattr(unit, "metadata_dict"):
        def metadata_dict(plan_ref: UnitPlan = plan) -> Dict[str, Any]:
            data: Dict[str, Any] = {
                "module": plan_ref.key.module,
                "option": plan_ref.key.option,
            }
            data.update(plan_ref.derived)
            if plan_ref.notes:
                data["notes"] = list(plan_ref.notes)
            return data

        setattr(unit, "metadata_dict", metadata_dict)
    return unit


def create_factory(template: str, descriptor: Dict[str, Any]) -> Callable[..., bst.Unit]:
    """Return a callable that builds migration-backed units for ``template``."""

    if template not in _TEMPLATE_TO_PLAN:
        raise KeyError(f"Migrations do not support template {template}")

    defaults = dict(descriptor.get("defaults") or {})
    plan_info = _TEMPLATE_TO_PLAN[template]

    def factory(id: str, **overrides: Any) -> bst.Unit:
        user_overrides = dict(overrides or {})
        option = user_overrides.pop("plan_option", plan_info.option)
        plan = _build_plan(plan_info.module, str(option))
        # Apply overrides after plan creation so derived fields reflect UI inputs.
        _apply_overrides(template, plan, defaults, user_overrides)
        unit = _build_unit(template, id, plan)
        setattr(unit, "ui_category", descriptor.get("category"))
        setattr(unit, "ui_overrides", dict(user_overrides))
        setattr(unit, "ui_plan_option", option)
        return unit

    return factory


__all__ = [
    "SUPPORTED_TEMPLATES",
    "supports",
    "create_factory",
]
