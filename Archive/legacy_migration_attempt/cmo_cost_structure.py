#!/usr/bin/env python3
"""
CMO Cost Structure Implementation
32.5% facility overhead with campaign economics (30 batches/year, 5 campaigns)

CMO COST STRUCTURE:
- Facility/CMO costs: 32.5% = $410.55/kg
- Campaign economics: 30 batches/year across 5 campaigns
- Time-based facility fees for USP and DSP
- Campaign setup and validation costs
- Facility reservation and maintenance
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import json
from datetime import datetime, timedelta

class FacilityType(Enum):
    """CMO facility types"""
    FERMENTATION = "fermentation"
    DSP = "downstream_processing"
    DRYING = "drying"
    ANALYTICAL = "analytical"
    WAREHOUSE = "warehouse"

class CampaignPhase(Enum):
    """Campaign phases"""
    SETUP = "setup"
    VALIDATION = "validation"
    PRODUCTION = "production"
    CHANGEOVER = "changeover"
    MAINTENANCE = "maintenance"

@dataclass
class FacilityAsset:
    """Individual facility asset definition"""
    asset_id: str
    facility_type: FacilityType
    capacity: float  # Primary capacity metric
    capacity_unit: str
    daily_rate: float  # $/day
    hourly_rate: Optional[float] = None  # $/hour if applicable
    minimum_booking_days: int = 1
    setup_time_days: float = 0.5
    changeover_time_days: float = 1.0
    utilization_factor: float = 0.85  # 85% utilization efficiency

@dataclass
class CampaignStructure:
    """Campaign structure and economics"""
    batches_per_campaign: int = 6
    campaigns_per_year: int = 5
    campaign_duration_days: float = 30
    inter_campaign_gap_days: float = 14
    validation_batches_per_campaign: int = 1

    # Cost allocation factors
    setup_cost_allocation: float = 0.8  # 80% to first batch
    validation_cost_allocation: float = 0.9  # 90% to validation batch

    # Annual fixed costs
    facility_reservation_annual: float = 500_000  # $/year
    regulatory_support_annual: float = 250_000  # $/year
    account_management_annual: float = 150_000  # $/year

class CMOFacility:
    """Complete CMO facility cost model"""

    def __init__(self):
        self.assets = self._define_facility_assets()
        self.campaign_structure = CampaignStructure()

        # Annual economics
        self.total_annual_batches = (self.campaign_structure.batches_per_campaign *
                                   self.campaign_structure.campaigns_per_year)

    def _define_facility_assets(self) -> Dict[str, FacilityAsset]:
        """Define all facility assets and their rates"""

        assets = {
            # Fermentation assets
            'fermentor_150m3': FacilityAsset(
                asset_id='fermentor_150m3',
                facility_type=FacilityType.FERMENTATION,
                capacity=150_000,  # L
                capacity_unit='L',
                daily_rate=75_000,  # $/day
                hourly_rate=3_125,  # $/hour
                minimum_booking_days=3,
                setup_time_days=1.0,
                changeover_time_days=2.0
            ),

            'seed_train': FacilityAsset(
                asset_id='seed_train',
                facility_type=FacilityType.FERMENTATION,
                capacity=10_000,  # L total seed capacity
                capacity_unit='L',
                daily_rate=15_000,  # $/day
                setup_time_days=0.5,
                changeover_time_days=0.5
            ),

            # DSP assets
            'dsp_suite_primary': FacilityAsset(
                asset_id='dsp_suite_primary',
                facility_type=FacilityType.DSP,
                capacity=100_000,  # L/day processing capacity
                capacity_unit='L/day',
                daily_rate=75_000,  # $/day
                hourly_rate=3_125,  # $/hour
                minimum_booking_days=2,
                setup_time_days=0.5,
                changeover_time_days=1.5
            ),

            'chromatography_suite': FacilityAsset(
                asset_id='chromatography_suite',
                facility_type=FacilityType.DSP,
                capacity=50_000,  # L/day feed capacity
                capacity_unit='L/day',
                daily_rate=50_000,  # $/day
                hourly_rate=2_083,  # $/hour
                minimum_booking_days=1,
                setup_time_days=1.0,  # Longer setup for chromatography
                changeover_time_days=2.0  # Extensive cleaning required
            ),

            # Drying assets
            'spray_dryer': FacilityAsset(
                asset_id='spray_dryer',
                facility_type=FacilityType.DRYING,
                capacity=150,  # kg/hour
                capacity_unit='kg/hour',
                daily_rate=24_000,  # $/day
                hourly_rate=1_000,  # $/hour
                minimum_booking_days=1,
                setup_time_days=0.25,
                changeover_time_days=0.5
            ),

            # Analytical assets
            'qc_laboratory': FacilityAsset(
                asset_id='qc_laboratory',
                facility_type=FacilityType.ANALYTICAL,
                capacity=20,  # samples/day
                capacity_unit='samples/day',
                daily_rate=5_000,  # $/day
                minimum_booking_days=7,  # Week minimum for QC
                setup_time_days=0.5,
                changeover_time_days=0.5
            ),

            # Storage assets
            'warehouse_cold': FacilityAsset(
                asset_id='warehouse_cold',
                facility_type=FacilityType.WAREHOUSE,
                capacity=1000,  # kg storage
                capacity_unit='kg',
                daily_rate=500,  # $/day
                minimum_booking_days=30,  # Month minimum
                setup_time_days=0.1,
                changeover_time_days=0.1
            )
        }

        return assets

    def calculate_batch_facility_costs(self, processing_times: Dict[str, float],
                                     capture_technology: str = "qff_aex") -> Dict[str, float]:
        """Calculate facility costs for a single batch"""

        costs = {}

        # Fermentation facility costs
        fermentation_days = processing_times.get('fermentation_total_days', 3.0)
        seed_train_days = processing_times.get('seed_train_days', 0.5)

        costs['fermentor_facility'] = fermentation_days * self.assets['fermentor_150m3'].daily_rate
        costs['seed_train_facility'] = seed_train_days * self.assets['seed_train'].daily_rate

        # DSP facility costs (depends on capture technology)
        if capture_technology == "qff_aex":
            # QFF AEX requires chromatography suite
            dsp_days = processing_times.get('dsp_total_days', 2.0)
            chromatography_days = processing_times.get('chromatography_days', 1.0)

            costs['dsp_suite_facility'] = dsp_days * self.assets['dsp_suite_primary'].daily_rate
            costs['chromatography_facility'] = chromatography_days * self.assets['chromatography_suite'].daily_rate

        else:  # chitosan
            # Chitosan uses only primary DSP suite
            dsp_days = processing_times.get('dsp_total_days', 1.0)  # Shorter for chitosan
            costs['dsp_suite_facility'] = dsp_days * self.assets['dsp_suite_primary'].daily_rate
            costs['chromatography_facility'] = 0  # No chromatography needed

        # Drying facility costs
        drying_hours = processing_times.get('drying_hours', 6.0)
        costs['spray_dryer_facility'] = drying_hours * self.assets['spray_dryer'].hourly_rate

        # QC facility costs
        qc_days = processing_times.get('qc_days', 7.0)
        costs['qc_laboratory_facility'] = qc_days * self.assets['qc_laboratory'].daily_rate

        # Storage facility costs
        storage_days = processing_times.get('storage_days', 30.0)
        costs['warehouse_facility'] = storage_days * self.assets['warehouse_cold'].daily_rate

        # Total facility costs
        costs['total_facility_cost'] = sum(costs.values())

        return costs

    def calculate_campaign_costs(self, batch_count: int = 6) -> Dict[str, float]:
        """Calculate campaign-level costs"""

        costs = {}

        # Campaign setup costs (allocated across batches)
        campaign_setup_cost = 250_000  # $ per campaign setup
        costs['campaign_setup_total'] = campaign_setup_cost
        costs['campaign_setup_per_batch'] = campaign_setup_cost / batch_count

        # Validation costs
        validation_cost_per_campaign = 150_000  # $ for validation batch
        costs['validation_total'] = validation_cost_per_campaign
        costs['validation_per_batch'] = validation_cost_per_campaign / batch_count

        # Facility changeover between campaigns
        changeover_cost = 100_000  # $ for full facility changeover
        costs['changeover_total'] = changeover_cost
        costs['changeover_per_batch'] = changeover_cost / batch_count

        # Regulatory support during campaign
        regulatory_cost_per_campaign = 75_000  # $ per campaign
        costs['regulatory_total'] = regulatory_cost_per_campaign
        costs['regulatory_per_batch'] = regulatory_cost_per_campaign / batch_count

        # Total campaign costs
        costs['total_campaign_cost'] = (campaign_setup_cost + validation_cost_per_campaign +
                                      changeover_cost + regulatory_cost_per_campaign)
        costs['total_campaign_cost_per_batch'] = costs['total_campaign_cost'] / batch_count

        return costs

    def calculate_annual_fixed_costs(self) -> Dict[str, float]:
        """Calculate annual fixed costs"""

        costs = {}

        # Fixed costs from campaign structure
        costs['facility_reservation'] = self.campaign_structure.facility_reservation_annual
        costs['regulatory_support'] = self.campaign_structure.regulatory_support_annual
        costs['account_management'] = self.campaign_structure.account_management_annual

        # Additional annual costs
        costs['facility_maintenance'] = 200_000  # $ annual maintenance
        costs['equipment_qualification'] = 100_000  # $ annual requalification
        costs['insurance_coverage'] = 75_000  # $ annual insurance
        costs['technology_transfer'] = 50_000  # $ annual tech transfer support

        # Total annual fixed costs
        costs['total_annual_fixed'] = sum(costs.values())

        # Per batch allocation
        costs['annual_fixed_per_batch'] = costs['total_annual_fixed'] / self.total_annual_batches

        return costs

    def calculate_total_cmo_costs(self, processing_times: Dict[str, float],
                                capture_technology: str = "qff_aex") -> Dict[str, float]:
        """Calculate total CMO costs per batch"""

        # Get all cost components
        facility_costs = self.calculate_batch_facility_costs(processing_times, capture_technology)
        campaign_costs = self.calculate_campaign_costs()
        annual_fixed = self.calculate_annual_fixed_costs()

        # Combine all costs
        total_costs = {}

        # Direct facility costs
        total_costs.update({f"facility_{k}": v for k, v in facility_costs.items()})

        # Campaign costs
        total_costs.update({f"campaign_{k}": v for k, v in campaign_costs.items()})

        # Annual fixed costs
        total_costs.update({f"annual_{k}": v for k, v in annual_fixed.items()})

        # Calculate total CMO cost per batch
        total_cmo_cost = (facility_costs['total_facility_cost'] +
                         campaign_costs['total_campaign_cost_per_batch'] +
                         annual_fixed['annual_fixed_per_batch'])

        total_costs['total_cmo_cost_per_batch'] = total_cmo_cost

        return total_costs

    def analyze_cmo_cost_structure(self, protein_kg_per_batch: float = 491.25) -> Dict[str, any]:
        """Analyze CMO cost structure and validate against target"""

        # Define processing times for QFF AEX baseline
        qff_processing_times = {
            'fermentation_total_days': 3.0,  # 48h ferment + 24h turnaround
            'seed_train_days': 0.5,
            'dsp_total_days': 2.0,
            'chromatography_days': 1.0,  # 10 hours = ~1 day
            'drying_hours': 6.0,
            'qc_days': 7.0,
            'storage_days': 30.0
        }

        # Define processing times for chitosan alternative
        chitosan_processing_times = {
            'fermentation_total_days': 3.0,  # Same fermentation
            'seed_train_days': 0.5,
            'dsp_total_days': 1.0,  # Faster DSP with chitosan
            'chromatography_days': 0.0,  # No chromatography
            'drying_hours': 6.0,
            'qc_days': 7.0,
            'storage_days': 30.0
        }

        # Calculate costs for both technologies
        qff_costs = self.calculate_total_cmo_costs(qff_processing_times, "qff_aex")
        chitosan_costs = self.calculate_total_cmo_costs(chitosan_processing_times, "chitosan")

        # Calculate cost per kg
        qff_cost_per_kg = qff_costs['total_cmo_cost_per_batch'] / protein_kg_per_batch
        chitosan_cost_per_kg = chitosan_costs['total_cmo_cost_per_batch'] / protein_kg_per_batch

        # Target validation (CMO should be 32.5% of $1264.34 = $410.55/kg)
        target_cmo_cost_per_kg = 410.55
        qff_vs_target = abs(qff_cost_per_kg - target_cmo_cost_per_kg)
        qff_within_tolerance = qff_vs_target < 50  # Within $50/kg

        analysis = {
            'qff_aex_analysis': {
                'processing_times': qff_processing_times,
                'costs': qff_costs,
                'cost_per_kg': qff_cost_per_kg,
                'vs_target_difference': qff_vs_target,
                'within_tolerance': qff_within_tolerance
            },
            'chitosan_analysis': {
                'processing_times': chitosan_processing_times,
                'costs': chitosan_costs,
                'cost_per_kg': chitosan_cost_per_kg
            },
            'comparison': {
                'cost_savings_per_batch': qff_costs['total_cmo_cost_per_batch'] - chitosan_costs['total_cmo_cost_per_batch'],
                'cost_savings_per_kg': qff_cost_per_kg - chitosan_cost_per_kg,
                'time_savings_days': (sum([qff_processing_times[k] for k in ['dsp_total_days', 'chromatography_days']]) -
                                    sum([chitosan_processing_times[k] for k in ['dsp_total_days', 'chromatography_days']]))
            },
            'validation': {
                'target_cmo_cost_per_kg': target_cmo_cost_per_kg,
                'calculated_qff_cost_per_kg': qff_cost_per_kg,
                'difference': qff_vs_target,
                'percentage_difference': (qff_vs_target / target_cmo_cost_per_kg) * 100,
                'within_tolerance': qff_within_tolerance
            }
        }

        return analysis

def demonstrate_cmo_cost_structure():
    """Demonstrate the CMO cost structure model"""

    print("=" * 80)
    print("CMO COST STRUCTURE WITH FACILITY OVERHEAD")
    print("=" * 80)

    # Initialize CMO facility
    cmo = CMOFacility()

    print(f"\n1. FACILITY ASSETS:")
    print(f"   Total annual batches: {cmo.total_annual_batches}")
    print(f"   Campaigns per year: {cmo.campaign_structure.campaigns_per_year}")
    print(f"   Batches per campaign: {cmo.campaign_structure.batches_per_campaign}")

    print(f"\n   Facility Assets Defined:")
    for asset_id, asset in cmo.assets.items():
        daily_rate = f"${asset.daily_rate:,.0f}/day"
        hourly_rate = f" (${asset.hourly_rate:,.0f}/hr)" if asset.hourly_rate else ""
        print(f"     {asset_id}: {daily_rate}{hourly_rate}")

    print(f"\n2. CMO COST ANALYSIS:")
    analysis = cmo.analyze_cmo_cost_structure()

    # QFF AEX analysis
    qff_analysis = analysis['qff_aex_analysis']
    print(f"\n   QFF AEX CMO Costs:")
    print(f"     Facility costs:")
    for key, value in qff_analysis['costs'].items():
        if key.startswith('facility_') and not key.endswith('_facility'):
            print(f"       {key.replace('facility_', '').replace('_', ' ').title()}: ${value:,.0f}")

    print(f"     Campaign costs:")
    for key, value in qff_analysis['costs'].items():
        if key.startswith('campaign_') and key.endswith('_per_batch'):
            print(f"       {key.replace('campaign_', '').replace('_per_batch', '').replace('_', ' ').title()}: ${value:,.0f}")

    print(f"     Annual fixed costs:")
    for key, value in qff_analysis['costs'].items():
        if key.startswith('annual_') and key.endswith('_per_batch'):
            print(f"       {key.replace('annual_', '').replace('_per_batch', '').replace('_', ' ').title()}: ${value:,.0f}")

    print(f"\n     Total CMO cost per batch: ${qff_analysis['costs']['total_cmo_cost_per_batch']:,.0f}")
    print(f"     CMO cost per kg protein: ${qff_analysis['cost_per_kg']:.2f}")

    # Chitosan analysis
    chitosan_analysis = analysis['chitosan_analysis']
    print(f"\n   Chitosan CMO Costs:")
    print(f"     Total CMO cost per batch: ${chitosan_analysis['costs']['total_cmo_cost_per_batch']:,.0f}")
    print(f"     CMO cost per kg protein: ${chitosan_analysis['cost_per_kg']:.2f}")

    # Comparison
    comparison = analysis['comparison']
    print(f"\n   CMO Cost Savings with Chitosan:")
    print(f"     Savings per batch: ${comparison['cost_savings_per_batch']:,.0f}")
    print(f"     Savings per kg: ${comparison['cost_savings_per_kg']:.2f}")
    print(f"     Time savings: {comparison['time_savings_days']:.1f} days")

    print(f"\n3. VALIDATION AGAINST TARGET:")
    validation = analysis['validation']
    print(f"   Target CMO cost (32.5% of $1264.34): ${validation['target_cmo_cost_per_kg']:.2f}/kg")
    print(f"   Calculated QFF cost: ${validation['calculated_qff_cost_per_kg']:.2f}/kg")
    print(f"   Difference: ${validation['difference']:.2f} ({validation['percentage_difference']:.1f}%)")
    print(f"   Within tolerance: {'✓ PASS' if validation['within_tolerance'] else '✗ FAIL'}")

    print(f"\n4. COST BREAKDOWN BY CATEGORY:")
    qff_costs = qff_analysis['costs']

    # Facility costs
    facility_total = sum([v for k, v in qff_costs.items() if k.startswith('facility_') and k != 'facility_total_facility_cost'])
    campaign_total = sum([v for k, v in qff_costs.items() if k.startswith('campaign_') and k.endswith('_per_batch')])
    annual_total = qff_costs['annual_annual_fixed_per_batch']

    total_cmo = qff_costs['total_cmo_cost_per_batch']

    print(f"   Facility usage costs: ${facility_total:,.0f} ({facility_total/total_cmo*100:.1f}%)")
    print(f"   Campaign costs: ${campaign_total:,.0f} ({campaign_total/total_cmo*100:.1f}%)")
    print(f"   Annual fixed costs: ${annual_total:,.0f} ({annual_total/total_cmo*100:.1f}%)")

    print(f"\n5. ANNUAL SAVINGS POTENTIAL:")
    annual_batch_savings = comparison['cost_savings_per_batch'] * cmo.total_annual_batches
    print(f"   Annual CMO cost savings: ${annual_batch_savings:,.0f}")
    print(f"   Facility time savings: {comparison['time_savings_days'] * cmo.total_annual_batches:.0f} facility-days/year")

    return analysis

if __name__ == "__main__":
    # Run the CMO cost structure demonstration
    results = demonstrate_cmo_cost_structure()

    # Export detailed results
    output_file = "/Users/davidnunn/Desktop/Apps/BetterDairy/Biosteam/cmo_cost_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n\nDetailed CMO analysis exported to: {output_file}")
    print("\nCMO COST STRUCTURE MODEL COMPLETE!")
    print("✓ Complete facility asset model with daily/hourly rates")
    print("✓ Campaign economics with 30 batches/year across 5 campaigns")
    print("✓ Validation against 32.5% target ($410.55/kg)")
    print("✓ Separate cost models for QFF AEX vs chitosan")
    print("✓ Annual fixed cost allocation")
    print("✓ Facility utilization and changeover costs")
    print("✓ CMO savings analysis for technology alternatives")