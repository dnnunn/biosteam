"""DSP05 final form and finish routing (spray dry, lyophilize, etc.)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional


__all__ = [
    "DSP05Method",
    "SprayDryConfig",
    "LyophilizeConfig",
    "LiquidBulkConfig",
    "DSP05Config",
    "FinalProductHandoff",
    "build_dsp05_chain",
]


class DSP05Method(str, Enum):
    SPRAY_DRY = "SprayDry"
    LYOPHILIZE = "Lyophilize"
    LIQUID_BULK = "LiquidBulk"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "DSP05Method":
        if isinstance(value, cls):
            return value
        normalized = (value or cls.SPRAY_DRY.value).strip().lower()
        for member in cls:
            if member.value.lower() == normalized:
                return member
        return cls.SPRAY_DRY


@dataclass
class SprayDryConfig:
    target_moisture_wt_pct: float = 3.0
    min_feed_solids_wt_pct_for_spray: float = 5.0
    precon_enable: bool = True
    precon_target_solids_wt_pct: float = 12.0
    dryer_yield_frac: float = 0.99
    bulk_density_kg_m3: float = 350.0
    max_inlet_temp_c: float = 190.0
    outlet_temp_c: float = 80.0


@dataclass
class LyophilizeConfig:
    target_moisture_wt_pct: float = 1.0
    primary_dry_time_h: float = 12.0
    secondary_dry_time_h: float = 6.0
    lyo_yield_frac: float = 0.99


@dataclass
class LiquidBulkConfig:
    target_conc_g_per_l: float = 100.0
    hold_temp_c: float = 4.0
    use_internal_precon: bool = False


@dataclass
class DSP05Config:
    method: DSP05Method = DSP05Method.SPRAY_DRY
    toll_fee_usd_per_m3_feed: float = 120.0
    utilities_usd_per_batch: float = 800.0
    consumables_usd_per_batch: float = 300.0
    labor_h_per_batch: float = 6.0
    labor_rate_usd_per_h: float = 80.0
    waste_fee_usd_per_tonne: float = 220.0
    dryer_capex_usd: float = 0.0
    install_factor: float = 1.8
    depr_years: float = 10.0
    annual_maint_frac: float = 0.03
    spraydry: SprayDryConfig = field(default_factory=SprayDryConfig)
    lyophilize: LyophilizeConfig = field(default_factory=LyophilizeConfig)
    liquid: LiquidBulkConfig = field(default_factory=LiquidBulkConfig)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object] | None) -> "DSP05Config":
        if not isinstance(data, Mapping):
            return cls()

        method = DSP05Method.from_string(data.get("method"))

        def _float(name: str, default: float) -> float:
            try:
                value = data.get(name)
                return float(value) if value is not None else default
            except (TypeError, ValueError):
                return default

        config = cls(
            method=method,
            toll_fee_usd_per_m3_feed=_float("toll_fee_usd_per_m3_feed", 120.0),
            utilities_usd_per_batch=_float("utilities_usd_per_batch", 800.0),
            consumables_usd_per_batch=_float("consumables_usd_per_batch", 300.0),
            labor_h_per_batch=_float("labor_h_per_batch", 6.0),
            labor_rate_usd_per_h=_float("labor_rate_usd_per_h", 80.0),
            waste_fee_usd_per_tonne=_float("waste_fee_usd_per_tonne", 220.0),
            dryer_capex_usd=_float("dryer_capex_usd", 0.0),
            install_factor=_float("install_factor", 1.8),
            depr_years=_float("depr_years", 10.0),
            annual_maint_frac=_float("annual_maint_frac", 0.03),
        )

        spray_cfg = data.get("spraydry") if isinstance(data.get("spraydry"), Mapping) else {}
        if isinstance(spray_cfg, Mapping):
            config.spraydry = SprayDryConfig(
                target_moisture_wt_pct=_float_nested(spray_cfg, "target_moisture_wt_pct", config.spraydry.target_moisture_wt_pct),
                min_feed_solids_wt_pct_for_spray=_float_nested(spray_cfg, "min_feed_solids_wt_pct_for_spray", config.spraydry.min_feed_solids_wt_pct_for_spray),
                precon_enable=bool(spray_cfg.get("precon_enable", config.spraydry.precon_enable)),
                precon_target_solids_wt_pct=_float_nested(spray_cfg, "precon_target_solids_wt_pct", config.spraydry.precon_target_solids_wt_pct),
                dryer_yield_frac=_float_nested(spray_cfg, "dryer_yield_frac", config.spraydry.dryer_yield_frac),
                bulk_density_kg_m3=_float_nested(spray_cfg, "bulk_density_kg_m3", config.spraydry.bulk_density_kg_m3),
                max_inlet_temp_c=_float_nested(spray_cfg, "max_inlet_temp_C", config.spraydry.max_inlet_temp_c),
                outlet_temp_c=_float_nested(spray_cfg, "outlet_temp_C", config.spraydry.outlet_temp_c),
            )

        lyo_cfg = data.get("lyophilize") if isinstance(data.get("lyophilize"), Mapping) else {}
        if isinstance(lyo_cfg, Mapping):
            config.lyophilize = LyophilizeConfig(
                target_moisture_wt_pct=_float_nested(lyo_cfg, "target_moisture_wt_pct", config.lyophilize.target_moisture_wt_pct),
                primary_dry_time_h=_float_nested(lyo_cfg, "primary_dry_time_h", config.lyophilize.primary_dry_time_h),
                secondary_dry_time_h=_float_nested(lyo_cfg, "secondary_dry_time_h", config.lyophilize.secondary_dry_time_h),
                lyo_yield_frac=_float_nested(lyo_cfg, "lyo_yield_frac", config.lyophilize.lyo_yield_frac),
            )

        liquid_cfg = data.get("liquid") if isinstance(data.get("liquid"), Mapping) else {}
        if isinstance(liquid_cfg, Mapping):
            config.liquid = LiquidBulkConfig(
                target_conc_g_per_l=_float_nested(liquid_cfg, "target_conc_gL", config.liquid.target_conc_g_per_l),
                hold_temp_c=_float_nested(liquid_cfg, "hold_temp_C", config.liquid.hold_temp_c),
                use_internal_precon=bool(liquid_cfg.get("use_internal_precon", config.liquid.use_internal_precon)),
            )

        return config


def _float_nested(data: Mapping[str, object], key: str, default: float) -> float:
    try:
        value = data.get(key)
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


@dataclass
class FinalProductHandoff:
    method: DSP05Method
    product_form: str
    product_mass_kg: Optional[float]
    product_volume_m3: Optional[float]
    protein_concentration_g_per_l: Optional[float]
    moisture_wt_pct: Optional[float]
    bulk_density_kg_m3: Optional[float]
    step_recovery_fraction: Optional[float]
    cycle_time_h: Optional[float]
    client_cost_usd: Optional[float]
    capex_flagged_usd: Optional[float]
    notes: list[str] = field(default_factory=list)


def build_dsp05_chain(
    *,
    config_mapping: Mapping[str, object] | None,
    feed_volume_m3: Optional[float],
    feed_opn_conc_gL: Optional[float],
    feed_moisture_wt_pct: Optional[float],
    feed_solids_wt_pct: Optional[float],
    plan_product_mass_kg: Optional[float],
    plan_product_volume_m3: Optional[float],
) -> FinalProductHandoff:
    config = DSP05Config.from_mapping(config_mapping)
    method = config.method

    product_mass_kg = plan_product_mass_kg
    product_volume_m3 = plan_product_volume_m3
    product_form = "powder" if method is not DSP05Method.LIQUID_BULK else "liquid"
    moisture = None
    protein_conc = None
    bulk_density = None
    recovery = 1.0
    notes: list[str] = []

    if method is DSP05Method.SPRAY_DRY:
        moisture = config.spraydry.target_moisture_wt_pct
        bulk_density = config.spraydry.bulk_density_kg_m3
        if plan_product_mass_kg is not None:
            recovery = config.spraydry.dryer_yield_frac
    elif method is DSP05Method.LYOPHILIZE:
        moisture = config.lyophilize.target_moisture_wt_pct
        if plan_product_mass_kg is not None:
            recovery = config.lyophilize.lyo_yield_frac
    elif method is DSP05Method.LIQUID_BULK:
        protein_conc = config.liquid.target_conc_g_per_l
        product_form = "liquid"

    client_cost = (
        config.toll_fee_usd_per_m3_feed * (feed_volume_m3 or 0.0)
        + config.utilities_usd_per_batch
        + config.consumables_usd_per_batch
        + config.labor_h_per_batch * config.labor_rate_usd_per_h
    )

    capex_flagged = config.dryer_capex_usd * config.install_factor if config.dryer_capex_usd else None

    return FinalProductHandoff(
        method=method,
        product_form=product_form,
        product_mass_kg=product_mass_kg,
        product_volume_m3=product_volume_m3,
        protein_concentration_g_per_l=protein_conc,
        moisture_wt_pct=moisture,
        bulk_density_kg_m3=bulk_density,
        step_recovery_fraction=recovery,
        cycle_time_h=None,
        client_cost_usd=client_cost,
        capex_flagged_usd=capex_flagged,
        notes=notes,
    )

