# 2025-10-06 — Allocation integration kickoff

## BioSTEAM
- Added `migration/cmo_resin_allocation.py` and exposed `FrontEndSection.allocation_result`; the helper pools campaign + resin spend and returns per-unit values for the declared `KG_RELEASED` basis.  
- Regression test `test_standardized_allocation` verifies the new totals against the underlying per-batch economics.  
- Could not run `pytest` locally (`pytest: command not found`); rerun `pytest -m "not slow"` inside the BioSTEAM env to confirm once available.

## Excel
- Created `migration/scripts/inject_allocation_into_workbook.py` to copy the Policy sheet from `CMO_Resin_Allocation_Module.xlsx`, rebuild named ranges, and (optionally) write a backup before patching.  
- Seeded `Revised Baseline Excel Model.xlsx` with the Policy sheet and wired the Value column back to existing named ranges (campaign counts, CMO totals, resin volume/life). `CMO_per_unit`, `Resin_per_unit`, and `Total_per_unit` are now workbook-level names.  
- Input gaps (CIP cost per cycle, retainer) remain manual; capture them in the workbook when those assumptions are finalized.

## Follow-ups
1. Replace downstream workbook formulas (`Final Costs`, regression hooks) with the new named ranges to avoid double-counting resin/CMO charges.  
2. Surface the standardized allocation numbers in reports/exports alongside the legacy per-batch metrics.  
3. When the workbook captures CIP-cycle or retainer entries, point `Policy!D?` at those cells and mirror them in the BioSTEAM metadata for parity.

## Follow-up progress (2025-10-06, Codex)
- Updated `Excel/Revised Baseline Excel Model.xlsx` Policy formulas and downstream `Final Costs` $/kg math to rely on the workbook-level `CMO_per_unit`, `Resin_per_unit`, and `Total_per_unit` names, removing the extra resin/CMP double-counting.  
- Extended `migration/baseline_metrics.py` (and the regression JSON fixtures) so baseline exports now carry the allocation basis, denominator, and per-unit $/kg numbers; CLI tools (`compare_front_end.py`, `export_carbon_overrides.py`) print the new policy values alongside legacy per-batch metrics.  
- `build_front_end_section` now threads a `Retainer_Fee_per_Year` parameter into the standardized allocation inputs, and the Excel policy injector will hook `Retainer_Fee_per_Year` / `CIP_Cost_per_Cycle` to named ranges whenever the workbook defines them.
