# DSP04 — Purpose & Scope

- Remove residual process contaminants (DNA, HCPs, chitosan traces, polyP remnants, aggregates).
- Tighten conductivity/pH into the formulation window.
- Deliver a **0.2 µm sterile-filtered** pool to spray dryer.
- Operate in CDMO mode with **client-borne consumables** (resins/membranes/buffers/labor/waste) and **CAPEX flagged** for in-house.

------

# DSP04 variants (toggle)

Expose a selector: `DSP04_Method ∈ {None, AEX_Repeat, CEX_Negative, HIC_FlowThrough, MixedBed_IEX, Enzymatic_TidyUp}` plus a **mandatory terminal step** `SterileFilter_0p2um`.

**When they shine**

- **AEX_Repeat (bind-elute or flow-through):** best all-around polish; orthogonal to chitosan (esp. after pH-mode elution) and good DNA mop-up; can also polish after AEX capture if first step was “loose.”
- **CEX_Negative (flow-through):** cost-effective after **Chitosan pH-elution** (OPN net negative) to trap cationics—including chitosan residues—while OPN flows through.
- **HIC_FlowThrough:** targets hydrophobes/aggregates with minimal salt if you tune gently; optional if analytics complain about aggregate tails.
- **MixedBed_IEX:** small stacked guard (CEX-FT then AEX-FT) for hard specs without full bind-elute cycles.
- **Enzymatic_TidyUp (optional):** e.g., residual nuclease quench/hold or protease cleanup if you validate it; typically not needed if benzonase upstream was good.

You can chain: e.g., `CEX_Negative → AEX_FT → SterileFilter` or just one polish then sterile.

------

# Common inputs (from DSP03 handoff)

- `DSP03_Pool_Volume_m3`, `DSP03_OPN_Conc_gL`, `DSP03_pH`, `DSP03_Conductivity_mM`
- `DSP03_DNA_mgL`, `DSP03_Chitosan_ppm`
- Route flags you may carry: `polyP_present` (true if chitosan-polyP path)
- Ownership & cost model: `ownership_mode`, `include_capex`

# Different inputs (from DSP02)



In the case of certain DSP04 operations such as HIC, there will not be a need to use DSPO3 to remove salt or reduce volume. In that case we have a potentially different input.



[link] (#Allow_two_upstream_entry_points). Please see the bottom of this document for how to address this before proceeding.



# Common outputs (handoff to spray drying)

- `DSP04_Pool_Volume_m3`
- `DSP04_OPN_Conc_gL`
- `DSP04_pH`, `DSP04_Conductivity_mM`
- `DSP04_DNA_mgL` (post-polish), `DSP04_Chitosan_ppm` (post-polish)
- `DSP04_Step_Recovery_pct`
- `DSP04_Time_h`
- `DSP04_ClientCost_usd`
- `DSP04_CAPEX_Flagged_usd` (reported, excluded in CDMO)
- `DSP04_Sterile_Filter_Area_m2`, `Sterility_Assurance_Flag` (pass/fail)

------

# Variant specs (BioSTEAM-ready)

## 1) AEX_Repeat

**Mode:** choose **flow-through (FT)** if OPN binding window is tight or conductivity is near the upper limit; else **bind-elute** if you need maximum impurity removal.

**Key knobs**

- `Resin_type="Q"`, `DBC_base_mg_per_mL`, `f_cond(C)`, `f_pH(pH)`
- FT capacity (impurity binding) vs load velocity
- Step BV: Equil/Wash/Elute (if bind-elute), CIP
- `Lin_vel_cm_per_h` or `RT_min`, `ΔP_max_bar`

**Performance**

- DNA removal high (0.5–2.0 log FT; 1–3 log bind-elute)
- Chitosan residues: generally **do not bind** at neutral/high pH—use CEX-FT instead if chitosan ppm is the driver
- Recovery: FT ~99%+, bind-elute 95–98%

**Economics**

- Client-borne: resin fee/usage (per L per cycle if CDMO bills that), buffers, labor, disposables
- CAPEX flagged (column/skid) if InHouse

**Use when**

- After **Chitosan-polyP + DF**, to catch DNA/leftovers
- After **AEX capture** if analytics show remaining HCP/DNA tails

------

## 2) CEX_Negative (flow-through)

**Idea:** OPN (anionic near neutral) **flows through**; cationic impurities (incl. residual **chitosan**) bind.

**Key knobs**

- `Resin_type="SP" or "CM"`, `pH=6.5–7.5`, `Cond=50–150 mM`
- `Load_LinearVelocity` or `RT_min` for FT mode
- Guard 0.2 µm before bed if fines risk flagged

**Performance**

- Chitosan removal: strong (often >90%); DNA moderate (pairs nicely with AEX FT if needed)
- Recovery: 98–99.5% (FT)
- Conductivity/pH drifts minimal

**Economics**

- Resin usage (FT), small buffer volumes, low time per cycle

**Use when**

- **Default polish after Chitosan pH-mode** (cheap & effective)
- Also helpful post-AEX if cationic HCPs linger

------

## 3) HIC_FlowThrough (optional)

**Idea:** Orthogonal hydrophobic cleanup, catch aggregates.

**Key knobs**

- `Resin_type` (Butyl/Phenyl), `Salt_mM` (ammonium sulfate or NaCl), FT load
- Keep salt low (e.g., 0.5–0.8 M NaCl) if OPN tolerates; avoid big desalting later

**Performance**

- Removes hydrophobes, some aggregates; DNA not the target
- Recovery: 97–99% if tuned mild

**Use when**

- Analytics show hydrophobe/aggregate signal; otherwise skip

------

## 4) MixedBed_IEX (stacked mini-guards)

**Idea:** Short **CEX-FT cartridge → AEX-FT cartridge** in series; tiny bed volumes, fast.

**Performance**

- Broad impurity net, minimal volume/time
- Recovery: 98–99.5%
- Great “insurance” polish without full columns

**Use when**

- Spec is tight but you want to avoid a full bind-elute

------

## 5) Enzymatic_TidyUp (optional micro-unit)

**Idea:** Quick enzymatic polish (e.g., DNase quench/hold) if DNA remains stubborn; usually avoid at this stage unless analytics demand it.

------

## Terminal: **SterileFilter_0p2um** (mandatory)

**Membrane:** 0.2 µm PES; add 0.45 µm **prefilter** if bioburden/particulates.

**Key knobs**

- `Sterile_Flux_LMH` (200–600 on clean protein), `Max_DP_bar` (≤1.5)
- `Specific_Capacity_L_per_m2` (from skid VLRs), integrity test pass
- 2× redundant filters if required by QA (N+1 sizing)

**Performance**

- Protein recovery: ≥99.5% (set adsorption loss per m²)
- Bioburden reduction: meets sterility assurance (integrity test gates handoff)

**Economics**

- Client-borne: filter capsule/module $/m², integrity test time, disposables
- CAPEX negligible (skid exists in CDMOs; flag if modeling in-house)

------

# Route-aware playbook (selection rules)

**If `Capture_Route=DSP02_CHITOSAN`**

- **Elution = pH-mode** (no polyP):
   Default: **CEX_Negative (FT)** → **SterileFilter**
   If DNA still high: add **AEX_FT** after CEX.
- **Elution = polyP** (after DF):
   If polyP residual ≤ spec: **CEX_Negative (FT)** → **SterileFilter**
   If still high DNA/small anions: **AEX_Repeat (FT or bind-elute)** → **SterileFilter**

**If `Capture_Route=DSP02_AEX`**

- If purity OK: **SterileFilter** only
- If extra cleanup needed (DNA/HCP tails): **AEX_FT** *or* **CEX_Negative** depending on impurity profile → **SterileFilter**
- If aggregates flagged: add **HIC_FT** before sterile

**Never ship to spray dryer without `SterileFilter_0p2um` passing integrity.**

------

# BioSTEAM class architecture (no code, just interfaces)

```
DSP04BasePolish (abstract)
├─ DSP04_AEX_Repeat
├─ DSP04_CEX_Negative
├─ DSP04_HIC_FT
├─ DSP04_MixedBed_IEX
└─ DSP04_SterileFilter_0p2  (always run last; simple unit)
```

**Common inputs (client costs always included)**

- Resin fee or cost per L per cycle (if CDMO charges per-use)
- Buffer fees per m³; step BV definitions
- Disposables per batch (pre-filters, cartridges)
- Labor, waste disposal
- CAPEX fields flagged (column/skid), only counted if `ownership_mode="InHouse"`

**Each chromatography subclass exposes**

- `capacity_model` (DBC or FT capacity vs pH/cond/RT)
- `hydraulics` (lin. vel., RT, ΔP cap)
- `step_BV` dict (Equil, Wash, Elute/FT volume, Strip, CIP, Re-equil)
- `pooling_rule` (UV/cond)
- Outputs: `recovery_pct`, `DNA/HCP reduction`, `pool volume/cond/pH`

**Sterile filter subclass**

- Inputs: `flux_LMH`, `capacity_L_m2`, `adsorption_loss_per_m2`, `max_DP_bar`, `prefilter_bool`
- Outputs: `area_m2`, `integrity_pass`, `recovery_pct`

------

# Compact equations you’ll actually wire

**IEX FT capacity** (impurity load, not product):

- `Load_mg = C_impurity_in * V_feed`
- `Cap_FT_mg = q_cap_mg_per_mL * Resin_L * Utilization`
- `Resin_L = ceil(Load_mg / Cap_FT_mg_per_L)`

**Bind-elute DBC_eff**
 `DBC_eff = DBC_base * f_cond(C) * f_pH(pH) * f_RT(RT)`

**Step times**
 `t_step = (BV_step * BedVolume) / Q`

**Sterile filter area**
 `A ≥ max( V / Capacity_L_m2 , Q / Flux_LMH )`
 `Recovery ≈ 1 – Adsorption_per_m2 * A`

------

# Defaults (swap with your data later)

**AEX_Repeat (FT)**

- `q_cap_impurity_mg_per_mL=10` (FT impurity capacity placeholder)
- `Lin_vel=300 cm/h`, `ΔP_max=2 bar`
- DNA removal 1.5 log (placeholder), recovery 99.2%

**CEX_Negative (FT)**

- `pH=7.0`, `Cond=100 mM`
- Recovery 99.0–99.5%; chitosan removal >90% (set spec-based)

**HIC_FT**

- `Salt=0.5 M NaCl`, recovery 98–99%

**Sterile 0.2 µm**

- `Flux=300 LMH`, `Capacity=2000 L/m²` on clean pool
- Adsorption 0.05% per m²

**Costs (client-borne placeholders)**

- IEX resin fee: `$50–150 per L per cycle` (CDMO usage fee) or resin amortization if in-house
- Buffers: `$50/m³` (equil/wash), `$70/m³` (elute), `$60/m³` (CIP)
- Sterile filter: `$350/m²`, prefilter `$200/m²`
- Labor: `6 h/batch @ $80/h`
- Waste: `$220/t`

------

# Adapter & handoff

Implement a **DSP04Selector** that:

1. Reads `DSP03Handoff`
2. Runs the chosen polish chain (0, 1, or 2 polish units)
3. Always runs `SterileFilter_0p2um`
4. Returns `DSP04Handoff` with volume/conc/pH/cond and cost/time

Downstream spray drying takes only `DSP04Handoff`.

------

# Validators (catch the gremlins)

- **PolyP present but AEX_FT skipped** and spec demands low anions → warn/insert DF upstream in DSP03 (you already have that).
- **Chitosan_ppm > spec** after chosen polish → force **CEX_Negative** or add a tiny **CEX guard**.
- **Sterile filter DP>cap** at required Q → increase area or add prefilter.
- **Total recovery DSP02×DSP03×DSP04 < threshold** → red-flag economics.

------

# Bottom line

- **Chitosan pH-mode path:** **CEX-Negative FT → Sterile 0.2 µm** is your fast, cheap default.
- **Chitosan polyP path:** **DF in DSP03**, then either **AEX-FT or CEX-FT** → **Sterile**.
- **AEX capture path:** usually **Sterile only**; add **AEX-FT** or **CEX-FT** if analytics demand it.
- Everything ends in a predictable, parameterized **sterile filtration** step so spray-drying sees a clean, consistent feed.



# Class attribute lists (DSP04)

## Base: `DSP04BasePolish`

**Purpose:** shared I/O, cost split, validators.

**Inputs (read-only feed from DSP03Handoff)**

- `feed_volume_m3: float`
- `feed_opn_conc_gL: float`
- `feed_pH: float`
- `feed_conductivity_mM: float`
- `feed_DNA_mgL: float`
- `feed_chitosan_ppm: float`
- `ownership_mode: Literal["CDMO","InHouse"] = "CDMO"`
- `include_capex: bool = False`  *(ignored if CDMO)*

**Client-borne cost params (always counted)**

- `buffer_fee_usd_per_m3: float = 60.0`
- `labor_h_per_batch: float = 6.0`
- `labor_rate_usd_per_h: float = 80.0`
- `disposables_usd_per_batch: float = 300.0`
- `waste_fee_usd_per_tonne: float = 220.0`

**CAPEX (flagged; counted only if InHouse)**

- `skid_capex_usd: float = 0.0`
- `install_factor: float = 1.8`
- `depr_years: int = 7`
- `annual_maint_frac: float = 0.03`

**Outputs (handoff to spray or next subunit)**

- `out_volume_m3: float`
- `out_opn_conc_gL: float`
- `out_pH: float`
- `out_conductivity_mM: float`
- `out_DNA_mgL: float`
- `out_chitosan_ppm: float`
- `step_recovery_frac: float`
- `cycle_time_h: float`
- `client_cost_usd: float`
- `capex_flagged_usd: float`
- `warnings: list[str]`

------

## `DSP04_AEX_Repeat`  *(FT or bind–elute)*

**Core**

- `mode: Literal["FT","BindElute"] = "FT"`
- `resin_type: Literal["Q","DEAE","Custom"] = "Q"`
- `bed_height_cm: float = 20.0`
- `lin_vel_cm_per_h: float = 300.0`
- `dp_max_bar: float = 2.0`
- `packing_factor: float = 0.75`
- `pooling_rule: str = "UV_10_90 & cond<=target"`

**Capacity/derates**

- `dbc_base_mg_per_mL: float = 60.0`          *(BindElute)*
- `ft_cap_mg_imp_per_mL: float = 10.0`        *(FT impurity capacity)*
- `rt_ref_min: float = 4.0`
- `beta_mass_transfer: float = 0.5`
- `cond_map: str|None = None`                 *(use your table/fit in code)*

**Step BV (BindElute)**

- `bv_equil=3.0; bv_wash1=3.0; bv_wash2=0.0; bv_elute=3.0; bv_strip=2.0; bv_cip=3.0; bv_reequil=3.0`

**Economics (client)**

- `resin_fee_usd_per_L_per_cycle: float = 90.0`  *(if CDMO charges per use; else amortize)*

**Typical outcomes (placeholders)**

- `dna_log_reduction: float = 1.5` (FT), `1.8` (BindElute)
- `base_recovery_frac: float = 0.992` (FT), `0.97` (BindElute)

------

## `DSP04_CEX_Negative`  *(flow-through)*

- `resin_type: Literal["SP","CM","Custom"] = "SP"`
- `pH: float = 7.0`
- `conductivity_mM: float = 100.0`
- `lin_vel_cm_per_h: float = 300.0`
- `dp_max_bar: float = 2.0`
- `ft_cap_mg_imp_per_mL: float = 8.0`
- `bv_equil=3.0; bv_wash=3.0; bv_flush=1.0; bv_cip=3.0; bv_reequil=3.0`
- `resin_fee_usd_per_L_per_cycle: float = 70.0`
- `chitosan_binding_eff_frac: float = 0.9`   *(fraction of residual chitosan captured)*
- `dna_log_reduction: float = 0.8`
- `base_recovery_frac: float = 0.995`

------

## `DSP04_HIC_FT`  *(optional orthogonal FT)*

- `resin_type: Literal["Butyl","Phenyl","Custom"] = "Butyl"`
- `salt_type: Literal["NaCl","(NH4)2SO4"] = "NaCl"`
- `salt_molarity_M: float = 0.5`
- `lin_vel_cm_per_h: float = 250.0`
- `dp_max_bar: float = 1.5`
- `ft_cap_mg_imp_per_mL: float = 6.0`
- `bv_equil=3.0; bv_wash=3.0; bv_flush=1.0; bv_cip=3.0; bv_reequil=3.0`
- `resin_fee_usd_per_L_per_cycle: float = 80.0`
- `aggregate_reduction_frac: float = 0.5`  *(50% removal placeholder)*
- `base_recovery_frac: float = 0.985`

------

## `DSP04_MixedBed_IEX`  *(stacked guards: CEX-FT → AEX-FT)*

- `cex_first: bool = True`
- `cex_ft_cap_mg_imp_per_mL: float = 6.0`
- `aex_ft_cap_mg_imp_per_mL: float = 6.0`
- `bv_each=2.0`
- `combined_recovery_frac: float = 0.99`
- `combo_resin_fee_usd_per_L_per_cycle: float = 120.0`  *(both cartridges)*

------

## Terminal: `DSP04_SterileFilter_0p2`

- `prefilter_enable: bool = False`
- `flux_LMH: float = 300.0`
- `capacity_L_per_m2: float = 2000.0`
- `max_dp_bar: float = 1.5`
- `adsorption_loss_frac_per_m2: float = 0.0005`  *(0.05%/m²)*
- `prefilter_adsorption_frac_per_m2: float = 0.0005`
- `module_cost_usd_per_m2: float = 350.0`
- `prefilter_cost_usd_per_m2: float = 200.0`
- **Outputs:** `area_m2`, `prefilter_area_m2`, `integrity_pass: bool`, `filter_cost_usd`, `recovery_frac`

------

# Sample YAML config (toggle-ready)

```
ownership_mode: CDMO              # CDMO | InHouse
include_capex: false

dsp04:
  method_chain:
    # Choose any 0–2 polish units (executed in order), then sterile filter runs automatically.
    # Examples:
    # - ["CEX_Negative"]
    # - ["AEX_Repeat:FT"]
    # - ["CEX_Negative", "AEX_Repeat:FT"]
    # - []
    - "CEX_Negative"

  targets:
    chitosan_ppm_max: 10
    dna_mgL_max: 0.1
    cond_mM_max_for_spray: 200
    pH_range_for_spray: [6.5, 7.5]

  AEX_Repeat:
    mode: FT                # FT | BindElute
    resin_type: Q
    bed_height_cm: 20
    lin_vel_cm_per_h: 300
    dp_max_bar: 2.0
    dbc_base_mg_per_mL: 60
    ft_cap_mg_imp_per_mL: 10
    resin_fee_usd_per_L_per_cycle: 90
    step_BV:
      equil: 3
      wash1: 3
      wash2: 0
      elute: 3
      strip: 2
      cip: 3
      reequil: 3

  CEX_Negative:
    resin_type: SP
    pH: 7.0
    conductivity_mM: 100
    lin_vel_cm_per_h: 300
    dp_max_bar: 2.0
    ft_cap_mg_imp_per_mL: 8
    chitosan_binding_eff_frac: 0.9
    resin_fee_usd_per_L_per_cycle: 70
    step_BV:
      equil: 3
      wash: 3
      flush: 1
      cip: 3
      reequil: 3

  HIC_FT:
    resin_type: Butyl
    salt_type: NaCl
    salt_molarity_M: 0.5
    lin_vel_cm_per_h: 250
    dp_max_bar: 1.5
    ft_cap_mg_imp_per_mL: 6
    resin_fee_usd_per_L_per_cycle: 80
    step_BV:
      equil: 3
      wash: 3
      flush: 1
      cip: 3
      reequil: 3

  MixedBed_IEX:
    cex_first: true
    cex_ft_cap_mg_imp_per_mL: 6
    aex_ft_cap_mg_imp_per_mL: 6
    bv_each: 2
    combo_resin_fee_usd_per_L_per_cycle: 120

  SterileFilter_0p2:
    prefilter_enable: false
    flux_LMH: 300
    capacity_L_per_m2: 2000
    max_dp_bar: 1.5
    adsorption_loss_frac_per_m2: 0.0005
    prefilter_adsorption_frac_per_m2: 0.0005
    module_cost_usd_per_m2: 350
    prefilter_cost_usd_per_m2: 200
```

------

# Selector logic (tiny, robust)

- If `feed_chitosan_ppm > chitosan_ppm_max` → **force** `CEX_Negative` first.
- If `polyP_present == True` (should be handled in DSP03 via DF) and DNA still high → add `AEX_Repeat:FT`.
- If aggregates flagged → add `HIC_FT` before sterile.
- Always run `DSP04_SterileFilter_0p2`; increase `prefilter_enable` if DP exceeds cap or NTU > threshold.

------

# What to wire next

- Add a microscopic “controller” that builds `method_chain` based on analytics flags and target specs, then executes units in order and composes a single `DSP04Handoff`.
- Drop in your lab-fit maps (DBC vs conductivity/pH, FT impurity capacities) to replace placeholders so resin/DF sizing becomes predictive.

From here, you can run full-route scenarios (AEX vs Chitosan) with DSP03/DSP04 toggles and see TEA impacts in minutes instead of weeks.



## # Allow two upstream entry points

Give DSP04 a small adapter that can ingest either handoff:

- **Normal path:** `DSP03Handoff → DSP04`
- **Bypass path:** `DSP02Handoff → DSP04` (skip DSP03 entirely)

Add a single function that “normalizes” whichever you pass in:

```
normalize_for_DSP04(feed):
    return {
      volume_m3: feed.volume_m3,
      opn_conc_gL: feed.opn_conc_gL,
      pH: feed.pH,
      conductivity_mM: feed.conductivity_mM,
      DNA_mgL: feed.DNA_mgL,
      chitosan_ppm: feed.chitosan_ppm or 0,
      flags: { polyP_present: feed.polyP_mM>0 }
    }
```

Downstream, **DSP04 never cares** whether it came from DSP02 or DSP03.

# 2) Add a “bypass DSP03” decision rule

Compute whether the capture pool already meets HIC’s salt window and pH:

- Define HIC guardrails (tune per resin):
  - `HIC_min_salt_M` (e.g., 0.5 M NaCl equivalent)
  - `HIC_max_salt_M` (e.g., 1.0 M, to avoid viscosity/solubility issues)
  - `HIC_pH_range = [6.0, 8.0]`
  - Optional: `HIC_max_polyP_mM` if polyP interferes

**Bypass rule (pseudo):**

```
if DSP04.method_chain starts with "HIC_FT"
   and feed.conductivity_mM ≥ salt_to_mM(HIC_min_salt_M)
   and feed.pH in HIC_pH_range
   and (polyP_present == False or polyP ≤ HIC_max_polyP_mM):
       source = DSP02Handoff  # bypass DSP03
else:
       source = DSP03Handoff  # run DSP03 as usual
```

You can also expose a **manual override**: `DSP03_Bypass=True` for scenario testing.

# 3) What if salt is high but *not* the right salt?

Two cases:

- **Right salt already (e.g., NaCl from AEX elution):** perfect—straight to HIC.
- **Wrong anion (e.g., polyphosphate from chitosan elution):** don’t feed HIC until you reduce/replace the anion. Two options:
  - Run **short DF in DSP03** to exchange polyP → chloride, *then* HIC.
  - If you really want to skip DSP03, make **DSP04_HIC** capable of a **pre-conditioning micro-step**: add a tiny in-unit DF/“salt swap” (e.g., 0.5–1.0 DV) accounted as **DSP04 buffer use**. Keep this strictly optional and only when volume is small; otherwise the DF belongs in DSP03.

I recommend the first (DF in DSP03) for clarity and scale economics.

# 4) Update the controller & YAML

Add these toggles:

```
dsp04:
  allow_bypass_dsp03: true
  hic_entry_conditions:
    min_salt_M: 0.5        # NaCl-equiv
    max_salt_M: 1.0
    pH_range: [6.0, 8.0]
    max_polyP_mM: 0        # set >0 if validated
  # If you insist on in-unit preconditioning:
  hic_precondition:
    enable: false          # true allows tiny DF/salt-swap inside DSP04_HIC
    dv: 0.5
    target_salt: "NaCl"
```

# 5) Make DSP04_HIC robust to either feed

Extend the HIC unit with two optional parameters:

- `feed_is_hic_ready: bool` (set by controller after checking conditions)
- `precondition_salt_swap_dv: float = 0.0` (0 means none; only used if enabled)

Then inside HIC:

- If `feed_is_hic_ready=True` → go straight to load.
- Else if `hic_precondition.enable=True` → perform the tiny DF/swap (adds buffer cost/time), re-check guards, then load.
- Else → raise a controller warning: “Feed not HIC-ready; enable DSP03 DF or HIC preconditioning.”

# 6) Handoffs and accounting

- When bypassing DSP03, make sure **DSP03 cost/time = 0** and your TEA and Gantt don’t include it.
- DSP04 client costs (resin fees, buffers, labor) still accrue normally.
- Sterile filtration remains mandatory at the end.

# 7) Edge cases to watch

- **Very high ionic strength (>1 M):** check OPN solubility/viscosity; you may need to dilute slightly before HIC to stay within ∆P and capacity limits.
- **PolyP presence:** strongly prefer clearing in DSP03; polyP can foul HIC or distort selectivity.
- **Chitosan fines:** ensure fines are below spec before HIC; if not, add a quick 0.2 µm guard (either in DSP02 or as the first step in DSP04).

# 8) Quick visual of the paths

```
           ┌─────────── AEX capture ───────────┐
Clarified →│                                    ├─→ (if HIC-ready) → DSP04_HIC → Sterile
           └── Chitosan capture (pH or polyP) ─┘
                           │
                           ├─ polyP present → DSP03_DF (1–3 DV) → (HIC-ready?) → HIC
                           └─ pH-mode (no polyP) → (HIC-ready?) → HIC
                           (not HIC-ready) → DSP03 SPTFF/DF as needed → DSP04 (AEX/CEX/HIC) → Sterile
```

# 9) Minimal validator strings

- “HIC bypass active: source=DSP02. Feed salt/pH within window.”
- “HIC bypass blocked: polyP detected; clear via DSP03 DF or enable HIC preconditioning.”
- “HIC DP limit exceeded at requested load; increase bed area or reduce linear velocity.”
- “Sterile 0.2 µm DP too high; add prefilter or increase area.”