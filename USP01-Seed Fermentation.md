# SEED01 — Purpose & Scope

- Expand *K. lactis* inoculum from cryovial → shake flask → seed bioreactors.
- Deliver healthy, exponential-phase culture at target volume, OD, and viability to inoculate production fermenter.
- Operate in CDMO mode (client-borne media/consumables/labor) or in-house (CAPEX counted).

------

# SEED01 variants (toggle)

Expose a selector: `SEED01_Method ∈ {ShakeFlaskOnly, TwoStage_Bioreactor, ThreeStage_Bioreactor}`

**When they shine**

- **ShakeFlaskOnly:** pilot/demo runs, small inoculum (<5 L).
- **TwoStage_Bioreactor:** common industrial train (flask → 50 L seed → 500 L seed).
- **ThreeStage_Bioreactor:** needed for 100 m³ production (flask → 50 L → 500 L → 5 m³).

------

# Common inputs

- `Seed_Feedstock` (YPD, defined glucose, glycerol, etc.)
- `Inoculum_Vial_CFU`
- `ShakeFlask_Volume_L`
- `Seed1_Volume_L`, `Seed2_Volume_L`, `Seed3_Volume_m3`
- `µmax_per_h`, `lag_h`
- `Temp_C`, `pH_set`, `DO_set`
- `Antifoam_policy`
- `CIP_SIP_time_h`
- `ownership_mode`, `include_capex`

------

# Common outputs (handoff to production)

- `Seed_Total_Time_h`
- `Seed_Total_Biomass_gDCW`
- `Seed_Viability_pct`
- `Seed_Volume_to_Production_m3`
- `Seed_ClientCost_usd`
- `Seed_CAPEX_Flagged_usd`

------

# Variant specs (BioSTEAM-ready)

## 1) ShakeFlaskOnly

- `Volume=1–5 L`
- Static incubation or orbital shaker, no pH/DO control.
- Performance: µ close to µmax if baffled, but lower biomass yield.
- Economics: negligible CAPEX, disposables (flasks, media), labor intensive.

## 2) TwoStage_Bioreactor

- **Seed1:** 50 L vessel, pH/DO/temp control, batch or fed-batch.
- **Seed2:** 500 L vessel, same controls, exponential phase at harvest.
- Handoff: 500 L exponential-phase inoculum for production 5–20 m³.
- Recovery: ~95% viability.

## 3) ThreeStage_Bioreactor

- Adds **Seed3:** 5 m³ vessel.
- Enables inoculation of 100 m³ production fermenter at 5–10% v/v.
- Time: additional 18–24 h.
- Economics: higher utility, CIP/SIP costs, labor.

------

# BioSTEAM class architecture

```
SeedBase (abstract)
├─ Seed_ShakeFlask
├─ Seed_TwoStage
└─ Seed_ThreeStage
```

**Inputs**
- Media cost ($/kg carbon, $/kg nitrogen, trace salts)
- Utility rates (steam, cooling, agitation)
- Vessel volumes, working fractions
- Growth params (µmax, Yx/s, lag)

**Outputs**
- Time, biomass, inoculum volume
- Costs (client-borne vs CAPEX)
- Warnings (e.g. insufficient inoculum volume)

------

# Compact equations

**Growth kinetics (batch)**
- `X(t) = X0 * exp(µ * (t - lag))`

**Yield**
- `Biomass_gDCW = Yx/s * Substrate_consumed`

**Time to reach target OD**
- `t = lag + ln(OD_target/OD_start)/µ`

------

# Defaults (swap later)

- `µmax=0.30 h⁻¹` (K. lactis on glucose)
- `Yx/s=0.48 g/g`
- `Lag=3 h`
- Costs: media $0.80/L, utilities $0.15/L, labor 4 h/batch @ $80/h, CIP/SIP 2 h per vessel.

------

# Selector logic

- If `Production_Volume≤20 m³` → default `TwoStage_Bioreactor`
- If `Production_Volume≥100 m³` → default `ThreeStage_Bioreactor`
- If demo/small scale → `ShakeFlaskOnly`

------

# Validators

- Inoculum viability <90% → warn
- Volume shortfall vs required 5–10% v/v inoculation → warn
- Seed lag overlaps production schedule → warn

