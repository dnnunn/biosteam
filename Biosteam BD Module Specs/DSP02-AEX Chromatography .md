# DSP02 — AEX Chromatography (Bind-and-Elute)

## Purpose

Capture OPN from clarified, concentrated supernatant; remove small proteins and media components that don’t bind or elute differently; deliver a pool compatible with the next step (e.g., polish or formulation).

## Streams

- **In:** conditioned feed (conductivity at or below bind spec, pH at bind pH)
- **Out 1:** load-through (unbound)
- **Out 2:** wash (weakly bound impurities)
- **Out 3:** **elution pool** (product)
- **Out 4:** strip + CIP + sanitization effluents

------

## Core design inputs (make these named params)

**Resin & hardware**

- `Resin_type = "Q"` (strong AEX), `particle_diameter_um` (e.g., 45–90)
- `Resin_cost_per_L`, `Resin_life_cycles` (e.g., 100–200)
- `Bed_height_cm` (20–30 typical), `Column_ID_cm` (sized)
- `Compressor_factor` (bed compressibility, 0.7–0.9 packing factor)

**Hydraulic & cycle**

- `Lin_vel_cm_per_h` (a.k.a. superficial velocity; 200–600 typical)
- `RT_load_min` (residence time target during load if you prefer RT control)
- `DeltaP_max_bar` (e.g., 3 bar system limit)
- `Fouling_factor_dp` (pressure growth per cycle, e.g., 0.2%/cycle)

**Thermo/chemistry**

- `pH_bind`, `Cond_bind_mM_max` (≤ ~200 mM from your experimental map)
- `pH_elute`, `Elute_salt_mM` (step or gradient)
- `Temperature_C` (20–25 default)

**Binding capacity model**

- `DBC10_base_mg_per_mL` at reference pH/cond/RT (from your sheet)
- `DBC_cond_slope` (mg/mL per mM; negative)
- `DNA_competition_coeff` (mL/mg DNA or fractional capacity loss per mg/L DNA)
- `Mass_transfer_factor` (derating for shorter residence times)

**Feed & targets**

- `Batch_volume_m3_in`, `Protein_conc_gL_in`
- `DNA_mg_per_L_in` (post-benzonase), `Cond_in_mM`, `pH_in`
- `Target_recovery_pct`, `Target_pool_cond_mM` (often ≤ 500–800 mM)
- `UV_pooling_rule` (e.g., 10–90% peak, or conductivity window + UV)

**Utilities & turnaround**

- `CIP_NaOH_M`, `CIP_time_min`, `Sanitization_agent`, `San_time_min`
- `Equilibration_BV`, `Wash_BV`, `Elution_BV`, `Strip_BV`, `CIP_BV` (bed volumes)

------

## Effective capacity & load model

### 1) **Effective DBC** (mg/mL resin)

Start from your lab-measured reference (e.g., DBC at 10% breakthrough):
$$
\text{DBC}_{\text{eff}} \;=\;
\underbrace{\text{DBC}_{\text{base}}}_{\text{sheet value}}
\;\times\;
\underbrace{f_{\text{RT}}(\text{RT})}_{\text{mass transfer derate}}
\;\times\;
\underbrace{f_{\text{cond}}(C)}_{\text{ionic strength derate}}
\;\times\;
\underbrace{f_{\text{DNA}}(\text{DNA})}_{\text{competition derate}}
$$

- **Mass-transfer derate (residence time)**
   Simple form: $f_{\text{RT}} = \min\!\left(1,\; \dfrac{\text{RT}}{\text{RT}_{\text{ref}}}\right)^\beta$ with $\beta \approx 0.3{-}0.7$.
   Or use your breakthrough vs. RT curve.
- **Conductivity derate** (use your spreadsheet mapping):
   Linear first pass: $f_{\text{cond}} = 1 + k_C (C - C_{\text{ref}})$ (clip at $[0,1]$).
   If you have a table/fit, use it directly.
- **DNA competition**
   Two practical options; pick one you can parameterize:
  1. **Linear capacity theft**: $f_{\text{DNA}} = \max\!\left(0,\, 1 - k_{\text{DNA}}\cdot \text{DNA}_{\text{mg/L}}\right)$
  2. **Langmuir-like**: $f_{\text{DNA}} = \dfrac{1}{1 + K\cdot \text{DNA}}$

Benzonase reduces DNA and thus increases $f_{\text{DNA}}$. Your earlier step should write `DNA_out` into this unit.

### 2) **Resin volume & cycles**

- **Product mass to capture per batch**: $m_p = V_{\text{in}} \cdot C_p$
- **Load per cycle (mg)**:
   $m_{\text{cycle}} = \text{DBC}_{\text{eff}} \cdot V_{\text{resin}} \cdot \eta_{\text{util}}$
   where $\eta_{\text{util}}$ is how close you run to the breakthrough spec (e.g., 0.9 for 10% BT safety).

Choose either:

- **Size for 1 cycle**: $V_{\text{resin}} = \dfrac{m_p}{\text{DBC}_{\text{eff}}\cdot \eta_{\text{util}}}$
- **Fix resin & compute cycles**: $N_{\text{cycles}} = \left\lceil \dfrac{m_p}{m_{\text{cycle}}} \right\rceil$

### 3) **Hydraulics & time**

- **Column cross-section**: $A_c = \pi (ID/2)^2$
- **Bed volume**: $BV = V_{\text{resin}}/\text{packing\_factor}$
- **Superficial velocity**: $u = \dfrac{Q}{A_c}$
- **Residence time (load)**: $\text{RT} = \dfrac{BV}{Q}$
- **Step times** (each step’s **bed volumes** × $BV/Q$), plus buffer switches, hold/soak if used.

### 4) **Pressure drop check** (packed bed)

Use Ergun in liquid regime (convert to bed porosity $\varepsilon$, particle diameter $d_p$):
$$
\frac{\Delta P}{L} = \frac{150(1-\varepsilon)^2}{\varepsilon^3}\,\frac{\mu u}{d_p^2}
\;+\;
\frac{1.75(1-\varepsilon)}{\varepsilon^3}\,\frac{\rho u^2}{d_p}
$$
Ensure $\Delta P \le \Delta P_{\text{max}}$. If exceeded, lower $u$, increase ID, or shorten bed.

------

## Step recipe (bind-and-elute, step elution shown)

- **Equilibrate:** 3–5 BV at `pH_bind`, `Cond_bind` (your sheet values)
- **Load:** to target breakthrough or calculated mass limit
- **Wash 1:** 3–5 BV bind buffer (remove unbound)
- **Wash 2 (optional):** low salt ramp (e.g., +50–100 mM) to clear weak anions
- **Elute:** step to `Elute_salt_mM` (or gradient) at same pH; collect by UV/cond rules
- **Strip:** high salt (or pH change) 1–2 BV
- **CIP:** NaOH (0.1–0.5 M) 2–3 BV (time/soak as validated)
- **Re-equilibrate:** to bind buffer

**Pooling rule**: UV threshold + conductivity window (e.g., pool 10–90% of main peak while  **Cond ≤ target**). Record pool volume and concentration to compute step yield.

------

## Performance & yields

- **Load loss** (breakthrough): set by your BT spec (e.g., 10% at end of load → ~2–5% mass lost depending on curve; calibrate to your BT curve).
- **Wash loss:** 0.5–2% (tunable)
- **Elution recovery:** 96–99% from bound mass (UV/cond pooling choice)
- **Strip loss:** residual irreversible binding (0.5–2%)
- **System hold-up:** 0.5–2% of peak mass (depends on skid lines/valves)

**Overall step recovery target:** 93–98% (set a baseline; tune with your data).

**Impurity clearance:** carry over DNA, small proteins, and media components via your experimental maps; couple to:

- load-through fraction (for non-binding),
- wash factor,
- co-elution factor (conductivity and gradient steepness dependent).

------

## Utilities, buffers, and chemicals (per cycle)

Track as functions of **bed volumes** and **flow**:

- **Buffers:** volumes and compositions for Equil, Wash, Elute, Strip, CIP, Re-equil (m³)
- **NaOH / acid mass** for CIP/sanitization
- **Water for prep/rinse**
- **Power:** pumps ∝ $Q \cdot \Delta P / \eta$

------

## Costs

**CAPEX**

- Column + skid (pumps/valves/UV/cond): $C_{\text{skid}} = a\cdot BV^{\,b}$ (b≈0.6–0.8)
- Ancillaries (tanks, inlines, sensors): factor or itemized
- Installation factor: 1.5–2.5×

**OPEX**

- Resin amortization per cycle: $\dfrac{V_{\text{resin}}\cdot \text{Resin\_cost}}{\text{Resin\_life\_cycles}}$
- Buffers & chemicals (from step BV × concentrations × unit prices)
- Utilities (electricity), labor time per cycle, QC (optional)

------

## Constraints & warnings

- **Conductivity in > bind threshold** → trigger **pre-DF top-off** (0.5–1.0 DV) or reduce load velocity / increase residence time if your data say capacity tolerates it.
- **DNA high** → warn that effective DBC is reduced; suggest raising benzonase dose/time.
- **Pressure > limit** → widen column (bigger ID), shorten bed, or reduce linear velocity.
- **Resin life exhausted** → replace resin; recalc amortization.
- **Cycles per batch too high** (e.g., >10–12) → consider larger column or modestly higher CF upstream (within conductivity limits) to cut load time.

------

## Defaults/placeholders (replace with your sheet values)

- `DBC10_base_mg_per_mL = 60` (illustrative; use your actual for OPN at ref conditions)
- `DBC_cond_slope = -0.08 mg/mL per mM` (placeholder—fit to your data)
- `DNA_competition_coeff = 1e-4 L/mg` (placeholder—fit)
- `Bed_height_cm = 25`, `Lin_vel_cm_per_h = 300`, `DeltaP_max_bar = 3`
- Step volumes: `Equil_BV=3`, `Wash1_BV=3`, `Wash2_BV=2`, `Elute_BV=3`, `Strip_BV=2`, `CIP_BV=3`, `ReEquil_BV=3`
- Pooling: UV 10–90% with **Cond ≤ 800 mM** cap (example)

These let you simulate immediately while you plug in your real DBC-vs-conductivity and DNA effects from the spreadsheet.

------

## Coupling back to DSP01 (what matters)

- **CF → load time**: You already compute CF from AEX load window. Use that to minimize cycles or column size without inflating viscosity/∆P.
- **Conductivity hand-off**: If `Cond_out_DSP01 > Cond_bind_max`, automatically request a **short DF** (0.5–1 DV).
- **DNA reduction**: Write `DNA_out` from benzonase into the **DBC_eff** calculation here; you’ll see resin volume or cycle count drop—monetize that win.

------

## BioSTEAM unit API (suggested fields)

**Inputs**
 `feed.F_vol, feed.C_prot, feed.DNA, feed.pH, feed.cond, feed.visc, temp`
 `resin: type, cost/L, life_cycles, dp_um, packing_factor`
 `column: bed_height_cm, dp_max_bar, ID (optional)`
 `cycle: lin_vel, RT_load (optional), step_BV dict, pooling_rule`
 `capacity_model: DBC_base, RT_ref, beta, cond_map (or slope), DNA_coeff`
 `chem_costs: NaOH, buffers, water, power_price`

**Design algorithm**

- Compute `DBC_eff`
- Size `V_resin` or `N_cycles`
- Size column ID to meet ΔP and velocity
- Compute step times, buffers, CIP
- Output `design_results` (V_resin, ID, cycles, step times/volumes)

**Performance**

- Recoveries by segment (load, wash, pool, strip, hold-up)
- Pool volume, concentration, conductivity, pH
- Impurity carryover/removal (DNA, small proteins) per your maps

**Costs**

- CAPEX (skid+column), resin amortization, buffers/chemicals, utilities, labor per batch

**Warnings**

- Conductivity too high; ΔP too high; cycles excessive; resin life depleted

------

## Where this leaves us

You can now run **what-ifs** that directly connect:

- benzonase dose → DNA_out → $f_{\text{DNA}}$ → `DBC_eff` → resin volume / cycles → AEX cost & time
- CF from DSP01 → load time / cycle count
- small DF top-off only when needed by the **conductivity guardrail**

# AEX in a CDMO scenario (CAPEX flagged, excluded from rollups)

Add two global switches:

- `Ownership_Mode ∈ {CDMO, InHouse}`
- `Include_CAPEX ∈ {False, True}` (auto-set `False` when `Ownership_Mode=CDMO`)

## Cost hooks to use (CDMO mode)

Use these instead of capital depreciation:

- **Resin lease / usage fee:** `Resin_Fee_per_L_per_cycle`
   (CDMOs often charge per-L per cycle, inclusive of expected lifetime and risk.)
- **Column rental:** `Column_Rental_per_day` (or per campaign)
- **Setup/teardown:** `Column_Setup_Fee_per_campaign`
- **Buffer make fees:** per-m³: `Equil_Fee_per_m3`, `Wash_Fee_per_m3`, `Elute_Fee_per_m3`, `Strip_Fee_per_m3`, `CIP_Fee_per_m3`, `ReEquil_Fee_per_m3`
- **Labor:** `Ops_Labor_h_per_cycle * Blended_Rate_per_h`
- **Disposables:** prefilters, housings gaskets: `Disposables_per_cycle`
- **Utilities passthrough:** keep power/water/NaOH costs if CDMO itemizes; else roll into flat **Overhead per cycle**.

### CDMO AEX cost per cycle (rollup)

$$
\text{Cost}_{\text{cycle}} =
(\text{Resin\_Fee} \cdot V_{\text{resin}}) +
\text{Column\_Rental\_per\_day}\cdot t_{\text{cycle,days}} +
\sum_s (\text{Fee}_s \cdot V_{s,\text{m}^3}) +
\text{Labor} + \text{Disposables} + \text{Overhead}
$$

Multiply by `N_cycles` per batch. Report CAPEX fields but **exclude** from totals when `Include_CAPEX=False`.

Keep all **performance/throughput** calcs unchanged (DBC, ∆P, cycles, pooling). The economics layer simply swaps depreciation for fee structures.

# Data fields to “flag for later” (show but don’t sum in CDMO mode)

- `Skid_CAPEX`, `Column_CAPEX`, `Installation_Factor`, `Total_CAPEX_AEX`
- `Resin_CAPEX_on_Purchase` (if in-house)
   In your outputs, label them clearly: “(flagged: excluded in CDMO totals)”.

# Routing map (naming alignment)

- **USP01–USP03 (Upstream)** → cell separation → clarification
- **DSP01** (Concentration/Buffer-Exchange: UF/DF/SPTFF/cTFF) → **DSP02A = AEX**
- **USP03: Chitosan Coacervate** (alternative capture) → **bypasses DSP02**
  - Handoff from **USP03** goes directly to its own polish/conditioning chain.

So in your scenario toggles:

- `Capture_Route ∈ {DSP02A_AEX, USP03_Chitosan}`
- If `Capture_Route=USP03_Chitosan`, **skip DSP02** entirely and consume the **USP03** pool as the input to the next step.

# Minimal additions to AEX unit I/O for CDMO mode

**Inputs (new economic fields):**

- `Ownership_Mode`, `Include_CAPEX`
- `Resin_Fee_per_L_per_cycle`
- `Column_Rental_per_day`, `Column_Setup_Fee_per_campaign`
- `*_Fee_per_m3` for each buffer step
- `Ops_Labor_h_per_cycle`, `Blended_Rate_per_h`
- `Disposables_per_cycle`, `Overhead_per_cycle`

**Outputs (economics):**

- `AEX_Cycle_Time_h`, `AEX_Cycles_per_Batch`
- `AEX_Buffer_Volumes_m3_by_step`
- `AEX_CDMO_Cost_per_Cycle`, `AEX_CDMO_Cost_per_Batch`
- `AEX_CAPEX_Flagged` (aggregate, reported but excluded)
- `Notes`: which items were excluded due to CDMO mode

Everything else (DBC_eff, pressure checks, recoveries) stays as specced.

# Handoff contracts (so branches plug in cleanly)

Define lightweight “contracts” the next unit expects.

**DSP02A (AEX) → Next step contract**

- `Pool_Volume_m3`
- `OPN_Conc_gL`
- `Conductivity_mM`
- `pH`
- `DNA_mgL` (post-AEX; for tracing)
- `Step_Recovery_pct`