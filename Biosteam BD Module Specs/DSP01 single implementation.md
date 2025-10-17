# DSP01 baseline: **Single-pass TFF (SPTFF) concentration**

**Goal:** cut load time to AEX by reducing volume **without** perturbing buffer (so your AEX bind chemistry is preserved). This works for broth clarified from either **rich (YPD-like)** or **defined salt media**; those media already carry salts and trace ions (see Invitrogen Pichia guideline recipes/parameters), so avoiding unnecessary buffer exchange here is a plus. 

## Why SPTFF (and not batch UF/DF here)?

- Fast, inline **CF 2–4×** with minimal tank time and no dilution.
- Keeps conductivity/pH essentially unchanged (handy when both media types already contain salts). 
- Scale-neutral control: you size membrane area to hit your takt time; everything else is just module count.

------

## Conservative operating set-points (defaults)

- **Membrane:** PES **30 kDa**
- **Total CF:** **3×** (cap baseline at **4×** once viscosity/TMP are verified on your pool)
- **Staging:** **3 stages**, per-stage CF ≈ **1.45–1.5×**
- **Flux:** **80 LMH** average (stay between 70–90)
- **TMP cap:** **≤ 1.2 bar** (per stage)
- **CFV:** **~2.0 m s⁻¹**
- **Protein sieving (cum.):** **~0.5–1.0 %** across all stages
- **Step recovery:** **≈ 99.0 %** (use **98.5–99.2 %** band)

**Guardrails**

- If feed conductivity for AEX bind must be ≤ a threshold, measure it here. If it’s above spec, schedule a **short DF (0.5–1.0 DV)** in **DSP03**, not in DSP01.
- If **TMP** projects > cap at target CF/flux → increase area or lower CF (don’t exceed cap).
- If antifoam is heavy, derate flux **−25 %**.

------

## Sizing for time (8 h takt example)

Let **J = 80 LMH = 0.08 m³ m⁻² h⁻¹** and **t = 8 h**.
 **Single-stage area to process feed volume $V_0$:** $A_\text{base} = V_0/(J\,t)$.
 SPTFF needs area on **each stage**; total installed area ≈ **2.2× $A_\text{base}$** (stage-wise flow decreases through the train). Add **+20 %** headroom.

### Sizing table (CF = 3×; J = 80 LMH; t = 8 h)

| Feed $V_0$ | Total installed area (m²) | 2 m² cassettes (count) | Notes                                         |
| ---------- | ------------------------- | ---------------------- | --------------------------------------------- |
| **1.5 m³** | **≈ 6 m²**                | **≈ 3**                | One skid, compact manifold                    |
| **15 m³**  | **≈ 62 m²**               | **≈ 31**               | One medium skid or two small in parallel      |
| **150 m³** | **≈ 620 m²**              | **≈ 310**              | Two trains or a large-train + parallel branch |

> Where the 2.2× comes from: stage-1 sees $V_0$, stage-2 ~$V_0/1.5$, stage-3 ~(that)/1.5 → areas add to ~2.2× single-stage equivalent at the same flux.

**Cycle time block (typical):** process ≈ **8 h** + setup/flush **~1 h** + CIP **~2 h** → **~11 h** total. Scale-independent when area scales with $V_0$.

------

## What this feeds to AEX

- **Same buffer** you started with (YPD/defined media supernatant chemistry intact). The Pichia/yeast processes typically run with basal salts and trace salts (phosphate, sulfate, etc.), but **AEX bind window** is handled later if needed (DSP03 short DF). 
- **Higher concentration / lower volume** for the same mass → **shorter AEX load** and fewer column cycles.

------

## BioSTEAM unit (single baseline class)

**Name:** `DSP01_SPTFF_Baseline`

**Inputs**
 `feed_volume_m3, feed_opn_gL, feed_pH, feed_conductivity_mM, temperature_C, antifoam_flag`

**Design knobs (defaults)**
 `cf_total=3.0, stages=3, cf_per_stage≈1.45, flux_LMH=80, tmp_cap_bar=1.2, cfv_ms=2.0, mwco_kDa=30, sieving_total=0.008, adsorption_loss_per_100m2=0.002, takt_time_h=8, area_headroom=0.2`

**Economics (client-borne, always counted)**
 `membrane_cost_per_m2, membrane_life_batches (or campaign_days), labor_h_per_batch, labor_rate, buffer_fee_per_m3 (flushes only), disposables_usd_per_batch, waste_fee_per_tonne`
 **Skid CAPEX flagged** (excluded in CDMO totals).

**.design() computes**

- Per-stage flows from $CF_\text{total}$ and `stages`
- Total area $A_\text{install}$ from $V_0, J, t$ with 2.2× multi-stage factor + headroom
- Module count, setup and CIP times

**.run() returns**
 `DSP01_Pool_Volume_m3 = V_0/CF_total`
 `DSP01_OPN_Conc_gL` (≈ CF_total × inlet)
 `DSP01_pH, DSP01_Conductivity_mM` (≈ inlet)
 `DSP01_Step_Recovery_pct ≈ 99%` (apply sieving+adsorption)
 `DSP01_Time_h ≈ takt + setup + CIP`

**.cost() returns**
 Membrane amortization + labor + disposables + buffer flush + waste; CAPEX flagged.

**Warnings**

- `TMP>cap` → increase area or lower CF/flux
- `antifoam_flag` → auto-derate flux −25% and add +0.3% adsorption
- If `feed_conductivity_mM > AEX_bind_max` (your guardrail), annotate “**schedule short DF in DSP03**”.

------

## “What if we need even less buffer before AEX?”

Use **this DSP01 SPTFF** as the **only** baseline. If conductivity must drop (e.g., for a tight bind window), insert **DSP03 short DF (0.5–1.0 DV)** right after DSP01. That separation of concerns keeps DSP01 simple, fast, and completely scalable from **1.5 m³ → 150 m³**.

------

## Media note (since you asked about ionic strength)

Rich (YPD) and defined Pichia/yeast media typically include substantial basal salts and trace metals; the Invitrogen Pichia guideline shows basal salts + PTM1 trace salts and operational DO/pH that are standard for high-cell-density fermentation. That’s why **preserving buffer** through DSP01 is a good default: it avoids unnecessary chemistry churn before capture. 