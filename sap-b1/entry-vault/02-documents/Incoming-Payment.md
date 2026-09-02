---
type: document
sap_tables: [ORCT, RCT2, RCT4]
objtype: 24
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Incoming Payment — the customer receipt

> 29,706 across the three books, about **47 a working day** — the single highest-volume
> thing a person keys at JIVO. Preshit alone keys 1,276 in 90 days.

## At a glance

| | |
|---|---|
| SAP tables | `ORCT` header · `RCT2` applied documents (19,514) · `RCT4` (2,176) · **`RCT1`, `RCT3`, `RCT5` all empty** |
| ObjType / TransType | **24** |
| Volume | Oil 14,149 · Mart 11,391 · Bev 4,166 · **29,706** |
| Last 120 days | Oil 1,560 · Mart 2,017 · Bev 1,219 |
| Who keys it | Preshit 1,276 · Shoaib 555 · Gurpreet-Mayapuri 472 · Avtar 413 · Taran 383 (90 days, per `acc/INVENTORY.md`) |
| Needs approval? | **Never.** `WddStatus` is `-` on all 14,149 Oil rows — single-valued |
| Cash is real here | `CashAcct` on 1,247 Oil receipts, unlike payments where it is 14 |

**Mart runs more receipts than Oil in the recent window** (2,017 vs 1,560) on a much smaller
ledger. Mart is the distribution book — many small customers — so per-book habits differ
sharply. Do not carry an Oil assumption into Mart.

## Three kinds

| `DocType` | Oil | Receives from |
|---|---:|---|
| **`C`** | 11,726 | A **customer** — the normal case |
| **`A`** | 2,114 | Straight to a **GL account** (no customer) |
| **`S`** | 309 | A **supplier** — a refund from a vendor |

## `RCT2` has the same misnamed keys as payments — this is systematic

| Column | Its name suggests | What it **actually holds** |
|---|---|---|
| `RCT2."DocNum"` | the receipt's document number | **the receipt's `DocEntry`** |
| `RCT2."DocEntry"` | the row's own key | **the settled document's `DocEntry`** |

```
RCT2 joined to ORCT on H."DocEntry" = L."DocNum"  ->  19,514 rows
RCT2 joined to ORCT on H."DocNum"   = L."DocNum"  ->           0 rows
```

Identical to `VPM2` on the payment side (11,856 vs 0). **Treat it as an SAP-wide convention
for payment-application tables**: the header key is stored under `DocNum` and the target
document under `DocEntry`, on both sides. Verify with a count before trusting any join.
→ [[Outgoing-Payment]], [[Field-Name-Rosetta]]

## What a receipt settles

`RCT2."InvType"`, Oil, all history:

| `InvType` | Document | Rows | Applied ₹ |
|---:|---|---:|---:|
| 13 | [[AR-Invoice]] | 11,900 | **660.43 Cr** |
| **24** | **Another incoming payment** | **4,747** | **−615.94 Cr** |
| 14 | [[AR-Credit-Memo]] | 1,876 | 22.47 Cr |
| 30 | [[Journal-Entry]] | 725 | −4.85 Cr |
| 46 | [[Outgoing-Payment]] | 152 | 9.39 Cr |
| 18 | [[AP-Invoice]] | 113 | 5.12 Cr |
| 19 | [[AP-Credit-Memo]] | 1 | 0.05 Cr |

> [!warning] The negative rows are 93% of the positive value.
> −₹615.94 Cr against `InvType` 24 versus ₹660.43 Cr against invoices. **Any sum over
> `SumApplied` that ignores sign is meaningless** — it double-counts nearly every rupee.
>
> *Inferred, not confirmed:* this is the **on-account clearing** mechanism, not error
> reversal. When an advance or unapplied receipt is later applied to an invoice, SAP appears
> to write a negative row against the original receipt and a positive one against the
> invoice — so the money is recorded twice with opposite signs, and only the net is real.
> The same pattern exists on the payment side at smaller scale (−₹41.76 Cr). **What would
> confirm it:** trace one receipt whose `InvType` 24 row is negative back through both
> documents and check the dates and amounts line up as an advance-then-application pair.

**725 receipts settle a journal entry.** Same mechanism as on the payment side, and the same
consequence: an A/R invoice cleared by journal keeps looking open. **(C-0019)**

## Where the money lands

`TrsfrAcct` — 20 accounts, led by `2201101` (6,393) and `3200003` (2,293). And unlike vendor
payments, **cash is genuinely in use**: `CashAcct` is populated on 1,247 Oil receipts
(`1105003` ×926, `1105001` ×319). `acc/INVENTORY.md` counts 657 cash receipts in 90 days
across the books, so it is current practice, not history. → [[Payment-Terms-and-Banks]]

`Series` has 24 values plus **`-1` on 2,293 receipts** — a manual/no-series case worth
understanding before automating anything here. → [[Numbering-Series]]

## Field names

Receipts use the **payment** property names, not the document ones:

| Concept | Property to send | HANA column |
|---|---|---|
| Free text | **`Remarks`** (not `Comments`) | `Comments` |
| Journal memo | **`JournalRemarks`** | `JrnlMemo` |
| Branch | **`BPLID`** | `BPLId` |
| Control account | `ControlAccount` | **`BpAct`** |
| Currency | `DocCurrency` | **`DocCurr`** |
| Transfer account | `TransferAccount` | `TrsfrAcct` |

→ [[Field-Name-Rosetta]]

## The journal it posts

TransType 24. Oil, 14,645 journals:

- **Dr** the bank or cash account
- **Cr** the customer control account (`BpAct`)

For a `DocType` `A` receipt there is no customer leg — it credits the GL account in `RCT4`.

## Before you start

- [ ] **Which book** — and note Mart out-volumes Oil here.
- [ ] **`DocType`** — customer (`C`), GL account (`A`), or vendor refund (`S`)?
- [ ] **Cash or bank**, and which account.
- [ ] **Which invoices is it against?** You need their `DocEntry`s and the amount each. If
      none, it is on-account and someone matches it later.
- [ ] **Branch** — Oil is FACTORY-first here (7,177) with DELHI close behind (6,418).
- [ ] **Series** — and be aware 2,293 Oil receipts carry `-1`.
- [ ] Use `Remarks`, **not** `Comments`.

## Traps

1. **`RCT2."DocNum"` is the receipt's `DocEntry`.** The obvious join returns zero rows.
2. **Never sum `SumApplied` without sign** — the negative rows are 93% of the positive value.
3. **`Canceled` here is two-valued** (`N` 13,653 · `Y` 496) with **no `C` mirror** on `ORCT`,
   unlike purchasing documents where the mirror exists. So the C-0021 three-valued rule is
   about the *document* tables; check per table rather than assuming. **(cf. C-0021)**
4. **No approval, ever** — `WddStatus` is single-valued. A receipt goes straight in, so
   there is no review step to catch an error.
5. **A receipt can settle a journal entry** (725 of them), which is why an A/R invoice can be
   paid and still look open.
6. **`RCT1`, `RCT3`, `RCT5` are empty.** Only `RCT2` and `RCT4` hold anything.
7. **Cheque dishonour** appears in manual journals per `acc/INVENTORY.md`, not as a receipt
   reversal — so a bounced cheque is not visible from `ORCT` alone. **Unverified**; see Open
   questions.

## Open questions

1. Confirm the on-account clearing hypothesis for the negative `InvType` 24 rows by tracing
   one pair end to end. Until then the −₹615.94 Cr is a measured number with an inferred
   explanation.
2. What are the 2,293 receipts with `Series` = `-1`? Manual numbering, a migration, or an
   integration?
3. How is a **dishonoured cheque** actually recorded? `acc/INVENTORY.md` says manual journal;
   find a real example and document the pattern.
4. Why does Mart run more receipts than Oil on a smaller ledger — many small distributors, or
   a different collection process?
5. `RCT4` (2,176 rows) — the GL-account side, by analogy with `VPM4`. Not verified.
6. Can `sapb1 draft payment` create an incoming payment, or only outgoing?
   → [[Payment-Draft]]

## Queries used

```sql
-- the misnamed key, same as VPM2
SELECT (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."RCT2" L
          JOIN "JIVO_OIL_HANADB"."ORCT" H ON H."DocEntry"=L."DocNum") AS JOIN_ON_DOCENTRY,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."RCT2" L
          JOIN "JIVO_OIL_HANADB"."ORCT" H ON H."DocNum"=L."DocNum")   AS JOIN_ON_DOCNUM
FROM DUMMY;
-- 19,514 / 0

-- what receipts settle, and the sign problem
SELECT "InvType", COUNT(*) N, ROUND(SUM("SumApplied"),0) APPLIED
FROM "JIVO_OIL_HANADB"."RCT2" GROUP BY "InvType" ORDER BY N DESC;

-- which RCT line tables are even used
SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."RCT1";  -- 0
SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."RCT2";  -- 19,514
SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."RCT3";  -- 0
SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."RCT4";  -- 2,176
SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."RCT5";  -- 0
```

Profile: `_data/profile-ORCT.md`. Name map: `_data/rosetta-ORCT.md`.
