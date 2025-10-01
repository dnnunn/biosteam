# DSP04 — Polish & Sterile Finish (conservative defaults)

## Scope & mindset

- Tighten purity (DNA/HCP/chitosan/aggregates), square pH/cond with finish, then **0.2 µm sterile filtration** to the dryer.
- Client-borne consumables (resins, filters, buffers, labor, waste) are **always** charged; skid CAPEX is **flagged** (CDMO mode excludes) — same split you already use. 

------

## Variant 1 — **AEX_Repeat** (FT or Bind-Elute)

When to use

- **FT:** as a gentle mop for DNA/anionic junk after capture.
- **Bind-Elute:** only if analytics still show significant binders; expect extra loss/time. 

Conservative hydraulics & capacities

- **Lin_vel:** **250–300 cm/h** (keep ΔP ≤ **2 bar**)
- **Bed height:** **20 cm** default
- **FT impurity capacity (q_cap_imp):** **6–10 mg/mL** as a planning value (set low; measure later). 

Conservative recovery & removal

- **FT recovery:** **99.0–99.3 %** (use **99.2%** baseline)
- **Bind-Elute recovery:** **95–97 %** (don’t assume ≥98% unless pooled with data)
- **DNA reduction:** **~0.5–2.0 log** (FT) / **1–3 log** (bind-elute) depending on load/RT and your maps. 

Costs & BV

- Step BVs from your recipe (Equil/Wash/Elute/Strip/CIP/Re-equil); keep the conservative BV totals in your doc. 

------

## Variant 2 — **CEX Negative (FT)**

When to use

- **Default polish after Chitosan pH-mode:** OPN (anionic) flows through; **cationic residues (incl. chitosan)** bind. Also useful post-AEX if cationic HCPs linger. 

Conservative settings

- **pH:** **7.0**; **Cond:** **100 mM**
- **Lin_vel:** **250–300 cm/h** (ΔP ≤ **2 bar**)
- **FT impurity capacity:** **6–8 mg/mL** (use **8 mg/mL** only with data) 

Performance

- **Recovery:** **98.8–99.5 %** (use **99.0–99.2 %** baseline)
- **Chitosan removal:** assume **≥90 %** effectiveness when tuned; set your spec gate at **≤10 ppm** downstream. 

Economics

- FT mode → small beds & modest buffer; low time per cycle. 

------

## Variant 3 — **HIC Flow-Through (optional orthogonal)**

When to use

- If analytics show hydrophobes/aggregates after capture/polish. Otherwise skip. 

Conservative settings

- **Salt:** **0.5 M NaCl** (or similar), **Lin_vel ~250 cm/h**, **ΔP ≤ 1.5 bar**
- **FT impurity capacity:** **~6 mg/mL** planning value. 

Performance

- **Aggregate/hydrophobe reduction:** assume **~30–50 %** first-pass unless tuned.
- **Recovery:** **97–99 %** (use **98.5 %** baseline). 

Guardrail

- Don’t choose HIC unless feed is already salt-ready **or** you explicitly pre-condition (tiny DF/salt swap). You already defined the bypass logic to feed HIC directly from DSP02 when salt is adequate. 

------

## Variant 4 — **MixedBed IEX (CEX-FT → AEX-FT)**

When to use

- Tight spec without the overhead of full bind-elute; a **stacked mini-guard** with tiny beds and quick cycles. 

Conservative settings & performance

- **BV each:** **~2 BV**; plan **combined recovery ~99 %** (don’t promise more).
- Good broad cleanup, but still keep sterile filter afterwards. 

------

## Terminal — **SterileFilter_0p2 µm** (mandatory)

Settings

- **Flux:** **200–350 LMH** (use **300 LMH** only for very clean pools)
- **Capacity:** **1,500–2,000 L/m²** on clean protein (use **2,000 L/m²** only as upside)
- **Max ΔP:** **≤1.5 bar**
- **Adsorption:** **0.05 %/m²** for main filter; same for prefilter if used. 

Performance

- **Recovery:** **≥99.5 %** typical; keep **0.5–1.0 %** loss budget if area is large.
- Integrity test must pass; if DP is high or NTU up, **enable prefilter** or increase area. 

------

## Route-aware playbook (enforced selections)

- **After Chitosan pH-mode:** **CEX-Negative FT → Sterile** (default). If DNA still high, add **AEX-FT** after CEX. 
- **After Chitosan polyP-mode:** **DF (in DSP03) → (AEX-FT or CEX-FT)** → **Sterile**. Do **not** skip DF if polyP is present. 
- **After AEX capture:** often **Sterile only**. If tails persist, add **AEX-FT** or **CEX-FT** per impurity profile. If aggregates flagged, add **HIC-FT** before sterile. 

------

## Guardrails (make over-promising impossible)

- **PolyP present & AEX/CEX chosen:** **require DF upstream**; block selection otherwise. 
- **Chitosan_ppm > spec** post-DSP02:** force CEX-Negative before sterile (or MixedBed with a CEX-first order). 
- **HIC selected:** check salt window (min/max), pH range, and polyP limit; if not met, either bypass DSP03 with HIC-ready feed or pre-condition with a tiny DF in DSP04 only if volume is small (you already documented this choice). 
- **Sterile filter DP > cap at required Q:** increase area and/or enable prefilter; do not push DP. 

------

## Drop-in defaults for your classes

**AEX_Repeat (FT)**

- `lin_vel_cm_per_h=300`, `dp_max_bar=2`, `ft_cap_mg_imp_per_mL=8–10` (use 8 by default)
- `dna_log_reduction≈1.0–1.5`, `base_recovery_frac=0.992` 

**AEX_Repeat (Bind-Elute)**

- Use only when needed; `base_recovery_frac=0.96` (range 0.95–0.97); BV set from your recipe. 

**CEX_Negative (FT)**

- `pH=7.0`, `cond=100 mM`, `lin_vel=300`, `dp_max=2`, `ft_cap_mg_imp≈8`, `base_recovery=0.992`
- `chitosan_binding_eff_frac≈0.9` (for ppm spec calc). 

**HIC_FT**

- `salt=0.5 M`, `lin_vel=250`, `dp_max=1.5`, `ft_cap_mg_imp≈6`, `base_recovery=0.985` 

**SterileFilter_0p2**

- `flux_LMH=250` (default), `capacity_L_per_m2=1500`, `max_dp_bar=1.5`,
   `adsorption_loss_frac_per_m2=0.0005`, `prefilter_enable=FALSE` by default. 

**Economics (client-borne placeholders)**

- IEX resin fee $/L·cycle (FT: **$70–90**, bind-elute: **$90–150**), buffers $/m³ by step, sterile filter **$350/m²** (prefilter **$200/m²**), labor **6 h/batch @ $80/h**, waste **$220/t**. Keep skid CAPEX flagged. 

------

## Controller logic (summary)

- Build `method_chain` from analytics flags and targets; always append **SterileFilter_0p2**.
- Allow **DSP03 bypass** into HIC when the feed already meets salt/pH window; otherwise route through DSP03 or perform tiny in-unit preconditioning if volume is small and explicitly enabled (your doc’s bypass/precondition rules). 

------

## Why these defaults are conservative

- We assume **FT capacities in the single-digit mg/mL** range for impurities and **mid-90s recovery** for bind-elute polish — numbers you can beat with data, but not embarrass yourself with. 
- **Sterile filter** sizing uses **low-end capacity** and modest flux so DP stays sane; adsorption losses are counted explicitly per m². 
- The route-aware hard stops (polyP → DF; chitosan ppm → CEX-FT) prevent “paper wins” that don’t survive the lab. 