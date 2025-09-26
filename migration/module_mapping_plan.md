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
- **Status:** UnitPlan covers cycle time, product yield on glucose, and override-driven assumptions for `USP00b/USP00c`.
- **Next steps:** wire a BioSTEAM fermentor that consumes media streams and honours the derived cycle time.

### USP01 — Seed Train
- **Excel options:** `USP01a` (baseline), cross-reference `USP00c` for shared defaults.
- **Key parameters:** yeast extract/peptone concentrations and unit costs.
- **Status:** UnitPlan provides nutrient concentration totals and flags missing data; overrides fill the shared `USP00c` defaults.
- **Next steps:** implement a reusable BioSTEAM seed-train block (e.g., cascade of `MixTank`/`BatchBioreactor`).

### USP02 — Microfiltration Harvest
- **Excel options:** `USP02a` (baseline), `USP02c` (alternative efficiency set).
- **Key parameters:** membrane area (80 m²), flux 45 L/m²·h, dilution volume 15 m³, target product loss 10%, membrane life/cost.
- **Status:** UnitPlan now reports throughput (flux × area), membrane replacement cost, and dilution volume (with overrides for `USP02c`).
- **Next steps:** instantiate a BioSTEAM microfiltration unit and attach membrane replacement economics.

## Downstream Processing

### DSP01 — UF/DF
- **Excel options:** `DSP01a` baseline; override profile added for `DSP01b` scenario.
- **Key parameters:** membrane area 150 m², flux 20 L/m²·h, diafiltration volumes (5), efficiency 95%.
- **Status:** UnitPlan captures throughput, diafiltration volumes, and membrane replacement OPEX.
- **Next steps:** wire UF/DF module (or custom membrane unit) and close diafiltration water loops.

### DSP02 — Chromatography
- **Excel options:** `DSP02a` (baseline only in defaults).
- **Key parameters:** dynamic binding capacity 60 g/L, 5 CV elution, wash/strip molarity, resin cost $1000/L, lifetime 30 cycles, buffer recipes.
- **Status:** UnitPlan computes resin cost per batch and aggregates total buffer bed volumes for TEA integration.
- **Next steps:** connect to a chromatography cycle model and buffer preparation units; add alternative technology options in future phases.

### DSP03 — Pre-Drying TFF/UFF
- **Excel options:** `DSP03a` (baseline), `DSP03b` (alternate flux/area set).
- **Key parameters:** efficiency 95%, flux 35 L/m²·h, membrane area 35 m², concentration factor 5.
- **Status:** UnitPlan targets throughput and efficiency, applying overrides for the alternate scenario.
- **Next steps:** reuse UF/DF membrane wiring to finalise the pre-drying stage.

### DSP05 — Spray Drying
- **Excel options:** `DSP05a` only (overrides supply scenario defaults).
- **Key parameters:** dryer efficiency 98%, capacity 150 kg/h, target recovery 80%, final solids 15%.
- **Status:** UnitPlan exposes dryer capacity and solids concentration with optional override support.
- **Next steps:** instantiate `biosteam.units.SprayDryer` and link to utility pricing from PROJ01.

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

1. **Diagnostics:** use `python -m migration.scripts.dump_defaults` to inspect module data and UnitPlans (supports inactive options via `--include-inactive`).
2. **Unit Wiring:** convert the established UnitPlans (USP00–DSP05) into fully fledged BioSTEAM unit factories, starting with fermentation, microfiltration, UF/DF, chromatography, and spray drying.
3. **Validation Hooks:** after each builder is implemented, connect it to regression tests comparing BioSTEAM outputs to Excel baselines (cost/kg, resin usage, buffer volumes).

This plan will evolve as we implement builders; update this file after each module is wired or when new Excel options are characterised.
