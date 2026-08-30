---
title: EXIM — the live plan, the inbound oil pipeline, and the Ukraine contract
type: reference
source: "EXIM API eximbe.jivo.in, scraped live 2026-08-29 (12 agents, 3 adversarial verifiers)"
last_verified: 2026-08-29
tags: [jivo/reference, jivo/exim, jivo/oil, jivo/planning]
---

# EXIM holds the live plan. The Excel round-trip is solved.

`GET /planning/latest/` — **this endpoint removes the hand-maintained workbook.**

| | |
|---|---|
| Month | **2026-09-01** — "PRODUCTION PLANING MONTH OF SEP 2026" |
| Uploaded | 2026-08-27 by `aahar831@gmail.com`, from `PLANNING FOR SEP 2026.xlsx` |
| Rows | 186 · **185 carry the SAP FG item code** |
| Total | **4,323,300 L** (commodity 1,077,000 + premium 813,300 + ecom 2,433,000) |
| **Weekly split** | `commodity_w1..w4`, `premium_w1..w4` — **475,800 / 471,500 / 471,500 / 471,500 L** |

`total_planning` is **LITRES**, proven on the large packs (5 L mustard = 230,000 L
÷ 5 = 46,000 jars). E-com carries a monthly figure only, no week split.

**This is the dated demand that was declared missing.** It is weekly, not daily, but
it is dated, per-SKU, and joined to SAP by item code. Nothing needs to come out of
Excel again. Loader: `jolly/engine/sep_plan.py`.

> **TLS note:** `eximbe.jivo.in` handshakes intermittently from the Mac
> (`unable to get local issuer certificate` / `UNEXPECTED_EOF`). It is reliable from
> the VPS, so every call routes `ssh vps → curl`. Not a permission problem.

# 28 endpoints the repo had never seen

The repo documented 100; 70 of 147 probed paths answered 200. The valuable new ones:

| Endpoint | What it gives |
|---|---|
| `GET /pos/` | **623 SAP purchase-order lines** with landed cost and PO→GRPO dates |
| `GET /planning/latest/` | the live monthly plan, per SKU, weekly |
| `GET /planning/uploads/` | plan version history |
| `GET /dc/details/` | 144 landed-cost rows |
| `GET /hana/accounts/*` | a whole treasury namespace — **403 for this login** |
| `GET /sap-sync/warehouses/` | 9 warehouses incl. BH-GJ, BH-CRUDE |
| `GET /rates/pack-size/`, `/rates/pack-rate/` | packing economics |

**Measured lead time across 623 PO lines: median 12 days, mean 17.0, p90 36, max 101.**

# The Ukraine crude canola contract — CONFIRMED, and it is a governance hole

| | |
|---|---|
| Record | EXIM stock-status **id 674**, item `RM0CDRO` CRUDE CANOLA |
| Quantity | **750,000 kg = 824,175 L** (EXIM stores mass; ÷0.91) |
| Rate / value | ₹126.000/kg (₹114.660/L) = **₹9,45,00,000 — ₹9.45 Cr** |
| Vendor | `TEMP0010`, vendor_name literally **"UKRAINE"**, country `UR` |
| Window | 2026-07-23 → **2026-08-22 — EXPIRED** |
| ETA / GRPO | **both null** |
| Status | still `IN_CONTRACT` |
| Created | 2026-07-25 by `raspreet@exim.com` |

**There is no SAP purchase order behind it, and it is structurally impossible for
there to be one:** SAP `JIVO_OIL_HANADB` has no business partner named Ukraine, no
CardCode starting `TEMP`, and no partner in country UA or UR. So this is a process
gap by construction — not a broken sync.

**₹29.36 Cr sits in 9 `IN_CONTRACT` rows** — Ukraine canola 9.45, Arora soya 5.96 +
0.28, AWL soya 3.93, AWL mustard 3.90, Arora mustard 2.62 ×2, Cobram olive 0.61.

# SUBSTITUTION IS A SAP ENTRY, NOT A FLOOR ACTION — ruled by Daman, 2026-08-29

> *"The substitutions are only done in the SAP."*

**This reverses the conclusion below and it matters more than anything else in this
file.** When SAP's August work orders show GROUNDNUT made from peanut + soyabean +
olive + rice bran, that is **bookkeeping, not a recipe**. The floor did not pour
soyabean into a sunflower tank. SAP recorded whatever code was issued.

**Consequences, and they are the opposite of what was written here first:**

1. **The BOM (`OITT`/`ITT1`) IS the real recipe.** Use it. `engine/plan_explode.py`
   already does — that was right.
2. **NEVER derive a recipe from `OWOR`/`WOR1` component history for a normal oil.**
   It is a record of what got booked, not of what the product is made of.
3. **Oil is NOT fungible.** Do not pool it. A mustard SKU needs mustard oil. Any
   engine that pools oil across SKUs will report a month as makeable when it is not.
4. **The ONE exception is the two real blends**, `RM0000021` GOLD and `RM0000040`
   SO OLIVE. They have no BOM, they genuinely are mixtures, and work-order history is
   the only source for their ratios. That use stands.

The section below is kept as the RAW OBSERVATION that led to the question — it is
accurate about what SAP contains, and wrong about what it means.

---

# What SAP's work orders literally contain (an artefact, see the ruling above)

Daman said it; SAP's August production orders prove it, and it **refutes this repo's
earlier crude→canola story**:

- `RM0000002` CANOLA COLD PRESS was made in August from **SOYA 217,330 L +
  RM0000015 73,300 L + RICE BRAN 12,500 L + PEANUT 2,050 L — and ZERO crude
  rapeseed.** 308,267 L produced without any `RM0000016`.
- `RM0000009` REFINED SUNFLOWER — 225,642 L made in August from **soyabean 202,150 L
  + rice bran 21,370 L**, no sunflower in it.
- `RM0000011` GROUNDNUT — 489,825 L made from **peanut 218,845 + soyabean 160,975 +
  RM0000001 51,000 + rice bran 39,370**.
- `RM0000001` OLIVE — 408,155 L made from itself + RM0000052 141,000 + soya 90,000
  + pomace 20,000.

**Consequence for every engine:** a per-oil shortage is NOT a real constraint. Total
litres of oil is. Any bottleneck list that says "short of sunflower" is an artefact —
the floor makes sunflower out of soyabean. [[OIL-PROCESSING]]'s 1.028 crude→canola
ratio is a 180-day average that August did not follow.

## Links
[[PLANNING-MODEL]] · [[PLAN-AND-LINES]] · [[GODOWNS]] · [[OIL-PROCESSING]]
