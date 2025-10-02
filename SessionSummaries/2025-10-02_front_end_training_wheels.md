# 2025-10-02 — Front-End Baseline Status

## Work Completed
- Restored CMO parity with the historical baseline by introducing `minimum_hours` support in `migration/cmo.py` and updating the default profile (`migration/cmo_profiles/default.yaml`) so DSP charges a full day plus prep and the spray dryer bills a six-hour slot. The regression cost metrics (`test_cost_metrics`) now pass.
- Enhanced `migration/scripts/compare_front_end.py` to label the mass-trail columns as *Baseline*, *Plan target*, and *Stream*, plus emit a warning whenever a unit’s stream output diverges from its plan-derived target. This makes the “training wheels” status obvious in every report.

## Current State (“training wheels” checklist)
- Seed train and fermentation units still write Excel-derived product targets into `plan.derived`; streams propagate ~191 kg OPN throughout downstream steps. We have not yet replaced those plan targets with BioSTEAM-calculated recoveries.
- `baseline_defaults.yaml` continues to embed the historical mass trail and material cost values. The regression fixture (`tests/opn/baseline_metrics.json`) therefore represents the Excel snapshot, not a simulated baseline.
- Materials cost breakdown matches baseline by construction; resin cost remains the same negligible $0.01 until the capture unit derives its own resin usage.

## Avoid Rework
- Do **not** reintroduce the Excel fallbacks in code; the YAML snapshot is the only baseline source we need going forward.
- Before adjusting CMO numbers again, confirm whether the rate card or the stage-hour calculation changed—today’s fix expects `dsp_suite.per_hour` to be multiplied by **24 h minimum** and adds a 6 h spray slot.

## Next Steps
1. Teach each unit to populate `plan.derived['product_out_kg']` from the stream it produces (or its recovery setting) and drop the corresponding overrides from `baseline_defaults.yaml`.
2. Regenerate `tests/opn/baseline_metrics.json` from a BioSTEAM simulation once the units “fly free,” then update the comparison/test tolerances accordingly.
3. Revisit the mass-trail warning output after step (1); once plan and stream values agree, the warning should disappear and we can prune the legacy targets.
