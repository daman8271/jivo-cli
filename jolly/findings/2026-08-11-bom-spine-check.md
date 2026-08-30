# Finding 01 — the BOM spine is real (Oil)

**Date:** 2026-08-11 · **Company:** JIVO_OIL_HANADB · **Method:** read-only SQL via `hana-sql`

Purpose: before designing anything, prove the data spine the pilot depends on
actually exists in SAP and is maintained. It does.

---

## 1. BOMs exist and are live

| | Count |
|---|---|
| BOM headers in Oil (`OITT`) | **625** |
| — production type (`P`) | 383 |
| — sales type (`S`) | 242 |
| Mustard production BOMs (`U_TYPE=COMMODITY`, `U_Sub_Group=MUSTARD`) | 36 |

Most recent BOM update: **2026-08-11** (FG0000429) — i.e. today. These are
maintained, not a stale one-time load.

## 2. The explosion works — worked example

`FG0000030 — MUSTARD KACHI GHANI 1 LTR 20 PCS` (BOM yields 20 PCS = 1 carton):

| Child | Item | Kind | Qty per 20 PCS |
|---|---|---|---|
| RM0000003 | MUSTARD LOOSE OIL | MUSTARD | 20 LTR |
| PM0000851 | PET BOTTLE 1 LTR 26 GM | PET BOTTLES | 20 |
| PM0000235 | CAPS 1 LTR WHITE AND YELLOW SMALL PLAIN | CAPS | 20 |
| PM0000020 | LABEL 1 LTR KACHCHI GHANI FRONT | LABEL | 20 |
| PM0000019 | LABEL 1 LTR KACHCHI GHANI BACK | LABEL | 20 |
| PM0000411 | CARTON 1 LTR 20 PCS PET 26GM | CARTON | 1 |
| PM0000075 | TAPE LOGO PRINTED | TAPE | 1.016 MTR |
| JWPL09240002 | Filling Cost Commodities | *resource (costing)* | 20 |

Packaging is segmented cleanly in the item master by `U_Sub_Group`:
LABEL (488 items) · CARTON (91) · TIKKI (59) · CAPS (54) · PET BOTTLES (33) ·
POUCH (32) · TIN (21) · SHRINK (17) · HDPE BOTTLES (13) · GLASS BOTTLES (11).

## 3. Live stock, same components (all warehouses summed)

| Item | UoM | On hand | Committed | On order |
|---|---|---|---|---|
| FG0000030 (finished 1L mustard) | PCS | 10,591 | **94,779** | 46,699 |
| PM0000851 PET bottle 1L | PCS | 68,068 | 31,006 | 1,642,232 |
| PM0000235 caps | PCS | 683,118 | 223,796 | 679,000 |
| PM0000020 label front | PCS | 346,358 | 18,400 | 500,000 |
| PM0000019 label back | PCS | 333,057 | 18,400 | 500,000 |
| PM0000411 carton (20 PCS) | PCS | 16,508 | 4,457 | 39,641 |
| PM0000075 tape | MTR | 1,260,206 | 97,531 | 183,876 |
| RM0000003 mustard loose oil | **LTR** | 163,117 | 110,076 | 458,619 |

**Open question, not yet verified:** finished-goods committed (94,779) exceeds
on-hand (10,591) by ~84k bottles. That is either a genuine live shortfall or an
artefact of how `IsCommited` accumulates open sales orders. Must be settled
before any alarm is built on it — an alarm that cries wolf is worse than none.

## 4. Lead times ARE derivable from history — no template needed

Observed PO date → GRPO receipt date, Oil, since 2025-08-01:

| Item | Vendor | Receipts | Avg days | Min | Max |
|---|---|---|---|---|---|
| RM0000003 mustard oil | AWL AGRI BUSINESS | 41 | **49.6** | 3 | 98 |
| RM0000003 mustard oil | VAISHNODEVI OIL SEEDS | 30 | 20.7 | 1 | 43 |
| RM0000003 mustard oil | VAISHNODEVI AGRO RESOURCES | 22 | **12.7** | 3 | 35 |
| RM0000003 mustard oil | ARORA AGRI BUSINESS | 6 | 15.0 | 5 | 28 |
| RM0000003 mustard oil | VAISHNODEVI REFOILS & SOLVEX | 4 | 16.3 | 5 | 30 |
| PM0000851 PET bottle | TPAC PACKAGING INDIA II | 21 | 19.4 | 2 | 47 |
| PM0000851 PET bottle | BR AGROTECH | 9 | 10.2 | 2 | 18 |
| PM0000411 carton | SSY CONTAINERS | 41 | 27.1 | 1 | 68 |
| PM0000411 carton | SHIVALIK CONTAINERS | 2 | 10.5 | 10 | 11 |
| PM0000235 caps | BABAJI UDYOG | 16 | 17.0 | 2 | 35 |
| PM0000235 caps | MAHESHWARI CAPS | 8 | 13.3 | 1 | 30 |
| PM0000019/20 labels | ZENBI INTERNATIONAL | 9 | 7.1 | 1 | 12 |
| PM0000075 tape | BAKSHI PLASTIC BHANDAR | 8 | 4.6 | 2 | 11 |
| PM0000075 tape | SHRI PATA ENTERPRISES | 2 | 8.5 | 5 | 12 |

**Two consequences:**

1. **Lead time is a property of the vendor, not the material.** Mustard oil takes
   49.6 days from AWL and 12.7 from Vaishnodevi Agro — 4× apart. A single
   "lead time per material" cell on a template averages these into a number that
   describes nothing. The pilot must reason per vendor.
2. **The spread is the real signal.** Every material swings wildly (cartons 1–68
   days). That variance is what should size the safety buffer — not a flat 35%.
   Buffer = f(observed lead-time variance, demand variance), computed per item.

## 5. Unit-of-measure trap — confirmed, and dangerous

`RM0000003 MUSTARD LOOSE OIL`: inventory UoM = **LTR**, purchase UoM = **MTS**,
`NumInBuy = 1098.9` → **1 MT = 1098.9 litres**.

Stock and BOM consumption are in litres; purchase orders are in tonnes. Any
message the pilot sends that says "order 50" without the unit is wrong by a
factor of ~1,100. Every quantity the pilot emits must carry its unit, and the
conversion must be read from `OITM.NumInBuy` per item, never assumed.

## 6. Machine capacity is genuinely absent — the brief is right

`ORSC` (SAP resources) holds **7 rows**, and all 7 are *costing* lines, not
machines:

```
FILLING COST RS 2/- PER LITRE · Filling Cost Commodities ·
FILLING COST CANOLA AND OLIVE · FILLING COST GIFT PACK ·
PET BOTTLE BLOWING CONVERSION COST · TEA JOB WORK · OIL FILLING JOB WORK
```

There are no machine speeds, no line definitions, no SKU→line mapping anywhere
in SAP. This must come from people. It is the single genuine data dependency.

---

## Scorecard against the management brief

| Brief says | Reality |
|---|---|
| Sales history — ERP automatic | ✅ confirmed |
| Live stock — ERP automatic | ✅ confirmed |
| BOM — ERP automatic | ✅ confirmed, maintained |
| **Lead times — template, from Procurement** | ❌ **derivable from history, and better** |
| Machine capacities — template, from Production/Infra | ✅ genuinely missing |
| Material-to-machine map — template, from Production | ✅ genuinely missing |
| Monthly plan — planning sheet, from Planning | ⚠️ human input the whole chain rests on |
| Min stock = flat 35% | ⚠️ placeholder; should be variance-driven per item |

**Net: three template asks become one and a half.** Procurement does not need to
fill in lead times — the pilot already knows them better than they do.
