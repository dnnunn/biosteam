"""Contract-based CMO cost calculations for the migration front-end."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .cmo import StageCostSummary


@dataclass
class CMOTimings:
    """Processing durations used to size CMO toll charges (hours)."""

    seed_hours: float
    fermentation_hours: float
    turnaround_hours: float
    micro_hours: float
    uf_hours: float
    df_hours: float
    chromatography_hours: float
    predry_hours: float
    spray_hours: float


@dataclass
class CMORates:
    """Base toll rates and per-batch fees quoted by the CMO."""

    fermenter_daily_rate: float
    dsp_daily_rate: float
    spray_hourly_rate: float
    labor_per_batch: float
    documentation_per_batch: float
    qa_review_per_batch: float
    qc_testing_per_batch: float
    consumables_markup_fraction: float


@dataclass
class CMODiscounts:
    """Campaign/contract discount structure."""

    fermenter_campaign: float
    dsp_campaign: float
    spray_campaign: float
    labor_campaign: float
    qa_campaign: float
    consumables_campaign: float
    long_term_contract: float
    contract_length_years: float
    annual_price_escalation: float


@dataclass
class CMOStructure:
    """Campaign scheduling parameters for amortising one-off fees."""

    batches_per_campaign: float
    annual_campaigns: float
    campaign_setup_fee: float
    facility_reservation_fee: float
    campaign_reservation_months: float
    validation_batches_required: float
    validation_batch_surcharge: float

    @property
    def batches_per_year(self) -> float:
        return self.batches_per_campaign * self.annual_campaigns


def _campaign_factor(discount: float, batches_per_campaign: float) -> float:
    if batches_per_campaign <= 0.0:
        return 1.0
    return 1.0 - discount * (1.0 - 1.0 / batches_per_campaign)


def _contract_factor(discount: float, contract_length_years: float) -> float:
    horizon = min(max(contract_length_years, 0.0) / 3.0, 1.0)
    return 1.0 - discount * horizon


def _escalation_factor(annual_escalation: float) -> float:
    # Excel averages the first three years of compounded escalation.
    return (1.0 + annual_escalation + annual_escalation ** 2) / 3.0


def _stage_summary(stage: str, *, base: float, total: float, notes: str) -> StageCostSummary:
    components = {
        "base_fee": base,
        "per_batch": total,
    }
    return StageCostSummary(stage=stage, total_usd=total, components=components, notes=[notes])


def compute_contract_stage_costs(
    timings: CMOTimings,
    rates: CMORates,
    discounts: CMODiscounts,
    structure: CMOStructure,
    *,
    materials_cost_usd: float,
    consumables_base_override: float | None = None,
) -> Tuple[Dict[str, StageCostSummary], float, float, float]:
    """Return detailed per-batch CMO costs mirroring the Excel contract logic.

    Returns a tuple of (stage_summaries, standard_batch_cost, campaign_adders, total_per_batch).
    """

    batches_per_campaign = max(structure.batches_per_campaign, 1.0)
    batches_per_year = max(structure.batches_per_year, 1.0)

    campaign_factors = {
        "fermenter": _campaign_factor(discounts.fermenter_campaign, batches_per_campaign),
        "dsp": _campaign_factor(discounts.dsp_campaign, batches_per_campaign),
        "spray": _campaign_factor(discounts.spray_campaign, batches_per_campaign),
        "labor": _campaign_factor(discounts.labor_campaign, batches_per_campaign),
        "qa": _campaign_factor(discounts.qa_campaign, batches_per_campaign),
        "consumables": _campaign_factor(discounts.consumables_campaign, batches_per_campaign),
    }

    contract_factor = _contract_factor(discounts.long_term_contract, discounts.contract_length_years)
    escalation_factor = _escalation_factor(discounts.annual_price_escalation)

    def _apply(base: float, campaign_key: str) -> float:
        return base * campaign_factors[campaign_key] * contract_factor * escalation_factor

    fermenter_base = (
        (timings.seed_hours + timings.fermentation_hours + timings.turnaround_hours)
        / 24.0
        * rates.fermenter_daily_rate
    )
    fermenter_fee = _apply(fermenter_base, "fermenter")

    dsp_hours = max(
        timings.micro_hours,
        timings.uf_hours + timings.df_hours,
        timings.chromatography_hours + timings.predry_hours,
    )
    dsp_base = dsp_hours / 24.0 * rates.dsp_daily_rate
    dsp_fee = _apply(dsp_base, "dsp")

    spray_base = timings.spray_hours * rates.spray_hourly_rate
    spray_fee = _apply(spray_base, "spray")

    labor_fee = _apply(rates.labor_per_batch, "labor")

    qa_factor = campaign_factors["qa"] * contract_factor * escalation_factor
    documentation_fee = rates.documentation_per_batch * qa_factor
    qa_review_fee = rates.qa_review_per_batch * qa_factor
    qc_fee = rates.qc_testing_per_batch * qa_factor

    consumables_base = (
        consumables_base_override
        if consumables_base_override is not None
        else materials_cost_usd * rates.consumables_markup_fraction
    )
    consumables_fee = _apply(consumables_base, "consumables")

    stage_costs: Dict[str, StageCostSummary] = {
        "usp02_fermentation": _stage_summary(
            "usp02_fermentation",
            base=fermenter_base,
            total=fermenter_fee,
            notes="Fermenter toll with campaign & contract discounts",
        ),
        "dsp_suite": _stage_summary(
            "dsp_suite",
            base=dsp_base,
            total=dsp_fee,
            notes="DSP suite toll (max of MF, UF/DF, Chrom + TFF)",
        ),
        "spray_dryer": _stage_summary(
            "spray_dryer",
            base=spray_base,
            total=spray_fee,
            notes="Spray dryer hourly toll",
        ),
        "labor": _stage_summary(
            "labor",
            base=rates.labor_per_batch,
            total=labor_fee,
            notes="Operations labor with campaign efficiency",
        ),
        "documentation": _stage_summary(
            "documentation",
            base=rates.documentation_per_batch,
            total=documentation_fee,
            notes="Batch documentation fee",
        ),
        "qa_review": _stage_summary(
            "qa_review",
            base=rates.qa_review_per_batch,
            total=qa_review_fee,
            notes="QA review charge",
        ),
        "qc_testing": _stage_summary(
            "qc_testing",
            base=rates.qc_testing_per_batch,
            total=qc_fee,
            notes="QC release testing",
        ),
        "consumables": _stage_summary(
            "consumables",
            base=consumables_base,
            total=consumables_fee,
            notes="CMO markup on consumables",
        ),
    }

    standard_batch_cost = sum(summary.total_usd for summary in stage_costs.values())

    campaign_setup_per_batch = structure.campaign_setup_fee / batches_per_campaign
    reservation_per_batch = (
        structure.facility_reservation_fee
        * structure.campaign_reservation_months
        * structure.annual_campaigns
        / batches_per_year
    )
    validation_annual = (
        structure.validation_batches_required
        * structure.validation_batch_surcharge
        * standard_batch_cost
        / max(discounts.contract_length_years, 1.0)
    )
    validation_per_batch = validation_annual / batches_per_year

    campaign_stage_costs = {
        "campaign_setup": StageCostSummary(
            stage="campaign_setup",
            total_usd=campaign_setup_per_batch,
            components={"per_campaign": structure.campaign_setup_fee, "per_batch": campaign_setup_per_batch},
            notes=["Campaign setup fee amortised per batch"],
        ),
        "facility_reservation": StageCostSummary(
            stage="facility_reservation",
            total_usd=reservation_per_batch,
            components={"monthly_fee": structure.facility_reservation_fee, "per_batch": reservation_per_batch},
            notes=["Facility reservation amortised across campaigns"],
        ),
        "validation": StageCostSummary(
            stage="validation",
            total_usd=validation_per_batch,
            components={"annual_validation_cost": validation_annual, "per_batch": validation_per_batch},
            notes=["Validation surcharge amortised over contract"],
        ),
    }

    stage_costs.update(campaign_stage_costs)

    campaign_related_total = sum(summary.total_usd for summary in campaign_stage_costs.values())
    total_per_batch = standard_batch_cost + campaign_related_total

    # Keep a seed entry for completeness (CMO profile expects it, value zero).
    stage_costs.setdefault(
        "usp01_seed",
        StageCostSummary(stage="usp01_seed", total_usd=0.0, components={}, notes=["Seed charged as direct materials"]),
    )

    return stage_costs, standard_batch_cost, campaign_related_total, total_per_batch
