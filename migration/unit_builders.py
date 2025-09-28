"""Builders that translate Excel module defaults into baseline unit plans.

For now these builders return lightweight planning objects that capture the
normalized parameter set together with helpful derived metrics. They establish
the bridge between the Excel defaults and future BioSTEAM unit factories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .excel_defaults import ExcelModuleDefaults, ModuleConfig, ModuleKey
from .default_overrides import get_overrides_for
from .module_builders import ModuleData, build_module_data
from .module_registry import ModuleRegistry
from .unit_specs import (
    FermentationSpecs,
    MicrofiltrationSpecs,
    SeedTrainSpecs,
    UltrafiltrationSpecs,
    ChromatographySpecs,
    PreDryingSpecs,
    DryerSpecs,
)


@dataclass
class UnitPlan:
    """Container describing how to instantiate a module in BioSTEAM later on."""

    key: ModuleKey
    data: ModuleData
    specs: Any
    derived: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def add_note(self, message: str) -> None:
        self.notes.append(message)


_DEFAULTS_LOADER: Optional[ExcelModuleDefaults] = None


def set_defaults_loader(loader: ExcelModuleDefaults) -> None:
    """Store the defaults loader for cross-module lookups."""

    global _DEFAULTS_LOADER
    _DEFAULTS_LOADER = loader

def _apply_overrides(data: ModuleData, config: ModuleConfig) -> List[str]:
    overrides = get_overrides_for(config.key)
    applied_fields: List[str] = []
    for field, value in overrides.items():
        if data.apply_override(field, value, note="default override", force=False):
            applied_fields.append(field)
    return applied_fields


def _get_config(module: str, option: Optional[str]) -> Optional[ModuleConfig]:
    if _DEFAULTS_LOADER is None:
        return None
    return _DEFAULTS_LOADER.get_module_config(ModuleKey(module, option))


def _get_active_config(module: str, fallback_option: Optional[str] = None) -> Optional[ModuleConfig]:
    if _DEFAULTS_LOADER is None:
        return None
    defaults = _DEFAULTS_LOADER.load_defaults()
    for key, cfg in defaults.items():
        if key.module == module and cfg.active:
            return cfg
    if fallback_option is not None:
        return defaults.get(ModuleKey(module, fallback_option))
    return None


def _get_parameter(config: Optional[ModuleConfig], name: str) -> Optional[float]:
    if config is None:
        return None
    record = config.parameters.get(name)
    if record is None:
        return None
    return record.value


DEFAULT_PRODUCT_YIELD_BIOMASS = 0.2
CALCULATIONS_SHEET = "Calculations"
CALCULATIONS_PRODUCT_YIELD_CELL = (31, 1)  # zero-based indices (row 32, col B)


CARBON_OPTION_MAP = {
    "USP00a": {
        "label": "Glucose",
        "cost_field": "Glucose_Cost",
        "initial_field": "Initial_Glucose_Concentration",
        "feed_field": "Feed_Glucose_Concentration",
    },
    "USP00b": {
        "label": "Glycerol",
        "cost_field": "Glycerol_Cost",
        "initial_field": "Initial_Glycerol_Concentration",
        "feed_field": "Feed_Glycerol_Concentration",
    },
    "USP00c": {
        "label": "Lactose",
        "cost_field": "Lactose_Cost",
        "initial_field": "Initial_Lactose_Concentration",
        "feed_field": "Feed_Lactose_Concentration",
    },
    "USP00d": {
        "label": "Molasses",
        "cost_field": "Molasses_Cost",
        "initial_field": "Initial_Molasses_Concentration",
        "feed_field": "Feed_Molasses_Concentration",
    },
}


def _compose_fermentation_specs(
    carbon_config: ModuleConfig,
    global_config: Optional[ModuleConfig],
) -> Tuple[FermentationSpecs, Dict[str, Any]]:
    option = carbon_config.key.option or "USP00a"
    mapping = CARBON_OPTION_MAP.get(option, CARBON_OPTION_MAP["USP00a"])

    biomass_yield = None
    name = f"Biomass_Yield_on_{mapping['label']}"
    record = carbon_config.parameters.get(name)
    if record and record.value is not None:
        biomass_yield = record.value

    product_yield = _get_parameter(global_config, "Product_Yield_on_Biomass")
    yield_source = None
    if product_yield is None:
        product_yield = _load_product_yield_from_calculations()
        if product_yield is not None:
            yield_source = "calculations"
        else:
            product_yield = DEFAULT_PRODUCT_YIELD_BIOMASS
            yield_source = "fallback"
    turnaround = _get_parameter(global_config, "Turnaround_Time")
    if turnaround is None:
        turnaround = _get_parameter(carbon_config, "Turnaround_Time")

    antifoam = _get_parameter(global_config, "Antifoam_Dosage")
    if antifoam is None:
        antifoam = _get_parameter(carbon_config, "Antifoam_Dosage")

    antifoam_cost = _get_parameter(global_config, "Antifoam_Cost")
    if antifoam_cost is None:
        antifoam_cost = _get_parameter(carbon_config, "Antifoam_Cost")

    minor_nutrient_cost = _get_parameter(global_config, "Minor_Nutrients_Cost")
    if minor_nutrient_cost is None:
        minor_nutrient_cost = _get_parameter(carbon_config, "Minor_Nutrients_Cost")

    costs = (
        _get_parameter(global_config, mapping["cost_field"])
        or _get_parameter(carbon_config, mapping["cost_field"])
        or 0.0
    )

    specs = FermentationSpecs(
        key=carbon_config.key.module,
        turnaround_time_hours=turnaround,
        biomass_yield_glucose=biomass_yield,
        product_yield_biomass=product_yield,
        glucose_cost_per_kg=costs,
        antifoam_dosage=antifoam,
    )

    derived: Dict[str, Any] = {
        "carbon_source": mapping["label"].lower(),
    }

    initial = _get_parameter(global_config, mapping["initial_field"])
    feed = _get_parameter(global_config, mapping["feed_field"])
    if initial is not None:
        derived["initial_carbon_concentration_g_per_l"] = initial
    if feed is not None:
        derived["feed_carbon_concentration_g_per_l"] = feed

    seed_duration = _get_parameter(global_config, "Seed_Train_Duration")
    if seed_duration is not None:
        derived["seed_train_duration_hours"] = seed_duration
    if yield_source:
        derived["product_yield_source"] = yield_source
    if antifoam_cost is not None:
        derived["antifoam_cost_per_unit"] = antifoam_cost
    if minor_nutrient_cost is not None:
        derived["minor_nutrients_cost_total"] = minor_nutrient_cost

    return specs, derived


def _build_usp00_plan(config: ModuleConfig) -> UnitPlan:
    global_config = _get_active_config("GLOBAL00", "GLOBAL00c")
    specs, derived = _compose_fermentation_specs(config, global_config)

    cycle_hours = specs.estimated_batch_cycle_hours()
    if cycle_hours is not None:
        derived["batch_cycle_hours"] = cycle_hours
    if (
        specs.biomass_yield_glucose is not None
        and specs.product_yield_biomass is not None
    ):
        derived["product_yield_glucose"] = (
            specs.biomass_yield_glucose * specs.product_yield_biomass
        )

    data = ModuleData(key=config.key, records=config.parameters, values={})
    applied_fields = _apply_overrides(data, config)

    if specs.turnaround_time_hours is None:
        plan_note = (
            "Turnaround time missing; fermentation cycle defaults may need update."
        )
    else:
        plan_note = None

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    source = plan.derived.get("product_yield_source")
    if specs.product_yield_biomass is None:
        plan.add_note("Product yield on biomass missing; verify GLOBAL00 defaults.")
    elif source == "fallback":
        plan.add_note(
            "Product yield on biomass not provided; using assumed value 0.20 g/g."
        )
    elif source == "calculations":
        plan.add_note("Product yield pulled from Calculations!B32.")
    if plan_note:
        plan.add_note(plan_note)
    if applied_fields:
        plan.add_note(
            "Applied default overrides for: " + ", ".join(sorted(applied_fields))
        )

    return plan


def _build_usp01_plan(config: ModuleConfig) -> UnitPlan:
    carbon_config = _get_active_config("USP00", "USP00a")
    global_config = _get_active_config("GLOBAL00", "GLOBAL00c")
    fermentation_config = _get_active_config("USP02", "USP02a")

    if carbon_config is None:
        carbon_config = config  # fall back to current config if available

    carb_specs, base_derived = _compose_fermentation_specs(carbon_config, global_config)

    yeast_conc = _get_parameter(fermentation_config, "Yeast_Extract_Concentration")
    peptone_conc = _get_parameter(fermentation_config, "Peptone_Concentration")
    yeast_cost = _get_parameter(global_config, "Yeast_Extract_Cost")
    if yeast_cost is None:
        yeast_cost = _get_parameter(config, "Yeast_Extract_Cost")

    peptone_cost = _get_parameter(global_config, "Peptone_Cost")
    if peptone_cost is None:
        peptone_cost = _get_parameter(config, "Peptone_Cost")

    specs = SeedTrainSpecs(
        key=config.key.module,
        yeast_extract_concentration_g_per_l=yeast_conc,
        peptone_concentration_g_per_l=peptone_conc,
        yeast_extract_cost_per_kg=yeast_cost,
        peptone_cost_per_kg=peptone_cost,
    )

    derived: Dict[str, Any] = dict(base_derived)
    if carb_specs.biomass_yield_glucose is not None:
        derived["biomass_yield_glucose"] = carb_specs.biomass_yield_glucose
    total_nutrient = 0.0
    missing = False
    for value in (yeast_conc, peptone_conc):
        if value is None:
            missing = True
        else:
            total_nutrient += value
    if not missing:
        derived["total_nutrient_concentration_g_per_l"] = total_nutrient

    derived.setdefault("seed_glucose_conversion_fraction", 0.15)

    data = ModuleData(key=config.key, records=config.parameters, values={})
    applied_fields = _apply_overrides(data, config)

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if missing:
        plan.add_note(
            "Seed train nutrient concentrations incomplete; verify GLOBAL00/USP02 defaults."
        )
    if applied_fields:
        plan.add_note(
            "Applied default overrides for: " + ", ".join(sorted(applied_fields))
        )

    return plan


def _build_usp02_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    applied_fields = _apply_overrides(data, config)
    specs = data.to_spec()
    assert isinstance(specs, MicrofiltrationSpecs)

    derived: Dict[str, Any] = {}
    if specs.flux_l_m2_h is not None and specs.membrane_area_m2 is not None:
        derived["throughput_l_per_hr"] = specs.flux_l_m2_h * specs.membrane_area_m2
    if specs.membrane_cost is not None and specs.membrane_lifetime is not None and specs.membrane_lifetime > 0:
        derived["membrane_cost_per_cycle"] = specs.membrane_cost / specs.membrane_lifetime
    if specs.dilution_volume_l is not None:
        derived["dilution_volume_m3"] = specs.dilution_volume_l / 1000.0

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if specs.efficiency is None:
        plan.add_note("Microfiltration efficiency missing; verify USP02 defaults.")
    if applied_fields:
        plan.add_note("Applied default overrides for: " + ", ".join(sorted(applied_fields)))
    return plan


def _build_dsp01_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    applied_fields = _apply_overrides(data, config)
    specs = data.to_spec()
    assert isinstance(specs, UltrafiltrationSpecs)

    derived: Dict[str, Any] = {}
    if specs.flux_l_m2_h is not None and specs.membrane_area_m2 is not None:
        derived["throughput_l_per_hr"] = specs.flux_l_m2_h * specs.membrane_area_m2
    if specs.diafiltration_volumes is not None:
        derived["diafiltration_volumes"] = specs.diafiltration_volumes
    if specs.membrane_cost is not None and specs.membrane_lifetime is not None and specs.membrane_lifetime > 0:
        derived["membrane_cost_per_cycle"] = specs.membrane_cost / specs.membrane_lifetime

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if specs.efficiency is None:
        plan.add_note("UF/DF efficiency missing; verify DSP01 defaults.")
    if applied_fields:
        plan.add_note("Applied default overrides for: " + ", ".join(sorted(applied_fields)))
    return plan


def _build_dsp02_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    applied_fields = _apply_overrides(data, config)
    specs = data.to_spec()
    assert isinstance(specs, ChromatographySpecs)

    derived: Dict[str, Any] = {}
    resin_cost = specs.resin_cost_per_batch()
    if resin_cost is not None:
        derived["resin_cost_per_batch"] = resin_cost
    buffer_volumes = [
        specs.wash1_bv,
        specs.wash2_bv,
        specs.elution_bv,
        specs.strip_bv,
    ]
    if all(v is not None for v in buffer_volumes):
        derived["total_buffer_bv"] = sum(buffer_volumes)  # type: ignore[arg-type]

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if specs.dynamic_binding_capacity_g_per_l is None:
        plan.add_note("DBC missing; chromatography sizing requires update.")
    if applied_fields:
        plan.add_note("Applied default overrides for: " + ", ".join(sorted(applied_fields)))
    return plan


def _build_dsp03_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    applied_fields = _apply_overrides(data, config)
    specs = data.to_spec()
    assert isinstance(specs, PreDryingSpecs)

    derived: Dict[str, Any] = {}
    if specs.flux_l_m2_h is not None and specs.membrane_area_m2 is not None:
        derived["throughput_l_per_hr"] = specs.flux_l_m2_h * specs.membrane_area_m2

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if specs.efficiency is None:
        plan.add_note("Pre-drying efficiency missing; verify DSP03 defaults.")
    if applied_fields:
        plan.add_note("Applied default overrides for: " + ", ".join(sorted(applied_fields)))
    return plan


def _build_dsp05_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    applied_fields = _apply_overrides(data, config)
    specs = data.to_spec()
    assert isinstance(specs, DryerSpecs)

    derived: Dict[str, Any] = {}
    if specs.spray_dryer_capacity_kg_per_hr is not None:
        derived["capacity_kg_per_hr"] = specs.spray_dryer_capacity_kg_per_hr
    if specs.final_solids_content is not None:
        derived["final_solids_percent"] = specs.final_solids_content * 100.0

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if specs.spray_dryer_efficiency is None:
        plan.add_note("Spray dryer efficiency missing; verify DSP05 defaults.")
    if applied_fields:
        plan.add_note("Applied default overrides for: " + ", ".join(sorted(applied_fields)))
    return plan


PLAN_BUILDERS: Dict[str, Tuple[Any, Tuple[str, ...]]] = {
    "USP00": (_build_usp00_plan, ("USP00a", "USP00b", "USP00c")),
    "USP01": (_build_usp01_plan, ("USP01a", "USP00c")),
    "USP02": (_build_usp02_plan, ("USP02a", "USP02c")),
    "DSP01": (_build_dsp01_plan, ("DSP01a", "DSP01b")),
    "DSP02": (_build_dsp02_plan, ("DSP02a",)),
    "DSP03": (_build_dsp03_plan, ("DSP03a", "DSP03b")),
    "DSP05": (_build_dsp05_plan, ("DSP05a",)),
}


def register_baseline_unit_builders(
    registry: ModuleRegistry,
    *,
    module_options: Dict[str, Iterable[str]] | None = None,
) -> None:
    """Register builders that map Excel modules into :class:`UnitPlan` objects."""

    module_options = module_options or {}

    for module, (builder, default_options) in PLAN_BUILDERS.items():
        options = tuple(module_options.get(module, default_options))
        for option in options:
            registry.register(
                ModuleKey(module, option),
                lambda cfg, _builder=builder: _builder(cfg),
                description=f"{module} unit plan from Excel defaults",
                overwrite=True,
            )


__all__ = [
    "UnitPlan",
    "register_baseline_unit_builders",
    "PLAN_BUILDERS",
]
def _load_product_yield_from_calculations() -> Optional[float]:
    if _DEFAULTS_LOADER is None:
        return None
    try:
        import pandas as pd
    except ImportError:  # pragma: no cover - pandas should always be present
        return None

    path = _DEFAULTS_LOADER.workbook_path
    try:
        row, col = CALCULATIONS_PRODUCT_YIELD_CELL
        series = pd.read_excel(
            path,
            sheet_name=CALCULATIONS_SHEET,
            header=None,
            skiprows=row,
            nrows=1,
            usecols=[col],
        ).iloc[0]
        value = series.iloc[0]
    except Exception:
        return None
    return float(value) if isinstance(value, (int, float)) else None
