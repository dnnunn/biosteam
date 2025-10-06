"""Shared helpers to compute standardized CMO + resin allocations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

__all__ = [
    "CMOResinAllocation",
    "compute_allocation",
]


_VALID_BASES = {
    "KG_RELEASED": ("kg released", "total_kg_released"),
    "GOOD_BATCHES": ("good batches released", "good_batches_released"),
    "SCHEDULED_CAPACITY": ("scheduled batches", "planned_batches"),
    "PROCESS_TIME_HOURS": ("process hours", "process_hours"),
}


@dataclass(frozen=True)
class CMOResinAllocation:
    """Computed allocation totals and per-unit values for CMO + resin pools."""

    basis: str
    denominator_label: str
    denominator_value: float
    cmo_fixed_total_usd: float
    cmo_variable_total_usd: float
    cmo_total_usd: float
    resin_amort_total_usd: float
    resin_cip_total_usd: float
    resin_total_usd: float
    pooled_total_usd: float
    cmo_per_unit_usd: Optional[float]
    resin_per_unit_usd: Optional[float]
    total_per_unit_usd: Optional[float]
    metadata: Mapping[str, float] = field(default_factory=dict)


def _coerce_float(value: Optional[float]) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_divide(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0.0:
        return None
    return numerator / denominator


def compute_allocation(
    *,
    allocation_basis: str,
    campaigns_planned: float,
    batches_planned_per_campaign: float,
    batches_executed: float,
    good_batches_released: float,
    total_kg_released: float,
    process_hours_per_batch: float,
    cmo_standard_per_batch_usd: float,
    cmo_campaign_per_batch_usd: float,
    cmo_retainer_annual_usd: float = 0.0,
    resin_cost_per_batch_usd: float,
    resin_cip_cost_per_batch_usd: float = 0.0,
    resin_lifetimes_consumed_per_batch: Optional[float] = None,
    resin_cost_per_l: Optional[float] = None,
    resin_volume_l: Optional[float] = None,
    resin_salvage_fraction: Optional[float] = None,
    cycles_per_batch: Optional[float] = None,
) -> CMOResinAllocation:
    """Return pooled allocation totals/per-unit values for a single policy."""

    basis = (allocation_basis or "KG_RELEASED").strip().upper()
    if basis not in _VALID_BASES:
        raise ValueError(f"Unsupported allocation basis: {allocation_basis!r}")

    campaigns_planned = _coerce_float(campaigns_planned)
    batches_planned_per_campaign = _coerce_float(batches_planned_per_campaign)
    planned_batches = campaigns_planned * batches_planned_per_campaign

    batches_executed = _coerce_float(batches_executed)
    good_batches_released = _coerce_float(good_batches_released) or batches_executed
    total_kg_released = _coerce_float(total_kg_released)
    process_hours_per_batch = _coerce_float(process_hours_per_batch)

    cmo_standard_per_batch_usd = _coerce_float(cmo_standard_per_batch_usd)
    cmo_campaign_per_batch_usd = _coerce_float(cmo_campaign_per_batch_usd)
    cmo_retainer_annual_usd = _coerce_float(cmo_retainer_annual_usd)

    resin_cost_per_batch_usd = _coerce_float(resin_cost_per_batch_usd)
    resin_cip_cost_per_batch_usd = _coerce_float(resin_cip_cost_per_batch_usd)

    utilization_fraction = 0.0
    if planned_batches > 0.0:
        utilization_fraction = batches_executed / planned_batches

    denominator_value = 0.0
    denominator_label, denominator_key = _VALID_BASES[basis]
    if basis == "KG_RELEASED":
        denominator_value = total_kg_released
    elif basis == "GOOD_BATCHES":
        denominator_value = good_batches_released
    elif basis == "SCHEDULED_CAPACITY":
        denominator_value = planned_batches
    elif basis == "PROCESS_TIME_HOURS":
        denominator_value = batches_executed * process_hours_per_batch

    cmo_fixed_total_usd = cmo_campaign_per_batch_usd * batches_executed + cmo_retainer_annual_usd
    cmo_variable_total_usd = cmo_standard_per_batch_usd * batches_executed
    cmo_total_usd = cmo_fixed_total_usd + cmo_variable_total_usd

    resin_amort_total_usd = resin_cost_per_batch_usd * batches_executed
    resin_cip_total_usd = resin_cip_cost_per_batch_usd * batches_executed
    resin_total_usd = resin_amort_total_usd + resin_cip_total_usd

    pooled_total_usd = cmo_total_usd + resin_total_usd

    cmo_per_unit_usd = _safe_divide(cmo_total_usd, denominator_value)
    resin_per_unit_usd = _safe_divide(resin_total_usd, denominator_value)
    total_per_unit_usd = _safe_divide(pooled_total_usd, denominator_value)

    metadata: Dict[str, float] = {
        "allocation_basis": basis,
        "campaigns_planned": campaigns_planned,
        "batches_planned_per_campaign": batches_planned_per_campaign,
        "planned_batches": planned_batches,
        "batches_executed": batches_executed,
        "good_batches_released": good_batches_released,
        "total_kg_released": total_kg_released,
        "process_hours_per_batch": process_hours_per_batch,
        "process_hours_total": batches_executed * process_hours_per_batch,
        "utilization_fraction": utilization_fraction,
        "cmo_standard_per_batch_usd": cmo_standard_per_batch_usd,
        "cmo_campaign_per_batch_usd": cmo_campaign_per_batch_usd,
        "cmo_retainer_annual_usd": cmo_retainer_annual_usd,
        "resin_cost_per_batch_usd": resin_cost_per_batch_usd,
        "resin_cip_cost_per_batch_usd": resin_cip_cost_per_batch_usd,
    }

    if resin_lifetimes_consumed_per_batch is not None:
        metadata["resin_lifetimes_consumed_per_batch"] = _coerce_float(
            resin_lifetimes_consumed_per_batch
        )
    if resin_cost_per_l is not None:
        metadata["resin_cost_per_l"] = _coerce_float(resin_cost_per_l)
    if resin_volume_l is not None:
        metadata["resin_volume_l"] = _coerce_float(resin_volume_l)
    if resin_salvage_fraction is not None:
        metadata["resin_salvage_fraction"] = _coerce_float(resin_salvage_fraction)
    if cycles_per_batch is not None:
        metadata["cycles_per_batch"] = _coerce_float(cycles_per_batch)

    metadata[denominator_key] = denominator_value

    return CMOResinAllocation(
        basis=basis,
        denominator_label=denominator_label,
        denominator_value=denominator_value,
        cmo_fixed_total_usd=cmo_fixed_total_usd,
        cmo_variable_total_usd=cmo_variable_total_usd,
        cmo_total_usd=cmo_total_usd,
        resin_amort_total_usd=resin_amort_total_usd,
        resin_cip_total_usd=resin_cip_total_usd,
        resin_total_usd=resin_total_usd,
        pooled_total_usd=pooled_total_usd,
        cmo_per_unit_usd=cmo_per_unit_usd,
        resin_per_unit_usd=resin_per_unit_usd,
        total_per_unit_usd=total_per_unit_usd,
        metadata=metadata,
    )
