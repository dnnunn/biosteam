# Module Mapping Plan for Excel v44

This document captures the current understanding of the Excel module defaults (v44) and how they will translate into BioSTEAM unit/facility builders. Values below come from `migration.excel_defaults.ExcelModuleDefaults` applied to `/Users/davidnunn/Desktop/Apps/TEAM/Revised Model_15052025v44.xlsx`.

## Baseline Module Sequence

```
USP00 (USP00a) → USP01 (USP01a) → USP02 (USP02a) →
DSP01 (DSP01a) → DSP02 (DSP02a) → DSP03 (DSP03a) → DSP05 (DSP05a) →
PROJ00 (PROJ00c) → PROJ01 (PROJ01a) → PROJ02 (PROJ02a)
```

The migration scaffolding (`migration.baseline_system.DEFAULT_MODULE_SEQUENCE`) already pulls these modules and exposes their parameters through `ModuleData` instances. The next step is wiring true BioSTEAM factories for each entry. The sections below summarise the Excel coverage and proposed BioSTEAM mappings, along with follow-up tasks.

> **Note:** Optional module variants that lack Excel parameters are captured in
> `migration/default_overrides.yaml`. `register_baseline_unit_builders` applies
> these overrides when present so we always produce complete `UnitPlan` specs.

## Upstream Processing

### USP00 — Fermentation
- **Excel options:** `USP00a` (baseline), `USP00b`, `USP00c`
- **Key parameters (baseline):** turnaround time (24 h), yields (OD→biomass 0.4, biomass→product 0.3), wet cell density 105 g/L, antifoam dosage.
- **Candidate BioSTEAM units:** `biosteam.units.AeratedBioreactor` or `biosteam.units.BatchBioreactor` for the production fermentor; possible use of `biosteam.units.Fermentation` convenience wrappers.
- **Implementation notes:**
  1. Define a `build_usp00_fermentor(config)` that instantiates a batch fermentor, sets cycle time via `turnaround_time_hours`, and configures yields and antifoam consumption.
  2. Support additional Excel variants (`USP00b`, `USP00c`) by branching on `ModuleKey.option` once their parameter differences are analysed.

### USP01 — Seed Train
- **Excel options:** `USP01a` (baseline), cross-reference `USP00c` for shared defaults.
- **Key parameters:** yeast extract/peptone concentrations and unit costs.
- **Candidate BioSTEAM units:** `biosteam.units.SeedTrain` (if available) or a chain of `MixTank` + `BatchBioreactor` sized via utilities.
- **Implementation notes:**
  1. Start with a placeholder returning a data object for mass balance verification.
  2. Investigate reuse of templates in `Bioindustrial-Park/biorefineries/BDO/` for seed trains.

### USP02 — Microfiltration Harvest
- **Excel options:** `USP02a` (baseline), `USP02c` (alternative efficiency set).
- **Key parameters:** membrane area (80 m²), flux 45 L/m²·h, dilution volume 15 m³, target product loss 10%, membrane life/cost.
- **Candidate BioSTEAM units:** `biosteam.units.CrossFlowFilter` (or `Microfiltration` helper) with membrane replacement economics.
- **Implementation notes:**
  1. Convert flux and area into processing time to size the unit.
  2. Track membrane replacement via `Unit.add_OPEX` using cost/lifetime.

## Downstream Processing

### DSP01 — UF/DF
- **Excel options:** `DSP01a` only.
- **Key parameters:** membrane area 150 m², flux 20 L/m²·h, diafiltration volumes (5), efficiency 95%.
- **BioSTEAM mapping:** use `biosteam.units.MembraneEvaporator` or repurpose `CrossFlowFilter` for UF/DF; ensure diafiltration loop is modelled (could leverage `Recycle` + `MixTank`).
- **Tasks:**
  1. Determine whether an existing BioSTEAM membrane unit can handle both UF and DF in one step; otherwise create a custom unit subclass.
  2. Parameterise permeate removal and diafiltration water usage.

### DSP02 — Chromatography
- **Excel options:** `DSP02a` (baseline only in defaults).
- **Key parameters:** dynamic binding capacity 60 g/L, 5 CV elution, wash/strip molarity, resin cost $1000/L, lifetime 30 cycles, buffer recipes.
- **BioSTEAM mapping:** extend/instantiate `biosteam.units.Chromatography` from `Bioindustrial-Park` modules or build a custom unit capturing cycle scheduling, resin replacement, and buffer prep streams.
- **Tasks:**
  1. Create a builder that returns a struct encapsulating resin cycle economics (mass balance, buffer volumes) before wiring a full unit.
  2. Use `ChromatographySpecs.resin_cost_per_batch()` helper to calculate consumables.
  3. For future phases, add support for alternative options (e.g., chitosan) as additional ModuleKeys.

### DSP03 — Pre-Drying TFF/UFF
- **Excel options:** `DSP03a` (baseline), `DSP03b` (alternate flux/area set).
- **Key parameters:** efficiency 95%, flux 35 L/m²·h, membrane area 35 m², concentration factor 5.
- **BioSTEAM mapping:** similar to DSP01; can reuse the same membrane unit builder with different parameters.
- **Tasks:** implement a shared membrane filtering builder that accepts the `ModuleData` fields and configures a BioSTEAM unit.

### DSP05 — Spray Drying
- **Excel options:** `DSP05a` only.
- **Key parameters:** dryer efficiency 98%, capacity 150 kg/h, target recovery 80%, final solids 15%.
- **BioSTEAM mapping:** `biosteam.units.SprayDryer` exists and can be parameterised with throughput, moisture removal, and energy demand.
- **Tasks:** map Excel capacity to residence time; integrate with PROJ utilities for steam/electricity pricing.

## Project / Financial Modules

### PROJ00 — Campaign Scheduling
- **Excel options:** `PROJ00c` baseline; Excel also provides `DSP00a` rows that feed into campaign defaults.
- **Data:** annual production target (10,000 kg), 6 batches per campaign, 5 campaigns/year.
- **Use in BioSTEAM:** feed into system-level scheduling objects (e.g., `SystemFactory` throughput scaling). Provide this as metadata rather than a unit.
- **Tasks:**
  1. Store schedule data in a dataclass (`CampaignSchedule`) and wire into TEA setup (batch time, annual uptime).
  2. Evaluate how the Excel `DSP00a` rows interplay with PROJ00; confirm whether they should seed upstream modules.

### PROJ01 — Utility Rates
- **Excel options:** `PROJ01a` (baseline), `PROJ01b`, `PROJ01c` (alternatives).
- **Data:** electricity $0.15/kWh, steam $25/MT, compressed air $0.02 per unit.
- **BioSTEAM mapping:** configure `HeatUtility`/`PowerUtility` globals (`biosteam.settings`).
- **Tasks:**
  1. Implement a builder that updates global utility rates and returns a record noting the applied tariff set.
  2. For options b/c, stash the alternative pricing to allow scenario toggles.

### PROJ02 — CMO Pricing
- **Excel options:** `PROJ02a` only at defaults layer; Excel contains comprehensive pricing fields.
- **Data highlights:** campaign setup $250k, daily rates (fermenter/DSP), overhead markup, documentation/QA fees, discounts.
- **BioSTEAM mapping:** integrate with TEA using `ModuleRegistry` entry that constructs a `CMOPricingSpecs` dataclass; later phases will turn this into cost correlations attached to systems.
- **Tasks:**
  1. Convert the dataclass into helper functions that compute per-batch and annual CMO fees for TEA.
  2. Plan extension for tiered pricing once scale toggles are introduced.

## Additional Excel Options to Analyse

- **DSP00b:** currently not in the baseline sequence; investigate how it affects PROJ00 defaults.
- **USP00b / USP00c:** likely alternative fermentation modes (e.g., glycerol feed vs glucose). Need to extract differentiating parameters.
- **USP02c / DSP03b / PROJ01b-c:** scenario variants for efficiency or utility pricing; ensure the registry gracefully returns placeholders until full implementations exist.

## Immediate Follow-Up Tasks

1. **Diagnostics:** add a CLI helper (e.g., `migration/scripts/dump_defaults.py`) to print module data for any key, smoothing future validation.
2. **Builder Stubs:** extend the new `migration.unit_builders.register_baseline_unit_builders` to cover the remaining modules. USP00/USP01 now return `UnitPlan` objects with derived metrics; replicate the pattern for USP02, DSP01, etc.
3. **Unit Wiring:** prioritise USP00, USP02, DSP01, DSP02, DSP05 for real BioSTEAM units since they dominate mass balance and cost. Use `Bioindustrial-Park` examples as references for unit parameters.
4. **Validation Hooks:** after each builder is implemented, connect it to regression tests comparing BioSTEAM outputs to Excel baselines (cost/kg, resin usage, buffer volumes).

This plan will evolve as we implement builders; update this file after each module is wired or when new Excel options are characterised.
