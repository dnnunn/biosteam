"""Route-aware DSP03 concentration/conditioning chain after capture."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Mapping, Optional

import biosteam as bst

from .capture import CaptureHandoff, CaptureRoute
from .simple_units import PlanBackedUnit
from .unit_builders import UnitPlan
from .concentration import SPTFFUnit

__all__ = [
    "DSP03Route",
    "DSP03UnitConfig",
    "DSP03Config",
    "DSP03Chain",
    "build_dsp03_chain",
]


class DSP03Route(str, Enum):
    """Available DSP03 membrane conditioning options."""

    AUTO = "auto"
    UF = "uf"
    DF = "df"
    SPTFF = "sptff"
    CTFF = "ctff"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "DSP03Route":
        if isinstance(value, cls):
            return value
        normalized = (value or cls.AUTO.value).strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.AUTO


@dataclass
class DSP03UnitConfig:
    """Configuration for a specific DSP03 route."""

    flux_lmh: Optional[float] = None
    tmp_bar_max: Optional[float] = None
    sieving_fraction: Optional[float] = None
    adsorption_loss_fraction: Optional[float] = None
    diafiltration_volumes: Optional[float] = None
    stages: Optional[int] = None
    cf_per_stage: Optional[float] = None
    bleed_rate_m3_per_h: Optional[float] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class DSP03Config:
    """Serialized configuration for DSP03 routing."""

    method: DSP03Route = DSP03Route.AUTO
    uf: DSP03UnitConfig = field(default_factory=DSP03UnitConfig)
    df: DSP03UnitConfig = field(default_factory=DSP03UnitConfig)
    sptff: DSP03UnitConfig = field(default_factory=DSP03UnitConfig)
    ctff: DSP03UnitConfig = field(default_factory=DSP03UnitConfig)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "DSP03Config":
        route = DSP03Route.from_string(data.get("method")) if isinstance(data, Mapping) else DSP03Route.AUTO

        def _load_section(name: str) -> DSP03UnitConfig:
            section = data.get(name) if isinstance(data, Mapping) else None
            if not isinstance(section, Mapping):
                return DSP03UnitConfig()
            return DSP03UnitConfig(
                flux_lmh=_as_float(section.get("flux_lmh")),
                tmp_bar_max=_as_float(section.get("tmp_bar_max")),
                sieving_fraction=_as_float(section.get("sieving_fraction")),
                adsorption_loss_fraction=_as_float(section.get("adsorption_loss_fraction")),
                diafiltration_volumes=_as_float(section.get("diafiltration_volumes")),
                stages=_as_int(section.get("stages")),
                cf_per_stage=_as_float(section.get("cf_per_stage")),
                bleed_rate_m3_per_h=_as_float(section.get("bleed_rate_m3_per_h")),
                notes=[str(item) for item in section.get("notes", [])] if isinstance(section.get("notes"), list) else [],
            )

        return cls(
            method=route,
            uf=_load_section("uf"),
            df=_load_section("df"),
            sptff=_load_section("sptff"),
            ctff=_load_section("ctff"),
        )


def _as_float(value: object | None) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: object | None) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass
class DSP03Chain:
    """Description of instantiated DSP03 units."""

    route: DSP03Route
    units: List[bst.Unit]
    handoff: CaptureHandoff
    notes: List[str] = field(default_factory=list)


class DSP03PassthroughUnit(PlanBackedUnit):
    """Fallback placeholder that copies the feed through unchanged."""

    _N_ins = 1
    _N_outs = 1
    line = "DSP03"

    def _run(self) -> None:
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)

        handoff = getattr(self, "_handoff_stream", None)
        if handoff is not None:
            handoff.copy_like(product)
        report = getattr(self, "_handoff_report_stream", None)
        if report is not None:
            report.copy_like(product)


def _select_route(route: DSP03Route, handoff: CaptureHandoff) -> DSP03Route:
    if route is not DSP03Route.AUTO:
        return route

    if handoff.route is not None and handoff.route.lower() == "dsp02_chitosan" and (handoff.polyp_mM or 0) > 0:
        return DSP03Route.DF

    if handoff.needs_df:
        return DSP03Route.DF

    return DSP03Route.SPTFF


def _calculate_pool_properties(handoff: CaptureHandoff) -> tuple[Optional[float], Optional[float]]:
    """Compute pool volume [L] and product mass [kg] from capture handoff."""

    volume_l = handoff.pool_volume_l
    concentration = handoff.opn_concentration_g_per_l
    if volume_l is not None and concentration is not None:
        product_kg = volume_l * concentration / 1_000.0
    else:
        product_kg = None
    return volume_l, product_kg


def _build_passthrough_chain(route: DSP03Route, handoff: CaptureHandoff, config: DSP03UnitConfig) -> DSP03Chain:
    derived = {"notes": list(config.notes)} if config.notes else {}
    plan = UnitPlan(key=None, data=None, specs=None, derived=derived)
    unit = DSP03PassthroughUnit(f"DSP03_{route.value}", plan=plan)
    new_handoff = CaptureHandoff(
        route=handoff.route,
        pool_volume_l=handoff.pool_volume_l,
        opn_concentration_g_per_l=handoff.opn_concentration_g_per_l,
        conductivity_mM=handoff.conductivity_mM,
        ph=handoff.ph,
        dna_mg_per_l=handoff.dna_mg_per_l,
        chitosan_ppm=handoff.chitosan_ppm,
        polyp_mM=handoff.polyp_mM,
        step_recovery_fraction=handoff.step_recovery_fraction,
        needs_df=handoff.needs_df,
        needs_fines_polish=handoff.needs_fines_polish,
        cycle_time_h=handoff.cycle_time_h,
        cost_per_batch=handoff.cost_per_batch,
        notes=list(set(handoff.notes + config.notes)),
    )
    return DSP03Chain(route=route, units=[unit], handoff=new_handoff, notes=list(set(config.notes)))


def _build_sptff_unit(handoff: CaptureHandoff, config: DSP03UnitConfig) -> tuple[bst.Unit, CaptureHandoff, List[str]]:
    volume_l, product_kg = _calculate_pool_properties(handoff)
    notes: List[str] = list(config.notes)
    if volume_l is None:
        notes.append("DSP03 SPTFF: pool volume unavailable; using passthrough")
        passthrough_chain = _build_passthrough_chain(DSP03Route.SPTFF, handoff, config)
        return passthrough_chain.units[0], passthrough_chain.handoff, notes

    stages = config.stages or 1
    cf_per_stage = config.cf_per_stage or 1.0
    concentration_factor = max(cf_per_stage, 1.0) ** max(stages, 1)
    if concentration_factor <= 0:
        concentration_factor = 1.0

    output_volume = volume_l / concentration_factor
    loss_fraction = config.adsorption_loss_fraction or 0.0
    recovery_fraction = max(min(1.0 - loss_fraction, 1.0), 0.0)
    product_out = None if product_kg is None else product_kg * recovery_fraction

    derived = {
        "input_volume_l": volume_l,
        "input_product_kg": product_kg,
        "output_volume_l": output_volume,
        "concentration_factor": concentration_factor,
        "protein_recovery_fraction": recovery_fraction,
        "flux_lmh": config.flux_lmh,
        "density_kg_per_l": 1.0,
    }
    plan = UnitPlan(key=None, data=None, specs=None, derived=derived)
    unit = SPTFFUnit("DSP03_SPTFF", plan=plan)

    updated_volume = output_volume if output_volume is not None else volume_l
    if updated_volume and updated_volume > 0 and product_out is not None:
        updated_concentration = product_out * 1_000.0 / updated_volume
    else:
        updated_concentration = handoff.opn_concentration_g_per_l

    updated_handoff = CaptureHandoff(
        route=handoff.route,
        pool_volume_l=updated_volume,
        opn_concentration_g_per_l=updated_concentration,
        conductivity_mM=handoff.conductivity_mM,
        ph=handoff.ph,
        dna_mg_per_l=handoff.dna_mg_per_l,
        chitosan_ppm=handoff.chitosan_ppm,
        polyp_mM=handoff.polyp_mM,
        step_recovery_fraction=product_out,
        needs_df=handoff.needs_df,
        needs_fines_polish=handoff.needs_fines_polish,
        cycle_time_h=handoff.cycle_time_h,
        cost_per_batch=handoff.cost_per_batch,
        notes=list(set(handoff.notes + notes)),
    )

    return unit, updated_handoff, notes


def build_dsp03_chain(
    *,
    capture_handoff: CaptureHandoff,
    config_mapping: Mapping[str, object] | None = None,
    upstream_plan: UnitPlan | None = None,
) -> DSP03Chain:
    config = DSP03Config.from_mapping(config_mapping or {})
    route = _select_route(config.method, capture_handoff)

    route_config = {
        DSP03Route.UF: config.uf,
        DSP03Route.DF: config.df,
        DSP03Route.SPTFF: config.sptff,
        DSP03Route.CTFF: config.ctff,
    }.get(route, config.sptff)

    upstream_notes = upstream_plan.notes if upstream_plan and upstream_plan.notes else []

    if route == DSP03Route.SPTFF:
        unit, handoff, note_list = _build_sptff_unit(capture_handoff, route_config)
        merged_notes = list(dict.fromkeys(list(upstream_notes) + note_list))
        return DSP03Chain(route=route, units=[unit], handoff=handoff, notes=merged_notes)

    chain = _build_passthrough_chain(route, capture_handoff, route_config)
    if upstream_notes:
        chain.notes.extend(upstream_notes)
        chain.notes = list(dict.fromkeys(chain.notes))
    return chain
