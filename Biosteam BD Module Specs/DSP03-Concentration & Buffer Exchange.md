DSP03 module: class map (conceptual)
DSP03BaseMembrane (abstract)
├─ DSP03a_UF          # batch ultrafiltration concentration
├─ DSP03b_DF          # batch diafiltration (constant volume)
├─ DSP03c_SPTFF       # single-pass TFF (multi-stage inline CF)
└─ DSP03d_cTFF        # continuous TFF (steady CF ± continuous DF)


Each subclass implements the same public API so downstream steps don’t care which you used.

Common data contract
Inputs (all variants read these)

feed_volume_m3

feed_opn_conc_gL

feed_pH

feed_conductivity_mM

feed_DNA_mgL

ownership_mode ∈ {CDMO,InHouse}

include_capex (bool; ignored if ownership_mode=CDMO)

Membrane & ops (client-borne)

mwco_kDa (default 30)

flux_LMH (steady or start value)

tmp_bar_cap (hard limit)

cfv_ms

sieving_protein (fraction)

adsorption_loss_per_100m2 (fraction)

membrane_cost_usd_per_m2

membrane_life_batches or membrane_life_campaign_days

disposables_usd_per_batch

buffer_fee_usd_per_m3 (DF & flush)

ops_labor_h_per_batch, ops_rate_usd_per_h

waste_disposal_usd_per_tonne

Flag from DSP02 (route awareness)

polyP_mM (0 for AEX route; >0 for chitosan polyP elution)

needs_df_flag (bool)

needs_fines_guard_flag (bool)

Outputs (all variants write these)

DSP03_Pool_Volume_m3

DSP03_OPN_Conc_gL

DSP03_pH

DSP03_Conductivity_mM

DSP03_DNA_mgL

DSP03_Chitosan_ppm (usually 0 unless propagated)

DSP03_Step_Recovery_pct

DSP03_Time_h

DSP03_ClientCost_usd

DSP03_CAPEX_Flagged_usd (report, exclude in CDMO)

Base class: DSP03BaseMembrane (abstract)
Responsibilities

Hold shared parameters.

Enforce client-vs-CAPEX cost separation.

Provide common validation & warnings (TMP, viscosity proxy, flux sanity, DF need for polyP).

Orchestrate handoff object creation for DSP04.

Required abstract methods (to implement per subclass)

_size_and_schedule() → returns area_m2, process_time_h, optional stages/parallel_modules

_compute_performance() → returns recovery_frac, protein_loss_breakdown, outlet_conductivity_mM, outlet_pH

_compute_buffers() → returns dict of buffer/flush volumes { "DF_m3": x, "flush_m3": y }

_compute_client_costs() → uses area, buffers, disposables, labor, waste

_compute_flagged_capex() → skid+install+maint (return 0 in CDMO)

Built-in validations (raise warning strings)

tmp_est_bar > tmp_bar_cap → suggest ↑ area or ↓ CF/flux

polyP_mM > 0 and DF_m3 == 0 → block (polyP must be cleared)

recovery_total < recovery_floor (e.g., <95% unless user set lower)

flux_LMH out of typical range (sanity light, not a blocker)

Subclasses
1) DSP03a_UF (batch UF concentration)

Extra inputs

target_VRR (e.g., 2–6)

kf_fouling_per_h (or per V/A)

time_h_cap (optional)

Sizing

Retentate volume 
𝑉
𝑓
=
𝑉
0
/
𝑉
𝑅
𝑅
V
f
	​

=V
0
	​

/VRR

Average flux derate: J_avg = J0 / (1 + kf * (V_removed / area)) or J0*exp(-kf*t)

area_m2 ≥ (V0 - Vf) / (J_avg * time_window_h)

Performance

Recovery ≈ 1 – sieving – adsorption – holdup

Conductivity rises slightly; pH unchanged (unless modeled)

Buffers

Flush/CIP volumes (parameterized)

2) DSP03b_DF (batch diafiltration)

Extra inputs

DV (0.3–3.0)

target_residual_fraction (optional; compute DV = −ln(f))

Performance

Passing solutes residual f = exp(-DV) (polyP, salt)

Protein loss ≈ sieving_DF * DV + adsorption

Buffers

DF_m3 = DV * V_hold (retentate volume during constant-volume DF)

Notes

If polyP_mM>0, enforce minimum DV (e.g., ≥2 unless user overrides)

3) DSP03c_SPTFF (single-pass)

Extra inputs

stages (2–3)

CF_per_stage (1.6–2.0)

tmp_bar_cap_stage (≤1.2)

Sizing

For each stage i: area_i = Q_in_i / flux_LMH

Guard check: pressure escalation across stages; if TMP estimate exceeds cap, ↑ area_i

Performance

Overall CF = Π CF_i (target 2–6×)

Recovery ≈ 1 – Σ(stage_sieving) – adsorption – holdup

Buffers

Minimal (forward flush); DF rarely used unless small top-off

4) DSP03d_cTFF (continuous)

Extra inputs

steady_flux_LMH

uptime_fraction (0.94–0.98)

bleed_rate_m3ph (to hold concentration)

continuous_DF_DV_per_h (optional)

Mass balance (steady)

Q_in = Q_perm + Q_bleed

Concentration setpoint via Q_bleed and membrane area.

Performance

Start-up hold-up loss (0.2–0.5 DV) amortized across campaign

Recovery similar to UF/SPTFF but quoted per day and per campaign

Buffers

If continuous DF enabled: DF_rate = DV_per_h * V_hold

Cost model (all subclasses use same formula skeleton)

Client costs (always included)

Membrane amortization
membrane_cost_per_m2 * area_m2 * (batch_fraction_of_life)

Disposables
disposables_usd_per_batch

Buffers
buffer_fee_usd_per_m3 * total_buffer_m3

Labor
ops_labor_h_per_batch * ops_rate_usd_per_h

Waste
waste_mass_t * waste_disposal_usd_per_tonne

Flagged CAPEX (only if InHouse)

skid_capex * install_factor → annualized + maintenance%

(Have base class return both; your TEA adds or excludes based on ownership_mode.)

Handoff object (to DSP04)

Create a simple record the base class fills for all variants:

DSP03Handoff:
  volume_m3
  opn_conc_gL
  pH
  conductivity_mM
  DNA_mgL
  chitosan_ppm
  recovery_frac
  time_h
  client_cost_usd
  capex_flagged_usd
  notes / warnings [list]


DSP04 reads only this.

Route-aware selector (tiny rules you can keep in a controller)

If polyP_mM > 0 → run DSP03b_DF (DV 1–3) then DSP03c_SPTFF (CF 2–4×) if you still need volume cut.

Else prefer DSP03c_SPTFF (CF 2–4×).

If campaign steady-state → choose DSP03d_cTFF (set CF & optional DF rate).

Fall back to DSP03a_UF when only batch UF skids are available or you want higher CF at lower control complexity.

Validation & warnings (standardize strings)

"TMP cap exceeded; increase area or reduce CF/flux."

"Polyphosphate detected; DF required but DV=0."

"Projected recovery below floor (set by user): X% < Y%."

"Flux outside recommended window for feed viscosity—expect fouling (kf↑)."

"Chitosan fines flag from DSP02 present; add 0.2 µm guard before membranes."

Minimal parameter presets (sane defaults)

mwco_kDa=30

flux_LMH=90 (UF), 85–95 (SPTFF), 80 (cTFF)

tmp_bar_cap=1.5 (UF/DF), 1.2 (SPTFF)

cfv_ms=2.0

sieving_protein=0.01 (UF), 0.005 per stage (SPTFF)

adsorption_loss_per_100m2=0.001

kf_fouling_per_h=0.2 (UF)

target_VRR=3 (UF), stages=3, CF_per_stage=1.7 (SPTFF), DV=0.5 (small tweak), DV=2.0 (polyP removal)

Membrane economics: membrane_cost_usd_per_m2=250, membrane_life_batches=30 (batch) or membrane_life_campaign_days=20 (cTFF)

Ops: disposables_usd_per_batch=500, buffer_fee_usd_per_m3=50, ops_labor_h_per_batch=8, ops_rate_usd_per_h=80, waste_disposal_usd_per_tonne=220

(Swap in your actual numbers when you have them.)

Integration checklist (so you only wire once)

Implement DSP03BaseMembrane with the abstract hooks and the client vs CAPEX split.

Implement the four subclasses using the sizing/performance rules above.

Build a tiny DSP03Selector that chooses and runs one subclass, then returns a DSP03Handoff.

Ensure DSP04 only accepts DSP03Handoff—no peeking at internals.

Add unit tests with synthetic feeds:

AEX route: no DF; SPTFF CF 3×

Chitosan-polyP: DF 2 DV then SPTFF CF 2×

cTFF campaign: 72 h, uptime 0.95, membrane life in days

That’s it. With this scaffold, swapping UF↔SPTFF↔cTFF later is a two-line config change, and CDMO vs in-house remains a single toggle while membranes/buffers/disposables are always fully costed.

# 0) What comes in from DSP02 (canonical inputs)

Both capture routes must populate the same fields (you already built this):

- `DSP02_Pool_Volume_m3`, `DSP02_OPN_Conc_gL`, `DSP02_pH`, `DSP02_Conductivity_mM`
- `DSP02_DNA_mgL`, `DSP02_Chitosan_ppm` (0 for AEX), `DSP02_PolyP_mM` (0 unless polyP)
- `DSP02_Step_Recovery_pct`
- Flags: `DSP02_Needs_DF_Flag`, `DSP02_Needs_Fines_Polish_Flag`

DSP03 consumes only these. It does **not** peek inside the AEX/Chitosan internals.

------

# 1) What DSP03 must output (handoff to DSP04)

**DSP03 handoff contract:**

- `DSP03_Pool_Volume_m3`
- `DSP03_OPN_Conc_gL`
- `DSP03_pH`
- `DSP03_Conductivity_mM`
- `DSP03_DNA_mgL` (carry for analytics)
- `DSP03_Chitosan_ppm` (target ≤ spec; usually 0 after AEX path)
- `DSP03_Step_Recovery_pct`
- `DSP03_Time_h`
- `DSP03_Cost_per_batch` (CDMO pass-through; CAPEX flagged)

Downstream (DSP04) never cares *how* you got here.

------

# 2) Route-aware selection logic (what to run)

**Primary goal of DSP03:** prepare the capture pool for the next step (typically polish or formulation) by (i) hitting load/throughput targets and (ii) hitting ionic/pH specs—**with minimal extra processing.**

### If `Capture_Route = DSP02_AEX` (bind-and-elute):

- **Likely needs:** modest **concentration** (reduce tank/transfer times) and **little/no DF**, because AEX elution conductivity is already in a controlled window.
- **Recommended default:** **SPTFF (c)** to CF 2–4× *or* **UF (a)** to VRR 2–4×.
- **Add DF (b)** **only** if your AEX elution buffer leaves you outside the next step’s conductivity target.

### If `Capture_Route = DSP02_CHITOSAN`:

- **Elution mode = pH-mode (7.2–7.8)**:
  Conductivity is moderate, chitosan fines already knocked down in DSP02.
  → **SPTFF (c)** (CF 2–4×) or light **UF (a)**; **no DF** unless you need a small nudge.
- **Elution mode = polyP**:
  Eluate contains significant polyphosphate; downstream resins hate this.
  → **Short DF (b)** first (1–3 DV to clear polyP), then **SPTFF (c)** or **UF (a)** as needed.
  If you want fully in-line: **cTFF (d)** with **continuous DF** is elegant for campaigns.

**Rule of thumb:** if your only objective is *speed* (shorten transfer/hold), pick **SPTFF**; if you must change **conductivity**, pick **short DF** (and stop there); if you run **steady campaigns**, pick **cTFF**.

------

# 3) Unit blueprints (no code, just what to wire)

## DSP03a — UF Concentration (batch)

**Purpose:** Concentrate pool from $V_0\to V_f$ (VRR = $V_0/V_f$) with high retention.

- **Inputs:** `MWCO_kDa` (baseline 30), `Flux_LMH_start` (80–110), `TMP_bar_max` (≤1.5), `CFV_m_s` (≈2.0), `Target_VRR` (2–6), `Sieving_protein` (0.005–0.02), `Fouling_coeff_kf` (h⁻¹).
- **Sizing:** $A \ge \dfrac{V_0 - V_f}{J_{avg}\, t_{max}}$ with fouling derate $J_{avg} = J_0/(1+k_f\cdot V/A)$ or $J_0 e^{-k_f t}$.
- **Recovery:** $\ge 98{-}99.5\%$ (adsorption + sieving + hold-up).
- **When to prefer:** batch ops; skids on site; simple CF 2–4×.

## DSP03b — Diafiltration (batch, constant-volume)

**Purpose:** Adjust conductivity (and remove small anions like **polyP**) with minimal complexity.

- **Inputs:** `DV` (0.5–3.0), `Flux_LMH` (90–120), `Sieving_protein_DF` (0.003–0.01).
- **Clearance:** residual fraction $f = e^{-DV}$ (for fully passing species).
  Example: DV=2 → ~86% removal of polyP.
- **Recovery penalty:** $\approx S_p^{DF}\cdot DV + adsorption$.
- **When to prefer:** chitosan-polyP eluate; minor desalting tweaks.

## DSP03c — Single-Pass TFF (SPTFF)

**Purpose:** Inline concentration with minimal tank time and stable conductivity.

- **Inputs:** `Stages` (2–3), `CF_per_stage` (1.6–2.0), `Flux_LMH` (70–100), `TMP_bar_cap` (≤1.2), `MWCO_kDa` (30), `Sieving_per_stage` (0.3–1.0%).
- **Overall CF:** $\prod CF_i$ (target 2–6×).
- **Recovery:** $\ge 99\%$ typical with sane staging.
- **When to prefer:** fast handoff; CDMO parallelism; keep conductivity as-is.

## DSP03d — Continuous TFF (cTFF)

**Purpose:** Campaign-steady CF and/or continuous DF at set conductivity.

- **Inputs:** `Steady_Flux_LMH` (70–100), `Uptime_frac` (0.94–0.98), `Bleed_rate` (to hold concentration), optional `Continuous_DF_DV_per_h`.
- **Mass balance:** $Q_{in} = Q_{permeate} + Q_{bleed}$.
- **Start-up loss:** 0.2–0.5 DV of hold-up (amortize).
- **When to prefer:** long runs, perfusion-style cadence, tight rhythm to DSP04.

------

## Two tiny variants worth having

- **DSP03c-LT (“low TMP” SPTFF):** Same as SPTFF but stricter `TMP_bar_cap` (≤1.0) for very shear-sensitive campaigns; area ↑ a bit, fouling ↓.
- **DSP03b-Top-off DF:** Micro-DF of **0.3–0.7 DV** *after* UF/SPTFF to pull conductivity into a narrow target without blowing time/volume.

------

# 4) Route-aware decision table (what DSP03 does)

| Upstream (DSP02)           | Condition                            | DSP03 plan                                                   |
| -------------------------- | ------------------------------------ | ------------------------------------------------------------ |
| **AEX**                    | Conductivity within DSP04 target     | **SPTFF (c)** CF 2–4× (or UF (a) if skids)                   |
| **AEX**                    | Conductivity above target            | **Short DF (b)** 0.5–1.0 DV → then **SPTFF (c)** if you still want CF |
| **Chitosan–pH elution**    | PolyP = 0; chitosan fines under spec | **SPTFF (c)** CF 2–4× (or UF (a))                            |
| **Chitosan–polyP elution** | PolyP > 0                            | **DF (b)** 1–3 DV (target residual ≤10–20%) → **SPTFF (c)** or UF (a) |
| Any                        | Campaign/steady requirement          | **cTFF (d)** (optionally with continuous DF)                 |

**Guardrails**

- Viscosity/TMP limits at CF target → increase area or reduce CF.
- If `DSP02_Chitosan_ppm > spec` and fines weren’t cleared upstream → insert **guard 0.2 µm** before membranes (quick, cheap insurance).

------

# 5) Economics: CDMO-friendly (CAPEX flagged)

Use pass-throughs; keep CAPEX fields for later but **exclude** in CDMO rollups:

- **Membrane costs** ($/m²) with lifetime (batches or campaign days).
- **Buffer fees** (per m³ for DF).
- **Processing fee** (per m³ handled).
- **Labor** (h per batch × blended rate).
- **Disposables** (modules, housings).
- **Utilities** (electricity, water, CIP).
- **Waste** (polyP DF brine, filters).

------

# 6) Parameters to drop into your sheet/JSON

**Common**

- `DSP03_Target_CF` or `DSP03_Target_VRR`
- `DSP03_Target_Conductivity_mM`
- `DSP03_Max_TMP_bar`, `DSP03_Flux_LMH`, `DSP03_MWCO_kDa` (default 30)
- `DSP03_Sieving_Protein`, `DSP03_Adsorption_Loss_per_100m2`
- `DSP03_Insert_Guard0p2` (bool)

**UF (a)**

- `DSP03a_J0_LMH`, `DSP03a_kf_per_h`, `DSP03a_VRR_Target`, `DSP03a_Time_h_cap`

**DF (b)**

- `DSP03b_DV`, `DSP03b_Target_Residual_Fraction`, `DSP03b_J_LMH`

**SPTFF (c)**

- `DSP03c_Stages`, `DSP03c_CF_per_stage`, `DSP03c_J_LMH`, `DSP03c_TMP_cap_bar`

**cTFF (d)**

- `DSP03d_Steady_J_LMH`, `DSP03d_Uptime_frac`, `DSP03d_Bleed_rate_m3ph`, `DSP03d_DF_DV_per_h` (optional)

**Economics**

- `Membrane_Cost_USD_per_m2`, `Membrane_Life_batches` (or `Campaign_days`)
- `DF_Buffer_Fee_USD_per_m3`
- `Processing_Fee_USD_per_m3`, `Labor_h_per_batch`, `Labor_USD_per_h`
- `Utilities_USD_per_batch`, `Disposables_USD_per_batch`
- `Include_CAPEX` (False in CDMO), `Skid_CAPEX_Flagged`

------

# 7) Equations you’ll actually use

- **UF/SPTFF area**: $A \ge \dfrac{Q}{J}$, $Q$ chosen from time window or line rate.
  Fouling derate: $J_{avg}=J_0/(1+k_f\cdot V/A)$ or $J_0 e^{-k_f t}$.
- **DF clearance**: Residual fraction $f=e^{-DV}$ for passing species (polyP, salts).
  Choose DV so $f \le f_{target}$.
- **Recovery** (each variant):
  $Y \approx 1 - (\text{sieving}) - (\text{adsorption}) - (\text{hold-up})$.
  For SPTFF multi-stage, sum per-stage sieving and adsorption.
- **cTFF steady state**: $Q_{in}=Q_p+Q_{bleed}$, hold concentration setpoint via $Q_{bleed}$.
  Start-up hold-up loss amortized over campaign time.

------

# 8) Defaults (good starting points)

- **SPTFF default (recommended):** `Stages=3`, `CF_per_stage=1.6–1.8` → CF ~4–5×, `J=85–95` LMH, `TMP_cap=1.2` bar, `Recovery≈99.0%`.
- **UF default:** `VRR=3×`, `J0=90` LMH, `kf=0.2 h⁻¹`, `Recovery≈98.5–99.3%`.
- **DF defaults:** `DV=0.5` for small tweak; `DV=2` for polyP removal (~86%); `J=100` LMH.
- **cTFF:** `J=80` LMH, `Uptime=0.95`, `StartUpLoss=0.3 DV`.

------

# 9) Minimal adapter table in the sheet (one place only)

```
# Selector:
DSP03_Method :=
  SWITCH(TRUE,
    Capture_Route="DSP02_CHITOSAN" && DSP02_PolyP_mM>0, "DF+SPTFF",
    Capture_Route="DSP02_CHITOSAN",                     "SPTFF",
    /* AEX default */                                   "SPTFF"
  )

DSP03_Target_CF := from takt time or next-step load window
DSP03_Insert_DF := (DSP02_PolyP_mM>0) OR (DSP02_Conductivity_mM > DSP03_Target_Conductivity_mM)
```

Route-specific nuances are invisible to DSP04 because you always publish the **DSP03 handoff** fields.

------

# 10) Sanity lights (catch foot-guns early)

- **Conductivity not met:** `DSP03_Conductivity_mM > DSP04_Cond_max` → light red.
- **TMP/viscosity exceeded:** calculated TMP > cap → suggest more area / lower CF.
- **PolyP present but no DF selected:** block run (red).
- **Total recovery:** `DSP02_Step_Recovery_pct * DSP03_Step_Recovery_pct < 0.85` → warn.