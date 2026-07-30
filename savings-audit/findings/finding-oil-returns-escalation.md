---
title: "Oil third-party returns ₹3.56 Cr above a 5% allowance — REFUTED as money, the rate trend is real"
created: 2026-07-28
verdict: REFUTED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding, returns, credit-notes, sap-b1, oil]
---

# Oil third-party returns escalation — verification of rank #14

Part of [[SAVINGS-MOC]] · Evidence: [[returns-leakage]]

**Verdict: REFUTED as a saving — ₹3.56 Cr → ₹0 bankable.**
The finder's arithmetic replicates to the rupee. The *money* does not exist, and the three
customers named as the worst offenders are not return offenders at all. What survives is a
genuine control finding about **billing discipline and salesperson attribution**, not a
distributor-returns problem.

**Window:** 2025-07-28 → 2026-07-29, `JIVO_OIL_HANADB`, `"CANCELED"='N'`, excluding related
party `CUSTA000606` (JIVO MART). **Tool:** `hana-sql` (read-only SELECT).

---

## Plain-language summary for the CFO

Someone looked at JIVO Oil's books and found that, once you strip out the sister company,
customers sent back ₹9.70 Cr of goods against ₹280.49 Cr of sales — 3.5% — and that if every
distributor were held to a 5% return cap, ₹3.56 Cr a year would come back to us. It sounded
alarming: the rate has genuinely tripled in two years, and names like R K Worldinfocom (67%
returns), Kailian Foods (47%) and Comed Chemicals (33%) looked like distributors dumping stock
back on us.

They are not. When you open the actual documents, the pattern for every one of those accounts is
the same: **we raise an invoice, cancel the whole invoice with a credit note a few days later,
and then raise the identical invoice again.** R K Worldinfocom was billed ₹3.33 lakh + ₹15.87
lakh on 12 Nov, credited the exact same two amounts on 13 Nov, re-billed on 29 Nov, credited
again on 13 Dec, and re-billed on 21 Jan. That is the *same one consignment* being documented
five times — it shows up in SAP as three "sales" and two "returns" when in truth no goods ever
came back and no rupee was ever lost. Comed Chemicals is a 31-March invoice reversed on 6 April
and re-billed on 10 April — a year-end cut-off correction. Kailian is the same at month-end.

Across the whole Oil book, 91% of the credit notes that carry an invoice link reverse **100% of
an entire invoice** — genuine damaged-goods returns are partial, and partial credits total only
₹0.39 Cr. On top of that, ₹1.42 Cr of what was counted as "returns" is not a return at all: it is
promotional discount, Diwali gifts and free samples booked as service-type credit notes — money
already claimed by a separate finding.

Strip out the billing churn and the promo spend and JIVO Oil's real third-party return rate is
**1.17%**, which is healthy for edible oil. The genuine excess above a 5% allowance is **₹0.31
Cr of reversed revenue** — and reversed revenue is not cash. The goods go back into stock and get
sold to someone else, so the real cost is margin plus a return truck, roughly **₹5 lakh a year**.
Below materiality.

Two things in the original finding are true and worth acting on: the return rate really has
roughly tripled in two years, and **62% of return documents have no salesperson attached**, so
returns can never be netted off sales incentives today. Both are billing-discipline fixes that
cost nothing.

---

## V1 — Does the headline replicate? Yes, exactly

```sql
SELECT ROUND(SUM(S)/10000000,3) AS SALES_CR, ROUND(SUM(R)/10000000,3) AS RET_CR,
       ROUND(100*SUM(R)/SUM(S),2) AS RATE,
       ROUND(SUM(GREATEST(0, R - S*0.05))/10000000,3) AS EXC5_CR,
       ROUND(SUM(GREATEST(0, R - S*0.03))/10000000,3) AS EXC3_CR
FROM ( SELECT CC, SUM(S) AS S, SUM(R) AS R FROM (
         SELECT "CardCode" AS CC, CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE) AS S, 0.0 AS R
         FROM JIVO_OIL_HANADB.OINV
         WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
           AND "CardCode"<>'CUSTA000606' GROUP BY "CardCode"
         UNION ALL
         SELECT "CardCode", 0.0, CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)
         FROM JIVO_OIL_HANADB.ORIN
         WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
           AND "CardCode"<>'CUSTA000606' GROUP BY "CardCode" )
       GROUP BY CC HAVING SUM(S)>0 )
```

| SALES_CR | RET_CR | RATE | EXC5_CR | EXC3_CR |
|---:|---:|---:|---:|---:|
| 280.493 | 9.704 | 3.46% | **3.558** | 4.895 |

Replicates to three decimals. The arithmetic is not in dispute. Credit to the finder.

---

## V2 — Trap #4: ₹1.42 Cr of the "returns" are trade spend, not returns

```sql
SELECT "DocType", COUNT(*) AS DOCS,
       ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/10000000,3) AS CR
FROM JIVO_OIL_HANADB.ORIN
WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
  AND "CardCode"<>'CUSTA000606'
GROUP BY "DocType"
```

| DocType | Docs | ₹ Cr |
|---|---:|---:|
| `I` goods returns | 1,640 | 8.318 |
| **`S` service credits** | 240 | **1.419** |

Line detail of the `S` credits: PROMOTIONAL DISCOUNT ₹129.10 L, DIWALI GIFT ₹6.66 L, RENT
RECEIVED ₹1.60 L, SAMPLE/FOC ₹2.5 L. **Not returns.** Already booked as
[[finding-trade-spend-as-credit-notes]] — counting it here is a direct double count.

Sales also carry service-type invoices (₹4.577 Cr). Like-for-like, goods-only:

| Basis | Sales | Returns | Rate | Excess >5% |
|---|---:|---:|---:|---:|
| All doc types (as claimed) | ₹280.49 Cr | ₹9.704 Cr | 3.46% | ₹3.558 Cr |
| **Goods only (`DocType='I'` both sides)** | ₹275.92 Cr | ₹8.290 Cr | **3.00%** | **₹2.516 Cr** |

**₹1.04 Cr (29%) of the claimed excess is promotional spend.**

---

## V3 — THE KILLER: 91% of linked credit notes reverse an ENTIRE invoice

Genuine returns are partial (a few damaged cases). Full-value reversals are billing corrections.

```sql
SELECT BUCKET, COUNT(*) AS CRN, ROUND(SUM(V)/10000000,3) AS CR
FROM ( SELECT c."DocEntry", CAST(c."DocTotal"-IFNULL(c."VatSum",0) AS DOUBLE) AS V,
              CASE WHEN SUM(l."LineTotal") >= 0.995*MAX(iv.NET)
                   THEN 'a FULL_INVOICE_REVERSAL' ELSE 'b partial' END AS BUCKET
       FROM JIVO_OIL_HANADB.ORIN c
       JOIN JIVO_OIL_HANADB.RIN1 l ON l."DocEntry"=c."DocEntry" AND l."BaseType"=13
       JOIN ( SELECT "DocEntry", CAST("DocTotal"-IFNULL("VatSum",0) AS DOUBLE) AS NET
              FROM JIVO_OIL_HANADB.OINV ) iv ON iv."DocEntry"=l."BaseEntry"
       WHERE c."CANCELED"='N' AND c."DocType"='I'
         AND c."DocDate">='2025-07-28' AND c."DocDate"<'2026-07-29'
         AND c."CardCode"<>'CUSTA000606'
       GROUP BY c."DocEntry",c."DocTotal",c."VatSum" )
GROUP BY BUCKET ORDER BY BUCKET
```

| Bucket | Docs | ₹ Cr |
|---|---:|---:|
| **Full reversal of the entire base invoice** | 101 | **4.132** |
| partial credit (what a real return looks like) | 279 | 0.394 |

**91% of linked credit-note value cancels a whole invoice.** And of that ₹4.13 Cr, ₹1.34 Cr is
provably **re-billed** — an identical-value invoice to the same customer within 60 days:

```sql
-- full-invoice reversals, then look for a same-value re-invoice AFTER the credit note
LEFT JOIN JIVO_OIL_HANADB.OINV r
       ON r."CardCode"=c."CardCode" AND r."CANCELED"='N'
      AND r."DocDate">c."DocDate" AND DAYS_BETWEEN(c."DocDate",r."DocDate")<=60
      AND ABS((r."DocTotal"-IFNULL(r."VatSum",0))-(c."DocTotal"-IFNULL(c."VatSum",0)))
          < 0.01*(c."DocTotal"-IFNULL(c."VatSum",0))
```

| | Docs | ₹ Cr |
|---|---:|---:|
| **reversed then re-billed** (pure paperwork, zero goods movement) | 23 | **1.336** |
| reversed, not re-billed (a *cancelled sale* — stock never left / came back whole) | 78 | 2.796 |

Neither category is a "return above allowance". A 5% return cap recovers nothing from either:
the first never involved goods, and in the second the stock is still ours to sell.

An independent test agrees. Credit notes with an **exact-value** invoice to the same customer
within ±30 days (`ABS(diff) < 0.1%`):

| | Docs | ₹ Cr |
|---|---:|---:|
| mirrored within 7 days | 168 | 3.729 |
| mirrored 8–30 days | 97 | 1.320 |
| **no mirror (candidate genuine returns)** | 921 | **3.247** |

---

## V4 — The named "worst offenders" are billing cycles, not return offenders

Actual document trails (`OINV` ∪ `ORIN`, `"CANCELED"='N'`):

**R K WORLDINFOCOM (CUSTA000048) — cited at 66.7%**

| Date | Doc | ₹ lakh |
|---|---|---:|
| 2025-11-12 | INV | 3.33 + 15.87 |
| 2025-11-13 | **CRN** | **3.33 + 15.87** |
| 2025-11-29 | INV | 15.87 + 3.33 |
| 2025-12-13 | **CRN** | **15.87 + 3.33** |
| 2026-01-21 | INV | 3.33 + 15.87 |

The same two amounts billed → credited → re-billed → credited → re-billed. One consignment,
five documents. The ₹38.4 lakh of "returns" is ₹19.2 lakh of goods counted twice.

**COMED CHEMICALS (CUSTA000437) — cited at 33.1%:** INV ₹3.64 L + ₹8.62 L on **31-Mar-2026** →
CRN ₹3.64 L + ₹8.62 L on 06-Apr → INV ₹24.76 L on 10-Apr. A **financial-year cut-off correction**.

**KAILIAN FOODS (CUSTA001068) — cited at 46.9%:** INV ₹8.19 L ×2 on **31-Aug** → CRN ₹8.19 L ×2
on 02-Sep → INV ₹8.19 L on 06-Sep. Repeats at 31-Dec → 07-Jan. **Month-end cut-off**, every time.

**CHAUDHARY MARKETING (100%):** 2 invoices dated 30-Sep-2025 (₹15.67 L, ₹11.08 L), both credited
in full on 04-Oct-2025 for the identical amounts. **DIN DAYAL DULI CHAND (100.1%):** CRN ₹7.98 L
08-Oct → INV ₹7.98 L 15-Oct; CRN ₹6.90 L 17-Nov → INV ₹6.90 L 17-Nov (same day). Re-billing.

⚠️ **Putting these five accounts on a distributor return league table would be a false
accusation** of both the distributors and the sales team. This also refutes
[[finding-total-reversal-accounts]] (Chaudhary + Din Dayal, ₹49.62 lakh).

---

## V5 — Re-derived: genuine excess over a 5% allowance = ₹0.31 Cr

Same per-customer `GREATEST(0, R − S×0.05)` shape, but returns = goods-only credit notes with
**no** exact-value mirror invoice within ±30 days:

| SALES_CR | GENUINE_RET_CR | RATE | EXC5_CR | EXC3_CR |
|---:|---:|---:|---:|---:|
| 275.916 | 3.232 | **1.17%** | **0.312** | 0.494 |

Full decomposition of the ₹9.704 Cr (additive):

| Component | ₹ Cr | Whose finding |
|---|---:|---|
| Service credits — promo discount, Diwali gifts, FOC samples | 1.42 | [[finding-trade-spend-as-credit-notes]] |
| Full-invoice reversal, re-billed within 60d (paperwork) | 1.34 | billing control |
| Full-invoice reversal, not re-billed (cancelled sale) | 2.80 | billing control |
| Partial credit against a linked invoice (**real returns**) | 0.39 | this note |
| Goods credit notes with no invoice link at all | 3.76 | [[finding-unlinked-credit-notes]] |
| **Total** | **9.70** | |

Top genuine offenders after cleaning — a short, honest list:

| Customer | Sales ₹L | Genuine ret ₹L | Rate | Excess >5% ₹L |
|---|---:|---:|---:|---:|
| JIOMART LUHARI Q1 | 95.42 | 14.18 | 14.9% | 9.41 |
| ONENESS TRADERS | 393.01 | 28.34 | 7.2% | 8.68 |
| MAKKAR GENERAL STORE | 25.91 | 4.86 | 18.7% | 3.56 |
| MORE RETAIL | 7.68 | 1.85 | 24.1% | 1.46 |

(JIOMART is a single card code — no split-code artefact; its 449 documents are modern-trade
reconciliation churn.)

**Why ₹0.31 Cr is still not ₹0.31 Cr of cash:** it is reversed *revenue*. `OITM."AvgPrice"` is
**0.00 for all 2,268 Oil items**, so SAP cannot report margin; the sibling verification measured
Mart's true gross margin at 8.36%. Returned goods re-enter stock (`"UpdInvnt"='I'` on every
`ORIN`) and are re-sold, so the economic loss is margin + a return truck ≈ **₹5 lakh/yr**. Below
materiality. **Bankable = ₹0.**

---

## V6 — What DOES survive

**✅ The trend is real (CONFIRMED).** Ex-intercompany, by financial year:

| Period | Sales ₹Cr | Goods ret ₹Cr | Svc credits ₹Cr | Rate (all) | Rate (goods) |
|---|---:|---:|---:|---:|---:|
| FY24-25 | 258.27 | 3.352 | 1.091 | **1.72%** | 1.30% |
| FY25-26 | 321.77 | 8.264 | 1.245 | **2.96%** | 2.57% |
| FY26-27 YTD | 71.87 | 2.862 | 0.223 | **4.29%** | 3.98% |

Matches the claim (1.7 → 3.0 → 4.3) and survives the goods-only recut (1.30 → 2.57 → 3.98).
But splitting it by cause changes the diagnosis entirely:

| Period | Churn (mirrored) % of sales | Genuine returns % of sales |
|---|---:|---:|
| FY24-25 | 1.02% | 0.58% |
| FY25-26 | 1.75% | 0.84% |
| FY26-27 YTD | 1.87% | **2.18%** |

Rising churn is the larger share of the deterioration for two of three years. **This is a billing
problem before it is a distributor problem.** (Caveat: FY24-25 carried 10,776 service-type
invoices worth ₹49.76 Cr vs 233 / ₹3.40 Cr in FY25-26 — a big booking-practice change, so
all-doc-type FY comparisons are unsafe; use the goods-only row.)

**✅ Salesperson attribution gap (CONFIRMED to the rupee).**

```sql
SELECT IFNULL(s."SlpName",'(null)') AS REP, COUNT(*) AS DOCS,
       ROUND(CAST(SUM(h."DocTotal"-IFNULL(h."VatSum",0)) AS DOUBLE)/10000000,3) AS RET_CR
FROM JIVO_OIL_HANADB.ORIN h
LEFT JOIN JIVO_OIL_HANADB.OSLP s ON s."SlpCode"=h."SlpCode"
WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
  AND h."CardCode"<>'CUSTA000606'
GROUP BY IFNULL(s."SlpName",'(null)') ORDER BY 3 DESC
```

`-No Sales Employee / Buyer-`: **817 docs, ₹6.037 Cr = 62.2%** of returns. Exactly as claimed.
Returns cannot feed any incentive scheme today.

**⚠️ New risk the finder did not raise — GST exposure.** 23 credit notes worth ₹1.34 Cr reverse
an invoice and are re-billed, several across GST return periods and one across the 31-Mar-2026
year end (Comed). Credit notes must be declared in GSTR-1 and are time-barred under s.34(2) after
30 November following the financial year. This churn is a compliance item, not a savings item.

---

## Action

| # | Action | Owner |
|---|---|---|
| 1 | **Do NOT issue a 5% return allowance or a distributor league table on these numbers.** The top five "offenders" are our own billing corrections; the policy would penalise blameless distributors. | Sales head / CFO |
| 2 | **Fix the root cause: stop cancel-and-rebill.** ₹4.13 Cr/yr of credit notes cancel a whole invoice; ₹1.34 Cr is re-billed. Find why (e-way bill / GSTIN / rate errors caught after despatch), and require a named approver for any credit note ≥ 95% of its base invoice. | Accounts + IT |
| 3 | **Make `SlpCode` mandatory on `ORIN`** (SAP B1 user-defined validation). Zero cost, removes the 62% blind spot, and is the precondition for ever netting returns off incentives. | IT |
| 4 | **Report returns as two separate KPIs** — "goods returned" (`DocType='I'`, partial credits) vs "invoices cancelled" — so the board sees a 1.17% return rate and a separate billing-error rate, not a misleading blended 3.5%. | Accounts |
| 5 | **Two real conversations only:** JIOMART LUHARI (14.9%) and ONENESS TRADERS (7.2%) — ₹18 lakh of combined excess revenue, worth a commercial discussion, not a policy. | Sales head |
| 6 | **Review the 23 cross-period credit-then-rebill cycles for GSTR-1 exposure** before 30-Nov-2026. | CFO |
| 7 | **Populate `OITM` standard costs** (all 2,268 items are ₹0) so returns can ever be measured in margin rather than revenue. | Accounts + IT |

**Working-capital interest at 7.3%: not applicable** — this is a P&L/control finding, not a
working-capital release. No cash is freed.

---

## Overlaps — do not add these together

- **[[finding-trade-spend-as-credit-notes]]** — ₹1.42 Cr of the ₹9.70 Cr counted here is that
  finding's promotional spend. Direct double count.
- **[[finding-unlinked-credit-notes]]** — ₹3.76 Cr of the same rupees.
- **[[finding-excess-returns-above-benchmark]]** — this note IS the Oil half of it (₹3.56 Cr of
  its ₹13.47 Cr); the Mart half is verified separately in [[verify-04-mart-return-rate]].
- **[[finding-return-rate-deterioration]]** — same trend rows; confirmed here as a control
  observation with ₹0 attached.
- **[[finding-total-reversal-accounts]]** — refuted by V4 above (both accounts are re-billing).

Back-links: [[SAVINGS-MOC]] · [[returns-leakage]] · [[2026-07-28]]
