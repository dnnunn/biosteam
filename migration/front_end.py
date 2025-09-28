"""Helpers to assemble the upstream (front-end) section of the migration flowsheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
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
    total_cost_per_batch_usd: Optional[float] = None
    cmo_fees_usd: Optional[float] = None
    cost_per_kg_usd: Optional[float] = None
    materials_cost_per_batch_usd: Optional[float] = None
    computed_material_cost_per_batch_usd: Optional[float] = None
    material_cost_breakdown: Dict[str, float] = field(default_factory=dict)

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


def _read_sheet_cell(
    workbook_path: Path | str,
    sheet_name: str,
    row: int,
    col: int,
) -> Optional[float]:
    try:
        import pandas as pd
    except ImportError:  # pragma: no cover
        return None

    try:
        value = pd.read_excel(
            workbook_path,
            sheet_name=sheet_name,
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


def _read_inputs_cell(defaults: ExcelModuleDefaults, row_1_based: int) -> Optional[float]:
    return _read_sheet_cell(defaults.workbook_path, "Inputs and Assumptions", row_1_based - 1, 1)


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
    total_glycerol_feed_kg = _read_calculation_cell(defaults, 82, 1)  # Calculations!B83
    total_molasses_feed_kg = _read_calculation_cell(defaults, 84, 1)  # Calculations!B85
    yeast_extract_per_batch = _read_calculation_cell(defaults, 85, 1)  # Calculations!B86
    peptone_per_batch = _read_calculation_cell(defaults, 86, 1)  # Calculations!B87
    antifoam_volume_l = _read_calculation_cell(defaults, 87, 1)  # Calculations!B88

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

    if total_glycerol_feed_kg is not None:
        fermentation_plan.derived["total_glycerol_feed_kg"] = total_glycerol_feed_kg
    if total_molasses_feed_kg is not None:
        fermentation_plan.derived["total_molasses_feed_kg"] = total_molasses_feed_kg

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
    if yeast_extract_per_batch is not None:
        seed_plan.derived["yeast_extract_per_batch_kg"] = yeast_extract_per_batch
    if peptone_per_batch is not None:
        seed_plan.derived["peptone_per_batch_kg"] = peptone_per_batch

    seed_specs = seed_unit.plan.specs
    yeast_cost_per_kg = _read_inputs_cell(defaults, 138)
    if yeast_cost_per_kg is not None and getattr(seed_specs, "yeast_extract_cost_per_kg", None) in (None, 0):
        seed_specs.yeast_extract_cost_per_kg = yeast_cost_per_kg

    peptone_cost_per_kg = _read_inputs_cell(defaults, 139)
    if peptone_cost_per_kg is not None and getattr(seed_specs, "peptone_cost_per_kg", None) in (None, 0):
        seed_specs.peptone_cost_per_kg = peptone_cost_per_kg

    fermentation_product = fermentation_plan.derived.get("product_out_kg")

    if antifoam_volume_l is not None:
        fermentation_plan.derived["antifoam_volume_l"] = antifoam_volume_l

    fermentation_specs = fermentation_unit.plan.specs
    glucose_cost = _read_inputs_cell(defaults, 134)
    glycerol_cost = _read_inputs_cell(defaults, 135)
    molasses_cost = _read_inputs_cell(defaults, 137)
    carbon_cost_lookup = {
        "glucose": glucose_cost,
        "glycerol": glycerol_cost,
        "molasses": molasses_cost,
    }
    carbon_source = fermentation_plan.derived.get("carbon_source")
    carbon_cost = carbon_cost_lookup.get(carbon_source)
    if carbon_cost is not None and getattr(fermentation_specs, "glucose_cost_per_kg", None) in (None, 0):
        fermentation_specs.glucose_cost_per_kg = carbon_cost

    antifoam_cost = _read_inputs_cell(defaults, 141)
    if antifoam_cost is not None:
        fermentation_plan.derived.setdefault("antifoam_cost_per_unit", antifoam_cost)

    minor_nutrient_total = fermentation_plan.derived.get("minor_nutrients_cost_total")
    if minor_nutrient_total is None:
        value = _read_inputs_cell(defaults, 140)
        if value is not None:
            fermentation_plan.derived["minor_nutrients_cost_total"] = value

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

    cost_per_kg_usd = _read_calculation_cell(defaults, 0, 1)
    cmo_fees_usd = _read_calculation_cell(defaults, 247, 1)
    total_cost_per_batch_usd = _read_sheet_cell(
        defaults.workbook_path, "Final Costs", 7, 1
    )
    materials_cost_per_batch = None
    if (
        total_cost_per_batch_usd is not None
        and cmo_fees_usd is not None
    ):
        materials_cost_per_batch = total_cost_per_batch_usd - cmo_fees_usd

    if (
        cost_per_kg_usd is None
        and total_cost_per_batch_usd is not None
        and final_product_kg is not None
        and final_product_kg != 0
    ):
        cost_per_kg_usd = total_cost_per_batch_usd / final_product_kg

    # Compute material cost breakdown using Excel-derived values (subject to refinement).
    def _calc_cell(row: int, col: int = 1) -> Optional[float]:
        return _read_calculation_cell(defaults, row, col)

    breakdown: Dict[str, float] = {}

    def _add_breakdown(key: str, value: Optional[float]) -> float:
        if value is not None:
            breakdown[key] = value
            return value
        return 0.0

    carbon_cost = _calc_cell(166)  # Calculations!B167
    yeast_cost = _calc_cell(167)   # Calculations!B168
    peptone_cost = _calc_cell(168)  # Calculations!B169
    minor_nutrients_cost = _calc_cell(169)  # Calculations!B170
    antifoam_cost = _calc_cell(170)  # Calculations!B171
    buffer_cost = _calc_cell(193)  # Calculations!B194
    resin_cost = _calc_cell(177)  # Calculations!B178
    mf_membrane_cost = _calc_cell(171)  # Calculations!B172
    uf_membrane_cost = _calc_cell(174)  # Calculations!B175
    tff_membrane_cost = _calc_cell(189)  # Calculations!B190
    cip_chemicals_cost = _calc_cell(192)  # Calculations!B193
    membrane_cleaning_cost = _read_sheet_cell(
        defaults.workbook_path, "Inputs and Assumptions", 168, 1
    )

    fermentation_specs = fermentation_unit.plan.specs
    carbon_source = fermentation_plan.derived.get("carbon_source")
    carbon_mass = 0.0
    if carbon_source == "glucose":
        carbon_mass = fermentation_plan.derived.get("total_glucose_feed_kg") or 0.0
    elif carbon_source == "glycerol":
        carbon_mass = fermentation_plan.derived.get("total_glycerol_feed_kg") or 0.0
    elif carbon_source == "molasses":
        carbon_mass = fermentation_plan.derived.get("total_molasses_feed_kg") or 0.0
    carbon_cost_calc = None
    if carbon_mass and fermentation_specs.glucose_cost_per_kg:
        carbon_cost_calc = carbon_mass * fermentation_specs.glucose_cost_per_kg

    seed_specs = seed_unit.plan.specs
    yeast_mass = seed_plan.derived.get("yeast_extract_per_batch_kg")
    yeast_cost_calc = None
    if yeast_mass is not None and seed_specs.yeast_extract_cost_per_kg is not None:
        yeast_cost_calc = yeast_mass * seed_specs.yeast_extract_cost_per_kg

    peptone_mass = seed_plan.derived.get("peptone_per_batch_kg")
    peptone_cost_calc = None
    if peptone_mass is not None and seed_specs.peptone_cost_per_kg is not None:
        peptone_cost_calc = peptone_mass * seed_specs.peptone_cost_per_kg

    antifoam_volume = fermentation_plan.derived.get("antifoam_volume_l")
    antifoam_cost_per_unit = fermentation_plan.derived.get("antifoam_cost_per_unit")
    antifoam_cost_calc = None
    if antifoam_volume is not None and antifoam_cost_per_unit is not None:
        antifoam_cost_calc = antifoam_volume * antifoam_cost_per_unit

    minor_nutrients_cost_calc = fermentation_plan.derived.get("minor_nutrients_cost_total")

    computed_material_cost = 0.0

    def _set_cost(key: str, computed: Optional[float], fallback: Optional[float]) -> None:
        nonlocal computed_material_cost
        value = computed if computed is not None else fallback
        if value is not None:
            breakdown[key] = value
            computed_material_cost += value

    _set_cost("carbon_source", carbon_cost_calc, _calc_cell(166))
    _set_cost("yeast_extract", yeast_cost_calc, _calc_cell(167))
    _set_cost("peptone", peptone_cost_calc, _calc_cell(168))
    _set_cost("minor_nutrients", minor_nutrients_cost_calc, _calc_cell(169))
    _set_cost("antifoam", antifoam_cost_calc, _calc_cell(170))
    _set_cost("buffers", None, _calc_cell(193))
    _set_cost("resin", None, _calc_cell(177))
    _set_cost("mf_membranes", None, _calc_cell(171))
    _set_cost("uf_df_membranes", None, _calc_cell(174))
    _set_cost("predry_tff_membranes", None, _calc_cell(189))
    _set_cost("cip_chemicals", None, _calc_cell(192))
    _set_cost(
        "membrane_cleaning",
        None,
        _read_sheet_cell(defaults.workbook_path, "Inputs and Assumptions", 168, 1),
    )

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
    microfiltration_unit.ins[0] = fermentation_broth
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
        total_cost_per_batch_usd=total_cost_per_batch_usd,
        cmo_fees_usd=cmo_fees_usd,
        cost_per_kg_usd=cost_per_kg_usd,
        materials_cost_per_batch_usd=materials_cost_per_batch,
        computed_material_cost_per_batch_usd=computed_material_cost,
        material_cost_breakdown=breakdown,
    )


__all__ = [
    "FrontEndSection",
    "build_front_end_section",
]
