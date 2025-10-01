# BioSTEAM Migration Next Steps

## Short-Term Build Targets
- Excel parity + baseline toggle complete. Two parallel tracks now:
  - **Carbon-source parity prep**: finish calibrating the eight USP00 carbon-source overrides and lock their Excel checkpoints before we start swapping unit models.
  - **Cell-removal migration**: keep building the interchangeable BioSTEAM unit stack for USP03 (see tasks below).
- **CMO/TEA scaffolding**: first-pass toll model now lives in ``migration/cmo.py`` with the conservative profile in ``migration/cmo_profiles/default.yaml``. Front-end totals combine material costs with fermenter/DSP/spray dryer day-rates and the baseline labor/QA/doc fees. Downstream cycle time now comes from the plan inputs (depth-filter flux, UF/DF diavolumes, predry TFF throughput, spray evaporation duty). Next iterations should (a) flesh out chromatography/sterile-filter timing, (b) wire alternative CMO profiles, and (c) surface campaign-level levers (setup, reservation, escalators) in the CLI.
- **Fermentation media overrides**: defined-media YAMLs now carry a ``media`` block (salts + PTM1, optional CSL). ``front_end`` computes the per-batch base-media cost from the override, so TEA picks up the salts/trace spend automatically when switching between rich vs minimal recipes. Carbon feeds remain separate.
- Immediate tasks for carbon-source parity:
  1. Capture the Excel mass/cost checkpoints for each carbon-source scenario (glucose/glycerol/lactose/molasses; rich vs. defined) into a reference table.
  2. Update each ``usp00_*`` override so ``product_out_kg``, feed totals, and utility hooks match the captured Excel values (close the ±5% gap seen in glycerol).
  3. Annotate the matching Excel tabs/cells in ``USP02-Production Fermentation.md`` for future auditability.
  4. Extend ``migration/scripts/compare_front_end`` (or add a helper) to batch-run the override list and emit a concise delta table per scenario.
  5. Note: Excel currently exposes only the rich-media recipes; revisit the alternative (defined) media cases later and anchor them to BioSTEAM-native mass balances rather than spreadsheet parity.
  6. For glycerol, lactose, and molasses variants, plan a first-principles recalibration (mass balance + cost hooks) once BioSTEAM baselines are stable—treat current numbers as placeholders.
- Immediate tasks for cell-removal module (unchanged focus):
  1. Create BioSTEAM classes for disc-stack centrifuge, depth filtration, MF-TFF (pre/post-centrifuge), and continuous centrifuge using specs in ``Cell Removal Specs.md``.
  2. Add a ``cell_removal`` section to ``baseline_defaults.yaml`` capturing feed properties, method selection, and per-unit parameters (Σ area, flux, membrane cost, etc.).
  3. Extend ``build_front_end_section`` to route the fermentation effluent through the selected method(s); keep Excel mode using the historical microfiltration path until new units are toggled on.
  4. Surface stream/cost metrics in ``compare_front_end.py`` so Excel vs baseline differences are obvious (e.g., clarified supernatant, wet cell cake, depth filter losses).
- Optional (if time permits): implement an auto-selection heuristic based on scale and solids (disc stack + depth as default for ≥100 m³) while keeping manual overrides in the config.

## Validation Workflow
- Generate a comparison report that juxtaposes BioSTEAM results with Excel KPIs (cost per kg, batch cost, annual production cost) targeting ±5–10% deviation.
- Extend the report to break out chromatography resin, buffer, and CMO cost contributors using the same grouping found in ``Final Costs``.

## Future Enhancements
- Auto-selection logic for cell removal (use scale + solids to recommend disc stack vs MF-TFF vs alternate centrifuge).
- Campaign-based economic toggles (e.g., PROJ02 sensitivity) after baseline validation to explore alternative CMO pricing structures.
- Install missing runtime dependencies (e.g., ``numba``) so ``biosteam`` imports succeed; current sandbox blocks network installs, so resolve this manually on the host environment before attaching full unit builders.

## Provenance & CMO Notes
- **USP01 Seed Train** – Baseline numbers (3.5 m³ working volume, 60 g/L DCW, 553 kg YE, 1 106 kg peptone) trace back to *Biosteam BD Module Specs/USP01-Seed Fermentation Followup.md*. Keep antifoam/foam caveats in mind; vendor warns that high antifoam can derate downstream depth-filter capacity by ~20–30%.
- **USP02 Production Fermentation** – Conservative 70 m³, 6.2 g/L broth titer, and current utility usage per *…/USP02-Production Fermentation Followup.md*. Carbon-source switches remain at zero until BioSTEAM-specific regressions are complete. CMO fee model: daily fermenter charge with adders for oxygen enrichment and extended turnaround; capture this when we build the TEA hooks.
- **USP03 Cell Removal** – Disc-stack/depth/MF specs now reflect *…/USP03-Cell Separation Followup.md* (97–99% recovery targets, 30% cake dryness, depth filter hold-up 0.6 kg, MF flux 90 LMH). Overall yield guardrail: 96–98.5% across the clarification train.
- **DSP01 Concentration / Buffer Exchange** – UF/DF/SPTFF defaults follow *…/DSP01-Concentration & Buffer Exchange Followup.md*: UF VRR capped at 4× with flux 80 LMH and 98.5% recovery; DF trimmed to ≤1 DV (flux 90 LMH, 99.5% recovery, sieving ≈0.007); SPTFF staged for ~4× CF at 80 LMH with ≈99% yield; cTFF flux 75 LMH and uptime ≈94%. Use these baselines until plant data justify higher flux or deeper DF.
- **DSP02 AEX Chromatography** – Baseline parameters now match *…/DSP02-AEX Chromatography Followup.md*: ΔP cap 2 bar, bed height 25 cm, velocity 300 cm/h, DBC derated with −8e−4 per mM conductivity slope and 1e−4 L/mg DNA coefficient, BV recipe 3/3/0/3/2/3/3, overall step recovery set to 94% with wash/strip/hold-up caveats noted. CDMO cost split (buffers, resin usage, labor/disposables) stays client-borne; column/skid CAPEX remains flagged for in-house scenarios only.
- **DSP03 Post-capture concentration** – Code warns when UF VRR > 6×, DF ND > 2, or SPTFF CF > 4× per *…/DSP03-Concentration & Buffer Exchange Followup.md*. Baseline defaults reuse the conservative flux/recovery numbers (UF 80 LMH, DF 90 LMH, SPTFF staged ~4×, cTFF uptime 0.94). Future work: add viscosity/TMP estimation so we can proactively derate area or flag overspec’d runs.
- **DSP04 Polish & Sterile Finish** – Baseline enables the route-aware stages from *…/DSP04-Polish & Sterile Finish Followup.md*: CEX-negative (default after chitosan pH-mode) and AEX-repeat (DNA cleanup) now on by default; sterile filter flux dropped to 250 LMH with adsorption loss 0.0005. CDMO guidance: charge prefilters/sterile membranes, labor, buffers; keep skid CAPEX flagged; enforce DF upstream when polyP is present or chitosan ppm exceeds spec.
- **DSP05 Final Form & Finish** – Sprayer defaults follow *…/DSP05-Final Form & Finish Followup.md*: dryer capacity 1.5 t H₂O/h, thermal efficiency 0.65, recovery 98.5%, precon enabled to reach 12 wt% solids with a 0.3% loss. Lyophilization and liquid bulk options are still stubs; add the conservative cycle/throughput/yield parameters when those routes are implemented. CAPEX remains flagged for CDMO mode.
- Each follow-up file also outlines how CMO contracts shape pass-through costs (nutrients, membranes) versus fixed-day or volume-based fees—use those notes when we formalize the CMO/TEA layer after the baseline migration.

## Implementation Notes
- ``migration.module_registry.ModuleRegistry`` and the data builders are in place—extend them as new workbook modules/options appear.
- ``SeedTrainBioreactor`` now wraps the NREL batch model; use a similar pattern when upgrading fermentation and downstream stages so plan data flows straight into real BioSTEAM units.
- ``ExcelModuleDefaults`` merges module defaults with option rows and retains source-row metadata; lean on it to chase Excel discrepancies without re-reading the sheet manually.
- ``migration/scripts/compare_front_end.py`` is the regression harness—keep it aligned with whatever metrics each stage exposes so deltas surface immediately.
