# 2025-10-02 — Front-End Baseline Status

## Work Completed
- Restored CMO parity with the historical baseline by introducing `minimum_hours` support in `migration/cmo.py` and updating the default profile (`migration/cmo_profiles/default.yaml`) so DSP charges a full day plus prep and the spray dryer bills a six-hour slot. The regression cost metrics (`test_cost_metrics`) now pass.
- Enhanced `migration/scripts/compare_front_end.py` to label the mass-trail columns as *Baseline*, *Plan target*, and *Stream*, plus emit a warning whenever a unit’s stream output diverges from its plan-derived target. This makes the “training wheels” status obvious in every report.
- Reworked `SeedTrainBioreactor` and `FermentationBioreactor` so biomass and glucose demand are driven by OD₆₀₀ inputs (OD→DCW conversion, growth yield, maintenance term) rather than target titer. Product is decoupled via a selectable model (`specific_productivity` in baseline), and NH₄OH/pH base usage now follow the biomass-derived nitrogen requirement.
- Chromatography and predry TFF plans now record their masses/volumes straight from the simulated capture/DSP03 chains; the static Excel checkpoints (205 kg, 195 L, etc.) are gone.
- Refreshed `tests/opn/baseline_metrics.json` and the regression assertions to track the new BioSTEAM-only baseline (fermentation product ≈217 kg, seed media costs based on the rich recipe concentrations). Updated `test_fermentation_stream_matches_plan` tolerance to reflect that downstream placeholder units still mutate the shared stream object.
- Retired the microfiltration/UFDF training wheels: the plan-backed units now pull recovery/dilution targets straight from their specs, UF/DF membrane spend comes from the spec sheet, we stripped the static `product_out_kg` overrides, and regenerated the regression fixture off the simulated mass trail (cell-removal chain now drives the 421 kg checkpoint).

## Current State (“training wheels” checklist)
- Seed train, fermentation, clarification, and chromatography/predry TFF now publish simulated outputs into their plans. The spray dryer still leans on static plan targets for recovery.
- `baseline_defaults.yaml` continues to embed the historical mass trail and material cost values. The regression fixture (`tests/opn/baseline_metrics.json`) therefore represents the Excel snapshot, not a simulated baseline.
- Materials cost breakdown matches baseline by construction; resin cost remains the same negligible $0.01 until the capture unit derives its own resin usage.

## Avoid Rework
- Do **not** reintroduce the Excel fallbacks in code; the YAML snapshot is the only baseline source we need going forward.
- Before adjusting CMO numbers again, confirm whether the rate card or the stage-hour calculation changed—today’s fix expects `dsp_suite.per_hour` to be multiplied by **24 h minimum** and adds a 6 h spray slot.

## Next Steps
1. Drive the spray dryer plan from the simulated product stream (final recovery & solution density) so the last static checkpoint disappears.
2. Model depth-filter/microfiltration media spend explicitly (area × media cost) so the MF line item stops reading as zero.
3. Re-run the regression harness once the downstream stages are dynamic and tighten the warning output in `compare_front_end.py` accordingly.
