# BioSTEAM Migration Next Steps

## Short-Term Build Targets
- Excel-driven parity pass is complete. Next phase: add a BioSTEAM baseline mode that can run without direct Excel overrides, then progressively turn on physics-based behavior per unit.
- Immediate tasks for the BioSTEAM baseline toggle:
  1. Introduce a configuration layer (YAML/JSON) that captures default plan/spec values for each stage when Excel data is not injected.
  2. Update ``build_front_end_section`` (and plan builders) to accept ``mode="excel"`` vs ``mode="baseline"``; keep the CLI defaulting to Excel parity.
  3. Seed the baseline config with values matching Excel to keep regression green, then iterate to BioSTEAM defaults.
- ``tests/opn/test_opn_front_end.py`` and ``migration/scripts/compare_front_end.py`` should be extended later to emit both Excel vs Excel-driven and Excel vs BioSTEAM-baseline deltas once the toggle exists.
- Any workbook assumptions unearthed during baseline wiring (e.g., inoculation ratios, buffer recipes) should be logged so we know which values need literature/industry references during the physics-based phase.

## Validation Workflow
- Generate a comparison report that juxtaposes BioSTEAM results with Excel KPIs (cost per kg, batch cost, annual production cost) targeting ±5–10% deviation.
- Extend the report to break out chromatography resin, buffer, and CMO cost contributors using the same grouping found in ``Final Costs``.

## Future Enhancements
- Expand the registry to cover non-default module options and scenario toggles once the baseline matches Excel outputs.
- Introduce campaign-based economic toggles (e.g., PROJ02 sensitivity) after baseline validation to explore alternative CMO pricing structures.
- Install missing runtime dependencies (e.g., ``numba``) so ``biosteam`` imports succeed; current sandbox blocks network installs, so resolve this manually on the host environment before attaching full unit builders.

## Implementation Notes
- ``migration.module_registry.ModuleRegistry`` and the data builders are in place—extend them as new workbook modules/options appear.
- ``SeedTrainBioreactor`` now wraps the NREL batch model; use a similar pattern when upgrading fermentation and downstream stages so plan data flows straight into real BioSTEAM units.
- ``ExcelModuleDefaults`` merges module defaults with option rows and retains source-row metadata; lean on it to chase Excel discrepancies without re-reading the sheet manually.
- ``migration/scripts/compare_front_end.py`` is the regression harness—keep it aligned with whatever metrics each stage exposes so deltas surface immediately.
