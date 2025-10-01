# DSP02 — Chitosan Coacervate Capture (for OPN in *K. lactis* supernatant)

## Purpose

Electrostatic complexation of OPN (acidic, anionic) with protonated chitosan (cationic) to capture and remove soluble impurities, then **release** OPN by either **competitive displacement (polyphosphate)** or **pH shift**. Aim: CMO-scale viability (≥100 m³ broth), low consumables, recoverable polymer, friendly handoff to downstream polish.

------

## Unit block and streams

**Block:**

1. **DSP02-A Coacervation Reactor (mix/hold)**
2. **DSP02-B Solid–Liquid Separation** (centrifuge or filtration)
3. **DSP02-C Wash of Coacervate** (optional, reduces carryover salts/impurities)
4. **DSP02-D Elution/Resolubilization** (Mode 1: metaphosphate; Mode 2: pH 7.5)
5. **DSP02-E Post-elution Clarification** (remove chitosan fines)
6. **DSP02-F Chitosan Recovery & Re-protonation** (recycle loop; optional bleed)

**Key streams:**

- In: clarified supernatant from cell removal (pre-treated with benzonase if using)
- In: chitosan solution (spec: MW, DD%, concentration)
- In: acid (for chitosan make-up), NaOH (for pH elution), polyphosphate (for competitive elution)
- Out: spent liquor (unbound)
- Out: coacervate solids/paste
- Out: **OPN eluate** (to polish)
- Out: polymer recycle + bleed

------

## A. Coacervation reactor (DSP02-A)

**Operating window (defaults—tune with your lab fit):**

- **pH_bind:** 4.2 (tune 3.8–5.0)
- **Ionic strength:** 0–150 mM NaCl baseline; above ~150–250 mM reduces capture (tunable salt sensitivity factor)
- **Temperature:** 20–25 °C
- **Residence/hold:** 10–45 min (mix → floc growth → settle assist if needed)
- **Chitosan type:** LMW vs MMW; **degree of deacetylation (DD%)** 80–95% (affects charge density and floc strength)
- **Chitosan concentration for dosing:** 5–15 g/L in acidified make-up (e.g., 0.1–0.3% v/v acetic or HCl); inline diluted to target stoichiometry
- **Stoichiometry:** parameterized as **charge ratio** $R_q = \dfrac{[Chit^+]}{[OPN^-]}$ at process pH
  - Typical capture sweet spot: $R_q \approx 1.2{-}2.5$ (maps to your “2:1–4:1 by mass” lab heuristics once converted to charge)

**Design knobs:**

- `pH_bind`, `I_bind_mM`, `T_C`, `R_q`, `MW_class ∈ {LMW, MMW}`, `DD_pct`, `τ_hold_min`
- **Charge balance model:** computes the chitosan mass feed from protein mass and its net charge at pH (use OPN pI and titration curve; practical shortcut: fit chitosan:OPN mass ratio vs pH from your 96-well DoE)

**Performance models:**

- **Capture yield (to coacervate):**
   $Y_{\text{cap}} = f(pH, I, R_q, MW, DD)$
   Use your plate data to fit a response surface; good starting plateaus: **80–95%** at optimal window.
- **DNA/HCP removal:** track as log-removal vs. same factors; DNA often co-captures **(0.5–1.5 log)** if benzonase used upstream, more if not.
- **Floc solids content:** 1–6 % w/w after growth (governs separator choice)

**Scale-up notes:**

- Impeller tip speed low–moderate (avoid over-shear → fines, poor separation)
- RTD smoothing via draft-tube or baffles; consider **flocculant addition split** (2-point addition) to avoid local over-dosage

------

## B. Solid–liquid separation (DSP02-B)

**Options (choose by floc size/strength and throughput):**

- **Disc-stack centrifuge:** good if flocs are compact (apparent d50 ≳ 2–5 µm, robust).
- **Decanter centrifuge:** tolerant to bulky flocs; lower g, larger footprint; continuous.
- **Rotary vacuum filter (RVF) / Belt filter:** when flocs are filterable and you want a wash.
- **Depth filtration:** as a backup/polish or when solids are modest; watch consumables.

**Design knobs:**

- `Σ` for disc-stack; G-factor/pond depth for decanter; filter area & ∆P for RVF
- Target cake/solids dryness and throughput

**Performance targets:**

- **Supernatant turbidity:** <50–100 NTU to protect downstream
- **Coacervate capture recovery:** minimal breakage losses; tank and piping shear minimized

------

## C. Coacervate wash (DSP02-C, optional but recommended)

**Purpose:** remove loosely bound impurities, salts that will otherwise carry into eluate.

- **Wash liquor:** same pH_bind, **low ionic strength** (0–50 mM)
- **Wash ratio:** 0.3–1.0 BV of wet cake (optimize with pilot)
- **Number of washes:** 1–2
- **Expected effects:** +0.5–2% OPN loss per wash, but cleaner eluate; choose based on polish economics

------

## D. Elution / release (DSP02-D)

Two validated modes. Keep both in model; choose per scenario.

### Mode 1: **Metaphosphate competitive elution (low pH)**

- **Mechanism:** Polyphosphate competes for chitosan cationic sites; OPN released at **same acidic pH** (keeps chitosan protonated/insoluble).
- **Eluant:** sodium **hexametaphosphate** (or tripolyphosphate) at pH_bind (±0.2 pH)
- **Dose:** 10–100 mM as **P-equiv**; start at 25–50 mM and fit to your lab curve
- **Hold:** 5–20 min mix; optional second contact for near-quantitative release
- **Pros:** Chitosan remains insoluble → easy solid–liquid split; OPN stays in solution at low pH
- **Cons:** **High anion load** (polyphosphate) in eluate → can antagonize AEX later; usually requires **DF (1–3 DV)** to remove polyP

### Mode 2: **pH-shift elution (to ~7.5)**

- **Mechanism:** Deprotonate chitosan (pKa ~6.3), **loses charge & insolubilizes**; OPN desorbs into aqueous phase.
- **Eluant:** NaOH (or Tris base) to **pH 7.2–7.8**, ionic strength 50–150 mM
- **Hold:** 5–20 min mix
- **Pros:** No polyP in eluate; conductivity moderate; OPN often stable at neutral pH; chitosan remains **insoluble solid** → easy removal
- **Cons:** If OPN has pH-dependent aggregation, watch viscosity; may solubilize traces of chitosan oligomers—polish will catch

**Performance to model for both modes:**

- **Elution yield:** 90–99% of captured OPN (fit to dose and time)
- **Carryover of chitosan fines:** 10–500 ppm before polish (depends on separator)
- **Eluate conductivity:** track; **polyP mode** will spike anions; **pH mode** mildly increases Na⁺

------

## E. Post-elution clarification (DSP02-E)

**Goal:** remove chitosan fines to **<10–100 ppm** and cut turbidity for polish.

**Options:**

- **Disc-stack polish** (low shear, high throughput)
- **Depth filtration train** (e.g., 10 µm → 1 µm)
- **0.2 µm guard** if going to membrane or AEX polish

**Design knobs:** filter area from capacity (L/m²) measured on eluate; centrifuge Σ if using machine polish.

------

## F. Chitosan recovery & recycle (DSP02-F)

**Loop:**

1. Collect chitosan solids after elution.
2. **Acidify** with HCl/acetic to pH 3–4 to re-protonate and re-solubilize.
3. Clarify to remove grit/contaminants.
4. Meter back to DSP02-A as **make-up polymer**.

**Model variables:**

- `Recycle_fraction` (e.g., 0.5–0.9), `Activity_retained` (charge capacity), `Quality_drift` (fouling coefficient per cycle)
- **Bleed** a fraction each cycle (e.g., 5–10%) to control buildup of contaminants
- **Polymer cost savings** vs. fresh; include **acid/base** costs for re-conditioning

------

## Performance & quality summary (typical ranges to start)

- **Overall capture + elute recovery:** 85–95% (coacervation + elution + handling)
- **DNA removal:** 1–2 log (with benzonase upstream), sometimes higher
- **HCP removal:** 0.5–1.5 log (matrix-dependent)
- **Chitosan residue in eluate (pre-polish):** 10–500 ppm (reduce to spec in polish)
- **Conductivity of eluate:**
  - **PolyP mode:** high anion—plan **DF (1–3 DV)** before ion-exchange polish
  - **pH mode:** moderate—often **no DF** needed before polish

------

## Economics hooks (CDMO-friendly)

- **Chitosan cost ($/kg)** by grade; **make-up rate** = demand − recycle
- **Acid/base cost** for make-up and pH-mode elution
- **Polyphosphate cost ($/kg as P-equiv)** & **DF buffer** volume (if used)
- **Separation OPEX:** centrifuge power, filter media $/m² and changeout frequency
- **Labor** and **cycle time** per batch
- **Waste**: wet cake (kg), spent filtrate volumes, bleed polymer disposal

> If you’re in CDMO mode: treat **equipment CAPEX** (centrifuges/filters) as flagged; cost via **per-m³ processing fee** + **consumables** + **buffers/chemicals**.

------

## Guardrails & feasibility checks

- **Salt sensitivity:** if feed ionic strength > threshold (your sheet), down-rate $Y_{\text{cap}}$ or demand pre-dilution.
- **Viscosity / floc size:** if flocs too fine, warn “separation risk” → require coagulant aid (e.g., minimal polyP pre-dose or low-MW chitosan spike) or slower mixing.
- **Elution choice:**
  - If downstream polish is **AEX** → **prefer pH-mode** to avoid polyP burden, unless lab data prove higher yield with polyP worth the extra DF.
  - If downstream polish is **CEX-negative** or **HIC** → both modes workable; assess by DF needs and resin compatibility.
- **Residual chitosan spec:** set `Chitosan_ppm_max`; if exceeded after DSP02-E, force a **polish** step selection.

------

## Downstream **Polish** options after DSP02 (pick by cost/compatibility)

| Polish option                                   | What it does well                                            | Scale & cost notes                           | When to pick                                                 |
| ----------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------- | ------------------------------------------------------------ |
| **AEX polish (bind-and-elute or flow-through)** | Removes residual chitosan (anionic at high pH? often non-binding), DNA, small proteins | Ubiquitous; resin $ but high productivity    | If eluate is near neutral & low salt (pH-mode). Min DF.      |
| **CEX negative chromatography**                 | Lets OPN flow through while cations bind                     | Robust, cheap resins; low salt               | If OPN stays net negative; excellent chitosan removal (cationic residues bind). |
| **HIC (flow-through)**                          | Orthogonal to charge; removes hydrophobes/aggregates         | Resin $/m² higher; needs salt                | If aggregates/hydrophobes matter; check OPN salt tolerance.  |
| **Ammonium sulfate precipitation**              | Bulk de-junking/vol cut                                      | Salt & handling heavy; resolubilization + DF | If aiming for very low resin usage; OPN must resolubilize cleanly. |
| **Heat step (pasteurization-style)**            | OPN is heat-stable; denature heat-labile impurities          | Simple; check viscosity/fouling              | If analytics confirm OPN retains activity & aggregates don’t form. |
| **Solvent precipitation (e.g., ethanol)**       | Strong deproteination                                        | Safety/EX-proof + solvent recovery           | Only if the economics beat membranes/resins (often not at 100 m³). |

**Fast rule-set:**

- If DSP02 elution uses **pH-mode** and conductivity is modest → **CEX-negative** is a beautiful, cheap polish.
- If you must use **polyP** → plan **DF** first, then **AEX polish** or **CEX-negative**.
- If analytics say “tiny hydrophobe/aggregate problem” → add **HIC-FT** as a slim module.

------

## Decision matrix: PolyP vs pH-mode elution

| Criterion                   | PolyP (low pH)                       | pH-mode (7.2–7.8)            |
| --------------------------- | ------------------------------------ | ---------------------------- |
| Elution yield ceiling       | **High** (strong competitor)         | High (if pH window tuned)    |
| Chitosan state              | Insoluble solid                      | Insoluble solid              |
| Eluate compatibility w/ AEX | **Poor** without DF (polyP competes) | **Good** (often DF-free)     |
| Buffer/chemical cost        | PolyP + DF buffers                   | NaOH + minor salts           |
| Cycle time                  | Similar (may add DF)                 | Usually shorter end-to-end   |
| Risk/complexity             | PolyP inventory, fouling risk        | Simpler chemicals & disposal |

**Recommendation (default):** **pH-mode elution** for lowest downstream friction. Keep **polyP mode** as an alternative when yield testing shows a clear advantage.

------

## BioSTEAM-ready spec fields

**Design inputs (common):**
 `pH_bind, I_bind_mM, T_C, R_q, Chitosan_MW_class, DD_pct, τ_hold_min, Separator_type, Wash_BV, Wash_count, Elution_mode∈{polyP,pH}, PolyP_mM, pH_elute, I_elute_mM, Clarifier_type, Recycle_fraction, Bleed_fraction, Activity_retained, Polymer_cost_per_kg, Acid_cost_per_kg, Base_cost_per_kg, PolyP_cost_per_kg, Filter_media_cost_per_m2, CDMO_processing_fee_per_m3, …`

**Design algorithm outputs:**

- Chitosan make-up (kg), recycle (kg), bleed (kg)
- Reactor volume & time; separator selection & duty (Σ or area)
- Wash volumes; elution volumes/chemicals; post-elution clarification area/Σ
- Cycle time per batch

**Performance outputs:**

- `Capture_yield_pct`, `Elution_yield_pct`, `Overall_DSP02_yield_pct`
- `DNA_log_reduction`, `HCP_log_reduction`
- `Eluate: volume, OPN_gL, pH, conductivity_mM, chitosan_ppm`
- `Residual polyP_mM` (if used) → triggers DF need flag

**Costs:**

- Chemicals (acid/base/polyP), polymer net consumption, separation media/energy, labor, CDMO fee, waste handling
- CAPEX fields flagged (if you want them for in-house scenarios later)

**Warnings:**

- Ionic strength above threshold → capture derated or infeasible
- Flocs too fine for chosen separator → suggest decanter or filter aid
- Eluate incompatible with chosen polish (e.g., polyP → AEX) → auto-insert DF or propose pH-mode

------

## Quick numeric defaults (placeholders to start; replace with your data)

- `pH_bind=4.2`, `I_bind=50 mM`, `R_q=1.8`, `τ_hold=20 min`, `LMW chitosan, DD=90%`
- **Capture yield** 90%, **Elution yield** 97% (pH-mode), overall **87%**
- **PolyP mode:** 40 mM as P-equiv, elution 98%, overall **~88–90%**, but add **DF = 2 DV**
- **Chitosan recycle:** 0.7 recycle, 0.05 bleed/cycle, **activity retained** 0.9/cycle equivalent
- **Post-elution fines:** 100 ppm pre-polish, goal **<10 ppm** after DSP02-E
- **Post-DSP02 polish default:** **CEX-negative FT at pH 7.0**, no DF needed for pH-mode; **AEX polish** if polyP used (after DF)

------

## What to validate early (saves months of regret)

1. **Response surface**: OPN capture vs **pH × salt × R_q × MW_class** (small DoE)
2. **Elution tradeoff**: pH-mode vs polyP at matched capture—measure yield and **downstream costs** (DF, resin antagonism)
3. **Floc separability**: d50, compressibility, and separator selection curves (disc-stack vs decanter vs filter)
4. **Recycle health**: activity decay per loop, impurity buildup, bleed fraction economics
5. **Residual chitosan spec**: ppm vs polish option; verify CEX-negative can hit spec at modest load

------

## Bottom line

- The **default economical route** for OPN at scale is:
   **Coacervate at pH ~4–4.5 → Separate → (Wash) → Elute by pH 7.5 → Clarify fines → CEX-negative polish**
   Minimal salt burden, no polyP headaches, great fit for CDMO operations.
- Keep **polyP elution** as a **scenario toggle**; it can squeeze a touch more yield but usually demands **DF** before ion-exchange polish, which often erases the gain.

When you’re ready, I can hand you a compact parameter pack (names/units/ranges) mirroring these fields so your BioSTEAM classes and Excel named ranges slot in cleanly—and we can wire the decision logic that automatically proposes the cheapest viable polish given the chosen elution mode and your conductivity/spec targets.

##### You said:

yes, please

###### ChatGPT said:

Awesome—here’s a **drop-in parameter pack** for **DSP02 Chitosan Coacervate Capture** plus a compact **equations sheet** and **named-range keys**. It’s code-free but precise enough to wire straight into your BioSTEAM classes and your spreadsheet/JSON layer.

------

# DSP02 parameter pack (JSON-style)

```
{
  "Ownership_Mode": "CDMO",                       // CDMO | InHouse
  "Include_CAPEX": false,

  "DSP02_Global": {
    "Batch_Volume_m3": 100.0,
    "Feed_Prot_g_L": 1.0,
    "Feed_DNA_mg_L": 5.0,
    "Feed_Cond_mM": 120.0,
    "Feed_pH": 4.5,
    "Temp_C": 25.0
  },

  "DSP02A_Coacervation": {
    "pH_bind": 4.2,
    "I_bind_mM": 50.0,
    "Hold_Time_min": 20.0,
    "Charge_Ratio_Rq": 1.8,                       // (+)chitosan : (−)OPN @ pH_bind
    "Chitosan_MW_Class": "LMW",                   // LMW | MMW
    "Chitosan_DD_pct": 90.0,
    "Chitosan_Soln_g_L": 10.0,                    // make-up solution conc
    "Mix_TipSpeed_m_s": 1.5,
    "Baffles": true,

    "Capture_Yield_pct_base": 90.0,               // lab-fit @ defaults
    "Salt_Sensitivity_kI": -0.15,                 // %Δyield per +100 mM
    "Rq_Response_kRq": 12.0,                      // %Δyield per +0.5 Rq (near optimum)
    "MW_Class_Factor": { "LMW": 1.00, "MMW": 1.03 }
  },

  "DSP02B_Separation": {
    "Mode": "DiscStack",                          // DiscStack | Decanter | RVF | DepthFilter
    "Sigma_per_unit_m2": 9000.0,
    "Units_Parallel_max": 4,
    "Target_Turbidity_NTU": 80.0,
    "Floc_Solids_wt_pct": 3.0,
    "Power_kW_per_unit": 15.0
  },

  "DSP02C_Wash": {
    "Enable": true,
    "Washes": 1,
    "Wash_Ratio_BV_per_wash": 0.5,                // wash liquor : wet-cake bed volumes
    "Wash_pH": 4.2,
    "Wash_I_mM": 25.0,
    "Loss_pct_per_wash": 1.0
  },

  "DSP02D_Elution": {
    "Mode": "pH",                                 // pH | PolyP
    "pH_elute": 7.5,
    "I_elute_mM": 100.0,
    "PolyP_mM_asP": 40.0,                         // only used if Mode=PolyP
    "Elution_Contact_min": 10.0,
    "Elution_Temp_C": 25.0,
    "Elution_Yield_pct_base": 97.0,               // lab-fit @ defaults
    "PolyP_DF_DV_required": 2.0                   // diavolumes if Mode=PolyP (for downstream)
  },

  "DSP02E_PostElution_Clarification": {
    "Mode": "DepthFilter",                        // DiscStack | DepthFilter | Guard0p2
    "Grades_um": [10, 1],
    "Specific_Capacity_L_m2": [120.0, 70.0],
    "Flux_LMH_cap": 100.0,
    "HoldUp_L_per_10in": 0.6,
    "Target_Chitosan_ppm": 10.0,
    "PrePolish_Chitosan_ppm_est": 100.0
  },

  "DSP02F_Polymer_Recycle": {
    "Recycle_Fraction": 0.70,
    "Bleed_Fraction": 0.05,
    "Activity_Retained_per_Loop": 0.90,
    "Acid_Reprotonation_pH": 3.5,
    "Fresh_Chitosan_Cost_USD_per_kg": 45.0,
    "Acid_Cost_USD_per_kg": 0.20,
    "Base_Cost_USD_per_kg": 0.20,
    "PolyP_Cost_USD_per_kg_asP": 3.00
  },

  "Economics_CDMPass": {
    "Processing_Fee_USD_per_m3": 65.0,
    "Filter_Media_USD_per_m2": 180.0,
    "Labor_h_per_batch": 10.0,
    "Labor_USD_per_h": 80.0,
    "Overhead_USD_per_batch": 1500.0,
    "Waste_Disposal_USD_per_tonne": 220.0
  },

  "Polish_Selector": {
    "Preferred": "CEX_Negative",                  // CEX_Negative | AEX_Polish | HIC_FT | Heat | Precipitation
    "Chitosan_ppm_max": 10.0,
    "Conductivity_mM_max_for_AEX": 200.0,
    "Notes": "If Elution.Mode=PolyP, enforce DF before AEX/CEX."
  }
}
```

------

# Equations sheet (compact, implementation-ready)

**Symbols:** $V$ volume [m³], $C$ concentration, $m$ mass, DV diavolumes, LMH = L·m⁻²·h⁻¹.

### A) Coacervation dose & capture

1. **OPN charge proxy at pH_bind** (use your lab fit or simple linearization):
    $z_{\text{OPN}}(pH) \rightarrow$ use table/fit.
    **Chitosan cationic sites** per kg at pH_bind from DD% and MW class → embed as parameter $q_{\text{Chit}}^+$ [eq·kg⁻¹].
2. **Chitosan mass dose** (from charge ratio $R_q$):
    $m_{\text{Chit}} = \dfrac{R_q \cdot |z_{\text{OPN}}| \cdot m_{\text{OPN}}}{q_{\text{Chit}}^+}$
3. **Capture yield** (percent):
    $Y_{\text{cap}} = Y_{\text{base}} \cdot f_I(I_{\text{bind}})\cdot f_{Rq}(R_q)\cdot f_{MW}$
    with:
    $f_I = 1 + k_I \cdot (I_{\text{bind}} - 50)/100$ (clip 0–1)
    $f_{Rq} = 1 - k_{Rq}\cdot (R_q - 1.8)^2$ near optimum (or your RSM)
    $f_{MW} \in \{1.00, 1.03\}$
4. **Captured OPN mass**:
    $m_{\text{cap}} = Y_{\text{cap}} \cdot m_{\text{OPN,in}}$

### B) Separation sizing

- **Disc-stack capacity constraint:**
   $Q \le v_{set,1g}\cdot \Sigma$, with Stokes $v_{set,1g}$ from floc d₅₀, $\rho,\mu$.
   Parallel units = $\lceil Q_{\text{req}} / Q_{\text{per unit}}\rceil$.

### C) Wash losses

- Per wash: $m_{\text{loss,wash}} = \text{Loss\%} \cdot m_{\text{cap}}$
- After $n$ washes: $m_{\text{cap,washed}} = m_{\text{cap}}\cdot (1 - \text{Loss\%})^n$

### D) Elution

- **pH-mode elution yield**: $Y_{\text{elu}} = Y_{\text{elu,base}} \cdot g(pH_{\text{elu}})$
   (use your curve; default flat near 7.2–7.8).
- **PolyP-mode yield**: $Y_{\text{elu}} = Y_{\text{elu,base}} \cdot h(\text{PolyP}_mM)$ (saturating fit).
- **Eluate mass**: $m_{\text{OPN,elu}} = m_{\text{cap,washed}} \cdot Y_{\text{elu}}$
- **If PolyP:** require DF; DV to residual $f$: $DV = -\ln(f)$. Use default DV=2 for ~86% polyP removal (f≈0.14).

### E) Post-elution clarification (filters)

- **Area per grade**: $A_i = \max\!\left(\dfrac{V_{\text{elu}}}{\text{Cap}_i},\, \dfrac{Q}{J_{\max}}\right)$
- **Hold-up loss**: $m_{\text{loss,holdup}} = \rho \cdot \text{HoldUp} \cdot C_{\text{OPN,elu}} \cdot N_{\text{modules}}$

### F) Polymer recycle

- **Recycle mass to next batch**:
   $m_{\text{Chit,recycle}} = \text{Recycle\_Fraction} \cdot m_{\text{Chit,recovered}} \cdot \text{Activity\_Retained}$
- **Fresh make-up**:
   $m_{\text{Chit,fresh}} = m_{\text{Chit,req}} - m_{\text{Chit,recycle,eq}} + \text{Bleed}$

### G) Overall step recovery

$$
Y_{\text{USP03}} = \frac{m_{\text{OPN,postClar}}}{m_{\text{OPN,in}}}
= Y_{\text{cap}} \cdot (1-\text{Loss}_{\text{wash}})^{n} \cdot Y_{\text{elu}} \cdot (1-\text{Loss}_{\text{holdup}})\,.
$$

### H) Economics (CDMO pass-through)

$$
\begin{aligned}
\text{ChemCost} &= m_{\text{Chit,fresh}}\cdot C_{\$/kg}^{\text{Chit}} + m_{\text{acid}}\cdot C_{\$/kg}^{\text{Acid}} + m_{\text{base}}\cdot C_{\$/kg}^{\text{Base}} + m_{\text{polyP}}\cdot C_{\$/kg}^{\text{PolyP}} \\
\text{FilterCost} &= \sum_i A_i \cdot C_{\$/m^2}^{\text{media}} \\
\text{ProcessingFee} &= \text{Processing\_Fee}_{\$/m^3} \cdot V_{\text{processed}} \\
\text{Labor} &= \text{Labor\_h} \cdot \text{Rate}_{\$/h} \\
\text{Waste} &= m_{\text{wet\_cake}}\cdot C_{\$/t}^{\text{disposal}} \\
\text{USP03\_CDMO\_Cost} &= \text{ChemCost} + \text{FilterCost} + \text{ProcessingFee} + \text{Labor} + \text{Overhead} + \text{Waste}
\end{aligned}
$$

------

# Named-range keys (minimal, one row per knob)

You can paste this header row into your spreadsheet to keep naming consistent; fill rows beneath for scenario packs.

```
Parameter,Module,Key,Unit,Default,Min,Max,Notes
Batch_Volume,DSP02_Global,Batch_Volume_m3,m3,100,1,300,Processed per batch
Feed_Prot,DSP02_Global,Feed_Prot_g_L,g/L,1.0,0.1,10,OPN in clarified feed
Feed_DNA,DSP02_Global,Feed_DNA_mg_L,mg/L,5,0,100,After benzonase
Feed_Cond,DSP02_Global,Feed_Cond_mM,mM,120,0,500,At DSP01 outlet
pH_bind,DSP02A,pH_bind,,4.2,3.6,5.2,Coacervation pH
I_bind,DSP02A,I_bind_mM,mM,50,0,250,NaCl equivalent
Rq,DSP02A,Charge_Ratio_Rq,,1.8,1.0,3.0,Chitosan(+):OPN(−) charge
Chitosan_MW,DSP02A,Chitosan_MW_Class,,LMW,,,"LMW|MMW"
Chitosan_DD,DSP02A,Chitosan_DD_pct,%,90,80,95,Deacetylation
Hold_Time,DSP02A,Hold_Time_min,min,20,5,60,Mixing/aggregation
Capture_Base,DSP02A,Capture_Yield_pct_base,%,90,60,99,Fit from lab
Sigma,DSP02B,Sigma_per_unit_m2,m2,9000,3000,15000,Disc-stack capacity
Sep_Mode,DSP02B,Mode,,DiscStack,,,"DiscStack|Decanter|RVF|DepthFilter"
Wash_Enable,DSP02C,Enable,,TRUE,,,
Wash_Count,DSP02C,Washes,,1,0,2,Number of washes
Wash_Ratio,DSP02C,Wash_Ratio_BV_per_wash,BV,0.5,0,1,Per wash
Elu_Mode,DSP02D,Mode,,pH,,,"pH|PolyP"
pH_elute,DSP02D,pH_elute,,7.5,7.0,8.0,If Mode=pH
PolyP_mM,DSP02D,PolyP_mM_asP,mM,40,10,100,If Mode=PolyP
Elu_Yield_Base,DSP02D,Elution_Yield_pct_base,%,97,85,99,Fit from lab
DF_DV_Req,DSP02D,PolyP_DF_DV_required,DV,2,0,4,DF needed if PolyP
Clar_Mode,DSP02E,Mode,,DepthFilter,,,"DiscStack|DepthFilter|Guard0p2"
Grades,DSP02E,Grades_um,um,"10;1",,,"Semicolon-separated"
Cap_Specific,DSP02E,Specific_Capacity_L_m2,L/m2,"120;70",,,"Match grades"
RecycleFrac,DSP02F,Recycle_Fraction,,0.7,0,0.95,Polymer recycle fraction
BleedFrac,DSP02F,Bleed_Fraction,,0.05,0,0.2,Polymer bleed per loop
ActivityKeep,DSP02F,Activity_Retained_per_Loop,,0.9,0.7,1.0,Charge capacity retention
Chitosan_ppm_Spec,Polish_Selector,Chitosan_ppm_max,ppm,10,1,100,Triggers polish
Cond_max_AEX,Polish_Selector,Conductivity_mM_max_for_AEX,mM,200,50,300,Guardrail for AEX
```

------

# Auto-selection logic (tiny rule set)

1. **Elution mode:** prefer **pH-mode**. If lab data show ≥1% absolute yield gain with PolyP *and* DF cost per batch < yield value → allow **PolyP**.
2. **Separator:** if predicted floc d₅₀ ≥ 3 µm and solids ≥ 1.5% → **Disc-stack**; else **Decanter** if bulky/compressible; else **DepthFilter** as fallback (warn on media cost).
3. **Polish:**
   - If `Elution.Mode="pH"` and `Chitosan_ppm ≤ spec` → **CEX-negative** by default.
   - If `Elution.Mode="PolyP"` → **DF** to clear polyP, then **AEX polish** or **CEX-negative** per conductivity.
   - If hydrophobes/aggregates flag on → add **HIC-FT**.

------

# What this gives you now

- A single JSON blob you can drop in as defaults.
- A short equations sheet to paste into your constructor/design docs.
- A clean set of named keys for your spreadsheet layer.

When you run this, you’ll immediately see the **economic crossover** between **pH-mode elution + CEX-negative** versus **PolyP + DF + AEX polish**, and you can tune the recycle loop to see how quickly chitosan costs collapse with a modest bleed. Next iteration, we can plug in your actual lab fits for capture/elution surfaces and your separator σ/area data to replace the placeholder coefficients.





One thing to keep in mind is we already have a DSP03 and DSP04 module in the spreadsheet that may overlap with some of the operations you have for the chitosan method (which by the way is DSP02 not USP03). How is it best to reconcile with those so we have a seamless swap of chromatography for chitosan.

###### ChatGPT said:

Thought for 8s

Got it—thanks for the correction: **Chitosan route = DSP02**, not USP03. Let’s make your workbook and BioSTEAM model **hot-swappable** between **DSP02_AEX** and **DSP02_CHITOSAN** without breaking DSP03/DSP04.

Here’s a clean reconciliation plan that keeps your existing **DSP03/DSP04** intact and avoids double-counting or logic spaghetti.

# 1) Define a single “handoff contract” for DSP02

Make **both** DSP02 variants output the same named fields so DSP03/DSP04 don’t care which path produced them.

**DSP02 handoff (identical schema regardless of route):**

- `DSP02_Pool_Volume_m3`
- `DSP02_OPN_Conc_gL`
- `DSP02_Conductivity_mM`
- `DSP02_pH`
- `DSP02_DNA_mgL`
- `DSP02_Chitosan_ppm` (0 for AEX route)
- `DSP02_PolyP_mM` (0 for AEX route; >0 if chitosan–polyP elution)
- `DSP02_Step_Recovery_pct`
- `DSP02_Needs_DF_Flag` (TRUE if polyP elution or cond > target)
- `DSP02_Needs_Fines_Polish_Flag` (TRUE if chitosan fines > spec)
- `DSP02_Time_h` (for cycle time/Gantt if you use it)
- `DSP02_Cost_per_batch` (CDMO pass-through; CAPEX flagged separately)

Everything downstream (DSP03/DSP04) consumes only these.

# 2) Route switch + adapter layer (one place only)

Create a **single selector cell**:

- `Capture_Route` ∈ {`DSP02_AEX`, `DSP02_CHITOSAN`}

Build a tiny **adapter block** (think “view” table) that maps the active route’s raw outputs into the handoff fields above. This lives once—e.g., in `Calculations!DSP02_Handoff`.

Example Excel pattern (using `XLOOKUP`/named ranges):

```
DSP02_Pool_Volume_m3 :=
IF(Capture_Route="DSP02_CHITOSAN",
    DSP02C_Pool_Volume_m3,
    DSP02A_Pool_Volume_m3)

DSP02_Needs_DF_Flag :=
IF(Capture_Route="DSP02_CHITOSAN",
    OR(DSP02C_PolyP_mM>0, DSP02C_Conductivity_mM>Polish_Cond_Target_mM),
    DSP02A_Conductivity_mM>Polish_Cond_Target_mM)
```

Do this **once** for each handoff field—then tell DSP03/DSP04 to only read from the **handoff table**, never directly from AEX/Chitosan sub-tables.

# 3) Partition responsibilities to avoid overlap with DSP03/DSP04

Decide which unit “owns” which operation. Recommended:

- **DSP02 (AEX or Chitosan)** owns:
  - Capture + primary elution
  - Immediate post-step **route-specific** necessities:
    - AEX: none beyond skid hold-ups
    - Chitosan: **post-elution fines removal** by a light **clarifier/depth filter** (USP03-E in prior spec) to get chitosan to a manageable ppm for polish
  - Route flags: `Needs_DF_Flag`, `Needs_Fines_Polish_Flag`
- **DSP03** owns **mandatory polish** chosen by your selector logic:
  - Default after AEX capture: usually **skip** (or a light polish if you already planned it)
  - Default after Chitosan: **CEX-negative** or **AEX polish** (if polyP used), or HIC-FT by rule
  - If `Needs_DF_Flag=TRUE`, **DSP03** inserts **DF** before resin polish and accounts its cost/time
  - If `Needs_Fines_Polish_Flag=TRUE` even after DSP02’s quick fines step, DSP03 escalates a tighter filter/guard
- **DSP04** keeps your existing **buffer-set/conditioning or formulation** step. It only sees the **polished** pool from DSP03.

This way, you don’t duplicate DF or fines removal across modules.

# 4) Tiny rule set to drive DSP03 automatically

Place these rules in `Calculations!DSP03_Control`:

- **Polish selection:**
  - If `Capture_Route="DSP02_CHITOSAN"` and `DSP02_PolyP_mM>0` → `DSP03_Method="DF + AEX_Polish"`
  - Else if `Capture_Route="DSP02_CHITOSAN"` → `DSP03_Method="CEX_Negative"`
  - Else (`DSP02_AEX`) → `DSP03_Method="None"` (or your planned polish)
- **DF insertion:**
  - `Insert_DF := DSP02_Needs_DF_Flag`
  - `DF_DV := IF(DSP02_PolyP_mM>0, PolyP_DF_Default_DV, Short_DF_for_Cond_DV)`
- **Fines guard:**
  - If `DSP02_Chitosan_ppm > Chitosan_ppm_max` → add **0.2 µm guard** before resin polish

Expose these three in the UI so you can override per scenario.

# 5) Cost rollup without double counting (CDMO mode)

- **DSP02_AEX**: cost/buffers/resin fee → `DSP02_Cost_per_batch`
- **DSP02_CHITOSAN**: polymer/acid/base/sep media → `DSP02_Cost_per_batch`
- **DSP03**: polished resin usage + **conditional DF** + any guard filters → `DSP03_Cost_per_batch`
- **DSP04**: as is
- **Total** = sum of module costs; keep CAPEX **flagged** but excluded in CDMO totals

# 6) Minimal migration steps (practical)

1. **Add selector** `Capture_Route`.
2. **Create DSP02 adapter table** with the handoff fields; wire both sub-paths into it.
3. **Update DSP03 inputs** to read only from the **adapter handoff**.
4. **Implement DSP03 control rules** (method pick, DF insert, fines guard).
5. **Check dependency graph** (Excel’s `Formulas → Trace Dependents`) to ensure no sheet still references raw AEX/Chitosan cells.
6. **Scenario Capture**: add `Capture_Route` and the key DSP02 flags to your scenario IF/INDEX block so snapshots persist.

# 7) Naming alignment (examples)

- Raw AEX outputs: `DSP02A_*`
- Raw Chitosan outputs: `DSP02C_*`
- Handoff: `DSP02_*` (canonical)
- DSP03 control: `DSP03_Method`, `DSP03_Insert_DF`, `DSP03_DF_DV`, `DSP03_Insert_Guard0p2`
- Specs: `Polish_Cond_Target_mM`, `Chitosan_ppm_max`

# 8) Sanity checks (validators)

Add a small validator table that lights up if:

- `DSP02_Conductivity_mM > DSP03_Method_BindCond_mM_max`
- `DSP02_Chitosan_ppm > Chitosan_ppm_max` with `DSP03_Insert_Guard0p2=FALSE`
- `DSP03_Method="None"` while `DSP02_PolyP_mM>0` (forbidden)
- `DSP02_Step_Recovery_pct * DSP03_Step_Recovery_pct < 0.80` (red flag)

# 9) BioSTEAM mirror (so sim and sheet match)

- Create **two unit classes**: `DSP02A_AEX`, `DSP02C_Chitosan`
- A **thin wrapper** `DSP02` runs exactly one, then writes the **handoff dataclass** consumed by `DSP03`.
- `DSP03` reads only the handoff; inserts DF/guard and selects polish according to the same rules.

—

This gives you a **single switch** for AEX↔Chitosan, a **single handoff contract**, and **centralized logic** in DSP03 for any extra cleanup—so the rest of the model stays blissfully unaware of the route drama. When you’re ready, I can draft the specific Excel cell map for your `Inputs & Assumptions` and `Calculations` sheets to drop these fields exactly where your nine-column schema expects them.