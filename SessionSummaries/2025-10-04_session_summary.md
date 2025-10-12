# 2025-10-04 — Baseline alignment status before break *(legacy workbook notes archived)*

## What changed today
- Switched the AEX resin accounting to prorate by lifetime consumed (25 cycles ÷ 20-cycle life → 1.25 lifetimes). BioSTEAM now books **$254k** per batch for resin (down from ~$407k) and the overall batch total drops to **$478k** (~$1,984/kg).
- Exported the updated assumptions to `SessionSummaries/glucose_rich_aex_baseline_parameters.csv` so every cost driver (volumes, times, amortisation factors) is captured with descriptions.
- Archived the old Excel workbook comparison after confirming the PROJ02 parameters now live in our YAML defaults. Cost deltas captured below are kept only for historical context; ongoing work should rely on the spec-driven baseline.

## BioSTEAM vs legacy Excel snapshot (glucose-rich, AEX)
| Metric | Excel | BioSTEAM | Notes |
| --- | --- | --- | --- |
| Final product per batch | 191.4 kg | 236.2 kg | Workbook still yields less product; BioSTEAM’s recovery chain delivers ~24% more mass. |
| Total cost per batch | $430k | $478k | 11% spread remains after resin changes. |
| Cost per kg | $2,249 | $1,984 | Lower BioSTEAM batch cost and higher yield pull the model below Excel. |
| Materials cost per batch | $247k | $300k | Excel folds most capture spend into buffers; BioSTEAM books it as resin. |
| CMO fees per batch | $135k | $178k | Excel still uses the legacy toll structure; BioSTEAM reproduces the contract math. |
| Resin cost per batch | $214k | $254k | Excel amortises 20-cycle life but assigns residual costs to the buffer line. |

## Remaining gaps & follow-ups
- **Yield basis:** The legacy Excel mass trail (191 kg) differs from the current spec baseline (≈189 kg). Document or eliminate the delta once we lock the spec values.
- **CMO rates:** Continue validating the contract math entirely in Python; the workbook implementation is now frozen.
- **Capture cost presentation:** Confirm whether the BD spec should pool buffers + resin, or keep BioSTEAM’s explicit split.
- **Seed media spend:** Align the seed/fermentation recipes in the spec bundle if that delta matters for reporting.

## Parking lot (post-break)
1. Decide whether to harmonise the product yield or keep both views for sensitivity work.
2. Review seed/fermentation media assumptions in the spec bundle for consistency.
3. If capture economics remain contentious, consider exporting a side-by-side of the per-cycle timing & buffer usage to pinpoint the residual 40k difference in resin spend.

Take the time you need—everything above should give you a clean starting point when you’re back.

## Allocation-scheme review
- The "A standardized accounting scheme" note (repo `Biosteam BD Module Specs/`) recommends locking campaign + resin economics to a single allocation basis. The approach is compatible with our current CMO module: we already track campaign structure, batches, and per-cycle resin usage, so adding a post-processing layer to compute $/unit from aggregated pools is straightforward.
- The helper scripts in `~/Downloads` provide a ready-made implementation:
  - `cmo_resin_allocation.py` encapsulates the math (basis selection, prorated resin, CIP, denominators) and mirrors the policy doc.
  - `biosteam_postprocess_allocation.py` shows how to call that helper after a BioSTEAM run using a YAML scenario like `CMO_Mid_Scenario.yaml`.
  - `inject_allocation_into_workbook.py` copies a standardized "Policy" sheet plus named ranges into Excel so the workbook references the same formulas (`CMO_per_unit`, `Resin_per_unit`, etc.).
- Integrating this next round would give us bidirectional parity:
  1. Drop `cmo_resin_allocation.py` into the repo, expose a small hook in the TEA/report pipeline (`FrontEndSection` → TEA summary) to call `compute_allocation` with the baseline campaign + resin numbers we already compute (campaign fees, planned batches, resin lifetimes, cycles per batch, etc.).
  2. Store the YAML inputs alongside other defaults so Excel/BioSTEAM share the same policy. The existing `CMO_Mid_Scenario.yaml` is a usable template; we would parameterize it from our baseline config.
  3. Use `inject_allocation_into_workbook.py` once to seed the Excel model with the Policy tab and named ranges. Future comparisons can then reference the same per-unit outputs.
- No blockers spotted: the helper exposes both `UNITS_OF_PRODUCTION` and `STRAIGHT_LINE_PER_CYCLE`, matching the policy doc. We can keep our per-cycle prorating and highlight variances in the GL as recommended.
- Suggested next steps when back from break: wire the helper into the TEA export, add a regression check that the standardized allocation numbers match the worksheet (similar to the baseline KPI test), and document the allocation basis in the README/TEA section so downstream users stick to the single declared basis.

## Next-session To-Do (Allocation Integration)
1. **BioSTEAM**
   - [ ] Add `cmo_resin_allocation.py` to the repo and expose a TEA hook to call `compute_allocation` after the front-end build, using campaign/resin inputs we already compute.
   - [ ] Parameterize the helper inputs from our baseline defaults (mirroring the Excel Policy sheet / YAML scenario).
   - [ ] Update regression tests to confirm standardized per-unit figures match the Excel Policy results.

2. **Docs**
   - [ ] Extend `A standardized accounting scheme.md` with implementation notes (which workbook cells feed the Policy sheet, TEA hook location).
   - [ ] Note in the TEA README/summary which allocation basis is the declared policy (KG_RELEASED).

3. **Optional clean-up**
   - [ ] Document the gap between the archived Excel recovery chain and the spec-driven baseline, or remove the workbook snapshot entirely once stakeholders are comfortable with the Python source of truth.
