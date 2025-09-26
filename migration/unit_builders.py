"""Builders that translate Excel module defaults into baseline unit plans.

For now these builders return lightweight planning objects that capture the
normalized parameter set together with helpful derived metrics. They establish
the bridge between the Excel defaults and future BioSTEAM unit factories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Tuple

from .excel_defaults import ModuleConfig, ModuleKey
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


def _apply_overrides(data: ModuleData, config: ModuleConfig) -> List[str]:
    overrides = get_overrides_for(config.key)
    applied_fields: List[str] = []
    for field, value in overrides.items():
        if data.apply_override(field, value, note="default override", force=False):
            applied_fields.append(field)
    return applied_fields


def _build_usp00_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    applied_fields = _apply_overrides(data, config)
    specs = data.to_spec()
    assert isinstance(specs, FermentationSpecs)

    derived: Dict[str, Any] = {}
    cycle_hours = specs.estimated_batch_cycle_hours()
    derived["batch_cycle_hours"] = cycle_hours

    product_yield_glucose = None
    if (
        specs.biomass_yield_glucose is not None
        and specs.product_yield_biomass is not None
    ):
        product_yield_glucose = (
            specs.biomass_yield_glucose * specs.product_yield_biomass
        )
        derived["product_yield_glucose"] = product_yield_glucose

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if cycle_hours is None:
        plan.add_note(
            "Turnaround time missing; fermentation cycle defaults to 48 h without adjustment."
        )
    if product_yield_glucose is None:
        plan.add_note(
            "Unable to compute product yield on glucose from Excel defaults."
        )
    if applied_fields:
        plan.add_note(
            "Applied default overrides for: " + ", ".join(sorted(applied_fields))
        )

    return plan


def _build_usp01_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    applied_fields = _apply_overrides(data, config)
    specs = data.to_spec()
    assert isinstance(specs, SeedTrainSpecs)

    derived: Dict[str, Any] = {}
    total_nutrient_conc = 0.0
    missing = False
    for field_name in (
        "yeast_extract_concentration_g_per_l",
        "peptone_concentration_g_per_l",
    ):
        value = getattr(specs, field_name)
        if value is None:
            missing = True
            continue
        total_nutrient_conc += value
    if not missing:
        derived["total_nutrient_concentration_g_per_l"] = total_nutrient_conc
    else:
        derived["total_nutrient_concentration_g_per_l"] = None

    plan = UnitPlan(key=config.key, data=data, specs=specs, derived=derived)

    if missing:
        plan.add_note(
            "Seed train nutrient concentrations incomplete; verify Excel defaults."
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
