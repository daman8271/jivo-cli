---
title: "Adversarial verification — Finding #6: ₹9.31 Cr JIVO MART intercompany return"
created: 2026-07-28
lens: verify-intercompany-stock-reversal
tags: [savings-audit, verification, returns, intercompany, sap-b1]
---

# Adversarial verification — Finding #6 (intercompany stock reversal)

Part of [[SAVINGS-MOC]] · verifies [[finding-intercompany-stock-reversal]] from [[returns-leakage]]

**Claim under test:** "₹9.31 Cr of finished goods pushed back from related party JIVO MART to
JIVO OIL in two days — chronic 10.3% intercompany return rate", classified
**working-capital-release ₹9,31,00,000**, action = *"cap primary dispatches to JIVO MART at its
actual secondary sell-through so ₹9 Cr of finished goods stops round-tripping."*

**Verdict: REFUTED — ₹0.** The documents are real and the arithmetic is exact, but the
transaction is a **godown migration inside one physical site**, not a commercial push-back of
unsold stock. Nothing is recoverable and nothing is released.

**Tool:** `/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql` (read-only SELECT).

---

## V1 — Does the ₹9.31 Cr reproduce at document level? (different query shape)

Finder used a `GROUP BY CardCode` aggregate. I pulled every document instead.

```sql
SELECT "DocEntry","DocNum",TO_VARCHAR("DocDate",'YYYY-MM-DD') AS DT,"DocType",
       "CANCELED","DocStatus",
       ROUND(CAST("DocTotal"-IFNULL("VatSum",0) AS DOUBLE)/100000,2) AS NET_L
FROM JIVO_OIL_HANADB.ORIN
WHERE "CardCode"='CUSTA000606' AND "DocDate">='2026-07-01'
ORDER BY "DocDate","DocNum"
```

19 documents, **all `DocType='I'` (item, not service), all `CANCELED='N'`**, all `DocStatus='C'`.

| Date | Docs | ₹ lakh |
|---|---:|---:|
| 02–07 Jul | 4 | 2.86 |
| 18 Jul (4 docs carry base invoice nos. in `Comments`) | 4 | 52.06 |
| **22–23 Jul (the event)** | **11** | **875.67** |
| **Total July** | **19** | **930.59** |

**Verdict: arithmetic CONFIRMED.** ₹9.3059 Cr, net of GST, no cancelled docs, no service-type
credit notes mixed in, no double counting. The finder's number is clean.

---

## V2 — Is it genuinely two-sided? Reconcile Oil ↔ Mart to the rupee

```sql
SELECT h."DocNum",TO_VARCHAR(h."DocDate",'YYYY-MM-DD') AS DT,h."CANCELED",h."DocStatus",
       ROUND(CAST(h."DocTotal"-IFNULL(h."VatSum",0) AS DOUBLE)/100000,2) AS NET_L
FROM JIVO_MART_HANADB.ORPC h
WHERE h."DocDate">='2026-07-01' AND h."CardCode"='VENDA000001'
ORDER BY h."DocDate",h."DocNum"
```

| Side | ₹ lakh |
|---|---:|
| Oil A/R credit notes to CUSTA000606, July | 930.59 |
| less 18-Jul docs not mirrored as ORPC | (52.06) |
| **Oil, comparable** | **878.53** |
| **Mart A/P credit memos to VENDA000001, July** | **878.53** |

The 11 event documents match **value-for-value** (93.00 / 80.61 / 85.00 / 74.28 / 87.42 / 86.05 /
85.67 / 86.64 / 89.38 / 79.49 / 28.13). One Mart memo of ₹77.01 L is `CANCELED='Y'` with its
cancellation twin — correctly excluded by both of us.

GST symmetry:

```sql
SELECT 'OIL_CN_VAT', ROUND(CAST(SUM("VatSum") AS DOUBLE)/100000,2) FROM JIVO_OIL_HANADB.ORIN
WHERE "CardCode"='CUSTA000606' AND "CANCELED"='N'
  AND "DocDate">='2026-07-22' AND "DocDate"<='2026-07-23'
UNION ALL
SELECT 'MART_APCN_VAT', ROUND(CAST(SUM("VatSum") AS DOUBLE)/100000,2) FROM JIVO_MART_HANADB.ORPC
WHERE "CardCode"='VENDA000001' AND "CANCELED"='N'
  AND "DocDate">='2026-07-22' AND "DocDate"<='2026-07-23'
```

| Side | VAT ₹ lakh |
|---|---:|
| Oil credit notes | 43.78 |
| Mart A/P credit memos | 43.78 |

**Verdict: mirrored and GST-neutral.** No booking irregularity, no tax leakage. The finder was
right about this much. But "mirrored" only proves the paperwork is consistent — it says nothing
about whether goods were *pushed back*. That is V3.

---

## V3 — KILLER TEST: what did Oil ship to Mart on the SAME two days?

The finder never looked at the invoice side of the same dates.

```sql
SELECT TO_VARCHAR("DocDate",'YYYY-MM-DD') AS DT, COUNT(*) AS DOCS,
       ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/100000,2) AS NET_L
FROM JIVO_OIL_HANADB.OINV
WHERE "CardCode"='CUSTA000606' AND "CANCELED"='N' AND "DocDate">='2026-07-01'
GROUP BY TO_VARCHAR("DocDate",'YYYY-MM-DD') ORDER BY 1
```

| Date | Oil → Mart invoices | Oil ← Mart credit notes |
|---|---:|---:|
| 22 Jul 2026 | **11 docs, ₹952.80 L** | 2 docs, ₹173.61 L |
| 23 Jul 2026 | 4 docs, ₹48.24 L | 9 docs, ₹702.06 L |
| **22–23 Jul total** | **₹1,001.04 L (344,987 units)** | **₹875.67 L (248,990 units)** |

**Mart took in MORE than it sent back — 344,987 units in vs 248,990 units out, +₹125 lakh net.**
Stock at the related distributor did not fall. There was no "push-back of ₹9 Cr of unsold goods":
there was a simultaneous two-way movement.

**Verdict: the "over-push / round-tripping" thesis fails on its own dates.** → [[finding-mart-godown-migration-not-a-return]]

---

## V4 — Where did the goods physically go? (warehouse forensics)

```sql
SELECT S, l."WhsCode", COUNT(*) AS LINES, ROUND(SUM(CAST(l."LineTotal" AS DOUBLE))/100000,2) AS VAL_L
FROM ( SELECT '1_INV' AS S, li."WhsCode", li."LineTotal"
       FROM JIVO_OIL_HANADB.INV1 li JOIN JIVO_OIL_HANADB.OINV h ON h."DocEntry"=li."DocEntry"
       WHERE h."CardCode"='CUSTA000606' AND h."CANCELED"='N'
         AND h."DocDate">='2026-07-22' AND h."DocDate"<='2026-07-23'
       UNION ALL
       SELECT '2_CN', lr."WhsCode", lr."LineTotal"
       FROM JIVO_OIL_HANADB.RIN1 lr JOIN JIVO_OIL_HANADB.ORIN hr ON hr."DocEntry"=lr."DocEntry"
       WHERE hr."CardCode"='CUSTA000606' AND hr."CANCELED"='N'
         AND hr."DocDate">='2026-07-22' AND hr."DocDate"<='2026-07-23' ) l
GROUP BY S, l."WhsCode" ORDER BY 1,4 DESC
```

| Flow | Warehouse | ₹ lakh |
|---|---|---:|
| Oil ships out → | `GP-FG` Gupta Godown Basement Finished, **Sonipat** | 952.80 |
| Oil receives back ← | **`BH-BT` Bhakharpur New Basement, Sonipat** | 847.53 |
| Oil receives back ← | `BH-PF` Bhakharpur Production Finished, Sonipat | 28.13 |
| Mart ships back out → | `BH-FGM` Bhakharpur finished goods, **Sonipat** | 878.53 |
| Mart receives in ← | `GP-FGM` Gupta Finished Goods Mart, **Sonipat** | 1,001.04 |

**Every one of these godowns is at the same Bhakharpur / Gupta Godown complex in Sonipat**
(`OWHS."City"='Sonipat'`, Khasra No 20//9/2). No inter-city movement, no two-way freight.

Is `BH-BT` new?

```sql
SELECT TO_VARCHAR("DocDate",'YYYY-MM') AS M, COUNT(*) AS TXNS,
       ROUND(SUM(CAST("InQty" AS DOUBLE)),0) AS IN_QTY,
       ROUND(SUM(CAST("OutQty" AS DOUBLE)),0) AS OUT_QTY
FROM JIVO_OIL_HANADB.OINM WHERE "Warehouse"='BH-BT'
GROUP BY TO_VARCHAR("DocDate",'YYYY-MM') ORDER BY 1
```

| Month | Txns | In | Out |
|---|---:|---:|---:|
| **2026-07 (only month in the entire ledger)** | 225 | 359,517 | 72,022 |

`BH-BT` "Bhakharpur **New** Basement" has **zero transactions before July 2026** — it was
commissioned for this event. By `TransType`: 241,285 units in via A/R credit note (14), 118,192 in
via inventory transfer (67), 67,305 out via A/R invoice (13).

**Verdict: the receiving location is a brand-new warehouse opened the same month.** This is a
warehouse commissioning, not a return-to-vendor of failed stock.

---

## V5 — Mart's receiving godown migrated. The "return" is the residual.

```sql
SELECT TO_VARCHAR(h."DocDate",'YYYY-MM') AS M, l."WhsCode",
       ROUND(SUM(CAST(l."LineTotal" AS DOUBLE))/100000,2) AS PURCH_L
FROM JIVO_MART_HANADB.PCH1 l JOIN JIVO_MART_HANADB.OPCH h ON h."DocEntry"=l."DocEntry"
WHERE h."CANCELED"='N' AND h."CardCode"='VENDA000001' AND h."DocDate">='2026-01-01'
GROUP BY TO_VARCHAR(h."DocDate",'YYYY-MM'), l."WhsCode" ORDER BY 1,3 DESC
```

Mart's purchases from Oil, by receiving warehouse (₹ lakh):

| Month | BH-FG | **BH-FGM** | **GP-FGM** | DL-FG | DL-MP |
|---|---:|---:|---:|---:|---:|
| 2026-01 | 558.11 | – | – | 518.76 | 140.18 |
| 2026-02 | 590.53 | – | – | 464.01 | 140.44 |
| 2026-03 | 767.34 | – | – | 596.65 | 81.30 |
| 2026-04 | 355.80 | **1,016.87** | – | 205.52 | 42.61 |
| 2026-05 | 42.67 | **1,614.53** | – | 55.39 | 0.15 |
| 2026-06 | – | **2,111.82** | – | 0.00 | 0.33 |
| **2026-07** | – | 739.70 | **1,231.55** | – | – |

A clean two-step godown migration: `BH-FG` → `BH-FGM` (Apr) → `GP-FGM` (22 Jul). Closing stock
confirms it:

```sql
SELECT "WhsCode", COUNT(*) AS ITEMS, ROUND(SUM(CAST("OnHand" AS DOUBLE)),0) AS ONHAND_UNITS
FROM JIVO_MART_HANADB.OITW
WHERE "WhsCode" IN ('BH-FGM','GP-FGM','BH-FG','BH-JM') AND "OnHand"<>0
GROUP BY "WhsCode" ORDER BY 3 DESC
```

| Mart warehouse | Items | On hand (units) |
|---|---:|---:|
| **`GP-FGM` (new, filled)** | 32 | **193,213** |
| **`BH-FGM` (drained)** | 39 | **14,098** |
| `BH-JM` | 12 | 7,739 |
| `BH-FG` (old) | 5 | 92 |

**Verdict: the ₹8.76 Cr "return" is the residual `BH-FGM` stock handed back to Oil so the godown
could be vacated, while fresh stock filled `GP-FGM` the same day.** Oil parked the residual in the
newly-created `BH-BT`. This is a stock-location restructuring executed through sale/return
documents between two related entities at one site.

---

## V6 — Is the "chronic 10.3%" rate real?

```sql
SELECT ROUND(SUM(CASE WHEN T='S' THEN V ELSE 0 END)/10000000,2) AS SALES_CR,
       ROUND(SUM(CASE WHEN T='R' THEN V ELSE 0 END)/10000000,2) AS RET_ALL_CR,
       ROUND(SUM(CASE WHEN T='R' AND NOT (D>=TO_DATE('2026-07-22') AND D<=TO_DATE('2026-07-23'))
                 THEN V ELSE 0 END)/10000000,2) AS RET_EX_SWAP_CR,
       ROUND(100*SUM(CASE WHEN T='R' THEN V ELSE 0 END)
                /SUM(CASE WHEN T='S' THEN V ELSE 0 END),2) AS PCT_ALL,
       ROUND(100*SUM(CASE WHEN T='R' AND NOT (D>=TO_DATE('2026-07-22') AND D<=TO_DATE('2026-07-23'))
                 THEN V ELSE 0 END)/SUM(CASE WHEN T='S' THEN V ELSE 0 END),2) AS PCT_EX_SWAP
FROM ( SELECT 'S' AS T, "DocDate" AS D, CAST("DocTotal"-IFNULL("VatSum",0) AS DOUBLE) AS V
       FROM JIVO_OIL_HANADB.OINV WHERE "CardCode"='CUSTA000606' AND "CANCELED"='N'
         AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
       UNION ALL
       SELECT 'R', "DocDate", CAST("DocTotal"-IFNULL("VatSum",0) AS DOUBLE)
       FROM JIVO_OIL_HANADB.ORIN WHERE "CardCode"='CUSTA000606' AND "CANCELED"='N'
         AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29' )
```

| Measure | Value |
|---|---:|
| 12M Oil → Mart sales | **₹179.59 Cr** |
| 12M returns (all) | ₹18.51 Cr → **10.30%** |
| 12M returns **ex the 22–23 Jul godown swap** | ₹9.75 Cr → **5.43%** |

Monthly intercompany returns (₹ lakh): Jan 28.82 · Feb 17.04 · Mar 90.91 · Apr 199.26 · May 43.78
· **Jun 0.55** · Jul 930.59. June was effectively zero.

Historic spikes went into **normal operating warehouses** (`BH-FG`, `BH-GR`, `GP-FG`, `DL-EC`) and
never exceeded ~₹2.2 Cr/month. July 2026's ₹8.48 Cr into a brand-new `BH-BT` is categorically
different.

**Verdict: "chronic 10.3%" is REFUTED.** The underlying recurring intercompany return rate is
**5.43%**, and more than half of the headline is one structural event.

---

## V7 — Is there any over-push at all? (sell-through test)

```sql
SELECT TO_VARCHAR("DocDate",'YYYY-MM') AS M,
       ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/100000,2) AS MART_SALES_L
FROM JIVO_MART_HANADB.OINV WHERE "CANCELED"='N' AND "DocDate">='2025-07-01'
GROUP BY TO_VARCHAR("DocDate",'YYYY-MM') ORDER BY 1
```

| Month | Oil → Mart purchases ₹L | Mart onward sales ₹L | Sell-through |
|---|---:|---:|---:|
| 2026-04 | 1,651.75 | 1,863.97 | 113% |
| 2026-05 | 1,812.37 | 2,163.21 | 119% |
| 2026-06 | 2,040.15 | 2,603.88 | 128% |
| 2026-07 (to 28th) | 2,108.09 | 1,599.68 | 76% |

**Verdict: no evidence of systematic over-push.** Mart sold *more* than it bought from Oil in three
of the last four months. The recommended action — "cap primary dispatches to JIVO MART at its
actual secondary sell-through" — is not supported by the data; sell-through already exceeds 100%.

---

## V8 — Even if it were a real push-back, is ₹9.31 Cr a working-capital release?

No, on three independent grounds:

1. **Group level = ₹0.** Both entities are related parties under common control. The inventory
   never left the group or the Sonipat site; the intercompany receivable/payable eliminates on
   consolidation. Total group working capital is unchanged by construction.
2. **Wrong direction for Oil.** Oil's receivable from Mart fell (`OCRD."Balance"` CUSTA000606 =
   ₹2,399.83 L debit) but Oil took the inventory back onto its own books. Oil converted a
   receivable into stock — a working-capital **deterioration**, not a release.
3. **Wrong price basis.** ₹9.31 Cr is a *selling* price net of GST. Inventory carries at cost.
   (And per [[returns-leakage]] caveat 1, `OITM."AvgPrice"` is zero for every item, so cost cannot
   be measured at all in this system.)

**Verdict: ₹0 recoverable, ₹0 released, ₹0 recurring.**

---

## What survives

Only the reporting-hygiene point the finder already conceded in their own caveat 2:
**intercompany documents must be excluded from customer return KPIs.** Oil's headline 12M return
rate falls **6.1% → 3.46%** once CUSTA000606 is removed. That is a valid KPI correction and worth
acting on — but it is worth **₹0** in savings and it was already double-counted inside
[[finding-excess-returns-above-benchmark]].

Two genuinely open questions this raises (not sized, not claimed as savings):

- ~287k units are now parked in `BH-BT`, a warehouse created in July with 359,517 in / 72,022 out.
  If that stock ages, it becomes a real provision — track it under [[dead-slow-stock]].
- Oil's reported turnover carries ₹8.76 Cr of intercompany revenue that was reversed within
  90 days. A revenue-recognition/disclosure question for the auditor, not a cash saving.

---

## Caveats on my own refutation

- I cannot see physical goods movement, only SAP documents. If the stock was in fact trucked
  somewhere and back, freight would be a real cost — but both godowns share one address, so any
  movement is intra-site handling, not transport.
- `OITM."AvgPrice"` = 0 everywhere, so I could not test whether returned goods were near-expiry or
  written down. If they were, the loss is a stock-provision question, not a return-rate question.
- The 18-Jul ₹52.06 L of credit notes (which *do* carry base-invoice references in `Comments`) look
  like ordinary commercial returns and are not part of my refutation.
- GST credit notes were issued well inside the statutory window, so no blocked ITC.

---

**FINAL VERDICT: REFUTED · ₹0**

Back-links: [[SAVINGS-MOC]] · [[returns-leakage]] · [[finding-intercompany-stock-reversal]] ·
[[finding-mart-godown-migration-not-a-return]] · [[2026-07-28]]
