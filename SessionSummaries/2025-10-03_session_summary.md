# 2025-10-03 — Migration capture & CMO cost alignment

## Progress
- Re-derived the campaign-fee logic from `Revised Baseline Excel Model.xlsx` and mapped each driver (fermenter, DSP, spray dryer, labor, QA/QC, consumables) to the time inputs and discount formulas Excel uses.
- Extended the BioSTEAM front-end notes for how we’ll calculate fees in-code: campaign factors, contract multipliers, and campaign-level adders (setup, reservation, validation) will be reproduced from the PROJ02 parameters instead of relying on static per-hour constants.
- Confirmed key baseline values for reference: seed train 16 h, main fermentation 48 h, turnaround 24 h, membrane/column occupancy durations, resulting Excel tolls (≈ 119 k $ standard batch + 59 k $ campaign adders → 178 k $/batch total).
- Introduced `migration/cmo_contracts.py` so the BioSTEAM model owns the full contract math; timings/rates/discounts map cleanly to a dataclass that can be swapped for future CMO variants.
- Front end now pulls contract parameters from the defaults, reproduces the Excel per-stage costs (fermenter 74.4 k, DSP 18.0 k, consumables 12.45 k, etc.), and exposes both the standard batch fee (≈ $119 k) and campaign adders (≈ $59 k) alongside the total CMO toll (≈ $178 k).
- Added regression coverage to lock in the new stage totals and refreshed `baseline_metrics.json` so total cost per batch drops to ~$221 k and cost/kg resolves to ~$787.
- Automated the timing inputs where possible (UF vs. DF split, chromatography cycle time, spray/polish TFF) and surface per-kg materials/CMO metrics so TEA/COGs layers can consume the data directly.
- Rebuilt the AEX sizing logic to use real column geometry (1.2 m × 0.25 m), compute per-cycle capacity/time, and emit notes/metrics (≈25 cycles/batch, 2.21 h cycle time, ~21 m³ eluate); resin amortisation now reflects the actual column inventory instead of the 6 m³ alias.
- Quick cost comparison: with resin life capped at 20 cycles and **amortized proportionally to cycles used**, the baseline AEX now lands at ≈$478 k per batch (≈$1.98 k/kg, ~$300 k materials with ~$254 k of resin, ~$740/kg CMO). The chitosan override still sits around $215 k per batch (≈$0.93 k/kg, ~$159/kg materials, ~$771/kg CMO). AEX consumes 1.25 resin lifetimes per batch (25 cycles @ 20-lifetime) and pools ~21 m³ versus 6.5 m³ for chitosan.
- Wired in USP01/USP02 carbon-source/media profiles so a single `profile` toggle loads the matching seed + fermentation overrides (glucose rich/defined, glycerol, molasses, lactose); carbon cost now honors the profile totals via `_profile_carbon_totals`.

## Next steps
1. Drive the remaining timing inputs (e.g., seed-train duration, membrane-throughput assumptions) from simulation outputs or plan data so the contract costs stay self-consistent as we tweak the flowsheet.
2. Surface a contract registry so we can swap between different CMO configurations (e.g., Laurus vs. Arxada) without changing code—`cmo_contracts.py` already exposes the shapes we need.
3. Pipe the per-kg metrics (`materials_cost_per_kg_usd`, `cmo_cost_per_kg_usd`, etc.) into the TEA/COGs layer to unlock margin and retail-price scenarios.

## References
- Workbook: `Revised Baseline Excel Model.xlsx` (Calculations → “CMO Fees & Campaigns”).
- Current defaults: `migration/module_defaults.yaml` (PROJ02 parameters) and `migration/baseline_defaults.yaml` (campaign structure).


**AEX vs Chitosan Capture – Cost Snapshot**

| Metric | AEX Capture | Chitosan Capture |
| --- | --- | --- |
| Total cost per batch (USD) | 432174 | 209610 |
| Cost per kg product (USD/kg) | 1536.82 | 776.19 |
| Materials cost per batch (USD) | 253858 | 31294 |
| Materials cost per kg (USD/kg) | 902.72 | 115.88 |
| CMO cost per batch (USD) | 178316 | 178316 |
| CMO cost per kg (USD/kg) | 634.09 | 660.31 |
| Resin/polymer cost per batch (USD) | 211718 (2 replacements) | 21638 |
| Cycles per batch | 30 | n/a (single-stage) |
| Cycle time (h) | 2.21 | — |
| Pool volume (L) | 25447 | 6500 |

**Key observations**
- AEX consumes ~30 cycles per 300 kg batch; at a 20-cycle resin lifetime that triggers two fresh charges, driving resin spend to ~\$212k per batch.
- The long cycle train (66 h) and large buffer volumes (~25 m³ eluate) contrast with the chitosan route’s single-stage run (~6.5 m³ pool).
- Chitosan materials remain low (~\$31k per batch, \$116/kg) even though polymer makeup (~\$21.6k) is now accounted for; CMO fees dominate both cases.
- Net effect: chitosan sits around \$776/kg versus \$1.54k/kg for the updated AEX, primarily due to resin replacements.
