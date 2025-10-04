# A standardized accounting scheme

### 1) Define one allocation basis and stick to it

Pick exactly one of these as your primary driver. Use it for **both** CMO fixed fees and resin amortization.

- **KG_RELEASED**: allocate by kilograms of product released to spec (most conservative and common for commercial costing).
- **GOOD_BATCHES**: allocate by count of released batches (useful if batch sizes are uniform).
- **SCHEDULED_CAPACITY**: allocate by planned batches (penalizes under-utilization; good for budget control).
- **PROCESS_TIME_HOURS**: allocate by occupied process hours (best when batch sizes vary or there’s significant time-based bottlenecks).

Make this a declared policy, not a hidden toggle.

### 2) Split costs into pools

- **CMO fixed**: campaign fees, suite retainer/occupancy, per-day suite fees during active campaigns.
- **CMO variable**: per-batch fees.
- **Resin costs**:
  - **Capitalized resin**: amortize by **units-of-production (cycles used)** or **straight-line per qualified cycle**.
  - **Cycle-dependent operating costs**: CIP chemicals/utilities per cycle.
  - **Write-off policy**: if retired early, either expense remaining book value immediately or carry it to next period — choose and document.

### 3) Apply the allocation basis once, at the end

Sum CMO fixed + CMO variable + Resin amort + resin-cycle OPEX into annual totals, then divide by your single allocation denominator (kg released, good batches, scheduled capacity, or process hours). This guarantees Excel and BioSTEAM land on the same $/unit.



# Drop-in formulas (copy into Excel or BioSTEAM calc blocks)

Let:

- `C_campaign = Campaigns * (Campaign_Fee_per_Campaign + Suite_Fee_per_Campaign)`
- `C_suite_days = Campaigns * Campaign_Days * Suite_Fee_Per_Day`
- `C_batch = Batches_Executed * Per_Batch_Fee`
- `CMO_total = Retainer_Fee_per_Year + C_campaign + C_suite_days + C_batch`

Resin:

- `Resin_gross = Resin_Cost_per_L * Resin_Volume_L`
- `Amort_per_cycle = (Resin_gross * (1 − Salvage_Fraction)) / Resin_Lifetime_Cycles`
- `Total_cycles_used = Batches_Executed * Cycles_per_Batch`
- `Resin_amort_used = Amort_per_cycle * min(Total_cycles_used, Resin_Lifetime_Cycles)`
- `CIP_total = Total_cycles_used * CIP_Cost_per_Cycle`
- `Resin_total = Resin_amort_used + CIP_total`

Allocation denominator (choose one):

- `Den = Total_KG_Released`  (KG_RELEASED)
- `Den = Good_Batches_Released`  (GOOD_BATCHES)
- `Den = Campaigns_Planned_per_Year * Batches_Planned_per_Campaign`  (SCHEDULED_CAPACITY)
- `Den = Batches_Executed * Process_Hours_per_Batch`  (PROCESS_TIME_HOURS)

Per-unit results:

- `CMO_per_unit = CMO_total / Den`
- `Resin_per_unit = Resin_total / Den`
- `Total_per_unit = (CMO_total + Resin_total) / Den`

# Practical policy choices (recommendations)

- **Primary basis:** `KG_RELEASED` for external pricing and audits; it cleanly absorbs batch variability and aligns with revenue.
- **Resin amortization:** `UNITS_OF_PRODUCTION` (per cycle actually used). It’s fair, easy to audit, and ties cost to utilization.
- **Variance treatment:** If actual utilization is >10% below plan, **expense the variance now** (don’t quietly inflate next year’s $/kg). Keep those variances visible for ops planning.
- **Minimums & aborts:** If the CMO contract charges minimum campaign/suite fees regardless of batches executed, those fixed costs remain in the pool — your basis choice decides whether they hit $/kg (KG_RELEASED) or $/planned_batch (SCHEDULED_CAPACITY).

# How to wire this into your models



**BioSTEAM:** Add a small post-processing node (or `@property` on the system TEA) that consumes the same parameters and writes `$ per kg` into your TEA report. Don’t spread amortization across unit ops; compute once at the system level.

Wire it into BioSTEAM by calling `compute_allocation` after system simulation and then writing the results into your TEA summary.



## Policy defaults

- **Allocation basis**: `KG_RELEASED` (clean for cost-per-kg and revenue alignment)
- **Resin write-off**: `UNITS_OF_PRODUCTION` (per cycles actually used)
- **Variance handling**: keep it in your GL, but the math fully supports expense-now if under-utilized