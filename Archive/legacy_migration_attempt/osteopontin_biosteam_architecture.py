#!/usr/bin/env python3
"""
Modular BioSTEAM Architecture for Osteopontin Production
Implements SystemFactory patterns with parametric scaling and CMO pricing
"""

import biosteam as bst
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import json

# Configure BioSTEAM
bst.settings.set_thermo(['Water', 'Glucose', 'O2', 'CO2', 'Ethanol', 'Biomass', 'Osteopontin', 'NaCl', 'H2SO4'])

class ProductionScale(Enum):
    """Production scale categories"""
    PILOT = "pilot"          # 1,000-5,000 kg/year
    SMALL_COMMERCIAL = "small_commercial"  # 5,000-15,000 kg/year
    MEDIUM_COMMERCIAL = "medium_commercial"  # 15,000-35,000 kg/year
    LARGE_COMMERCIAL = "large_commercial"   # 35,000+ kg/year

class CMOPricingTier(Enum):
    """CMO pricing tier structure"""
    TIER_1 = "tier_1"  # <5,000 kg/year
    TIER_2 = "tier_2"  # 5,000-15,000 kg/year
    TIER_3 = "tier_3"  # 15,000-35,000 kg/year
    TIER_4 = "tier_4"  # 35,000+ kg/year

@dataclass
class ProcessParameters:
    """Comprehensive process parameters from Excel extraction"""

    # Fermentation parameters
    strain_titer: float = 10.0  # g/L
    working_volume: float = 105000  # L
    fermentation_time: float = 48  # hours
    turnaround_time: float = 24  # hours
    seed_train_duration: float = 10  # hours
    biomass_yield_glucose: float = 0.48  # g biomass/g glucose
    product_yield_biomass: float = 0.14286  # g product/g biomass

    # Separation parameters
    mf_efficiency: float = 0.9
    mf_flux: float = 45  # L/m2/h
    biomass_volume_fraction: float = 0.19048

    # Concentration parameters
    uf_efficiency: float = 0.95
    uf_concentration_factor: float = 20
    diafiltration_volumes: float = 5

    # Chromatography parameters
    chromatography_dynamic_capacity: float = 60  # g/L resin
    chromatography_yield: float = 0.8
    chromatography_buffer_cv_loading: float = 3.0  # CV of loading buffer
    chromatography_buffer_cv_wash: float = 5.0    # CV of wash buffer (5 CV as specified)
    chromatography_buffer_cv_elution: float = 5.0  # CV of elution buffer (5 CV as specified)

    # CEX Buffer specifications (implementing Excel gap)
    wash_buffer_nacl_concentration: float = 250.0  # mM NaCl
    wash_buffer_phosphate_concentration: float = 10.0  # mM phosphate
    elution_buffer_nacl_concentration: float = 375.0  # mM NaCl
    elution_buffer_phosphate_concentration: float = 10.0  # mM phosphate

    # Buffer preparation parameters
    nacl_molecular_weight: float = 58.44  # g/mol
    phosphate_molecular_weight: float = 137.99  # g/mol (Na2HPO4)
    buffer_preparation_excess: float = 1.1  # 10% excess for preparation
    buffer_storage_factor: float = 1.5  # Storage tank sizing factor

    # Drying parameters
    spray_dryer_efficiency: float = 0.98
    pre_drying_concentration_factor: float = 5

    # Cost parameters
    glucose_cost: float = 0.75  # $/kg
    yeast_extract_cost: float = 12.0  # $/kg
    peptone_cost: float = 15.0  # $/kg
    buffer_component_cost: float = 8.0  # $/kg
    resin_cost: float = 1000.0  # $/L
    resin_lifetime: float = 30  # cycles

    # Enhanced buffer cost parameters (addressing Excel gap)
    nacl_cost: float = 0.45  # $/kg
    phosphate_cost: float = 2.8  # $/kg (Na2HPO4)
    buffer_preparation_labor_cost: float = 50.0  # $/hr
    buffer_disposal_cost: float = 0.15  # $/L waste buffer
    buffer_neutralization_cost: float = 0.25  # $/L for pH adjustment

    # Utility costs
    electricity_cost: float = 0.15  # $/kWh
    steam_cost: float = 25.0  # $/MT
    water_cost: float = 2.0  # $/MT
    wfi_cost: float = 5.0  # $/MT

@dataclass
class CMOPricingStructure:
    """CMO pricing structure with volume tiers"""

    # Daily rates by tier ($/day)
    fermenter_daily_rates: Dict[CMOPricingTier, float] = field(default_factory=lambda: {
        CMOPricingTier.TIER_1: 75000,  # Premium for small volumes
        CMOPricingTier.TIER_2: 70000,  # 7% discount
        CMOPricingTier.TIER_3: 65000,  # 13% discount
        CMOPricingTier.TIER_4: 60000   # 20% discount
    })

    dsp_daily_rates: Dict[CMOPricingTier, float] = field(default_factory=lambda: {
        CMOPricingTier.TIER_1: 75000,
        CMOPricingTier.TIER_2: 70000,
        CMOPricingTier.TIER_3: 65000,
        CMOPricingTier.TIER_4: 60000
    })

    # Campaign setup costs by tier
    campaign_setup_costs: Dict[CMOPricingTier, float] = field(default_factory=lambda: {
        CMOPricingTier.TIER_1: 1500000,  # High setup for small campaigns
        CMOPricingTier.TIER_2: 1250000,  # 17% discount
        CMOPricingTier.TIER_3: 1000000,  # 33% discount
        CMOPricingTier.TIER_4: 750000    # 50% discount
    })

    # Minimum batch fees
    minimum_batch_fees: Dict[CMOPricingTier, float] = field(default_factory=lambda: {
        CMOPricingTier.TIER_1: 500000,
        CMOPricingTier.TIER_2: 450000,
        CMOPricingTier.TIER_3: 400000,
        CMOPricingTier.TIER_4: 350000
    })

class SystemFactory(ABC):
    """Abstract factory for creating process systems"""

    @abstractmethod
    def create_system(self, scale: ProductionScale, parameters: ProcessParameters) -> bst.System:
        pass

    @abstractmethod
    def get_tea(self, system: bst.System, scale: ProductionScale) -> bst.TEA:
        pass

class OsteopontinSystemFactory(SystemFactory):
    """Factory for creating osteopontin production systems"""

    def __init__(self, cmo_pricing: CMOPricingStructure = None):
        self.cmo_pricing = cmo_pricing or CMOPricingStructure()
        self.systems_cache = {}

    def create_system(self, scale: ProductionScale, parameters: ProcessParameters) -> bst.System:
        """Create complete osteopontin production system"""

        cache_key = f"{scale.value}_{hash(str(parameters))}"
        if cache_key in self.systems_cache:
            return self.systems_cache[cache_key]

        # Scale parameters based on production scale
        scaled_params = self._scale_parameters(parameters, scale)

        # Create system components
        flowsheet = bst.Flowsheet('osteopontin_production')
        bst.main_flowsheet.set_flowsheet(flowsheet)

        with flowsheet:
            system = self._create_process_system(scaled_params, scale)

        self.systems_cache[cache_key] = system
        return system

    def _scale_parameters(self, base_params: ProcessParameters, scale: ProductionScale) -> ProcessParameters:
        """Apply scaling factors based on production scale"""

        scaling_factors = {
            ProductionScale.PILOT: 0.3,
            ProductionScale.SMALL_COMMERCIAL: 1.0,
            ProductionScale.MEDIUM_COMMERCIAL: 2.5,
            ProductionScale.LARGE_COMMERCIAL: 5.0
        }

        factor = scaling_factors[scale]
        scaled = ProcessParameters()

        # Scale volume-dependent parameters
        scaled.working_volume = base_params.working_volume * factor

        # Apply economy of scale effects
        economy_factor = factor ** 0.7  # 0.7 power rule for equipment

        # Scale costs with economy factors
        scaled.glucose_cost = base_params.glucose_cost * (0.95 ** np.log10(factor))  # Volume discounts
        scaled.yeast_extract_cost = base_params.yeast_extract_cost * (0.97 ** np.log10(factor))
        scaled.peptone_cost = base_params.peptone_cost * (0.97 ** np.log10(factor))

        # Copy unchanged parameters
        for field_name, field_value in base_params.__dict__.items():
            if not hasattr(scaled, field_name) or getattr(scaled, field_name) is None:
                setattr(scaled, field_name, field_value)

        return scaled

    def _create_process_system(self, params: ProcessParameters, scale: ProductionScale) -> bst.System:
        """Create the complete process system"""

        # Create streams
        streams = self._create_streams(params)

        # Create unit operations
        units = self._create_unit_operations(params, streams, scale)

        # Connect the system
        system = bst.System('OsteopontinProduction',
                           path=units,
                           recycle=streams['recycle_water'])

        return system

    def _create_streams(self, params: ProcessParameters) -> Dict[str, bst.Stream]:
        """Create all process streams"""

        streams = {}

        # Feed streams
        streams['glucose'] = bst.Stream('glucose', Glucose=1000, units='kg/hr')
        streams['yeast_extract'] = bst.Stream('yeast_extract',
                                            Glucose=100, units='kg/hr')  # Placeholder composition
        streams['peptone'] = bst.Stream('peptone',
                                      Glucose=200, units='kg/hr')  # Placeholder composition
        streams['water'] = bst.Stream('water', Water=10000, units='kg/hr')
        streams['air'] = bst.Stream('air', O2=1000, units='kg/hr')

        # Process streams
        streams['fermentation_broth'] = bst.Stream('fermentation_broth')
        streams['clarified_broth'] = bst.Stream('clarified_broth')
        streams['concentrated_product'] = bst.Stream('concentrated_product')
        streams['purified_product'] = bst.Stream('purified_product')
        streams['dried_product'] = bst.Stream('dried_product')

        # Buffer streams - detailed CEX specifications (addressing Excel gap)
        # These will be calculated dynamically based on column volume in chromatography unit
        streams['wash_buffer'] = bst.Stream('wash_buffer', units='kg/hr')
        streams['elution_buffer'] = bst.Stream('elution_buffer', units='kg/hr')
        streams['buffer_nacl'] = bst.Stream('buffer_nacl', NaCl=1000, units='kg/hr')  # NaCl supply
        streams['buffer_phosphate'] = bst.Stream('buffer_phosphate', NaCl=100, units='kg/hr')  # Phosphate supply (placeholder composition)

        # Waste streams
        streams['cell_waste'] = bst.Stream('cell_waste')
        streams['buffer_waste'] = bst.Stream('buffer_waste')
        streams['wastewater'] = bst.Stream('wastewater')

        # Recycle stream
        streams['recycle_water'] = bst.Stream('recycle_water')

        return streams

    def _create_unit_operations(self, params: ProcessParameters, streams: Dict[str, bst.Stream],
                              scale: ProductionScale) -> List[bst.Unit]:
        """Create all unit operations"""

        units = []

        # 1. Fermentation system
        fermentor = FermentorWithScaling('R101',
                                       ins=[streams['glucose'], streams['yeast_extract'],
                                           streams['peptone'], streams['water'], streams['air']],
                                       outs=[streams['fermentation_broth']],
                                       params=params)
        units.append(fermentor)

        # 2. Cell separation - addressing Excel gap with alternatives
        cell_separator = FlexibleCellSeparation('S101',
                                              ins=streams['fermentation_broth'],
                                              outs=[streams['clarified_broth'], streams['cell_waste']],
                                              separation_type='microfiltration',  # Could be centrifuge, depth filtration
                                              params=params)
        units.append(cell_separator)

        # 3. Concentration system
        concentrator = bst.units.MultiStageEvaporator('E101',
                                                    ins=streams['clarified_broth'],
                                                    outs=[streams['concentrated_product']],
                                                    P=101325)
        units.append(concentrator)

        # 4. Buffer preparation system (addressing Excel gap)
        buffer_prep = BufferPreparationSystem('BP101',
                                             ins=[streams['buffer_nacl'], streams['buffer_phosphate'], streams['water']],
                                             outs=[streams['wash_buffer'], streams['elution_buffer']],
                                             params=params)
        units.append(buffer_prep)

        # 5. CEX Chromatography with detailed buffer calculations (addressing Excel gap)
        chromatography = EnhancedCEXChromatography('C101',
                                                  ins=[streams['concentrated_product'],
                                                      streams['wash_buffer'],
                                                      streams['elution_buffer']],
                                                  outs=[streams['purified_product'], streams['buffer_waste']],
                                                  params=params)
        units.append(chromatography)

        # 6. Final concentration and drying
        final_concentrator = bst.units.MultiStageEvaporator('E102',
                                                          ins=streams['purified_product'],
                                                          outs=['pre_drying_product'],
                                                          P=101325)
        units.append(final_concentrator)

        dryer = bst.units.SplitFlash('D101',
                                   ins=final_concentrator.outs[0],
                                   outs=[streams['dried_product'], streams['wastewater']],
                                   split={'Osteopontin': 0.98, 'Water': 0.02})
        units.append(dryer)

        return units

    def get_tea(self, system: bst.System, scale: ProductionScale) -> bst.TEA:
        """Create TEA with CMO pricing structure"""

        # Determine pricing tier based on annual production
        annual_production = self._estimate_annual_production(system, scale)
        pricing_tier = self._get_pricing_tier(annual_production)

        # Create custom TEA with CMO pricing
        tea = CMOTechnoEconomicAnalysis(system=system,
                                       cmo_pricing=self.cmo_pricing,
                                       pricing_tier=pricing_tier,
                                       scale=scale)

        return tea

    def _estimate_annual_production(self, system: bst.System, scale: ProductionScale) -> float:
        """Estimate annual production in kg/year (4.5K to 75K range)"""

        scale_to_production = {
            ProductionScale.PILOT: 4500,           # 4.5K kg/year minimum
            ProductionScale.SMALL_COMMERCIAL: 15000,  # 15K kg/year
            ProductionScale.MEDIUM_COMMERCIAL: 35000, # 35K kg/year
            ProductionScale.LARGE_COMMERCIAL: 75000   # 75K kg/year maximum
        }

        return scale_to_production[scale]

    def _get_pricing_tier(self, annual_production: float) -> CMOPricingTier:
        """Determine CMO pricing tier based on annual production"""

        if annual_production < 5000:
            return CMOPricingTier.TIER_1
        elif annual_production < 15000:
            return CMOPricingTier.TIER_2
        elif annual_production < 35000:
            return CMOPricingTier.TIER_3
        else:
            return CMOPricingTier.TIER_4

# Custom Unit Operations addressing Excel gaps

class FermentorWithScaling(bst.Unit):
    """Fermentor with scale-dependent parameters"""

    def __init__(self, ID='', ins=None, outs=(), thermo=None, params=None):
        super().__init__(ID, ins, outs, thermo)
        self.params = params or ProcessParameters()

    def _run(self):
        """Run fermentation with scale effects"""
        feed_glucose, feed_yeast, feed_peptone, water, air = self.ins
        broth = self.outs[0]

        # Calculate biomass production
        glucose_consumed = feed_glucose.F_mass  # kg/hr
        biomass_produced = glucose_consumed * self.params.biomass_yield_glucose
        product_produced = biomass_produced * self.params.product_yield_biomass

        # Set output composition
        broth.imass['Biomass'] = biomass_produced
        broth.imass['Osteopontin'] = product_produced
        broth.imass['Water'] = water.F_mass + feed_yeast.F_mass + feed_peptone.F_mass
        broth.imass['Glucose'] = glucose_consumed * 0.1  # Residual glucose

        broth.T = 310  # 37°C
        broth.P = 101325

class FlexibleCellSeparation(bst.Unit):
    """Flexible cell separation addressing Excel gap"""

    def __init__(self, ID='', ins=None, outs=(), separation_type='microfiltration', params=None):
        super().__init__(ID, ins, outs)
        self.separation_type = separation_type
        self.params = params or ProcessParameters()

    def _run(self):
        """Run separation based on type"""
        broth = self.ins[0]
        clarified, waste = self.outs

        if self.separation_type == 'microfiltration':
            efficiency = self.params.mf_efficiency
        elif self.separation_type == 'centrifuge':
            efficiency = 0.95  # Higher efficiency for centrifuge
        elif self.separation_type == 'depth_filtration':
            efficiency = 0.92  # Moderate efficiency
        else:
            efficiency = 0.9

        # Separate biomass
        clarified.copy_like(broth)
        clarified.imass['Biomass'] *= (1 - efficiency)
        clarified.imass['Osteopontin'] *= 0.95  # Some product loss

        waste.imass['Biomass'] = broth.imass['Biomass'] * efficiency
        waste.imass['Water'] = broth.imass['Water'] * 0.1  # Entrained water

class BufferPreparationSystem(bst.Unit):
    """Buffer preparation system with detailed salt and phosphate calculations"""

    def __init__(self, ID='', ins=None, outs=(), params=None):
        super().__init__(ID, ins, outs)
        self.params = params or ProcessParameters()
        self.wash_buffer_volume = 0  # Will be set by chromatography unit
        self.elution_buffer_volume = 0  # Will be set by chromatography unit

    def _run(self):
        """Prepare wash and elution buffers with specified compositions"""
        nacl_supply, phosphate_supply, water_supply = self.ins
        wash_buffer, elution_buffer = self.outs

        # Buffer volumes will be calculated based on column volume from chromatography
        # For now, use placeholder volumes (will be updated by chromatography unit)
        if self.wash_buffer_volume == 0:
            self.wash_buffer_volume = 1000  # L/hr placeholder
        if self.elution_buffer_volume == 0:
            self.elution_buffer_volume = 1000  # L/hr placeholder

        # Calculate wash buffer composition (250mM NaCl + 10mM phosphate)
        wash_nacl_kg = (self.params.wash_buffer_nacl_concentration / 1000 *
                       self.params.nacl_molecular_weight / 1000 *
                       self.wash_buffer_volume * self.params.buffer_preparation_excess)  # kg/hr

        wash_phosphate_kg = (self.params.wash_buffer_phosphate_concentration / 1000 *
                           self.params.phosphate_molecular_weight / 1000 *
                           self.wash_buffer_volume * self.params.buffer_preparation_excess)  # kg/hr

        # Calculate elution buffer composition (375mM NaCl + 10mM phosphate)
        elution_nacl_kg = (self.params.elution_buffer_nacl_concentration / 1000 *
                          self.params.nacl_molecular_weight / 1000 *
                          self.elution_buffer_volume * self.params.buffer_preparation_excess)  # kg/hr

        elution_phosphate_kg = (self.params.elution_buffer_phosphate_concentration / 1000 *
                              self.params.phosphate_molecular_weight / 1000 *
                              self.elution_buffer_volume * self.params.buffer_preparation_excess)  # kg/hr

        # Set wash buffer stream
        wash_buffer.imass['NaCl'] = wash_nacl_kg
        wash_buffer.imass['H2SO4'] = wash_phosphate_kg  # Using H2SO4 as phosphate placeholder
        wash_buffer.imass['Water'] = self.wash_buffer_volume  # kg/hr (assuming density ~1 kg/L)
        wash_buffer.T = 298.15  # 25°C
        wash_buffer.P = 101325

        # Set elution buffer stream
        elution_buffer.imass['NaCl'] = elution_nacl_kg
        elution_buffer.imass['H2SO4'] = elution_phosphate_kg  # Using H2SO4 as phosphate placeholder
        elution_buffer.imass['Water'] = self.elution_buffer_volume  # kg/hr
        elution_buffer.T = 298.15  # 25°C
        elution_buffer.P = 101325

        # Track raw material consumption
        self.nacl_consumed = wash_nacl_kg + elution_nacl_kg
        self.phosphate_consumed = wash_phosphate_kg + elution_phosphate_kg

class EnhancedCEXChromatography(bst.Unit):
    """Enhanced CEX chromatography with detailed buffer volume calculations"""

    def __init__(self, ID='', ins=None, outs=(), params=None):
        super().__init__(ID, ins, outs)
        self.params = params or ProcessParameters()

    def _run(self):
        """Run CEX chromatography with detailed buffer calculations"""
        feed, wash_buffer, elution_buffer = self.ins
        product, waste = self.outs

        # Calculate column volume based on protein load and binding capacity
        protein_load = feed.imass['Osteopontin']  # kg/hr
        if protein_load <= 0:
            protein_load = 0.1  # Minimum for calculation

        # Column volume calculation (addressing Excel gap)
        # Convert binding capacity from g/L to kg/m3: 60 g/L = 60 kg/m3
        column_volume_m3 = protein_load / (self.params.chromatography_dynamic_capacity)  # m3
        column_volume_L = column_volume_m3 * 1000  # L

        # Calculate buffer volumes based on column volumes (Excel specifications)
        wash_buffer_volume = column_volume_L * self.params.chromatography_buffer_cv_wash  # 5 CV
        elution_buffer_volume = column_volume_L * self.params.chromatography_buffer_cv_elution  # 5 CV

        # Update buffer preparation system with calculated volumes
        # This creates a coupling between units that would be handled by the system solver
        buffer_prep = None
        for unit in self.flowsheet.unit:
            if hasattr(unit, 'wash_buffer_volume') and unit.ID == 'BP101':
                buffer_prep = unit
                break

        if buffer_prep:
            buffer_prep.wash_buffer_volume = wash_buffer_volume
            buffer_prep.elution_buffer_volume = elution_buffer_volume

        # Set product stream with yield
        product.copy_like(feed)
        product.imass['Osteopontin'] *= self.params.chromatography_yield
        product.imass['Biomass'] = 0  # Biomass removed in chromatography
        product.imass['Glucose'] *= 0.1  # Most impurities removed

        # Calculate waste stream (spent buffers + impurities + lost product)
        total_buffer_volume = wash_buffer_volume + elution_buffer_volume  # L/hr
        waste.imass['Water'] = total_buffer_volume  # kg/hr (assuming density ~1 kg/L)

        # Salt content from buffers
        total_nacl = (wash_buffer.imass['NaCl'] + elution_buffer.imass['NaCl'] if
                     wash_buffer.imass['NaCl'] > 0 else
                     total_buffer_volume * 0.025)  # ~2.5% salt content as fallback

        waste.imass['NaCl'] = total_nacl
        waste.imass['H2SO4'] = wash_buffer.imass['H2SO4'] + elution_buffer.imass['H2SO4']

        # Lost product and impurities
        waste.imass['Osteopontin'] = feed.imass['Osteopontin'] * (1 - self.params.chromatography_yield)
        waste.imass['Biomass'] = feed.imass['Biomass']  # All biomass to waste
        waste.imass['Glucose'] = feed.imass['Glucose'] * 0.9  # Most glucose to waste

        waste.T = 298.15  # 25°C
        waste.P = 101325

        # Store operational parameters for costing
        self.column_volume = column_volume_L
        self.wash_buffer_volume = wash_buffer_volume
        self.elution_buffer_volume = elution_buffer_volume
        self.total_buffer_volume = total_buffer_volume

class CMOTechnoEconomicAnalysis(bst.TEA):
    """Custom TEA with CMO pricing structure"""

    def __init__(self, system, cmo_pricing: CMOPricingStructure,
                 pricing_tier: CMOPricingTier, scale: ProductionScale):
        super().__init__(system)
        self.cmo_pricing = cmo_pricing
        self.pricing_tier = pricing_tier
        self.scale = scale

    def _DPI(self):
        """Direct permanent investment (equipment costs)"""
        # For CMO, this represents facility reservation costs
        return self.cmo_pricing.campaign_setup_costs[self.pricing_tier]

    def _TDC(self):
        """Total direct costs"""
        return self._DPI()

    def _FCI(self):
        """Fixed capital investment"""
        return self._TDC()

    def _FOC(self):
        """Fixed operating costs (CMO daily rates)"""

        # Calculate operating time
        operating_days_per_year = 300  # Typical CMO utilization

        # Get tier-specific daily rates
        fermenter_rate = self.cmo_pricing.fermenter_daily_rates[self.pricing_tier]
        dsp_rate = self.cmo_pricing.dsp_daily_rates[self.pricing_tier]

        annual_fermenter_cost = fermenter_rate * operating_days_per_year * 0.5  # 50% fermentation time
        annual_dsp_cost = dsp_rate * operating_days_per_year * 0.5  # 50% DSP time

        return annual_fermenter_cost + annual_dsp_cost

    def _VOC(self):
        """Variable operating costs (raw materials + buffer costs)"""
        # Calculate raw material costs from flowsheet
        annual_raw_material_cost = 0
        annual_buffer_cost = 0
        annual_buffer_disposal_cost = 0

        # Get operating hours per year
        operating_hours_per_year = 8760 * 0.85  # 85% uptime

        try:
            # Find buffer preparation and chromatography units
            buffer_prep = None
            chromatography = None

            for unit in self.system.units:
                if hasattr(unit, 'nacl_consumed') and unit.ID == 'BP101':
                    buffer_prep = unit
                elif hasattr(unit, 'total_buffer_volume') and unit.ID == 'C101':
                    chromatography = unit

            # Calculate buffer preparation costs
            if buffer_prep:
                # NaCl costs
                annual_nacl_cost = (buffer_prep.nacl_consumed * operating_hours_per_year *
                                  buffer_prep.params.nacl_cost)

                # Phosphate costs
                annual_phosphate_cost = (buffer_prep.phosphate_consumed * operating_hours_per_year *
                                       buffer_prep.params.phosphate_cost)

                # Buffer preparation labor
                buffer_prep_time_per_batch = 2  # hours per batch
                batches_per_year = operating_hours_per_year / 72  # Assuming 72-hour cycles
                annual_buffer_labor_cost = (batches_per_year * buffer_prep_time_per_batch *
                                          buffer_prep.params.buffer_preparation_labor_cost)

                annual_buffer_cost = annual_nacl_cost + annual_phosphate_cost + annual_buffer_labor_cost

            # Calculate buffer disposal costs
            if chromatography:
                # Disposal and neutralization costs
                annual_buffer_waste_volume = (chromatography.total_buffer_volume *
                                            operating_hours_per_year)  # L/year

                annual_disposal_cost = (annual_buffer_waste_volume *
                                      chromatography.params.buffer_disposal_cost)

                annual_neutralization_cost = (annual_buffer_waste_volume *
                                            chromatography.params.buffer_neutralization_cost)

                annual_buffer_disposal_cost = annual_disposal_cost + annual_neutralization_cost

            # Base raw materials (glucose, yeast extract, peptone)
            # This would normally be calculated from actual feed flows
            # Using scaled estimates based on production scale
            scale_factors = {
                ProductionScale.PILOT: 1000000,
                ProductionScale.SMALL_COMMERCIAL: 2500000,
                ProductionScale.MEDIUM_COMMERCIAL: 6000000,
                ProductionScale.LARGE_COMMERCIAL: 12000000
            }

            annual_raw_material_cost = scale_factors.get(self.scale, 2500000)

        except Exception as e:
            # Fallback calculation if system analysis fails
            print(f"Warning: Could not calculate detailed buffer costs: {e}")
            annual_buffer_cost = 500000  # $500K estimated buffer costs
            annual_buffer_disposal_cost = 200000  # $200K estimated disposal costs
            annual_raw_material_cost = 2000000  # $2M estimated raw materials

        total_voc = annual_raw_material_cost + annual_buffer_cost + annual_buffer_disposal_cost

        # Store cost breakdown for analysis
        self.annual_raw_material_cost = annual_raw_material_cost
        self.annual_buffer_cost = annual_buffer_cost
        self.annual_buffer_disposal_cost = annual_buffer_disposal_cost
        self.buffer_cost_percentage = (annual_buffer_cost + annual_buffer_disposal_cost) / total_voc * 100

        return total_voc

def main():
    """Demonstration of the modular architecture"""

    print("="*80)
    print("OSTEOPONTIN BIOSTEAM MODULAR ARCHITECTURE DEMONSTRATION")
    print("="*80)

    # Create factory and parameters
    factory = OsteopontinSystemFactory()
    base_params = ProcessParameters()

    # Create systems for different scales
    scales = [ProductionScale.PILOT, ProductionScale.SMALL_COMMERCIAL,
              ProductionScale.MEDIUM_COMMERCIAL, ProductionScale.LARGE_COMMERCIAL]

    results = {}

    for scale in scales:
        print(f"\nCreating system for {scale.value} scale...")

        # Create system
        system = factory.create_system(scale, base_params)

        # Create TEA
        tea = factory.get_tea(system, scale)

        # Store results
        results[scale.value] = {
            'system': system,
            'tea': tea,
            'annual_production': factory._estimate_annual_production(system, scale),
            'pricing_tier': factory._get_pricing_tier(factory._estimate_annual_production(system, scale)).value
        }

        print(f"  Annual production: {results[scale.value]['annual_production']:,.0f} kg/year")
        print(f"  CMO pricing tier: {results[scale.value]['pricing_tier']}")

    print("\n" + "="*80)
    print("ARCHITECTURE FEATURES IMPLEMENTED:")
    print("="*80)

    features = [
        "✓ Modular SystemFactory pattern for different scales",
        "✓ Parametric scaling with economy of scale effects",
        "✓ Non-linear CMO pricing with volume tiers",
        "✓ Detailed IEX chromatography buffer calculations",
        "✓ Flexible cell separation technologies",
        "✓ Scale-dependent parameter modeling",
        "✓ Process gap identification and filling",
        "✓ Custom TEA with CMO cost structures"
    ]

    for feature in features:
        print(feature)

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Validate against Excel baseline (±5% tolerance)")
    print("2. Implement uncertainty analysis and Monte Carlo")
    print("3. Add process optimization capabilities")
    print("4. Create scenario comparison tools")
    print("5. Develop user interface for parameter adjustment")

    return results

if __name__ == "__main__":
    results = main()