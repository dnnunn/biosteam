"""Structured builders transforming Excel defaults into canonical parameter sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional

from .excel_defaults import ModuleConfig, ModuleKey, ParameterRecord
from .module_registry import ModuleRegistry
from .unit_specs import (
    CampaignSchedule,
    CMOPricingSpecs,
    ChromatographySpecs,
    DryerSpecs,
    FermentationSpecs,
    MicrofiltrationSpecs,
    PreDryingSpecs,
    SeedTrainSpecs,
    UltrafiltrationSpecs,
    UtilityCostSpecs,
)


@dataclass
class ModuleData:
    """Normalized view of module inputs ready for BioSTEAM wiring."""

    key: ModuleKey
    records: Mapping[str, ParameterRecord]
    values: Dict[str, float] = field(default_factory=dict)
    field_map: Mapping[str, str] = field(default_factory=dict)

    def get(self, name: str, default: Optional[float] = None) -> Optional[float]:
        return self.values.get(name, default)

    def apply_override(
        self,
        canonical_name: str,
        value: float,
        note: Optional[str] = None,
        *,
        force: bool = False,
    ) -> bool:
        """Apply an override value for ``canonical_name`` if missing."""

        updated = False
        current = self.values.get(canonical_name)
        if current is None or force:
            self.values[canonical_name] = value
            if current != value:
                updated = True

        excel_name = next(
            (excel for excel, canonical in self.field_map.items() if canonical == canonical_name),
            None,
        )

        def _append_note(record: ParameterRecord) -> None:
            nonlocal updated
            if force or record.value is None or record.value != value:
                record.value = value
                updated = True
            if note:
                record.notes = f"{record.notes}; {note}" if record.notes else note

        if excel_name and isinstance(self.records, dict):
            record = self.records.get(excel_name)
            if record is not None:
                _append_note(record)
            else:
                self.records[excel_name] = ParameterRecord(
                    name=excel_name,
                    value=value,
                    notes=note,
                    source_row=None,
                )
                updated = True
        elif isinstance(self.records, dict):
            record = self.records.get(canonical_name)
            if record is not None:
                _append_note(record)
            else:
                self.records[canonical_name] = ParameterRecord(
                    name=canonical_name,
                    value=value,
                    notes=note,
                    source_row=None,
                )
                updated = True

        return updated

    def to_spec(self):
        builder = SPEC_BUILDERS.get(self.key.module)
        if builder:
            return builder(self)
        return self


def _extract_numeric(records: Mapping[str, ParameterRecord], field_map: Mapping[str, str]) -> Dict[str, float]:
    extracted: Dict[str, float] = {}
    for excel_name, canonical_name in field_map.items():
        record = records.get(excel_name)
        if record and record.value is not None:
            extracted[canonical_name] = record.value
    return extracted


USP00_FIELDS = {
    "Turnaround_Time": "turnaround_time_hours",
    "Biomass_Yield_on_Glucose": "biomass_yield_glucose",
    "Product_Yield_on_Biomass": "product_yield_biomass",
    "Glucose_Cost": "glucose_cost_per_kg",
    "Antifoam_Dosage": "antifoam_dosage",
}

USP01_FIELDS = {
    "Yeast_Extract_Concentration": "yeast_extract_concentration_g_per_l",
    "Peptone_Concentration": "peptone_concentration_g_per_l",
    "Yeast_Extract_Cost": "yeast_extract_cost_per_kg",
    "Peptone_Cost": "peptone_cost_per_kg",
}

USP02_FIELDS = {
    "Yeast_Extract_Concentration": "yeast_extract_concentration_g_per_l",
    "Peptone_Concentration": "peptone_concentration_g_per_l",
    "Oxygen_Transfer_Rate": "oxygen_transfer_rate",
    "Agitation_Power_Intensity": "agitation_power_intensity",
    "Aeration_Rate": "aeration_rate",
}

USP03_FIELDS = {
    "MF_Efficiency": "microfiltration_efficiency",
    "MF_Membrane_Area": "microfiltration_area_m2",
    "Microfiltration_Flux": "microfiltration_flux_l_m2_h",
    "Dilution volume": "dilution_volume_l",
    "Target product loss": "target_product_loss",
    "MF_Membrane_Cost": "microfiltration_membrane_cost",
    "MF_Membrane_Lifetime": "microfiltration_membrane_lifetime",
}

DSP01_FIELDS = {
    "UF_DF_Efficiency": "uf_df_efficiency",
    "UF_DF_Flux": "uf_df_flux_l_m2_h",
    "UF_Concentration_Factor": "uf_concentration_factor",
    "UF_Membrane_Area": "uf_membrane_area_m2",
    "Diafiltration_Volumes": "diafiltration_volumes",
    "UF_Membrane_Cost": "uf_membrane_cost",
    "UF_Membrane_Lifetime": "uf_membrane_lifetime",
}

DSP02_FIELDS = {
    "Chromatography_Dynamic_Capacity": "dynamic_binding_capacity_g_per_l",
    "Chromatography_Yield": "chromatography_yield",
    "Wash1_BV": "wash1_bv",
    "Wash2_BV": "wash2_bv",
    "Elution_BV": "elution_bv",
    "Strip_BV": "strip_bv",
    "Resin_Column_Volume_L": "resin_column_volume_l",
    "Columns_in_Service": "columns_in_service",
    "DBC_g_per_L": "dbc_g_per_l",
    "Utilization_pct": "utilization_percent",
    "Eluate_Peak_Fraction_of_Elution": "eluate_peak_fraction",
    "Resin_Cost": "resin_cost_per_l",
    "Resin_Lifetime": "resin_lifetime_cycles",
    "Phosphate_Cost": "phosphate_cost_per_kg",
    "Phosphate_MW_g_per_mol": "phosphate_mw_g_per_mol",
    "Phosphate_M": "phosphate_molarity",
    "NaCl_Cost": "nacl_cost_per_kg",
    "NaCl_MW_g_per_mol": "nacl_mw_g_per_mol",
    "NaCl_M_Wash1": "nacl_molarity_wash1",
    "NaCl_M_Wash2": "nacl_molarity_wash2",
    "NaCl_M_Elution": "nacl_molarity_elution",
    "NaCl_M_Strip": "nacl_molarity_strip",
    "Buffer_Component_Cost_Basic_kg": "buffer_component_cost_basic",
    "Buffer_Component_Cost_Premium_kg": "buffer_component_cost_premium",
}

DSP03_FIELDS = {
    "Pre_Drying_TFF_UFF_Efficiency": "pre_drying_efficiency",
    "Pre_Drying_TFF_UFF_Flux": "pre_drying_flux_l_m2_h",
    "Pre_Drying_TFF_UFF_Membrane_Area": "pre_drying_membrane_area_m2",
    "Pre_Drying_Concentration_Factor": "pre_drying_concentration_factor",
}

DSP05_FIELDS = {
    "Spray_Dryer_Efficiency": "spray_dryer_efficiency",
    "Spray_Dryer_Capacity": "spray_dryer_capacity_kg_per_hr",
    "Target_Recovery_Rate": "target_recovery_rate",
    "Solution_Density": "solution_density",
    "Final_Solids_Content": "final_solids_content",
}

PROJ00_FIELDS = {
    "Annual_Production_Target_Year": "annual_production_target_year",
    "Batches_Per_Campaign": "batches_per_campaign",
    "Annual_Campaigns": "annual_campaigns",
    "Batches_Per_Year": "batches_per_year",
}

PROJ01_FIELDS = {
    "Electricity_Cost": "electricity_cost_per_kwh",
    "Steam_Cost": "steam_cost_per_mt",
    "Compressed_Air_Cost": "compressed_air_cost",
}

PROJ02_FIELDS = {
    "Campaign_Setup_Fee": "campaign_setup_fee",
    "Campaign_Setup_Fee_Per_Batch": "campaign_setup_fee_per_batch",
    "Campaign_Changeover_Time": "campaign_changeover_time",
    "Facility_Reservation_Fee": "facility_reservation_fee",
    "Campaign_Reservation_Months": "campaign_reservation_months",
    "Long_Term_Contract_Discount": "long_term_contract_discount",
    "Contract_Length": "contract_length",
    "Annual_Price_Escalation": "annual_price_escalation",
    "Validation_Batch_Surcharge": "validation_batch_surcharge",
    "Validation_Batches_Required": "validation_batches_required",
    "Fermenter_Daily_Rate": "fermenter_daily_rate",
    "Fermenter_Campaign_Discount": "fermenter_campaign_discount",
    "DSP_Daily_Rate": "dsp_daily_rate",
    "DSP_Campaign_Discount": "dsp_campaign_discount",
    "Spray_Dryer_Hourly_Rate": "spray_dryer_hourly_rate",
    "Spray_Dryer_Campaign_Discount": "spray_dryer_campaign_discount",
    "Labor_Cost_Per_Batch": "labor_cost_per_batch",
    "Labor_Campaign_Discount": "labor_campaign_discount",
    "CMO_Overhead_Markup": "cmo_overhead_markup",
    "CMO_Consumables_Campaign_Discount": "cmo_consumables_campaign_discount",
    "Documentation_Base_Fee": "documentation_base_fee",
    "QA_Review_Base_Fee": "qa_review_base_fee",
    "QA_Campaign_Discount": "qa_campaign_discount",
}


FIELD_MAP = {
    "USP00": USP00_FIELDS,
    "USP01": USP01_FIELDS,
    "USP02": USP02_FIELDS,
    "USP03": USP03_FIELDS,
    "DSP01": DSP01_FIELDS,
    "DSP02": DSP02_FIELDS,
    "DSP03": DSP03_FIELDS,
    "DSP05": DSP05_FIELDS,
    "PROJ00": PROJ00_FIELDS,
    "PROJ01": PROJ01_FIELDS,
    "PROJ02": PROJ02_FIELDS,
}


def build_module_data(config: ModuleConfig) -> ModuleData:
    """Return normalized data for a module using predefined field mappings."""

    field_map = FIELD_MAP.get(config.key.module, {})
    values = _extract_numeric(config.parameters, field_map)
    return ModuleData(
        key=config.key,
        records=config.parameters,
        values=values,
        field_map=field_map,
    )


def register_data_builders(
    registry: ModuleRegistry,
    keys: Iterable[ModuleKey],
    *,
    description: str = "Excel default snapshot",
) -> None:
    """Register builders that return :class:`ModuleData` objects for ``keys``."""

    for key in keys:
        registry.register(
            key,
            lambda config, _key=key: build_module_data(config),
            description=description,
            overwrite=True,
        )


def register_spec_builders(
    registry: ModuleRegistry,
    keys: Iterable[ModuleKey],
    *,
    description: str = "Process specs derived from Excel defaults",
) -> None:
    """Register builders that return structured process specs."""

    for key in keys:
        registry.register(
            key,
            lambda config, _key=key: build_module_data(config).to_spec(),
            description=description,
            overwrite=True,
        )


def _build_usp00_spec(data: ModuleData) -> FermentationSpecs:
    return FermentationSpecs(
        key=data.key.module,
        turnaround_time_hours=data.get("turnaround_time_hours"),
        biomass_yield_glucose=data.get("biomass_yield_glucose"),
        product_yield_biomass=data.get("product_yield_biomass"),
        glucose_cost_per_kg=data.get("glucose_cost_per_kg"),
        antifoam_dosage=data.get("antifoam_dosage"),
    )


def _build_usp01_spec(data: ModuleData) -> SeedTrainSpecs:
    return SeedTrainSpecs(
        key=data.key.module,
        yeast_extract_concentration_g_per_l=data.get("yeast_extract_concentration_g_per_l"),
        peptone_concentration_g_per_l=data.get("peptone_concentration_g_per_l"),
        yeast_extract_cost_per_kg=data.get("yeast_extract_cost_per_kg"),
        peptone_cost_per_kg=data.get("peptone_cost_per_kg"),
    )


def _build_usp02_spec(data: ModuleData) -> MicrofiltrationSpecs:
    return MicrofiltrationSpecs(
        key=data.key.module,
        efficiency=data.get("microfiltration_efficiency"),
        membrane_area_m2=data.get("microfiltration_area_m2"),
        flux_l_m2_h=data.get("microfiltration_flux_l_m2_h"),
        dilution_volume_l=data.get("dilution_volume_l"),
        target_product_loss=data.get("target_product_loss"),
        membrane_cost=data.get("microfiltration_membrane_cost"),
        membrane_lifetime=data.get("microfiltration_membrane_lifetime"),
    )


def _build_dsp01_spec(data: ModuleData) -> UltrafiltrationSpecs:
    return UltrafiltrationSpecs(
        key=data.key.module,
        efficiency=data.get("uf_df_efficiency"),
        flux_l_m2_h=data.get("uf_df_flux_l_m2_h"),
        concentration_factor=data.get("uf_concentration_factor"),
        membrane_area_m2=data.get("uf_membrane_area_m2"),
        diafiltration_volumes=data.get("diafiltration_volumes"),
        membrane_cost=data.get("uf_membrane_cost"),
        membrane_lifetime=data.get("uf_membrane_lifetime"),
    )


def _build_dsp02_spec(data: ModuleData) -> ChromatographySpecs:
    return ChromatographySpecs(
        key=data.key.module,
        dynamic_binding_capacity_g_per_l=data.get("dynamic_binding_capacity_g_per_l"),
        chromatography_yield=data.get("chromatography_yield"),
        wash1_bv=data.get("wash1_bv"),
        wash2_bv=data.get("wash2_bv"),
        elution_bv=data.get("elution_bv"),
        strip_bv=data.get("strip_bv"),
        resin_column_volume_l=data.get("resin_column_volume_l"),
        columns_in_service=data.get("columns_in_service"),
        dbc_g_per_l=data.get("dbc_g_per_l"),
        utilization_percent=data.get("utilization_percent"),
        eluate_peak_fraction=data.get("eluate_peak_fraction"),
        resin_cost_per_l=data.get("resin_cost_per_l"),
        resin_lifetime_cycles=data.get("resin_lifetime_cycles"),
        phosphate_cost_per_kg=data.get("phosphate_cost_per_kg"),
        phosphate_mw_g_per_mol=data.get("phosphate_mw_g_per_mol"),
        phosphate_molarity=data.get("phosphate_molarity"),
        nacl_cost_per_kg=data.get("nacl_cost_per_kg"),
        nacl_mw_g_per_mol=data.get("nacl_mw_g_per_mol"),
        nacl_molarity_wash1=data.get("nacl_molarity_wash1"),
        nacl_molarity_wash2=data.get("nacl_molarity_wash2"),
        nacl_molarity_elution=data.get("nacl_molarity_elution"),
        nacl_molarity_strip=data.get("nacl_molarity_strip"),
        buffer_component_cost_basic=data.get("buffer_component_cost_basic"),
        buffer_component_cost_premium=data.get("buffer_component_cost_premium"),
    )


def _build_dsp03_spec(data: ModuleData) -> PreDryingSpecs:
    return PreDryingSpecs(
        key=data.key.module,
        efficiency=data.get("pre_drying_efficiency"),
        flux_l_m2_h=data.get("pre_drying_flux_l_m2_h"),
        membrane_area_m2=data.get("pre_drying_membrane_area_m2"),
        concentration_factor=data.get("pre_drying_concentration_factor"),
    )


def _build_dsp05_spec(data: ModuleData) -> DryerSpecs:
    return DryerSpecs(
        key=data.key.module,
        spray_dryer_efficiency=data.get("spray_dryer_efficiency"),
        spray_dryer_capacity_kg_per_hr=data.get("spray_dryer_capacity_kg_per_hr"),
        target_recovery_rate=data.get("target_recovery_rate"),
        solution_density=data.get("solution_density"),
        final_solids_content=data.get("final_solids_content"),
    )


def _build_proj00_spec(data: ModuleData) -> CampaignSchedule:
    return CampaignSchedule(
        key=data.key.module,
        annual_production_target_year=data.get("annual_production_target_year"),
        batches_per_campaign=data.get("batches_per_campaign"),
        annual_campaigns=data.get("annual_campaigns"),
        batches_per_year=data.get("batches_per_year"),
    )


def _build_proj01_spec(data: ModuleData) -> UtilityCostSpecs:
    return UtilityCostSpecs(
        key=data.key.module,
        electricity_cost_per_kwh=data.get("electricity_cost_per_kwh"),
        steam_cost_per_mt=data.get("steam_cost_per_mt"),
        compressed_air_cost=data.get("compressed_air_cost"),
    )


def _build_proj02_spec(data: ModuleData) -> CMOPricingSpecs:
    return CMOPricingSpecs(
        key=data.key.module,
        campaign_setup_fee=data.get("campaign_setup_fee"),
        campaign_setup_fee_per_batch=data.get("campaign_setup_fee_per_batch"),
        campaign_changeover_time=data.get("campaign_changeover_time"),
        facility_reservation_fee=data.get("facility_reservation_fee"),
        campaign_reservation_months=data.get("campaign_reservation_months"),
        long_term_contract_discount=data.get("long_term_contract_discount"),
        contract_length=data.get("contract_length"),
        annual_price_escalation=data.get("annual_price_escalation"),
        validation_batch_surcharge=data.get("validation_batch_surcharge"),
        validation_batches_required=data.get("validation_batches_required"),
        fermenter_daily_rate=data.get("fermenter_daily_rate"),
        fermenter_campaign_discount=data.get("fermenter_campaign_discount"),
        dsp_daily_rate=data.get("dsp_daily_rate"),
        dsp_campaign_discount=data.get("dsp_campaign_discount"),
        spray_dryer_hourly_rate=data.get("spray_dryer_hourly_rate"),
        spray_dryer_campaign_discount=data.get("spray_dryer_campaign_discount"),
        labor_cost_per_batch=data.get("labor_cost_per_batch"),
        labor_campaign_discount=data.get("labor_campaign_discount"),
        cmo_overhead_markup=data.get("cmo_overhead_markup"),
        cmo_consumables_campaign_discount=data.get("cmo_consumables_campaign_discount"),
        documentation_base_fee=data.get("documentation_base_fee"),
        qa_review_base_fee=data.get("qa_review_base_fee"),
        qa_campaign_discount=data.get("qa_campaign_discount"),
    )


SPEC_BUILDERS = {
    "USP00": _build_usp00_spec,
    "USP01": _build_usp01_spec,
    "USP02": _build_usp02_spec,
    "DSP01": _build_dsp01_spec,
    "DSP02": _build_dsp02_spec,
    "DSP03": _build_dsp03_spec,
    "DSP05": _build_dsp05_spec,
    "PROJ00": _build_proj00_spec,
    "PROJ01": _build_proj01_spec,
    "PROJ02": _build_proj02_spec,
}


__all__ = [
    "ModuleData",
    "build_module_data",
    "register_data_builders",
    "register_spec_builders",
]
