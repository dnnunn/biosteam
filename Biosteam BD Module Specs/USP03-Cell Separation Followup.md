# What the unit ops really deliver (conservative, wire these into BioSTEAM)

## Disc-stack centrifuge (primary cell removal)

- **What it achieves:** robust cell removal at high g with centrate turbidity typically tens–hundreds NTU depending on inlet solids and Σ; it’s the standard primary step at scale. [Alfa Laval+1](https://www.alfalaval.com/products/separation/centrifugal-separators/separators/innovations/separator-innovator/how-separation-works/how-a-disc-stack-centrifuge-works/?utm_source=chatgpt.com)
- **Protein step recovery (secreted):** **97–99%** (baseline 98.5%). Losses reflect **entrained supernatant in the wet sludge** and minor foam/adsorption; not “cells stealing protein.” (CMO plants routinely operate in this band.)
- **Solids removal:** **>99%** of intact yeast when sized correctly (Σ check).
- **Underflow dryness (to size entrainment):** assume **25–35% w/w dry** (i.e., **65–75% moisture**). Use your DCW to compute sludge volume; the “mother-liquor” fraction is the dominant loss term. (Keep a guardrail that disc-stack clears low-% solids feeds; decanters take the high-% solids jobs.) [Alfa Laval+1](https://www.alfalaval.com/products/separation/centrifugal-separators/separators/innovations/separator-innovator/how-separation-works/how-a-disc-stack-centrifuge-works/?utm_source=chatgpt.com)

> Practical note: if your DCW or antifoam are high, expect more carryover and slightly higher turbidity out; that’s why we keep the recovery range wide.

## Depth filtration (post-centrifuge polish)

- **Purpose:** drop turbidity to **<10–20 NTU** with modest area after a good spin; widely used after centrifugation in yeast and Pichia harvests. [PubMed](https://pubmed.ncbi.nlm.nih.gov/30737749/?utm_source=chatgpt.com)
- **Specific capacity (post-centrifuge yeast supernatant):** plan conservatively at **70–120 L/m²** per final grade at ~100 NTU inlet (tune with your tests). (CHO centrate reports are often higher; yeast is tougher—use the low end.)
- **Flux cap:** **75–100 LMH** at terminal ΔP ≈ **1.0–1.2 bar**.
- **Hold-up loss:** assume **~0.3–0.7 L per 10″ module** after blow-down; vendor capsule data show residual volumes in that ballpark. [multimedia.3m.com](https://multimedia.3m.com/mws/media/1949217O/3m-zeta-plus-encapsulated-system-brochure.pdf?utm_source=chatgpt.com)
- **Adsorptive loss:** **0.3–1.0%** per train (protein/media dependent).
- **Protein step recovery:** **98–99.5%** (baseline **99.0%**).
- **Overall (disc-stack → depth):** **95–98%** (baseline **97.5%** as 0.985×0.99).

## Microfiltration (TFF) as polish (0.2 µm), not primary

- **Why as polish:** MF on **unclarified** yeast is area-hungry; even vendors show **~15–25 LMH** at **20–45% wet cell volume** without dilution—fine for pilots, punishing at 100 m³. [cdn.cytivalifesciences.com.cn](https://cdn.cytivalifesciences.com.cn/api/public/content/digi-13107-pdf?utm_source=chatgpt.com)
- **Clarified feeds:** **80–120 LMH** at **TMP ~0.8–1.0 bar** is a conservative operating window with near-quantitative passage of secreted proteins. Standard handbooks recommend stepping up flux while watching TMP to avoid transmission drops. [static.fishersci.eu](https://static.fishersci.eu/content/dam/fishersci/en_EU/suppliers/GE/Cross_Flow_Filtration_Method.pdf?utm_source=chatgpt.com)
- **Adsorption/hold-up:** **~0.5–1.5%** (membrane/polymer dependent; cassette hold-ups for 0.5–2.5 m² devices are on the order of **0.04–0.63 L** per cassette channel type—small but real). [Repligen](https://www.repligen.com/Products/TangenX_Flat_Sheet/TangenX_PRO_Reusable_TFF_Cassettes/resources/TX1001-VGD-101_R13.pdf?utm_source=chatgpt.com)
- **Protein step recovery (polish):** **98.5–99.5%** (baseline **99.0%**).
- **Overall (disc-stack → MF-polish):** **96–98.5%** (baseline **97.5–98.0%**).

# Cross-checks & anchors (why these numbers aren’t rosy)

- **Disc-stack is the right first step** for yeast at ≥3% v/v solids; it’s the industry default for primary harvest (and designed for low-to-moderate solids with small particles). [Alfa Laval+1](https://www.alfalaval.com/products/separation/centrifugal-separators/separators/innovations/separator-innovator/how-separation-works/how-a-disc-stack-centrifuge-works/?utm_source=chatgpt.com)
- **Yeast/Pichia harvest recipes** commonly run **centrifugation → depth filter → 0.2 µm** to deliver supernatant to capture; this exact sequence is described in lab-to-plant methods for Pichia supernatant processing. [PubMed](https://pubmed.ncbi.nlm.nih.gov/30737749/?utm_source=chatgpt.com)
- **Depth modules retain residual liquid** after blow-down (capsule hold-up tables exist), which is precisely why we budget an explicit volume loss per 10″ equivalent. [multimedia.3m.com](https://multimedia.3m.com/mws/media/1949217O/3m-zeta-plus-encapsulated-system-brochure.pdf?utm_source=chatgpt.com)
- **Unclarified MF is slow**: Pichia microfiltration data show **~15–25 LMH** at high WCW—a non-starter at 100 m³ unless you buy a football field of membranes. Use it as a **polish** after centrifuge, where flux rebounds. [cdn.cytivalifesciences.com.cn](https://cdn.cytivalifesciences.com.cn/api/public/content/digi-13107-pdf?utm_source=chatgpt.com)
- **MF operating discipline** (flux/TMP stepping) matters; even general TFF method guides emphasize backing off flux as TMP climbs to protect transmission. [static.fishersci.eu](https://static.fishersci.eu/content/dam/fishersci/en_EU/suppliers/GE/Cross_Flow_Filtration_Method.pdf?utm_source=chatgpt.com)

# Plug-and-play numbers for your BioSTEAM classes (derated, “upside possible”)

Use these as **defaults**, not maxima:

- **Disc-stack**
   `protein_recovery = 0.985` (97–99% range)
   `centrate_turbidity_NTU = 100` (50–200 NTU band)
   `underflow_dry_fraction = 0.30` (25–35%) → drives entrainment loss
   `carryover_solids = 0.2% of feed solids`
- **Depth filter train (10 → 1 µm)**
   `final_grade_capacity_Lm2 = 70` (range 70–120)
   `flux_LMH_cap = 90` ; `dP_term_bar = 1.2`
   `adsorption_loss = 0.5%` ; `hold_up_L_per_10in = 0.6`
   `step_recovery = 0.99` (98–99.5%)
- **MF-polish (0.2 µm TFF)**
   `flux_LMH = 90` (range 80–120) ; `TMP_bar = 0.8–1.0`
   `adsorption_loss = 0.01` (0.5–1.5%) ; `cassette_holdup_L` from device spec (e.g., 0.11–0.63 L per cassette, size-dependent) [Repligen](https://www.repligen.com/Products/TangenX_Flat_Sheet/TangenX_PRO_Reusable_TFF_Cassettes/resources/TX1001-VGD-101_R13.pdf?utm_source=chatgpt.com)
   `step_recovery = 0.99`
- **Overall step yield guards**
   `overall_yield_disc+depth = 0.975` (use 0.96–0.98 bounds)
   `overall_yield_disc+MF = 0.975` (use 0.965–0.985 bounds)

# Where to be extra-cautious (dial these down first if you need to)

- **Antifoam present?** Derate depth filter capacity by **~20–30%** and expect higher adsorptive loss.
- **Very high DCW (≥50–60 g/L)** at harvest? Expect larger sludge volumes; entrainment-driven loss grows—keep disc-stack step to **97–98%** until plant data prove better.
- **Trying unclarified MF?** Cap flux at **25 LMH** and set a big area budget; it’s rarely competitive at 100 m³. [cdn.cytivalifesciences.com.cn](https://cdn.cytivalifesciences.com.cn/api/public/content/digi-13107-pdf?utm_source=chatgpt.com)