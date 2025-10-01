# DSP03 — Concentration & Buffer Exchange (conservative defaults)

## What we’re designing for

- **Goal:** deliver a column-friendly or dryer-friendly pool (volume & conductivity spec) with **minimal over-processing**.
- **Feeds:** either **DSP02_AEX** pool (usually moderate conductivity) or **DSP02_Chitosan** pool (pH-mode elution: moderate cond.; polyP-mode: anion burden → needs short DF).
- **Reality bias:** yeast supernatants + antifoam foul membranes; we pick **boringly safe flux/TMP** and **count hold-up/adsorption**.

------

## Variant A — **UF (batch TFF)** for concentration

- **Flux (average across run):** **65–90 LMH** (start higher, derate; antifoam → lower end).
- **TMP cap:** **≤1.5 bar** (stay below 1.2 if viscosity climbs).
- **CFV:** ~**2.0 m/s**.
- **VRR target:** **3–6×** (cap 6× unless you’ve confirmed viscosity <~8 mPa·s at outlet).
- **Protein losses:** **1.0–2.0%** total (sieving + adsorption + hold-up).
- **Step recovery:** **98–99%** (baseline **98.5%**).

**Use when:** you have batch skids and simply need a CF tied to column load time or to reduce hold/transfer times.

------

## Variant B — **Diafiltration (batch, constant-volume)** for small conductivity trims (and polyP removal)

- **DV (diavolumes):** **0.5–2.0 DV** for normal AEX hand-off; **avoid deep DF** unless analytics force it.
- **Flux:** **80–110 LMH**, **TMP ≤1.2 bar**.
- **Protein losses:** **0.3–1.0%** across **1–2 DV** (assume sieving Sp^DF = 0.005–0.01; adsorption small but non-zero).
- **Residual rule:** $f = e^{-ND}$ for passing species (salts/polyP).
- **Step recovery:** **99–99.7% (≤2 DV)**; **97–99% (3–5 DV)**.

**Use when:** you need to nudge conductivity into the AEX bind window or must **clear polyP** after chitosan competitive elution (typ. **2 DV**).

------

## Variant C — **SPTFF (single-pass)** for fast, in-line CF

- **Overall CF:** **2–4×** baseline (use **1.5–1.8× per stage**, **2–3 stages**).
- **Flux / TMP per stage:** **70–90 LMH**, **TMP ≤1.0–1.2 bar**; **CFV 1.8–2.5 m/s**.
- **Losses:** **0.8–1.5%** total (cumulative sieving + adsorption + hold-up).
- **Step recovery:** **98.5–99.2%** (baseline **99.0%**).

**Use when:** you want to hit a **load-time CF** with **minimal tank time** and keep conductivity largely unchanged.

------

## Variant D — **cTFF (continuous)** for steady campaigns

- **Steady-state flux:** **70–85 LMH**, **TMP ≤1.0–1.2 bar**.
- **Uptime:** **0.92–0.96** (24–72 h CIP cadence).
- **Start-up loss:** amortize **0.2–0.5 DV** of hold-up per campaign.
- **Step recovery:** **98–99%** (baseline **98.7%**).

**Use when:** perfusion/continuous cadence or fixed-rhythm loading to capture.

------

## Route-aware playbook (what DSP03 actually runs)

- **After AEX (DSP02_AEX):**
   If conductivity already ≤ bind/next-step target → **SPTFF 2–4×** (or **UF 2–4×**).
   If slightly high → **DF 0.5–1.0 DV**, then **SPTFF/UF** **only if** you still need volume cut.
- **After Chitosan pH-mode:**
   Conductivity moderate; run **SPTFF 2–4×** (or **UF**) without DF unless a small nudge is needed.
- **After Chitosan polyP-mode:**
   **DF 1–2 DV** first to clear polyP (count its yield/time cost), then **SPTFF/UF** if you need CF.

------

## Guardrails (make the unit refuse to over-promise)

- **Viscosity/TMP limit:** If predicted **TMP>cap** or **viscosity>8 mPa·s** at target CF → **increase area or lower CF**.
- **DF cap:** ND > **2** triggers a warning (“deep DF erodes yield/time; revisit specs”).
- **PolyP presence:** **Force DF ≥1 DV** before any IEX polish; do not “hope” polish ignores polyP.
- **Antifoam flag:** Derate flux **−20–30%** and raise adsorption loss by **+0.2–0.5%**.

------

## Drop-in defaults for BioSTEAM (replace when plant data land)

**Shared knobs**

- `MWCO_kDa = 30` (PES)
- `TMP_bar_cap = 1.2` (SPTFF/cTFF), `1.5` (UF/DF)
- `sieving_protein = 0.01 (UF), 0.005–0.01 (DF), 0.003–0.01 (SPTFF per stage)`
- `adsorption_loss_per_100m2 = 0.001–0.003`

**UF**

- `flux_LMH = 80`, `target_VRR = 4` (cap 6), `recovery = 0.985`

**DF**

- `flux_LMH = 90`, `ND = 1` (cap 2), `recovery = 0.995 (ND≤1)`; `0.99 (ND≈2)`

**SPTFF**

- `flux_LMH = 80`, `stages = 3`, `CF_per_stage = 1.6` → total CF ≈ 4.1×, `recovery = 0.99`

**cTFF**

- `steady_flux_LMH = 75`, `uptime = 0.94`, `startup_loss_DV = 0.3`, `recovery = 0.987`

**Economics (CDMO)**

- Always cost **membranes, disposables, buffers, labor, waste**; keep skid CAPEX **flagged** (excluded) unless `Ownership_Mode="InHouse"`.

------

## Equations you’ll wire (compact)

- **UF area:** $A \ge \dfrac{V_0 - V_f}{J_{\text{avg}} \, t}$, with $J_{\text{avg}} = \dfrac{J_0}{1+k_f \cdot V/A}$ or $J_0 e^{-k_f t}$.
- **DF clearance:** residual $f = e^{-ND}$; protein loss $ \approx S_p^{DF}\cdot ND + \text{adsorption}$.
- **SPTFF stage check:** $A_i \ge Q_{in,i}/J$ with **per-stage TMP ≤ cap**; total CF = $\prod CF_i$.
- **cTFF steady state:** $Q_{in} = Q_p + Q_{bleed}$; hold concentration with bleed; amortize start-up DV.
- **Recovery (each):** $1 - (\text{sieving} + \text{adsorption} + \text{hold-up})$.

------

## Why these numbers are conservative

- Yeast supernatants routinely underperform brochure flux; **65–90 LMH** averages are realistic with antifoam.
- **Small sieving** (So≈0.005–0.01) **still** erodes yield with large ND/VCF — we budget **1–2%** losses rather than pretending “zero.”
- **SPTFF** can hit high CF, but we set **2–4×** as everyday reliable until pilot data prove more.
- Continuous trains **do** lose time to CIP; assuming **0.94 uptime** avoids fantasy capacity.