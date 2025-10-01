# Media & Feeds — Minimal Defined (no lactose)

**Base: BSM-KLi (fully defined, inorganic N)**

- **Salts per L (in-vessel sterilized):** H₃PO₄ 85% 26.7 mL; K₂SO₄ 18.2 g; MgSO₄·7H₂O 14.9 g; CaSO₄ 0.93 g; KOH 4.13 g; water to 1 L.
- **Trace metals:** PTM1 stock (filter-sterilized) dosed **4.0–4.35 mL/L**.
  - PTM1 (make 1 L): CuSO₄·5H₂O 6.0 g; NaI 0.08 g; MnSO₄·H₂O 3.0 g; Na₂MoO₄·2H₂O 0.2 g; H₃BO₃ 0.02 g; CoCl₂ 0.5 g; ZnCl₂ 20.0 g; FeSO₄·7H₂O 65.0 g; **Biotin 0.2 g**; H₂SO₄ (conc.) 5 mL; water to 1 L.
- **Nitrogen/pH control:** use 25–30% NH₄OH as pH base; capture NH₄⁺ uptake in N balance. (Toggle to urea or ammonium sulfate if desired.)
- **Carbon source (choose one):** Glucose or Glycerol (see YAML).

**Complex cost-down toggle (optional): BSM + CSL**

- Add **CSL 10–30 g/L** (typical screens 10/20/30/40 g/L).
- Tradeoffs: cheaper N/vitamins, higher lot variability; add mild DSP penalty factor.

**Cost placeholders (no carbon):** $0.02–0.05 per L for salts+PTM1. Use procurement to override.

**YAML (drop-in)**

seed01:

  media:

​    base: BSM_KLi

​    ptm1_mL_per_L: 4.2

​    nitrogen:

​      mode: NH4OH

​      nh4oh_wt_pct: 28

​    carbon:

​      source: Glycerol   # Glucose|Glycerol

​      batch_gL: 40

​    csl:

​      enable: false

​      g_per_L: 20

​    costs:

​      salts_usd_per_m3: 30

​      ptm1_usd_per_m3: 5

​      carbon_usd_per_kg:

​        Glucose: 0.75

​        Glycerol: 1.20

**Validators**

- PTM1 dose 3.5–5.0 mL/L; warn outside.
- Biotin present (from PTM1) else warn.
- CSL enabled → flag “complex” route & DSP penalty.









Nitrogen & pH control via NH₄OH**

- Biomass N ≈ **0.10 g N / g DCW**.
- NH₃ (g) = 1.214 × gN.
- 28% NH₄OH (kg) = NH₃ / 0.28; Volume ≈ kg / **0.90 kg·L⁻¹**.
- 