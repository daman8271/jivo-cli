---
title: Dead & Slow Stock — capital locked in non-moving inventory
created: 2026-07-28
lens: dead-slow-stock
tags: [savings-audit]
---

# 🧊 Dead & Slow Stock — capital locked in inventory

Part of [[SAVINGS-MOC]]

**Lens question:** where is JIVO's cash sitting as inventory that isn't turning into sales?

**Scope:** all 3 HANA companies — `JIVO_OIL_HANADB` (Oil), `JIVO_MART_HANADB` (Mart), `JIVO_BEVERAGES_HANADB` (Beverages). As-of **2026-07-28**. 180-day window = since **2026-01-29**. 90-day window = since **2026-04-29**.

---

## 0. Method & the three traps that would have broken this analysis

Three modelling traps were found and corrected before any number below was trusted. They are recorded because any re-run must avoid them.

**Trap 1 — `OITM."AvgPrice"` is 0 for Oil and Mart.** Valuation is held per-warehouse. The authoritative book value is `OITW."StockValue"`, not `OITM."OnHand" * OITM."AvgPrice"`. Using the naive product gave ₹636 Cr for Oil (vs a real ₹63 Cr) — a 10x error.

**Trap 2 — `OITL` is the batch/serial log, NOT a universal movement ledger.** `OINM` does not exist in this database. `OITL` only carries rows for batch-managed items:

```sql
SELECT I."ManBtchNum" AS BATCH, COUNT(*) AS ITEMS,
       SUM(CASE WHEN T."ItemCode" IS NOT NULL THEN 1 ELSE 0 END) AS HAS_OITL_ROWS
FROM JIVO_OIL_HANADB.OITM I
LEFT JOIN (SELECT DISTINCT "ItemCode" FROM JIVO_OIL_HANADB.OITL) T ON T."ItemCode"=I."ItemCode"
WHERE I."InvntItem"='Y' GROUP BY I."ManBtchNum";
```

| BATCH | ITEMS | HAS_OITL_ROWS |
|---|---|---|
| N | 1300 | **2** |
| Y | 610 | 481 |

1,300 non-batch items (most packaging material) have **no OITL rows at all** — they would have been falsely classified as dead. Consumption is therefore built from real document lines instead.

**Trap 3 — JIVO Oil and Beverages are manufacturers.** Raw and packing material is consumed into production, never sold. Measuring velocity by sales alone (`INV1`) marked ₹39.94 Cr as "zero sales" — meaningless. True consumption = **sales (net returns) + goods issue**. `IGE1` and `WOR1."IssuedQty"` were verified to be the *same* movements (item `PM0000235`: IGE1 1,697,043 vs WOR1 1,704,304) so only `IGE1` is counted — no double-count.

**Canonical consumption CTE used throughout:**

```sql
CONS AS (SELECT "ItemCode", SUM(Q) AS OUTQ FROM (
  SELECT L."ItemCode" AS "ItemCode", L."Quantity" AS Q FROM <S>.INV1 L JOIN <S>.OINV H ON H."DocEntry"=L."DocEntry"
    WHERE H."CANCELED"='N' AND H."DocDate">='2026-01-29'
  UNION ALL SELECT L."ItemCode", -L."Quantity" FROM <S>.RIN1 L JOIN <S>.ORIN H ON H."DocEntry"=L."DocEntry"
    WHERE H."CANCELED"='N' AND H."DocDate">='2026-01-29'
  UNION ALL SELECT L."ItemCode", L."Quantity" FROM <S>.IGE1 L JOIN <S>.OIGE H ON H."DocEntry"=L."DocEntry"
    WHERE H."CANCELED"='N' AND H."DocDate">='2026-01-29'
) X GROUP BY "ItemCode")
```

`months_of_cover = OnHand / (OUTQ / 6.0)`

---

## H1 — Baseline: how much capital is in stock at all?

```sql
SELECT ROUND(TO_DOUBLE(SUM(W."StockValue"))/10000000,2) AS BOOK_VAL_CR
FROM <S>.OITW W JOIN <S>.OITM I ON I."ItemCode"=W."ItemCode" WHERE I."InvntItem"='Y';
```

| Company | Book stock value |
|---|---|
| Oil | ₹63.24 Cr |
| Beverages | ₹34.06 Cr |
| Mart | ₹9.30 Cr |
| **Total** | **₹106.60 Cr** |

**Verdict:** baseline established. ₹106.60 Cr gross.

---

## H2 — Is all of that really inventory? (FIXED ASSETS contamination)

```sql
SELECT B."ItmsGrpNam", COUNT(*) AS ITEMS, ROUND(TO_DOUBLE(SUM(S.VAL))/100000,2) AS VAL_LAKH
FROM (SELECT "ItemCode", SUM("OnHand") AS QTY, SUM("StockValue") AS VAL FROM <S>.OITW GROUP BY "ItemCode") S
JOIN <S>.OITM I ON I."ItemCode"=S."ItemCode" JOIN <S>.OITB B ON B."ItmsGrpCod"=I."ItmsGrpCod"
WHERE S.QTY>0 AND S.VAL>0 AND I."InvntItem"='Y' GROUP BY B."ItmsGrpNam" ORDER BY SUM(S.VAL) DESC;
```

Oil: RAW MATERIAL ₹2711.86 L · FINISHED ₹1590.12 L · **FIXED ASSETS ₹1311.08 L** · SEMI FINISHED ₹463.53 L · PACKAGING ₹313.99 L
Beverages: **FIXED ASSETS ₹3285.79 L** · PACKAGING ₹175.81 L · RAW MATERIAL ₹59.44 L · FINISHED ₹34.80 L

Top Beverages "FIXED ASSETS" rows are genuine plant: `FA0000048 FREEZE DEHYDRATION LINE` ₹526.29 L, `FA0000049 REFRIGERATION LINE` ₹476.95 L, `FA0000025 WATER BOTTLE FILLER` ₹404.63 L.

**Verdict: CRITICAL EXCLUSION.** ₹32.86 Cr of Beverages' ₹34.06 Cr "stock" is plant & machinery held in warehouse `BH-FA`, not working capital. **Beverages' true tradeable inventory is only ~₹1.20 Cr.** All dead-stock figures below exclude `ItmsGrpNam='FIXED ASSETS'`. (Note: `OITM."AssetItem"` is `'N'` for every item in all 3 companies, so the asset flag cannot be used — the item *group* must be.)

---

## H3 — Dead & slow stock (headline)

Classified excluding FIXED ASSETS, and excluding items **purchased in the last 90 days** (fresh stock is not dead stock — this removes e.g. `SF0000009 REFINED CANOLA OIL` ₹74.25 L bought 2026-07-18 and `SF0000008 POMACE OLIVE OIL 15KG TIN` ₹72.00 L bought 2026-06-11).

| Class | Oil | Mart | Beverages | Total |
|---|---|---|---|---|
| DEAD — no consumption 180d | ₹898.63 L | ₹7.89 L | ₹30.13 L | **₹936.65 L** |
| SLOW — cover > 12 months | ₹194.22 L | — | ₹92.35 L | **₹286.57 L** |
| SLOW — cover 6–12 months | ₹36.76 L | ₹4.83 L | ₹8.37 L | ₹49.96 L |
| (excluded: bought in last 90d) | ₹2319.84 L | ₹905.04 L | ₹110.21 L | — |

**Verdict: ₹12.23 Cr locked in dead + >12-month-cover stock** (₹9.37 Cr dead + ₹2.87 Cr slow). See [[finding-dead-slow-stock-1223cr]].

---

## H4 — Concentration: is it one item?

```sql
-- top dead items, Oil
... WHERE STK.QTY>0 AND STK.VAL>0 AND IFNULL(CONS.OUTQ,0)<=0 ORDER BY STK.VAL DESC;
```

| ItemCode | Name | Qty | Value | Cons. 180d | Last consumed |
|---|---|---|---|---|---|
| **RM0000052** | **LOOSE REFINED OLIVE OIL (DARK COLOUR)** | 294,993 | **₹821.16 L** | 0 | **2025-04-01** |
| SC0000069 | STAINLESS STEEL TESO LUNCHBOX | 2,027 | ₹7.13 L | −995 | 2026-01-31 |
| RM0000055 | VEGETABLE OIL (15 KGS) PER TIN | 160 | ₹5.79 L | 0 | 2025-11-11 |
| FB0000017 | MUSTARD KACCHI GHANI 5 LTR | 430 | ₹3.54 L | −4 | 2025-12-17 |

**91% of Oil's dead stock is a single item.** Confirming evidence — compare against its healthy sibling grade:

| ItemCode | Name | Stock | Value | Consumed 180d |
|---|---|---|---|---|
| RM0000052 | LOOSE REFINED OLIVE OIL **(DARK COLOUR)** | 294,993 | ₹821.16 L | **0** |
| RM0000001 | LOOSE REFINED OLIVE OIL | 157,523 | ₹280.35 L | **2,598,041** |
| RM0000013 | POMACE OLIVE LOOSE OIL IMPORTED | 47,222 | ₹144.38 L | 73,053 |

And it has **no production route at all**:

```sql
SELECT T."Father" FROM JIVO_OIL_HANADB.ITT1 T WHERE T."Code"='RM0000052';  -- 0 rows
```

Movement history (`OITL`, warehouse `BH-OT` bulk tank): last outward **2025-04-01**; a goods receipt of **249,949 units on 2026-03-31** (financial year end).

**Verdict: ₹8.21 Cr in one off-spec tank.** `RM0000052` holds ~2x the stock of the good grade, consumed zero while the good grade consumed 2.6M units, appears in **zero bills of material**, and has been static for **16 months**. Implied value ₹278.4/kg. See [[finding-offspec-olive-oil-821cr]].

---

## H5 — Carrying cost of the dead pile

₹12.23 Cr × 10% p.a. = **₹1.22 Cr per year** of financing/holding cost, recurring until liquidated.

**Verdict: ₹1.22 Cr annual-recurring.** See [[finding-stock-carrying-cost]].

---

## H6 — Negative stock quantity (phantom stock)

```sql
SELECT SUM(CASE WHEN "OnHand"<0 THEN 1 ELSE 0 END) AS NEG_QTY_ROWS FROM <S>.OITW;
```

Oil 1 row (qty 0) · Mart 0 · Beverages 0.

**Verdict: KILLED.** No negative-quantity problem. Physical quantity discipline is clean.

---

## H7 — Inventory valuation drift (zero quantity, non-zero value)

```sql
SELECT SUM(CASE WHEN IFNULL("OnHand",0)=0 AND "StockValue"<>0 THEN 1 ELSE 0 END) AS ROWS_,
       ROUND(TO_DOUBLE(SUM(CASE WHEN IFNULL("OnHand",0)=0 AND "StockValue"<>0 THEN "StockValue" ELSE 0 END))/100000,2) AS LAKH
FROM <S>.OITW;
```

| Company | Rows | Value |
|---|---|---|
| Oil | 960 | −₹188.68 L |
| Beverages | 289 | −₹148.48 L |
| Mart | 1 | −₹0.01 L |
| **Total** | **1,250** | **−₹337.17 L** |

Concentrated in packing-material warehouses — Oil `GP-PM` −₹53.63 L, `BH-PM` −₹35.95 L; Beverages `GP-PM` −₹88.61 L.

Total negative `StockValue` rows (regardless of qty): Oil 831 rows −₹216.85 L, Beverages 424 rows −₹259.58 L.

**Verdict: ₹3.37 Cr of inventory carried at negative value with zero physical stock.** Inventory over-relieved → COGS overstated, inventory GL understated. An accounting correction, not cash. See [[finding-inventory-valuation-drift]].

---

## H8 — Physical stock carried at ZERO value (hidden asset)

```sql
SELECT COUNT(*) AS ROWS_, ROUND(TO_DOUBLE(SUM(W."OnHand")),0) AS QTY,
       ROUND(TO_DOUBLE(SUM(W."OnHand"*IFNULL(I."LastPurPrc",0)))/100000,2) AS WORTH_LAKH
FROM <S>.OITW W JOIN <S>.OITM I ON I."ItemCode"=W."ItemCode"
JOIN <S>.OITB B ON B."ItmsGrpCod"=I."ItmsGrpCod"
WHERE W."OnHand">0 AND IFNULL(W."StockValue",0)=0 AND I."InvntItem"='Y' AND B."ItmsGrpNam"<>'FIXED ASSETS';
```

Raw output: Oil ₹28.93 L (112,985 u) · Mart ₹9.80 L (2,804 u) · **Beverages ₹517.35 L (807,207 u)**.

**⚠ Beverages figure is a data artefact — do not report it.** It is 98% one row: `PM0000566 LABEL 250 MLS BOPP`, 95,500 units × `LastPurPrc` **₹531 each** = ₹507.11 L. Peer labels price at ₹0.48–0.73. Verification:

```sql
SELECT ... FROM JIVO_BEVERAGES_HANADB.PCH1 L JOIN JIVO_BEVERAGES_HANADB.OPCH H ON ...
WHERE L."ItemCode"='PM0000566' AND H."CANCELED"='N';   -- 0 rows
```

The item has **no purchase history at all**; the ₹531 is stale inherited master data (~1000x out).

**Verdict: ₹0.49 Cr** of genuine unvalued physical stock (₹28.93 + ₹9.80 + ~₹10.24 L) — understated asset. Plus a master-data defect on `PM0000566`. See [[finding-zero-valued-stock]].

---

## H9 — Stop-buying: still purchasing what we already have years of

Items with **> 12 months cover** that were **still purchased in the last 90 days**:

| Company | Items | Spend in 90d | Their stock |
|---|---|---|---|
| Oil | 16 | ₹21.49 L | ₹48.81 L |
| Mart | 5 | ₹9.62 L | ₹11.66 L |
| Beverages | 4 | ₹1.00 L | ₹6.51 L |
| **Total** | **25** | **₹32.11 L** | ₹66.98 L |

Worst offenders (Oil): `PM0000125 PET BOTTLE 500 MLS` 26.0 months cover, bought 57,744 more; `PM0000860 LABEL 1 LTR SOYABEAN` **39.7 months** cover, bought 154,600 more; `PM0000609 LABEL 15 KGS REFINED SOYBEAN` 24.8 months cover, bought 36,900 more; `RM0000043 COCONUT OIL` **46.5 months** cover.

**Verdict: ₹1.28 Cr/yr run-rate** (₹32.11 L × 4) spent on items already carrying >1 year of cover. See [[finding-overbuying-covered-items]].

*Caveat:* MOQs, price-lock and seasonal buys make some of this legitimate; treat as the deferrable pool, not a guaranteed saving.

---

## H10 — Open POs on items that need nothing

```sql
OPO AS (SELECT L."ItemCode", SUM(L."OpenQty"*L."Price") AS OVAL FROM <S>.POR1 L
  JOIN <S>.OPOR H ON H."DocEntry"=L."DocEntry"
  WHERE H."CANCELED"='N' AND H."DocStatus"='O' AND L."LineStatus"='O' AND L."OpenQty">0 GROUP BY L."ItemCode")
```

| Class | Oil | Mart | Beverages | Total |
|---|---|---|---|---|
| Cover > 12m | ₹150.87 L | ₹0.60 L | ₹32.36 L | ₹183.83 L |
| Dead (no consumption) | ₹6.27 L | ₹4.11 L | ₹33.98 L | ₹44.36 L |
| **Total** | **₹157.14 L** | **₹4.71 L** | **₹66.34 L** | **₹228.19 L** |

Dominated by one line:

| ItemCode | Name | Stock | Cons 180d | Cover | Open PO | PO date |
|---|---|---|---|---|---|---|
| **RM0000039** | **A-2 COW GHEE** | 3,966 | 1,000 | **23.8 mo** | 20,000 u = **₹142.00 L** | **2026-07-23** |
| PM0000125 | PET BOTTLE 500 MLS | 108,927 | 25,131 | 26.0 mo | ₹7.11 L | 2026-07-01 |
| SC0000069 | SS TESO LUNCHBOX | 2,027 | −995 | dead | ₹2.87 L | 2025-02-01 |

A ₹1.42 Cr purchase order raised **5 days ago** for an item with ~2 years of cover; 20,000 units against 1,000 consumed per 180 days is ~10 years of cover.

**Verdict: ₹2.28 Cr of cancellable/deferrable open commitment**, of which ₹1.42 Cr is a single fresh ghee PO. See [[finding-open-po-on-overstocked]].

*Caveat:* the A-2 ghee PO may be a deliberate new-product/contract scale-up — confirm with Purchase before cancelling.

---

## H11 — Stale open purchase orders

```sql
SELECT CASE WHEN H."DocDate"<'2025-01-28' THEN 'A_GT_18M' WHEN H."DocDate"<'2025-07-28' THEN 'B_12_18M' ... END AS AGE,
  COUNT(DISTINCT H."DocEntry") AS POS, ROUND(TO_DOUBLE(SUM(L."OpenQty"*L."Price"))/100000,2) AS OPEN_LAKH
FROM <S>.POR1 L JOIN <S>.OPOR H ON H."DocEntry"=L."DocEntry"
WHERE H."CANCELED"='N' AND H."DocStatus"='O' AND L."LineStatus"='O' AND L."OpenQty">0 GROUP BY ...;
```

| Age | Oil | Mart | Beverages |
|---|---|---|---|
| > 18 months old | ₹166.69 L (84 POs) | — | ₹71.26 L (42 POs) |
| 12–18 months old | ₹275.20 L (53 POs) | ₹41.43 L (2) | ₹39.57 L (69 POs) |
| **> 12 months total** | **₹441.89 L** | **₹41.43 L** | **₹110.83 L** |

Oldest examples still open: `FG0000195/196/199` spices POs dated **2024-10-21**.

**Verdict: ₹5.94 Cr of open PO commitment older than 12 months across ~250 POs.** Exposure: a supplier shipping against a stale PO obliges JIVO to accept unwanted goods; it also inflates `OnOrder` and corrupts reorder logic. See [[finding-stale-open-pos]].

---

## H12 — Near-expiry / expired stock (FMCG risk)

`OBTN."Quantity"` is **cumulative received, not on-hand** (Oil: OBTN 88.2M vs OITW 3.15M; only 74/480 items reconcile). Correct source is `OBTQ` joined to `OBTN` for `ExpDate`, valued at item unit value `SUM(StockValue)/SUM(OnHand)`.

| Bucket | Oil | Beverages |
|---|---|---|
| Already expired | ₹18.76 L (12,708 u) | ₹1.62 L |
| Expiring < 3 months | ₹0.09 L | ₹0.13 L |
| Expiring 3–6 months | ₹0.61 L | — |
| **No expiry date set** | **₹3,902.18 L** | — |

**Verdict: ₹0.20 Cr of expired stock on hand** — modest, write-off/disposal candidate. The larger issue is qualitative: **the overwhelming majority of batch stock has no expiry date recorded at all** (Oil ₹39 Cr; Mart has *zero* expiry dates on 3,868 batches). For an edible-oil/beverage FMCG this is a shelf-life traceability control gap, not a ₹ figure. See [[finding-expiry-not-tracked]].

---

## H13 — Warehouse-stranded stock

Warehouses holding > ₹1 L of non-FA stock with **zero** outbound movement in 180 days:

| Company | Warehouse | Stranded |
|---|---|---|
| Beverages | BH-PM | ₹104.12 L |
| Oil | BH-BS | ₹71.80 L |
| Beverages | BH-WST / BH-NM / BH-FR / BH-LB / PB-ST | ₹26.05 L |
| Oil | GP-NM | ₹5.11 L |
| Mart | GP-ECM | ₹1.15 L |
| **Total** | | **₹208.23 L** |

**Verdict: ₹2.08 Cr sitting in warehouses with no outbound activity.** ⚠ **Overlaps** with H3/H4 (same items counted there) — do **not** add to the headline. Useful as a physical-location worklist for the liquidation exercise.

---

## H14 — Negative warehouse valuation, Beverages

From the warehouse breakdown: Beverages carries materially negative `StockValue` in `GP-PM` −₹84.95 L, `BH-SN` −₹67.47 L, `BH-PF` −₹17.03 L, `BH-GR` −₹6.34 L, `GP-NM` −₹4.91 L ≈ **−₹1.81 Cr**, offsetting its positive stock. This is the same root cause as H7 (over-relieved inventory) concentrated at Beverages.

**Verdict:** folded into [[finding-inventory-valuation-drift]]; flags Beverages costing as the priority company to fix.

---

## Summary ledger

| # | Finding | Company | ₹ | Kind | Confidence |
|---|---|---|---|---|---|
| 1 | Off-spec olive oil `RM0000052`, 16 months static, no BOM | Oil | 8.21 Cr | working-capital-release | high |
| 2 | Stale open POs > 12 months old (~250 POs) | ALL | 5.94 Cr | working-capital-release | medium |
| 3 | Inventory valuation drift (zero qty, negative value) | ALL | 3.37 Cr | one-time-recovery | high |
| 4 | Slow stock, cover > 12 months | ALL | 2.87 Cr | working-capital-release | high |
| 5 | Open POs on dead / >12-month-cover items | ALL | 2.28 Cr | working-capital-release | high |
| 6 | Overbuying items already >12 months covered | ALL | 1.28 Cr/yr | annual-recurring | medium |
| 7 | Carrying cost @10% on ₹12.23 Cr dead+slow | ALL | 1.22 Cr/yr | annual-recurring | high |
| 8 | Dead stock excluding the olive oil | ALL | 1.15 Cr | working-capital-release | high |
| 9 | Physical stock carried at zero value | ALL | 0.49 Cr | one-time-recovery | medium |
| 10 | Expired batches still on hand | Oil+Bev | 0.20 Cr | one-time-recovery | high |

**One-time / working-capital release: ~₹24.5 Cr.  Annual-recurring: ~₹2.50 Cr/yr.**

*Not double-counted:* H13 warehouse-stranded ₹2.08 Cr overlaps rows 1/4/8. Beverages' ₹32.86 Cr FIXED ASSETS is excluded throughout.

Back-links: [[SAVINGS-MOC]] · [[2026-07-28]]
