"""DSP04 polish and sterile filtration routing after DSP03."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Mapping, Optional

import biosteam as bst

from .capture import CaptureHandoff
from .simple_units import PlanBackedUnit
from .unit_builders import UnitPlan

__all__ = [
    "DSP04Stage",
    "DSP04Config",
    "DSP04Chain",
    "build_dsp04_chain",
]


class DSP04Stage(str, Enum):
    """Available DSP04 polish stages."""

    NONE = "none"
    AEX_REPEAT = "aex_repeat"
    CEX_NEGATIVE = "cex_negative"
    HIC_FLOWTHROUGH = "hic_flowthrough"
    MIXEDBED_IEX = "mixedbed_iex"
    ENZYMATIC = "enzymatic_tidyup"


@dataclass
class DSP04StageConfig:
    """Configuration for an individual DSP04 stage."""

    enabled: bool = True
    notes: List[str] = field(default_factory=list)


@dataclass
class SterileFilterConfig:
    flux_lmh: Optional[float] = None
    max_dp_bar: Optional[float] = None
    adsorption_loss_fraction: Optional[float] = None
    prefilter_enabled: bool = False


@dataclass
class DSP04Config:
    """Serialized configuration for DSP04 routing."""

    stage_order: List[DSP04Stage] = field(default_factory=list)
    stages: Mapping[DSP04Stage, DSP04StageConfig] = field(default_factory=dict)
    sterile_filter: SterileFilterConfig = field(default_factory=SterileFilterConfig)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "DSP04Config":
        if not isinstance(data, Mapping):
            return cls()

        order = []
        for name in data.get("stage_order", []):
            try:
                order.append(DSP04Stage(name))
            except ValueError:
                continue

        stages: dict[DSP04Stage, DSP04StageConfig] = {}
        stage_map = data.get("stages") if isinstance(data.get("stages"), Mapping) else {}
        for stage_name, cfg in stage_map.items():
            try:
                stage = DSP04Stage(stage_name)
            except ValueError:
                continue
            if not isinstance(cfg, Mapping):
                stages[stage] = DSP04StageConfig()
            else:
                stages[stage] = DSP04StageConfig(
                    enabled=bool(cfg.get("enabled", True)),
                    notes=[str(item) for item in cfg.get("notes", [])] if isinstance(cfg.get("notes"), list) else [],
                )

        sterile_cfg = data.get("sterile_filter") if isinstance(data.get("sterile_filter"), Mapping) else {}
        sterile = SterileFilterConfig(
            flux_lmh=_as_float(sterile_cfg.get("flux_lmh")),
            max_dp_bar=_as_float(sterile_cfg.get("max_dp_bar")),
            adsorption_loss_fraction=_as_float(sterile_cfg.get("adsorption_loss_fraction")),
            prefilter_enabled=bool(sterile_cfg.get("prefilter_enabled", False)),
        )

        return cls(stage_order=order, stages=stages, sterile_filter=sterile)


def _as_float(value: object | None) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class DSP04Chain:
    """DSP04 stage sequence plus sterile filtration."""

    stages: List[bst.Unit]
    sterile_filter: bst.Unit
    handoff: CaptureHandoff
    notes: List[str] = field(default_factory=list)


class DSP04StageUnit(PlanBackedUnit):
    """Placeholder polish step (future upgrade to real BioSTEAM units)."""

    _N_ins = 1
    _N_outs = 1
    line = "DSP04"

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


class SterileFilterUnit(PlanBackedUnit):
    """Placeholder sterile filter with integrity pass flag."""

    _N_ins = 1
    _N_outs = 1
    line = "SterileFilter"

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


def _default_stage_order(handoff: CaptureHandoff) -> List[DSP04Stage]:
    if handoff.route.value.lower() == "dsp02_chitosan":
        if (handoff.polyp_mM or 0) > 0:
            return [DSP04Stage.CEX_NEGATIVE, DSP04Stage.AEX_REPEAT]
        return [DSP04Stage.CEX_NEGATIVE]
    return [DSP04Stage.NONE]


def build_dsp04_chain(
    *,
    capture_handoff: CaptureHandoff,
    dsp03_handoff: CaptureHandoff,
    config_mapping: Mapping[str, object] | None = None,
) -> DSP04Chain:
    config = DSP04Config.from_mapping(config_mapping or {})
    order = config.stage_order or _default_stage_order(capture_handoff)

    stages: List[bst.Unit] = []
    notes: List[str] = []
    current_handoff = dsp03_handoff

    for stage in order:
        if stage is DSP04Stage.NONE:
            continue
        stage_cfg = config.stages.get(stage, DSP04StageConfig())
        if not stage_cfg.enabled:
            continue
        plan = UnitPlan(None, None, None, derived={"route": stage.value}, notes=list(stage_cfg.notes))
        unit = DSP04StageUnit(f"DSP04_{stage.value}", plan=plan)
        stages.append(unit)
        notes.extend(stage_cfg.notes)

    sterile_plan = UnitPlan(
        None,
        None,
        None,
        derived={
            "flux_lmh": config.sterile_filter.flux_lmh,
            "max_dp_bar": config.sterile_filter.max_dp_bar,
            "adsorption_loss_fraction": config.sterile_filter.adsorption_loss_fraction,
            "prefilter_enabled": config.sterile_filter.prefilter_enabled,
        },
        notes=[],
    )
    sterile_unit = SterileFilterUnit("DSP04_SterileFilter", plan=sterile_plan)

    dsp04_handoff = CaptureHandoff(
        route=DSP04Stage.NONE,
        pool_volume_l=current_handoff.pool_volume_l,
        opn_concentration_g_per_l=current_handoff.opn_concentration_g_per_l,
        conductivity_mM=current_handoff.conductivity_mM,
        ph=current_handoff.ph,
        dna_mg_per_l=current_handoff.dna_mg_per_l,
        chitosan_ppm=current_handoff.chitosan_ppm,
        polyp_mM=current_handoff.polyp_mM,
        step_recovery_fraction=current_handoff.step_recovery_fraction,
        needs_df=current_handoff.needs_df,
        needs_fines_polish=current_handoff.needs_fines_polish,
        cycle_time_h=current_handoff.cycle_time_h,
        cost_per_batch=current_handoff.cost_per_batch,
        notes=list(set(notes + current_handoff.notes)),
    )

    return DSP04Chain(stages=stages, sterile_filter=sterile_unit, handoff=dsp04_handoff, notes=notes)
