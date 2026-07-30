---
title: "Stock discipline bundle — stale POs, slow stock, over-covered buying"
created: 2026-07-29
verdict: MIXED
amount_verified_inr: 13949000
kind: working-capital-release
tags: [savings-audit, finding]
---

# 🧮 Stock discipline — three claims, re-derived and cut by 87%

Part of [[SAVINGS-MOC]] · Evidence: [[dead-slow-stock]]

## CFO summary in plain language

The sweep put **₹10.89 Cr** on the table under three headings: ₹5.94 Cr of purchase orders nobody ever closed, ₹2.87 Cr of stock we hold more than a year's worth of, and ₹2.28 Cr of fresh purchase orders for things we already have too much of.

I re-derived all three against live SAP and against a second, unrelated system (the factory gate-in database). **Only ₹1.39 Cr of it is money.**

- **The ₹5.94 Cr of old purchase orders is not money at all.** It is stale paperwork. Over the last twelve months JIVO received **17,093 goods-receipt lines worth ₹528 Cr** against purchase orders. **Not one single line** came against a purchase order older than a year. Nine out of ten arrive within a month of the order being raised. So the stated risk — "a supplier could still ship against these and we would have to pay" — has a measured frequency of **zero**. On top of that, **58% of the ₹5.94 Cr is capital projects** (bottling line, conveyors, moulds, refrigeration, civil construction), not stock. Closing these orders releases no cash whatsoever. It is a housekeeping job, and worth doing — an inflated "on order" figure quietly corrupts the reorder logic — but it is a control fix, not a saving.
- **The ₹2.87 Cr of slow stock is really ₹1.85 Cr, and only ₹0.98 Cr of that can actually be turned back into cash.** Measuring demand over six months instead of twelve made a set of ordinary seasonal items look dead; ₹70 lakh of the pile disappears the moment you use a full year. And ₹80 lakh of what is left is printed packaging — labels that say "DESI GHEE 1000 LTR (JIVO)" and pouches printed "SANO SOYABEAN". Nobody buys those second-hand. They unwind by being used up, not by being sold.
- **The ₹2.28 Cr of bad purchase orders is really ₹0.41 Cr.** The headline ₹1.42 Cr A-2 cow ghee order is **a good decision, not a mistake**: the item feeds fifteen live finished-goods recipes including the US export packs, and the order moves the business to a new dairy at **₹710 a unit against ₹807 previously — a 12% cut worth ₹19.4 lakh on this order alone**. A further ₹19.7 lakh is JIVO Mart restocking SKUs it had run out of, from JIVO Wellness — our own factory. And ₹54.9 lakh of it is the same rupees already counted in the stale-PO number.

**Net: ₹1.39 Cr of genuine working capital, worth ₹11.5 lakh a year in interest at our measured 8.25% cost of capital.**

---

## Component 1 — "₹5.94 Cr of open POs older than 12 months" → **REFUTED (₹0)**

**Arithmetic reproduces exactly.** My independent run returns **₹594.16 L** against the claimed ₹594.15 L. The number is right. It is not money.

### 1a. Measured conversion risk is zero

Every goods receipt in the last 12 months, in all three companies, traced back to its base purchase order:

```sql
SELECT CASE WHEN DAYS_BETWEEN(P."DocDate", G."DocDate") <= 30  THEN 'a 0-30d'
            WHEN DAYS_BETWEEN(P."DocDate", G."DocDate") <= 90  THEN 'b 31-90d'
            WHEN DAYS_BETWEEN(P."DocDate", G."DocDate") <= 180 THEN 'c 91-180d'
            WHEN DAYS_BETWEEN(P."DocDate", G."DocDate") <= 365 THEN 'd 181-365d'
            ELSE 'e >365d' END AS LAG_BUCKET,
       COUNT(*) AS GRPO_LINES, ROUND(TO_DOUBLE(SUM(L."LineTotal"))/100000,2) AS VALUE_L
FROM <S>.PDN1 L JOIN <S>.OPDN G ON G."DocEntry"=L."DocEntry"
JOIN <S>.OPOR P ON P."DocEntry"=L."BaseEntry" AND L."BaseType"=22
WHERE G."CANCELED"='N' AND G."DocDate" >= '2025-07-29'
GROUP BY 1 ORDER BY 1;
```

| Lag PO → receipt | Lines | Value |
|---|---:|---:|
| 0–30 days | 15,993 | ₹486.54 Cr |
| 31–90 days | 936 | ₹38.98 Cr |
| 91–180 days | 146 | ₹2.62 Cr |
| 181–365 days | 18 | ₹0.02 Cr |
| **> 365 days** | **0** | **₹0** |

17,093 lines, ₹528.16 Cr, **zero** against a PO older than a year.

**Corroborated from a completely separate system.** The factory gate-in database (`factory_flow`, Postgres — not SAP) logs raw-material receipts at the plant gate with the PO date recorded independently:

```sql
SELECT CASE WHEN (created_at::date - po_date) <= 30 THEN 'a 0-30d' … END AS bucket,
       COUNT(*) FROM raw_material_gatein_poreceipt WHERE po_date IS NOT NULL GROUP BY 1;
```

698 receipts, Feb–Jul 2026: **78.7% within 30 days, 98.3% within 90, 99.7% within 180, and zero beyond 365 days.** Two systems, two record-keeping teams, same answer.

### 1b. 58% is capital projects, not working capital (Trap 1)

```sql
SELECT CASE WHEN G."ItmsGrpNam" IN ('FIXED ASSETS','FA CONSUMABLES') THEN 'CAPEX' ELSE 'INVENTORY' END AS KIND,
       CASE WHEN L."OpenQty"/NULLIF(L."Quantity",0) <= 0.10 THEN 'residual tail'
            WHEN L."OpenQty"/NULLIF(L."Quantity",0) <  1.0  THEN 'part received'
            ELSE 'never received' END AS SHAPE,
       ROUND(TO_DOUBLE(SUM(L."OpenQty"*L."Price"))/100000,2) AS OPEN_L
FROM <S>.POR1 L JOIN <S>.OPOR H ON H."DocEntry"=L."DocEntry"
LEFT JOIN <S>.OITM I ON I."ItemCode"=L."ItemCode" LEFT JOIN <S>.OITB G ON G."ItmsGrpCod"=I."ItmsGrpCod"
WHERE H."CANCELED"='N' AND H."DocStatus"='O' AND L."LineStatus"='O' AND L."OpenQty">0
  AND H."DocDate" < '2025-07-29' GROUP BY 1,2;
```

| | CAPEX | INVENTORY | Total |
|---|---:|---:|---:|
| residual tail (≤10% left) | — | ₹3.74 L | ₹3.74 L |
| part received | — | ₹27.41 L | ₹27.41 L |
| never received | **₹344.38 L** | ₹218.63 L | ₹563.01 L |
| **Total** | **₹344.38 L** | **₹249.78 L** | **₹594.16 L** |

The capex names are unambiguous: JK CIVIL CONSTRUCTION ₹65.38 L, WILLUS INFRASTRUCTURE ₹60.97 L, VEETA CONVEYORS ₹85.00 L across two POs, INDUSTRIAL AIDERS ₹34.00 L, BOTTMAC INDIA, THE MOULDS, GLOBAL REFRIGERATION, DOMINO PRINTECH, SIGNODE INDIA, AIRPOWER SYSTEMS. Same shape as the Bakharpur land and Beverages bottling-line traps — deliberate capital spend, related to [[finding-hs-filling-advance]].

### 1c. A trap I set for myself and killed

I first re-derived using SAP's own `POR1."OpenSum"` field instead of `OpenQty × Price`, which produced a bigger, more alarming **₹8.82 Cr**. It is wrong. `OpenSum` is **not maintained** as a line is received:

| PO | Item | Ordered | Still open | Price | `OpenSum` | True residual |
|---|---|---:|---:|---:|---:|---:|
| 1224226665 (CONCEPT COLOUR, 28-Dec-24) | RM0000001 LOOSE OIL POMACE | 42.87 MT | **0.06 MT** | ₹2,97,623/MT | ₹1.28 Cr | **₹17,857** |
| 525226637 (SPEAR AGRO, 27-May-25) | RM0000006 DESI GHEE | 20,000 | 125 | ₹419.64 | ₹83.93 L | **₹52,455** |

`OpenSum` retains the full original line total forever. `OpenQty × Price` — the sweep's basis — is the correct one. Currency contamination also ruled out: of the entire open-PO book only ₹0.90 L is non-INR.

### 1d. Why the rupees are zero

A purchase order is an unrecognised commitment: no cash has moved, no asset is on the books, no liability is recorded. Cancelling one releases **nothing**. With a measured zero probability of conversion, there is neither money to collect nor spend to stop. What is real is the control defect — 250 orders holding phantom quantity in `OnOrder`, which suppresses genuine reorders and feeds bad MRP. Of the 71 Oil vendors involved, 33 are still actively billing us, so the paperwork should be closed on hygiene grounds regardless.

**Verdict: REFUTED as bankable. ₹0. Reclassify as a control observation.**

---

## Component 2 — "₹2.87 Cr of stock with >12 months cover" → **REVISED to ₹0.98 Cr bankable**

### 2a. The claim's own method does not reproduce

Running the sweep's exact recipe (180-day consumption × 2, exclude FIXED ASSETS, exclude anything bought in the last 90 days) gives **₹220.10 L**, not ₹286.57 L — 23% lower (Oil ₹157.01 L vs ₹194.22 L; Beverages ₹63.09 L vs ₹92.35 L; Mart nil).

### 2b. A six-month window manufactures slow stock

Rebuilding cover on a **365-day** consumption window drops the pile to **₹185.10 L**. Fifty-one items worth **₹70.22 L flip from "slow" to "healthy"** — they were half-year seasonality artefacts:

| Item | Cover on 180d | Cover on 365d | Value |
|---|---:|---:|---:|
| PM0000643 GLASS BOTTLE 200 MLS NEW (Bev) | 40.6 mo | **9.7 mo** | ₹21.92 L |
| RM0000034 LOOSE OIL RICE BRAN & OLIVE | 19.4 mo | **10.5 mo** | ₹20.36 L |
| FG0000155 EXTRA VIRGIN 2 LTR HANDLE | 18.8 mo | **8.9 mo** | ₹5.92 L |
| PM0000806 GIFT BOX | 2,907 mo | **5.1 mo** | ₹3.48 L |
| RM0000008 LOOSE OIL EXTRA LIGHT OLIVE | 1,002 mo | **5.1 mo** | ₹1.87 L |

```sql
-- consumption = A/R invoices − credit notes + production goods-issue, 365 days
C365 AS (SELECT IC, SUM(Q) OUTQ FROM (
  SELECT L."ItemCode" IC,  L."Quantity" Q FROM <S>.INV1 L JOIN <S>.OINV H ON H."DocEntry"=L."DocEntry" WHERE H."CANCELED"='N' AND H."DocDate">='2025-07-29'
  UNION ALL SELECT L."ItemCode", -L."Quantity"  FROM <S>.RIN1 L JOIN <S>.ORIN H ON H."DocEntry"=L."DocEntry" WHERE H."CANCELED"='N' AND H."DocDate">='2025-07-29'
  UNION ALL SELECT L."ItemCode",  L."Quantity"  FROM <S>.IGE1 L JOIN <S>.OIGE H ON H."DocEntry"=L."DocEntry" WHERE H."CANCELED"='N' AND H."DocDate">='2025-07-29'
) X GROUP BY IC)
-- cover = SUM(OITW."OnHand") / (OUTQ/12)
```

### 2c. Not all of it can become cash

| Group | Book value | Excess over policy* | Recovery route |
|---|---:|---:|---|
| PACKAGING MATERIAL | ₹79.57 L | ₹72.57 L | **none** — SKU-printed labels, preforms, caps, cartons |
| FINISHED | ₹57.07 L | ₹53.93 L | discount clearance |
| RAW MATERIAL | ₹48.46 L | ₹44.09 L | return-to-vendor / redeploy |
| **Total** | **₹185.10 L** | **₹170.60 L** | |

\* policy: 4 months packaging & raw material, 2 months finished goods.

It is a long tail, not a concentration — biggest single line is FG0000386 CHAI 250 GMS ₹39.57 L (36 months), then RM0000053 TOASTED SESAME ₹22.55 L (40 months) and RM0000047 LOOSE RICE ₹10.35 L (65 months); 256 items in all.

Printed packaging has no external market. It unwinds by being consumed, so it is a stop-buying and carrying-cost problem, not a releasable asset.

**Verdict: REVISED. Bankable = ₹98.03 L** (finished ₹53.93 L + raw material ₹44.09 L, excess over policy). Interest saved at 8.25% = **₹8.09 L/yr** (overlay on [[finding-cc-interest-conversion-rate]], not additive money). The dead pile is excluded throughout and stays with [[finding-off-spec-olive-oil]].

---

## Component 3 — "₹2.28 Cr of open POs on dead/over-covered items" → **REVISED to ₹0.41 Cr**

Like-for-like re-derivation gives **₹257.99 L** (180-day basis, inventory items only, capex groups excluded) — the claimed ₹228.19 L is in range. Then the composition dismantles it.

### 3a. The ₹1.42 Cr A-2 cow ghee PO is a good buy, not a leak

Three independent checks, all pointing the same way:

```sql
SELECT H."DocNum", H."DocDate", H."CardName", H."DocStatus",
       L."Quantity", L."OpenQty", L."Price", L."LineStatus"
FROM JIVO_OIL_HANADB.POR1 L JOIN JIVO_OIL_HANADB.OPOR H ON H."DocEntry"=L."DocEntry"
WHERE L."ItemCode"='RM0000039' AND H."CANCELED"='N' ORDER BY H."DocDate";
```

| PO | Date | Vendor | Qty | **Price** | Status |
|---|---|---|---:|---:|---|
| 625226610 | 2025-06-24 | ONLY AND SURELY ORGANIC (OSO) | 2,000 | ₹807 | Closed, fully received |
| 925226514 | 2025-09-04 | ONLY AND SURELY ORGANIC (OSO) | 2,600 | ₹807 | Closed, fully received |
| **220726107** | **2026-07-23** | **MALLEKAN DAIRY AND AGRO** | **20,000** | **₹710** | Open |

1. **It is a vendor switch with a 12% price cut** — ₹807 → ₹710, worth **₹19.4 L on this order**. That is a negotiated volume contract, not an oversight.
2. **The item is BOM-live in 15 finished SKUs** (`ITT1` where `"Code"='RM0000039'`): JIVO / KIRPA / LA RASOI desi ghee, DESI GHEE A2 500 MLS & 1 LTR, **DESI GHEE A2 USA 500 GMS & 1000 GMS** (export), 700 ML, 750 MLS, 15 KGS, and a gift pack. Its sibling RM0000006 DESI GHEE consumed 44,379 units in 365 days — this is a large, live ghee business.
3. **It was raised six days before the audit.** Second-guessing a live procurement decision as "verified savings" is not defensible.

Challenge it with Purchase — 20,000 units is 11× the 1,735 units issued last year and the scale-up should be evidenced — but do **not** book it as money.

### 3b. Mart's "dead item" POs are our own factory restocking us (Trap 2)

Every Mart line in the dead bucket is a purchase order on **JIVO WELLNESS PVT LTD** — the group's manufacturing company:

| Item | PO date | Open value |
|---|---|---:|
| FG0000430 MUSTARD KACHI GHANI 200 ML 70 PCS | **2026-07-28** | ₹7.56 L |
| FG0000388 COLD PRESS GROUNDNUT 200 MLS | 2026-04-08 | ₹5.35 L |
| FG0000047 COLD PRESS 3 LTR + EXTRA LIGHT OLIVE | 2026-07-21 | ₹1.99 L |
| FG0000152 SANO OLIVE CLASSIC 5 LTR (×2) | 2026-03/04 | ₹3.54 L |
| FG0000391 EXTRA VIRGIN OLIVE 3 LTR TIN | 2026-04-18 | ₹1.22 L |
| **Total** | | **₹19.66 L** |

Zero stock plus zero consumption means Mart is **out of stock** and restocking. The classifier reads a stockout as "dead item". It is also intercompany, so it nets to zero at group level.

### 3c. ₹54.87 L is already inside Component 1

```sql
… WHERE (no consumption in 180d OR OnHand > 2 × 180d consumption)
  AND I."InvntItem"='Y' AND G."ItmsGrpNam" NOT IN ('FIXED ASSETS','FA CONSUMABLES')
GROUP BY CASE WHEN H."DocDate" < '2025-07-29' THEN 'PO older than 12m' ELSE 'PO under 12m' END;
```

Oil ₹6.14 L + Beverages ₹48.73 L = **₹54.87 L** of this value sits on POs that are themselves older than 12 months, so it is the same rupees as the stale-PO finding.

### 3d. What survives

₹257.99 L − ₹142.00 L (ghee) − ₹19.66 L (intercompany) − ₹54.87 L (overlap) = **₹41.46 L** of genuinely deferrable live commitment — mostly packaging: PM0000891 POUCH SOYABEAN ₹9.30 L (17.1 mo), PM0000125 PET BOTTLE 500 MLS ₹7.11 L (**38.5 mo**), PM0000584 PET BOTTLE 160 MLS WHEAT GRASS ₹6.72 L (15.1 mo), PM0000799 POUCH 9 GM WG POWDER ₹1.78 L (43.1 mo), PM0000738 BOPP 160 MLS SHIKANJI ₹1.35 L (**507 mo**), plus a tail.

Unlike Component 1 these are 2026-dated POs that **will** be delivered — 99.4% of receipts land within 30 days — so deferring them genuinely stops cash going out.

**Verdict: REVISED. Bankable = ₹41.46 L.**

---

## Bundle total and overlaps

| Component | Claimed | Verified bankable | Verdict |
|---|---:|---:|---|
| Open POs > 12 months old | ₹5.94 Cr | **₹0** | REFUTED — control observation |
| Slow stock, cover > 12 months | ₹2.87 Cr | **₹0.98 Cr** | REVISED |
| Open POs on dead / over-covered items | ₹2.28 Cr | **₹0.41 Cr** | REVISED |
| **Bundle** | **₹10.89 Cr** | **₹1.39 Cr** | **MIXED** |

**Overlaps stated explicitly:**
- **₹54.87 L** appears in *both* Component 1 and Component 3 (open POs that are simultaneously over 12 months old and on over-covered/dead items). Removed from Component 3; Component 1 is zero anyway, so the bundle is not inflated by it.
- Components 2 and 3 do **not** share rupees — one is stock already on the balance sheet, the other is cash not yet spent — but they share a root cause, so the same corrective policy fixes both.
- Dead stock (₹9.37 Cr incl. RM0000052) is excluded from Component 2 throughout and belongs to [[finding-off-spec-olive-oil]].
- The **8.25% interest overlay is ₹11.51 L/yr** on the ₹1.39 Cr. Per audit convention this is an **overlay on [[finding-cc-interest-conversion-rate]], never additive bankable money**.
- Beverages capital-project POs inside Component 1 are adjacent to [[finding-hs-filling-advance]].

## Action

| # | Action | Owner |
|---|---|---|
| 1 | Close all 250 open POs older than 12 months as a data-hygiene sweep — **book ₹0 of savings against it**. Separate the ₹344 L of capital-project POs and route them to Projects to confirm live vs abandoned before closing. | Head of Purchase, with Finance sign-off on the capex list |
| 2 | Liquidate the ₹98 L convertible slow tier — discount-clear ₹54 L of finished goods, RTV/redeploy ₹44 L of raw material. Leave the ₹73 L of printed packaging to be consumed. | Head of Supply Chain |
| 3 | Defer or cancel the ₹41 L of live packaging POs on items already carrying 15–500 months of cover, before goods land. | Purchase Manager |
| 4 | Ask Purchase to evidence the 20,000-unit A-2 cow ghee scale-up (PO 220726107). **Do not cancel** — it carries a 12% price cut worth ₹19.4 L. | Head of Purchase → CFO |
| 5 | Add a hard control: block PO release when months-of-cover exceeds policy (4 months packaging/RM, 2 months FG), measured on a **rolling 365-day** window — a 180-day window creates false positives worth ₹70 L. | SAP / IT with Purchase |

## Method note for any re-run

- Use `OpenQty × Price`, **never** `POR1."OpenSum"` — that field is not maintained and overstates by ~1.5×.
- Use a **365-day** consumption window. A 180-day window mistakes seasonality for slow stock.
- Exclude `ItmsGrpNam IN ('FIXED ASSETS','FA CONSUMABLES')` and filter `OITM."InvntItem"='Y'` — otherwise capital projects and directly-expensed consumables land in the inventory numbers.
- "Zero stock + zero consumption" is **not** dead — for Mart it means a stockout being restocked.
- Before calling an open PO an exposure, measure the actual PO→receipt lag. Ours is 99.4% within 30 days and **zero** beyond a year.

Back-links: [[SAVINGS-MOC]] · [[dead-slow-stock]] · [[finding-off-spec-olive-oil]] · [[finding-hs-filling-advance]] · [[finding-cc-interest-conversion-rate]] · [[finding-inventory-valuation]]
