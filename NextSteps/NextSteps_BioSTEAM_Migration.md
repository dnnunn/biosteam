# BioSTEAM Migration Next Steps

## Short-Term Build Targets
- Excel parity + baseline toggle complete. Next focus: USP3 (cell removal) stage with interchangeable BioSTEAM units reflecting industry practice.
- Immediate tasks for cell-removal module:
  1. Create BioSTEAM classes for disc-stack centrifuge, depth filtration, MF-TFF (pre/post-centrifuge), and continuous centrifuge using specs in ``Cell Removal Specs.md``.
  2. Add a ``cell_removal`` section to ``baseline_defaults.yaml`` capturing feed properties, method selection, and per-unit parameters (Σ area, flux, membrane cost, etc.).
  3. Extend ``build_front_end_section`` to route the fermentation effluent through the selected method(s); keep Excel mode using the historical microfiltration path until new units are toggled on.
  4. Surface stream/cost metrics in ``compare_front_end.py`` so Excel vs baseline differences are obvious (e.g., clarified supernatant, wet cell cake, depth filter losses).
- Optional (if time permits): implement an auto-selection heuristic based on scale and solids (disc stack + depth as default for ≥100 m³) while keeping manual overrides in the config.

## Validation Workflow
- Generate a comparison report that juxtaposes BioSTEAM results with Excel KPIs (cost per kg, batch cost, annual production cost) targeting ±5–10% deviation.
- Extend the report to break out chromatography resin, buffer, and CMO cost contributors using the same grouping found in ``Final Costs``.

## Future Enhancements
- Auto-selection logic for cell removal (use scale + solids to recommend disc stack vs MF-TFF vs alternate centrifuge).
- Campaign-based economic toggles (e.g., PROJ02 sensitivity) after baseline validation to explore alternative CMO pricing structures.
- Install missing runtime dependencies (e.g., ``numba``) so ``biosteam`` imports succeed; current sandbox blocks network installs, so resolve this manually on the host environment before attaching full unit builders.

## Implementation Notes
- ``migration.module_registry.ModuleRegistry`` and the data builders are in place—extend them as new workbook modules/options appear.
- ``SeedTrainBioreactor`` now wraps the NREL batch model; use a similar pattern when upgrading fermentation and downstream stages so plan data flows straight into real BioSTEAM units.
- ``ExcelModuleDefaults`` merges module defaults with option rows and retains source-row metadata; lean on it to chase Excel discrepancies without re-reading the sheet manually.
- ``migration/scripts/compare_front_end.py`` is the regression harness—keep it aligned with whatever metrics each stage exposes so deltas surface immediately.
