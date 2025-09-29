# 2025-09-28 – Cell Removal Auto-Selection & Overrides

## Context
- Implemented BioSTEAM-native clarification units (disc-stack, depth filtration, MF-TFF) per `Cell Removal Specs.md`.
- Added auto-selection logic for cell removal routes based on feed volume, solids %, turbidity targets, and membrane requirements.
- Established warning system for overrides that violate scale constraints (e.g., membrane-only at high solids).
- Created `migration/overrides/micro_only.yaml` for Excel-style parity checks without touching baseline defaults.
- Updated baseline loader to deep-merge override YAML with canonical defaults.

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
