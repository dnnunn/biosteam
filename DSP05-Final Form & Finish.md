# DSP05 — Final Form & Finish (single input → single output)

## Scope

Takes the polished, sterile-filtered liquid from DSP04 and produces the final product stream. Keep it toggle-friendly but still one input/one output at the unit level.

### Variants (pick one)

- **SprayDry** (default for shelf-stable powder)
- **Lyophilize** (when heat is touchy or you want very low moisture)
- **LiquidBulk** (skip drying; concentrates to ship-strength)
- **ConcentrateThenDry** (small helper inside SprayDry if solids too low)

You can still model it as one BioSTEAM unit with a `method` switch; internally, SprayDry may run an optional pre-concentrate sub-step, but externally it’s one input and one output.

------

## Inputs from DSP04 (canonical)

- `feed_volume_m3`
- `feed_opn_conc_gL`
- `feed_pH`
- `feed_conductivity_mM`
- `feed_DNA_mgL` (trace)
- `feed_chitosan_ppm` (trace, usually 0)
- `bioburden_pass: bool` (sterile filter integrity flag)
- `ownership_mode: "CDMO"|"InHouse"`
- `include_capex: bool` *(ignored if CDMO)*

------

## Outputs (to packaging/shipping)

- `product_form: "powder"|"liquid"`
- `product_mass_kg`
- `product_volume_m3` *(liquid path)*
- `protein_purity_wt_pct` *(optional analytic placeholder)*
- `moisture_wt_pct` *(powder)* or `protein_gL` *(liquid)*
- `bulk_density_kg_m3` *(powder; for logistics)*
- `step_recovery_frac`
- `cycle_time_h`
- `client_cost_usd`
- `capex_flagged_usd`
- `warnings: [ ... ]`

------

## Variant specs (BioSTEAM-ready, no code)

### 1) SprayDry (default)

**Goal:** Convert liquid to powder at target moisture.

**Key knobs**

- `target_moisture_wt_pct = 3.0` (typical 2–5%)
- `min_feed_solids_wt_pct_for_spray = 5.0` (pre-conc if below)
- `max_inlet_temp_C = 190` (adjust to stability)
- `outlet_temp_C = 80`
- `dryer_yield_frac = 0.98–0.995` (cyclone + fines return losses)
- `bulk_density_kg_m3 = 250–500` (set/fit)
- **Pre-concentrate (internal):** `enable_if_needed: True`, `target_solids_wt_pct = 10–20%`, modeled as a tiny evaporator (client buffer/steam fee)

**Performance**

- **Powder mass:** `m_powder ≈ m_dry_solids / (1 - moisture)`
- **Recovery:** `dryer_yield_frac` × (pre-conc recovery if used)

**Costs (client-borne)**

- **Tolling fee** per m³ of feed or per kg of powder *(CDMO)*
- **Utilities** pass-through (steam, power, chilled water) as a single line item or detailed if you want
- **Consumables** (bags, liners, N₂ for inerting)
- **Labor** hours
- **Waste** (fines/cyclone losses, scrubber blowdown)

**CAPEX flagged (InHouse only)**

- Dryer + cyclones + baghouse + CIP skid (install factor, depreciation)

**Warnings**

- If `bioburden_pass=False` → block (sterile filtration required upstream)
- If feed solids < `min_feed_solids_wt_pct_for_spray` and pre-conc disabled → warn “thin feed; enable pre-conc or expect ↑energy/↓capacity”

------

### 2) Lyophilize

**Key knobs**

- `target_moisture_wt_pct = 1.0`
- `fill_depth_mm` (shelf loading), `chamber_area_m2`
- `primary_dry_time_h`, `secondary_dry_time_h`
- `lyo_yield_frac = 0.98–0.995`

**Costs**

- Cycle-time driven tolling (per tray-m²·h or per kg product)
- Utilities (vacuum/power) and labor; disposables (vials/trays, stoppers) if used

**When to pick**

- Heat-sensitive specs or ultra-low moisture; usually more expensive than spray dry.

------

### 3) LiquidBulk

**Key knobs**

- `target_conc_gL` or `target_solids_wt_pct`
- `UF/SPTFF_precon enable: True|False` *(internal helper like DSP03 but scoped here)*
- `hold_temp_C`, `preservative_flag` *(if allowed)*

**Output**

- Liquid volume and concentration ready for tanker/IBC

------

## Minimal equations (you’ll wire these)

**Solids in feed**
 `m_solids_in = feed_volume_m3 * 1000 * (solids_wt_pct_in/100)`

**If SprayDry pre-conc enabled**

- Raise from `solids_in` to `target_solids`; evaporation loss is just water
- Add small recovery penalty (e.g., 0.2–0.5%)

**Powder mass**
 `m_powder = (m_solids_after_losses) / (1 - target_moisture)`

**Protein recovery**
 `Y = preconc_recovery * dryer_yield_frac` (or lyophilizer yield)

**Cycle time**

- SprayDry: `t ≈ (feed_volume / nominal_throughput) + CIP_time`
- Lyophilize: `t = primary + secondary + load/unload`

**Costs**
 Client costs only (always included):
 `toll_fee + utilities + consumables + labor + waste`
 Flagged CAPEX (in-house only): `dryer_capex * install_factor → depreciation + maintenance`

------

## Attribute list (one class with method switch)

```
DSP05_Finalize
```

- `method: "SprayDry"|"Lyophilize"|"LiquidBulk" = "SprayDry"`
- **Common costs (client)**
  - `toll_fee_usd_per_m3_feed = 120.0` *(or per kg powder: set alt field)*
  - `utilities_usd_per_batch = 800.0`
  - `consumables_usd_per_batch = 300.0`
  - `labor_h_per_batch = 6.0`, `labor_rate_usd_per_h = 80.0`
  - `waste_fee_usd_per_tonne = 220.0`
- **CAPEX flagged (in-house only)**
  - `dryer_capex_usd = 0.0`, `install_factor = 1.8`, `depr_years = 10`, `annual_maint_frac = 0.03`
- **SprayDry params**
  - `target_moisture_wt_pct = 3.0`
  - `min_feed_solids_wt_pct_for_spray = 5.0`
  - `precon_enable = True`
  - `precon_target_solids_wt_pct = 12.0`
  - `dryer_yield_frac = 0.99`
  - `bulk_density_kg_m3 = 350.0`
  - `max_inlet_temp_C = 190`, `outlet_temp_C = 80`
- **Lyophilize params**
  - `target_moisture_wt_pct_lyo = 1.0`
  - `primary_dry_time_h = 12.0`, `secondary_dry_time_h = 6.0`
  - `lyo_yield_frac = 0.99`
- **LiquidBulk params**
  - `target_conc_gL = 100.0`
  - `hold_temp_C = 4.0`
  - `use_internal_precon = False`

**Outputs (as above)**

**Validators**

- `bioburden_pass must be True`
- `target_moisture` feasible (e.g., SprayDry <1.5% often unrealistic without special gear)
- `precon_enable or feed_solids ≥ min_feed_solids` else warning

------

## YAML snippet (example)

```
ownership_mode: CDMO
include_capex: false

dsp05:
  method: SprayDry     # SprayDry | Lyophilize | LiquidBulk
  spraydry:
    target_moisture_wt_pct: 3.0
    min_feed_solids_wt_pct_for_spray: 5.0
    precon_enable: true
    precon_target_solids_wt_pct: 12.0
    dryer_yield_frac: 0.99
    bulk_density_kg_m3: 350
    toll_fee_usd_per_m3_feed: 120
    utilities_usd_per_batch: 800
    consumables_usd_per_batch: 300
    labor_h_per_batch: 6
    labor_rate_usd_per_h: 80
    waste_fee_usd_per_tonne: 220
```

------

## How this fits the pipeline

`DSP02 (AEX or Chitosan)` → `DSP03 (as needed)` → `DSP04 polish + sterile` → **`DSP05_Finalize (this unit)`** → Packaging/ship.

You get one clean handoff in, one clean product stream out—no branching visible externally. Later, when you add QC, you can insert a passive “QC gate” that reads the DSP05 output and sets release flags without changing material flow.

When you’re wiring this with Codex, give a shout if you want a tiny “throughput model” for spray drying (kg water evaporated per hour vs inlet/outlet temps and heat duty). It’s easy to add, but this spec will run fine without it.

##### You said:

might as well add 

###### ChatGPT said:

Perfect—let’s bolt on a **throughput/energy model** for SprayDry, so you can track **evaporation duty, throughput capacity, and energy costs**. This makes DSP05 not just a black-box toll but a predictive unit.

------

# SprayDry Throughput & Energy Model

## Additional Inputs

- `dryer_nominal_capacity_kgH2O_h: float`
   (how many kg of water evaporated per hour; depends on dryer size. Pilot ≈ 50–200, commercial ≈ 1000–5000+)
- `feed_inlet_temp_C: float` (preheated air), default 190
- `exhaust_temp_C: float` (after drying), default 80
- `air_cp_kJ_kgC: float = 1.0` (air specific heat; rough)
- `air_flow_kg_h: float` (optional; otherwise back-calc from duty)
- `latent_heat_H2O_kJ_kg: float = 2250` (at ~100 °C; adjust if using lower outlet T)
- `thermal_efficiency: float = 0.65–0.80` (fraction of supplied energy actually drives evaporation)
- `steam_cost_usd_per_tonne: float = 25.0` (or `energy_cost_usd_per_kWh`)

## Calculations

**1. Water to evaporate**
$$
m_{H2O, evap} = (V_{feed} \cdot \rho_{feed}) \cdot (w_{H2O,in} - w_{H2O,out})
$$
Where $w$ = mass fraction water.

- Input solids fraction = feed solids (g/L protein + other solubles) / (density).
- Target solids = $1 - \text{target moisture}$.
   Simplify:

$$
m_{H2O, evap} \approx m_{feed,total} - m_{powder,dry} - m_{water,residual}
$$

**2. Time to dry**

t_{dry,h} = \frac{m_{H2O, evap}}{\text{dryer_nominal_capacity_kgH2O_h}}

Add `CIP_time_h` for total cycle.

**3. Energy demand**
$$
Q_{req,kJ} = \frac{m_{H2O, evap} \cdot \Delta H_{vap}}{\eta}
$$

- Convert to kWh: $Q_{req}/3600$.
- Convert to steam tonnes: $Q_{req}/(2250 \cdot 1000)$.

**4. Energy cost**
$$
\text{Energy\_Cost} = Q_{req,kWh} \cdot \text{energy\_cost\_usd\_per\_kWh}
$$
or steam equivalent.

**5. Throughput check**
 If `t_dry` > target batch window, warn “Dryer undersized; parallel trains or larger dryer required.”

------

## Extra Outputs

- `water_evaporated_kg`
- `drying_time_h`
- `energy_demand_kWh`
- `energy_cost_usd`
- `dryer_utilization_frac` = actual load / nominal capacity
- `warnings` (undersized, efficiency < target, energy cost spike)

------

# Update Attribute List (`DSP05_Finalize.SprayDry`)

Add to earlier list:

- `dryer_nominal_capacity_kgH2O_h = 2000.0`
- `feed_inlet_temp_C = 190`
- `exhaust_temp_C = 80`
- `latent_heat_H2O_kJ_kg = 2250`
- `thermal_efficiency = 0.70`
- `energy_cost_usd_per_kWh = 0.10`
- `cip_time_h = 2.0`

Outputs:

- `water_evaporated_kg`
- `drying_time_h`
- `energy_demand_kWh`
- `energy_cost_usd`
- `dryer_utilization_frac`

------

# YAML Snippet (extended)

```
dsp05:
  method: SprayDry
  spraydry:
    target_moisture_wt_pct: 3.0
    precon_enable: true
    precon_target_solids_wt_pct: 12.0
    dryer_yield_frac: 0.99
    bulk_density_kg_m3: 350

    # Throughput/energy
    dryer_nominal_capacity_kgH2O_h: 2000
    feed_inlet_temp_C: 190
    exhaust_temp_C: 80
    latent_heat_H2O_kJ_kg: 2250
    thermal_efficiency: 0.70
    energy_cost_usd_per_kWh: 0.10
    cip_time_h: 2.0
```

------

# Integration Notes

- In CDMO mode, you can either:
   (i) let energy roll up as a **pass-through utility cost** if CDMO bills separately,
   or (ii) keep a **flat tolling fee** and only report energy for engineering insight.
- In InHouse mode, energy stays in OPEX, and dryer CAPEX appears flagged.
- If `water_evaporated_kg / dryer_nominal_capacity > 1.0` → highlight dryer undersized.

------

This way, DSP05 isn’t just a “black box toll” but a predictive dryer model: you can scale throughput, test dryer sizes, and see energy tradeoffs.

Would you like me to also sketch a **lyophilizer throughput/energy model** (shelf load, chamber area, sublimation rate) for parity with spray drying?

##### You said:

sure, why not

###### ChatGPT said:

Awesome—here’s a compact, engineering-ready **Lyophilizer throughput & energy model** you can drop into `DSP05_Finalize` alongside SprayDry. Same one-in/one-out contract, CDMO-friendly cost split, and realistic sizing/throughput math.

# Lyophilize: model spec (add as `method: Lyophilize`)

## Inputs (add to `DSP05_Finalize`)

- `batch_volume_m3` *(from DSP04 handoff; read-only)*
- `feed_opn_conc_gL`
- `feed_solids_wt_pct` *(if you track non-protein solids; else compute from conc)*
- `bioburden_pass: bool` *(must be True)*

### Equipment & loading

- `tray_fill_depth_mm: 8.0`  *(liquid height in trays)*
- `tray_fill_fraction: 0.90`  *(usable area due to edges/meniscus)*
- `shelf_area_m2: 30.0`  *(total shelves in chamber)*
- `max_chambers_parallel: 1`  *(scale-out option)*
- `vial_mode: false`  *(if true, use vial packing instead of trays; see note)*

### Cycle recipe (time/temperature/pressure)

- `freezing_time_h: 2.0`
- `primary_dry_time_h: 12.0`
- `secondary_dry_time_h: 6.0`
- `loading_unloading_time_h: 2.0`
- `target_moisture_wt_pct_lyo: 1.0`

*(Optional physics-driven alternative, below, can replace fixed times.)*

### Heat/mass transfer (for physics mode)

- `Kv_W_m2K: 12.0`  *(overall vapo-front heat transfer through dried layer)*
- `Rp_Pa_s_m: 500.0`  *(product resistance to mass transfer; affects sublimation)*
- `shelf_temp_C_primary: -20.0`
- `shelf_temp_C_secondary: +25.0`
- `chamber_pressure_mTorr: 150.0`
- `latent_heat_ice_kJ_kg: 2830.0`
- `overall_thermal_efficiency: 0.55`  *(wall/shelf losses, compressor COP)*

### Utilities & costs (client-borne)

- `vacuum_power_kW: 12.0`  *(average during primary)*
- `refrigeration_power_kW: 18.0`  *(average during primary)*
- `heating_power_kW: 10.0`  *(secondary)*
- `energy_cost_usd_per_kWh: 0.12`
- `disposables_usd_per_batch: 250.0`  *(trays/liners/gaskets)*
- `labor_h_per_batch: 10.0`
- `labor_rate_usd_per_h: 80.0`
- `waste_fee_usd_per_tonne: 220.0`

### CAPEX (flagged; in-house only)

- `lyo_capex_usd: 0.0`
- `install_factor: 1.8`
- `depr_years: 10`
- `annual_maint_frac: 0.03`

------

## Core calculations

### 1) Loadable volume on shelves

$$
V_{\text{max,load}} = \text{shelf\_area}\cdot \text{tray\_fill\_fraction}\cdot \frac{\text{fill\_depth\_mm}}{1000}
\;\;[\text{m}^3]
$$

If `batch_volume_m3 > max_chambers_parallel * V_max,load` → **scale-out** (more chambers or multiple cycles). Compute `n_cycles = ceil(batch_volume / (V_max,load * max_chambers_parallel))`.

### 2) Ice mass to sublimate

Let $w_{\text{water,in}}$ be water mass fraction in feed (1 − solids). Residual moisture target $w_{\text{res}} = \text{target\_moisture}$.
$$
m_{\text{ice}} \approx m_{\text{feed}} \cdot w_{\text{water,in}} - m_{\text{dry\_solids}}\cdot \frac{w_{\text{res}}}{1-w_{\text{res}}}
$$

### 3) Throughput / time modes

- **Timed recipe (simple):**
   `t_cycle_h = freezing + primary + secondary + loading_unloading`

- **Physics mode (predictive):**
   Primary time from average sublimation rate:
  $$
  \dot{m}_{\text{sub}} \approx \frac{Q_{\text{to ice}}}{\Delta H_{\text{sub}}}
  \quad\text{with}\quad
  Q_{\text{to ice}} \approx K_v A_\text{load} (T_\text{shelf} - T_\text{product})
  $$
  Use a practical average $\dot{m}_{\text{sub,avg}}$ (kg/h) fitted to Kv/Rp; then
  $$
  t_{\text{primary}} = \frac{m_{\text{ice}}}{\dot{m}_{\text{sub,avg}}}
  $$
  Secondary time as setpoint (or rule of thumb: 30–50% of primary for low moistures).

### 4) Energy demand & cost

**Primary (vacuum + refrigeration to remove sublimation heat):**
$$
Q_{\text{primary,th}} \approx \frac{m_{\text{ice}}\cdot \Delta H_{\text{sub}}}{\eta_{\text{thermal}}}
$$
Convert to kWh and add electrical loads:
$$
E_{\text{elec}} \approx (P_{\text{vac}}+P_{\text{ref}})\cdot t_{\text{primary}}
$$
**Secondary:**
$$
E_{\text{sec}} \approx P_{\text{heat}}\cdot t_{\text{secondary}}
$$
**Total energy cost** = $(E_{\text{elec}}+E_{\text{sec}})\cdot \text{energy\_cost}$.

### 5) Recovery & moisture

- `step_recovery_frac = lyo_yield_frac` (adsorption/handling losses, typically 0.985–0.995)
- Output moisture = `target_moisture_wt_pct_lyo` (assumed met by cycle recipe)

------

## Outputs

- `n_cycles`
- `load_per_cycle_m3`
- `ice_mass_kg`
- `t_primary_h`, `t_secondary_h`, `t_freeze_h`, `t_loadunload_h`, `t_cycle_h`
- `energy_kWh_primary`, `energy_kWh_secondary`, `energy_cost_usd`
- `product_mass_kg` (dry solids / (1 − moisture))
- `step_recovery_frac`
- `client_cost_usd` (labor + disposables + energy + waste)
- `capex_flagged_usd` (if InHouse)
- `warnings: [undersized loading, excessive cycle time, bioburden fail]`

------

## Warnings & guards

- If `bioburden_pass == False` → **block** (“Sterile filtration required upstream.”)
- If `load_per_cycle_m3 < batch_volume_m3` and `max_chambers_parallel==1` → warn “Multiple cycles needed; throughput reduced.”
- If `t_cycle_h > cycle_time_cap` *(add if you have takt targets)* → flag capacity gap.
- If `Kv` or `Rp` lead to unreasonably low sublimation rate (e.g., primary > 36 h) → suggest increasing shelf temp / lowering fill depth.

------

## YAML example (Lyophilize)

```
dsp05:
  method: Lyophilize

  lyophilize:
    # Loading
    tray_fill_depth_mm: 8.0
    tray_fill_fraction: 0.9
    shelf_area_m2: 30
    max_chambers_parallel: 1
    vial_mode: false   # set true if you later model vial packing

    # Cycle recipe (simple mode)
    freezing_time_h: 2.0
    primary_dry_time_h: 12.0
    secondary_dry_time_h: 6.0
    loading_unloading_time_h: 2.0
    target_moisture_wt_pct_lyo: 1.0

    # Physics mode (optional – if provided, override primary time)
    Kv_W_m2K: 12.0
    Rp_Pa_s_m: 500.0
    shelf_temp_C_primary: -20
    shelf_temp_C_secondary: 25
    chamber_pressure_mTorr: 150
    latent_heat_ice_kJ_kg: 2830
    overall_thermal_efficiency: 0.55

    # Utilities & costs
    vacuum_power_kW: 12
    refrigeration_power_kW: 18
    heating_power_kW: 10
    energy_cost_usd_per_kWh: 0.12
    disposables_usd_per_batch: 250
    labor_h_per_batch: 10
    labor_rate_usd_per_h: 80
    waste_fee_usd_per_tonne: 220

  # CAPEX (flagged – counted only if InHouse)
  capex:
    lyo_capex_usd: 0
    install_factor: 1.8
    depr_years: 10
    annual_maint_frac: 0.03
```