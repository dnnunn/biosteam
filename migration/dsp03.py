"""Route-aware DSP03 concentration/conditioning chain after capture."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Mapping, Optional

import biosteam as bst

from .capture import CaptureHandoff
from .simple_units import PlanBackedUnit
from .unit_builders import UnitPlan

__all__ = [
    "DSP03Route",
    "DSP03Unit",
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


class DSP03Unit(PlanBackedUnit):
    """Plan-backed placeholder that currently passes feed through unchanged."""

    _N_ins = 1
    _N_outs = 1
    line = "DSP03"

    def _run(self) -> None:
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)


def _select_route(route: DSP03Route, handoff: CaptureHandoff) -> DSP03Route:
    if route is not DSP03Route.AUTO:
        return route

    if handoff.route is not None and handoff.route.lower() == "dsp02_chitosan" and (handoff.polyp_mM or 0) > 0:
        return DSP03Route.DF

    if handoff.needs_df:
        return DSP03Route.DF

    return DSP03Route.SPTFF


def _make_plan(route: DSP03Route, handoff: CaptureHandoff, config: DSP03UnitConfig) -> UnitPlan:
    derived = {
        "input_volume_l": handoff.pool_volume_l * 1_000 if handoff.pool_volume_l is not None else None,
        "input_product_kg": (handoff.pool_volume_l or 0.0) * (handoff.opn_concentration_g_per_l or 0.0) / 1_000.0,
        "route": route.value,
        "notes": list(config.notes),
    }
    plan = UnitPlan(
        key=None,  # DSP03 is not keyed to Excel defaults yet
        data=None,
        specs=None,
        derived={k: v for k, v in derived.items() if v is not None},
    )
    return plan


def _build_unit(route: DSP03Route, plan: UnitPlan) -> DSP03Unit:
    return DSP03Unit(f"DSP03_{route.value}", plan=plan)


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

    plan = _make_plan(route, capture_handoff, route_config)
    if upstream_plan is not None:
        notes = upstream_plan.notes.copy()
    else:
        notes = []
    if route_config.notes:
        notes.extend(route_config.notes)

    unit = _build_unit(route, plan)

    # For now, DSP03 handoff mirrors capture handoff until more detailed models arrive.
    dsp03_handoff = CaptureHandoff(
        route=route,
        pool_volume_l=capture_handoff.pool_volume_l,
        opn_concentration_g_per_l=capture_handoff.opn_concentration_g_per_l,
        conductivity_mM=capture_handoff.conductivity_mM,
        ph=capture_handoff.ph,
        dna_mg_per_l=capture_handoff.dna_mg_per_l,
        chitosan_ppm=capture_handoff.chitosan_ppm,
        polyp_mM=capture_handoff.polyp_mM,
        step_recovery_fraction=capture_handoff.step_recovery_fraction,
        needs_df=capture_handoff.needs_df,
        needs_fines_polish=capture_handoff.needs_fines_polish,
        cycle_time_h=capture_handoff.cycle_time_h,
        cost_per_batch=capture_handoff.cost_per_batch,
        notes=list(set(capture_handoff.notes + notes)),
    )

    return DSP03Chain(route=route, units=[unit], handoff=dsp03_handoff, notes=notes)

