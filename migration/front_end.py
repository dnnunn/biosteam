"""Helpers to assemble the upstream (front-end) section of the migration flowsheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import math
from typing import Any, Dict, Iterable, Mapping, Optional

import biosteam as bst
from .cmo_contracts import (
    CMODiscounts,
    CMORates,
    CMOStructure,
    CMOTimings,
    StageCostSummary,
    compute_contract_stage_costs,
)
from .unit_specs import DepthFilterSpecs
from .excel_defaults import ExcelModuleDefaults, ModuleConfig, ModuleKey
from .module_registry import ModuleRegistry
from .unit_builders import register_baseline_unit_builders, set_defaults_loader
from .unit_factories import register_plan_backed_unit_factories
from .cell_removal import build_cell_removal_chain
from .capture import build_capture_chain, CaptureHandoff, CaptureRoute
from .concentration import build_concentration_chain
from .dsp03 import build_dsp03_chain
from .dsp04 import build_dsp04_chain
from .dsp05 import build_dsp05_chain, FinalProductHandoff, DSP05Config
from .usp01 import SeedConfig, determine_seed_method
from .usp02 import ProductionConfig, determine_production_method
from .thermo_setup import set_migration_thermo
from .baseline_config import load_baseline_defaults, DEFAULT_BASELINE_CONFIG
from .usp_profiles import load_seed_fermentation_profile
from .cmo_resin_allocation import CMOResinAllocation, compute_allocation

FRONT_END_KEYS = (
    ModuleKey("USP01", "USP01a"),
    ModuleKey("USP00", "USP00a"),
    ModuleKey("USP02", "USP02a"),
    ModuleKey("DSP01", "DSP01a"),
    ModuleKey("DSP02", "DSP02a"),
    ModuleKey("DSP03", "DSP03a"),
    ModuleKey("DSP05", "DSP05a"),
)


@dataclass
class FrontEndSection:
    """Container with the simulated seed-through-drying unit operations."""

    feed: bst.Stream
    seed_unit: bst.Unit
    fermentation_unit: bst.Unit
    microfiltration_unit: bst.Unit
    cell_removal_units: tuple[bst.Unit, ...]
    concentration_units: tuple[bst.Unit, ...]
    ufdf_unit: bst.Unit
    chromatography_unit: bst.Unit
    predrying_unit: bst.Unit
    spray_dryer_unit: bst.Unit
    system: bst.System
    defaults: ExcelModuleDefaults
    ufdf_in_system: bool = True
    fermentation_handoff_stream: Optional[bst.Stream] = None
    total_cost_per_batch_usd: Optional[float] = None
    cmo_fees_usd: Optional[float] = None
    cost_per_kg_usd: Optional[float] = None
    materials_cost_per_batch_usd: Optional[float] = None
    computed_material_cost_per_batch_usd: Optional[float] = None
    capture_handoff: Optional[CaptureHandoff] = None
    capture_units: tuple[bst.Unit, ...] = field(default_factory=tuple)
    dsp03_units: tuple[bst.Unit, ...] = field(default_factory=tuple)
    dsp04_units: tuple[bst.Unit, ...] = field(default_factory=tuple)
    dsp04_handoff: Optional[CaptureHandoff] = None
    dsp05_handoff: Optional[FinalProductHandoff] = None
    material_cost_breakdown: Dict[str, float] = field(default_factory=dict)
    cmo_profile_name: str = "conservative_cmo_default"
    cmo_stage_costs: Dict[str, StageCostSummary] = field(default_factory=dict)
    cmo_total_fee_usd: float = 0.0
    batches_per_campaign: float = 1.0
    cmo_standard_batch_usd: Optional[float] = None
    cmo_campaign_adders_usd: Optional[float] = None
    materials_cost_per_kg_usd: Optional[float] = None
    cmo_cost_per_kg_usd: Optional[float] = None
    cmo_standard_cost_per_kg_usd: Optional[float] = None
    cmo_campaign_cost_per_kg_usd: Optional[float] = None
    cmo_retainer_annual_usd: Optional[float] = None
    handoff_streams: Dict[str, bst.Stream] = field(default_factory=dict)
    _allocation_result: Optional[CMOResinAllocation] = None
    allocation_inputs: Dict[str, Any] = field(default_factory=dict)

    def units(self) -> tuple[bst.Unit, ...]:
        """Return the ordered unit operations for convenience."""

        units: list[bst.Unit] = [
            self.seed_unit,
            self.fermentation_unit,
            *self.cell_removal_units,
        ]
        units.extend(self.concentration_units)
        if self.ufdf_in_system:
            units.append(self.ufdf_unit)
        units.append(self.chromatography_unit)
        units.extend(self.capture_units)
        units.extend(self.dsp03_units)
        units.append(self.predrying_unit)
        units.extend(self.dsp04_units)
        units.append(self.spray_dryer_unit)
        return tuple(units)

    def simulate(self, *, design: bool = False, cost: bool = False) -> None:
        """Run the front-end units in sequence using plan-derived targets."""

        for unit in self.units():
            unit._run()
            if design:
                unit._design()
            if cost:
                unit._cost()
        self._refresh_post_simulation_metrics()

    @property
    def allocation_result(self) -> Optional[CMOResinAllocation]:
        self._refresh_post_simulation_metrics()
        return self._allocation_result

    @allocation_result.setter
    def allocation_result(self, value: Optional[CMOResinAllocation]) -> None:
        self._allocation_result = value

    def _refresh_post_simulation_metrics(self) -> None:
        """Update allocation/per-kg summaries after the flowsheet runs."""

        allocation = self._allocation_result
        if allocation is None or not self.allocation_inputs:
            return

        final_mass_per_batch = _coerce_float(
            self.spray_dryer_unit.plan.derived.get("product_out_kg"),
            0.0,
        )
        if final_mass_per_batch <= 0.0:
            return

        batches_executed = _coerce_float(
            allocation.metadata.get("batches_executed"),
            0.0,
        )
        if batches_executed <= 0.0:
            return

        total_kg_released = final_mass_per_batch * batches_executed

        recorded_total = allocation.metadata.get("total_kg_released")
        if recorded_total is None or not math.isclose(
            recorded_total,
            total_kg_released,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            inputs = dict(self.allocation_inputs)
            inputs["total_kg_released"] = total_kg_released
            try:
                allocation = compute_allocation(**inputs)
            except Exception:
                return
            self._allocation_result = allocation
            self.allocation_inputs = inputs
            if allocation is None:
                return

        def _safe_divide(numerator: float, denominator: float):
            if denominator == 0.0:
                return None
            return numerator / denominator

        metadata = dict(allocation.metadata)
        metadata["total_kg_released"] = total_kg_released

        self._allocation_result = CMOResinAllocation(
            basis=allocation.basis,
            denominator_label=allocation.denominator_label,
            denominator_value=total_kg_released,
            cmo_fixed_total_usd=allocation.cmo_fixed_total_usd,
            cmo_variable_total_usd=allocation.cmo_variable_total_usd,
            cmo_total_usd=allocation.cmo_total_usd,
            resin_amort_total_usd=allocation.resin_amort_total_usd,
            resin_cip_total_usd=allocation.resin_cip_total_usd,
            resin_total_usd=allocation.resin_total_usd,
            pooled_total_usd=allocation.pooled_total_usd,
            cmo_per_unit_usd=_safe_divide(allocation.cmo_total_usd, total_kg_released),
            resin_per_unit_usd=_safe_divide(allocation.resin_total_usd, total_kg_released),
            total_per_unit_usd=_safe_divide(
                allocation.pooled_total_usd, total_kg_released
            ),
            metadata=metadata,
        )

        self.cost_per_kg_usd = _safe_divide(
            self.total_cost_per_batch_usd or 0.0,
            final_mass_per_batch,
        )
        self.materials_cost_per_kg_usd = _safe_divide(
            self.materials_cost_per_batch_usd or 0.0,
            final_mass_per_batch,
        )
        self.cmo_cost_per_kg_usd = _safe_divide(
            self.cmo_total_fee_usd or 0.0,
            final_mass_per_batch,
        )
        self.cmo_standard_cost_per_kg_usd = _safe_divide(
            self.cmo_standard_batch_usd or 0.0,
            final_mass_per_batch,
        )
        self.cmo_campaign_cost_per_kg_usd = _safe_divide(
            self.cmo_campaign_adders_usd or 0.0,
            final_mass_per_batch,
        )


def _register_front_end_builders(
    registry: ModuleRegistry,
    *,
    module_options: Optional[Dict[str, Iterable[str]]] = None,
) -> None:
    module_options = module_options or {
        "USP00": ("USP00a",),
        "USP01": ("USP01a",),
        "USP02": ("USP02a",),
    }
    register_baseline_unit_builders(registry, module_options=module_options)
    register_plan_backed_unit_factories(registry, module_options=module_options)


def _get_parameter(
    defaults: ExcelModuleDefaults,
    module: str,
    option: Optional[str],
    name: str,
) -> Optional[float]:
    config = defaults.get_module_config(ModuleKey(module, option))
    if config is None:
        return None
    record = config.parameters.get(name)
    if record is None:
        return None
    return record.value


def _coerce_float(value: Any, default: float = 0.0) -> float:
    """Best-effort conversion of ``value`` to float with a fallback."""

    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _capture_cip_cost_per_batch(plan: Any) -> float:
    """Estimate the capture CIP spend captured in buffer fees per batch."""

    derived = getattr(plan, "derived", {})
    volumes = derived.get("buffer_volumes_l")
    if not isinstance(volumes, Mapping):
        return 0.0
    cip_volume_l = volumes.get("cip")
    if cip_volume_l in (None, 0):
        return 0.0
    try:
        cip_volume_l = float(cip_volume_l)
    except (TypeError, ValueError):
        return 0.0
    if cip_volume_l <= 0.0:
        return 0.0
    specs = getattr(plan, "specs", None)
    fee_per_m3 = getattr(specs, "cip_fee_per_m3", None)
    if fee_per_m3 in (None, 0):
        return 0.0
    try:
        fee_per_m3 = float(fee_per_m3)
    except (TypeError, ValueError):
        return 0.0
    if fee_per_m3 <= 0.0:
        return 0.0
    return fee_per_m3 * (cip_volume_l / 1_000.0)


def _compute_media_cost(
    media_cfg: Mapping[str, Any],
    working_volume_l: float,
) -> tuple[float, Dict[str, float]]:
    """Calculate salts/trace media cost and optional CSL addition."""

    volume_m3 = max(_coerce_float(working_volume_l, 0.0) / 1_000.0, 0.0)
    costs_cfg = media_cfg.get("costs", {}) if isinstance(media_cfg, Mapping) else {}

    salts_cost = _coerce_float(costs_cfg.get("salts_usd_per_m3"), 0.0) * volume_m3
    ptm_cost = _coerce_float(costs_cfg.get("ptm1_usd_per_m3"), 0.0) * volume_m3

    csl_cost = 0.0
    csl_cfg = media_cfg.get("csl") if isinstance(media_cfg, Mapping) else None
    if isinstance(csl_cfg, Mapping) and csl_cfg.get("enable"):
        csl_g_per_l = _coerce_float(csl_cfg.get("g_per_l"), 0.0)
        csl_usd_per_kg = _coerce_float(
            csl_cfg.get("usd_per_kg"),
            _coerce_float(costs_cfg.get("csl_usd_per_kg"), 0.0),
        )
        csl_mass_kg = csl_g_per_l * working_volume_l / 1_000.0
        csl_cost = csl_mass_kg * csl_usd_per_kg

    breakdown = {
        "salts_usd": salts_cost,
        "ptm1_usd": ptm_cost,
    }
    if csl_cost:
        breakdown["csl_usd"] = csl_cost

    total = salts_cost + ptm_cost + csl_cost
    return total, breakdown


def _estimate_depth_filter_hours(plan: Any) -> float:
    """Estimate depth-filter processing time from flux and specific capacity."""

    volume_l = _coerce_float(plan.derived.get("input_volume_l"), 0.0)
    if volume_l <= 0.0:
        volume_l = _coerce_float(plan.derived.get("harvest_volume_l"), 0.0)
    if volume_l <= 0.0:
        return 0.0

    throughput = _coerce_float(plan.derived.get("throughput_l_per_hr"), 0.0)
    if throughput > 0.0:
        return volume_l / throughput

    specs = getattr(plan, "specs", None)
    if not isinstance(specs, DepthFilterSpecs):
        return 0.0

    flux = _coerce_float(getattr(specs, "flux_lmh", None), 0.0)
    capacities = [
        _coerce_float(cap, 0.0)
        for cap in (specs.specific_capacity_l_per_m2 or [])
        if cap
    ]
    if flux <= 0.0 or not capacities:
        return 0.0

    limiting_capacity = min(capacities)
    if limiting_capacity <= 0.0:
        return 0.0

    area_m2 = volume_l / limiting_capacity
    throughput = flux * area_m2
    if throughput <= 0.0:
        return 0.0
    return volume_l / throughput


def _estimate_ufdf_hours(plan: Any) -> float:
    """Estimate UF/DF time from throughput and diavolumes."""

    total, _, _ = _ufdf_time_breakdown(plan)
    return total


def _ufdf_time_breakdown(plan: Any) -> tuple[float, float, float]:
    """Return total, UF-only, and DF-only processing hours."""

    throughput = _coerce_float(plan.derived.get("throughput_l_per_hr"), 0.0)
    if throughput <= 0.0:
        return 0.0, 0.0, 0.0

    input_volume = _coerce_float(plan.derived.get("input_volume_l"), 0.0)
    output_volume = _coerce_float(plan.derived.get("output_volume_l"), 0.0)
    dia_volumes = _coerce_float(
        plan.derived.get("dia_volumes"),
        _coerce_float(plan.derived.get("diafiltration_volumes"), 0.0),
    )

    uf_time = input_volume / throughput if input_volume > 0 else 0.0
    df_time = 0.0
    if dia_volumes > 0 and output_volume > 0:
        df_time = (dia_volumes * output_volume) / throughput

    total_time = uf_time + df_time
    if total_time <= 0.0 and input_volume > 0:
        total_time = input_volume / throughput

    return total_time, uf_time, df_time


def _estimate_tff_hours(plan: Any) -> float:
    """Estimate post-capture TFF processing time."""

    throughput = _coerce_float(plan.derived.get("throughput_l_per_hr"), 0.0)
    volume = _coerce_float(plan.derived.get("input_volume_l"), 0.0)
    if throughput <= 0.0 or volume <= 0.0:
        return 0.0
    return volume / throughput


def _estimate_spray_hours(predry_plan: Any, spray_plan: Any) -> float:
    """Estimate spray dryer occupancy based on evaporation duty."""

    capacity = _coerce_float(spray_plan.derived.get("capacity_kg_per_hr"), 0.0)
    if capacity <= 0.0:
        return 0.0

    feed_volume_l = _coerce_float(predry_plan.derived.get("output_volume_l"), 0.0)
    if feed_volume_l <= 0.0:
        feed_volume_l = _coerce_float(predry_plan.derived.get("input_volume_l"), 0.0)
    if feed_volume_l <= 0.0:
        return 0.0

    density = _coerce_float(spray_plan.derived.get("solution_density"), 1.0)
    feed_mass = feed_volume_l * density

    final_product_mass = _coerce_float(spray_plan.derived.get("product_out_kg"), 0.0)
    recovery = _coerce_float(spray_plan.derived.get("target_recovery_rate"), 0.0)
    upstream_solids = final_product_mass / recovery if recovery > 0.0 else final_product_mass

    water_evap = max(feed_mass - upstream_solids, 0.0)
    if water_evap <= 0.0:
        return 0.0

    return water_evap / capacity


def _get_module_parameter(
    defaults: ExcelModuleDefaults,
    module: str,
    option: Optional[str],
    name: str,
) -> Optional[float]:
    config = defaults.get_module_config(ModuleKey(module, option))
    if config is None:
        return None
    record = config.parameters.get(name)
    if record is None:
        return None
    return record.value


def _section_mapping(overrides: Mapping[str, Any], section: str) -> Mapping[str, Any]:
    data = overrides.get(section)
    return data if isinstance(data, Mapping) else {}


def _section_values(
    overrides: Mapping[str, Any],
    section: str,
    category: str,
) -> Mapping[str, Any]:
    section_data = _section_mapping(overrides, section)
    values = section_data.get(category)
    return values if isinstance(values, Mapping) else {}


def _apply_plan_overrides(plan: Any, overrides: Optional[Dict[str, Any]]) -> None:
    if not overrides:
        return
    derived = overrides.get("derived")
    if derived:
        plan.derived.update(derived)
    specs_overrides = overrides.get("specs")
    if specs_overrides:
        specs = getattr(plan, "specs", None)
        if specs is not None:
            for key, value in specs_overrides.items():
                setattr(specs, key, value)


def _apply_fermentation_override(
    plan: Any,
    override: Mapping[str, Any],
) -> list[str]:
    """Apply structured fermentation override fields and return advisory notes."""

    notes: list[str] = []
    feed_cfg = override.get("feed") if isinstance(override, Mapping) else None
    method = override.get("method") if isinstance(override, Mapping) else None
    media_type = None
    yield_proxy = None

    if isinstance(feed_cfg, Mapping):
        media_type = feed_cfg.get("media_type")
        yield_proxy = feed_cfg.get("yield_proxy")
        for key, value in feed_cfg.items():
            if value is None:
                continue
            if key in {
                "working_volume_l",
                "target_titer_g_per_l",
                "oxygen_enrichment_fraction",
                "carbon_source",
                "media_type",
                "yield_proxy",
            }:
                plan.derived[key] = value
            else:
                plan.derived[key] = value

    derived_cfg = override.get("derived") if isinstance(override, Mapping) else None
    if isinstance(derived_cfg, Mapping):
        for key, value in derived_cfg.items():
            if value is not None:
                plan.derived[key] = value

    specs_cfg = override.get("specs") if isinstance(override, Mapping) else None
    if isinstance(specs_cfg, Mapping):
        specs = getattr(plan, "specs", None)
        for key, value in specs_cfg.items():
            if value is None:
                continue
            if specs is not None and hasattr(specs, key):
                setattr(specs, key, value)
            else:
                plan.derived[key] = value

    media_cfg = override.get("media") if isinstance(override, Mapping) else None
    if isinstance(media_cfg, Mapping):
        plan.derived.setdefault("media", media_cfg)
        working_volume_l = plan.derived.get("working_volume_l")
        if working_volume_l is not None:
            media_cost, breakdown = _compute_media_cost(media_cfg, working_volume_l)
            plan.derived["media_cost_per_batch_usd"] = media_cost
            plan.derived["media_cost_breakdown_usd"] = breakdown
        else:
            notes.append(
                "Fermentation media override supplied without working_volume_l; cannot compute base media cost."
            )

    descriptor = method or "custom"
    if method or media_type or yield_proxy:
        notes.append(
            f"Fermentation override '{descriptor}' applied"
            f" (media={media_type or 'n/a'}, proxy={yield_proxy or 'baseline'})"
        )

    return notes


def _build_seed_media_stream(
    *,
    fermentation_unit: bst.Unit,
    seed_unit: bst.Unit,
    seed_volume_l: float,
    dcw_concentration_g_per_l: Optional[float],
) -> bst.Stream:
    feed = bst.Stream("seed_media", T=298.15, P=101325.0)

    # Base assumption: bulk density of 1 kg/L for the broth.
    total_mass = seed_volume_l  # kg
    plan = fermentation_unit.plan
    derived = plan.derived
    feed_carbon = derived.get("feed_carbon_concentration_g_per_l") or derived.get(
        "initial_carbon_concentration_g_per_l"
    )
    carbon_mass = (feed_carbon or 0.0) * seed_volume_l / 1e3
    water_mass = max(total_mass - carbon_mass, 0.0)

    feed.imass["Water"] = water_mass

    carbon_source = derived.get("carbon_source") or seed_unit.plan.derived.get(
        "carbon_source"
    )
    component_map = {
        "glucose": "Glucose",
        "glycerol": "Glycerol",
        "lactose": "Lactose",
        "molasses": "Molasses",
    }
    component_id = component_map.get(str(carbon_source).strip().lower(), "Glucose")

    if carbon_mass > 0:
        feed.imass[component_id] = carbon_mass

    specs = seed_unit.plan.specs
    def _add_if_available(component: str, value: Optional[float]) -> None:
        if value is None:
            return
        mass = value * seed_volume_l / 1e3
        if mass <= 0:
            return
        feed.imass[component] += mass

    _add_if_available("YeastExtract", specs.yeast_extract_concentration_g_per_l)
    _add_if_available("Peptone", specs.peptone_concentration_g_per_l)

    if dcw_concentration_g_per_l is not None:
        feed.imass["Yeast"] += dcw_concentration_g_per_l * seed_volume_l / 1e3

    return feed


def build_front_end_section(
    workbook_path: Optional[str] = None,
    *,
    batch_volume_l: Optional[float] = None,
    flowsheet: Optional[bst.Flowsheet] = None,
    mode: str = "excel",
    baseline_config: Optional[Path | str] = None,
) -> FrontEndSection:
    """Instantiate the seed train, fermentation, and harvest units for the baseline flow."""

    mode_normalized = (mode or "excel").lower()
    if mode_normalized not in {"excel", "baseline"}:
        raise ValueError(f"Unsupported mode {mode!r}; expected 'excel' or 'baseline'")

    module_defaults_path = Path(__file__).with_name("module_defaults.yaml")
    data_source: Path | str = module_defaults_path
    if workbook_path:
        candidate = Path(workbook_path)
        if candidate.suffix.lower() in {".yaml", ".yml"} and candidate.exists():
            data_source = candidate
    defaults = ExcelModuleDefaults(data_source)
    set_defaults_loader(defaults)
    set_migration_thermo()

    baseline_overrides: Dict[str, Any] = {}
    if mode_normalized == "baseline":
        config_path = (
            Path(baseline_config) if baseline_config is not None else DEFAULT_BASELINE_CONFIG
        )
        default_data = load_baseline_defaults(DEFAULT_BASELINE_CONFIG)
        if config_path != DEFAULT_BASELINE_CONFIG:
            merged = load_baseline_defaults(config_path, merge_with=default_data)
            baseline_overrides = dict(merged)
        else:
            baseline_overrides = dict(default_data)

    registry = ModuleRegistry()
    _register_front_end_builders(registry)

    key_to_unit = {}
    for key in FRONT_END_KEYS:
        config = defaults.get_module_config(key)
        if config is None:
            config = ModuleConfig(key=key)
        key_to_unit[key] = registry.build(config)

    seed_unit = key_to_unit[ModuleKey("USP01", "USP01a")]
    fermentation_unit = key_to_unit[ModuleKey("USP00", "USP00a")]
    microfiltration_unit = key_to_unit[ModuleKey("USP02", "USP02a")]
    ufdf_unit = key_to_unit[ModuleKey("DSP01", "DSP01a")]
    chromatography_unit = key_to_unit[ModuleKey("DSP02", "DSP02a")]
    predrying_unit = key_to_unit[ModuleKey("DSP03", "DSP03a")]
    spray_dryer_unit = key_to_unit[ModuleKey("DSP05", "DSP05a")]

    working_volume_l = batch_volume_l or _get_parameter(
        defaults, "GLOBAL00", "GLOBAL00b", "Working_Volume"
    ) or 1_000.0

    inoc_ratio = _get_parameter(
        defaults, "USP01", "USP01a", "Inoc_ratio_vv_USP02"
    ) or 0.05
    seed_volume_l = working_volume_l * inoc_ratio

    fermentation_derived = _section_values(baseline_overrides, "fermentation", "derived")
    fermentation_specs_override = _section_values(baseline_overrides, "fermentation", "specs")
    seed_derived = _section_values(baseline_overrides, "seed", "derived")
    seed_specs_override = _section_values(baseline_overrides, "seed", "specs")
    cell_feed = _section_values(baseline_overrides, "cell_removal", "feed")
    concentration_feed = _section_values(baseline_overrides, "concentration", "feed")

    od_to_dcw_default = _get_module_parameter(
        defaults, "GLOBAL00", "GLOBAL00a", "OD to Biomass Conversion"
    )
    fermentation_od_default = _get_module_parameter(
        defaults, "GLOBAL00", "GLOBAL00b", "Fermentation OD600"
    )

    working_volume_l = _coerce_float(fermentation_derived.get("working_volume_l"), 0.0)
    if working_volume_l <= 0.0:
        vessel_m3 = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00c", "Fermenter size")
        if vessel_m3 is not None and vessel_m3 > 0:
            working_volume_l = vessel_m3 * 1_000.0
        else:
            working_volume_l = 70_000.0

    working_titer = fermentation_derived.get("target_titer_g_per_l")
    if working_titer is None:
        working_titer = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00c", "Strain_Titer")

    fermentation_od_target = fermentation_derived.get("od600_target")
    if fermentation_od_target is None:
        fermentation_od_target = fermentation_od_default

    fermentation_od_to_dcw = fermentation_derived.get("od_to_dcw_g_per_l_per_od")
    if fermentation_od_to_dcw is None:
        dcw_from_override = fermentation_derived.get("dcw_concentration_g_per_l")
        if dcw_from_override and fermentation_od_target:
            fermentation_od_to_dcw = dcw_from_override / fermentation_od_target
        else:
            fermentation_od_to_dcw = od_to_dcw_default

    if fermentation_od_target and fermentation_od_to_dcw:
        dcw_concentration = fermentation_od_target * fermentation_od_to_dcw
    else:
        dcw_concentration = fermentation_derived.get("dcw_concentration_g_per_l")
        if dcw_concentration is None:
            dcw_concentration = seed_derived.get("dcw_concentration_g_per_l")

    total_glucose_feed_kg = fermentation_derived.get("total_glucose_feed_kg")
    total_glycerol_feed_kg = fermentation_derived.get("total_glycerol_feed_kg")
    total_molasses_feed_kg = fermentation_derived.get("total_molasses_feed_kg")

    initial_carbon_conc = fermentation_derived.get("initial_carbon_concentration_g_per_l")
    feed_carbon_conc = fermentation_derived.get("feed_carbon_concentration_g_per_l")
    if initial_carbon_conc is None:
        initial_carbon_conc = _get_module_parameter(
            defaults,
            "GLOBAL00",
            "GLOBAL00c",
            "Initial_Glucose_Concentration",
        )
    if feed_carbon_conc is None:
        feed_carbon_conc = _get_module_parameter(
            defaults,
            "GLOBAL00",
            "GLOBAL00c",
            "Feed_Glucose_Concentration",
        )

    yeast_extract_per_batch = seed_derived.get("yeast_extract_per_batch_kg")
    peptone_per_batch = seed_derived.get("peptone_per_batch_kg")
    antifoam_volume_l = fermentation_derived.get("antifoam_volume_l")

    product_preharvest = fermentation_derived.get("product_out_kg")
    harvested_product = product_preharvest

    harvest_volume_l = None
    feed_volume_m3 = cell_feed.get("volume_m3")
    if isinstance(feed_volume_m3, (int, float)) and feed_volume_m3 > 0:
        harvest_volume_l = feed_volume_m3 * 1_000.0
    if harvest_volume_l is None or harvest_volume_l <= 0.0:
        harvest_volume_l = working_volume_l

    product_after_mf = product_preharvest
    product_after_uf = product_preharvest
    product_after_chrom = product_preharvest
    product_after_predry = product_preharvest
    final_product_kg = None

    post_uf_volume_l = None
    conc_volume_m3 = concentration_feed.get("volume_m3")
    if isinstance(conc_volume_m3, (int, float)) and conc_volume_m3 > 0:
        post_uf_volume_l = conc_volume_m3 * 1_000.0

    post_elution_volume_l = None
    post_elution_conc_volume_l = None
    volume_to_spray_l = None

    fermentation_plan = fermentation_unit.plan
    fermentation_plan.derived.update(
        {
            "working_volume_l": working_volume_l,
            "target_titer_g_per_l": working_titer,
            "dcw_concentration_g_per_l": dcw_concentration,
            "od600_target": fermentation_od_target,
            "od_to_dcw_g_per_l_per_od": fermentation_od_to_dcw,
            "total_glucose_feed_kg": total_glucose_feed_kg,
            "initial_carbon_concentration_g_per_l": initial_carbon_conc,
            "feed_carbon_concentration_g_per_l": feed_carbon_conc,
        }
    )

    maintenance_coeff = fermentation_derived.get("maintenance_coefficient_g_glucose_per_gdcw_h")
    if maintenance_coeff is None:
        maintenance_coeff = 0.03
    fermentation_plan.derived.setdefault(
        "maintenance_coefficient_g_glucose_per_gdcw_h",
        maintenance_coeff,
    )

    loss_fraction = fermentation_derived.get("loss_fraction_glucose")
    if loss_fraction is None:
        loss_fraction = 0.0
    fermentation_plan.derived.setdefault("loss_fraction_glucose", loss_fraction)

    specific_productivity = fermentation_derived.get("specific_productivity_g_per_gdcw_h")
    if specific_productivity is None:
        specific_productivity = 0.0
    fermentation_plan.derived.setdefault(
        "specific_productivity_g_per_gdcw_h",
        specific_productivity,
    )

    product_model = fermentation_derived.get("product_model")
    if product_model is None:
        product_model = "specific_productivity" if specific_productivity else "growth_associated"
    fermentation_plan.derived.setdefault("product_model", product_model)

    nitrogen_requirement = fermentation_derived.get("nitrogen_requirement_g_per_gdcw")
    if nitrogen_requirement is None:
        nitrogen_requirement = 0.1
    fermentation_plan.derived.setdefault(
        "nitrogen_requirement_g_per_gdcw",
        nitrogen_requirement,
    )

    nh4oh_ratio = fermentation_derived.get("nh4oh_kg_per_kg_n")
    if nh4oh_ratio is None:
        nh4oh_ratio = 1.0
    fermentation_plan.derived.setdefault("nh4oh_kg_per_kg_n", nh4oh_ratio)

    if total_glycerol_feed_kg is not None:
        fermentation_plan.derived["total_glycerol_feed_kg"] = total_glycerol_feed_kg
    if total_molasses_feed_kg is not None:
        fermentation_plan.derived["total_molasses_feed_kg"] = total_molasses_feed_kg

    if product_preharvest is not None:
        fermentation_plan.derived["product_out_kg"] = product_preharvest
    elif working_titer is not None:
        fermentation_plan.derived["product_out_kg"] = (
            working_titer * working_volume_l / 1_000.0
        )

    seed_plan = seed_unit.plan
    seed_od_target = seed_derived.get("od600_target")
    if seed_od_target is None:
        seed_od_target = fermentation_od_target
    seed_od_to_dcw = seed_derived.get("od_to_dcw_g_per_l_per_od")
    if seed_od_to_dcw is None:
        seed_dcw = seed_derived.get("dcw_concentration_g_per_l")
        if seed_dcw and seed_od_target:
            seed_od_to_dcw = seed_dcw / seed_od_target
        else:
            seed_od_to_dcw = od_to_dcw_default
    seed_dcw_concentration = seed_od_target * seed_od_to_dcw if seed_od_target and seed_od_to_dcw else seed_derived.get("dcw_concentration_g_per_l")

    seed_plan.derived.update(
        {
            "working_volume_l": seed_volume_l,
            "dcw_concentration_g_per_l": seed_dcw_concentration,
            "od600_target": seed_od_target,
            "od_to_dcw_g_per_l_per_od": seed_od_to_dcw,
            "seed_glucose_conversion_fraction": 0.0,
        }
    )
    if yeast_extract_per_batch is not None:
        seed_plan.derived["yeast_extract_per_batch_kg"] = yeast_extract_per_batch
    if peptone_per_batch is not None:
        seed_plan.derived["peptone_per_batch_kg"] = peptone_per_batch

    seed_profile_name = None
    fermentation_profile_name = None
    seed_override_cfg = None
    fermentation_override_cfg = None
    if baseline_overrides:
        seed_override_cfg = baseline_overrides.get("seed")
        fermentation_override_cfg = baseline_overrides.get("fermentation")
        if isinstance(seed_override_cfg, Mapping):
            seed_profile_name = seed_override_cfg.get("profile")
        if isinstance(fermentation_override_cfg, Mapping):
            fermentation_profile_name = fermentation_override_cfg.get("profile")

    profile_name = fermentation_profile_name or seed_profile_name
    if profile_name:
        try:
            seed_profile_override, fermentation_profile_override = load_seed_fermentation_profile(profile_name)
        except Exception as exc:  # pragma: no cover - defensive path
            seed_plan.add_note(
                f"Failed to load seed/fermentation profile '{profile_name}': {exc}"
            )
        else:
            if seed_profile_override:
                _apply_plan_overrides(seed_plan, seed_profile_override)
                seed_plan.add_note(f"Seed profile '{profile_name}' applied")
            if fermentation_profile_override:
                profile_notes = _apply_fermentation_override(
                    fermentation_plan,
                    fermentation_profile_override,
                )
                if profile_notes:
                    for note in profile_notes:
                        fermentation_plan.add_note(note)
                else:
                    fermentation_plan.add_note(
                        f"Fermentation profile '{profile_name}' applied"
                    )
                profile_feed = fermentation_profile_override.get("feed", {})
                profile_derived = fermentation_profile_override.get("derived", {})
                carbon_totals = {}
                for key, carbon_key in (
                    ("total_glucose_feed_kg", "glucose"),
                    ("total_glycerol_feed_kg", "glycerol"),
                    ("total_molasses_feed_kg", "molasses"),
                    ("total_lactose_feed_kg", "lactose"),
                ):
                    value = profile_derived.get(key)
                    if value is not None:
                        carbon_totals[carbon_key] = value
                if carbon_totals:
                    fermentation_plan.derived["_profile_carbon_totals"] = carbon_totals
                if "product_out_kg" in profile_derived:
                    fermentation_plan.derived.setdefault(
                        "_profile_product_out_kg",
                        profile_derived.get("product_out_kg"),
                    )
                if isinstance(profile_feed, Mapping):
                    carbon_source_override = profile_feed.get("carbon_source")
                    if carbon_source_override:
                        fermentation_plan.derived["carbon_source"] = carbon_source_override
                    media_type_override = profile_feed.get("media_type")
                    if media_type_override:
                        fermentation_plan.derived["media_type"] = media_type_override
            if isinstance(seed_override_cfg, dict):
                updated_seed_override = dict(seed_override_cfg)
                updated_seed_override.pop("profile", None)
                baseline_overrides["seed"] = updated_seed_override
                seed_override_cfg = updated_seed_override
            if isinstance(fermentation_override_cfg, dict):
                updated_ferm_override = dict(fermentation_override_cfg)
                updated_ferm_override.pop("profile", None)
                baseline_overrides["fermentation"] = updated_ferm_override
                fermentation_override_cfg = updated_ferm_override

    if baseline_overrides:
        _apply_plan_overrides(seed_plan, baseline_overrides.get("seed"))

    seed_specs = seed_unit.plan.specs
    yeast_cost_per_kg = seed_specs_override.get("yeast_extract_cost_per_kg")
    if yeast_cost_per_kg is None:
        yeast_cost_per_kg = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Yeast_Extract_Cost")
    if yeast_cost_per_kg is not None and getattr(seed_specs, "yeast_extract_cost_per_kg", None) in (None, 0):
        seed_specs.yeast_extract_cost_per_kg = yeast_cost_per_kg

    peptone_cost_per_kg = seed_specs_override.get("peptone_cost_per_kg")
    if peptone_cost_per_kg is None:
        peptone_cost_per_kg = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Peptone_Cost")
    if peptone_cost_per_kg is not None and getattr(seed_specs, "peptone_cost_per_kg", None) in (None, 0):
        seed_specs.peptone_cost_per_kg = peptone_cost_per_kg

    seed_biomass_total = None
    if seed_dcw_concentration is not None and seed_volume_l:
        seed_biomass_total = seed_dcw_concentration * seed_volume_l / 1_000.0

    if seed_biomass_total is not None:
        initial_biomass_conc_g_per_l = (seed_biomass_total * 1_000.0 / working_volume_l) if working_volume_l else None
        initial_od = None
        if initial_biomass_conc_g_per_l is not None and fermentation_od_to_dcw:
            initial_od = initial_biomass_conc_g_per_l / fermentation_od_to_dcw
        fermentation_plan.derived.setdefault("initial_biomass_kg", seed_biomass_total)
        if initial_od is not None:
            fermentation_plan.derived.setdefault("initial_od600", initial_od)

    fermentation_product = fermentation_plan.derived.get("product_out_kg")

    fermentation_notes: list[str] = []
    if mode_normalized == "baseline":
        fermentation_override = (
            baseline_overrides.get("fermentation") if baseline_overrides else None
        )
        if fermentation_override:
            fermentation_notes = _apply_fermentation_override(
                fermentation_plan,
                fermentation_override,
            )
            for note in fermentation_notes:
                fermentation_plan.add_note(note)

    if antifoam_volume_l is not None:
        fermentation_plan.derived["antifoam_volume_l"] = antifoam_volume_l

    fermentation_specs = fermentation_unit.plan.specs
    glucose_cost = fermentation_specs_override.get("glucose_cost_per_kg")
    if glucose_cost is None:
        glucose_cost = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Glucose_Cost")
    glycerol_cost = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Glycerol_Cost")
    lactose_cost = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Lactose_Cost")
    molasses_cost = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Molasses_Cost")
    carbon_cost_lookup = {
        "glucose": glucose_cost,
        "glycerol": glycerol_cost,
        "lactose": lactose_cost,
        "molasses": molasses_cost,
    }
    carbon_source = fermentation_plan.derived.get("carbon_source")
    carbon_cost = carbon_cost_lookup.get(carbon_source)
    carbon_totals_override = fermentation_plan.derived.get("_profile_carbon_totals")
    if carbon_cost is not None and getattr(fermentation_specs, "glucose_cost_per_kg", None) in (None, 0):
        fermentation_specs.glucose_cost_per_kg = carbon_cost

    antifoam_cost = fermentation_derived.get("antifoam_cost_per_unit")
    if antifoam_cost is None:
        antifoam_cost = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Antifoam_Cost")
    if antifoam_cost is not None:
        fermentation_plan.derived.setdefault("antifoam_cost_per_unit", antifoam_cost)

    minor_nutrient_total = fermentation_plan.derived.get("minor_nutrients_cost_total")
    if minor_nutrient_total is None:
        value = _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00a", "Minor_Nutrients_Cost")
        if value is not None:
            fermentation_plan.derived["minor_nutrients_cost_total"] = value

    if baseline_overrides:
        _apply_plan_overrides(fermentation_plan, baseline_overrides.get("fermentation"))
        fermentation_product = fermentation_plan.derived.get("product_out_kg", fermentation_product)

    working_volume_override = fermentation_plan.derived.get("working_volume_l")
    if working_volume_override is not None:
        working_volume_l = working_volume_override
        seed_volume_l = working_volume_l * inoc_ratio

    micro_plan = microfiltration_unit.plan
    clarified_volume_l = harvest_volume_l
    micro_plan.derived.update(
        {
            "input_product_kg": fermentation_product,
            "input_volume_l": working_volume_l,
            "output_volume_l": clarified_volume_l,
            "product_out_kg": product_after_mf,
            "harvested_product_kg": harvested_product,
        }
    )

    if baseline_overrides:
        _apply_plan_overrides(micro_plan, baseline_overrides.get("microfiltration"))
        product_after_mf = micro_plan.derived.get("product_out_kg", product_after_mf)
        clarified_volume_l = micro_plan.derived.get("output_volume_l", clarified_volume_l)
        fermentation_product = micro_plan.derived.get("input_product_kg", fermentation_product)

    cell_removal_units: list[bst.Unit] = [microfiltration_unit]
    if mode_normalized == "baseline":
        cell_config = baseline_overrides.get("cell_removal") if baseline_overrides else None
        if cell_config:
            chain = build_cell_removal_chain(
                method=cell_config.get("method"),
                config=cell_config,
                fermentation_plan=fermentation_plan,
                micro_plan=micro_plan,
                harvested_volume_l=harvest_volume_l,
            )
            if chain.product_out_kg is not None:
                product_after_mf = chain.product_out_kg
                micro_plan.derived["product_out_kg"] = chain.product_out_kg
            if chain.output_volume_l is not None:
                clarified_volume_l = chain.output_volume_l
                micro_plan.derived["output_volume_l"] = chain.output_volume_l
            if chain.units:
                cell_removal_units = chain.units
            if chain.notes:
                for note in chain.notes:
                    micro_plan.add_note(note)
            micro_plan.derived.setdefault(
                "clarification_route",
                cell_config.get("method"),
            )

    cell_removal_units_tuple = tuple(cell_removal_units)
    microfiltration_unit = cell_removal_units_tuple[-1]

    concentration_units: list[bst.Unit] = [ufdf_unit]
    ufdf_in_system = True
    concentration_route: Optional[str] = None
    if mode_normalized == "baseline":
        conc_config = baseline_overrides.get("concentration") if baseline_overrides else None
        if conc_config:
            feed_cfg = conc_config.get("feed", {}) if isinstance(conc_config, Mapping) else {}
            density_m3 = feed_cfg.get("density_kg_per_m3")
            density_kg_per_l = (
                float(density_m3) / 1000.0
                if isinstance(density_m3, (int, float)) and density_m3 > 0
                else 1.0
            )
            chain = build_concentration_chain(
                method=conc_config.get("method"),
                config=conc_config,
                micro_plan=micro_plan,
                product_mass_kg=product_after_mf,
                volume_l=clarified_volume_l,
                density_kg_per_l=density_kg_per_l,
            )
            if chain.product_out_kg is not None:
                product_after_uf = chain.product_out_kg
            if chain.output_volume_l is not None:
                post_uf_volume_l = chain.output_volume_l
            if chain.units:
                concentration_units = chain.units
                ufdf_unit = chain.units[-1]
            if chain.notes:
                for note in chain.notes:
                    ufdf_unit.plan.add_note(note)
            concentration_route = chain.route.value

    concentration_units_tuple = tuple(concentration_units)
    if concentration_units_tuple:
        ufdf_unit = concentration_units_tuple[-1]

    ufdf_plan = ufdf_unit.plan
    if concentration_route:
        ufdf_plan.derived.setdefault("concentration_route", concentration_route)
    ufdf_plan.derived.update(
        {
            "input_product_kg": product_after_mf,
            "input_volume_l": clarified_volume_l,
            "output_volume_l": post_uf_volume_l,
            "product_out_kg": product_after_uf,
        }
    )

    if baseline_overrides:
        _apply_plan_overrides(ufdf_plan, baseline_overrides.get("ufdf"))
        product_after_uf = ufdf_plan.derived.get("product_out_kg", product_after_uf)
        post_uf_volume_l = ufdf_plan.derived.get("output_volume_l", post_uf_volume_l)

    capture_route = None
    capture_pool_cond = None
    capture_pool_ph = None
    capture_cdmo_cost = None
    capture_resin_cost = None
    capture_buffer_cost = None
    capture_handoff: Optional[CaptureHandoff] = None
    capture_units_tuple: tuple[bst.Unit, ...] = ()
    dsp03_units_tuple: tuple[bst.Unit, ...] = ()
    dsp04_units_tuple: tuple[bst.Unit, ...] = ()
    dsp03_handoff: Optional[CaptureHandoff] = None
    dsp03_route_value: Optional[str] = None
    dsp04_handoff: Optional[CaptureHandoff] = None
    dsp05_handoff = None
    if mode_normalized == "baseline":
        capture_config_raw = baseline_overrides.get("capture") if baseline_overrides else None
        capture_config = (
            capture_config_raw if isinstance(capture_config_raw, Mapping) else {}
        )
        chain = build_capture_chain(
            method=capture_config.get("method"),
            config=capture_config,
            concentration_plan=ufdf_plan,
        )
        if chain.product_out_kg is not None:
            product_after_chrom = chain.product_out_kg
        if chain.pool_volume_l is not None:
            post_elution_conc_volume_l = chain.pool_volume_l
            post_elution_volume_l = chain.pool_volume_l
        if chain.notes:
            for note in chain.notes:
                chromatography_unit.plan.add_note(note)
        capture_route_enum = chain.route or CaptureRoute.AEX
        capture_route = capture_route_enum.value
        capture_pool_cond = chain.pool_conductivity_mM
        capture_pool_ph = chain.pool_ph
        capture_cdmo_cost = chain.cdmo_cost_per_batch
        capture_resin_cost = chain.resin_cost_per_batch
        capture_buffer_cost = chain.buffer_cost_per_batch
        capture_handoff = chain.handoff

        if chain.units:
            chromatography_unit = chain.units[0]
            capture_units_tuple = tuple(chain.units[1:])
        else:
            capture_units_tuple = tuple()

        if capture_route_enum is CaptureRoute.CHITOSAN:
            concentration_units = []
            concentration_units_tuple = tuple()
            ufdf_in_system = False
            product_after_uf = product_after_mf
            post_uf_volume_l = clarified_volume_l

        dsp03_config_raw = baseline_overrides.get("dsp03") if baseline_overrides else None
        dsp03_chain = build_dsp03_chain(
            capture_handoff=capture_handoff,
            config_mapping=dsp03_config_raw if isinstance(dsp03_config_raw, Mapping) else {},
            upstream_plan=chromatography_unit.plan,
        )
        dsp03_units_tuple = tuple(dsp03_chain.units)
        dsp03_handoff = dsp03_chain.handoff
        dsp03_route_value = dsp03_chain.route.value
        if dsp03_handoff.pool_volume_l is not None:
            post_elution_conc_volume_l = dsp03_handoff.pool_volume_l
            post_elution_volume_l = dsp03_handoff.pool_volume_l
        if (
            dsp03_handoff.pool_volume_l is not None
            and dsp03_handoff.opn_concentration_g_per_l is not None
        ):
            product_after_chrom = (
                dsp03_handoff.pool_volume_l
                * dsp03_handoff.opn_concentration_g_per_l
                / 1_000.0
            )
    if dsp03_handoff is None:
        dsp03_handoff = capture_handoff

    chrom_plan = chromatography_unit.plan

    chrom_actual: Dict[str, float] = {}

    def _set_chrometric(key: str, value: Optional[float]) -> None:
        if value is not None:
            chrom_actual[key] = value

    _set_chrometric("input_product_kg", product_after_uf)
    _set_chrometric("product_out_kg", product_after_chrom)
    _set_chrometric("output_volume_l", post_elution_conc_volume_l)
    _set_chrometric("eluate_volume_l", post_elution_volume_l)
    _set_chrometric("pool_conductivity_mM", capture_pool_cond)
    _set_chrometric("pool_ph", capture_pool_ph)
    _set_chrometric("cdmo_cost_per_batch", capture_cdmo_cost)
    _set_chrometric("resin_cost_per_batch", capture_resin_cost)
    _set_chrometric("buffer_cost_per_batch", capture_buffer_cost)

    if capture_route is not None:
        chrom_actual["capture_route"] = capture_route

    for key, value in chrom_actual.items():
        chrom_plan.derived[key] = value
    if capture_handoff is not None:
        for key, value in capture_handoff.as_dict().items():
            chrom_plan.derived[f"handoff_{key}"] = value

    if baseline_overrides:
        _apply_plan_overrides(chrom_plan, baseline_overrides.get("chromatography"))
        for key, value in chrom_actual.items():
            chrom_plan.derived[key] = value

    product_after_chrom = chrom_actual.get("product_out_kg", product_after_chrom)
    post_elution_conc_volume_l = chrom_actual.get("output_volume_l", post_elution_conc_volume_l)
    post_elution_volume_l = chrom_actual.get("eluate_volume_l", post_elution_volume_l)

    dsp04_config_raw = baseline_overrides.get("dsp04") if baseline_overrides else None
    base_handoff_for_dsp04 = dsp03_handoff or capture_handoff
    if base_handoff_for_dsp04 is not None:
        dsp04_chain = build_dsp04_chain(
            capture_handoff=capture_handoff,
            dsp03_handoff=base_handoff_for_dsp04,
            config_mapping=dsp04_config_raw if isinstance(dsp04_config_raw, Mapping) else {},
        )
        dsp04_units_tuple = tuple(dsp04_chain.stages + [dsp04_chain.sterile_filter])
        dsp04_handoff = dsp04_chain.handoff
    else:
        dsp04_handoff = None

    predry_plan = predrying_unit.plan
    predry_specs = predrying_unit.plan.specs
    predry_input_volume_l = predry_plan.derived.get("input_volume_l", post_elution_conc_volume_l)
    predry_input_product_kg = product_after_chrom
    if dsp03_handoff is not None:
        if dsp03_handoff.pool_volume_l is not None:
            predry_input_volume_l = dsp03_handoff.pool_volume_l
        if (
            dsp03_handoff.pool_volume_l is not None
            and dsp03_handoff.opn_concentration_g_per_l is not None
        ):
            predry_input_product_kg = (
                dsp03_handoff.pool_volume_l
                * dsp03_handoff.opn_concentration_g_per_l
                / 1_000.0
            )
        if dsp03_route_value is not None:
            predry_plan.derived.setdefault("dsp03_route", dsp03_route_value)

    efficiency = getattr(predry_specs, "efficiency", None)
    if efficiency is None:
        efficiency = 1.0
    efficiency = max(min(efficiency, 1.0), 0.0)

    concentration_factor = getattr(predry_specs, "concentration_factor", None)
    if concentration_factor is None or concentration_factor <= 0.0:
        concentration_factor = 1.0

    predry_output_product_kg = None
    if predry_input_product_kg is not None:
        predry_output_product_kg = max(predry_input_product_kg * efficiency, 0.0)

    predry_output_volume_l = predry_input_volume_l
    if predry_input_volume_l is not None and concentration_factor:
        predry_output_volume_l = predry_input_volume_l / concentration_factor

    predry_recovery_fraction = None
    if predry_input_product_kg and predry_input_product_kg > 0:
        predry_recovery_fraction = (predry_output_product_kg or 0.0) / predry_input_product_kg

    predry_actual = {
        "input_product_kg": predry_input_product_kg,
        "input_volume_l": predry_input_volume_l,
        "output_volume_l": predry_output_volume_l,
        "product_out_kg": predry_output_product_kg,
        "product_recovery_fraction": predry_recovery_fraction,
    }
    if predry_plan.derived.get("broth_density_kg_per_l") is None and chrom_plan.derived.get("density_kg_per_l") is not None:
        predry_actual["broth_density_kg_per_l"] = chrom_plan.derived.get("density_kg_per_l")

    for key, value in predry_actual.items():
        if value is not None:
            predry_plan.derived[key] = value

    if baseline_overrides:
        _apply_plan_overrides(predry_plan, baseline_overrides.get("predrying"))
        for key, value in predry_actual.items():
            if value is not None:
                predry_plan.derived[key] = value

    product_after_predry = predry_actual.get("product_out_kg", product_after_predry)
    volume_to_spray_l = predry_actual.get("output_volume_l", volume_to_spray_l)

    dsp05_config_raw = baseline_overrides.get("dsp05") if baseline_overrides else None
    dsp05_config = DSP05Config.from_mapping(
        dsp05_config_raw if isinstance(dsp05_config_raw, Mapping) else None
    )

    spray_plan = spray_dryer_unit.plan
    spray_density = _coerce_float(spray_plan.derived.get("solution_density"), 1.0)
    if (
        dsp05_config.spraydry.precon_enable
        and product_after_predry is not None
    ):
        target_solids_frac = (
            _coerce_float(dsp05_config.spraydry.precon_target_solids_wt_pct, 0.0) / 100.0
        )
        if target_solids_frac > 0 and spray_density > 0:
            volume_to_spray_l = (
                product_after_predry / (target_solids_frac * spray_density)
            )
            predry_plan.derived["output_volume_l"] = volume_to_spray_l

    spray_input_product_kg = product_after_predry
    spray_input_volume_l = volume_to_spray_l
    final_handoff_for_spray = dsp04_handoff or dsp03_handoff or capture_handoff
    if final_handoff_for_spray is not None:
        if (
            spray_input_product_kg is None
            and final_handoff_for_spray.pool_volume_l is not None
            and final_handoff_for_spray.opn_concentration_g_per_l is not None
        ):
            spray_input_product_kg = (
                final_handoff_for_spray.pool_volume_l
                * final_handoff_for_spray.opn_concentration_g_per_l
                / 1_000.0
            )
        if spray_input_volume_l is None and final_handoff_for_spray.pool_volume_l is not None:
            spray_input_volume_l = final_handoff_for_spray.pool_volume_l
    if dsp04_units_tuple:
        spray_plan.derived.setdefault(
            "dsp04_stages",
            [unit.plan.derived.get("route") for unit in dsp04_units_tuple if unit.plan is not None],
        )

    spray_plan.derived.update(
        {
            "input_product_kg": spray_input_product_kg,
            "input_volume_l": spray_input_volume_l,
            "product_out_kg": final_product_kg,
        }
    )

    if baseline_overrides:
        _apply_plan_overrides(spray_plan, baseline_overrides.get("spray_dryer"))
        final_product_kg = spray_plan.derived.get("product_out_kg", final_product_kg)

    dsp05_handoff = build_dsp05_chain(
        config_mapping=dsp05_config_raw if isinstance(dsp05_config_raw, Mapping) else None,
        feed_volume_m3=final_handoff_for_spray.pool_volume_l if final_handoff_for_spray else None,
        feed_opn_conc_gL=final_handoff_for_spray.opn_concentration_g_per_l if final_handoff_for_spray else None,
        feed_moisture_wt_pct=None,
        feed_solids_wt_pct=None,
        plan_product_mass_kg=spray_plan.derived.get("product_out_kg"),
        plan_product_volume_m3=spray_plan.derived.get("output_volume_l"),
    )
    spray_plan.derived.setdefault("dsp05_method", dsp05_handoff.method.value)

    cost_per_kg_usd = None
    cmo_fees_usd = None
    total_cost_per_batch_usd = None
    materials_cost_per_batch = None

    breakdown: Dict[str, float] = {}

    def _add_breakdown(key: str, value: Optional[float]) -> float:
        nonlocal breakdown
        nonlocal computed_material_cost
        if value is None:
            return 0.0
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if math.isnan(numeric):
            return 0.0
        breakdown[key] = numeric
        computed_material_cost += numeric
        return numeric

    fermentation_specs = fermentation_unit.plan.specs
    carbon_source = fermentation_plan.derived.get("carbon_source")
    carbon_mass = 0.0
    profile_carbon_totals = fermentation_plan.derived.get("_profile_carbon_totals") or {}
    if carbon_source and carbon_source in profile_carbon_totals:
        carbon_mass = profile_carbon_totals[carbon_source]
    else:
        if carbon_source == "glucose":
            carbon_mass = fermentation_plan.derived.get("total_glucose_feed_kg") or 0.0
        elif carbon_source == "glycerol":
            carbon_mass = fermentation_plan.derived.get("total_glycerol_feed_kg") or 0.0
        elif carbon_source == "molasses":
            carbon_mass = fermentation_plan.derived.get("total_molasses_feed_kg") or 0.0
        elif carbon_source == "lactose":
            carbon_mass = fermentation_plan.derived.get("total_lactose_feed_kg") or 0.0
    carbon_cost_calc = None
    if carbon_mass and fermentation_specs.glucose_cost_per_kg:
        carbon_cost_calc = carbon_mass * fermentation_specs.glucose_cost_per_kg

    seed_specs = seed_unit.plan.specs
    yeast_mass = seed_plan.derived.get("yeast_extract_per_batch_kg")
    if yeast_mass is None:
        conc = getattr(seed_specs, "yeast_extract_concentration_g_per_l", None)
        working_vol = seed_plan.derived.get("working_volume_l") or seed_volume_l
        if conc and working_vol:
            yeast_mass = conc * working_vol / 1_000.0
    yeast_cost_calc = None
    if yeast_mass is not None and seed_specs.yeast_extract_cost_per_kg is not None:
        yeast_cost_calc = yeast_mass * seed_specs.yeast_extract_cost_per_kg

    peptone_mass = seed_plan.derived.get("peptone_per_batch_kg")
    if peptone_mass is None:
        conc = getattr(seed_specs, "peptone_concentration_g_per_l", None)
        working_vol = seed_plan.derived.get("working_volume_l") or seed_volume_l
        if conc and working_vol:
            peptone_mass = conc * working_vol / 1_000.0
    peptone_cost_calc = None
    if peptone_mass is not None and seed_specs.peptone_cost_per_kg is not None:
        peptone_cost_calc = peptone_mass * seed_specs.peptone_cost_per_kg

    antifoam_volume = fermentation_plan.derived.get("antifoam_volume_l")
    antifoam_cost_per_unit = fermentation_plan.derived.get("antifoam_cost_per_unit")
    antifoam_cost_calc = None
    if antifoam_volume is not None and antifoam_cost_per_unit is not None:
        antifoam_cost_calc = antifoam_volume * antifoam_cost_per_unit

    minor_nutrients_cost_calc = fermentation_plan.derived.get("minor_nutrients_cost_total")

    cip_cost_calc = None
    cip_fee_per_m3 = concentration_feed.get("cip_fee_per_m3")
    cip_bv = concentration_feed.get("cip_bv")
    if (
        isinstance(cip_fee_per_m3, (int, float))
        and isinstance(cip_bv, (int, float))
        and cip_fee_per_m3 > 0
        and cip_bv > 0
        and working_volume_l > 0
    ):
        cip_cost_calc = cip_fee_per_m3 * cip_bv * (working_volume_l / 1_000.0)

    computed_material_cost = 0.0

    def _set_cost(key: str, value: Optional[float]) -> None:
        _add_breakdown(key, value)

    _set_cost("carbon_source", carbon_cost_calc)
    _set_cost("yeast_extract", yeast_cost_calc)
    _set_cost("peptone", peptone_cost_calc)
    _set_cost("minor_nutrients", minor_nutrients_cost_calc)
    _set_cost("antifoam", antifoam_cost_calc)
    _set_cost("buffers", chrom_plan.derived.get("buffer_cost_per_batch"))
    _set_cost("resin", chrom_plan.derived.get("resin_cost_per_batch"))
    _set_cost(
        "mf_membranes",
        micro_plan.derived.get("membrane_cost_per_cycle"),
    )
    if ufdf_in_system:
        _set_cost(
            "uf_df_membranes",
            ufdf_plan.derived.get("membrane_cost_per_cycle"),
        )
    _set_cost(
        "predry_tff_membranes",
        predry_plan.derived.get("membrane_cost_per_cycle"),
    )
    capture_polymer = chrom_plan.derived.get("polymer_cost_per_batch")
    capture_reagents = chrom_plan.derived.get("reagent_cost_per_batch")
    capture_utilities = chrom_plan.derived.get("utilities_cost_per_batch")
    _set_cost("capture_polymer", capture_polymer)
    _set_cost("capture_reagents", capture_reagents)
    _set_cost("capture_utilities", capture_utilities)
    _set_cost("cip_chemicals", cip_cost_calc)
    _set_cost(
        "media",
        fermentation_plan.derived.get("media_cost_per_batch_usd"),
    )

    materials_cost_per_batch = computed_material_cost or None

    final_product_mass = spray_plan.derived.get("product_out_kg")
    if final_product_mass is None:
        final_product_mass = final_product_kg
    if final_product_mass in (None, 0):
        target_recovery = _coerce_float(spray_plan.derived.get("target_recovery_rate"), 1.0)
        final_product_mass = _coerce_float(product_after_predry, 0.0) * target_recovery

    cmo_config_raw = baseline_overrides.get("cmo") if isinstance(baseline_overrides, Mapping) else None

    fermentation_hours = _coerce_float(fermentation_plan.derived.get("batch_cycle_hours"), 0.0)
    turnaround_hours = _coerce_float(
        getattr(fermentation_unit.plan.specs, "turnaround_time_hours", None),
        0.0,
    )
    fermentation_hours += turnaround_hours

    micro_hours = _estimate_depth_filter_hours(micro_plan)
    ufdf_hours_total, uf_hours_auto, df_hours_auto = _ufdf_time_breakdown(ufdf_plan)
    ufdf_hours = ufdf_hours_total
    predry_hours = _estimate_tff_hours(predry_plan)
    dsp_hours = micro_hours + ufdf_hours + predry_hours

    spray_hours_est = _estimate_spray_hours(predry_plan, spray_plan)
    spray_hours = spray_hours_est

    if isinstance(cmo_config_raw, Mapping):
        dsp_hours_default = _coerce_float(cmo_config_raw.get("dsp_hours_per_batch"), 0.0)
        if dsp_hours <= 0.0 and dsp_hours_default > 0.0:
            dsp_hours = dsp_hours_default
        spray_hours_default = _coerce_float(
            cmo_config_raw.get("spray_dryer_hours_per_batch"),
            0.0,
        )
        if spray_hours <= 0.0 and spray_hours_default > 0.0:
            spray_hours = spray_hours_default

    if dsp_hours < 0.0:
        dsp_hours = 0.0
    if spray_hours < 0.0:
        spray_hours = 0.0

    batches_per_campaign = _coerce_float(
        _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00c", "Batches_Per_Campaign"),
        0.0,
    )
    if isinstance(cmo_config_raw, Mapping):
        override_batches = cmo_config_raw.get("batches_per_campaign")
        if override_batches is not None:
            batches_per_campaign = _coerce_float(override_batches, batches_per_campaign)
    if batches_per_campaign <= 0.0:
        batches_per_campaign = 1.0

    seed_hours = _coerce_float(seed_plan.derived.get("seed_train_duration_hours"), 0.0)

    fermentation_feed_m3 = _coerce_float(
        fermentation_plan.derived.get("working_volume_l"),
        working_volume_l,
    ) / 1_000.0
    dsp_feed_m3 = _coerce_float(
        micro_plan.derived.get("input_volume_l"),
        harvest_volume_l,
    ) / 1_000.0
    spray_feed_m3 = _coerce_float(
        spray_plan.derived.get("input_volume_l"),
        volume_to_spray_l,
    ) / 1_000.0

    chrom_hours_auto = _coerce_float(
        chrom_plan.derived.get("handoff_cycle_time_h"),
        _coerce_float(chrom_plan.derived.get("cycle_time_h"), 0.0),
    )

    timings_override = _section_mapping(cmo_config_raw, "timings") if isinstance(cmo_config_raw, Mapping) else {}

    def _timing_value(name: str, default: float) -> float:
        return _coerce_float(timings_override.get(name), default)

    fermentation_process_hours = max(fermentation_hours - turnaround_hours, 0.0)

    timings = CMOTimings(
        seed_hours=_timing_value("seed_train_hours", seed_hours or 16.0),
        fermentation_hours=_timing_value(
            "fermentation_hours",
            fermentation_process_hours or fermentation_hours,
        ),
        turnaround_hours=_timing_value("turnaround_hours", turnaround_hours),
        micro_hours=_timing_value("micro_hours", micro_hours),
        uf_hours=_timing_value("uf_hours", uf_hours_auto),
        df_hours=_timing_value("df_hours", df_hours_auto),
        chromatography_hours=_timing_value("chromatography_hours", chrom_hours_auto),
        predry_hours=_timing_value("predry_hours", predry_hours),
        spray_hours=_timing_value("spray_hours", spray_hours),
    )

    def _proj02_value(name: str, fallback: float = 0.0) -> float:
        return _coerce_float(_get_module_parameter(defaults, "PROJ02", "PROJ02a", name), fallback)

    def _global_value(option: str, name: str, fallback: float = 0.0) -> float:
        return _coerce_float(_get_module_parameter(defaults, option, option + "a", name), fallback)

    rates = CMORates(
        fermenter_daily_rate=_proj02_value("Fermenter_Daily_Rate"),
        dsp_daily_rate=_proj02_value("DSP_Daily_Rate"),
        spray_hourly_rate=_proj02_value("Spray_Dryer_Hourly_Rate"),
        labor_per_batch=_proj02_value("Labor_Cost_Per_Batch"),
        documentation_per_batch=_proj02_value("Documentation_Base_Fee"),
        qa_review_per_batch=_proj02_value("QA_Review_Base_Fee"),
        qc_testing_per_batch=_global_value("GLOBAL00", "QC_Testing_Cost_Per_Batch"),
        consumables_markup_fraction=_proj02_value("CMO_Overhead_Markup"),
    )

    discounts = CMODiscounts(
        fermenter_campaign=_proj02_value("Fermenter_Campaign_Discount"),
        dsp_campaign=_proj02_value("DSP_Campaign_Discount"),
        spray_campaign=_proj02_value("Spray_Dryer_Campaign_Discount"),
        labor_campaign=_proj02_value("Labor_Campaign_Discount"),
        qa_campaign=_proj02_value("QA_Campaign_Discount"),
        consumables_campaign=_proj02_value("CMO_Consumables_Campaign_Discount"),
        long_term_contract=_proj02_value("Long_Term_Contract_Discount"),
        contract_length_years=_proj02_value("Contract_Length", 3.0),
        annual_price_escalation=_proj02_value("Annual_Price_Escalation"),
    )

    structure = CMOStructure(
        batches_per_campaign=batches_per_campaign,
        annual_campaigns=_coerce_float(
            _get_module_parameter(defaults, "GLOBAL00", "GLOBAL00c", "Annual_Campaigns"),
            1.0,
        ),
        campaign_setup_fee=_proj02_value("Campaign_Setup_Fee"),
        facility_reservation_fee=_proj02_value("Facility_Reservation_Fee"),
        campaign_reservation_months=_proj02_value("Campaign_Reservation_Months"),
        validation_batches_required=_proj02_value("Validation_Batches_Required"),
        validation_batch_surcharge=_proj02_value("Validation_Batch_Surcharge"),
    )

    consumables_base_override = None
    if isinstance(cmo_config_raw, Mapping):
        raw_value = cmo_config_raw.get("consumables_base_markup_usd")
        if raw_value is not None:
            consumables_base_override = _coerce_float(raw_value, 0.0)

    cmo_stage_costs, standard_batch_cost, campaign_adders, cmo_total_fee = compute_contract_stage_costs(
        timings,
        rates,
        discounts,
        structure,
        materials_cost_usd=computed_material_cost,
        consumables_base_override=consumables_base_override,
    )
    materials_cost = computed_material_cost
    total_cost = materials_cost + cmo_total_fee

    cost_per_kg = None
    if final_product_mass:
        try:
            cost_per_kg = total_cost / float(final_product_mass)
        except ZeroDivisionError:
            cost_per_kg = None

    materials_cost_per_kg = None
    cmo_cost_per_kg = None
    cmo_standard_cost_per_kg = None
    cmo_campaign_cost_per_kg = None
    if final_product_mass:
        try:
            fm = float(final_product_mass)
            if fm > 0:
                materials_cost_per_kg = computed_material_cost / fm
                cmo_cost_per_kg = cmo_total_fee / fm
                if standard_batch_cost is not None:
                    cmo_standard_cost_per_kg = standard_batch_cost / fm
                if campaign_adders is not None:
                    cmo_campaign_cost_per_kg = campaign_adders / fm
        except (TypeError, ValueError):
            pass

    retainer_fee_per_year = 0.0
    allocation_result: Optional[CMOResinAllocation] = None
    try:
        chrom_plan = chromatography_unit.plan
        campaigns_planned = getattr(structure, "annual_campaigns", 0.0)
        batches_planned_per_campaign = getattr(structure, "batches_per_campaign", 0.0)
        batches_executed = getattr(structure, "batches_per_year", 0.0)
        good_batches_released = batches_executed
        final_product_mass_float = _coerce_float(final_product_mass, 0.0)
        total_kg_released = final_product_mass_float * good_batches_released
        process_hours_per_batch = sum(
            _coerce_float(value, 0.0)
            for value in (
                timings.seed_hours,
                timings.fermentation_hours,
                timings.turnaround_hours,
                timings.micro_hours,
                timings.uf_hours,
                timings.df_hours,
                timings.chromatography_hours,
                timings.predry_hours,
                timings.spray_hours,
            )
        )
        resin_cost_per_batch = _coerce_float(chrom_plan.derived.get("resin_cost_per_batch"), 0.0)
        resin_cip_cost_per_batch = _capture_cip_cost_per_batch(chrom_plan)
        resin_lifetimes_consumed = chrom_plan.derived.get("resin_lifetimes_consumed")
        resin_cost_per_l = getattr(chrom_plan.specs, "resin_cost_per_l", None)
        resin_volume_l = chrom_plan.derived.get("resin_volume_l")
        cycles_per_batch = chrom_plan.derived.get("cycles_per_batch")
        resin_salvage_fraction = chrom_plan.derived.get("resin_salvage_fraction")
        if resin_salvage_fraction is None:
            salvage_spec = getattr(chrom_plan.specs, "resin_salvage_fraction", None)
            if salvage_spec is not None:
                try:
                    resin_salvage_fraction = float(salvage_spec)
                except (TypeError, ValueError):
                    resin_salvage_fraction = None

        retainer_fee_per_year = _coerce_float(
            _get_module_parameter(defaults, "PROJ02", "PROJ02a", "Retainer_Fee_per_Year"),
            0.0,
        )
        if isinstance(cmo_config_raw, Mapping):
            override_retainer = cmo_config_raw.get("retainer_fee_per_year")
            if override_retainer is not None:
                retainer_fee_per_year = _coerce_float(override_retainer, retainer_fee_per_year)

        allocation_result = compute_allocation(
            allocation_basis="KG_RELEASED",
            campaigns_planned=campaigns_planned,
            batches_planned_per_campaign=batches_planned_per_campaign,
            batches_executed=batches_executed,
            good_batches_released=good_batches_released,
            total_kg_released=total_kg_released,
            process_hours_per_batch=process_hours_per_batch,
            cmo_standard_per_batch_usd=standard_batch_cost or 0.0,
            cmo_campaign_per_batch_usd=campaign_adders or 0.0,
            cmo_retainer_annual_usd=retainer_fee_per_year,
            resin_cost_per_batch_usd=resin_cost_per_batch,
            resin_cip_cost_per_batch_usd=resin_cip_cost_per_batch,
            resin_lifetimes_consumed_per_batch=resin_lifetimes_consumed,
            resin_cost_per_l=resin_cost_per_l,
            resin_volume_l=resin_volume_l,
            cycles_per_batch=cycles_per_batch,
            resin_salvage_fraction=resin_salvage_fraction,
        )
    except Exception:
        allocation_result = None

    feed = _build_seed_media_stream(
        fermentation_unit=fermentation_unit,
        seed_unit=seed_unit,
        seed_volume_l=seed_volume_l,
        dcw_concentration_g_per_l=dcw_concentration,
    )

    seed_unit.ins[0] = feed
    seed_vent, seed_broth = seed_unit.outs
    fermentation_unit.ins[0] = seed_broth
    fermentation_vent, fermentation_broth = fermentation_unit.outs


    handoff_streams: Dict[str, bst.Stream] = {}

    def _wire_unit_with_handoff(unit: bst.Unit, incoming: bst.Stream) -> bst.Stream:
        unit.ins[0] = incoming
        product_stream = unit.outs[0]
        handoff = product_stream.copy(f"{product_stream.ID}_handoff")
        handoff.empty()
        report_clone = product_stream.copy(f"{product_stream.ID}_report")
        report_clone.empty()
        setattr(unit, "_handoff_stream", handoff)
        setattr(unit, "_handoff_report_stream", report_clone)
        handoff_streams[unit.ID] = report_clone
        return handoff

    fermentation_handoff = fermentation_broth.copy(
        f"{fermentation_broth.ID}_to_cell_removal"
    )
    fermentation_handoff.copy_like(fermentation_broth)
    setattr(fermentation_unit, "_handoff_stream", fermentation_handoff)
    fermentation_report = fermentation_handoff.copy(f"{fermentation_handoff.ID}_report")
    setattr(fermentation_unit, "_handoff_report_stream", fermentation_report)
    handoff_streams[fermentation_unit.ID] = fermentation_report

    previous = fermentation_handoff
    for unit in cell_removal_units_tuple:
        previous = _wire_unit_with_handoff(unit, previous)

    for unit in concentration_units_tuple:
        previous = _wire_unit_with_handoff(unit, previous)

    previous = _wire_unit_with_handoff(chromatography_unit, previous)

    for unit in capture_units_tuple:
        previous = _wire_unit_with_handoff(unit, previous)

    for unit in dsp03_units_tuple:
        previous = _wire_unit_with_handoff(unit, previous)

    previous = _wire_unit_with_handoff(predrying_unit, previous)

    for unit in dsp04_units_tuple:
        previous = _wire_unit_with_handoff(unit, previous)

    spray_dryer_unit.ins[0] = previous

    active_flowsheet = flowsheet or bst.Flowsheet("bd_front_end")
    bst.main_flowsheet.set_flowsheet(active_flowsheet)

    system_path_units = [
        seed_unit,
        fermentation_unit,
        *cell_removal_units_tuple,
        *concentration_units_tuple,
    ]
    if ufdf_in_system:
        system_path_units.append(ufdf_unit)
    system_path_units.append(chromatography_unit)
    system_path_units.extend(capture_units_tuple)
    system_path_units.extend(dsp03_units_tuple)
    system_path_units.append(predrying_unit)
    system_path_units.extend(dsp04_units_tuple)
    system_path_units.append(spray_dryer_unit)

    system = bst.System(
        "front_end",
        path=tuple(system_path_units),
    )

    allocation_inputs = {
        "allocation_basis": "KG_RELEASED",
        "campaigns_planned": campaigns_planned,
        "batches_planned_per_campaign": batches_planned_per_campaign,
        "batches_executed": batches_executed,
        "good_batches_released": good_batches_released,
        "total_kg_released": total_kg_released,
        "process_hours_per_batch": process_hours_per_batch,
        "cmo_standard_per_batch_usd": standard_batch_cost or 0.0,
        "cmo_campaign_per_batch_usd": campaign_adders or 0.0,
        "cmo_retainer_annual_usd": retainer_fee_per_year,
        "resin_cost_per_batch_usd": resin_cost_per_batch,
        "resin_cip_cost_per_batch_usd": resin_cip_cost_per_batch,
        "resin_lifetimes_consumed_per_batch": resin_lifetimes_consumed,
        "resin_cost_per_l": resin_cost_per_l,
        "resin_volume_l": resin_volume_l,
        "resin_salvage_fraction": resin_salvage_fraction,
        "cycles_per_batch": cycles_per_batch,
    }

    section = FrontEndSection(
        feed=feed,
        seed_unit=seed_unit,
        fermentation_unit=fermentation_unit,
        microfiltration_unit=microfiltration_unit,
        cell_removal_units=cell_removal_units_tuple,
        concentration_units=concentration_units_tuple,
        ufdf_unit=ufdf_unit,
        ufdf_in_system=ufdf_in_system,
        chromatography_unit=chromatography_unit,
        predrying_unit=predrying_unit,
        spray_dryer_unit=spray_dryer_unit,
        fermentation_handoff_stream=fermentation_handoff,
        handoff_streams=handoff_streams,
        system=system,
        defaults=defaults,
        total_cost_per_batch_usd=total_cost,
        cmo_fees_usd=cmo_total_fee,
        cost_per_kg_usd=cost_per_kg,
        materials_cost_per_batch_usd=materials_cost,
        computed_material_cost_per_batch_usd=materials_cost,
        capture_handoff=capture_handoff,
        capture_units=capture_units_tuple,
        dsp03_units=dsp03_units_tuple,
        dsp04_units=dsp04_units_tuple,
        dsp04_handoff=dsp04_handoff,
        dsp05_handoff=dsp05_handoff,
        material_cost_breakdown=breakdown,
        cmo_profile_name=(
            str(cmo_config_raw.get("profile", "contract_default"))
            if isinstance(cmo_config_raw, Mapping)
            else "contract_default"
        ),
        cmo_stage_costs=cmo_stage_costs,
        cmo_total_fee_usd=cmo_total_fee,
        batches_per_campaign=batches_per_campaign,
        cmo_standard_batch_usd=standard_batch_cost,
        cmo_campaign_adders_usd=campaign_adders,
        materials_cost_per_kg_usd=materials_cost_per_kg,
        cmo_cost_per_kg_usd=cmo_cost_per_kg,
        cmo_standard_cost_per_kg_usd=cmo_standard_cost_per_kg,
        cmo_campaign_cost_per_kg_usd=cmo_campaign_cost_per_kg,
        cmo_retainer_annual_usd=retainer_fee_per_year,
        _allocation_result=allocation_result,
        allocation_inputs=allocation_inputs,
    )

    section._refresh_post_simulation_metrics()

    return section


__all__ = [
    "FrontEndSection",
    "build_front_end_section",
]
