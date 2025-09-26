# Archive Reference Index

Curated catalogue of legacy migration assets retained under `Archive/legacy_migration_attempt/` for future reference. Titles reflect the original work product from the January–May 2025 migration effort.

## Analytical Reports

- `COMPLETE_MODULAR_ANALYSIS_REPORT.md` — End-to-end narrative of the modular migration strategy, including timeline, assumptions, and validation checkpoints.
- `COMPREHENSIVE_BIOSTEAM_MAPPING_SUMMARY.md` — Executive summary of the osteopontin parameter mapping with cost deltas for the QFF AEX vs. chitosan alternative flowsheets.
- `MIGRATION_ANALYSIS_SUMMARY.md` — High-level analysis of Excel gaps, CMO pricing research, and the proposed SystemFactory architecture.
- `INSTALLATION_SUMMARY.md` — Snapshot of BioSTEAM installation attempts, environment hurdles, and mitigation steps captured during early bring-up.

## Scripts and Notebooks

- `biosteam_modular_framework.py`, `systemfactory_comparative_framework.py` — Early modular architecture prototypes for assembling osteopontin flowsheets.
- `osteopontin_biosteam_architecture.py`, `osteopontin_biosteam_comprehensive.py` — Legacy SystemFactory workflows predating the current `migration/` package.
- `chitosan_coacervation_model.py`, `qff_aex_chromatography_model.py` — Comparative models exploring downstream technology swaps.
- `comprehensive_excel_extractor.py`, `excel_modular_analysis.py`, `updated_excel_analyzer.py` — Exploratory tooling for extracting and normalizing Excel parameters.

## Data & Results Assets

- `excel_extraction_results/` — JSON and text exports of the 2025 parameter harvesting run (complete database, cost breakdowns, critical drivers, and outstanding questions).
- `architecture_demonstration_results.csv` — Scenario matrix showing scale/technology cost impacts used in early presentations.
- `biosteam_parameter_mapping.json`, `corrected_biosteam_framework.*` — Serialized parameter maps aligning Excel defaults with BioSTEAM inputs.
- `chitosan_analysis_results.json`, `modular_analysis_results.json`, `final_cost_validation.json` — Result files capturing validation metrics for alternative process concepts.

## Supporting Utilities

- `biosteam_wrapper.py` — Compatibility helper targeting legacy Python environments.
- `cmo_cost_structure.py`, `cost_reconciliation_analysis.py`, `cost_validation_final.py` — One-off economic calculators used to reconcile Excel and BioSTEAM outputs.
- `excel_gap_analysis.py` (plus `_report.json`) — Original gap audit preceding the streamlined tooling in `migration/`.

All items remain read-only; new development should prefer the `migration/` package and current documentation, using these archived files solely for historical context or data backfill.
