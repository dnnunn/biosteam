# 2025-10-02 — Front-End Parameter Snapshot

Consolidated view of the parameters currently feeding the front-end migration. Values come from `migration/module_defaults.yaml` (mirrors the workbook) and `migration/baseline_defaults.yaml` (baseline overrides lifted from the Excel mass trail). Units and notes follow the source files.

## Global Production Settings (`GLOBAL00`)

- **GLOBAL00c (workbook defaults, inactive)**
  - Annual campaigns: 5
  - Batches per campaign: 6
  - Annual production target: 10 000 kg purified product
  - Fermenter size: 100 m³
  - Fermentation time: 48 h, turnaround time: 24 h
  - Initial glucose: 20 g/L, feed glucose: 500 g/L (glycerol 600, lactose **200**, molasses 1 000)
  - Strain titer: **5 g/L** (whole-broth production target before cell removal)
  - Antifoam dosage: **0.001 fraction v/v** (0.1 % v/v)
- **GLOBAL00a (costs and physical properties)**
  - Glucose 0.75 $/kg, glycerol 1.20 $/kg, lactose 0.95 $/kg, molasses 0.25 $/kg
  - Yeast extract 12 $/kg, peptone 15 $/kg, antifoam 10 $/kg
  - Minor nutrients: 500 $/batch, QC testing 15 000 $/batch
  - Wet cell density 1.05 kg/L, sludge dry fraction 0.35

## Seed Train (`USP01` and overrides)

- **Workbook defaults (USP01a, inactive)**
  - Stage inoculation ratios: S0 1 mL, S1 0.03 v/v, S2 0.05 v/v, S3 0.05 v/v, production 0.05 v/v
  - Stage times: S0–S3 each 4 h; working fractions 0.5 / 0.7 / 0.8 / 0.85
  - DO setpoint 30 %, temperature 32 °C
- **Baseline overrides (`seed`)**
  - Working volume 3 500 L, DCW 60 g/L, OD600 target 150, wet-cell density 190 g/L
  - Yeast extract 8.5 g/L, peptone 12.5 g/L (costs 12 and 15 $/kg)

## Production Fermentation (`USP00`, `USP02`, overrides)

- **Workbook defaults**
  - Biomass yield on glucose 0.48 g/g (USP00a)
  - Media recipe: yeast extract 10 g/L, peptone 20 g/L (USP02a)
  - Aeration 1 vvm, agitation 2.5 kW/m³, OTR 100 mmol/L/h
- **Baseline overrides (`fermentation`)**
  - Working volume 70 000 L (70 m³)
  - Target broth titer **5.0 g/L** (whole fermenter prior to disc stack)
  - Clarified supernatant titer 6.176 g/L (post-disc-stack checkpoint for UF/DF sizing)
  - DCW 47.5 g/L derived from **OD₆₀₀ = 150** with 0.3167 g/L·OD⁻¹ conversion
  - Total glucose feed **10 573 kg** from OD-driven growth + maintenance (Yₓ/ₛ = 0.48, mₛ = 0.0297 g/gDCW/h, 3 % loss allowance); glycerol/molasses feeds 0 kg
  - Antifoam 70 L (10 $/unit), NH₃ 311.5 kg, caustic 311.5 kg (biomass-derived)
  - Blower air 0.6 vvm, power density 1.2 kW/m³, O₂ enrichment 5 %
  - Lactose feed concentration **200 g/L** (raised only as far as solubility allows without heating)
  - Broth density **1.05 kg/L** → 73.5 t total broth mass at harvest
  - Product model: **specific productivity** with qₚ = 2.75 × 10⁻³ g/(gDCW·h); growth-associated yield (0.0714 g/gDCW) retained for reference
  - Nitrogen requirement 0.1 g N/gDCW with 1.0 kg NH₄OH per kg N demand (ties base usage to biomass growth); current batch ⇒ ~311 kg NH₄OH

## Cell Removal / Clarification (`USP03`, `cell_removal` overrides)

- **Disc-stack stage**
  - σ area 9 000 m², recovery 0.985, solids carryover 0.002, wet-cake moisture 0.7, power 0.2 kWh/m³, single train
- **Depth filter polish**
  - Recovery 0.99, holdup loss 0.6 kg, specific capacity 120 / 70 L·m⁻², flux 90 LMH, ΔP 1.2 bar, media 75 $/m²
- **MF polish (SPTFF-like)**
  - Recovery 0.99, flux 90 LMH, membrane 350 $/m², life 30 batches
- **Feed body**
  - Volume 70 m³, density 1 040 kg/m³, solids 0.08 v/v

## UF / Diafiltration (`DSP01`, `concentration` overrides)

- **UF concentration stage**
  - Volume-reduction ratio 4×, recovery 0.985, flux 80 LMH, TMP 1.2 bar
  - Membrane area 150 m², cost 220 $/m², life 30 batches, fouling derate 0.9
- **Diafiltration stage**
  - Dia volumes 1.0, flux 90 LMH, recovery 0.995, sieving 0.007
  - Membrane area 150 m² (same cost/life as UF), buffer 45 $/m³
- **Other concentration options**
  - SPTFF: 3 stages at 1.7× each, flux 85 LMH, sieving 0.008, TMP 1.2 bar
  - cTFF: flux 80 LMH, bleed 0.1 m³/h, TMP 1.2 bar (baseline defaults)
- **Feed assumptions**
  - Volume 60 m³, density 1 025 kg/m³, target VRR 4, inline capture off

## Capture Chromatography (`DSP02`, `capture` overrides)

- Resin column: 25 cm bed, 300 cm/h velocity, packing factor 0.72, ΔP max 2 bar
- Resin cost 520 $/L, life 120 cycles, fee 25 $/L per cycle; two columns in service
- AEX stage recovery 94 %, target pool conductivity 450 mM
- Buffer sequence BV: 3 equilibration / 3 wash1 / 0 wash2 / 3 elute / 2 strip / 3 CIP / 3 re-equil
- CMO rates: blended labor 95 $/h, disposables 450 $/cycle, overhead 320 $/cycle, fees per m³ for each solution (220–260 $/m³)
- Chitosan pre-treatment defaults retained (capture route “aex”)
  - Chromatography plan now records simulated pool volumes/masses (no static overrides); buffer/resin costs flow directly from the capture model

## DSP03 Concentration / Buffer Exchange (`dsp03` overrides)

- Auto route with UF, DF, SPTFF, CTFF settings (not yet wired into the placeholder units)
  - UF: flux 90 LMH, sieving 0.01, TMP 1.5 bar
  - DF: 2 dia volumes, flux 100 LMH, sieving 0.005
  - SPTFF: 3 stages, flux 85 LMH, sieving 0.008
  - CTFF: flux 80 LMH, TMP 1.2 bar, bleed 0.1 m³/h

## DSP04 Polish & Sterile Finish (`dsp04` overrides)

- Stage order currently empty; enabled defaults: CEX-negative and AEX-repeat (others disabled)
- Sterile filter: flux 250 LMH, max ΔP 1.5 bar, adsorption loss 5e-4, prefilter disabled

## Predry TFF (`DSP03a`, `predrying` overrides)

- Derived from Excel baseline: throughput 1 225 L/h, product out 195.32 kg, output volume 1 627.7 L, membrane cost per cycle 12.6 $

## Spray Dryer (`DSP05a`, `spray_dryer` overrides)

- Capacity 1 500 kg/h, efficiency 0.65, recovery 0.985
- Solution density 1.05 kg/L, final solids 12 %
- Baseline product out 191.42 kg per batch

---

These values match the dump taken on 2025-10-02. Any update to defaults or overrides should be reflected back into this document for traceability.
