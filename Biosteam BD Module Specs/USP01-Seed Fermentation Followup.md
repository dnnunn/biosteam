# USP01 — Seed Fermentation (conservative pass)

## What changes vs. a fuels seed train

Your seed is feeding a **secreted-protein** fed-batch—oxygen transfer and foaming control matter more than saccharification throughput. We therefore bias toward lower specific growth rates, explicit antifoam penalties, and viability gates at each stage. Keep the stage structure you already laid out (flask → 50 L → 500 L → 5 m³ for 100 m³ production). 

### Conservative operating baselines

- **µmax (glucose media):** **0.25–0.30 h⁻¹**; design at **0.25 h⁻¹** until you prove higher. 
- **Lag:** **3–6 h** (use 3 h if seed provenance is tight). 
- **Viability at transfer:** **≥95 %** gate; model **92–95 %** when antifoam is heavy (penalize viability 1–3 %). 
- **DO setpoint:** **30–40 %** air saturation (not 10–20% as sometimes used in ethanol), to protect secretion machinery.
- **Antifoam penalty:** reduce kLa **−10–20 %** when antifoam on; add **0.2–0.5 %** downstream adsorption loss (it shows up in harvest filters).
- **Seed working fraction:** **70–80 %** (never plan 90%—leave headspace for gas and foam).
- **Inoculum into production:** **5–10 % v/v** (5% minimum); add a validator that blocks <5%. 

### Time & scale

- **Two-stage seed (50 L → 500 L):** **~36–48 h** total at µeff≈0.20–0.25 h⁻¹.
- **Three-stage seed (→ 5 m³):** add **~18–24 h**; total **~54–72 h**. 

### Cost split (CDMO linkage)

Client-borne, always include: media (YPD/defined), disposables, utilities, labor, CIP/SIP; flag seed-train CAPEX (exclude in CDMO totals). Keep your `ownership_mode` / `include_capex` toggles from the rest of the model. 

### BioSTEAM mapping

- Reuse your **SEED01 variants** and I/O as written (shake-flask only, two-stage, three-stage). 
- If you stub seed vessels as **NRELBatchBioreactor** instances for time/cost scaling, keep **tau_0 (CIP/unload) = 2–3 h** and **V_wf = 0.75–0.80** (not 0.9). 

**Validators (hard stops):**

- Viability <90 % → warn (and derate inoculum effectiveness). 
- Calculated inoculum volume <5 % of production working volume → block. 