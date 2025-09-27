"""Helpers to assemble the upstream (front-end) section of the migration flowsheet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import biosteam as bst

from .excel_defaults import ExcelModuleDefaults, ModuleConfig, ModuleKey
from .module_registry import ModuleRegistry
from .unit_builders import register_baseline_unit_builders, set_defaults_loader
from .unit_factories import register_plan_backed_unit_factories
from .thermo_setup import set_migration_thermo

FRONT_END_KEYS = (
    ModuleKey("USP01", "USP01a"),
    ModuleKey("USP00", "USP00a"),
    ModuleKey("USP02", "USP02a"),
)


@dataclass
class FrontEndSection:
    """Container with the simulated seed, fermentation, and harvest units."""

    feed: bst.Stream
    seed_unit: bst.Unit
    fermentation_unit: bst.Unit
    harvest_unit: bst.Unit
    system: bst.System
    defaults: ExcelModuleDefaults


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


def _build_seed_media_stream(
    *,
    fermentation_unit: bst.Unit,
    seed_unit: bst.Unit,
    batch_volume_l: float,
) -> bst.Stream:
    feed = bst.Stream("seed_media", T=298.15, P=101325.0)

    # Base assumption: bulk density of 1 kg/L for the broth.
    total_mass = batch_volume_l  # kg
    plan = fermentation_unit.plan
    derived = plan.derived
    feed_carbon = derived.get("feed_carbon_concentration_g_per_l") or derived.get(
        "initial_carbon_concentration_g_per_l"
    )
    glucose_mass = (feed_carbon or 0.0) * batch_volume_l / 1e3
    water_mass = max(total_mass - glucose_mass, 0.0)

    feed.imass["Water"] = water_mass
    if glucose_mass > 0:
        feed.imass["Glucose"] = glucose_mass

    specs = seed_unit.plan.specs
    def _add_if_available(component: str, value: Optional[float]) -> None:
        if value is None:
            return
        mass = value * batch_volume_l / 1e3
        if mass <= 0:
            return
        feed.imass[component] = mass

    _add_if_available("YeastExtract", specs.yeast_extract_concentration_g_per_l)
    _add_if_available("Peptone", specs.peptone_concentration_g_per_l)

    return feed


def build_front_end_section(
    workbook_path: str,
    *,
    batch_volume_l: float = 1_000.0,
    flowsheet: Optional[bst.Flowsheet] = None,
) -> FrontEndSection:
    """Instantiate the seed train, fermentation, and harvest units for the baseline flow."""

    defaults = ExcelModuleDefaults(workbook_path)
    set_defaults_loader(defaults)
    set_migration_thermo()

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
    harvest_unit = key_to_unit[ModuleKey("USP02", "USP02a")]

    feed = _build_seed_media_stream(
        fermentation_unit=fermentation_unit,
        seed_unit=seed_unit,
        batch_volume_l=batch_volume_l,
    )

    seed_unit.ins[0] = feed
    fermentation_unit.ins[0] = seed_unit.outs[0]
    harvest_unit.ins[0] = fermentation_unit.outs[0]

    active_flowsheet = flowsheet or bst.Flowsheet("bd_front_end")
    bst.main_flowsheet.set_flowsheet(active_flowsheet)

    system = bst.System("front_end", path=(seed_unit, fermentation_unit, harvest_unit))

    return FrontEndSection(
        feed=feed,
        seed_unit=seed_unit,
        fermentation_unit=fermentation_unit,
        harvest_unit=harvest_unit,
        system=system,
        defaults=defaults,
    )


__all__ = [
    "FrontEndSection",
    "build_front_end_section",
]
