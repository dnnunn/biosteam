# BioSTEAM Migration Next Steps

## Short-Term Build Targets
- Implement a module registry that maps Excel module keys to BioSTEAM unit factory callables (start with USP00/01/02, DSP01/02/03/05, PROJ00/01/02).
- Develop ``build_baseline_system(config)`` by refactoring the minimal subset of ``Archive/legacy_migration_attempt/osteopontin_biosteam_architecture.py`` to use the new registry and the ``ExcelModuleDefaults`` loader.
- Snapshot baseline KPIs with ``python -m migration.scripts.export_baseline_metrics`` (writes ``tests/opn/baseline_metrics.json``) whenever ``BaselineModel.xlsx`` changes.
- Stage-by-stage migration plan (seed → fermentation → MF/UFDF → chromatography → spray dryer):
  1. Extend ``baseline_metrics_map.yaml`` with mass/cost checkpoints for the target stage, regenerate the JSON fixture.
  2. Update ``tests/opn/test_opn_front_end.py`` and ``compare_front_end.py`` to surface the new checkpoints.
  3. Swap the placeholder unit logic for BioSTEAM calculations that reproduce the Excel values; keep derived costs in sync.
  4. Repeat for the next downstream stage once regression passes.
- Wire per-batch mass balance calculations for the baseline path to produce total product, resin usage, buffer volumes, and primary utilities.

## Validation Workflow
- Generate a comparison report that juxtaposes BioSTEAM results with Excel KPIs (cost per kg, batch cost, annual production cost) targeting ±5–10% deviation.
- Extend the report to break out chromatography resin, buffer, and CMO cost contributors using the same grouping found in ``Final Costs``.

## Future Enhancements
- Expand the registry to cover non-default module options and scenario toggles once the baseline matches Excel outputs.
- Introduce campaign-based economic toggles (e.g., PROJ02 sensitivity) after baseline validation to explore alternative CMO pricing structures.
- Install missing runtime dependencies (e.g., ``numba``) so ``biosteam`` imports succeed; current sandbox blocks network installs, so resolve this manually on the host environment before attaching full unit builders.

## Implementation Notes
- Use ``migration.module_registry.ModuleRegistry`` to register baseline builders; during bring-up you can temporarily register lambdas that return placeholders (e.g., strings) to validate flow before wiring actual BioSTEAM units.
- Use ``migration.module_builders.register_data_builders`` to register normalized data builders for the baseline keys; replace or augment these with true unit factories as BioSTEAM wiring progresses.
- Invoke ``migration.baseline_system.build_baseline_system`` with the Excel workbook path to assemble the baseline in sequence.  Missing modules are skipped, but unregistered modules raise ``MissingModuleBuilder`` so coverage gaps surface early.
- ``ExcelModuleDefaults`` merges option-specific parameters with any optionless module defaults so shared settings (e.g., chromatography utilities defined at ``DSP02`` scope) are still available to the option-level builders.
- ``ExcelModuleDefaults`` preserves Excel row numbers inside ``ParameterRecord.source_row``; leverage this when tracing discrepancies back to the workbook during validation.
