# DSP02A — AEX Chromatography (conservative defaults)

## What we’ll assume by default (yeast supernatant, secreted protein)

**Binding window:** pH at your lab optimum; ionic strength kept **≤ 200 mM** at load (if higher, do a **short DF 0.5–1.0 DV** upstream rather than trying to “force bind” with velocity/RT tricks). This follows your own guardrail design. 

**Resin behavior:** Treat catalog DBC as “lab best case.” Apply three derates automatically: residence-time, conductivity, DNA. Keep the **utilization** to ~90% of the chosen BT spec (safety margin). 

------

## Conservative performance (set these baselines)

- **Overall step recovery (bind-elute):** **93–96%** baseline, range **92–98%** depending on pooling/strip/hold-up.
   Rationale: load loss at BT, 0.5–2% in washes, 96–99% elution of bound, 0.5–2% irreversibles, 0.5–2% hold-up — aligns with your segment model. 
- **Load loss at end-of-load:** target **10% BT** → plan **2–5%** mass lost overall from the loading curve; do not assume sub-2% until curve is measured. 
- **Elution recovery (of bound):** **96–98%** baseline (leave 99% as upside with tighter pooling). 
- **Wash loss:** **1–2%** (use 2% until you have data). 
- **Irreversible/strip loss:** **1–2%** (use 1.5%). 
- **System hold-up:** **1–2%** of peak mass (use 1.5% until your skid is measured). 
- **DNA removal:** keep your spreadsheet maps; absent data, assume **~1–2 log** for bind-elute operated in a standard recipe and **≤1.5 log** for FT polish. 

------

## Capacity & hydraulics (defaults that won’t blow up at scale)

- **DBC_base_mg/mL (10% BT)**: start with your lab DBC; use **60 mg/mL** only as a placeholder label, not a promise. Apply:
  $$
  \textbf{DBC}_{\text{eff}}=\text{DBC}_{\text{base}}\cdot f_{\text{RT}}\cdot f_{\text{cond}}\cdot f_{\text{DNA}}
  $$
  with:

  - $f_{\text{RT}}=(\text{RT}/\text{RT}_{\text{ref}})^{0.5}$ (clip ≤1)
  - $f_{\text{cond}}=\max(0,\,1+k_C(C-C_{\text{ref}}))$, start with **−0.08%/mM** as a placeholder slope
  - $f_{\text{DNA}}=\max(0,\,1-k_{\text{DNA}}\cdot \text{DNA}_{\text{mg/L}})$ (placeholder slope ~1e-4 L/mg) 

- **Linear velocity (load):** **250–350 cm/h**, baseline **300 cm/h**; increase only if Ergun ΔP shows margin. **ΔP_max = 2–3 bar**, keep **2 bar** as a soft cap. 

- **Bed height:** **20–25 cm**; taller beds punish ΔP and mass transfer without proportional ROI. 

- **Packing/porosity:** keep your **packing_factor ~0.75–0.9** and run Ergun check; if ΔP warns, widen ID before you shorten bed (keeps step BVs intact). 

- **Cycles per batch:** if **>10–12**, either enlarge column or raise upstream CF (but only within the 200 mM bind guardrail). 

------

## Step recipe (guarded BVs & pooling)

- **Equil** 3 BV, **Wash1** 3 BV, **Wash2** 0–2 BV (default **0**)
- **Elute** 3 BV (step), **Strip** 2 BV, **CIP** 3 BV, **Re-equil** 3 BV. Don’t shrink these on paper unless plant data support it. 
- **Pooling rule:** UV **10–90%** with a **conductivity cap**; if peak tail exceeds cond target, trim pool even if it costs a point of recovery. This is how you avoid invisible “salt-drag” problems into DSP04. 

------

## Buffer, utilities, and time (plan for the dull reality)

- **Bed-volume accounting** from your spec; compute step times as BV × (BV_bed / flow). Keep **flow from velocity×area**; don’t back-solve velocity to meet a time window if it violates ΔP. 
- **Buffers per cycle:** Equil + Wash + Elute + Strip + CIP + Re-equil. Add **switch/soak overhead** explicitly; typical CDMOs charge for it. 

------

## CDMO economics (client-borne vs flagged CAPEX)

- **Always include**: resin usage fee (or amortization), **buffer make fees per m³**, **labor hours/cycle**, **disposables/cycle**, **utilities/overhead** if itemized.
- **Flag (exclude in CDMO)**: column/skid CAPEX & install; keep it visible but **out of totals** unless `Ownership_Mode=InHouse`. 

Formula you’re already using is fine; just feed it the conservative volumes/times above. 

------

## Defaults to drop straight into your unit (replace with your lab fits)

- `Bed_height_cm = 25`
- `Lin_vel_cm_per_h = 300`
- `DeltaP_max_bar = 2`
- `DBC10_base_mg_per_mL` = **your lab value** (placeholder **60**)
- `f_RT beta = 0.5` ; `DBC_cond_slope = −0.0008 per mM` ; `DNA_competition_coeff = 1e−4 L/mg`
- `Equil_BV=3, Wash1_BV=3, Wash2_BV=0, Elute_BV=3, Strip_BV=2, CIP_BV=3, ReEquil_BV=3`
- `Utilization (η)` = **0.9** at 10% BT
- **Recoveries (bind-elute):** load loss **3%**, wash loss **2%**, elute **97%**, strip/irreversibles **1.5%**, hold-up **1.5%** → **overall ≈ 94–95%** (report 93–96%). 

------

## Conservative control logic (so the model won’t over-promise)

1. **If Cond_in > Cond_bind_max** → perform **DF 0.5–1.0 DV** upstream; do **not** rely on slower loading to “save” capacity. 
2. **If cycles > 12** → recommend **larger ID** or **modest CF increase** (stay within the 200 mM guardrail). 
3. **If ΔP exceeds cap at planned velocity** → increase ID (not shorten bed first). 
4. **If DNA high** → increase benzonase dose/time **before** AEX (capacity gain beats fighting co-binding). 

------

## Why we’re this conservative (and where the upside will show)

- Yeast supernatants at scale rarely let you run “brochure DBC” at “brochure velocities” with pretty ΔP; the derates (RT/cond/DNA) are the reality checks. 
- Your own segment yield structure (load, washes, elute, strip, hold-up) already implies **mid-90s** overall unless pooling is heroic — we’re just **setting the baseline there** and letting your data lift it. 
- The CDMO cost split remains intact: **client-borne consumables & buffers** always count; **CAPEX flagged** stays out of COGS unless you flip to in-house. 