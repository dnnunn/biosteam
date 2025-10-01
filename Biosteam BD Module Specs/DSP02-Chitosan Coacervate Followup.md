# DSP02 — Chitosan Coacervate (conservative defaults)

## What we’ll assume (yeast supernatant, secreted OPN)

- You operate in the validated window: **pH_bind ≈ 4.2 (3.8–5.0)**, **I_bind ≤ 150 mM**, **20–25 °C**, **hold 10–45 min**. Don’t assume “salt-agnostic” behavior; above ~150–250 mM capture drops. 

------

## A) Coacervation (DSP02-A)

**Baseline capture yield:** **85–90%** (range **80–95%**); set **90%** only with lab fit at your chosen **Rq**, pH, and ionic strength. Keep a salt-penalty on by default. 

**Charge ratio (Rq):** design in the **1.4–2.0** band (sweet spot), not 2.5+. Over-dosing drives unnecessary polymer cost and can worsen fines. 

**Derates to apply automatically**

- **Salt sensitivity:** −**15% per +100 mM** (placeholder) clipped to [0,1]. 
- **Off-optimum Rq:** quadratic penalty around the chosen Rq* (use your DoE fit; start with a mild parabola). 

**Mixer/scale cautions (loss guard):** add **0.5–1.0%** handling loss if you require high shear to disperse viscous feeds (keeps totals honest).

------

## B) Solid–liquid separation (DSP02-B)

**Preferred**: **Disc-stack** if flocs are compact (apparent d50 ≥ 3–5 µm); **Decanter** if bulky/compressible; **Depth filter** only as fallback (consumables spike). 

**Targets**

- **Centrate turbidity:** **<50–100 NTU**. 
- **Coacervate recovery:** assume **≤1%** breakage loss (conservative handle = **1%**).

------

## C) Wash of coacervate (DSP02-C)

**Default**: **1 wash @ 0.5 BV** (same pH, **0–50 mM** salt).
 **Loss budget:** **1.0% per wash** (range 0.5–2.0%). Don’t plan “free” washing. 

------

## D) Elution / release (DSP02-D)

Choose **one** mode per run; keep both in the model.

### Mode 1 — **pH-shift to 7.2–7.8 (recommended default)**

- **Elution yield (of captured):** **95–98%** baseline (use 97% only with lab proof).
- **Pros:** no polyP burden; chitosan remains insoluble → easy solid-liquid split; polish is cheaper.
- **Watch:** trace chitosan oligomers; polish will catch. 

### Mode 2 — **Polyphosphate (hexametaphosphate) at bind pH**

- **Elution yield (of captured):** **96–98%** baseline (do not assume 99% without data).
- **DF requirement:** **2 DV** default (1–3 DV) to clear polyP before ion-exchange polish; budget the DF time/losses now, not later. 

------

## E) Post-elution clarification (DSP02-E)

You must remove fines to spec before resin polish.

- **Default route:** **Depth filter train 10 µm → 1 µm**, flux cap **90–100 LMH**, terminal ΔP **~1.2 bar**.
- **Hold-up loss:** **~0.3–0.7 L per 10″** module; budget conservatively at **0.6 L/10″**.
- **Target chitosan:** **<10 ppm** (spec knob). 

(If you’ve got a disc-stack available for polish and flocs are robust, that’s fine too; still keep a small hold-up loss.) 

------

## F) Polymer recycle (DSP02-F)

- **Recycle fraction:** **0.6–0.8** (baseline **0.7**).
- **Activity retained per loop:** **0.85–0.95** (baseline **0.90**).
- **Bleed:** **5–10%** per loop to control contaminants/fines.
- Count acid/base re-protonation costs explicitly. 

------

## Conservative mass-balance (wire this into your unit)

Let:

- $Y_\text{cap}$ = coacervation capture (0.85–0.90 baseline)
- $Y_\text{wash}$ = $(1-\text{wash\_loss})^{n}$ (use 1 wash @ 1% loss → 0.99)
- $Y_\text{elu}$ = elution (pH-mode 0.95–0.98; polyP 0.96–0.98)
- $Y_\text{clar}$ = post-elution clar. recovery (1 − hold-up − adsorption), use **0.99** baseline

**Overall step recovery (conservative):**
$$
Y_{\text{DSP02}} \approx Y_\text{cap}\cdot Y_\text{wash}\cdot Y_\text{elu}\cdot Y_\text{clar}
$$

- **pH-mode default:** $0.90 \times 0.99 \times 0.97 \times 0.99 \approx \mathbf{0.85}$ (85%)
- **PolyP default:** $0.90 \times 0.99 \times 0.97 \times 0.99 \approx \mathbf{0.85}$ **minus DF loss** (see below)
  - Add DF loss for polyP: use **ND = 2**, $f=e^{-ND}$ for small species; protein loss budget **0.5–1.0%** across 2 DV → overall **~84–85%**. 

> Your prior doc’s “85–95% overall” band is retained—but we **set the baseline at 84–85%** so upside shows as you tune Rq, salt, and elution. 

------

## Defaults to drop straight into BioSTEAM (replace once lab fits land)

**Coacervation**

- `pH_bind = 4.2`, `I_bind_mM = 50`
- `Charge_Ratio_Rq = 1.8` (tunable)
- `Capture_Yield_pct_base = 90` with **Salt_Sensitivity_kI = −15% / +100 mM**, and mild Rq parabola penalty. 

**Separation**

- `Mode = DiscStack` (target turbidity <100 NTU; coacervate loss 1%). 

**Wash**

- `Washes = 1`, `Wash_Ratio_BV_per_wash = 0.5`, `Loss_pct_per_wash = 1.0`. 

**Elution**

- `Mode = pH`, `pH_elute = 7.5`, `I_elute_mM = 100`, `Elution_Yield_pct_base = 97`.
- PolyP option: `PolyP_mM_asP = 40`, `PolyP_DF_DV_required = 2`. 

**Post-elution clarification**

- `Mode = DepthFilter`, `Grades_um = [10,1]`, `Flux_LMH_cap = 100`, `HoldUp_L_per_10in = 0.6`, `Target_Chitosan_ppm = 10`. 

**Recycle**

- `Recycle_Fraction = 0.70`, `Bleed_Fraction = 0.05`, `Activity_Retained_per_Loop = 0.90`. 

**Economics (CDMO)**

- `Processing_Fee_USD_per_m3`, `Filter_Media_USD_per_m2`, `Acid/Base/PolyP costs`, `Labor`, `Waste` as in your pack; **equipment CAPEX flagged** (excluded). 

------

## Guardrails (make the unit refuse to over-promise)

- **If I_bind > threshold** → **derate $Y_\text{cap}$** and flag “pre-dilute or derate yield.” 
- **If elution = PolyP** → **force DF (≥1 DV, default 2 DV)** before any IEX polish selection. 
- **If post-DSP02 chitosan ppm > spec** → require **CEX-negative polish** in DSP04. 
- **If fines too high for chosen separator** → raise warning and switch to decanter/RVF or add filter-aid. 

------

## Why this is conservative (and where you’ll see upside)

- We lock **coacervation at 85–90%** rather than 90–95% until your DoE confirms the plateau at the *actual* ionic strength with your **Rq**. 
- We require **DF after polyP** and count its **yield/time cost** now; it’s cheaper than discovering AEX antagonism later. 
- We **budget hold-up/adsorption** explicitly in post-elution clarification; many spreadsheets forget that liter or two per 10″ module. 