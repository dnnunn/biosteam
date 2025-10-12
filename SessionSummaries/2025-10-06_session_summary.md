# 2025-10-06 — Allocation integration kickoff

## BioSTEAM
- Added `migration/cmo_resin_allocation.py` and exposed `FrontEndSection.allocation_result`; the helper pools campaign + resin spend and returns per-unit values for the declared `KG_RELEASED` basis.  
- Regression test `test_standardized_allocation` verifies the new totals against the underlying per-batch economics.  
- Could not run `pytest` locally (`pytest: command not found`); rerun `pytest -m "not slow"` inside the BioSTEAM env to confirm once available.

## Excel (archived)
- Previous work copied the allocation Policy sheet into the legacy workbook and wired named ranges (`CMO_per_unit`, `Resin_per_unit`, `Total_per_unit`). With the switch to the spec-driven baseline, the workbook is now read-only historical context.

## Follow-ups
1. Replace downstream workbook formulas (`Final Costs`, regression hooks) with the new named ranges to avoid double-counting resin/CMO charges.  
2. Surface the standardized allocation numbers in reports/exports alongside the legacy per-batch metrics.  
3. When the workbook captures CIP-cycle or retainer entries, point `Policy!D?` at those cells and mirror them in the BioSTEAM metadata for parity.

## Follow-up progress (2025-10-06, Codex)
- Extended `migration/baseline_metrics.py` (and the regression JSON fixtures) so baseline exports now carry the allocation basis, denominator, and per-unit $/kg numbers; CLI tools (`compare_front_end.py`, `export_carbon_overrides.py`) print the new policy values alongside legacy per-batch metrics.  
- `build_front_end_section` now threads a `Retainer_Fee_per_Year` parameter into the standardized allocation inputs for consistent TEA hooks.

## Session wrap-up (2025-10-07, Codex)
- Regenerated `tests/opn/baseline_metrics.json`, reran `pytest -m "not slow"`, and committed the allocation sync changes (`Align CMO/resin allocation across BioSTEAM and Excel`). The workbook snapshot is retained only as an archived artifact.
