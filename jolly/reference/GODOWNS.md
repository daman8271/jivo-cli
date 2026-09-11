---
title: Godown codes — JIVO Oil
type: reference
company: JIVO_OIL_HANADB
source: "SAP OWHS + OITW, pulled live"
last_verified: 2026-08-29
tags: [jivo/reference, jivo/godown]
---

# Godown codes — what each one is, and whether the engine counts it

> [!important] Capacity lives in [STORAGE-CAPACITY.md](STORAGE-CAPACITY.md)
> This file says which godowns **count**. That one says how much **fits**. Oil's
> finished-goods ceiling is **827 T working / 923 T peak** — `BH-BT` 450/502 and
> `BH-PF` 377/421. Ruled by Daman 2026-08-29. Capacity tonnes are **litres**
> (1 T = 1,000 L). A requirement that ignores the ceiling is not a plan.
>
> **Gupta is not Oil's.** The sheet's 1,120 T `GP-FGM` row is *Mart's* warehouse
> in `JIVO_MART_HANADB`, committed to Mart — a different code from Oil's `GP-FG`.
>
> **Bulk oil is not in SAP's godowns at all — it is in EXIM.** Tank capacity is
> **1,351,500 L** across 32 tanks (`exim/exim tank get-summary`). EXIM and SAP
> share **no item code**, so `BH-LO` and the tanks cannot be reconciled.

**Settled by Daman, 2026-08-29. This is an ALLOW-LIST** — a godown nobody has
ruled on never silently starts counting as stock.

| Role | Codes |
|---|---|
| **Finished goods — Wellness only** | `BH-BT` · `BH-PF` |
| **Oil + packaging** | `BH-BS` · `BH-PM` · `BH-LO` · `BH-NM` · `BH-SDL` · `GP-NM` · `GP-FG` · `GP-PM` |
| **NOT ours** | `BH-OT` (Param) |
| **IGNORED — closed, do not raise again** | `BH-PP` (Daman, 2026-08-29) |
| Everything else | not counted |

> [!important] On-order is NOT allow-listed
> Stock is filtered to the godowns above. **Goods on order are counted from every
> godown** — inbound material is on its way in whatever warehouse it is booked
> against. Mustard's 465,334 L of open POs sit against `BH-GJ` (Gujarat job
> worker); filtering those out zeroed half a million litres of real inbound oil.

---

> **Wellness FG scope — Daman, 9 September 2026:** Finished goods, storage and dispatch-space reconciliation use **BH-BT and BH-PF only**. Exclude Gupta/GP-FG and GP-FGM from these calculations. Older FG inclusions below are superseded. Packaging has its own separately approved allow-list; this FG correction does not change it. Bulk oil remains EXIM-only; BH-LO and BH-GJ balances are not added. A mixed-company billed backlog is not verified BH-only physical occupancy.

## The four that count

| Code | Name | Holds today |
|---|---|---|
| **BH-BT** | Bhakharpur New Basement | **228,430 FG** + 10,326 PM |
| **BH-PF** | Bhakharpur Production Finished 1st Floor | **128,846 FG** + 510 PM |
| **BH-BS** | Bhakharpur Basement | **2,787,828 PM** (caps, preforms, bottles) |
| **BH-PM** | Bhakharpur Packaging Materials 1st Floor | **5,931,461 PM** |

> [!note] `BH-PP` is settled — ignore it
> 5,023,302 units, frozen since 2026-02-23. **Daman's call 2026-08-29: ignore.**
> Not counted as stock, not to be re-proposed, not a question for anyone.

## Excluded, and why it matters

| Code | Name | Holds today | Why excluded |
|---|---|---|---|
| **BH-OT** | **Param** | **302,668 RM** | **Not ours to use — Daman, 2026-08-29.** Holds dark olive, soyabean and ~32,500 L groundnut. Do NOT net it against any shortage. |

---

## Every Bhakharpur code

| Code | Name | FG | RM | PM | Active |
|---|---|---:|---:|---:|:--:|
| `BH-BS` | Bhakharpur Basement | | | 2,787,828 | ✅ |
| `BH-BT` | Bhakharpur New Basement | 228,430 | | 10,326 | ✅ |
| `BH-CRUDE` | Gujarat Crude | | | | ✅ |
| `BH-EC` | Bhakharpur Finished E-Commerce | | | | ✅ |
| `BH-EX` | Bhakharpur Export Warehouse | | | | ⛔ |
| `BH-FA` | Bhakharpur Fixed Assets | | | | ✅ |
| `BH-FG` | Bhakharpur Finished Basement | 13,432 | 4,894 | 173,234 | ✅ |
| `BH-FP` | Bhakharpur Production Test (GS) | | | | ⛔ |
| `BH-FU` | Bhakharpur Finished 1st Floor | | | | ⛔ |
| `BH-GJ` | Gujarat Job Worker | | 42,853 | | ✅ |
| `BH-GR` | Bhakharpur GR | 3,676 | | | ✅ |
| `BH-INT` | Bhakharpur Intransit | | | 8,060 | ✅ |
| `BH-JW` | BH-Job Work | 2,617 | | 252,355 | ✅ |
| `BH-LO` | **Bhakharpur Loose Oil** | | **808,933** | | ✅ |
| `BH-LR` | Luhari Jhajjar Finished | | | | ⛔ |
| `BH-NM` | Bhakharpur Non-Moving | | | 1,035,827 | ✅ |
| `BH-OT` | **Param** | | **302,668** | | ✅ |
| `BH-PC` | Bhakharpur Production Consumption | | 75,796 | 2,804,789 | ✅ |
| `BH-PF` | Bhakharpur Production Finished 1st Floor | 128,846 | | 510 | ✅ |
| `BH-PM` | Bhakharpur Packaging Materials 1st Floor | | | 5,931,461 | ✅ |
| `BH-PP` | Bhakharpur Production Process 1st Floor | 7,475 | 10,934 | 5,003,454 | ⛔ |
| `BH-PS` | Bhakharpur Preshit | | | | ✅ |
| `BH-SC` | Bhakharpur Schemes | 70,154 | 37 | 2,351 | ✅ |
| `BH-SDL` | Bhakharpur Sidel | | | 236,950 | ✅ |
| `BH-SN` | Bhakharpur Cold Storage | | | | ⛔ |
| `BH-UF` | Bhakharpur Unfinished | | | | ⛔ |
| `BH-VA` | Bhakharpur VA | | | | ✅ |
| `BH-WST` | Bhakharpur Wastage | 3,365 | 10,616 | 513,088 | ✅ |

## Delhi

| Code | Name | FG | PM | Active |
|---|---|---:|---:|:--:|
| `DL` | Infosys Delhi | | | ✅ |
| `DL-CG` | Delhi Consumable Goods | | | ✅ |
| `DL-EC` | Mayapuri E-Commerce | 1 | 5,027 | ✅ |
| `DL-FA` | Delhi Fixed Assets | | | ✅ |
| `DL-FG` | Mayapuri Finished | | | ✅ |
| `DL-GR` | Mayapuri GR | | | ✅ |
| `DL-INT` | Mayapuri Intransit | 1 | | ✅ |
| `DL-ISD` | Delhi ISD | | | ⛔ |
| `DL-J3` | Rajouri Garden Warehouse | 127 | | ✅ |
| `DL-POP` | Delhi Paper Media | | | ✅ |
| `DL-PS` | Preshit Samagam | 1,240 | | ✅ |

## Punjab

| Code | Name | FG | PM | Active |
|---|---|---:|---:|:--:|
| `PB-FG` | Punjab Haryana | | | ✅ |
| `PB-INT` | Punjab Intransit | | | ✅ |
| `PB-JP` | Punjab Grover Agency Jagraon C & F | 3,105 | 3,896 | ✅ |
| `PB-PS` | Punjab Preshit | 7 | | ✅ |
| `PB-RG` | Punjab Sangrur Oneness GR | | | ✅ |
| `PB-SG` | Punjab Sai Trading GR C & F | | | ✅ |
| `PB-SP` | Punjab Sangrur Oneness | | | ✅ |
| `PB-ST` | Punjab Sai Trading C & F | 20 | 25,956 | ✅ |

## Gupta godown · drop-ship · other

| Code | Name | FG | PM | Active |
|---|---|---:|---:|:--:|
| `GP-FA` | Gupta Godown Fixed Assets | | | ✅ |
| `GP-FG` | Gupta Godown Basement Finished | 2,615 | 64,680 | ✅ |
| `GP-NM` | Gupta Non-Moving | | 1,618,332 | ✅ |
| `GP-PM` | Gupta Godown Packaging Material | | 442,006 | ✅ |
| `DP-DL` | Drop Ship Delhi | | | ✅ |
| `DP-HR` | Drop Ship Haryana | | | ✅ |
| `DP-PB` | Drop Ship Punjab | | | ✅ |
| `HP-FG` | Himachal Finished | | | ⛔ |
| `HR` | Infosys Haryana | | | ⛔ |
| `MY-FA` | Mayapuri Consumable | | | ⛔ |
| `01` | General Warehouse | | | ⛔ |

---

## Traps

- **`BH-BS` is packaging, not finished goods.** The name says "Basement" and the
  finished-goods basement is `BH-BT` "New Basement". Reading `BH-BS` as FG returns
  zero and inflates every production requirement.
- **`BH-LO` is a factory/book loose-oil location, not a second tank balance.**
  Daman's 30-August EXIM-only ruling (C-0056) supersedes using this balance for
  planning oil. Read EXIM quantities and grades; missing mappings stay unresolved.
- **`BH-PP` and `BH-FU` are inactive but still hold stock.** `BH-PP` carries
  5,003,454 PM. Inactive does not mean empty.
- **`BH-NM` / `GP-NM` are non-moving but explicitly included by Daman.** His
  29-August 12:50:52 message adds both rooms (`harness/questions/log.jsonl:1136`).
  The earlier "Not available" sentence contradicted that instruction and is
  corrected on 9 September. Keep the recorded warehouse allow-list; individual
  rejected or otherwise held material is not made usable by a warehouse name.
- **`BH-WST` is wastage.** Never count it as stock.

---

## `BH-GJ` — NOT an exclusion. It is the front door for imported oil.

**Ruled by Daman, 2026-08-29** (this supersedes any earlier reading that BH-GJ is
merely a job-worker warehouse to be filtered out):

> *"import goods receives comes to this godown, this goes to job work. job work goes
> the crude oil and comes back the cold press. Or if the oil does not need cold
> pressing it comes to us."*

```
IMPORT ARRIVES ──► BH-GJ ──┬──► job work (crude out, COLD PRESS back) ──► BH-LO
                           └──► needs no cold pressing ──────────────────► us
```

**Therefore BH-GJ COUNTS as available oil.** Filtering it out was wrong and it
mattered: 670,038 of the 690,038 L of oil on order on 1 Aug was inbound to BH-GJ.
Excluding it cut the makeable figure from 17.7% to 7.7% — a 10-point error created
entirely by applying the allow-list to stock but not to inbound.

Evidence it is live transit, not storage: in August BH-GJ received 1,957,679 L by
GRPO and transferred out 1,870,262 L, with BH-LO receiving 1,890,605 L.

**Rule for every engine:** oil and crude at BH-GJ is COUNTED. The allow-list must be
applied to stock and inbound purchase orders identically — never one side only.
