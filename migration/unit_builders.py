"""Builders that translate Excel module defaults into baseline unit plans.

For now these builders return lightweight planning objects that capture the
normalized parameter set together with helpful derived metrics. They establish
the bridge between the Excel defaults and future BioSTEAM unit factories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .excel_defaults import ModuleConfig, ModuleKey
from .default_overrides import get_overrides_for
from .module_builders import ModuleData, build_module_data
from .module_registry import ModuleRegistry
from .unit_specs import FermentationSpecs, SeedTrainSpecs


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


def _build_usp00_plan(config: ModuleConfig) -> UnitPlan:
    data = build_module_data(config)
    overrides = get_overrides_for(config.key)
    applied_fields: List[str] = []
    for field, value in overrides.items():
        if data.apply_override(field, value, note="default override", force=False):
            applied_fields.append(field)
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
    overrides = get_overrides_for(config.key)
    applied_fields: List[str] = []
    for field, value in overrides.items():
        if data.apply_override(field, value, note="default override", force=False):
            applied_fields.append(field)
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


def register_baseline_unit_builders(
    registry: ModuleRegistry,
    *,
    fermentation_options: Iterable[str] | None = None,
    seed_train_options: Iterable[str] | None = None,
) -> None:
    """Register builders for USP00 (fermentation) and USP01 (seed train).

    Parameters
    ----------
    registry:
        Module registry to register builders with.
    fermentation_options:
        Optional iterable of option codes to register for USP00. Defaults to the
        three options present in Excel v44 ("USP00a", "USP00b", "USP00c").
    seed_train_options:
        Optional iterable of option codes to register for USP01. Defaults to the
        two options currently observed ("USP01a" and "USP00c", which provides
        shared defaults for USP01).
    """

    fermentation_options = tuple(fermentation_options or ("USP00a", "USP00b", "USP00c"))
    for option in fermentation_options:
        registry.register(
            ModuleKey("USP00", option),
            lambda cfg, _builder=_build_usp00_plan: _builder(cfg),
            description="Fermentation unit plan from Excel defaults",
            overwrite=True,
        )

    seed_train_options = tuple(seed_train_options or ("USP01a", "USP00c"))
    for option in seed_train_options:
        registry.register(
            ModuleKey("USP01", option),
            lambda cfg, _builder=_build_usp01_plan: _builder(cfg),
            description="Seed train unit plan from Excel defaults",
            overwrite=True,
        )


__all__ = [
    "UnitPlan",
    "register_baseline_unit_builders",
]
