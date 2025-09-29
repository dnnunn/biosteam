# TL;DR recommendation (what CMOs do at ≥100 m³)

For yeast like *K. lactis* at 50–200 m³:

- **Primary:** Disc-stack centrifugation (nozzle or self-cleaning) for cell harvest/clarification.
- **Polish:** Depth filtration (one or two grades) to remove fines/colloids before UF/TFF or chromatography.
- **Alternatives:** Continuous tubular/pusher centrifuges are niche; tangential microfiltration for *unclarified* yeast broth at this scale is usually punished by area, fouling, and cleaning overhead—often only viable as a **post-centrifuge** polish or as a specialized flowpath when solids are unusually low.

So your scalable, CMO-standard flowsheet at 100 m³+ is:
 **Fermenter → Disc-stack centrifuge (harvest) → Depth filter(s) (clarify) → UF/TFF → …**

Below is everything you need to spec each unit in BioSTEAM terms.

------

## Cross-cutting feed assumptions (set as named inputs)

These are the “truth knobs” the four units will consume.

- **Feed volume per batch (m³):** 1–200 (baseline: 100)
- **Broth temperature (°C):** 20–30 (baseline: 25)
- **Density (kg/m³):** 1,020–1,080 (baseline: 1,040)
- **Viscosity (mPa·s):** 1.2–3.0 (baseline: 1.5)
- **Wet solids (% v/v):** 5–12 for yeast (baseline: 8)
- **Cell diameter (µm):** 3–6 (baseline: 4.5)
- **Fines/Turbidity (NTU or mg/L as PSD proxy):** set as needed
- **Target protein location:** secreted in supernatant
- **Protein concentration (g/L):** your model’s current value
- **Shear sensitivity:** low/moderate for OPN (affects lysis penalties)
- **Antifoam present (y/n):** influences filter loading, fouling
- **DNA/host cell proteins baseline (mg/L):** optional—useful for CQAs

------

# Unit specs

## A) Disc-stack centrifuge (primary harvest)

**Purpose:** Remove intact yeast cells and most large fines, high throughput, good scalability.

**Streams**

- In: fermentation broth
- Out1: clarified supernatant
- Out2: wet cell concentrate (for disposal or reuse)

**Key design variables**

- **Σ (sigma, m²):** equivalent settling area; proxy for capacity
- **Operating mode:** nozzle (continuous discharge) or self-cleaning
- **Bowl speed (rpm):** vendor-constrained; treat as embedded in Σ
- **Solids capacity (kg/h):** constraint; limits at high biomass
- **Dilution factor:** optional (adds water to reduce viscosity)
- **Inlet shear index:** surrogate to penalize lysis

**Performance model**

- **Throughput capacity:** $Q \le v_{set,1g} \cdot \Sigma$
  - $v_{set,1g} = \dfrac{d_p^2(\rho_p-\rho_f)g}{18\mu}$ (Stokes)
  - Use your dp, densities, viscosity. Σ is a tunable “size” variable.
- **Clarified solids carryover:** 0.05–0.5 % of feed solids (settable)
- **Product recovery in supernatant:** 98–99.9 % (minor losses to cake/foam)
- **Lysis penalty:** add 0–10 % increase in soluble impurities if shear high
- **Moisture in solids discharge:** 70–85 % w/w (affects waste mass)

**Utilities & cleaning**

- Power: 5–25 kW per machine; scale ∝ flow^0.7 (settable)
- CIP/SIP: caustic and acid cycles—time loss + chemicals (parameters)
- Water flushes: 0.5–2 % of batch volume per cycle

**Cost hooks**

- **Purchase CAPEX:** $C = a \cdot \Sigma^{b}$ (b ≈ 0.6–0.75)
- **Install factor:** 1.5–2.5×
- **OPEX:** power + maintenance (2–4 % of CAPEX/yr) + CIP chemicals
- **Spares/consumables:** seals, nozzles (amortized per year)

**Constraints & flags**

- Max solids % (v/v) before choking; max flow per machine
- Shear-sensitive product flag triggers impurity penalty model
- If $Q$ demand > machine max: parallel trains (integer)

**Outputs to track**

- Turbidity after unit, protein recovery, dsDNA, HCP, conductivity, pH

------

## B) Depth filtration (polishing after centrifuge)

**Purpose:** Remove fines/colloids, reduce turbidity to <10–50 NTU; scalable by area, but consumable cost-heavy if used alone on raw yeast broth.

**Streams**

- In: partially clarified supernatant
- Out: filtrate (to UF/TFF or chromatography)
- Waste: spent modules + hold-up losses

**Key design variables**

- **Filter grade sequence:** e.g., 10 µm → 1 µm (or 5 µm → 0.5 µm)
- **Specific capacity (L/m²) at spec’d turbidity/viscosity**
- **Flux setpoint (LMH):** 50–200 LMH typical; 75–120 LMH baseline
- **Max ΔP (bar):** 1.5–2.4 bar; terminal at 1.0–1.5 bar
- **Adsorptive loss factor:** 0.3–2 % protein per pass (grade-dependent)

**Performance model**

- **Required area per stage:** $A = \dfrac{V_{batch}}{Capacity_{L/m^2}}$
  - Optionally cap by flux-time window: $A \ge \dfrac{Q}{Flux}$
- **Breakthrough/plugging:** staging rule—if turbidity > setpoint, add grade
- **Hold-up:** 0.3–1.0 L per 10″ module equivalent; product loss calc
- **Recovery:** 97–99.7 % per train (staged losses + hold-up)

**Utilities & cleaning**

- Single-use: water flush 1–3 L/m²; no CIP (or limited backflush variants)
- Reusable modules are rare for depth media; model as disposable

**Cost hooks**

- **Media cost:** $/m² per grade (project input)
- **Skids:** CAPEX scales with max A installed; low install factor
- **Changeout labor:** time per module; add to OPEX
- **Waste disposal:** $/kg of wet media

**Constraints & flags**

- If used **without** centrifuge and feed solids >~1–2 % v/v, capacity collapses—make model throw an infeasibility/warning and balloon cost.

------

## C) Tangential flow microfiltration (MF-TFF)

**Purpose:** Cell removal using membranes; better for low-solids feeds (mammalian). For yeast, practical **after** centrifuge or on low-solids scenarios.

**Streams**

- In: broth or pre-clarified supernatant
- Out1: permeate (clarified)
- Out2: retentate (cells/solids)

**Key design variables**

- **Pore rating:** 0.1–0.45 µm (set 0.2 µm baseline)
- **Flux (LMH):**
  - Unclarified yeast: 20–60 LMH (fouling-limited)
  - Post-centrifuge: 80–150 LMH
- **TMP (bar):** 0.5–1.5; **Crossflow velocity:** 1–3 m/s
- **Area:** sized from $A = \dfrac{Q}{Flux}$
- **Fouling model:** flux decay factor vs. processed volumes (V/A)

**Performance model**

- **Clarification efficiency:** >99.9 % cell removal at spec grade
- **Product passage:** assume full passage; add 0.5–2 % loss to adsorption
- **Shear penalty:** optional (usually low for secreted proteins)
- **Cleaning cycles:** NaOH 0.1–0.5 M; recover flux to 80–95 % of new

**Utilities & cleaning**

- CIP chemicals, water, time; pump power ∝ ∆P·Q/cη (set efficiency)

**Cost hooks**

- **Membrane cost ($/m²)** + lifetime (batches to replacement)
- **Skid CAPEX:** $C = a \cdot A^{b}$ (b ≈ 0.6–0.8)
- **OPEX:** electricity + chemicals + membrane amortization

**Constraints & flags**

- If feed solids > ~2–3 % v/v, require pre-centrifuge or area explodes; raise warning.
- Temperature limits for polymeric membranes.

------

## D) Continuous centrifuge (tubular/pusher or high-g nozzle variants)

**Purpose:** When extremely high solids loads or special particle PSDs demand it; less common than disc-stack for biotech liquids but include as an option.

**Design, performance, and cost hooks**

- Same Σ-based framework as disc-stack, but allow higher solids fractions and different power/maintenance scalars; add a **higher lysis/shear penalty** and more intense CIP.

------

# Decision matrix (use this to auto-select in scenarios)

| Criterion                  | Disc-stack     | Depth only             | MF-TFF (unclarified)     | MF-TFF (post-centrifuge)                 | Continuous centrifuge |
| -------------------------- | -------------- | ---------------------- | ------------------------ | ---------------------------------------- | --------------------- |
| Scale to 100–200 m³        | **Excellent**  | Poor (area/cost)       | Fair–Poor (area/fouling) | **Good**                                 | **Excellent**         |
| Capex                      | High           | Low–Med                | Med–High                 | Med                                      | High                  |
| Opex                       | Low–Med        | **High** (consumables) | Med–High (CIP, energy)   | Med                                      | Med                   |
| Robust to 5–12% v/v solids | **Yes**        | No                     | No                       | **Yes** (because solids already removed) | **Yes**               |
| Typical CMO availability   | **Ubiquitous** | Ubiquitous (as polish) | Selective                | **Common as polish**                     | Less common           |
| Product shear/lysis risk   | Low–Med        | Low                    | Low                      | Low                                      | Med–High              |
| Turbidity after step       | 50–200 NTU     | 5–50 NTU               | <5–20 NTU                | **<5–20 NTU**                            | 50–200 NTU            |

**Policy:**

- If solids ≥3 % v/v → choose disc-stack (or continuous) first.
- If turbidity spec <50 NTU → follow with depth filtration or MF-TFF polish.
- If membranes are strategic → place MF-TFF **after** centrifuge.

------

# Parameter defaults for *K. lactis* supernatant at 100 m³ (tune as you get plant/lab data)

**Disc-stack**

- Σ per machine: 6,000–12,000 m² (baseline 9,000)
- Carry-over: 0.2 % of feed solids
- Product recovery: 99.2 %
- Lysis penalty: +5 % soluble impurity if shear flag on
- Power: 15 kW per unit, 0.20 kWh/m³ processed
- Parallel trains allowed; max flow per machine computed from Σ

**Depth filter train**

- Grades: 10 µm → 1 µm
- Specific capacity (after centrifuge): 120 L/m² (grade 10) then 70 L/m² (grade 1)
- Flux cap: 100 LMH
- Terminal ∆P: 1.2 bar
- Adsorptive loss: 0.5 % per train
- Hold-up: 0.6 L per 10″ module equivalent

**MF-TFF (polish)**

- Pore: 0.2 µm
- Flux: 120 LMH
- TMP: 0.8 bar, CFV: 2.0 m/s
- Product adsorption loss: 0.5 %
- Cleanability factor: 0.9 (90 % flux recovery per full CIP)
- Membrane life: 30 batches (tune)

------

# BioSTEAM-oriented specification fields (so you can implement cleanly)

For each unit, expose the following attributes and methods:

**Design inputs (settable)**

- `feed_flow_m3_per_batch`, `feed_temp_C`, `density`, `viscosity_mPa_s`, `solids_vv`, `dp_um`, `turbidity_NTU`
- Unit-specific knobs (e.g., `sigma_m2`, `grades=[10,1]`, `membrane_area_m2`, `flux_LMH`, `TMP_bar`)
- Economic inputs: media costs ($/m²), membrane costs ($/m²), install factors, maintenance %, power price, water & chemical prices

**Design algorithm (returns .design_results)**

- Sizing decision (area, number of modules, number of centrifuges in parallel)
- Cycle times (process time, CIP time, changeout time)
- Utility loads (kWh, m³ water, kg NaOH/HNO3) per batch
- Consumables (m² of media, membrane replacement fraction)

**Performance (returns .performance_results)**

- Product recovery (%), solids removal (%), turbidity out (NTU)
- Impurity penalties (lysis-induced HCP/DNA factors)
- Losses from hold-up/adsorption (kg protein)

**Costs (returns .cost_results)**

- CAPEX (purchase + install)
- OPEX per batch (power, chemicals, water, labor, disposables, maintenance)
- Waste disposal costs (spent media/membranes, wet solids)

**Constraints & warnings**

- Feasibility checks (e.g., depth-only with high solids → “infeasible”)
- Scale-outs (ceil to integer trains)
- Pressure/flux limits exceeded → warnings and automatic derating

------

# How to wire selection logic in your scenario toggles

Expose a `ClarificationRoute` enum and a “smart select” helper:

1. If `solids_vv ≥ 3%` → choose `DiscStack` (or `ContinuousCentrifuge` if flagged).
2. If `post_turbidity_spec ≤ 50 NTU` → append `DepthPolish`.
3. If membranes required (user flag) → substitute `DepthPolish` with `MF_TFF_Polish`.
4. If user forces `DepthOnly` and `solids_vv > 2%` → mark “cost blowout” and compute with drastically reduced `Capacity_L/m²`.

------

# What you’ll learn fastest from the plant/lab (high-value calibration data)

- Σ vs. flow from vendor quotes (Alfa Laval / GEA / Flottweg) for your target yeast—drop those numbers into `sigma_m2`.
- Depth filter capacities (L/m²) on your real broth post-centrifuge at target turbidity.
- MF fouling curves: flux vs. V/A over time with your antifoam regime.
- Actual protein losses on filters/membranes (quick spiking tests pay for themselves).

------

# Bottom line for 100 m³ *K. lactis*

Start with **disc-stack** (Σ ≈ 9,000 m² per machine; scale-out as needed) → **two-stage depth** (10→1 µm) to knock turbidity down before UF/TFF. Keep MF-TFF as a **polish alternative** if you want reusability and tighter turbidity control, but don’t try to MF raw yeast at this scale unless your solids are unusually low.