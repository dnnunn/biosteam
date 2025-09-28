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
    ufdf_unit: bst.Unit
    chromatography_unit: bst.Unit
    predrying_unit: bst.Unit
    spray_dryer_unit: bst.Unit
    system: bst.System
    defaults: ExcelModuleDefaults

    def units(self) -> tuple[bst.Unit, ...]:
        """Return the ordered unit operations for convenience."""

        return (
            self.seed_unit,
            self.fermentation_unit,
            self.microfiltration_unit,
            self.ufdf_unit,
            self.chromatography_unit,
            self.predrying_unit,
            self.spray_dryer_unit,
        )

    def simulate(self, *, design: bool = False, cost: bool = False) -> None:
        """Run the front-end units in sequence using plan-derived targets."""

        for unit in self.units():
            unit._run()
            if design:
                unit._design()
            if cost:
                unit._cost()


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


def _read_calculation_cell(
    defaults: ExcelModuleDefaults,
    row: int,
    col: int,
) -> Optional[float]:
    try:
        import pandas as pd
    except ImportError:  # pragma: no cover
        return None

    try:
        value = pd.read_excel(
            defaults.workbook_path,
            sheet_name="Calculations",
            header=None,
            skiprows=row,
            nrows=1,
            usecols=[col],
        ).iloc[0, 0]
    except Exception:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
    glucose_mass = (feed_carbon or 0.0) * seed_volume_l / 1e3
    water_mass = max(total_mass - glucose_mass, 0.0)

    feed.imass["Water"] = water_mass
    if glucose_mass > 0:
        feed.imass["Glucose"] = glucose_mass

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
    workbook_path: str,
    *,
    batch_volume_l: Optional[float] = None,
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

    working_titer = _read_calculation_cell(defaults, 46, 1)  # Calculations!B47
    dcw_concentration = _read_calculation_cell(defaults, 28, 1)  # Calculations!B29
    total_glucose_feed_kg = _read_calculation_cell(defaults, 81, 1)  # Calculations!B82

    product_preharvest = _read_calculation_cell(defaults, 43, 1)  # Calculations!B44
    harvested_product = _read_calculation_cell(defaults, 44, 1)  # Calculations!B45
    harvest_volume_l = _read_calculation_cell(defaults, 104, 1)  # Calculations!B105
    product_after_mf = _read_calculation_cell(defaults, 107, 1)  # Calculations!B108
    product_after_uf = _read_calculation_cell(defaults, 110, 1)  # Calculations!B111
    post_uf_volume_l = _read_calculation_cell(defaults, 111, 1)  # Calculations!B112
    product_after_chrom = _read_calculation_cell(defaults, 112, 1)  # Calculations!B113
    post_elution_volume_l = _read_calculation_cell(defaults, 115, 1)  # Calculations!B116
    post_elution_conc_volume_l = _read_calculation_cell(defaults, 116, 1)  # Calculations!B117
    volume_to_spray_l = _read_calculation_cell(defaults, 117, 1)  # Calculations!B118
    product_after_predry = _read_calculation_cell(defaults, 119, 1)  # Calculations!B120
    final_product_kg = _read_calculation_cell(defaults, 120, 1)  # Calculations!B121

    fermentation_plan = fermentation_unit.plan
    fermentation_plan.derived.update(
        {
            "working_volume_l": working_volume_l,
            "target_titer_g_per_l": working_titer,
            "dcw_concentration_g_per_l": dcw_concentration,
            "total_glucose_feed_kg": total_glucose_feed_kg,
        }
    )

    if working_titer is not None:
        fermentation_plan.derived["product_out_kg"] = (
            working_titer * working_volume_l / 1_000.0
        )
    elif product_preharvest is not None:
        fermentation_plan.derived["product_out_kg"] = product_preharvest

    seed_plan = seed_unit.plan
    seed_plan.derived.update(
        {
            "working_volume_l": seed_volume_l,
            "dcw_concentration_g_per_l": dcw_concentration,
            "seed_glucose_conversion_fraction": 0.0,
        }
    )

    fermentation_product = fermentation_plan.derived.get("product_out_kg")

    micro_plan = microfiltration_unit.plan
    micro_plan.derived.update(
        {
            "input_product_kg": fermentation_product,
            "input_volume_l": working_volume_l,
            "output_volume_l": harvest_volume_l,
            "product_out_kg": product_after_mf,
            "harvested_product_kg": harvested_product,
        }
    )

    uf_plan = ufdf_unit.plan
    uf_plan.derived.update(
        {
            "input_product_kg": product_after_mf,
            "input_volume_l": harvest_volume_l,
            "output_volume_l": post_uf_volume_l,
            "product_out_kg": product_after_uf,
        }
    )

    chrom_plan = chromatography_unit.plan
    chrom_plan.derived.update(
        {
            "input_product_kg": product_after_uf,
            "eluate_volume_l": post_elution_volume_l,
            "output_volume_l": post_elution_conc_volume_l,
            "product_out_kg": product_after_chrom,
        }
    )

    predry_plan = predrying_unit.plan
    predry_plan.derived.update(
        {
            "input_product_kg": product_after_chrom,
            "input_volume_l": post_elution_conc_volume_l,
            "output_volume_l": volume_to_spray_l,
            "product_out_kg": product_after_predry,
        }
    )

    spray_plan = spray_dryer_unit.plan
    spray_plan.derived.update(
        {
            "input_product_kg": product_after_predry,
            "product_out_kg": final_product_kg,
        }
    )

    feed = _build_seed_media_stream(
        fermentation_unit=fermentation_unit,
        seed_unit=seed_unit,
        seed_volume_l=seed_volume_l,
        dcw_concentration_g_per_l=dcw_concentration,
    )

    seed_unit.ins[0] = feed
    fermentation_unit.ins[0] = seed_unit.outs[0]
    microfiltration_unit.ins[0] = fermentation_unit.outs[0]
    ufdf_unit.ins[0] = microfiltration_unit.outs[0]
    chromatography_unit.ins[0] = ufdf_unit.outs[0]
    predrying_unit.ins[0] = chromatography_unit.outs[0]
    spray_dryer_unit.ins[0] = predrying_unit.outs[0]

    active_flowsheet = flowsheet or bst.Flowsheet("bd_front_end")
    bst.main_flowsheet.set_flowsheet(active_flowsheet)

    system = bst.System(
        "front_end",
        path=(
            seed_unit,
            fermentation_unit,
            microfiltration_unit,
            ufdf_unit,
            chromatography_unit,
            predrying_unit,
            spray_dryer_unit,
        ),
    )

    return FrontEndSection(
        feed=feed,
        seed_unit=seed_unit,
        fermentation_unit=fermentation_unit,
        microfiltration_unit=microfiltration_unit,
        ufdf_unit=ufdf_unit,
        chromatography_unit=chromatography_unit,
        predrying_unit=predrying_unit,
        spray_dryer_unit=spray_dryer_unit,
        system=system,
        defaults=defaults,
    )


__all__ = [
    "FrontEndSection",
    "build_front_end_section",
]
