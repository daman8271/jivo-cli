# Finding 05 — the real problem, and what start-run teaches

**Date:** 2026-08-11 · Jivo Oil

---

## 1. The problem, stated correctly

From the operator, and it reframes everything built so far:

> There is a raw-material shortage. Demand exceeds what we can produce, so we sell
> at higher prices. We produce less oil than the market wants.

**This is not a stockout-prevention problem. It is an allocation problem.**

The difference matters more than anything else in this project:

| Stockout prevention | Allocation under scarcity |
|---|---|
| Goal: never run out | Assumes you *will* run short |
| Answer: order earlier, buffer more | Answer: decide what to make with what you have |
| Metric: fill rate | Metric: value per litre of scarce oil |
| Fails when supply is capped | Designed for supply being capped |

Kamalpreet's brief solves the left column. The business is in the right one.

**What follows logically:** if oil is the binding constraint, then every litre
spent on a low-margin SKU is a litre not spent on a high-margin one. The pilot's
core calculation is not "what do we need" — it is:

```
for every SKU that can be made:
    contribution per litre of scarce raw material
      = (selling price − packaging cost − conversion cost) ÷ litres of oil consumed
  → rank → allocate the available oil down the ranking
  → respect what is actually committed to customers
  → then tell the right person what to run and what to buy
```

Every input to that is already available: selling prices and costs in SAP, litres
per SKU from the BOM, oil on hand from stock, committed quantities from OMS.
**This is computable today.** It has not been computed.

## 2. Capacity is not the constraint — which confirms the above

Finding 04 established ~1.9× filling headroom at one shift. Combined with the
shortage, the picture is consistent and clear:

> **Machines are idle because there is nothing to fill them with.**

That is why availability reads 93–100% while performance reads 28–32%. The line is
switched on and assigned; it just has no oil. The OEE report has been measuring a
supply-chain problem and labelling it a production problem.

## 3. What `start-run` shows

`/production/execution/start-run` — walked read-only. **`Start Run` not pressed:
it is a live write into the factory.**

Form structure:

| Section | Fields |
|---|---|
| **Product SKU** | searchable — *"Search product by SKU code or name"* |
| **Run Details** | Production Line (all 7) · Date · Product (auto-filled) · **Required FG Quantity (cases/boxes)** · **Rated Speed (bottles/hr)** |
| **Raw Materials (BOM)** | Code · Name · **Per Unit** · **Required Qty** (editable) · UoM — *"BOM materials scale from this finished-good case/box quantity"* |
| **Manpower** | Labour · Other Manpower · Supervisor Name · Engineer/Operators |

Worked example from the operator (basil seeds, 400 gms jar) — 3 BOM lines:

| Code | Name | Per unit | UoM |
|---|---|---|---|
| PM0000302 | BASIL SEEDS SABZA | 0.4 | KGS |
| PM0000390 | PET JAR 60 GMS 400 GMS SEEDS | 1 | PCS |
| PM0000473 | LABEL 400 GMS BASIL SEEDS FULL | 1 | PCS |

### Three things this tells us

**a) The app reads SAP directly for items.** The search calls
`/api/v1/production-execution/sap/items/?search=…&produced_only=true`. So the item
master and the BOM behind this screen are **SAP's** — the same `OITT`/`ITT1` I
exploded in Finding 01. One source of truth for BOM. Good: no reconciliation
needed between app BOM and SAP BOM, because there is only one.

**b) `Rated Speed` is typed per run, not read from the line configuration.** The
field is free entry with a placeholder of `e.g., 3000`. **Performance % — and
therefore OEE — is computed against a number a human types at the start of each
run.** That is very likely part of the 28–32% story: a rated speed entered too
high manufactures a low performance figure with no machine involved.

Before anyone treats the OEE collapse as a factory problem, this needs checking:
compare each run's typed rated speed against that line's configured standard for
that pack size. Cheap to do, and it separates "we were starved" from "someone
typed 3000 instead of 1080".

**c) `Required Qty` on every BOM line is editable.** So actual consumption can
differ from BOM at the operator's discretion. Useful in reality, but it means BOM
explosion predicts requirement while actual issue may differ — and the gap between
the two is itself a signal worth watching.

## 4. What this changes about the pilot

The pilot's first job is not to raise alarms. It is to answer, every day:

1. **How much raw material do we actually have and what is inbound** (SAP stock +
   open POs + exim in-transit, with real lead times per vendor)
2. **What is that material worth in each possible finished good** (contribution per
   litre)
3. **What are we committed to** (OMS)
4. **Therefore: what should run tomorrow, on which line, and what must be bought
   today** — and who needs to be told

Steps 1–3 are computable from data already in hand. Step 4 is the pilot.

---

## Open items

- Rated-speed audit: typed value vs line standard, per run (§3b)
- Contribution-per-litre ranking across all Oil SKUs (§1)
- Correlate low-performance runs with component stock on the day (Finding 04 §5)
- Labour still zero on every line config
- 200 ML / 500 ML have no line; 3 LTR has no standard
