# What CMOs actually have

- **Common**: 0.6–1.2 m ID process columns (DAC/PAC), bed height 20–30 cm.
- **Less common, but available at some large sites**: 1.6 m ID.
- **Rare at CDMOs**: 2.0 m ID (exists in some in-house plants).
- Bed heights much above **30 cm** are atypical for ion-exchange at scale because of ∆P and mass-transfer penalties; **20–25 cm** is the sweet spot.

# What one cycle really binds (and how many cycles you need)

Assume **utilization η = 0.9** (10% safety at the BT setpoint). Show both **50 g/L** (mild derate) and **40 g/L** (more conservative). Bed height = **0.25 m** unless noted.

Per-cycle capacity (kg) = Resin volume (L) × DBC_eff (g/L) × 0.9 / 1000.

| Column (ID × H)    | Resin Vol (L) | kg/cycle @50 g/L | kg/cycle @40 g/L | Cycles for 300 kg (@50/@40) |
| ------------------ | ------------- | ---------------- | ---------------- | --------------------------- |
| **0.8 m × 0.20 m** | 100           | 4.5              | 3.6              | 66 / 83                     |
| **1.0 m × 0.20 m** | 157           | 7.1              | 5.7              | 42 / 53                     |
| **1.2 m × 0.20 m** | 226           | 10.2             | 8.1              | 29 / 37                     |
| **1.2 m × 0.25 m** | 283           | 12.7             | 10.2             | 24 / 30                     |
| **1.6 m × 0.25 m** | 502           | 22.6             | 18.1             | 13 / 17                     |
| **2.0 m × 0.25 m** | 785           | 35.3             | 28.2             | 9 / 11                      |
| **2.0 m × 0.30 m** | 942           | 42.4             | 33.9             | 7 / 9                       |

> Sanity check: your “one-shot” resin at 60 g/L would be 5,000 L (not 6,000), but once you include η=0.9 and DBC_eff 40–50 g/L, the **resin-equivalent** you must process per batch sits in the **5.5–7.5 m³** band—which you service with **multiple cycles** on a practical column (or a couple of columns in parallel/staggered).

# Smallest **practical** column for a 100 m³ batch (300 kg)

- **What I’d call “smallest practical” and still keep the campaign sane:**
   **1.2 m ID × 0.25 m bed** (≈**283 L**) → **~24 cycles** at 50 g/L eff (or **~30** at 40 g/L).
   Most CDMOs can field this size; cycle time then drives your campaign length.
- If you want **≤15 cycles** per batch, step up to **1.6 m ID × 0.25 m** (≈**502 L**) or run **two 1.2 m columns** staggered (effectively halving cycles).
- If you need **single-digit cycles**, you’re in **2.0 m ID** territory (~785–940 L), which is **not typical** inventory at many CDMOs—doable in a few large facilities, but plan to verify availability early.

# Cycle-time reality (order-of-magnitude)

- **Load flow** at **300 cm/h** and **1.2 m ID** (area ≈0.785 m²) gives ~**2.35 m³/h** through the bed; if your load concentration is, say, **10 g/L**, then each **12.7 kg** cycle (1.2 m×0.25 m, 50 g/L eff) needs ~**1.27 m³ of load** → **~0.54 h** load time. Add equil/wash/elute/strip/CIP volumes (BV-based) and switches; a **2–3 h cycle** is a safe planning number.
- With **~24 cycles** that’s **~48–72 h** of column time (plus buffers and changeovers) — feasible for a campaign. Larger columns or dual columns drop that into the **1–2 day** zone.

# Recommended plan (what I’d spec for a CMO RFP)

- **Base case (widely available):** **1.2 m ID × 0.25 m** bed, **~24–30 cycles** per 300 kg batch (DBC_eff 50→40).
   Option to **duplicate column** for staggered cycling if you must shorten campaign time.
- **Stretch case (fewer cycles):** **1.6 m ID × 0.25 m**, **~13–17 cycles** — check CMO inventory.
- **Aspirational/limited availability:** **2.0 m ID**, **~7–11 cycles** — only some large sites; verify early.
- Keep **bed height 20–25 cm** unless your Ergun check and pump limits say you can push 30 cm without ∆P pain.

# A few conservative knobs to lock in your model

- **Utilization η = 0.9** at the chosen BT setpoint (10% safety).
- **DBC_eff = 40–50 g/L** until you’ve fitted your $f_{\text{RT}}, f_{\text{cond}}, f_{\text{DNA}}$ maps.
- **Lin. velocity = 250–300 cm/h**; **∆P cap = 2 bar**.
- **Pooling**: UV 10–90% with a **conductivity cap**; accept a point of recovery loss rather than sending salt to polish.
- **If cycles > ~30** on a 1.2 m column → suggest **dual columns** or **step up to 1.6 m**.

If you want, I can drop these options into a tiny sizing worksheet (you enter **DBC_eff**, **η**, **ID**, **H**, **product mass**) and it spits out **per-cycle kg, cycles/batch, and a rough time**—handy for AEX vs. chitosan scenarios and for CMO conversations.

