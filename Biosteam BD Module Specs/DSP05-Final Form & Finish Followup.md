# DSP05 — Final Form & Finish (conservative defaults)

## Scope & mindset

Single-in / single-out step that turns the polished, sterile pool into shippable product. Client-borne consumables/utilities always counted; equipment CAPEX **flagged** (excluded in CDMO totals). Guard for bioburden pass before any finishing. 

------

## Variant A — **SprayDry** (default)

**Conservative operating window**

- **Target moisture:** **3.0–4.0%** (use **3.5%** baseline; sub-3% only with proven dryer/recipe).
- **Pre-concentration:** require **min feed solids ≥5 wt%**; if lower, auto-enable internal pre-conc to **10–12 wt%** (small evaporator model), and add **0.2–0.5%** loss for that micro-step. 
- **Yield (powder recovery):** **98.0–99.2%** (use **98.5%** baseline). Count cyclone/fines losses explicitly; don’t assume perfect fines return. 

**Throughput & energy (derated)**

- **Nominal evaporation capacity:** size to **1,500–2,000 kg H₂O/h** for a “medium” unit; use **1,500** as baseline to avoid over-promising.
- **Thermal efficiency:** **0.65–0.72** (assume **0.70** only with heat recovery; else 0.65).
- **Duty:** $Q = \dfrac{m_{H2O,evap}\cdot \Delta H_{vap}}{\eta}$ ; convert to kWh for utility cost.
- **Cycle time:** $t \approx \dfrac{m_{H2O,evap}}{\text{capacity}}\,+\,\text{CIP/turnaround}$ (use **CIP = 2 h** default).
- **Guardrail:** if $t$ exceeds batch takt, flag “dryer undersized.” 

**Economics (client-borne)**

- Toll fee per **m³ feed** (or **kg powder**) + utilities + liners/bags/N₂ + labor + waste; skid CAPEX flagged. 

**Drop-in defaults**

- `target_moisture_wt_pct = 3.5`
- `min_feed_solids_wt_pct_for_spray = 5.0` ; `precon_enable = TRUE` ; `precon_target_solids_wt_pct = 12` ; `precon_loss_frac = 0.003`
- `dryer_yield_frac = 0.985`
- `dryer_nominal_capacity_kgH2O_h = 1500` ; `thermal_efficiency = 0.65` ; `latent_heat_H2O_kJ_kg = 2250` ; `cip_time_h = 2`
- `bulk_density_kg_m3 = 300–400` (use **350** baseline) 

------

## Variant B — **Lyophilize** (when heat or ultra-low moisture is required)

**Conservative operating window**

- **Target moisture:** **1.0–1.5%** (use **1.0%** only with a validated cycle).
- **Shelf loading:** tray fill **8 mm** at **90%** area utilization; scale-out via chambers if needed.
- **Cycle time (recipe mode):** **Freezing 2 h + Primary 14–18 h + Secondary 8–10 h + Load/Unload 2 h** → **26–32 h** per cycle baseline (don’t promise 20 h until measured).
- **Physics mode (optional):** use conservative **Kv** and **Rp**; if computed primary > 36 h, flag “cycle long; raise shelf temp or reduce fill depth.” 

**Yield**

- **Step recovery:** **98.0–99.2%** (use **98.5%** baseline) for handling/adsorption. 

**Economics (client-borne)**

- Toll per **tray-m²·h** or **kg**, plus energy and disposables; CAPEX flagged. 

**Drop-in defaults**

- `tray_fill_depth_mm = 8` ; `tray_fill_fraction = 0.9` ; `shelf_area_m2 = 30` ; `max_chambers_parallel = 1`
- `freezing_time_h = 2` ; `primary_dry_time_h = 16` ; `secondary_dry_time_h = 8` ; `loading_unloading_time_h = 2`
- `lyo_yield_frac = 0.985`
- Physics: `Kv_W_m2K = 10–12` (use **10**), `Rp_Pa_s_m = 600–800` (use **700**), `overall_thermal_efficiency = 0.50–0.55` (use **0.50**) 

------

## Variant C — **LiquidBulk** (no drying)

**Conservative operating window**

- **Target concentration:** cap at a viscosity-safe value (e.g., **100 g/L**) unless you’ve got rheology data.
- **UF/SPTFF pre-conc helper:** same conservative flux/TMP from DSP03 (don’t double-count losses; add **0.3–0.8%** step loss for this internal helper). 

**Drop-in defaults**

- `target_conc_gL = 100` ; `use_internal_precon = FALSE` ; `hold_temp_C = 4` ; optional preservative flag per spec. 

------

## Mandatory end-gate — **Sterility & QA guards**

- **Bioburden pass required** from DSP04 sterile filter (integrity test pass). If `bioburden_pass = FALSE`, block DSP05.
- **SprayDry**: warn if `feed_solids < min_feed_solids` **and** `precon_enable = FALSE`.
- **Lyophilize**: warn if `load_per_cycle_m3 < batch_volume_m3` and `max_chambers_parallel = 1` (multiple cycles needed). 

------

## Equations to wire (compact)

- **Water to evaporate (spray):** $m_{H2O,evap} \approx m_{feed} - m_{dry\,solids} - m_{water,residual}$.
- **Drying time:** $t_{dry} = m_{H2O,evap}/\text{capacity}$ ; **Energy:** $Q = m_{H2O,evap}\cdot \Delta H_{vap}/\eta$ → kWh, cost via tariff.
- **Powder mass:** $m_{powder} = m_{dry\,solids}/(1-\text{moisture})$.
- **Lyo ice mass:** from feed water minus residual moisture; primary time from $\dot m_{sub}$ using conservative $K_v, R_p$.
- **Step recovery:** `= precon_recovery * (dryer_yield_frac or lyo_yield_frac)` (account for helper losses). 

------

## Economics split (unchanged policy)

- **Always include (client-borne):** toll fee, utilities, consumables, labor, waste.
- **Flagged CAPEX:** dryer/lyo unit + install + maintenance; include **only** when `Ownership_Mode="InHouse"`. 

------

## Drop-in defaults (summary table)

- **SprayDry:** `target_moisture 3.5%`, `dryer_yield 0.985`, `capacity 1500 kgH2O/h`, `thermal_eff 0.65`, `bulk_density 350 kg/m³`, `precon_enable TRUE`, `precon_target 12%`, `precon_loss 0.003`. 
- **Lyophilize:** `moisture 1.0%`, `cycle 26–32 h`, `lyo_yield 0.985`, `Kv 10`, `Rp 700`, `η_thermal 0.50`. 
- **LiquidBulk:** `target_conc 100 g/L`, `use_internal_precon FALSE`. 

------

## Why these are conservative (and where upside will appear)

- Spray dryers seldom hit brochure capacities on first campaigns; sizing to **1.5 t/h** evap with **η=0.65** avoids day-one bottlenecks. Any better performance becomes clear upside. 
- Lyo cycles rarely deliver sub-24 h without tight optimization; baselining **~30 h** keeps schedules honest, and you can tighten with Kv/Rp fits later. 
- Pre-conc and sterile-filter losses are **explicit** rather than hand-waved; that transparency protects COGS and schedule.