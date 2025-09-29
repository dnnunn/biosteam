# TL;DR recommendation at 50–200 m³

- **Default**: Batch **UF Concentration (DSP01a)** to target VRR, followed by **Diafiltration (DSP01b)** to reach conductivity/salt targets. This matches what CMOs already run for yeast supernatants.
- **When you need in-line, chromatography-friendly feed** with minimal tank time: **SPTFF (DSP01c)** to a modest CF (2–6×), then either go straight to capture or finish with a small DF.
- **For perfusion/continuous trains** or when you want steady-state loading to capture: **cTFF (DSP01d)**.

------

## Cross-cutting feed & product assumptions (inputs all units consume)

- **Batch volume in (m³):** 1–200 (baseline 100)
- **Protein MW & target retention:** OPN ≈ 35–50 kDa (phospho-heterogeneous). Choose **MWCO 10–30 kDa**; baseline **30 kDa** with **R_protein ≈ 0.98–0.995** (sieving $S_p=1-R$).
- **Viscosity (mPa·s):** 1.2–3.0; **max allowable at outlet** usually 5–8 mPa·s for pump/pressure limits.
- **Fouling behavior:** flux decay coefficient $k_f$ (empirical), flux recovery after CIP $f_{\text{clean}} = 0.85–0.95$.
- **Antifoam flag** (reduces flux by a factor, e.g., 0.9 if heavy antifoam).
- **Temperature (°C):** 20–30; increases flux modestly but watch stability.
- **Target conductivity/pH after DF** (user-set specs).
- **Hold-up/LRV flags for bioburden control** (if relevant to downstream).

------

# DSP01a — UF Concentration (batch TFF)

**Purpose**
 Concentrate product from volume $V_0$ to $V_f$, achieving **volume reduction ratio (VRR) = $V_0/V_f$**, while retaining product.

**Streams**

- In: Clarified supernatant
- Out (retentate): Concentrated product
- Out (permeate): Water + small solutes (and any sieved protein)

**Design variables**

- **MWCO (kDa):** 10–30 (baseline 30)
- **Flux setpoint (LMH)** at start of batch: 60–120 LMH post-clarification (baseline 90 LMH)
- **TMP (bar):** 1.0–2.0 (baseline 1.2)
- **Crossflow velocity (m/s):** 1.5–3.0 (baseline 2.0)
- **Max ∆P (bar):** 2.5 typical
- **Target VRR:** 4–15× (baseline 6×)
- **Membrane area $A$ (m²):** sized from flux/time targets
- **Fouling model:** constant-flux with time penalty or V/A penalty
- **Protein sieving $S_p$:** 0.002–0.02 (baseline 0.01)
- **Adsorptive loss factor:** 0.05–0.3 % per 100 m² processed (baseline 0.1 %/100 m²)

**Performance model (batch, constant-flux approximation)**

- **Permeate flow:** $Q_p = J \cdot A$ where $J$ is flux (m³/m²·h).
- **Time to target VRR:** $ t \approx \dfrac{V_0 - V_f}{Q_p}$ with optional derate $J(t)=J_0 e^{-k_f t}$ or $J=J_0/(1+k_f \cdot V/A)$.
- **Protein recovery (retentate):**
   $\text{Rec} \approx 1 - S_p \cdot \dfrac{\int Q_p\,dt}{\text{Protein in}} - \text{Adsorption} - \text{Hold\!-\!up}$
   Typical overall **98–99.5 %**.
- **Viscosity/pressure constraint:** If retentate viscosity at target concentration exceeds limit, cap VRR or raise area.

**Utilities & cleaning**

- CIP (NaOH 0.1–0.5 M) + acid; water: 50–150 L per m² per full CIP cycle (tunable).
- Pump power from $P \approx Q_{\text{recirc}}\cdot \Delta P / \eta$.

**Cost hooks**

- **Membrane cost:** $/m², lifetime $N_{\text{batches}}$.
- **Skid CAPEX:** $C = a\cdot A^{b}$ (b ≈ 0.6–0.8), install factor 1.5–2.0×.
- OPEX: electricity, water, chemicals, membrane amortization, labor.

**Constraints & warnings**

- Flux > recommended for broth → warn/derate.
- $\Delta P$ or TMP exceed limits → infeasible/auto-cap.
- Viscosity at outlet > limit → reduce VRR or increase $A$.

**Defaults for \*K. lactis\* at scale**

- **MWCO 30 kDa**, $J_0=90$ LMH (post-centrifuge/depth filter), $k_f$ tuned to your runs, VRR=6×, $S_p=0.01$.
- Overall recovery 98.5–99.3 % typical.

------

# DSP01b — Diafiltration (constant-volume buffer exchange)

**Purpose**
 Exchange salts/buffer while holding retentate volume ~constant.

**Design variables**

- **Mode:** constant-volume DF (feed dia-buffer at same rate as permeate).
- **Number of diavolumes $N_D$:** user-set to hit residual fraction.
- **MWCO / membrane:** reuse from UF run or separate DF train.
- **Flux (LMH):** slightly higher than late-UF if low viscosity (baseline 100 LMH).
- **Protein sieving during DF $S_p^{DF}$:** often similar or slightly lower than UF.
- **Small-solute sieving $S_s \approx 1$.**

**Performance model**

- **Small-solute clearance (ideal):** Residual fraction $f = e^{-N_D}$ (when $S_s \approx 1$).
   Thus **$N_D = -\ln(f)$**; e.g., 95 % removal → $N_D \approx 3$.
- **Protein loss:** $\text{Loss} \approx S_p^{DF}\cdot N_D$ (refine with your data).
- **Time:** $t_{DF} \approx \dfrac{N_D \cdot V_{\text{ret}}}{J \cdot A}$.
- **Buffer use:** $V_{\text{buffer}} = N_D \cdot V_{\text{ret}}$.

**Utilities & cleaning**

- As UF; additional water/buffer use per DV.

**Cost hooks**

- **Buffer cost ($/m³)**, water, chemicals; membrane amortization as above.

**Constraints & warnings**

- If conductivity spec implies $N_D>8$, warn on time/water/cost blowout—suggest partial UF to lower volume or SPTFF pre-concentration.

**Defaults**

- $N_D = 3$ for 95 % salt removal; $J=100$ LMH; $S_p^{DF}=0.005–0.01$.
- Protein recovery across DF: **97–99 %** (depends on $N_D$ and sieving).

------

# DSP01c — Single-Pass TFF (SPTFF)

**Purpose**
 Achieve **inline concentration in one pass** using cascaded modules at controlled TMP/CFV. Ideal to feed capture directly, shorten tank cycles, and avoid batch recirculation.

**Streams**

- In: clarified feed
- Out: concentrated permeate/retentate path depends on configuration; most SPTFF designs give a **concentrated retentate** outlet.

**Design variables**

- **Stages in series:** 1–4 (baseline 2–3).
- **Stage-wise concentration factor $CF_i$:** 1.5–2.5× each; **overall CF = ∏ CF_i** (typical overall 2–8×).
- **Area per stage:** sized from target stage flux and allowable TMP.
- **Flux (LMH):** 60–120 LMH with guardrails; lower than batch UF at high CF.
- **TMP caps per stage:** 1.0–1.5 bar; CFV 1.5–3.0 m/s.
- **Protein sieving per stage $S_{p,i}$:** 0.003–0.02.

**Performance model**

- Mass balance per stage with concentration-dependent viscosity; update TMP limit and derate $J$ with $\mu(C)$.
- **Recovery:** product loss from cumulative sieving + adsorption across stages + hold-up (SPTFF generally **high recovery**: 98–99.5 %, often better than long batch recirculations).
- **Pressure/viscosity check:** enforce maximum at final stage; if violated, increase stages/area or reduce target CF.

**Utilities & cleaning**

- Similar to UF, but cleaning by forward flush + CIP between campaigns; less recirculation time.

**Cost hooks**

- **Area tends to be higher** than batch UF for the same final CF if you constrain TMP tightly—model area accordingly.
- Skid premium **(+10–25 %)** vs generic UF for SPTFF manifolds and control.

**Constraints & warnings**

- High inlet variability → stage TMP spikes; include guard margin.
- If target CF > 8× in one pass, warn and propose batch UF or more stages.

**Defaults**

- 3 stages, each CF ≈ 1.8× → overall ~5.8×, $J=80$ LMH, per-stage TMP ≤1.2 bar, overall protein recovery 99.0 %.

------

# DSP01d — Continuous TFF (cTFF)

**Purpose**
 Operate at **steady state** for continuous processes (e.g., perfusion harvest or continuous capture feed). Can also run **continuous DF**.

**Control concept**

- Retentate loop with **level/pressure control**, bleed to maintain steady concentration, continuous buffer feed for DF.

**Design variables**

- **Steady-state retentate volume $V_R$** and **target concentration** (or VRR).
- **Permeate rate $Q_p$** set by $J\cdot A$, with TMP/CFV limits.
- **Bleed (product) rate** to hold concentration.
- **For continuous DF:** set **DV per hour** or specify residual conductivity.

**Performance model**

- **Mass balance at steady state**:
   $Q_{in} = Q_{bleed} + Q_p$
   Protein balance with sieving $S_p$ → steady-state recovery $\approx 1 - S_p\cdot Q_p/(Q_{in}\cdot C) - \text{adsorption loss rate}$.
- **Transient start-up**: include a **start-up loss** term (e.g., 0.2–0.5 DV of hold-up) amortized over campaign time.
- **Fouling drift**: derate $J$ over campaign; periodic CIP windows reduce uptime.

**Utilities & cleaning**

- More automation/controls; scheduled CIP (e.g., every 24–72 h) → uptime factor (0.92–0.98 typical).

**Cost hooks**

- Skid CAPEX premium vs batch (+20–40 % for instrumentation/automation).
- Same membrane $/m²; plan for **campaign-based** lifetime (days) rather than batches.

**Constraints & warnings**

- If required uptime × flux with allowable TMP demands area above practical footprint, flag and suggest staged parallel trains.
- Control limits: high variability in feed → risk of oscillations (add buffer tank).

**Defaults**

- $J=70–100$ LMH at steady state; uptime 95 %; start-up loss equivalent to 0.3 DV; recovery 98.5–99.5 % depending on $S_p$ and adsorption.

------

# Decision matrix (which sub-option to prefer)

| Criterion           | UF (batch) DSP01a | DF (batch) DSP01b            | SPTFF DSP01c                    | cTFF DSP01d                   |
| ------------------- | ----------------- | ---------------------------- | ------------------------------- | ----------------------------- |
| Scale to 100–200 m³ | **Excellent**     | **Excellent**                | **Good**                        | **Good–Excellent**            |
| Time efficiency     | Good              | Fair–Good (depends on $N_D$) | **Excellent**                   | **Excellent**                 |
| Water/buffer use    | N/A               | **High** (∝ $N_D$)           | Low–Med                         | Low–Med (continuous DF)       |
| Recovery            | **High**          | High (watch $S_p\cdot N_D$)  | **High**                        | High                          |
| Control/automation  | Standard          | Standard                     | Moderate                        | **High**                      |
| CAPEX               | Med–High          | Med                          | Med–High                        | **High**                      |
| When to pick        | Default           | When exchange needed         | Inline concentration to capture | Perfusion / continuous trains |

**Policy:**

- Need big CF with minimal tank time to feed capture? → **SPTFF**.
- Need conductivity/pH change? → **DF** (batch or continuous DF).
- Classic batch workflow? → **UF → DF**.
- Continuous perfusion or flow-through capture train? → **cTFF**.

------

# BioSTEAM-oriented fields (consistent across DSP01a–d)

Expose in each class:

**Design inputs (user-settable)**

- `feed_volume_m3`, `protein_conc_gL_in`, `target_VRR`, `target_CF`, `target_conductivity_mScm`, `temperature_C`, `viscosity_model_params`, `MWCO_kDa`, `flux_LMH`, `TMP_bar`, `CFV_ms`, `max_DP_bar`, `Nd` (for DF), `stages` (for SPTFF), `uptime_fraction` (for cTFF), `fouling_coeff_kf`, `flux_recovery_after_CIP`, `sieving_protein`, `adsorption_loss_frac_per_100m2`.
- Economics: `membrane_cost_per_m2`, `skid_cost_a`, `skid_cost_b`, `install_factor`, `membrane_life_batches` (or `campaign_days`), `power_price_per_kWh`, `water_price_per_m3`, `CIP_NaOH_cost_per_kg`, `buffer_cost_per_m3`, `labor_cost_per_h`.

**Design algorithm (populate `.design_results`)**

- Membrane area $A$, number of modules, recirc flow, pump sizes.
- Cycle/campaign times, CIP time, buffer/water needs.
- For SPTFF: stage areas and predicted outlet CF.
- For cTFF: steady-state flows $Q_{in}, Q_p, Q_{bleed}$.

**Performance (`.performance_results`)**

- Product recovery %, protein loss split (sieving/adsorption/hold-up).
- Final concentration, VRR/CF, DF residual fraction, conductivity, pH shift if modeled.
- TMP/viscosity/∆P checks and any derating invoked.

**Costs (`.cost_results`)**

- CAPEX (purchase + install), OPEX per batch (or per day for cTFF), consumables, utilities, labor, waste.
- Membrane amortization based on life (batches or campaign days).

**Constraints/warnings**

- Flux/TMP over limits; viscosity exceedance; $N_D$ too high; SPTFF CF too high; cTFF area/uptime infeasible → clear messages and suggested mitigation (increase area, add stage, relax spec, etc.).

------

## Practical defaults for your *K. lactis* OPN line (tune with your runs)

- **Membrane polymer:** PES/PS (sanitary), **MWCO 30 kDa** baseline.
- **Batch UF:** $J_0=90$ LMH → derate with $k_f=0.15–0.3 \, \text{h}^{-1}$ (project-specific), VRR=6×, TMP 1.2 bar, CFV 2.0 m/s, $S_p=0.01$.
- **DF:** $N_D=3$ for 95 % small-solute removal; $J=100$ LMH; $S_p^{DF}=0.005–0.01$.
- **SPTFF:** 3 stages, per-stage CF 1.8×, $J=80$ LMH, stage TMP ≤1.2 bar.
- **cTFF:** $J=80$ LMH steady; uptime 0.95; start-up loss 0.3 DV; scheduled CIP every 48 h with 90 % flux recovery.

------

## Where DSP01 sits in your flowsheet

**Disc-stack + depth filter → DSP01 (UF/DF/SPTFF/cTFF) → Capture (chromatography or alternative) → …**
 Keep a small surge tank before DSP01 for buffer prep and flow smoothing; for SPTFF or cTFF feeding capture, include a feed conditioning loop (temperature, conductivity) and a pressure interlock with the next unit.

------

## Named-range hints (so you can wire to your spreadsheet/JSON cleanly)

Suggested names (examples—map to your style):

- `DSP01a_MWCO_kDa`, `DSP01a_Target_VRR`, `DSP01a_Flux_LMH`, `DSP01a_TMP_bar`, `DSP01a_Area_m2`, `DSP01a_Recovery_pct`, `DSP01a_Time_h`, `DSP01a_Energy_kWh`, `DSP01a_Membrane_Life_batches`
- `DSP01b_ND`, `DSP01b_Buffer_m3`, `DSP01b_ResidualConductivity_mScm`, `DSP01b_Time_h`, `DSP01b_Recovery_pct`
- `DSP01c_Stages`, `DSP01c_CF_per_stage`, `DSP01c_Total_CF`, `DSP01c_Area_m2`, `DSP01c_Recovery_pct`, `DSP01c_Time_h`
- `DSP01d_SteadyFlux_LMH`, `DSP01d_Uptime_frac`, `DSP01d_Qp_m3ph`, `DSP01d_Bleed_m3ph`, `DSP01d_Area_m2`, `DSP01d_CampaignDays`, `DSP01d_Recovery_pct`

------

## High-value experiments to tighten the model fast

- Flux vs. TMP curves at two crossflow velocities on **post-depth-filter broth**.
- Short **UF→DF** sequence measuring $S_p$ for OPN (simple mass balance).
- **SPTFF** pilot: measure per-stage TMP and recovery vs. CF.
- **CIP cycles**: flux recovery vs. cycle count; set membrane lifetime.

------

If you want, I can generate a compact **parameter defaults JSON** for DSP01a–d and a **one-pager of equations** you can paste into your Codex prompts to scaffold the BioSTEAM design/cost methods.

##### You said:

For clarity, our next step is AEX chromatography, where concentration is crucial. This process will also remove small molecular weight proteins and media components that could interfere with the binding capacity of the column. The protein of interest binds at relatively high ionic concentrations (less than 200 mM), and reducing the volume is primarily necessary to decrease the loading time of the column. There is a certain amount of DNA present that binds and elutes from the column so we may want to consider implementing a benzonase step prior to the concentration to reduce the competing binding capacity for the column. These factors may change your recommendation for preferred operations.

###### ChatGPT said:

Thought for 15s

Got it—since the very next step is **AEX bind-and-elute** and your main motive for DSP01 is **load-time reduction** (not big buffer exchange), we’ll tune the block for: (i) **volume cut** without over-stripping salts, (ii) **low DNA** to avoid capacity theft and pressure spikes, and (iii) **stable, column-friendly conductivity** (<~200 mM where your protein still binds).

Here’s the tightened plan.

# What changes with AEX next?

- **Minimize diafiltration.** If your protein binds up to ~200 mM, you don’t need deep conductivity reduction—keep ionic strength “AEX-friendly,” not ultra-low.
- **Prioritize fast, gentle concentration.** You want a **CF that matches your target column load time**, not the absolute maximum CF.
- **Knock down DNA before concentration.** DNA eats AEX capacity, raises viscosity/fouling, and can co-elute. A **benzonase + Mg²⁺** pretreatment pays for itself in resin productivity and lower ∆P.

------

# Updated route recommendation (pre-AEX)

**Default (batch upstream):**
 **Disc-stack → depth filter → Benzonase digest → depth filter (polish) → SPTFF (CF 3–6×) → (optional) light DF to target conductivity → 0.2 µm guard → AEX**

Why SPTFF instead of batch UF here? Because your goal is primarily **load-time control** with **minimal tank time and minimal conductivity drift**. SPTFF gives you clean, predictable CF with less recirculation; if your skid fleet is batch-UF-only, then **Batch UF → Short DF** is the fallback.

**Continuous/perfusion variant:**
 **Disc-stack → depth filter → inline Benzonase loop (cSTR) → cTFF to steady CF → 0.2 µm guard → AEX**

------

# How to pick between DSP01a–d under AEX constraints

| Goal                                                       | Pick                             | Why                                                          |
| ---------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------ |
| Fast volume cut, keep conductivity roughly where it is     | **DSP01c SPTFF**                 | Inline CF (2–6×) with minimal mixing/tankage; great handoff to AEX load. |
| You only have batch skids, not SPTFF manifolds             | **DSP01a UF (batch)**            | Then **stop at the CF needed for load-time**; don’t “over-CF” just because you can. |
| Need small correction to conductivity (e.g., 220 → 150 mM) | **DSP01b Diafiltration (short)** | 0.5–2 diavolumes max; keep it surgical.                      |
| Running a steady capture feed from perfusion               | **DSP01d cTFF**                  | Steady CF with uptime control; pairs well with periodic AEX cycling. |

------

# Set the **CF target** from column economics (don’t guess)

Let:

- $V_{\text{feed}}$ = volume from clarification (m³)
- $m_p$ = mass of protein per batch (kg)
- $Q_L$ = permissible AEX **load flow** (m³/h) at your linear velocity/residence time
- $t_{\text{load,target}}$ = desired **max** load time (h)

Then the **minimum concentration factor** to meet load time is:
$$
\text{CF}_{\text{time}} = \frac{V_{\text{feed}}}{Q_L \cdot t_{\text{load,target}}}
$$
Pick **CF = max(1, CF$_{\text{time}}$)**, but **cap CF** if viscosity or TMP limits bite. There’s no prize for going beyond the load-time need.

**Tip:** sanity-check that the concentrated pool conductivity stays ≤ your ~200 mM binding ceiling. If your feed is near the ceiling already, either (i) take a slightly **lower CF** or (ii) follow with **0.5–1.0 DV DF** to nudge conductivity back into the comfort zone.

------

# Benzonase step (add before concentration)

**Purpose:** Slash DNA (and viscosity) to free AEX capacity and lower fouling risk.

**Where:** After primary depth filtration (to remove cells/debris), **before** UF/SPTFF.

**Operating spec (practical defaults, tune with trials):**

- **Enzyme:** Benzonase (or equivalent endonuclease)
- **Dose:** 25–100 U/mL of process fluid (start at **50 U/mL**); scale with DNA load
- **Cofactor:** **MgCl₂ 1–2 mM** in the mix tank
- **pH:** 7.5–8.5 typical (check your protein’s stability window)
- **Temp:** 20–30 °C (room temp works; 30–37 °C is faster if stable)
- **Hold:** **30–60 min** with gentle mixing; target **>90–99 % DNA reduction**
- **Quench options:** cool to process temp; optional **EDTA 1–5 mM** if you need to stop activity before AEX (only if EDTA won’t harm AEX binding)
- **Follow with:** a **fine depth filter** (0.5–1 µm grade) to remove any floc/complexes

**BioSTEAM unit hook (high-level):**

- **Inputs:** DNA_in (mg/L), enzyme_units_per_mL, Mg²⁺ (mM), time (min), T (°C)
- **Kinetics:** pseudo-first order on DNA mass (or fixed log-reduction table vs time & dose)
- **Outputs:** DNA_out, added mass of enzyme, MgCl₂, salts
- **Costs:** enzyme $/kU, MgCl₂ $/kg, mixing time/energy

**AEX impact to model:**

- **Resin capacity reclaimed (ΔDBC):** model as proportional to DNA reduction (empirical fit once you have runs).
- **Pressure benefit:** include viscosity drop factor after DNA cut (often noticeable at scale).

------

# DSP01 specs tuned for AEX handoff

## DSP01c — **Single-Pass TFF** (recommended in this context)

- **Overall CF:** **2–6×** (set from load-time equation)
- **Stages:** 2–3; per-stage CF ~1.6–2.0×
- **Flux:** 70–100 LMH (guarded by TMP ≤1.2 bar)
- **CFV:** 1.8–2.5 m/s
- **Protein sieving per stage:** 0.3–1.0 % (choose MWCO 30 kDa; confirm on OPN)
- **Recovery:** **≥99 %** typical for 3-stage 5–6× CF if adsorption is low
- **Conductivity drift:** small; if concentrated feed creeps close to 200 mM, add **0.5–1 DV DF**
- **Notes:** Lower tank time and fewer “heat/air” cycles than batch UF; very column-friendly.

## DSP01a — **UF (batch)** (fallback or if skids are batch-only)

- **Target VRR:** from CF$_{\text{time}}$ (often **3–6×**)
- **Flux start:** 80–100 LMH; ramp/derate with fouling (keep TMP ≤1.5 bar)
- **Recovery:** 98–99.5 % (watch adsorption on high area)
- **Conductivity:** may rise modestly during concentration; correct with **short DF** if needed

## DSP01b — **Diafiltration** (use lightly)

- **Goal:** correct conductivity into your AEX binding window—not desalinate deeply
- **DV:** **0.5–2.0 DV** usually enough (e.g., 220 → 150 mM)
- **Loss model:** protein sieving × DV + adsorption; keep **total loss <1–2 %**
- **Buffer:** choose AEX-compatible buffer (pH & counter-ion identical to load buffer)

## DSP01d — **cTFF** (continuous)

- **Setpoint:** steady CF to meet average column cycle time
- **Uptime:** 0.94–0.98 with scheduled CIP; start-up hold-up loss amortized
- **Use case:** perfusion or continuous AEX where load cadence is fixed

------

# Guardrails & quick checks

1. **Conductivity check (after DSP01):**
    If $C_{\text{out}} > C_{\text{bind,max}}$ (≈ 200 mM), apply **0.5–1.0 DV DF** or reduce CF.
2. **Viscosity/TMP limit at CF target:**
    If viscosity exceeds your pump/∆P guardrail, reduce CF or increase area/stages.
3. **DNA residual:**
    If AEX DBC still low or pressure high, increase benzonase dose/time (or add a short heat-hold if product tolerates it).
4. **Protein recovery budget:**
    Keep total losses across digest + filters + TFF **<2 %** before AEX.

------

# Suggested defaults to drop into your parameter pack

**Benzonase step**

- `BZN_Dose_U_per_mL = 50`
- `BZN_MgCl2_mM = 2`
- `BZN_Time_min = 45`
- `BZN_Temp_C = 25`
- `BZN_Target_LogReduction_DNA = 2.0` (99%)
- `BZN_Quench_EDTA_mM = 0` (set >0 only if required)

**SPTFF (preferred)**

- `DSP01c_CF_Target = from load-time` (often 3–6)
- `DSP01c_Stages = 3`
- `DSP01c_J_LMH = 85`
- `DSP01c_TMP_bar_max = 1.2`
- `DSP01c_CFV_ms = 2.0`
- `DSP01c_MWCO_kDa = 30`
- `DSP01c_Sieving_Protein = 0.005`
- `DSP01c_Recovery_pct_expected = 99.0`

**UF (batch) + short DF (fallback)**

- `DSP01a_VRR_Target = from load-time`
- `DSP01a_J0_LMH = 90` with fouling coefficient `kf = 0.2 1/h`
- `DSP01a_TMP_bar_max = 1.5`
- `DSP01b_DV = 0.5–1.0` (only if conductivity > target)

**AEX-handshake**

- `AEX_Bind_Conductivity_mM_max = 200`
- `AEX_Load_Flow_m3ph = your skid limit`
- `AEX_Load_Time_h_target = 6–10` (set your preference)
- `CF_Time_Min = V_feed / (AEX_Load_Flow * AEX_Load_Time)`

------

# Integration notes you can wire today

- Add a **“DNA_competition_factor”** that subtracts from effective DBC and **scales with DNA (mg/L)** pre-AEX; let the benzonase unit write a **DNA_out** value that drives that factor.
- Let DSP01 units consume a **“Conductivity_in_mM”** and output **“Conductivity_out_mM”** using a simple mixing/DF model; trigger a **DF_top-off** only if **Conductivity_out_mM > AEX_Bind_Conductivity_mM_max**.
- Expose a **“CF_from_load_time()”** helper to compute the minimum CF needed for your chosen AEX load window.