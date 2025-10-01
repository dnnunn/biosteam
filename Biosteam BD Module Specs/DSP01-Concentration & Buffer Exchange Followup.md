# What to expect in the real world (conservative baselines)

## DSP01a — UF Concentration (batch TFF)

- **Flux (post-clarification yeast supernatant):** plan **65–90 LMH** average across the run (start higher, derate). Keep **TMP ≤1.2–1.5 bar**; **CFV ~2.0 m/s**. (Vendor guides show higher numbers in gentle feeds, but yeast broths + antifoam are punishing—stay modest.) [Sartorius+1](https://www.sartorius.com/download/1701264/tff-portfolio-brochure-en-b-pdf-data.pdf?utm_source=chatgpt.com)
- **VRR:** design **3–6×**; push beyond 6× only if you can confirm viscosity <~8 mPa·s and TMP under cap.
- **Protein losses:** budget **1.0–2.0%** total (sieving + adsorption + hold-up) at VRR 3–6× with a 30 kDa PES. Literature reminds us that even tiny sieving (So≈0.01) stacks up over large VCF/ND; don’t assume “zero loss.” [aiche.onlinelibrary.wiley.com](https://aiche.onlinelibrary.wiley.com/doi/pdf/10.1002/btpr.3481?utm_source=chatgpt.com)
- **Step recovery:** **98–99%** (baseline: **98.5%**).

## DSP01b — Diafiltration (constant-volume)

- **Diavolumes:** for AEX hand-off, keep it **surgical: 0.5–2.0 DV** (e.g., 220 → 140–180 mM). Deep desalting (≥3 DV) costs time/buffer and compounds sieving loss—avoid unless analytics force it. The textbook residual **f = e^(-ND)** is a good planning rule. [dcvmn.org](https://dcvmn.org/wp-content/uploads/2018/02/4._application_note_-_a_hands-on_guide_to_ultrafiltration-diafiltration_optimization.pdf?utm_source=chatgpt.com)
- **Flux:** **80–110 LMH** (viscosity-dependent), **TMP ≤1.2 bar**.
- **Protein losses:** plan **0.3–1.0%** across **1–2 DV** (use **Sp^DF ~0.005–0.01**); at higher ND, add proportionally (AIChE 2024 shows how small So erodes yield with large ND). [aiche.onlinelibrary.wiley.com](https://aiche.onlinelibrary.wiley.com/doi/pdf/10.1002/btpr.3481?utm_source=chatgpt.com)
- **Step recovery:** **99–99.7%** at **≤1–2 DV**; **97–99%** if you push to **3–5 DV**.

## DSP01c — Single-Pass TFF (SPTFF)

- **Use case:** quickest way to hit a **column load-time CF** without tank gymnastics.
- **Overall CF:** **2–4×** as the **default ceiling**; design **per-stage CF 1.5–1.8×**, **2–3 stages**. (Yes, >5× is often shown in app notes; don’t set that as your baseline until you’ve piloted.) [Repligen+1](https://www.repligen.com/ctech-resources/pdf/Bristol-Myers-Squibb_Ultrafiltration-of-Partially-and-Completely-Retained-Proteins-Single-Pass-Tangential-Flow-Filtration.pdf?utm_source=chatgpt.com)
- **Flux/TMP:** **70–90 LMH**, **per-stage TMP ≤1.0–1.2 bar**; **CFV 1.8–2.5 m/s**.
- **Losses:** budget **0.8–1.5%** total (cumulative sieving + adsorption + hold-up across stages).
- **Step recovery:** **98.5–99.2%** (baseline: **99.0%**).

## DSP01d — Continuous TFF (cTFF)

- **Steady-state flux:** **70–85 LMH** under **TMP ≤1.0–1.2 bar**; **uptime 0.92–0.96** with 24–72 h CIP windows. [BioProcess International+1](https://www.bioprocessintl.com/continuous-bioprocessing/is-continuous-downstream-processing-becoming-a-reality-?utm_source=chatgpt.com)
- **Start-up loss:** amortize **0.2–0.5 DV** of hold-up across the campaign.
- **Step recovery:** **98–99%** (depends on sieving/adsorption rate and hold-up).
- **Membrane life (campaign):** plan **10–20 days** before meaningful flux recovery decline (cleaning factor 0.85–0.9).

------

# AEX-aware guardrails (tightened)

- **Pick CF from load-time, not bravado.**
   $\text{CF}_{\min} = \dfrac{V_{\text{feed}}}{Q_L \cdot t_{\text{load target}}}$. Then **cap CF at 4×** by default; only raise after a viscosity/TMP check passes with real broth. 
- **Conductivity:** If **>200 mM** post-DSP01, use **0.5–1.0 DV DF** (not 3+ DV). 
- **DNA:** keep **benzonase** upstream; it pays back on AEX DBC and TFF foul-rate. (You already spec’d 50 U/mL, 30–60 min—keep it.) 

------

# Conservative “drop-in” defaults for BioSTEAM (use these until plant data say otherwise)

## Shared

- `MWCO_kDa = 30` (PES)  [Sartorius](https://www.sartorius.com/download/1701264/tff-portfolio-brochure-en-b-pdf-data.pdf?utm_source=chatgpt.com)
- `TMP_bar_cap = 1.2` (SPTFF/cTFF), `1.5` (batch UF/DF)
- `flux_LMH` (design): UF **80**; DF **90**; SPTFF **80**; cTFF **75**
- `sieving_protein = 0.01` (UF), `0.005–0.01` (DF), `0.003–0.01` (SPTFF per stage)  [aiche.onlinelibrary.wiley.com](https://aiche.onlinelibrary.wiley.com/doi/pdf/10.1002/btpr.3481?utm_source=chatgpt.com)
- `adsorption_loss_frac_per_100m2 = 0.001–0.003`

## UF (DSP01a)

- `target_VRR = 4` (cap 6)
- `recovery = 0.985` (range 0.98–0.99)

## DF (DSP01b)

- `ND = 1` (cap 2 for AEX trim)
- `recovery = 0.995` at ND≤1; `0.99` at ND≈2

## SPTFF (DSP01c)

- `stages = 3`, `CF_per_stage = 1.6` → total CF ≈ **4.1×**
- `recovery = 0.99`

## cTFF (DSP01d)

- `uptime = 0.94`
- `startup_loss_DV = 0.3`
- `recovery = 0.985–0.99` (baseline 0.987)

------

# Why these are conservative (and not pessimistic)

- **SPTFF:** Application papers show high CF in one pass, but those are optimized proteins/conditions; using **2–4×** as the baseline keeps pressure/viscosity in a safe box for yeast supernatants. [Repligen+1](https://www.repligen.com/ctech-resources/pdf/Bristol-Myers-Squibb_Ultrafiltration-of-Partially-and-Completely-Retained-Proteins-Single-Pass-Tangential-Flow-Filtration.pdf?utm_source=chatgpt.com)
- **UF/DF sieving:** Recent analyses quantify how **So≈0.01** still bites at large **VCF/ND**; that’s exactly why we budget **1–2%** losses instead of pretending 99.9% retention means 99.9% step yield. [aiche.onlinelibrary.wiley.com](https://aiche.onlinelibrary.wiley.com/doi/pdf/10.1002/btpr.3481?utm_source=chatgpt.com)
- **Flux:** Vendor brochures and handbooks advertise wide ranges; I’ve chosen the **lower middle** of those windows for yeast feeds (not CHO harvest water). [Sartorius+1](https://www.sartorius.com/download/1701264/tff-portfolio-brochure-en-b-pdf-data.pdf?utm_source=chatgpt.com)
- **Continuous:** Real campaigns include **CIP downtime**; uptime **≤0.96** is a safer financial assumption than “98–99%” unless you’ve run that train. [BioProcess International+1](https://www.bioprocessintl.com/continuous-bioprocessing/is-continuous-downstream-processing-becoming-a-reality-?utm_source=chatgpt.com)

------

# Simple TEA rules (so your model can’t over-promise)

1. **Stop at the CF the column needs.** No extra CF unless the viscosity check passes. 
2. **DF only to spec.** ND ≤ 2 by default; each extra DV adds loss and time. [dcvmn.org](https://dcvmn.org/wp-content/uploads/2018/02/4._application_note_-_a_hands-on_guide_to_ultrafiltration-diafiltration_optimization.pdf?utm_source=chatgpt.com)
3. **Benzonase before membranes.** It’s cheaper than over-sizing AEX and fighting DP. 
4. **Red flag any run where** `TMP>cap`, `viscosity>8 mPa·s`, or `CF>4×` at baseline area.