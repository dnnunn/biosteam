# USP02 — Production Fermentation (conservative pass)

Your uploaded **USP02** scaffold already captures batch/fed-batch/continuous variants; we’ll lock in oxygen reality and yield math appropriate to a secreted protein, *not* ethanol. 

## Sense-check vs. NREL bioreactor

The **NREL batch/fed-batch classes** are great for vessel sizing and cost scaling (6/10ths exponent, agitators, CIP, etc.), but the default reactions/“efficiency” target ethanol and CO₂, not secreted protein. Use the class **for vessel/cycle/cost**, but drive **biomass/product** with your own Yx/s and Yp/x kinetics or a simple C-limited fed-batch model. 

### Oxygen transfer & power—bankable numbers

- **Power density:** **1.0–1.5 kW/m³** at 100 m³ scale (plan **1.2 kW/m³**); higher is uncommon without custom drives.
- **kLa (air-only):** **60–120 h⁻¹**; use **80 h⁻¹** baseline.
- **Air rate:** **~1.0 vvm** at scale is aggressive; plan **0.5–0.8 vvm** with **O₂ enrichment option** for the last third of the run.
- **Antifoam penalty:** knock **kLa −15 %** when antifoam is present.
- **Guard:** enforce **OTR ≥ OUR**; if not, automatically enable **O₂ enrichment** or throttle µ (feed-limited). 

### Titers, time & yields (secreted OPN, fed-batch)

- **Titers (conservative):** **10–30 g/L**; start designs at **12–20 g/L** until pilot data climb. 
- **Fed-batch duration:** **72–120 h** (use **96 h** baseline). 
- **Yx/s (g/g substrate):** glucose **0.45–0.50**, glycerol **0.55–0.60**, lactose **~0.45**, molasses **~0.25** (complex). Keep the lower end in the model. 
- **Yp/x (g/g biomass):** set **0.08–0.12** (baseline **0.10**); derate if OTR is tight. 

### Carbon selection (already fixed in your Excel)

Keep your dynamic carbon-cost wiring (Glucose/Glycerol/Lactose/Molasses) in BioSTEAM as a **lookup**, not nested IFs; we already standardized that on the spreadsheet side. The same selector should drive **Yx/s** and feed cost here. 

### “Borrowed” NREL knobs to keep (with caution)

- **NREL cost scalers (tank, agitator, CIP, heat-x)**: keep as-is—good for CAPEX order-of-magnitude. 
- **Cycle bookkeeping**: retain `tau` (reaction time) + `tau_0` (CIP/unload) = batch time; keep **tau_0≈3 h** unless site SOP proves shorter. 
- **Autoselect_N**: leave **off** unless you truly want cost-optimal **N**; CDMOs don’t resize vessels for you. 

### CDMO linkage—how your fees and energy show up

- **Client-borne** (always counted): carbon & nitrogen feeds, utilities (air/O₂, cooling, power), labor, QC, antifoam, CIP/SIP chemicals.
- **Flagged CAPEX**: reactor(s), agitators, CIP skids—report, exclude in CDMO totals; include only if `Ownership_Mode="InHouse"`. Keep this identical to DSP policy for consistency. 

------

## Drop-in conservative defaults (USP02 fields)

- `Method = FedBatch` (default)
- `Working_Volume_m3 = 100` (example scale)
- `µmax_per_h = 0.25` ; `Yx/s_glc = 0.48` ; `Yx/s_gly = 0.58` ; `Yx/s_lac = 0.45` ; `Yx/s_mol = 0.25` 
- `Yp/x = 0.10` ; `DO_set = 35%` ; `Temp_C = 30` ; `pH_set = 5.5–6.0`
- `Air_vvm = 0.7` ; `O2_enrichment_bool = TRUE (on demand)` ; `PowerDensity_kW_m3 = 1.2`
- `Antifoam_policy = “as needed; −15% kLa”`
- `CIP_SIP_time_h = 3`
- **Outputs to enforce:** `Batch_Time_h = tau + tau_0` with **tau ≈ 96 h**, **tau_0 ≈ 3 h**; `Final_ProductConc_gL` computed from **Yp/x × Biomass** under OTR guard. 

**Validators (hard stops):**

- `OTR < OUR` → enable **O₂** or throttle feed to hold DO.
- `Batch_Time_h > 168 h` (7 d) → warn “schedule risk”.
- `Antifoam use high` → apply kLa penalty & extra DSP adsorption 0.2–0.5%. 

------

## Quick BioSTEAM wiring notes

- **Class choice:** wrap **NRELBatchBioreactor/NRELFermentation** for vessel/cost/cycle, but compute **biomass & product** with your Yx/s, Yp/x & OTR/OUR constraints (ignore ethanol stoichiometry). Keep **tau** (reaction time) as your fed-batch duration; keep **tau_0** for CIP/unload. 
- **OUR/OTR model (compact):**
   $\textbf{OTR} = k_La \,(C^* - C_L)$ with kLa from power & gas;
   $\textbf{OUR} = q_{O2}\,X$.
   If **OUR > OTR**, reduce effective µ or enable O₂ enrichment until **OTR ≥ OUR** (your controller sets this toggle). 
- **CDMO fees:** keep them at USP level (suite/day + labor/utilities) or push them into a **Prod_ClientCost_usd** roll-up, matching your DSP fee approach. 

------

## TL;DR: what’s conservative and why

- **Oxygen reality** at 100 m³: **kLa 80 h⁻¹**, **1.2 kW/m³**, VVM <1.0 with **O₂** assist → you won’t promise 60 h miracle titers that die on contact with physics.
- **Titers**: 12–20 g/L baseline for secreted OPN; higher is upside once OTR, antifoam, and feeding are dialed.
- **Seed viability & inoculum** guards make sure production batches don’t start in a hole.
- **CDMO split** mirrors DSP: you always count consumables/utilities; CAPEX is flagged and excluded unless you flip to in-house.