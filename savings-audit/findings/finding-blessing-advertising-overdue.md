---
title: "BLESSING ADVERTISING PVT LTD (Beverages) — ₹3.11 Cr trade debtor on a 53-month self-service instalment plan"
created: 2026-07-28
verdict: REVISED
amount_verified_inr: 31092246
kind: one-time-recovery
tags: [savings-audit, finding]
---

# BLESSING ADVERTISING PVT LTD — ₹3.11 Cr overdue in Beverages

Part of [[SAVINGS-MOC]] · Evidence: [[receivables-aging]]

## Plain-language summary (for the CFO)

JIVO's Beverage Unit sold ₹3.67 Cr of 200 ml tonic water to a single customer —
**Blessing Advertising Pvt Ltd**, which is also one of JIVO's own advertising
agencies — on a single sales order dated 30-Sep-2025, on **cash/advance, zero-day
payment terms**. Ten months later ₹3.11 Cr is still outstanding. The goods were
genuinely made (16 production orders, ~2.4 lakh cases in Sep–Nov 2025) and
genuinely dispatched, and ~₹1.04 Cr of GST and cess on those invoices has already
been paid to the government out of JIVO's own cash. This one account is 20% of the
Beverage Unit's entire last-12-month sales and is single-handedly why Beverages'
DSO is 108 days against Oil's 12 and Mart's 19.

The customer is not dead and not silent — it has been paying **exactly ₹5,83,330
every month since December 2025** (₹52.50 lakh collected, two payments as recently
as 23-Jul and 27-Jul-2026). But at that rate the balance takes **53 months to
clear**, JIVO charges no interest on it, and JIVO kept adding to it (a fresh
₹21.93 lakh invoice on 30-Jun-2026). Worse, the SAP credit limit on this customer
was set to **₹3.23 Cr** — 7.6× the next-largest external Beverages customer — and
the customer master was last updated on 30-Jun-2026, the very day the newest
invoice was raised. In other words the exposure was *authorised*, not accidental.
Separately, JIVO's Oil books owe the same company **₹29.66 lakh**, which has never
been paid and can be set off against the receivable immediately, because the
Beverage Unit and Oil are the same legal entity (JIVO Wellness Pvt Ltd) and
Blessing is the same counterparty on both sides (same Gurugram Sector-18 address).

## Verdict: REVISED — ₹3,10,92,246 (₹3.11 Cr)

The original finding's arithmetic is **exact** — I reproduced ₹289.00 lakh in the
181–365-day credit-adjusted bucket to the rupee. I have revised it because:

1. **The number should be ₹3.11 Cr, not ₹2.89 Cr (+7.6%).** Every invoice on this
   account carries payment terms `GroupNum = -1` = *ADVANCE/CASH/0 DAYS* and
   `DocDueDate = DocDate`. That makes the entire reconciled balance of
   ₹3,10,92,246 legally due today, including the ₹21.93 lakh June-2026 invoice
   that the 181–365 bucket excludes. ₹2.89 Cr is the correct *aged* slice; ₹3.11 Cr
   is the correct *collectible* figure.
2. **The evidence claim "nothing paid for 9-10 months" is wrong and the action
   built on it is wrong.** ₹52.50 lakh has been collected in ten monthly
   instalments of ₹5,83,330 (Dec-25 → Jul-26). A cold demand letter to a customer
   that is current on an agreed schedule is the wrong first move; the right move is
   to renegotiate and secure that schedule.
3. **The set-off is ₹29.66 lakh, not ₹26.26 lakh.** ₹26.26 lakh is the open A-P
   invoice total; `OCRD."Balance"` for the vendor is −₹29,65,533 because a
   migrated journal credit of ₹3,39,268 also sits there.
4. **"Stop paying the vendor side" is already the status quo** — `OVPM` shows
   **zero** outgoing payments to Blessing since SAP go-live. The action is to
   *formalise* the set-off, not to start withholding.

**Not refuted, and not a barter.** I tested the barter/media-credit hypothesis
hard and it fails: total advertising billed by Blessing to JIVO since go-live is
₹24.82 lakh against ₹8.98 Cr of total Oil advertising spend (2.8%) — there is no
₹3 Cr of media credit to offset. The ledger posts to `1101001 SUNDRY DEBTORS GT`
(ordinary general-trade debtors), not a contra or adjustment account, and the cash
that has come in arrived as bank transfers (`ORCT."TrsfrSum"`), not contra entries.

## Re-derived evidence

**1. The ledger reconciles to the rupee — the balance is real.**
```sql
SELECT (SELECT ROUND(SUM(CAST("DocTotal" AS DOUBLE))/100000,2) FROM JIVO_BEVERAGES_HANADB.OINV
        WHERE "CardCode"='CUSTA000175' AND "CANCELED"='N') INV_L,
       (SELECT ROUND(SUM(CAST("DocTotal" AS DOUBLE))/100000,2) FROM JIVO_BEVERAGES_HANADB.ORIN
        WHERE "CardCode"='CUSTA000175' AND "CANCELED"='N') CN_L,
       (SELECT ROUND(SUM(CAST("DocTotal" AS DOUBLE))/100000,2) FROM JIVO_BEVERAGES_HANADB.ORCT
        WHERE "CardCode"='CUSTA000175' AND "Canceled"='N') RCPT_L,
       (SELECT ROUND(SUM(CAST(IFNULL("OpenBal",0) AS DOUBLE))/100000,2) FROM JIVO_BEVERAGES_HANADB.ORCT
        WHERE "CardCode"='CUSTA000175' AND "Canceled"='N') UNAPPL_L,
       (SELECT ROUND(CAST("Balance" AS DOUBLE)/100000,2) FROM JIVO_BEVERAGES_HANADB.OCRD
        WHERE "CardCode"='CUSTA000175') OCRD_L,
       (SELECT ROUND(CAST("Balance" AS DOUBLE)/100000,2) FROM JIVO_OIL_HANADB.OCRD
        WHERE "CardCode"='VENDA001047') OIL_VENDOR_L
FROM DUMMY;
```
| INV_L | CN_L | RCPT_L | UNAPPL_L | OCRD_L | OIL_VENDOR_L |
|---:|---:|---:|---:|---:|---:|
| 367.05 | 3.63 | 52.50 | 23.33 | **310.92** | **−29.66** |

367.05 − 3.63 − 52.50 = **310.92** ✅ exact. No unapplied-cash illusion here
(trap #3 does not bite): the ₹23.33 lakh of unreconciled receipts is already
netted inside the ₹310.92 lakh balance.

**2. Credit-adjusted aging (oldest-first), independent of the lens query.**
```sql
WITH inv AS (SELECT "DocEntry","DocDueDate",CAST("DocTotal"-"PaidToDate" AS DOUBLE) OPENAMT
             FROM JIVO_BEVERAGES_HANADB.OINV
             WHERE "CardCode"='CUSTA000175' AND "CANCELED"='N' AND ("DocTotal"-"PaidToDate")>0),
r AS (SELECT i."DocEntry", DAYS_BETWEEN(i."DocDueDate",DATE'2026-07-28') AGE, i.OPENAMT,
             2342603.0 AS CREDIT,
             SUM(i.OPENAMT) OVER (ORDER BY i."DocDueDate", i."DocEntry"
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) CUM
      FROM inv i),
b AS (SELECT CASE WHEN AGE<=30 THEN 'B_1-30' WHEN AGE<=180 THEN 'E_91-180'
                  WHEN AGE<=365 THEN 'F_181-365' ELSE 'G_365+' END BUCKET,
             OPENAMT, GREATEST(0,LEAST(OPENAMT,CUM-CREDIT)) EFF FROM r)
SELECT BUCKET, COUNT(*) N, ROUND(SUM(OPENAMT)/100000,2) RAW_L, ROUND(SUM(EFF)/100000,2) EFF_L
FROM b GROUP BY BUCKET ORDER BY BUCKET;
```
| Bucket | N | Raw ₹L | Credit-adjusted ₹L |
|---|---:|---:|---:|
| 1–30 days | 1 | 21.93 | **21.93** |
| 181–365 days | 10 | 312.42 | **289.00** |
| | | | **310.93** |

₹289.00 lakh confirmed exactly. Total collectible **₹310.93 lakh**.

**3. The customer is paying — a fixed monthly instalment nobody flagged.**
```sql
SELECT "DocNum","DocDate","DocTotal","OpenBal","TrsfrSum"
FROM JIVO_BEVERAGES_HANADB.ORCT WHERE "CardCode"='CUSTA000175' ORDER BY "DocDate";
```
₹5,83,370 (30-Dec-25) · ₹58,330 + ₹5,25,000 (Jan-26) · ₹5,83,330 on 20-Feb ·
23-Mar · 22-Apr · 16-May · 16-Jun · **23-Jul** · **27-Jul-2026** = **₹52.50 lakh**,
all `TrsfrSum` (bank transfer). Implied run-off: 310.92 ÷ 5.8333 = **53 months**.

**4. The goods are real — this is not a paper sale.**
```sql
SELECT "DocNum","PostDate","PlannedQty","CmpltQty" FROM JIVO_BEVERAGES_HANADB.OWOR
WHERE "ItemCode"='FG0000273' ORDER BY "PostDate";
SELECT "TransType",SUM(CAST("OutQty" AS DOUBLE)) OUTQ FROM JIVO_BEVERAGES_HANADB.OINM
WHERE "ItemCode"='FG0000273' GROUP BY "TransType";
```
16 production orders for `FG0000273 GLASS BOTTLE 200 MLS TONIC WATER 12 PCS`,
~2,39,528 cases completed Sep–Nov 2025 — a dedicated campaign timed to this order.
`OINM` TransType 13 (A/R invoice) shows 2,66,865 cases physically issued. Closing
stock is 124. Blessing took **2,49,102 cases** across 12 invoices.

**5. Margin and cash already sunk.**
```sql
SELECT SUM(CAST(l."LineTotal" AS DOUBLE)) NET, SUM(CAST(l."GrssProfit" AS DOUBLE)) GP
FROM JIVO_BEVERAGES_HANADB.INV1 l JOIN JIVO_BEVERAGES_HANADB.OINV h ON h."DocEntry"=l."DocEntry"
WHERE h."CardCode"='CUSTA000175' AND h."CANCELED"='N';
```
Net ₹2,62,17,986 · COGS ₹33,12,176 · **gross profit ₹2,28,93,898 (87.3%)**. Blessing
pays ₹105.25/case where domestic wholesale is ₹41–46 and JIVO Mart pays ₹21–37 —
a deliberately premium, export-channel-flavoured deal (the 30-Jun-26 invoice
carries a "resell overseas only" clause). Two consequences: (a) ₹2.29 Cr of
Beverages' booked gross profit is unrealised cash sitting in one debtor, and
(b) JIVO's hard cash out of pocket is only ~₹1.38 Cr (₹33 lakh COGS + ~₹1.04 Cr
GST/cess remitted) against ₹52.50 lakh collected — but the ₹3.11 Cr is what is
financed on the cash-credit line.

**6. The credit limit was engineered around the exposure.**
```sql
SELECT "CardCode","CardName","CreditLine","Balance" FROM JIVO_BEVERAGES_HANADB.OCRD
WHERE "CardType"='C' ORDER BY "CreditLine" DESC LIMIT 5;
```
| Customer | Credit line | Balance |
|---|---:|---:|
| **BLESSING ADVERTISING PVT LTD** | **₹3,22,68,190** | ₹3,10,92,246 |
| VARNAY CO GOODS WHOLESALERS LLC | ₹42,70,200 | −₹13,50,281 |
| JIVO MART PVT LTD | ₹25,00,000 | ₹6,07,562 |
| GAGANDEEP SINGH | ₹12,00,000 | ₹9,54,491 |

The limit sits ₹11.76 lakh above the balance, and `OCRD."UpdateDate"` = 2026-06-30,
the same day the ₹21.93 lakh invoice was raised. SAP's credit block was moved, not
respected.

**7. Same-entity set-off is legally clean.**
`OADM."CompnyName"`: Oil = `JIVO WELLNESS PVT LTD`, Beverages =
`(BEVERAGE UNIT) JIVO WELLNESS PVT LTD` — one legal entity, one PAN. `CRD1` shows
Bev `CUSTA000175` and Oil `VENDA001047` at the same **Gurugram, Sector 18, 122001**
address — one counterparty. Mutual debts, so set-off is available without consent
under ordinary contract principles (a signed set-off letter is still advisable).
Oil A-P detail: ₹1,43,787 + ₹68 (both migrated 30-Sep-2024) + ₹24,82,410
(01-Jun-2026, GL `5640001 ADVERTISEMENT`) + ₹3,39,268 migrated JE credit =
**₹29,65,533**.

## What is bankable

| Tier | Amount | Certainty |
|---|---:|---|
| Same-entity set-off against Oil A-P (execute this week) | **₹29,65,533** | Certain — JIVO controls both sides |
| Already contracted instalments (₹5.83 L × 12) | ₹69,99,960/yr | Flowing, **not incremental** |
| Balance requiring renegotiation / security | ₹2,81,26,713 | Commercial |
| **Total working-capital exposure to release** | **₹3,10,92,246** | |

At the verified 7.3% cash-credit borrowing rate, carrying this account costs JIVO
**₹22,69,734 per year** in interest it never bills back. JIVO has never raised a
rupee of late-payment interest on any customer ([[receivables-aging]] H12); at a
standard 18% overdue clause this account alone would carry ~₹56 lakh/yr.

## Action

**Owner: CFO (decision) → Accounts (execution) → Sales head (supply control)**

1. **CFO first, before anything is sent.** The ₹3.23 Cr credit line and the
   30-Jun-2026 master update prove this exposure was authorised. Confirm in writing
   whether an instalment agreement, a security, or an export-channel arrangement
   exists before Accounts issues any notice. *(This is the one step that must not be
   skipped.)*
2. **Accounts — execute the ₹29,65,533 set-off this week.** Issue a set-off letter
   covering Oil A-P `VENDA001047` (₹26,26,265 open + ₹3,39,268 migrated credit)
   against Beverages A-R `CUSTA000175`. Zero collection effort, same PAN, same
   counterparty. Do **not** pay the 01-Jun-2026 ₹24.82 lakh advertising bill in cash.
3. **Accounts — reconcile the ₹23,33,320 of unapplied receipts** (`ORCT."OpenBal"`
   on the last four instalments) against the oldest open invoices, so the aging
   report stops lying about this account.
4. **CFO/Accounts — convert the informal ₹5.83 lakh/month drip into a written
   settlement**: shortened tenor (12–18 months, not 53), post-dated cheques or a
   bank guarantee, and an 18% p.a. interest clause on any slippage.
5. **Sales head — freeze further supply.** Reset `OCRD."CreditLine"` from ₹3.23 Cr
   to the ₹42.70 lakh band used for every other external Beverages customer, and
   require advance payment for any new order. Lock credit-limit changes to CFO
   approval (IT to restrict the authorisation in SAP).
6. **Accounts — no bad-debt provision exists** (`OACT 5680009` in Beverages = ₹0).
   If the settlement is not signed within 60 days, raise a provision, because ₹2.29
   Cr of Beverage Unit gross profit currently rests on this single debtor.

## Overlaps — do not double count

- **[[finding-contra-adagency-30L]]** — its Blessing component (₹26.26 lakh of the
  ₹30.37 lakh three-way contra) is **inside** this ₹3.11 Cr, not additional. Setting
  off *reduces* this receivable. Only the Media Mind (₹2.60 lakh) and Idea Publicity
  (₹1.51 lakh) legs of that finding are incremental to this one.
- **[[finding-ar-reconciliation-backlog]]** — the ₹23,33,320 of unapplied receipts on
  this account is a subset of the group-wide ₹143.23 Cr unreconciled-cash figure.
- **[[receivables-aging]] H5** — this ₹2.89 Cr is the largest single line of the
  ₹7.26 Cr external 60+ overdue total; do not add it on top of that total.
- No overlap with [[finding-ab-enterprises-going-bad]], [[finding-bsa-engineering-116L]]
  or [[finding-future-retail-writeoff-tax]] — different counterparties, different
  companies.
