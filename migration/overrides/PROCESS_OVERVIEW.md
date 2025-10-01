# DSP Front-End Defaults & Override Knobs

This note consolidates the baseline configuration and available overrides for the upstream and DSP steps that precede DSP03–DSP05. Use it as the at-a-glance map before you start enabling predrying and drying variants.

## Seed Train (USP01)
- **Baseline source:** `migration/baseline_defaults.yaml:seed`  
  - Working volume 3,500 L, DCW 60 g/L, OD600 ~150.  
  - Yeast extract 8.5 g/L (@ $12/kg) and peptone 12.5 g/L (@ $15/kg).  
- **Override files:**
  - `usp01_shake_flask.yaml` — single-stage shake flask expansion for pilot/demo runs; trims media mass, zero CIP/SIP time, lower labor.
  - `usp01_two_stage.yaml` — two-seed bioreactors mirroring the Excel baseline with explicit labor/media/CIP hooks.
  - `usp01_three_stage.yaml` — adds a 5 m³ third stage for ≥100 m³ production, increases media/labor and tracks Stage 3 volume.

## Production Fermentation (USP02)
- **Baseline:** `baseline_defaults.yaml:fermentation`  
  - 70,000 L batch, 4 g/L titer, 280 kg OPN, 7.8 t glucose feed plus optional glycerol/molasses entries.  
  - Cost hooks for antifoam, NH₃, pH base, O₂, etc.
- **Scenario overrides:**  
    - Glucose: `usp00_glucose_rich.yaml`, `usp00_glucose_defined.yaml`
    - Glycerol: `usp00_glycerol_rich.yaml`, `usp00_glycerol_defined.yaml`
    - Molasses: `usp00_molasses_rich.yaml`, `usp00_molasses_defined.yaml`
    - Lactose: `usp00_lactose_rich.yaml`, `usp00_lactose_defined.yaml`
    - Method toggles: `usp02_batch.yaml`, `usp02_fedbatch.yaml`, `usp02_continuous.yaml` encode Batch/FedBatch/Continuous cycle time, titers, and O₂ policies.

Each carbon-source YAML now bundles the matching USP01 seed plan (media loads, nutrient
costs) with the USP02 fermentation settings so parity runs don’t mix glucose seed media
with glycerol/molasses production batches. Each file carries scenario feed volumes, carbon
totals, media type, and yield proxy flags.

## Cell Removal (USP03)
- **Baseline auto-selection:** `baseline_defaults.yaml:cell_removal`
  - Feed: 70 m³ broths @ 8% v/v solids.  
  - Disc-stack specs (σ=9,000 m², 0.2 kWh/m³, 99.2% recovery).  
  - Depth filtration follow-up, MF-TFF polish (membrane cost and life).  
- **Override example:** `usp03_micro_only.yaml` forces `method: microfiltration`
  - Use this when Excel parity requires skipping the new chain.

## Concentration & Buffer Exchange (DSP01)
- **Baseline method:** `concentration.method = uf_df`  
  - UF stage: VRR 6× at 90 LMH, 98.5% recovery.  
  - DF stage: 3 DiaVolumes @ 100 LMH, 99% recovery, 45 $/m³ buffer.  
- **Alternative override files:**  
  - `dsp02_uf_only.yaml` – UF-only path.  
  - `dsp02_df_only.yaml` – DF-only cleanup.  
  - `dsp02_sptff.yaml` – single-pass TFF routing.  
  - `dsp02_ctff.yaml` – continuous TFF configuration.

## Capture (DSP02)
- **Baseline method:** `capture.method = aex`  
  - Feed: 72 g/L protein, 0.6 mg/L DNA, 55 mM conductivity.  
  - AEX specs: Q resin, 60 mg/mL base DBC, 25 cm bed, 0.9 utilization, pH 7 buffers (10 mM phosphate) with NaCl-driven elution, 2 columns, full buffer/fee schedule.  
  - Targets block: conductivity cutoff (400 mM) and chitosan ppm guard (100 ppm).
- **Chitosan path:** included in baseline defaults under `capture.chitosan`  
  - Capture yield 92%, elution yield 93%, PolyP elution (200 mM), recycle/bleed factors.  
  - When `capture.method` is overridden to `chitosan`, the new capture handoff publishes: pool volume/conductivity, polyP levels, DF/fines flags for DSP03.

## DSP03 Membrane Conditioning
- **Baseline:** `dsp03.method = auto` routes to SPTFF defaults (3 stages, CF≈4×).  
  - Config sections: `dsp03.uf`, `dsp03.df`, `dsp03.sptff`, `dsp03.ctff` hold flux/TMP/sieving parameters.
- **Route logic:**
  - PolyP present or `Needs_DF_Flag` → DF branch.
  - Otherwise defaults to SPTFF; cTFF available for steady campaigns.
- Overrides mirror baseline structure; drop a YAML with `dsp03: { method: df, df: {...} }` to force routes or tweak flux/TMP limits.  
  - Example files: `dsp03_uf_only.yaml`, `dsp03_df_polyP.yaml`, `dsp03_sptff_fast.yaml`, `dsp03_ctff_campaign.yaml`.

## DSP04 Polish & Sterile Filter
- **Baseline:** no polish stages enabled; always includes `SterileFilter_0p2um`.  
  - Config structure: `dsp04.stage_order` (list of stages), `dsp04.stages.<stage>` toggles, `dsp04.sterile_filter` holds flux/ΔP/adsorption settings.  
- **Stage options:** `aex_repeat`, `cex_negative`, `hic_flowthrough`, `mixedbed_iex`, `enzymatic_tidyup`; append sterile filter automatically.  
- **Overrides:** supply YAML such as `dsp04: { stage_order: ["cex_negative"], stages: { cex_negative: { enabled: true } } }` to enable polish before sterile filtration. Example files: `dsp04_cex_polish.yaml`, `dsp04_cex_aex_combo.yaml`, `dsp04_hic_guard.yaml`.

## DSP05 Final Form & Finish
- **Baseline:** `dsp05.method = SprayDry`; uses Excel spray dryer plan values but records method/cost metadata.  
  - Config structure: `dsp05` with common tolling/cost fields and nested sections `spraydry`, `lyophilize`, `liquid` for variant-specific knobs.  
- **Variants:** `SprayDry`, `Lyophilize`, `LiquidBulk`.  
- **Overrides:** drop a YAML such as `dsp05: { method: Lyophilize, lyophilize: { primary_dry_time_h: 14 } }` to switch method and adjust parameters.
  - Example files: `dsp05_lyophilize.yaml`, `dsp05_liquid_bulk.yaml`.

## Using Overrides
- Load overrides via `build_front_end_section(..., baseline_config=YOUR.yaml)` or pass `--baseline-config` to `migration.scripts.compare_front_end`.  
- YAML structure mirrors the baseline tree; any subkey you provide will update `plan.derived` or `plan.specs` before units are instantiated.

## Next Steps
- Extend this overview when you introduce DSP03/DSP04 polish choices.  
- Capture additional handoff fields (e.g., chromatography pooling rules, DF volumes) as new overrides become available.
