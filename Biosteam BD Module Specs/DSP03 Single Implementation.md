one baseline that’s boringly scalable and will always hit “375 mM NaCl + 10 mM phosphate → ~0 salt, ~1 mM phosphate,” then wire it as your **only** DSP03 implementation for now.

## Baseline choice: **Batch TFF “UF → DF → UF” (30 kDa PES)**

- **Step 1 (Pre-concentration UF):** Reduce volume to cut DF buffer and time (VRR ≈ **3×**; cap at 6× if viscosity allows).
- **Step 2 (Constant-volume DF):** **ND = 5 diavolumes** to push NaCl from 375 mM to ≲5 mM and phosphate from 10 mM to ≲0.1 mM (you asked ~1 mM; ND = 3 would do phosphate, but NaCl drives you to ND ≈ 4–5).
   Residual fraction $f=e^{-ND}$ ⇒ **ND = 5 → f≈0.0067**.
- **Step 3 (Final UF):** Concentrate to spray-dryer solids (e.g., **10–12 wt %** total dissolved solids, or to your target protein g/L).

This single train works identically for AEX and Chitosan pools and hands straight to **DSP05**. It’s the most routine, vendor-agnostic, and CMO-friendly path at 50–100 m³ scale. 

------

## Conservative operating set-points (drop-in defaults)

- **Membrane:** PES **30 kDa**
- **Flux (UF/DF):** **80–90 LMH** average; **TMP ≤ 1.5 bar** (aim ≤ 1.2 bar); **CFV ≈ 2.0 m/s**.
- **Protein sieving (So):** UF **0.01**, DF **0.005–0.01**.
- **Adsorptive loss:** **0.1–0.3 % per 100 m²** processed.
- **Total step recovery (UF→DF→UF):** **~96–98 %** (use **97 %** baseline).
- **Antifoam penalty:** flux −**20–30 %**, adsorption +**0.2–0.5 %**.

------

## Sizing math you can trust (example + formulas)

Let **$V_0$** be the incoming pool volume.

1. **Pre-UF (VRR = 3×):**
    Retentate volume for DF: $V_R = V_0/3$.
2. **DF buffer (constant volume):**
    $V_{\text{buffer}} = ND \cdot V_R$.
    With **ND = 5** ⇒ $V_{\text{buffer}} = 5\,V_0/3$.
3. **Permeate throughput for DF:** total permeate = $ND\cdot V_R$.
    If you want DF done in $t_{\text{DF}}$ hours, permeate flow $Q_p = (ND\cdot V_R)/t_{\text{DF}}$.
    Area $A = Q_p / J$ where $J$ is flux in m³ m⁻² h⁻¹.

**Concrete example (70 m³ feed):**

- Pre-UF VRR = 3× → $V_R ≈ 23.3$ m³.
- DF **ND = 5** → buffer $≈ 116.7$ m³; permeate to remove $≈ 116.7$ m³.
- At **90 LMH (0.09 m³ m⁻² h⁻¹)** over **10 h**, area $A ≈ 116.7 / (0.09×10) ≈ 130$ m².
- Add headroom → **150 m²** installed (≈ **75** × 2 m² cassettes, or vendor-equivalent).
- Final UF to spray: size at same area (or reuse) to reach dryer solids within takt.

(Pre-UF permeate is much smaller—same area suffices. Total cycle ~**14–18 h** end-to-end, including UF-in + DF + UF-out, priming and CIP, at these conservative fluxes.)

------

## BioSTEAM baseline (one class, fixed recipe)

**Class:** `DSP03_UFDFUF_Baseline`

**Inputs (from DSP02 handoff):**

- `feed_volume_m3, feed_opn_gL, feed_pH, feed_cond_mM` (≈ 375 mM NaCl, 10 mM phosphate), `temperature_C`, `antifoam_flag`

**Design knobs (defaults):**

- `vr_preUF = 3.0`
- `ND = 5.0`
- `mwco_kDa = 30`
- `flux_LMH = 85` (UF & DF), `tmp_bar_cap = 1.5`, `cfv_ms = 2.0`
- `sieving_UF = 0.01`, `sieving_DF = 0.007`
- `adsorption_loss_per_100m2 = 0.002`
- `area_installed_m2 = auto` (compute; allow override)
- `t_DF_h = 10` (target DF duration)
- `final_spray_solids_wt_pct = 12` (or set `final_OPN_gL`)

**Economics (client-borne, always included):**

- `membrane_cost_usd_per_m2`, `membrane_life_batches` (or campaign days)
- `buffer_fee_usd_per_m3` (for DF buffer + flushes)
- `labor_h_per_batch, labor_rate_usd_per_h`
- `disposables_usd_per_batch, waste_fee_usd_per_tonne`
- **Skid CAPEX flagged** (exclude in CDMO totals)

**What `.design()` computes:**

- Pre-UF retentate $V_R$, DF buffer $ND·V_R$
- Area from DF time/flux; check TMP guard; bump area if needed
- Time blocks (pre-UF, DF, final-UF, setup/CIP)
- Final concentrations (phosphate ≲ 0.1 mM, NaCl ≲ 5 mM at ND = 5)

**What `.run()` returns:**

- `DSP03_Pool_Volume_m3, DSP03_OPN_Conc_gL`
- `DSP03_pH` (=7.0), `DSP03_Conductivity_mM` (≈ near-zero NaCl), `phosphate_mM` (≲ 1 mM)
- `DSP03_Step_Recovery_pct` (≈ 97 % baseline)
- `DSP03_Time_h`

**What `.cost()` returns:**

- Membrane amortization + buffers + labor + disposables + waste
- `DSP03_ClientCost_usd`, `DSP03_CAPEX_Flagged_usd` (reported, excluded in CDMO mode)

**Guardrails (raise warnings):**

- `TMP_est > tmp_bar_cap` → increase area or lower flux
- `viscosity > 8 mPa·s` at pre-UF target → reduce `vr_preUF`
- `antifoam_flag = TRUE` → auto-derate flux −25% and add +0.3% adsorption
- `membrane_life exhausted` → include replacement this batch

All of this mirrors the conservative DSP03 philosophy we already aligned on. 

------

## Why ND = 5 (and not 2–3)

- You asked for **“salt down to close to 0”**. NaCl at 375 mM needs **ND ≈ 4–5** to push residual to single-digit mM; phosphate is easier (ND ≈ 2.3 to reach 1 mM), but salt drives the spec.
- Pre-UF keeps buffer use and time reasonable; at ND = 5 after VRR = 3×, buffer ≈ **1.67× feed volume** (not 5×).

------

## One-page defaults (put straight in your config)

- `vr_preUF: 3.0`

- `ND: 5.0`

- `mwco_kDa: 30`

- `flux_LMH: 85`

- `tmp_bar_cap: 1.5`

- `cfv_ms: 2.0`

- `sieving_UF: 0.01`

- `sieving_DF: 0.007`

- `adsorption_loss_per_100m2: 0.002`

- `t_DF_h: 10`

- `final_spray_solids_wt_pct: 12`

- `membrane_cost_usd_per_m2: (your vendor)`; `membrane_life_batches: 30`

- `buffer_fee_usd_per_m3: (site)`; `labor_h_per_batch: 8`; `labor_rate_usd_per_h: 80`

- `disposables_usd_per_batch: 500`; `waste_fee_usd_per_tonne: 220`

  Assumptions are exactly the ones we agreed: **UF→DF→UF** (30 kDa PES), **VRR = 3× pre-UF**, **ND = 5** (constant-volume DF), **flux = 85 LMH**, **TMP ≤ 1.5 bar**, target **~0 mM NaCl** and **≤ 1 mM phosphate**, handoff to **DSP05**.

  ## What ND=5 gives you

  - Residual fraction $f=e^{-ND}=e^{-5}\approx0.0067$.
  - From **375 mM NaCl → ~2.5 mM**; **10 mM phosphate → ~0.067 mM** (well below your 1 mM spec).

  ## Sizing rules (quick math)

  - Pre-UF retentate $V_R = V_0/3$.

  - DF buffer $= ND \cdot V_R = \tfrac{5}{3}V_0 \approx 1.667\times V_0$.

  - Area for DF (10 h at 85 LMH):
    $$
    A = \frac{ND\cdot V_R}{J\cdot t}=\frac{\tfrac{5}{3}V_0}{0.085\cdot10}\approx \mathbf{1.961\times V_0}\;\text{m}^2
    $$

  - Install **+20% headroom**; assume **2 m² per cassette** for counts.

  - Time blocks with that area: **Pre-UF ≈ 4 h**, **DF = 10 h**, **Final-UF ≈ 0.7–1.5 h** (depends how hard you push), **Setup/flush ≈ 1 h**, **CIP ≈ 2 h** → **~17–18 h total** per batch.

  ## Baseline table (drop straight into TEA)

  | Feed volume $V_0$ | DF buffer (m³) | DF area A (m²) | Installed area (m²) | Cassettes (2 m² ea) | Time (h): UF-in / DF / UF-out / Setup / CIP / **Total** |
  | ----------------- | -------------- | -------------- | ------------------- | ------------------- | ------------------------------------------------------- |
  | **30 m³**         | **50.0**       | **58.8**       | **70.6**            | **36**              | 4.0 / 10.0 / 0.7–1.5 / 1 / 2 / **17–18**                |
  | **50 m³**         | **83.3**       | **98.0**       | **117.6**           | **59**              | 4.0 / 10.0 / 0.7–1.5 / 1 / 2 / **17–18**                |
  | **70 m³**         | **116.7**      | **137.3**      | **164.8**           | **83**              | 4.0 / 10.0 / 0.7–1.5 / 1 / 2 / **17–18**                |
  | **100 m³**        | **166.7**      | **196.1**      | **235.3**           | **118**             | 4.0 / 10.0 / 0.7–1.5 / 1 / 2 / **17–18**                |

  **Notes**

  - Times are effectively **volume-independent** at this design point because we scale area with $V_0$.
  - If antifoam is heavy, derate flux **−25%** → multiply areas by **~1.33** and expect +2–3 h cycle time.
  - **Step recovery**: plan **~97%** overall (sieving UF~1%, DF~0.5–1% over 5 DV, adsorption/hold-up ~0.5–1%).
  - Re-use the same installed area for UF-in and UF-out; no need to over-install.

  ## BioSTEAM defaults (for this baseline)

  - `mwco_kDa: 30`
  - `vr_preUF: 3.0`
  - `ND: 5.0`
  - `flux_LMH: 85`
  - `tmp_bar_cap: 1.5`
  - `cfv_ms: 2.0`
  - `sieving_UF: 0.01`
  - `sieving_DF: 0.007`
  - `adsorption_loss_per_100m2: 0.002`
  - `t_DF_h: 10`
  - `area_installed_m2: auto (1.2 × A)`
  - Economics: **membranes, buffers, labor, disposables, waste** always counted; skid CAPEX **flagged** (excluded for CDMO).