"""Capture module helpers supporting DSP02 AEX and chitosan routes."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Mapping, Optional, Tuple

import biosteam as bst

from .excel_defaults import ModuleKey
from .module_builders import ModuleData
from .simple_units import PlanBackedUnit
from .unit_builders import UnitPlan

__all__ = [
    "CaptureRoute",
    "CaptureFeedSpecs",
    "AEXChromatographySpecs",
    "ChitosanCoacervateSpecs",
    "CaptureTargets",
    "CaptureConfig",
    "CaptureHandoff",
    "CaptureChain",
    "build_capture_chain",
    "AEXCaptureUnit",
    "ChitosanCaptureUnit",
]


class CaptureRoute(str, Enum):
    """Capture configuration options available for DSP02."""

    AEX = "aex"
    CHITOSAN = "chitosan"
    AUTO = "auto"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "CaptureRoute":
        if isinstance(value, cls):
            return value
        normalized = (value or cls.AUTO.value).strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.AUTO


@dataclass
class CaptureFeedSpecs:
    """Feed properties relevant to capture route sizing and checks."""

    volume_m3: Optional[float] = None
    density_kg_per_m3: Optional[float] = None
    protein_concentration_g_per_l: Optional[float] = None
    dna_mg_per_l: Optional[float] = None
    conductivity_mM: Optional[float] = None
    ph: Optional[float] = None
    temperature_c: Optional[float] = None


@dataclass
class AEXChromatographySpecs:
    """Key design inputs for a bind-and-elute anion exchange step."""

    resin_type: Optional[str] = None
    particle_diameter_um: Optional[float] = None
    resin_cost_per_l: Optional[float] = None
    resin_life_cycles: Optional[float] = None
    bed_height_cm: Optional[float] = None
    packing_factor: Optional[float] = None
    lin_vel_cm_per_h: Optional[float] = None
    rt_load_min: Optional[float] = None
    delta_p_max_bar: Optional[float] = None
    fouling_factor_dp: Optional[float] = None

    ph_bind: Optional[float] = None
    cond_bind_mM_max: Optional[float] = None
    ph_elute: Optional[float] = None
    elute_salt_mM: Optional[float] = None
    temperature_c: Optional[float] = None

    dbc_base_mg_per_ml: Optional[float] = None
    dbc_cond_slope: Optional[float] = None
    dna_competition_coeff: Optional[float] = None
    mass_transfer_beta: Optional[float] = None
    rt_ref_min: Optional[float] = None

    target_recovery_pct: Optional[float] = None
    target_pool_cond_mM: Optional[float] = None
    uv_pooling_rule: Optional[str] = None

    utilization_fraction: Optional[float] = None
    columns_in_service: Optional[int] = None
    equilibration_bv: Optional[float] = None
    wash1_bv: Optional[float] = None
    wash2_bv: Optional[float] = None
    elution_bv: Optional[float] = None
    strip_bv: Optional[float] = None
    cip_bv: Optional[float] = None
    reequil_bv: Optional[float] = None

    resin_fee_per_l_per_cycle: Optional[float] = None
    column_rental_per_day: Optional[float] = None
    column_setup_fee_per_campaign: Optional[float] = None
    equil_fee_per_m3: Optional[float] = None
    wash_fee_per_m3: Optional[float] = None
    elute_fee_per_m3: Optional[float] = None
    strip_fee_per_m3: Optional[float] = None
    cip_fee_per_m3: Optional[float] = None
    reequil_fee_per_m3: Optional[float] = None
    ops_labor_h_per_cycle: Optional[float] = None
    blended_rate_per_h: Optional[float] = None
    disposables_per_cycle: Optional[float] = None
    overhead_per_cycle: Optional[float] = None


@dataclass
class ChitosanCoacervateSpecs:
    """Design and economic parameters for the chitosan coacervate capture route."""

    ph_bind: Optional[float] = None
    ionic_strength_mM: Optional[float] = None
    temperature_c: Optional[float] = None
    charge_ratio: Optional[float] = None
    chitosan_concentration_g_per_l: Optional[float] = None
    chitosan_cost_per_kg: Optional[float] = None
    degree_deacetylation_pct: Optional[float] = None
    molecular_weight_class: Optional[str] = None
    hold_time_min: Optional[float] = None

    capture_yield_fraction: Optional[float] = None
    dna_removal_log: Optional[float] = None
    hcp_removal_log: Optional[float] = None
    floc_solids_fraction: Optional[float] = None

    separation_method: Optional[str] = None
    separator_sigma_m2: Optional[float] = None
    separator_power_kwh_per_m3: Optional[float] = None

    wash_enabled: Optional[bool] = None
    wash_ratio_bv: Optional[float] = None
    wash_loss_fraction: Optional[float] = None

    elution_mode: Optional[str] = None
    polyphosphate_mM: Optional[float] = None
    elution_ph: Optional[float] = None
    elution_conductivity_mM: Optional[float] = None
    elution_yield_fraction: Optional[float] = None
    eluate_volume_l: Optional[float] = None

    post_elution_filter_flux_lmh: Optional[float] = None
    post_elution_filter_area_m2: Optional[float] = None

    polymer_recovery_fraction: Optional[float] = None
    polymer_bleed_fraction: Optional[float] = None
    polymer_makeup_cost_per_kg: Optional[float] = None
    acid_cost_per_kg: Optional[float] = None
    base_cost_per_kg: Optional[float] = None
    polyphosphate_cost_per_kg: Optional[float] = None

    recycle_efficiency: Optional[float] = None


@dataclass
class CaptureTargets:
    """Handoff targets used to trigger downstream conditioning/polish."""

    polish_conductivity_mM: Optional[float] = None
    chitosan_ppm_max: Optional[float] = None


@dataclass
class CaptureConfig:
    """Serialized capture configuration from baseline overrides."""

    method: CaptureRoute = CaptureRoute.AUTO
    feed: CaptureFeedSpecs = field(default_factory=CaptureFeedSpecs)
    aex: AEXChromatographySpecs = field(default_factory=AEXChromatographySpecs)
    chitosan: ChitosanCoacervateSpecs = field(default_factory=ChitosanCoacervateSpecs)
    ownership_mode: Optional[str] = None
    include_capex: Optional[bool] = None
    targets: "CaptureTargets" | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "CaptureConfig":
        method = CaptureRoute.from_string(data.get("method")) if isinstance(data, Mapping) else CaptureRoute.AUTO

        def _as_float(value: object | None) -> Optional[float]:
            try:
                if value is None:
                    return None
                return float(value)
            except (TypeError, ValueError):
                return None

        def _as_bool(value: object | None) -> Optional[bool]:
            if isinstance(value, bool):
                return value
            if value is None:
                return None
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "yes", "1"}:
                    return True
                if normalized in {"false", "no", "0"}:
                    return False
            try:
                return bool(int(value))
            except (TypeError, ValueError):
                return None
            return None

        feed_cfg = data.get("feed") if isinstance(data, Mapping) else {}
        feed = CaptureFeedSpecs(
            volume_m3=_as_float(feed_cfg.get("volume_m3")) if isinstance(feed_cfg, Mapping) else None,
            density_kg_per_m3=_as_float(feed_cfg.get("density_kg_per_m3")) if isinstance(feed_cfg, Mapping) else None,
            protein_concentration_g_per_l=_as_float(feed_cfg.get("protein_concentration_g_per_l")) if isinstance(feed_cfg, Mapping) else None,
            dna_mg_per_l=_as_float(feed_cfg.get("dna_mg_per_l")) if isinstance(feed_cfg, Mapping) else None,
            conductivity_mM=_as_float(feed_cfg.get("conductivity_mM")) if isinstance(feed_cfg, Mapping) else None,
            ph=_as_float(feed_cfg.get("ph")) if isinstance(feed_cfg, Mapping) else None,
            temperature_c=_as_float(feed_cfg.get("temperature_c")) if isinstance(feed_cfg, Mapping) else None,
        )

        aex_cfg = data.get("aex") if isinstance(data, Mapping) else {}
        aex = AEXChromatographySpecs(
            resin_type=aex_cfg.get("resin_type") if isinstance(aex_cfg, Mapping) else None,
            particle_diameter_um=_as_float(aex_cfg.get("particle_diameter_um")) if isinstance(aex_cfg, Mapping) else None,
            resin_cost_per_l=_as_float(aex_cfg.get("resin_cost_per_l")) if isinstance(aex_cfg, Mapping) else None,
            resin_life_cycles=_as_float(aex_cfg.get("resin_life_cycles")) if isinstance(aex_cfg, Mapping) else None,
            bed_height_cm=_as_float(aex_cfg.get("bed_height_cm")) if isinstance(aex_cfg, Mapping) else None,
            packing_factor=_as_float(aex_cfg.get("packing_factor")) if isinstance(aex_cfg, Mapping) else None,
            lin_vel_cm_per_h=_as_float(aex_cfg.get("lin_vel_cm_per_h")) if isinstance(aex_cfg, Mapping) else None,
            rt_load_min=_as_float(aex_cfg.get("rt_load_min")) if isinstance(aex_cfg, Mapping) else None,
            delta_p_max_bar=_as_float(aex_cfg.get("delta_p_max_bar")) if isinstance(aex_cfg, Mapping) else None,
            fouling_factor_dp=_as_float(aex_cfg.get("fouling_factor_dp")) if isinstance(aex_cfg, Mapping) else None,
            ph_bind=_as_float(aex_cfg.get("ph_bind")) if isinstance(aex_cfg, Mapping) else None,
            cond_bind_mM_max=_as_float(aex_cfg.get("cond_bind_mM_max")) if isinstance(aex_cfg, Mapping) else None,
            ph_elute=_as_float(aex_cfg.get("ph_elute")) if isinstance(aex_cfg, Mapping) else None,
            elute_salt_mM=_as_float(aex_cfg.get("elute_salt_mM")) if isinstance(aex_cfg, Mapping) else None,
            temperature_c=_as_float(aex_cfg.get("temperature_c")) if isinstance(aex_cfg, Mapping) else None,
            dbc_base_mg_per_ml=_as_float(aex_cfg.get("dbc_base_mg_per_ml")) if isinstance(aex_cfg, Mapping) else None,
            dbc_cond_slope=_as_float(aex_cfg.get("dbc_cond_slope")) if isinstance(aex_cfg, Mapping) else None,
            dna_competition_coeff=_as_float(aex_cfg.get("dna_competition_coeff")) if isinstance(aex_cfg, Mapping) else None,
            mass_transfer_beta=_as_float(aex_cfg.get("mass_transfer_beta")) if isinstance(aex_cfg, Mapping) else None,
            rt_ref_min=_as_float(aex_cfg.get("rt_ref_min")) if isinstance(aex_cfg, Mapping) else None,
            target_recovery_pct=_as_float(aex_cfg.get("target_recovery_pct")) if isinstance(aex_cfg, Mapping) else None,
            target_pool_cond_mM=_as_float(aex_cfg.get("target_pool_cond_mM")) if isinstance(aex_cfg, Mapping) else None,
            uv_pooling_rule=aex_cfg.get("uv_pooling_rule") if isinstance(aex_cfg, Mapping) else None,
            utilization_fraction=_as_float(aex_cfg.get("utilization_fraction")) if isinstance(aex_cfg, Mapping) else None,
            columns_in_service=int(aex_cfg.get("columns_in_service")) if isinstance(aex_cfg, Mapping) and aex_cfg.get("columns_in_service") is not None else None,
            equilibration_bv=_as_float(aex_cfg.get("equilibration_bv")) if isinstance(aex_cfg, Mapping) else None,
            wash1_bv=_as_float(aex_cfg.get("wash1_bv")) if isinstance(aex_cfg, Mapping) else None,
            wash2_bv=_as_float(aex_cfg.get("wash2_bv")) if isinstance(aex_cfg, Mapping) else None,
            elution_bv=_as_float(aex_cfg.get("elution_bv")) if isinstance(aex_cfg, Mapping) else None,
            strip_bv=_as_float(aex_cfg.get("strip_bv")) if isinstance(aex_cfg, Mapping) else None,
            cip_bv=_as_float(aex_cfg.get("cip_bv")) if isinstance(aex_cfg, Mapping) else None,
            reequil_bv=_as_float(aex_cfg.get("reequil_bv")) if isinstance(aex_cfg, Mapping) else None,
            resin_fee_per_l_per_cycle=_as_float(aex_cfg.get("resin_fee_per_l_per_cycle")) if isinstance(aex_cfg, Mapping) else None,
            column_rental_per_day=_as_float(aex_cfg.get("column_rental_per_day")) if isinstance(aex_cfg, Mapping) else None,
            column_setup_fee_per_campaign=_as_float(aex_cfg.get("column_setup_fee_per_campaign")) if isinstance(aex_cfg, Mapping) else None,
            equil_fee_per_m3=_as_float(aex_cfg.get("equil_fee_per_m3")) if isinstance(aex_cfg, Mapping) else None,
            wash_fee_per_m3=_as_float(aex_cfg.get("wash_fee_per_m3")) if isinstance(aex_cfg, Mapping) else None,
            elute_fee_per_m3=_as_float(aex_cfg.get("elute_fee_per_m3")) if isinstance(aex_cfg, Mapping) else None,
            strip_fee_per_m3=_as_float(aex_cfg.get("strip_fee_per_m3")) if isinstance(aex_cfg, Mapping) else None,
            cip_fee_per_m3=_as_float(aex_cfg.get("cip_fee_per_m3")) if isinstance(aex_cfg, Mapping) else None,
            reequil_fee_per_m3=_as_float(aex_cfg.get("reequil_fee_per_m3")) if isinstance(aex_cfg, Mapping) else None,
            ops_labor_h_per_cycle=_as_float(aex_cfg.get("ops_labor_h_per_cycle")) if isinstance(aex_cfg, Mapping) else None,
            blended_rate_per_h=_as_float(aex_cfg.get("blended_rate_per_h")) if isinstance(aex_cfg, Mapping) else None,
            disposables_per_cycle=_as_float(aex_cfg.get("disposables_per_cycle")) if isinstance(aex_cfg, Mapping) else None,
            overhead_per_cycle=_as_float(aex_cfg.get("overhead_per_cycle")) if isinstance(aex_cfg, Mapping) else None,
        )

        chito_cfg = data.get("chitosan") if isinstance(data, Mapping) else {}
        chitosan = ChitosanCoacervateSpecs(
            ph_bind=_as_float(chito_cfg.get("ph_bind")) if isinstance(chito_cfg, Mapping) else None,
            ionic_strength_mM=_as_float(chito_cfg.get("ionic_strength_mM")) if isinstance(chito_cfg, Mapping) else None,
            temperature_c=_as_float(chito_cfg.get("temperature_c")) if isinstance(chito_cfg, Mapping) else None,
            charge_ratio=_as_float(chito_cfg.get("charge_ratio")) if isinstance(chito_cfg, Mapping) else None,
            chitosan_concentration_g_per_l=_as_float(chito_cfg.get("chitosan_concentration_g_per_l")) if isinstance(chito_cfg, Mapping) else None,
            chitosan_cost_per_kg=_as_float(chito_cfg.get("chitosan_cost_per_kg")) if isinstance(chito_cfg, Mapping) else None,
            degree_deacetylation_pct=_as_float(chito_cfg.get("degree_deacetylation_pct")) if isinstance(chito_cfg, Mapping) else None,
            molecular_weight_class=chito_cfg.get("molecular_weight_class") if isinstance(chito_cfg, Mapping) else None,
            hold_time_min=_as_float(chito_cfg.get("hold_time_min")) if isinstance(chito_cfg, Mapping) else None,
            capture_yield_fraction=_as_float(chito_cfg.get("capture_yield_fraction")) if isinstance(chito_cfg, Mapping) else None,
            dna_removal_log=_as_float(chito_cfg.get("dna_removal_log")) if isinstance(chito_cfg, Mapping) else None,
            hcp_removal_log=_as_float(chito_cfg.get("hcp_removal_log")) if isinstance(chito_cfg, Mapping) else None,
            floc_solids_fraction=_as_float(chito_cfg.get("floc_solids_fraction")) if isinstance(chito_cfg, Mapping) else None,
            separation_method=chito_cfg.get("separation_method") if isinstance(chito_cfg, Mapping) else None,
            separator_sigma_m2=_as_float(chito_cfg.get("separator_sigma_m2")) if isinstance(chito_cfg, Mapping) else None,
            separator_power_kwh_per_m3=_as_float(chito_cfg.get("separator_power_kwh_per_m3")) if isinstance(chito_cfg, Mapping) else None,
            wash_enabled=_as_bool(chito_cfg.get("wash_enabled")) if isinstance(chito_cfg, Mapping) else None,
            wash_ratio_bv=_as_float(chito_cfg.get("wash_ratio_bv")) if isinstance(chito_cfg, Mapping) else None,
            wash_loss_fraction=_as_float(chito_cfg.get("wash_loss_fraction")) if isinstance(chito_cfg, Mapping) else None,
            elution_mode=chito_cfg.get("elution_mode") if isinstance(chito_cfg, Mapping) else None,
            polyphosphate_mM=_as_float(chito_cfg.get("polyphosphate_mM")) if isinstance(chito_cfg, Mapping) else None,
            elution_ph=_as_float(chito_cfg.get("elution_ph")) if isinstance(chito_cfg, Mapping) else None,
            elution_conductivity_mM=_as_float(chito_cfg.get("elution_conductivity_mM")) if isinstance(chito_cfg, Mapping) else None,
            elution_yield_fraction=_as_float(chito_cfg.get("elution_yield_fraction")) if isinstance(chito_cfg, Mapping) else None,
            eluate_volume_l=_as_float(chito_cfg.get("eluate_volume_l")) if isinstance(chito_cfg, Mapping) else None,
            post_elution_filter_flux_lmh=_as_float(chito_cfg.get("post_elution_filter_flux_lmh")) if isinstance(chito_cfg, Mapping) else None,
            post_elution_filter_area_m2=_as_float(chito_cfg.get("post_elution_filter_area_m2")) if isinstance(chito_cfg, Mapping) else None,
            polymer_recovery_fraction=_as_float(chito_cfg.get("polymer_recovery_fraction")) if isinstance(chito_cfg, Mapping) else None,
            polymer_bleed_fraction=_as_float(chito_cfg.get("polymer_bleed_fraction")) if isinstance(chito_cfg, Mapping) else None,
            polymer_makeup_cost_per_kg=_as_float(chito_cfg.get("polymer_makeup_cost_per_kg")) if isinstance(chito_cfg, Mapping) else None,
            acid_cost_per_kg=_as_float(chito_cfg.get("acid_cost_per_kg")) if isinstance(chito_cfg, Mapping) else None,
            base_cost_per_kg=_as_float(chito_cfg.get("base_cost_per_kg")) if isinstance(chito_cfg, Mapping) else None,
            polyphosphate_cost_per_kg=_as_float(chito_cfg.get("polyphosphate_cost_per_kg")) if isinstance(chito_cfg, Mapping) else None,
            recycle_efficiency=_as_float(chito_cfg.get("recycle_efficiency")) if isinstance(chito_cfg, Mapping) else None,
        )

        targets_cfg = data.get("targets") if isinstance(data, Mapping) else {}
        targets = None
        if isinstance(targets_cfg, Mapping) and targets_cfg:
            targets = CaptureTargets(
                polish_conductivity_mM=_as_float(targets_cfg.get("polish_conductivity_mM")),
                chitosan_ppm_max=_as_float(targets_cfg.get("chitosan_ppm_max")),
            )

        return cls(
            method=method,
            feed=feed,
            aex=aex,
            chitosan=chitosan,
            ownership_mode=data.get("ownership_mode") if isinstance(data, Mapping) else None,
            include_capex=_as_bool(data.get("include_capex")) if isinstance(data, Mapping) else None,
            targets=targets,
        )


def _make_plan(spec_key: str, specs: object) -> UnitPlan:
    """Create a :class:`UnitPlan` wrapper for ad-hoc capture specs."""

    data = ModuleData(
        key=ModuleKey(module="DSP02", option=spec_key),
        records={},
        values={},
        field_map={},
    )
    return UnitPlan(key=data.key, data=data, specs=specs, derived={})


def _safe_float(value: Optional[float], default: float = 0.0) -> float:
    try:
        if value is None:
            raise TypeError
        result = float(value)
    except (TypeError, ValueError):
        result = default
    return result


def _safe_fraction(value: Optional[float], default: float = 0.0) -> float:
    result = _safe_float(value, default)
    return min(max(result, 0.0), 1.0)


def _safe_positive(value: Optional[float], default: float = 0.0) -> float:
    result = _safe_float(value, default)
    return result if result >= 0.0 else default


def _safe_int(value: object | None) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass
class CaptureHandoff:
    """Canonical DSP02 outputs consumed by downstream polishing stages."""

    route: CaptureRoute
    pool_volume_l: Optional[float]
    opn_concentration_g_per_l: Optional[float]
    conductivity_mM: Optional[float]
    ph: Optional[float]
    dna_mg_per_l: Optional[float]
    chitosan_ppm: Optional[float]
    polyp_mM: Optional[float]
    step_recovery_fraction: Optional[float]
    needs_df: bool
    needs_fines_polish: bool
    cycle_time_h: Optional[float]
    cost_per_batch: Optional[float]
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data['route'] = self.route.value if self.route else None
        return data


@dataclass
class CaptureChain:
    """Description of the instantiated capture module configuration."""

    route: CaptureRoute
    units: List[bst.Unit]
    product_out_kg: Optional[float]
    pool_volume_l: Optional[float]
    pool_conductivity_mM: Optional[float] = None
    pool_ph: Optional[float] = None
    cdmo_cost_per_batch: Optional[float] = None
    resin_cost_per_batch: Optional[float] = None
    buffer_cost_per_batch: Optional[float] = None
    notes: List[str] = field(default_factory=list)
    handoff: Optional[CaptureHandoff] = None


class AEXCaptureUnit(PlanBackedUnit):
    """Plan-backed bind-and-elute capture step."""

    _N_ins = 1
    _N_outs = 2
    line = "AEX Capture"

    _units = {
        "Effective DBC": "mg/mL",
        "Resin volume": "L",
        "Bed volume": "L",
        "Total buffer": "BV",
        "Resin cost per batch": "USD",
        "Buffer cost per batch": "USD",
        "CDMO cost per batch": "USD",
        "Pool volume": "L",
        "Pool conductivity": "mM",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product_stream, waste_stream = self.outs
        derived = self.plan.derived

        product_stream.empty()
        waste_stream.empty()

        product_mass = derived.get("product_out_kg")
        if product_mass is None:
            product_mass = float(feed.imass.get("Osteopontin", 0.0))
        product_mass = max(product_mass or 0.0, 0.0)

        pool_volume_l = derived.get("pool_volume_l")
        density = derived.get("density_kg_per_l") or 1.0
        if pool_volume_l is not None:
            product_total_mass = pool_volume_l * density
        else:
            product_total_mass = product_mass

        product_stream.imass['Osteopontin'] = product_mass
        product_stream.imass['Water'] = max(product_total_mass - product_mass, 0.0)

        input_product = derived.get("input_product_kg")
        if input_product is None:
            input_product = float(feed.imass.get("Osteopontin", 0.0))
        waste_product = max((input_product or 0.0) - product_mass, 0.0)
        if waste_product:
            waste_stream.imass['Osteopontin'] = waste_product

        eluate_volume_l = derived.get("eluate_volume_l") or pool_volume_l
        if eluate_volume_l is not None:
            waste_total_mass = max(eluate_volume_l * density - product_total_mass, 0.0)
        else:
            waste_total_mass = 0.0
        if waste_total_mass > 0.0:
            waste_stream.imass['Water'] += waste_total_mass

        product_stream.T = feed.T
        product_stream.P = feed.P
        waste_stream.T = feed.T
        waste_stream.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        self.design_results.update(
            {
                "Effective DBC": derived.get("dbc_effective_mg_per_ml", 0.0),
                "Resin volume": derived.get("resin_volume_l", 0.0),
                "Bed volume": derived.get("bed_volume_l", 0.0),
                "Total buffer": derived.get("total_buffer_bv", 0.0),
                "Pool volume": derived.get("pool_volume_l", 0.0),
                "Pool conductivity": derived.get("pool_conductivity_mM", 0.0),
            }
        )
        if derived.get("resin_cost_per_batch") is not None:
            self.design_results['Resin cost per batch'] = derived['resin_cost_per_batch']
        if derived.get("buffer_cost_per_batch") is not None:
            self.design_results['Buffer cost per batch'] = derived['buffer_cost_per_batch']
        if derived.get("cdmo_cost_per_batch") is not None:
            self.design_results['CDMO cost per batch'] = derived['cdmo_cost_per_batch']

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
        resin_cost = self.plan.derived.get("resin_cost_per_batch") or 0.0
        buffer_cost = self.plan.derived.get("buffer_cost_per_batch") or 0.0
        cdmo_cost = self.plan.derived.get("cdmo_cost_per_batch") or 0.0
        self.operating_cost = resin_cost + buffer_cost + cdmo_cost
        self.material_costs = {}
        if resin_cost:
            self.material_costs['Resin'] = resin_cost
        if buffer_cost:
            self.material_costs['Buffers'] = buffer_cost
        if cdmo_cost:
            self.material_costs['CDMO fees'] = cdmo_cost


class ChitosanCaptureUnit(PlanBackedUnit):
    """Plan-backed chitosan coacervate capture aggregate."""

    _N_ins = 1
    _N_outs = 2
    line = "Chitosan Capture"

    _units = {
        "Capture yield": "fraction",
        "Elution yield": "fraction",
        "Pool volume": "L",
        "Polymer cost per batch": "USD",
        "Reagent cost per batch": "USD",
    }

    def _run(self) -> None:
        feed = self.ins[0]
        product_stream, waste_stream = self.outs
        derived = self.plan.derived

        product_stream.empty()
        waste_stream.empty()

        product_mass = derived.get("product_out_kg")
        if product_mass is None:
            product_mass = float(feed.imass.get("Osteopontin", 0.0))
        product_mass = max(product_mass or 0.0, 0.0)

        pool_volume_l = derived.get("pool_volume_l")
        density = derived.get("density_kg_per_l") or 1.0
        if pool_volume_l is not None:
            product_total_mass = pool_volume_l * density
        else:
            product_total_mass = product_mass

        product_stream.imass['Osteopontin'] = product_mass
        product_stream.imass['Water'] = max(product_total_mass - product_mass, 0.0)

        input_product = derived.get("input_product_kg")
        if input_product is None:
            input_product = float(feed.imass.get("Osteopontin", 0.0))
        waste_product = max((input_product or 0.0) - product_mass, 0.0)
        if waste_product:
            waste_stream.imass['Osteopontin'] = waste_product

        eluate_volume_l = derived.get("eluate_volume_l") or pool_volume_l
        if eluate_volume_l is not None:
            waste_total_mass = max(eluate_volume_l * density - product_total_mass, 0.0)
        else:
            waste_total_mass = 0.0
        if waste_total_mass > 0.0:
            waste_stream.imass['Water'] += waste_total_mass

        product_stream.T = feed.T
        product_stream.P = feed.P
        waste_stream.T = feed.T
        waste_stream.P = feed.P

    def _design(self) -> None:
        derived = self.plan.derived
        for key in (
            "capture_yield_fraction",
            "elution_yield_fraction",
            "pool_volume_l",
        ):
            if derived.get(key) is not None:
                self.design_results[key.replace('_', ' ').title()] = derived[key]
        if derived.get("polymer_cost_per_batch") is not None:
            self.design_results['Polymer cost per batch'] = derived['polymer_cost_per_batch']
        if derived.get("reagent_cost_per_batch") is not None:
            self.design_results['Reagent cost per batch'] = derived['reagent_cost_per_batch']

    def _cost(self) -> None:
        self.baseline_purchase_costs.clear()
        self.installed_costs.clear()
        polymer_cost = self.plan.derived.get("polymer_cost_per_batch") or 0.0
        reagent_cost = self.plan.derived.get("reagent_cost_per_batch") or 0.0
        utilities = self.plan.derived.get("utilities_cost_per_batch") or 0.0
        self.operating_cost = polymer_cost + reagent_cost + utilities
        self.material_costs = {}
        if polymer_cost:
            self.material_costs['Chitosan polymer'] = polymer_cost
        if reagent_cost:
            self.material_costs['Reagents'] = reagent_cost
        if utilities:
            self.material_costs['Utilities'] = utilities


def _select_route(
    requested: Optional[str],
    config: CaptureConfig,
    *,
    feed_conductivity_mM: Optional[float],
    feed_volume_l: Optional[float],
) -> Tuple[CaptureRoute, List[str]]:
    """Determine capture route based on overrides and guardrails."""

    notes: List[str] = []
    requested_route = CaptureRoute.from_string(requested)
    if requested_route is not CaptureRoute.AUTO:
        return requested_route, notes

    bind_max = config.aex.cond_bind_mM_max
    if feed_conductivity_mM is not None and bind_max is not None:
        if feed_conductivity_mM > bind_max * 1.15:
            notes.append(
                "Feed conductivity exceeds AEX bind spec; auto-switching to chitosan route."
            )
            return CaptureRoute.CHITOSAN, notes

    if config.method is CaptureRoute.CHITOSAN:
        return CaptureRoute.CHITOSAN, notes
    if config.method is CaptureRoute.AEX:
        return CaptureRoute.AEX, notes

    if config.chitosan.capture_yield_fraction is None:
        notes.append("Chitosan capture yields undefined; defaulting to AEX.")
        return CaptureRoute.AEX, notes

    if feed_volume_l is not None and feed_volume_l >= 80_000:
        notes.append("High volumetric throughput; preferring chitosan route for surge buffering.")
        return CaptureRoute.CHITOSAN, notes

    return CaptureRoute.AEX, notes


def _build_aex_unit(
    config: CaptureConfig,
    concentration_plan: UnitPlan,
) -> Tuple[AEXCaptureUnit, Dict[str, float], List[str], CaptureHandoff]:
    notes: List[str] = []

    feed_product_input_kg = concentration_plan.derived.get("product_out_kg")
    if feed_product_input_kg is None:
        feed_product_input_kg = concentration_plan.derived.get("input_product_kg")
    feed_product_kg = feed_product_input_kg
    feed_volume_l = concentration_plan.derived.get("output_volume_l")
    if feed_volume_l is None:
        feed_volume_l = concentration_plan.derived.get("eluate_volume_l")
    if feed_volume_l is None:
        feed_volume_l = concentration_plan.derived.get("input_volume_l")

    density_kg_per_l = None
    if config.feed.density_kg_per_m3 is not None:
        density_kg_per_l = config.feed.density_kg_per_m3 / 1000.0
    if density_kg_per_l is None:
        density_kg_per_l = concentration_plan.derived.get("broth_density_kg_per_l")
    if density_kg_per_l is None:
        density_kg_per_l = 1.0

    protein_conc_g_per_l = config.feed.protein_concentration_g_per_l
    if protein_conc_g_per_l is None and feed_product_kg is not None and feed_volume_l:
        try:
            protein_conc_g_per_l = (feed_product_kg * 1000.0) / feed_volume_l
        except ZeroDivisionError:
            protein_conc_g_per_l = None

    feed_conductivity = config.feed.conductivity_mM
    feed_dna = config.feed.dna_mg_per_l

    specs = config.aex
    dbc_base = _safe_positive(specs.dbc_base_mg_per_ml, 35.0)
    dbc_eff = dbc_base
    cond_slope = specs.dbc_cond_slope
    cond_ref = specs.cond_bind_mM_max
    if cond_slope is not None and feed_conductivity is not None and cond_ref is not None:
        delta = feed_conductivity - cond_ref
        if delta > 0:
            dbc_eff = max(dbc_base + cond_slope * delta, 0.0)
        else:
            dbc_eff = dbc_base

    dna_coeff = specs.dna_competition_coeff
    if dna_coeff is not None and feed_dna:
        dbc_eff *= max(1.0 - dna_coeff * feed_dna, 0.1)

    if specs.mass_transfer_beta is not None and specs.rt_ref_min and specs.rt_load_min:
        rt_ratio = min(specs.rt_load_min / specs.rt_ref_min, 1.0)
        dbc_eff *= rt_ratio ** specs.mass_transfer_beta

    utilization = _safe_fraction(specs.utilization_fraction, 0.9)
    if specs.target_recovery_pct is not None:
        target_recovery = _safe_fraction(specs.target_recovery_pct / 100.0, utilization)
    else:
        target_recovery = utilization

    if feed_product_kg is None or feed_product_kg <= 0:
        notes.append("Feed product mass missing; assuming zero for capture sizing.")
        feed_product_kg = 0.0

    valid_feed_mass = feed_product_input_kg if feed_product_input_kg and feed_product_input_kg > 0 else None

    product_mass_g = feed_product_kg * 1000.0
    resin_volume_l = 0.0
    if dbc_eff > 0.0 and utilization > 0.0:
        resin_volume_l = product_mass_g / (dbc_eff * utilization)
    resin_volume_l = max(resin_volume_l, 0.0)

    columns = specs.columns_in_service or 1
    if columns > 0:
        resin_per_column = resin_volume_l / columns
    else:
        resin_per_column = resin_volume_l
        columns = 1

    packing_factor = _safe_fraction(specs.packing_factor, 0.72)
    bed_volume_l = resin_volume_l / packing_factor if packing_factor > 0 else resin_volume_l

    equil_bv = _safe_positive(specs.equilibration_bv, 3.0)
    wash1_bv = _safe_positive(specs.wash1_bv, 2.0)
    wash2_bv = _safe_positive(specs.wash2_bv, 0.0)
    elution_bv = _safe_positive(specs.elution_bv, 4.0)
    strip_bv = _safe_positive(specs.strip_bv, 1.0)
    cip_bv = _safe_positive(specs.cip_bv, 1.0)
    reequil_bv = _safe_positive(specs.reequil_bv, 2.0)
    total_buffer_bv = (
        equil_bv + wash1_bv + wash2_bv + elution_bv + strip_bv + cip_bv + reequil_bv
    )

    buffer_volumes_l: Dict[str, float] = {
        "equilibration": bed_volume_l * equil_bv,
        "wash1": bed_volume_l * wash1_bv,
        "wash2": bed_volume_l * wash2_bv,
        "elution": bed_volume_l * elution_bv,
        "strip": bed_volume_l * strip_bv,
        "cip": bed_volume_l * cip_bv,
        "reequil": bed_volume_l * reequil_bv,
    }

    pool_volume_l = buffer_volumes_l["elution"]
    eluate_volume_l = pool_volume_l
    if specs.target_pool_cond_mM is not None and specs.elute_salt_mM and specs.elute_salt_mM > specs.target_pool_cond_mM:
        notes.append("Elution salt exceeds downstream target; expect DF request post-DSP02.")

    product_out_kg = feed_product_kg * target_recovery
    pool_conductivity = specs.elute_salt_mM or config.feed.conductivity_mM
    pool_ph = specs.ph_elute or config.feed.ph

    resin_cost_per_batch = None
    if specs.resin_cost_per_l is not None and specs.resin_life_cycles:
        resin_cost_per_batch = (
            specs.resin_cost_per_l * resin_volume_l / max(specs.resin_life_cycles, 1.0)
        )

    buffer_cost = 0.0
    fee_map = {
        "equilibration": specs.equil_fee_per_m3,
        "wash1": specs.wash_fee_per_m3,
        "wash2": specs.wash_fee_per_m3,
        "elution": specs.elute_fee_per_m3,
        "strip": specs.strip_fee_per_m3,
        "cip": specs.cip_fee_per_m3,
        "reequil": specs.reequil_fee_per_m3,
    }
    for step, volume_l in buffer_volumes_l.items():
        fee = fee_map.get(step)
        if fee is None:
            continue
        buffer_cost += fee * (volume_l / 1000.0)

    cdmo_cost = 0.0
    if specs.resin_fee_per_l_per_cycle is not None:
        cdmo_cost += specs.resin_fee_per_l_per_cycle * resin_volume_l
    if specs.ops_labor_h_per_cycle is not None and specs.blended_rate_per_h is not None:
        cdmo_cost += specs.ops_labor_h_per_cycle * specs.blended_rate_per_h
    if specs.disposables_per_cycle is not None:
        cdmo_cost += specs.disposables_per_cycle
    if specs.overhead_per_cycle is not None:
        cdmo_cost += specs.overhead_per_cycle

    derived = {
        "input_product_kg": feed_product_kg,
        "product_out_kg": product_out_kg,
        "density_kg_per_l": density_kg_per_l,
        "pool_volume_l": pool_volume_l,
        "eluate_volume_l": eluate_volume_l,
        "pool_conductivity_mM": pool_conductivity,
        "pool_ph": pool_ph,
        "dbc_effective_mg_per_ml": dbc_eff,
        "resin_volume_l": resin_volume_l,
        "bed_volume_l": bed_volume_l,
        "columns_in_service": columns,
        "resin_per_column_l": resin_per_column,
        "total_buffer_bv": total_buffer_bv,
        "buffer_cost_per_batch": buffer_cost if buffer_cost else None,
        "resin_cost_per_batch": resin_cost_per_batch,
        "cdmo_cost_per_batch": cdmo_cost if cdmo_cost else None,
        "input_volume_l": feed_volume_l,
        "utilization_fraction": utilization,
        "target_recovery_fraction": target_recovery,
        "buffer_volumes_l": buffer_volumes_l,
    }

    if feed_conductivity is not None and cond_ref is not None and feed_conductivity > cond_ref:
        notes.append(
            f"Feed conductivity ({feed_conductivity:.0f} mM) exceeds bind max ({cond_ref:.0f} mM)."
        )

    plan = _make_plan("DSP02_AEX", specs)
    plan.derived.update(derived)

    unit = AEXCaptureUnit("DSP02_AEX", plan=plan)

    target_cond = specs.target_pool_cond_mM
    if target_cond is None and config.targets and config.targets.polish_conductivity_mM is not None:
        target_cond = config.targets.polish_conductivity_mM

    needs_df = False
    if target_cond is not None and pool_conductivity is not None:
        needs_df = pool_conductivity > target_cond

    step_recovery = None
    if valid_feed_mass:
        try:
            step_recovery = product_out_kg / valid_feed_mass
        except ZeroDivisionError:
            step_recovery = None

    opn_conc = None
    if pool_volume_l:
        try:
            opn_conc = (product_out_kg * 1_000.0) / pool_volume_l
        except ZeroDivisionError:
            opn_conc = None

    dna_out = feed_dna

    cost_per_batch = (buffer_cost or 0.0) + (resin_cost_per_batch or 0.0) + (cdmo_cost or 0.0)

    handoff = CaptureHandoff(
        route=CaptureRoute.AEX,
        pool_volume_l=pool_volume_l,
        opn_concentration_g_per_l=opn_conc,
        conductivity_mM=pool_conductivity,
        ph=pool_ph,
        dna_mg_per_l=dna_out,
        chitosan_ppm=0.0,
        polyp_mM=0.0,
        step_recovery_fraction=step_recovery,
        needs_df=needs_df,
        needs_fines_polish=False,
        cycle_time_h=None,
        cost_per_batch=cost_per_batch,
        notes=list(notes),
    )

    return unit, derived, notes, handoff


def _build_chitosan_unit(
    config: CaptureConfig,
    concentration_plan: UnitPlan,
) -> Tuple[ChitosanCaptureUnit, Dict[str, float], List[str], CaptureHandoff]:
    notes: List[str] = []

    feed_product_input_kg = concentration_plan.derived.get("product_out_kg")
    if feed_product_input_kg is None:
        feed_product_input_kg = concentration_plan.derived.get("input_product_kg")
    feed_product_kg = feed_product_input_kg
    feed_volume_l = concentration_plan.derived.get("output_volume_l")
    if feed_volume_l is None:
        feed_volume_l = concentration_plan.derived.get("input_volume_l")

    density_kg_per_l = None
    if config.feed.density_kg_per_m3 is not None:
        density_kg_per_l = config.feed.density_kg_per_m3 / 1000.0
    if density_kg_per_l is None:
        density_kg_per_l = concentration_plan.derived.get("broth_density_kg_per_l")
    if density_kg_per_l is None:
        density_kg_per_l = 1.0

    specs = config.chitosan
    capture_yield = _safe_fraction(specs.capture_yield_fraction, 0.9)
    elution_yield = _safe_fraction(specs.elution_yield_fraction, 0.95)
    product_out_kg = (feed_product_kg or 0.0) * capture_yield * elution_yield

    pool_volume_l = specs.eluate_volume_l
    if pool_volume_l is None and feed_volume_l is not None:
        pool_volume_l = feed_volume_l * 0.25
        notes.append("Chitosan eluate volume not provided; assuming 25% of feed volume.")

    eluate_volume_l = pool_volume_l
    pool_conductivity = specs.elution_conductivity_mM
    pool_ph = specs.elution_ph

    polymer_ratio = _safe_positive(specs.charge_ratio, 2.0)
    polymer_recovery = _safe_fraction(specs.polymer_recovery_fraction, 0.85)
    polymer_bleed = _safe_fraction(specs.polymer_bleed_fraction, 0.05)

    polymer_mass_kg = (feed_product_kg or 0.0) * polymer_ratio
    net_polymer_makeup = polymer_mass_kg * (1.0 - polymer_recovery + polymer_bleed)
    polymer_cost = None
    if specs.polymer_makeup_cost_per_kg is not None:
        polymer_cost = net_polymer_makeup * specs.polymer_makeup_cost_per_kg

    reagent_cost = 0.0
    if specs.acid_cost_per_kg is not None and specs.chitosan_concentration_g_per_l is not None and pool_volume_l:
        acid_mass = (specs.chitosan_concentration_g_per_l / 1000.0) * (pool_volume_l / 1000.0)
        reagent_cost += acid_mass * specs.acid_cost_per_kg
    if specs.base_cost_per_kg is not None and pool_volume_l:
        base_mass = 0.05 * max(pool_volume_l / 1000.0, 0.0)
        reagent_cost += base_mass * specs.base_cost_per_kg
    if specs.polyphosphate_cost_per_kg is not None and specs.polyphosphate_mM is not None and pool_volume_l:
        poly_mass = specs.polyphosphate_mM * 0.001 * (pool_volume_l / 1000.0)
        reagent_cost += poly_mass * specs.polyphosphate_cost_per_kg

    utilities_cost = 0.0
    if specs.separator_power_kwh_per_m3 is not None and feed_volume_l is not None:
        utilities_cost = specs.separator_power_kwh_per_m3 * (feed_volume_l / 1000.0) * 0.1

    derived = {
        "input_product_kg": feed_product_kg,
        "product_out_kg": product_out_kg,
        "density_kg_per_l": density_kg_per_l,
        "pool_volume_l": pool_volume_l,
        "eluate_volume_l": eluate_volume_l,
        "pool_conductivity_mM": pool_conductivity,
        "pool_ph": pool_ph,
        "capture_yield_fraction": capture_yield,
        "elution_yield_fraction": elution_yield,
        "polymer_cost_per_batch": polymer_cost,
        "reagent_cost_per_batch": reagent_cost or None,
        "utilities_cost_per_batch": utilities_cost or None,
    }

    plan = _make_plan("DSP02_CHITOSAN", specs)
    plan.derived.update(derived)

    unit = ChitosanCaptureUnit("DSP02_CHITOSAN", plan=plan)
    if pool_volume_l is None:
        notes.append("Unable to infer chitosan pool volume; downstream units may need overrides.")

    target_cond = specs.elution_conductivity_mM
    if target_cond is None and config.targets and config.targets.polish_conductivity_mM is not None:
        target_cond = config.targets.polish_conductivity_mM

    polyp_mM = specs.polyphosphate_mM or 0.0

    needs_df = False
    if polyp_mM and polyp_mM > 0:
        needs_df = True
    if not needs_df and target_cond is not None and pool_conductivity is not None:
        needs_df = pool_conductivity > target_cond

    polymer_in_pool = 0.0
    if polymer_mass_kg and polymer_bleed and pool_volume_l:
        polymer_in_pool = polymer_mass_kg * polymer_bleed

    chitosan_ppm = None
    if polymer_in_pool and pool_volume_l:
        try:
            chitosan_ppm = (polymer_in_pool * 1_000_000.0) / pool_volume_l
        except ZeroDivisionError:
            chitosan_ppm = None

    needs_fines_polish = False
    threshold_ppm = None
    if config.targets and config.targets.chitosan_ppm_max is not None:
        threshold_ppm = config.targets.chitosan_ppm_max
    if threshold_ppm is not None and chitosan_ppm is not None:
        needs_fines_polish = chitosan_ppm > threshold_ppm

    dna_out = config.feed.dna_mg_per_l
    if dna_out is not None and specs.dna_removal_log is not None:
        try:
            dna_out = dna_out / (10 ** specs.dna_removal_log)
        except (TypeError, ZeroDivisionError):
            pass

    step_recovery = None
    if feed_product_input_kg and feed_product_input_kg > 0:
        try:
            step_recovery = product_out_kg / feed_product_input_kg
        except ZeroDivisionError:
            step_recovery = None

    opn_conc = None
    if pool_volume_l:
        try:
            opn_conc = (product_out_kg * 1_000.0) / pool_volume_l
        except ZeroDivisionError:
            opn_conc = None

    cost_per_batch = (polymer_cost or 0.0) + (reagent_cost or 0.0) + (utilities_cost or 0.0)

    handoff = CaptureHandoff(
        route=CaptureRoute.CHITOSAN,
        pool_volume_l=pool_volume_l,
        opn_concentration_g_per_l=opn_conc,
        conductivity_mM=pool_conductivity,
        ph=pool_ph,
        dna_mg_per_l=dna_out,
        chitosan_ppm=chitosan_ppm,
        polyp_mM=polyp_mM,
        step_recovery_fraction=step_recovery,
        needs_df=needs_df,
        needs_fines_polish=needs_fines_polish,
        cycle_time_h=None,
        cost_per_batch=cost_per_batch,
        notes=list(notes),
    )

    return unit, derived, notes, handoff


def build_capture_chain(
    *,
    method: Optional[str],
    config: Mapping[str, object],
    concentration_plan: UnitPlan,
) -> CaptureChain:
    """Instantiate capture units based on baseline configuration."""

    capture_cfg = CaptureConfig.from_mapping(config)

    feed_conductivity = capture_cfg.feed.conductivity_mM
    feed_volume_l = concentration_plan.derived.get("output_volume_l")
    if feed_volume_l is None:
        feed_volume_l = concentration_plan.derived.get("input_volume_l")

    route, selection_notes = _select_route(
        method,
        capture_cfg,
        feed_conductivity_mM=feed_conductivity,
        feed_volume_l=feed_volume_l,
    )

    if route is CaptureRoute.CHITOSAN:
        unit, derived, route_notes, handoff = _build_chitosan_unit(
            capture_cfg, concentration_plan
        )
    else:
        route = CaptureRoute.AEX
        unit, derived, route_notes, handoff = _build_aex_unit(
            capture_cfg, concentration_plan
        )

    if handoff:
        handoff.notes.extend(selection_notes)

    notes = selection_notes + route_notes + unit.notes
    chain = CaptureChain(
        route=route,
        units=[unit],
        product_out_kg=derived.get("product_out_kg"),
        pool_volume_l=derived.get("pool_volume_l"),
        pool_conductivity_mM=derived.get("pool_conductivity_mM"),
        pool_ph=derived.get("pool_ph"),
        cdmo_cost_per_batch=derived.get("cdmo_cost_per_batch"),
        resin_cost_per_batch=derived.get("resin_cost_per_batch"),
        buffer_cost_per_batch=derived.get("buffer_cost_per_batch"),
        notes=notes,
        handoff=handoff,
    )
    return chain
