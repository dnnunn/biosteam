"""Dataclasses capturing process specs derived from Excel defaults."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


Number = Optional[float]


@dataclass
class FermentationSpecs:
    key: str
    turnaround_time_hours: Number
    biomass_yield_glucose: Number
    product_yield_biomass: Number
    glucose_cost_per_kg: Number
    antifoam_dosage: Number

    def estimated_batch_cycle_hours(self) -> Number:
        if self.turnaround_time_hours is None:
            return None
        # Assume fixed 48 h fermentation when not provided; adjust by turnaround.
        return 48.0 + self.turnaround_time_hours


@dataclass
class SeedTrainSpecs:
    key: str
    yeast_extract_concentration_g_per_l: Number
    peptone_concentration_g_per_l: Number
    yeast_extract_cost_per_kg: Number
    peptone_cost_per_kg: Number


@dataclass
class MicrofiltrationSpecs:
    key: str
    efficiency: Number
    membrane_area_m2: Number
    flux_l_m2_h: Number
    dilution_volume_l: Number
    target_product_loss: Number
    membrane_cost: Number
    membrane_lifetime: Number

    def membrane_area_per_batch(self) -> Number:
        return self.membrane_area_m2


@dataclass
class DiscStackSpecs:
    key: str
    sigma_m2: Number
    product_recovery_fraction: Number
    solids_carryover_fraction: Number
    wet_cake_moisture_fraction: Number
    power_kwh_per_m3: Number
    parallel_trains: Optional[int] = None


@dataclass
class DepthFilterSpecs:
    key: str
    product_recovery_fraction: Number
    holdup_loss_kg: Number
    specific_capacity_l_per_m2: Optional[list[Number]] = None
    flux_lmh: Number = None  # type: ignore[assignment]
    terminal_delta_p_bar: Number = None  # type: ignore[assignment]
    media_cost_per_m2: Number = None  # type: ignore[assignment]


@dataclass
class MFTFFSpecs:
    key: str
    product_recovery_fraction: Number
    flux_lmh: Number
    membrane_cost_per_m2: Number
    membrane_life_batches: Optional[float] = None


@dataclass
class ContinuousCentrifugeSpecs:
    key: str
    sigma_m2: Number
    product_recovery_fraction: Number
    solids_carryover_fraction: Number
    wet_cake_moisture_fraction: Number
    power_kwh_per_m3: Number


@dataclass
class UltrafiltrationSpecs:
    key: str
    efficiency: Number
    flux_l_m2_h: Number
    concentration_factor: Number
    membrane_area_m2: Number
    diafiltration_volumes: Number
    membrane_cost: Number
    membrane_lifetime: Number


@dataclass
class ChromatographySpecs:
    key: str
    dynamic_binding_capacity_g_per_l: Number
    chromatography_yield: Number
    wash1_bv: Number
    wash2_bv: Number
    elution_bv: Number
    strip_bv: Number
    resin_column_volume_l: Number
    columns_in_service: Number
    dbc_g_per_l: Number
    utilization_percent: Number
    eluate_peak_fraction: Number
    resin_cost_per_l: Number
    resin_lifetime_cycles: Number
    phosphate_cost_per_kg: Number
    phosphate_mw_g_per_mol: Number
    phosphate_molarity: Number
    nacl_cost_per_kg: Number
    nacl_mw_g_per_mol: Number
    nacl_molarity_wash1: Number
    nacl_molarity_wash2: Number
    nacl_molarity_elution: Number
    nacl_molarity_strip: Number
    buffer_component_cost_basic: Number
    buffer_component_cost_premium: Number

    def resin_cost_per_batch(self) -> Number:
        if None in (self.resin_cost_per_l, self.resin_column_volume_l, self.resin_lifetime_cycles):
            return None
        if not self.resin_lifetime_cycles:
            return None
        return (self.resin_cost_per_l * self.resin_column_volume_l) / self.resin_lifetime_cycles


@dataclass
class PreDryingSpecs:
    key: str
    efficiency: Number
    flux_l_m2_h: Number
    membrane_area_m2: Number
    concentration_factor: Number


@dataclass
class DryerSpecs:
    key: str
    spray_dryer_efficiency: Number
    spray_dryer_capacity_kg_per_hr: Number
    target_recovery_rate: Number
    solution_density: Number
    final_solids_content: Number


@dataclass
class CampaignSchedule:
    key: str
    annual_production_target_year: Number
    batches_per_campaign: Number
    annual_campaigns: Number
    batches_per_year: Number


@dataclass
class UtilityCostSpecs:
    key: str
    electricity_cost_per_kwh: Number
    steam_cost_per_mt: Number
    compressed_air_cost: Number


@dataclass
class CMOPricingSpecs:
    key: str
    campaign_setup_fee: Number
    campaign_setup_fee_per_batch: Number
    campaign_changeover_time: Number
    facility_reservation_fee: Number
    campaign_reservation_months: Number
    long_term_contract_discount: Number
    contract_length: Number
    annual_price_escalation: Number
    validation_batch_surcharge: Number
    validation_batches_required: Number
    fermenter_daily_rate: Number
    fermenter_campaign_discount: Number
    dsp_daily_rate: Number
    dsp_campaign_discount: Number
    spray_dryer_hourly_rate: Number
    spray_dryer_campaign_discount: Number
    labor_cost_per_batch: Number
    labor_campaign_discount: Number
    cmo_overhead_markup: Number
    cmo_consumables_campaign_discount: Number
    documentation_base_fee: Number
    qa_review_base_fee: Number
    qa_campaign_discount: Number


SPEC_TYPES = {
    'USP00': FermentationSpecs,
    'USP01': SeedTrainSpecs,
    'USP02': MicrofiltrationSpecs,
    'DSP01': UltrafiltrationSpecs,
    'DSP02': ChromatographySpecs,
    'DSP03': PreDryingSpecs,
    'DSP05': DryerSpecs,
    'PROJ00': CampaignSchedule,
    'PROJ01': UtilityCostSpecs,
    'PROJ02': CMOPricingSpecs,
}


__all__ = [
    'FermentationSpecs',
    'SeedTrainSpecs',
    'MicrofiltrationSpecs',
    'DiscStackSpecs',
    'DepthFilterSpecs',
    'MFTFFSpecs',
    'ContinuousCentrifugeSpecs',
    'UltrafiltrationSpecs',
    'ChromatographySpecs',
    'PreDryingSpecs',
    'DryerSpecs',
    'CampaignSchedule',
    'UtilityCostSpecs',
    'CMOPricingSpecs',
    'SPEC_TYPES',
]
