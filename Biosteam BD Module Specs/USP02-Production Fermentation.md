# PROD01 — Purpose & Scope

- Convert carbon source (glucose/glycerol/lactose/molasses) into target protein with *K. lactis*.
- Deliver clarified fermentation broth (post-harvest supernatant) to DSP01.
- Operate in CDMO mode (client-borne feeds/utilities/labor) or in-house (CAPEX included).

------

# PROD01 variants (toggle)

Expose selector: `PROD01_Method ∈ {Batch, FedBatch, Continuous}`

**When they shine**

- **Batch:** simplest, low yield; demo or early pilot.
- **FedBatch:** industrial standard; higher titers, oxygen efficiency.
- **Continuous:** advanced option; productivity gains but higher complexity.

------

# Common inputs

- `Carbon_Source ∈ {Glucose, Glycerol, Lactose, Molasses}`
- `Carbon_Feed_Conc_gL`
- `Nitrogen_Source` (NH3, urea, AS)
- `Working_Volume_m3`
- `Inoculum_pct`
- `µmax_per_h`, `Yx/s`, `Yp/x`
- `DO_set`, `pH_set`, `Temp_C`
- `Air_vvm`, `O2_enrichment_bool`, `PowerDensity_kW_m3`
- `Antifoam_policy`
- `CIP_SIP_time_h`
- `ownership_mode`, `include_capex`

------

# Common outputs (handoff to DSP01 harvest)

- `Final_OD600`
- `Final_Biomass_gDCW_L`
- `Final_ProductConc_gL`
- `Batch_Time_h`
- `Broth_Volume_m3`
- `OUR_mmolLh`, `CPR_mmolLh`
- `Prod_ClientCost_usd`
- `Prod_CAPEX_Flagged_usd`

------

# Variant specs (BioSTEAM-ready)

## 1) Batch

- Inoculate with 5–10% v/v seed.
- Run until C-source exhausted.
- Titers limited (5–15 g/L typical).
- Economics: lowest complexity, highest variability.

## 2) FedBatch

- Carbon fed at `Carbon_FeedRate` to maintain DO or C-limitation.
- Enables 20–60 g/L titers.
- Oxygen transfer may limit at 100 m³ scale; O₂ enrichment toggle critical.
- Time: 60–120 h.
- Costs: feedstock + utilities.

## 3) Continuous

- Chemostat at dilution rate near µmax.
- Productivity high (g/L/h) but risk of contamination and instability.
- Requires steady utilities, high monitoring.

------

# BioSTEAM class architecture

```
ProdBase (abstract)
├─ Prod_Batch
├─ Prod_FedBatch
└─ Prod_Continuous
```

**Inputs**
- Media/feedstock costs (glucose, glycerol, lactose, molasses)
- Utility rates (steam, cooling, agitation, aeration)
- Vessel size, working volume
- Growth/productivity params

**Outputs**
- Titer, biomass, volume, OUR/CPR
- Costs (client vs CAPEX)
- Warnings (oxygen limited, solubility exceeded)

------

# Compact equations

**Growth (FedBatch C-limited)**
- `µ = f(DO, substrate)`
- `X(t) = X0 * exp(µeff * t)`

**Yield**
- `Biomass = Yx/s * Substrate`
- `Product = Yp/x * Biomass`

**Oxygen transfer**
- `OTR = kLa * (C* - CL)`
- `OUR = qO2 * Biomass`

**Mass balance**
- `Substrate_in - Substrate_out = Biomass + Product + CO2`

------

# Defaults (swap later)

- `µmax=0.30 h⁻¹`
- `Yx/s=0.48 g/g (glucose)`, `0.58 g/g (glycerol)`, `0.45 g/g (lactose)`, `0.25 g/g (molasses)`
- `Yp/x=0.1 g/g`
- `Air=1 vvm`, `PowerDensity=1.5 kW/m³`
- Costs: glucose $0.75/kg, glycerol $1.20/kg, lactose $0.95/kg, molasses $0.25/kg
- Labor: 12 h/batch @ $80/h
- CIP/SIP: 4 h per campaign

------

# Scenario parity capture

- Use `migration/scripts/export_carbon_overrides.py` to snapshot Excel vs BioSTEAM checkpoints
  for each carbon-source override (`usp00_*`). Example:

```bash
python -m migration.scripts.export_carbon_overrides \
  --out tmp/carbon_parity.json \
  --csv tmp/carbon_parity.csv \
  --max-delta 5 \
  --max-delta-pct 0.05
```

- The JSON payload lists mass-trail stages, batch-level cost metrics, and material breakdown
  entries. Hydrate the Excel columns referenced in `migration/baseline_metrics_map.yaml`
  before exporting so the captured “excel” values reflect the workbook scenario we’re
  reconciling against.
- The CSV companion and optional `--max-delta` / `--max-delta-pct` flags give quick
  validation feedback; the command exits non-zero when any absolute or relative delta
  exceeds the thresholds.
- Record the target Excel cells/assumptions for each scenario in this section once the
  parity numbers are finalized; these notes become the regression spec when BioSTEAM unit
  swaps begin.

------

# Selector logic

- If `Target_Titer<15 g/L` → Batch acceptable.
- If `Target_Titer 15–60 g/L` → FedBatch default.
- If `Target_Titer>60 g/L` and high monitoring capacity → Continuous.

------

# Validators

- Check C-feed solubility vs `Carbon_Feed_Conc_gL` (e.g. lactose ≤220 g/L at RT).
- Check `OTR≥OUR`; if not, force O₂ enrichment or throttle µ.
- Warn if `Batch_Time` exceeds 7 d.
- Flag if antifoam addition > spec (risk OTR penalty).
- Ensure inoculum volume ≥5% working volume.
