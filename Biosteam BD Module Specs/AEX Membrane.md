## What it does (and doesn’t)

- **Does:** Strongly depletes **DNA** and trims **acidic HCPs** (partial, salt-dependent), with **≥99.5 % product recovery** in FT mode.
- **Doesn’t:** Replace bind-and-elute capture. You size membranes for **mg impurity per mL** + time window.

------

## Core design parameters (conservative defaults)

**Performance / sizing**

- DNA capacity at load buffer, per membrane volume: `q_DNA = 10 mg/mL`
- Anionic-HCP capacity (at ~250 mM NaCl): `q_HCP = 2 mg/mL`
- Utilization (safety vs BT): `utilization = 0.70`
- Salt derate on HCP capture: `salt_derate_HCP = 0.5`
- Rated linear velocity: `MV_per_min = 10`  (membrane volumes per minute)
- ΔP cap: `deltaP_cap = 2.0 bar`
- Product adsorption loss (overall): `0.5–1.0 %` (use 0.5 %)

**Packaging (single-use capsules / stacks)**

- Membrane volume per module: `0.5 L`
- Max flow per module: `600 L/h` (at ΔP cap)
- Module cost: `USD 1,500` (process-grade)

**Economics (client-borne, always counted)**

- Buffer prep/flush fee: site rate (often USD `30–80 / m³`)
- Labor: `6 h/batch` @ `USD 80/h` (tune to site)
- Waste disposal: site rate (e.g., `USD 220 / t`)
- **Skid CAPEX flagged** (excluded in CDMO totals)

**Recovery & quality (targets)**

- Product recovery: `≥ 99.5 %` (budget 0.5 % loss)
- DNA breakthrough target: `≤ 10 %` of feed DNA (or to spec)
- HCP reduction: `~0.2–0.8 log` at 200–300 mM salt (protein- and pI-dependent)

------

## Equations you’ll wire

Let:

- $V_f$ = feed volume [L]
- DNA in feed = `DNA_in` [mg/L]; HCP in feed = `HCP_in` [g/L] (optional for sizing)
- Window $t$ [h] you want to process in (e.g., takt to next unit)

**1) Capacity-based membrane volume (mL):**
$$
V_{\text{cap}} = \frac{V_f \cdot \text{DNA\_in}}{q_{DNA} \cdot \text{util}} \;+\; \frac{V_f \cdot (1000 \cdot \text{HCP\_in}) \cdot \text{salt\_derate\_HCP}}{q_{HCP} \cdot \text{util}}
$$
(If $HCP\_in$ unknown, size only on DNA.)

**2) Throughput-based membrane volume (mL):**
$$
V_{\text{flow}} = \frac{V_f}{\text{MV\_per\_min} \cdot 60 \cdot t}
$$
**3) Required membrane volume:**
$$
V_{\text{mem}} = \max(V_{\text{cap}},\, V_{\text{flow}})
$$
**4) Modules, flow & time checks:**
$$
N_{\text{modules}} = \left\lceil \frac{V_{\text{mem}}}{\text{membrane\_volume\_per\_module}} \right\rceil,\quad
Q_{\text{need}} = \frac{V_f}{t} \le N_{\text{modules}}\cdot \text{max\_flow\_per\_module}
$$
If flow cap is exceeded, increase $N_{\text{modules}}$ or the window $t$.

**5) Buffers & losses (rough-cut):**

- Flush/prime/sanitize: plan **2–4 MV** total → buffer volume ≈ `(2–4) × V_mem`
- Product loss ≈ `product_adsorption_frac × product_mass` + hold-up (~**1 L per module**)

**6) Cost**
$$
\text{Cost}_{\text{batch}} \approx N_{\text{modules}}\cdot \text{module\_cost} \;+\; \text{buffer\_fee}\cdot V_{\text{buffer}} \;+\; (\text{labor}_h\cdot \text{rate}) \;+\; \text{waste}
$$

------

## Worked examples (takt = 8 h, MV/min = 10, defaults above)

Assume **DNA_in = 0.1 mg/L** after nuclease (tight), **HCP_in** unknown → size on DNA only.

### A) 15 m³ feed

- $V_{\text{cap}} = \frac{15{,}000 \times 0.1}{10 \times 0.70} \approx 214 \text{ mL}$
- $V_{\text{flow}} = \frac{15{,}000}{10 \cdot 60 \cdot 8} \approx 3.125 \text{ L}$ → **flow-limited**
- **Membrane volume** ≈ **3.13 L** → **7 modules** (0.5 L each)
- **Module cost** ≈ **USD 10.5k**
- Buffers (3 MV): ~9.4 L (negligible fee); Labor ≈ USD 480 → **Batch cost ~USD 11–12k**
- If product mass ~75 kg (5 g/L × 15,000 L × 100% — upstream example; adjust to your actual), **$ / kg ~ USD 150** (dominant cost is modules).

### B) 70 m³ feed

- $V_{\text{cap}} = \frac{70{,}000 \times 0.1}{10 \times 0.70} \approx 1.0 \text{ L}$
- $V_{\text{flow}} = \frac{70{,}000}{10 \cdot 60 \cdot 8} \approx 14.6 \text{ L}$ → **flow-limited**
- **Membrane volume** ≈ **14.6 L** → **30 modules**
- **Module cost** ≈ **USD 45k**
- Buffers (3 MV): ~44 L; Labor ~USD 480; add minor waste → **Batch cost ~USD 47–50k**
- If product ≈ **350 kg** (5 g/L × 70 m³), **$ / kg ≈ USD 135–145**.
   (If upstream recovery reduces mass to 0.7×, then ~245 kg → $ / kg scales proportionally.)

### C) 150 m³ feed

- $V_{\text{flow}} = \frac{150{,}000}{4800} \approx 31.25 \text{ L}$ → **63 modules**
- **Module cost** ≈ **USD 94.5k**; **Batch cost** typically ~**USD 100–105k**
- If product ≈ **750 kg**, **$ / kg ≈ USD 135–140**; at 70 % overall prior recovery, ~525 kg → **$ / kg ≈ USD 190–200**.

> Key pattern: with tight DNA after nuclease (0.1 mg/L), you are **throughput-limited**, so **$ / kg** stays roughly constant vs batch size for a fixed takt and MV/min. Reducing takt (e.g., 10 h → 12 h) or increasing MV/min reduces module count and cost.

------

## Sensitivities (what moves the needle)

- **Dose/treatment upstream (DNA_in):** If DNA_in doubles (0.2 → 0.4 mg/L), capacity begins to matter; $V_{\text{cap}}$ grows linearly, but at the DNA levels above you’re still often **flow-limited**.
- **Takt time:** Going 8 h → 12 h reduces $V_{\text{flow}}$ by **33%** (fewer modules).
- **MV/min:** Moving 10 → 12 MV/min reduces area ~**17%** (check ΔP).
- **Module price:** Real ranges are **USD 1,000–2,000**; this directly scales cost.
- **Product adsorption loss:** Keep it **≤ 1 %** (guard with a prefilter and adequate salt).

------

## Where to place it and how to operate

- **Placement:** After **DSP01 SPTFF** or **DSP02 capture** (AEX or Chitosan pH-mode) when DNA/HCP trimming is needed before **DSP04/05**.
- **Buffer:** Operate at your product-nonbinding buffer (e.g., **pH 7.0, 200–300 mM NaCl**).
- **Sequence:** `Prime → Equilibrate (1 MV) → Load → Flush (1–2 MV) → Optionally sanitize/storage`.
- **QC:** Trend **UV260** (DNA) and **UV280**; measure DNA_in/out to confirm capacity headroom.
- **Recovery protection:** Add a **0.2–0.45 µm guard filter** upstream; keep **CFV high enough** to avoid channeling; don’t exceed ΔP cap.

------

## BioSTEAM class knobs (recap)

```
# Performance
q_DNA_mg_per_mL = 10
q_HCP_mg_per_mL = 2
utilization = 0.70
salt_derate_HCP = 0.5
MV_per_min = 10
deltaP_cap_bar = 2.0

# Packaging
membrane_volume_per_module_L = 0.5
max_flow_per_module_Lph = 600
module_cost_usd = 1500
hold_up_L_per_module = 1.0
product_adsorption_loss_frac = 0.005

# Ops & econ
t_window_h (e.g., 8–12)
buffer_fee_usd_per_m3, labor_h_per_batch, labor_rate_usd_per_h, waste_fee_usd_per_tonne
ownership_mode = "CDMO"  # skid CAPEX flagged/excluded
```

------

## When to choose membrane AEX vs resin polish

- **Choose Membrane AEX FT** when **DNA** is the main offender or you want an inline, high-flux polish with **minimal tank time**.
- **Choose Resin AEX FT/BE** when you need **deeper HCP removal**, tighter selectivity, or when your DNA is already very low and polishing cost per kg is dominated by other factors.

  **Default: put the AEX membrane \*after\* SPTFF.**
   Reason: in flow-through mode you size the membrane mostly on **throughput (volume/time)**, not product mass. SPTFF cuts the volume by CF (e.g., 3×), so the **membrane area/modules and buffer use drop ~CF-fold** while the DNA mass to remove is unchanged. Capacity-based sizing (mg DNA per mL membrane) doesn’t care where you put it, but **time/cost do**—so you win by running on the smaller post-SPTFF pool.

  ### Why “after SPTFF” is the right baseline

  - **Fewer modules / lower cost:** In the common flow-limited regime, modules ∝ volume. CF=3 shrinks module count and cost ~3× for the same takt time.
  - **Same DNA removal:** Total DNA mass is the same; membrane capacity sizing is unchanged.
  - **Recovery risk is minimal:** Product adsorption in FT at 200–300 mM salt stays ≲0.5–1.0%; higher product concentration doesn’t materially change that if you keep the salt up.
  - **Cleaner handoff:** You get a compact, DNA-trimmed stream ready for DSP04/05; easier to hit dryer specs.

  ### When to consider “before SPTFF” (exceptions)

  - **SPTFF foul-prone feed:** If your clarified pool shows **>20% flux decay or fast TMP rise** in SPTFF despite standard prefilters—and diagnostics point to **DNA/acidic HCP as the culprit**—put a **small membrane AEX FT ahead of SPTFF** to protect it. You’ll size it for capacity (DNA mass) and allow a longer window, then still run the main membrane AEX after SPTFF if needed.
  - **Regulatory sequencing:** If you must demonstrate DNA reduction **before any downstream membrane**, run a light FT pass pre-SPTFF (again: capacity-not-time sizing), then keep the main FT after SPTFF for takt.

  ### Quick rule of thumb

  - **If SPTFF is stable** (normal flux curve, TMP within cap): **Membrane AEX FT after SPTFF**.
  - **If SPTFF fouls early from anionic junk:** add a **small pre-SPTFF FT mop**, but keep the main FT **after** SPTFF for cost and schedule.