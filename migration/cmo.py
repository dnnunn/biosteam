"""CMO/TEA cost profile handling for BioSTEAM migration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Optional

import yaml


DEFAULT_PROFILE_PATH = Path("migration/cmo_profiles/default.yaml")


@dataclass
class StageCostRates:
    """CMO rate card for a single stage."""

    fixed_per_batch: float = 0.0
    per_m3_feed: float = 0.0
    per_kg_product: float = 0.0
    per_hour: float = 0.0
    per_m2_membrane: float = 0.0
    minimum_hours: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class CMOCostProfile:
    """Complete CMO profile covering every stage plus metadata."""

    name: str
    stages: Dict[str, StageCostRates]
    include_capex: bool = False


@dataclass
class StageCostSummary:
    stage: str
    total_usd: float
    components: Dict[str, float]
    notes: list[str]


def _as_float(value: object | None, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_cmo_profile(path: Optional[Path | str]) -> CMOCostProfile:
    """Load a cost profile from YAML. Falls back to the default profile."""

    profile_path = Path(path) if path else DEFAULT_PROFILE_PATH
    if not profile_path.exists():
        raise FileNotFoundError(f"CMO profile not found: {profile_path}")

    with profile_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    name = str(data.get("name") or profile_path.stem)
    include_capex = bool(data.get("include_capex", False))

    stages_cfg: Mapping[str, Mapping[str, object]] = data.get("stages", {})
    stages: Dict[str, StageCostRates] = {}
    for stage, cfg in stages_cfg.items():
        cfg = cfg or {}
        stages[stage] = StageCostRates(
            fixed_per_batch=_as_float(cfg.get("fixed_per_batch")),
            per_m3_feed=_as_float(cfg.get("per_m3_feed")),
            per_kg_product=_as_float(cfg.get("per_kg_product")),
            per_hour=_as_float(cfg.get("per_hour")),
            per_m2_membrane=_as_float(cfg.get("per_m2_membrane")),
            minimum_hours=_as_float(cfg.get("minimum_hours")),
            notes=[str(note) for note in cfg.get("notes", [])] if isinstance(cfg.get("notes"), list) else [],
        )

    return CMOCostProfile(name=name, stages=stages, include_capex=include_capex)


def evaluate_stage_cost(
    stage: str,
    rates: StageCostRates,
    *,
    feed_volume_m3: float = 0.0,
    product_kg: float = 0.0,
    hours: float = 0.0,
    membrane_area_m2: float = 0.0,
) -> StageCostSummary:
    """Compute the cost for a single stage given the available metrics."""

    components: Dict[str, float] = {}
    total = 0.0

    if rates.fixed_per_batch:
        components["fixed_per_batch"] = rates.fixed_per_batch
        total += rates.fixed_per_batch

    if rates.per_m3_feed and feed_volume_m3:
        cost = rates.per_m3_feed * feed_volume_m3
        components["per_m3_feed"] = cost
        total += cost

    if rates.per_kg_product and product_kg:
        cost = rates.per_kg_product * product_kg
        components["per_kg_product"] = cost
        total += cost

    effective_hours = hours
    if rates.per_hour:
        if effective_hours < rates.minimum_hours:
            effective_hours = rates.minimum_hours
        cost = rates.per_hour * effective_hours if effective_hours else 0.0
        if cost:
            components["per_hour"] = cost
            total += cost

    if rates.per_m2_membrane and membrane_area_m2:
        cost = rates.per_m2_membrane * membrane_area_m2
        components["per_m2_membrane"] = cost
        total += cost

    return StageCostSummary(
        stage=stage,
        total_usd=total,
        components=components,
        notes=list(rates.notes),
    )


def compute_cmo_costs(
    profile: CMOCostProfile,
    metrics: Mapping[str, Mapping[str, float]],
) -> tuple[Dict[str, StageCostSummary], float]:
    """Evaluate all stage costs and return summaries and the total fee."""

    summaries: Dict[str, StageCostSummary] = {}
    total = 0.0

    for stage, rates in profile.stages.items():
        stage_metrics = metrics.get(stage, {})
        summary = evaluate_stage_cost(
            stage,
            rates,
            feed_volume_m3=stage_metrics.get("feed_volume_m3", 0.0),
            product_kg=stage_metrics.get("product_kg", 0.0),
            hours=stage_metrics.get("hours", 0.0),
            membrane_area_m2=stage_metrics.get("membrane_area_m2", 0.0),
        )
        summaries[stage] = summary
        total += summary.total_usd

    return summaries, total
