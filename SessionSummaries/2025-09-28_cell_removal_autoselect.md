# 2025-09-28 – Cell Removal Auto-Selection & Overrides

## Context
- Implemented BioSTEAM-native clarification units (disc-stack, depth filtration, MF-TFF) per `Cell Removal Specs.md`.
- Added auto-selection logic for cell removal routes based on feed volume, solids %, turbidity targets, and membrane requirements.
- Established warning system for overrides that violate scale constraints (e.g., membrane-only at high solids).
- Created `migration/overrides/micro_only.yaml` for Excel-style parity checks without touching baseline defaults.
- Updated baseline loader to deep-merge override YAML with canonical defaults.
- Implemented DSP01 concentration variants (UF concentration, DF, SPTFF, continuous TFF) per `Concentration options.md`, including auto-selection and override warnings.

## Key Commands
```bash
python -m migration.scripts.compare_front_end \
  --mode baseline \
  --workbook /Users/davidnunn/Desktop/Apps/Biosteam/BaselineModel.xlsx

python -m migration.scripts.compare_front_end \
  --mode baseline \
  --workbook /Users/davidnunn/Desktop/Apps/Biosteam/BaselineModel.xlsx \
  --baseline-config migration/overrides/micro_only.yaml
```

## Next Ideas
- Extend auto-selection template to fermentation media (rich vs. defined) and carbon source switching.
- When user forces unsuitable routes, consider automatic fallbacks with explicit confirmation.
- Mirror this pattern for downstream polishing and chromatography options as the migration continues.

### Fermentation Carbon Source Overrides (2025-09-28)
- Added override files for fermentation scenarios:
  - `fermentation_glucose_rich.yaml`
  - `fermentation_glucose_defined.yaml`
  - `fermentation_glycerol_defined.yaml`
  - `fermentation_molasses_rich.yaml`
- Each override carries explicit feed volumes, carbon totals, and a `media_type` field (rich vs defined) along with a `yield_proxy` flag capturing the current industry proxy assumption.
- Recovery proxies (product/bio yields, recovery fractions) are placeholders derived from literature/CMO data until lab results arrive.
