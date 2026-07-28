---
title: "Receivables aging — overdue A/R and the interest it costs"
created: 2026-07-28
lens: receivables-aging
tags: [savings-audit]
---

# Receivables aging — overdue A/R + interest cost

Part of [[SAVINGS-MOC]]

**Scope:** all three SAP companies — `JIVO_OIL_HANADB` (JIVO Wellness Pvt Ltd),
`JIVO_MART_HANADB` (JIVO Mart Pvt Ltd), `JIVO_BEVERAGES_HANADB` (Beverage Unit,
JIVO Wellness Pvt Ltd). As-of date **2026-07-28**. SAP go-live **2024-09-30**
(everything dated 2024-09-30 is a migrated opening balance).

## Headline

| Measure | Oil | Mart | Bev | Group |
|---|---:|---:|---:|---:|
| Open A-R invoices (raw, `DocStatus`='O') | ₹181.23 Cr | ₹108.94 Cr | ₹7.05 Cr | **₹297.22 Cr** |
| Customer debit balances (`OCRD.Balance`>0) | ₹109.99 Cr | ₹24.04 Cr | ₹4.66 Cr | ₹138.69 Cr |
| … of which branch / intra-group | ₹101.51 Cr | ₹13.89 Cr | ₹0.84 Cr | ₹116.24 Cr |
| **External trade debtors** | **₹8.47 Cr** | **₹10.15 Cr** | **₹3.82 Cr** | **₹22.44 Cr** |
| **External overdue 60+ days** | **₹3.97 Cr** | **₹0.26 Cr** | **₹3.03 Cr** | **₹7.26 Cr** |
| % of external book 60+ overdue | 47% | 3% | 79% | 32% |
| Unapplied customer receipts (`ORCT.OpenBal`) | ₹71.00 Cr | ₹70.02 Cr | ₹2.21 Cr | **₹143.23 Cr** |

The raw SAP aging report is **unusable**: ₹297 Cr of "open" invoices against
₹138.69 Cr of actual customer debit, because ₹143.23 Cr of received cash and
₹12.24 Cr of credit notes were never internally reconciled. Every number in this
note is **credit-adjusted** (unapplied receipts applied oldest-invoice-first)
before aging.

---

## H1 — Raw aging buckets by due date (all 3 companies)

```sql
SELECT CASE WHEN DAYS_BETWEEN("DocDueDate", DATE'2026-07-28') <= 0   THEN 'A_notdue'
            WHEN DAYS_BETWEEN("DocDueDate", DATE'2026-07-28') <= 30  THEN 'B_1-30'
            WHEN DAYS_BETWEEN("DocDueDate", DATE'2026-07-28') <= 60  THEN 'C_31-60'
            WHEN DAYS_BETWEEN("DocDueDate", DATE'2026-07-28') <= 90  THEN 'D_61-90'
            WHEN DAYS_BETWEEN("DocDueDate", DATE'2026-07-28') <= 180 THEN 'E_91-180'
            WHEN DAYS_BETWEEN("DocDueDate", DATE'2026-07-28') <= 365 THEN 'F_181-365'
            ELSE 'G_365+' END AS BUCKET,
       COUNT(*) AS N,
       ROUND(SUM(CAST("DocTotal"-"PaidToDate" AS DOUBLE))/10000000,2) AS OPEN_CR
FROM JIVO_OIL_HANADB.OINV
WHERE "DocStatus"='O' AND "CANCELED"='N'
GROUP BY 1 ORDER BY 1;
```

| Bucket | Oil N / ₹Cr | Mart N / ₹Cr | Bev N / ₹Cr |
|---|---:|---:|---:|
| not due | 129 / 2.91 | 2 / 0.01 | 42 / 0.03 |
| 1-30 | 299 / 29.82 | 878 / 16.70 | 274 / 0.86 |
| 31-60 | 208 / 3.72 | 331 / 10.87 | 215 / 0.60 |
| 61-90 | 181 / 3.40 | 243 / 7.70 | 64 / 0.13 |
| 91-180 | 924 / 6.80 | 579 / 23.77 | 116 / 0.39 |
| 181-365 | 1,814 / 27.66 | 822 / 31.77 | 156 / 3.60 |
| 365+ | 9,236 / 106.91 | 2,041 / 18.11 | 284 / 1.44 |

**Verdict: DO NOT USE.** ₹181 Cr "overdue" in Oil against ₹193.91 Cr of FY25-26
turnover would be a 341-day DSO — impossible. Something is wrong with the
document status, not with collections. → H2.

---

## H2 — Why the raw aging lies: unapplied receipts + unapplied credit notes

```sql
SELECT "DocType","Canceled", COUNT(*) AS N,
       ROUND(SUM(CAST("DocTotal" AS DOUBLE))/10000000,2) AS TOT_CR,
       ROUND(SUM(CAST(IFNULL("OpenBal",0) AS DOUBLE))/10000000,2) AS OPENBAL_CR
FROM JIVO_OIL_HANADB.ORCT GROUP BY "DocType","Canceled";

SELECT COUNT(*) N, ROUND(SUM(CAST("DocTotal"-"PaidToDate" AS DOUBLE))/100000,2) OPEN_L,
       MIN("DocDate") OLDEST
FROM JIVO_OIL_HANADB.ORIN WHERE "DocStatus"='O' AND "CANCELED"='N';
```

| Company | Customer receipts total | **Unapplied (`OpenBal`)** | Unapplied credit notes |
|---|---:|---:|---:|
| Oil | ₹839.64 Cr | **₹71.00 Cr** (1,902 docs >365 d old = ₹44.85 Cr) | ₹1.23 Cr (1,685 docs) |
| Mart | ₹250.00 Cr | **₹70.02 Cr** | ₹10.95 Cr (497 docs) |
| Bev | ₹17.78 Cr | **₹2.21 Cr** | ₹0.07 Cr (49 docs) |
| **Group** | | **₹143.23 Cr** | **₹12.24 Cr** |

Reconciliation check (Oil): open invoices ₹181.23 Cr − unapplied receipts
₹71.00 Cr − unapplied credit notes ₹1.23 Cr ≈ ₹109.00 Cr ≈ `OCRD` debit
₹109.99 Cr. ✅ The model holds.

Proof by example — customers whose cash is fully in the bank but never matched:

```sql
SELECT c."CardCode", c."CardName", ROUND(CAST(c."Balance" AS DOUBLE)/100000,2) BAL_L,
  ROUND((SELECT SUM(CAST(i."DocTotal"-i."PaidToDate" AS DOUBLE)) FROM JIVO_OIL_HANADB.OINV i
         WHERE i."CardCode"=c."CardCode" AND i."DocStatus"='O' AND i."CANCELED"='N')/100000,2) OPEN_INV_L
FROM JIVO_OIL_HANADB.OCRD c WHERE c."CardCode" IN ('CUSTA000908','CUSTA000341','CUSTA000907','CUSTA000873');
```

| Customer | `OCRD.Balance` | Open invoices | Unapplied receipts |
|---|---:|---:|---:|
| ABU DHABI VEGETABLE OIL COMPANY LLC | ₹0 | ₹13.28 Cr | ₹13.26 Cr |
| LEGACY COMMODITIES PVT LTD | ₹0 | ₹8.66 Cr | ₹8.65 Cr |
| QATAR LUBRICANTS COMPANY | ₹0 | ₹7.18 Cr | ₹7.19 Cr |
| AMAZON | ₹0 | ₹1.51 Cr (3,061 invoices!) | ₹0.92 Cr |
| R K WORLDINFOCOM (Mart) | ₹8.63 Cr | — | **₹59.81 Cr across 658 receipts** |

**Verdict: CONFIRMED — [[finding-ar-reconciliation-backlog]].** ₹143.23 Cr of
customer money is banked but not knocked off. Nobody in Accounts can produce a
usable overdue list, which is exactly why the ₹7.26 Cr below is uncollected.

---

## H3 — Branch / intra-group accounts are not receivables at all

```sql
SELECT g."GroupName", COUNT(*) N, ROUND(SUM(CAST(c."Balance" AS DOUBLE))/100000,2) BAL_L
FROM JIVO_OIL_HANADB.OCRD c JOIN JIVO_OIL_HANADB.OCRG g
  ON g."GroupCode"=c."GroupCode" AND g."GroupType"=c."CardType"
WHERE g."GroupName" LIKE '%BRANCH%' GROUP BY g."GroupName";
```

| Company | BRANCH CUSTOMER (Dr) | BRANCH VENDOR (Cr) | Net |
|---|---:|---:|---:|
| Oil | +₹77.52 Cr | −₹77.54 Cr | −₹0.02 Cr |
| Mart | +₹6.88 Cr | −₹6.64 Cr | +₹0.24 Cr |
| Bev | +₹0.78 Cr | −₹0.79 Cr | −₹0.01 Cr |

`OADM.CompnyName` for Oil = **JIVO WELLNESS PVT LTD**, and the top four "customers"
are `JIVO WELLNESS PVT LTD - PB / DL / HR / DL-ISD` (₹56.10 Cr + ₹13.03 Cr +
₹6.47 Cr + ₹1.92 Cr) — the company's own state GST registrations. They net to
zero against the mirror BRANCH VENDOR accounts.

**Verdict: NOT A LEAK, but a reporting distortion.** ₹116.24 Cr of the ₹138.69 Cr
"debtors" is branch/intra-group. Excluded from every figure below.

---

## H4 — Credit-adjusted aging, branch vs external trade

Method: per customer, unapplied credit = Σ(open invoices) − max(0, `OCRD.Balance`);
apply it to the **oldest** invoices first with a HANA window function, then age the
remainder.

```sql
WITH inv AS (
  SELECT i."CardCode", i."DocEntry", i."DocDueDate",
         CAST(i."DocTotal"-i."PaidToDate" AS DOUBLE) AS OPENAMT
  FROM JIVO_OIL_HANADB.OINV i
  WHERE i."DocStatus"='O' AND i."CANCELED"='N' AND (i."DocTotal"-i."PaidToDate")>0),
tot AS (SELECT "CardCode", SUM(OPENAMT) TOTOPEN FROM inv GROUP BY "CardCode"),
bal AS (SELECT "CardCode","GroupCode", CAST("Balance" AS DOUBLE) BAL
        FROM JIVO_OIL_HANADB.OCRD WHERE "CardType"='C'),
cr  AS (SELECT t."CardCode", IFNULL(b."GroupCode",0) GRP,
          GREATEST(0, t.TOTOPEN - GREATEST(0, IFNULL(b.BAL,t.TOTOPEN))) CREDIT
        FROM tot t LEFT JOIN bal b ON b."CardCode"=t."CardCode"),
r AS (SELECT i.*, c.CREDIT, c.GRP,
        SUM(i.OPENAMT) OVER (PARTITION BY i."CardCode"
          ORDER BY i."DocDueDate", i."DocEntry"
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) CUM
      FROM inv i JOIN cr c ON c."CardCode"=i."CardCode")
SELECT /* bucket */, CASE WHEN GRP=100 THEN 'BRANCH' ELSE 'TRADE' END KIND,
       ROUND(SUM(GREATEST(0, LEAST(OPENAMT, CUM - CREDIT)))/100000,2) OPEN_L
FROM r GROUP BY 1,2;
```

Result (₹ lakh, effective open after credit application):

| Bucket | Oil BRANCH | Oil TRADE | Mart BRANCH | Mart TRADE | Bev BRANCH | Bev TRADE |
|---|---:|---:|---:|---:|---:|---:|
| not due | – | 229.74 | – | 0.03 | – | 2.89 |
| 1-30 | 0.73 | 2,501.04 | 26.41 | 932.40 | 0.31 | 59.45 |
| 31-60 | 2.30 | 48.77 | 13.99 | 248.31 | 1.28 | 6.18 |
| **61-90** | 2.32 | **10.83** | 7.60 | – | 0.67 | **4.13** |
| **91-180** | 231.90 | **124.93** | 157.07 | **8.98** | 6.41 | **9.35** |
| **181-365** | 1,741.18 | **146.58** | 19.00 | **12.25** | 12.25 | **297.56** |
| **365+** | 5,773.73 | **119.35** | 225.23 | **6.74** | 57.13 | **7.40** |

Note: Mart's `JIVO MART PVT LTD - DL` (₹10.22 Cr) and `- ISD - DL` (₹1.60 Cr) are
branch accounts *not* tagged to group 100, so they land in the TRADE column above
and are removed by name in H5.

**Verdict: CONFIRMED.** Real external trade overdue 60+ = **₹7.26 Cr**.

---

## H5 — Top external overdue customers (the actual collection list)

Same query, grouped per customer, JIVO-group names removed:

| Company | Customer | Balance | 61-90 | 91-180 | 181-365 | 365+ | **60+ total** |
|---|---|---:|---:|---:|---:|---:|---:|
| Bev | **BLESSING ADVERTISING PVT LTD** | ₹310.92 L | – | – | **289.00** | – | **₹289.00 L** |
| Oil | **AB ENTERPRISES** | ₹128.78 L | – | – | **128.78** | – | **₹128.78 L** |
| Oil | **B S A ENGINEERING LLP** | ₹110.80 L | 7.98 | 102.82 | – | – | **₹110.80 L** |
| Oil | **FUTURE RETAIL LTD** | ₹94.57 L | – | – | – | 94.54 | **₹94.54 L** |
| Oil | CANTEEN STORES DEPT (CSD) | ₹164.33 L | – | 15.63 | 4.94 | 9.27 | ₹29.84 L |
| Oil | INNOVATIVE RETAIL (BigBasket) | ₹13.28 L | – | 3.36 | 7.57 | 2.35 | ₹13.28 L |
| Mart | ZOMATO HYPERPURE PVT LTD | ₹13.04 L | – | – | 5.09 | 6.74 | ₹11.83 L |
| Mart | CMUNITY INNOVATIONS PVT LTD | ₹10.74 L | – | 7.74 | 2.92 | – | ₹10.67 L |
| Oil | BLESSING ADVERTISING (B SAHIB) | ₹7.40 L | – | – | – | 7.40 | ₹7.40 L |
| Oil | LIFE ESSENTIALS PERSONAL CARE | ₹4.70 L | – | – | – | 4.70 | ₹4.70 L |
| Bev | B S A ENGINEERING LLP | ₹4.26 L | 0.06 | 4.20 | – | – | ₹4.26 L |
| Oil | WAL MART INDIA PVT LTD | ₹144.76 L | 2.81 | 1.08 | 0.20 | – | ₹4.09 L |
| Mart | INNOVATIVE RETAIL (BigBasket) | ₹3.98 L | – | 0.62 | 3.36 | – | ₹3.98 L |
| Bev | GULATI TRADERS | ₹2.57 L | – | – | – | 2.32 | ₹2.32 L |
| Bev | SUPER MARCHE 37 TRADERS LLP | ₹2.28 L | – | – | – | 2.28 | ₹2.28 L |
| Oil | AVENUE SUPERMARTS (DMart) | ₹2.35 L | – | 0.64 | 1.71 | – | ₹2.35 L |
| Bev | M/S MEDIA MIND | ₹2.60 L | – | 0.85 | 1.36 | – | ₹2.21 L |
| Bev | IDEA PUBLICITY | ₹1.51 L | – | – | – | 1.51 | ₹1.51 L |
| Oil | METRO CASH & CARRY | ₹1.23 L | – | 0.46 | 0.39 | 0.38 | ₹1.23 L |
| Bev | M/S GURU ARJAN DEV TRADING | ₹1.18 L | – | – | 1.18 | – | ₹1.18 L |
| | **TOTAL EXTERNAL 60+** | | | | | | **₹726.25 L** |

**Verdict: CONFIRMED — ₹7.26 Cr.** Four names carry ₹6.23 Cr (86%) of it.

---

## H6 — [[finding-blessing-advertising-289L]] — Bev's single biggest debtor

```sql
SELECT "DocNum","DocDate","DocDueDate",
       ROUND(CAST("DocTotal" AS DOUBLE)/100000,2) T_L,
       ROUND(CAST("PaidToDate" AS DOUBLE)/100000,2) P_L
FROM JIVO_BEVERAGES_HANADB.OINV
WHERE "CardCode"='CUSTA000175' AND "CANCELED"='N' AND "DocStatus"='O' ORDER BY "DocDate";
```

| DocNum | DocDate = DueDate | Total | Paid |
|---|---|---:|---:|
| 625098131 | 2025-09-30 | ₹31.83 L | ₹29.17 L |
| 625108075 / 8099 / 8098 / 8116 / 8130 | 2025-10-15 → 10-22 | ₹35.36 L ×5 | ₹0 |
| 625117955 / 7960 / 7996 | 2025-11-03 → 11-11 | ₹35.36 L ×3 | ₹0 |
| 625118033 | 2025-11-14 | ₹26.85 L | ₹0 |
| 626068302 | 2026-06-30 | ₹21.93 L | ₹0 |

Line detail (`INV1`): every invoice is **FG0000273 — GLASS BOTTLE 200 ML TONIC
WATER 12 PCS**, ~24,000 units @ ₹105.25. Real product, real dispatch, **terms =
immediate (DueDate = DocDate)**, nothing paid for 9-10 months.

Beverages external DSO = ₹3.82 Cr ÷ ₹12.87 Cr trade sales L12M × 365 = **108 days**,
versus Oil 12 days and Mart 19 days — entirely this one account.

**Verdict: CONFIRMED. ₹2.89 Cr recoverable, 8-10 months past an immediate-payment term.**

---

## H7 — [[finding-contra-adagency-30L]] — we are paying the party that owes us

```sql
SELECT h."CardCode", c."CardName", COUNT(*) N,
       ROUND(SUM(CAST(h."DocTotal"-h."PaidToDate" AS DOUBLE))/100000,2) OPENAP_L, MIN(h."DocDate")
FROM JIVO_OIL_HANADB.OPCH h JOIN JIVO_OIL_HANADB.OCRD c ON c."CardCode"=h."CardCode"
WHERE h."CardCode" IN ('VENDA001047','VENDA000706') AND h."DocStatus"='O' AND h."CANCELED"='N'
GROUP BY h."CardCode", c."CardName";
```

| Party | JIVO owes (Oil A-P) | Party owes JIVO | Contra available |
|---|---:|---:|---:|
| BLESSING ADVERTISING PVT LTD | ₹26.26 L open (3 bills, oldest 2024-09-30) | ₹310.92 L (Bev) | **₹26.26 L** |
| MEDIA MIND | ₹18.86 L open (27-Jun-2026) | ₹2.60 L (Bev) | **₹2.60 L** |
| IDEA PUBLICITY | ₹47.02 L (customer credit bal, Oil) | ₹1.51 L (Bev) | **₹1.51 L** |
| | | | **₹30.37 L** |

**Verdict: CONFIRMED.** ₹30.37 L collectible today with a three-way set-off letter,
zero collection effort. Caveat: cross-entity (Oil ↔ Beverage Unit are the same
legal entity — JIVO Wellness Pvt Ltd — so Blessing/Media Mind set-off is a simple
same-PAN adjustment).

---

## H8 — [[finding-ab-enterprises-going-bad]] — dormant debtors

```sql
SELECT c."CardCode", c."CardName", ROUND(CAST(c."Balance" AS DOUBLE)/100000,2) BAL_L,
 (SELECT MAX(i."DocDate") FROM JIVO_OIL_HANADB.OINV i WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N') LAST_INV,
 (SELECT MAX(r."DocDate") FROM JIVO_OIL_HANADB.ORCT r WHERE r."CardCode"=c."CardCode" AND r."Canceled"='N') LAST_PAY
FROM JIVO_OIL_HANADB.OCRD c
WHERE c."CardType"='C' AND c."Balance">100000 AND c."GroupCode"<>100
  AND IFNULL((SELECT MAX(i."DocDate") FROM JIVO_OIL_HANADB.OINV i
              WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N'), DATE'2000-01-01') < DATE'2026-01-28';
```

| Company | Customer | Balance | Last invoice | Last payment |
|---|---|---:|---|---|
| Oil | **AB ENTERPRISES** | ₹128.78 L | 2025-12-29 | **2025-09-27 (10 months)** |
| Oil | FUTURE RETAIL LTD | ₹94.57 L | 2024-09-30 (migration) | **never** |
| Oil | BLESSING ADVERTISING B SAHIB | ₹7.40 L | 2024-09-30 | 2024-09-30 |
| Oil | LIFE ESSENTIALS PERSONAL CARE | ₹4.70 L | 2025-08-23 | 2025-10-08 |
| Mart | INNOVATIVE RETAIL (BigBasket) | ₹3.98 L | 2026-01-13 | 2026-02-26 |
| Bev | GULATI TRADERS | ₹2.57 L | 2025-03-31 | 2025-05-23 |
| Bev | SUPER MARCHE 37 TRADERS LLP | ₹2.28 L | 2024-11-28 | 2025-01-27 |
| Bev | IDEA PUBLICITY | ₹1.51 L | 2025-10-28 | 2026-01-08 |
| Bev | M/S GURU ARJAN DEV TRADING | ₹1.18 L | 2026-01-14 | 2026-01-12 |

AB Enterprises verified invoice-by-invoice — 3 open bills, all immediate terms:
₹66.34 L (14-Oct-25, ₹46.49 L part-paid), ₹54.38 L (17-Dec-25, nil), ₹54.55 L
(29-Dec-25, nil). Trading stopped, payments stopped, balance frozen at ₹128.78 L.

**Verdict: CONFIRMED. ₹1.29 Cr actively going bad — legal notice window is closing.**

---

## H9 — [[finding-bsa-engineering-116L]] — overdue *and* still being supplied

```sql
SELECT "DocNum","DocDate","DocDueDate", ROUND(CAST("DocTotal" AS DOUBLE)/100000,2) T_L,
       ROUND(CAST("PaidToDate" AS DOUBLE)/100000,2) P_L
FROM JIVO_OIL_HANADB.OINV WHERE "CardCode"='CUSTA000680' AND "CANCELED"='N' AND "DocStatus"='O';
```

30 open invoices. The money is in three: **₹22.86 L (19-Mar-26)**, **₹55.81 L
(28-Mar-26)**, **₹9.23 L (30-Mar-26)** — all immediate terms, all 4 months old,
₹0.27 L paid in total. Yet fresh invoices ran through **April, May and June 2026**.
Also owes Bev ₹4.26 L and Mart ₹0.45 L → **₹115.51 L group-wide**.

**Verdict: CONFIRMED. ₹1.16 Cr, and supply was never stopped.**

---

## H10 — [[finding-future-retail-writeoff-tax]] — provided but never written off

```sql
SELECT "AcctCode","AcctName", ROUND(CAST("CurrTotal" AS DOUBLE)/100000,2) BAL_L
FROM JIVO_OIL_HANADB.OACT
WHERE UPPER("AcctName") LIKE '%BAD DEBT%' OR UPPER("AcctName") LIKE '%DOUBT%';
```

| Acct | Name | Balance |
|---|---|---:|
| 2180008 | PROVISION FOR BAD AND DOUBTFUL DEBTS (Oil) | −₹94.57 L |
| 5680009 | BAD DEBTS WRITTEN OFF (Oil) | **₹0.00** |
| 5680009 | BAD DEBTS WRITTEN OFF (Mart) | ₹22.38 L |

The Oil provision (₹94.57 L) is **exactly** the FUTURE RETAIL LTD balance
(₹94.57 L) — the company already knows it is gone. But a *provision* for doubtful
debts is disallowed for a non-banking company under s.36(1)(vii); only an actual
write-off (debiting the debtor account) is deductible.

**Verdict: CONFIRMED. ₹23.80 L one-time cash tax saving** (₹94.57 L × 25.168%)
by converting the provision to a write-off. Caveat: needs the auditor's sign-off
and, ideally, an NCLT claim filed first; no GST relief is available on Indian bad
debts.

---

## H11 — Interest cost of the overdue book (derived, not assumed)

```sql
SELECT a."AcctCode", a."AcctName",
       ROUND(SUM(CAST(j."Debit"-j."Credit" AS DOUBLE))/100000,2) NET_L
FROM JIVO_OIL_HANADB.JDT1 j JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE UPPER(a."AcctName") LIKE '%INTEREST%' AND j."RefDate">='2025-07-28' GROUP BY 1,2;
```

| Item | Amount |
|---|---:|
| INTEREST ON BANK LOAN (Oil, L12M) | ₹402.08 L |
| INTEREST ON UNSECURED LOAN (Oil + Mart, L12M) | ₹36.93 L |
| BANK CHARGES (Oil) | ₹32.52 L |
| Indian Bank CC A/C 7007270527 | −₹28.39 Cr |
| Term loans (Indian Bank ×7, ICICI ×6) | −₹19.10 Cr |
| **Total bank debt** | **₹47.49 Cr** |
| **Derived blended bank rate** | **402.08 ÷ 4,748.88 = 8.47% p.a.** |

The CC account is drawn ₹28.39 Cr, so every rupee collected repays CC at the
marginal rate.

**Verdict: CONFIRMED. ₹7.26 Cr × 8.5% = ₹61.7 L per year** of interest JIVO pays
purely to finance customers who are already 60+ days past due. Collecting it is
₹7.26 Cr of one-time working capital **and** ₹61.7 L/yr recurring.

---

## H12 — JIVO has never charged a rupee of late-payment interest

```sql
SELECT a."AcctCode", a."AcctName", ROUND(SUM(CAST(j."Credit"-j."Debit" AS DOUBLE))/100000,2) INC_L
FROM <each schema>.JDT1 j JOIN <each schema>.OACT a ON a."AcctCode"=j."Account"
WHERE (UPPER(a."AcctName") LIKE '%INTEREST%RECEIV%' OR UPPER(a."AcctName") LIKE '%INTEREST ON DELAY%'
    OR UPPER(a."AcctName") LIKE '%LATE PAYMENT%' OR UPPER(a."AcctName") LIKE '%INTEREST FROM CUSTOMER%')
  AND j."RefDate">='2025-07-28' GROUP BY 1,2;
```

**Zero rows in all three companies.** Meanwhile Oil pays ₹4.02 Cr/yr of bank
interest. At the market-standard 18% p.a. overdue clause, the current 60+ book
would carry ₹1.31 Cr/yr of billable interest.

**Verdict: CONFIRMED but discounted.** Realistically only chronic non-strategic
accounts can be billed and only some will pay — budget **₹32.7 L/yr (25% capture)**.
Caveat: charging interest to CSD, Walmart, DMart, Amazon, Flipkart is commercially
impossible; the recoverable base is the ₹4.3 Cr of small/mid trade accounts.

---

## H13 — Credit-limit control is not functioning

```sql
SELECT CASE WHEN IFNULL("CreditLine",0)=0 THEN 'NO_LIMIT' ELSE 'HAS_LIMIT' END K,
       COUNT(*) N, ROUND(SUM(CAST("Balance" AS DOUBLE))/100000,2) BAL_L
FROM JIVO_OIL_HANADB.OCRD WHERE "CardType"='C' AND "Balance">0 GROUP BY 1;
```

| Oil | N | Balance |
|---|---:|---:|
| HAS_LIMIT | 65 | ₹31.41 Cr |
| **NO_LIMIT** | **40** | **₹78.58 Cr** |

And where limits do exist they track the exposure: AB ENTERPRISES 128.78 / limit
128.78 · B S A 110.80 / 111.80 · ILAHI 69.29 / 70.00 · SHIVAY EDIBLES 49.40 /
49.50 · G PURE INDIA 42.39 / 42.40. Only **one** Oil customer is technically over
limit (SHRI JEE TRADING, ₹0.68 L).

**Verdict: CONFIRMED (control finding, no direct ₹).** The limit is being raised
to whatever the customer already owes, so SAP's credit block can never fire.

---

## H14 — Fresh supply flowing to delinquent accounts

```sql
SELECT o."CardCode", c."CardName", COUNT(*) N,
       ROUND(SUM(CAST(o."DocTotal"-o."PaidToDate" AS DOUBLE))/100000,2) OPENORD_L,
       ROUND(CAST(c."Balance" AS DOUBLE)/100000,2) BAL_L
FROM <schema>.ORDR o JOIN <schema>.OCRD c ON c."CardCode"=o."CardCode"
WHERE o."DocStatus"='O' AND o."CANCELED"='N' AND c."Balance">500000 AND IFNULL(c."GroupCode",0)<>100
GROUP BY 1,2,c."Balance" ORDER BY 4 DESC;
```

| Company | Customer | Open orders | Balance | Limit |
|---|---|---:|---:|---:|
| Mart | R K WORLDINFOCOM PVT LTD | **₹11.31 Cr** (332 orders) | ₹8.63 Cr | ₹9.00 Cr |
| Mart | KNOWTABLE ONLINE SERVICES | ₹5.09 Cr (45) | ₹0.41 Cr | ₹0.50 Cr |
| Oil | SHIVAY EDIBLES PVT LTD | ₹2.87 Cr (2) | ₹0.49 Cr | ₹0.50 Cr |
| Oil | JIVO MART (intercompany) | ₹1.67 Cr (8) | ₹24.00 Cr | ₹26.00 Cr |
| Oil | INNOVATIVE RETAIL (BigBasket) | ₹0.27 Cr (15) | ₹0.13 Cr — all 90+ overdue | ₹0.35 Cr |
| Mart | CMUNITY INNOVATIONS | ₹0.15 Cr (8) | ₹0.11 Cr — all 90+ overdue | ₹0.52 Cr |

**Verdict: RISK FLAG (not a savings figure).** R K Worldinfocom alone is 85% of
Mart's external debtor book and is at 96% of its limit with ₹11.31 Cr more on
order — if that order book ships, exposure is ~₹19.9 Cr against a ₹9 Cr limit.
They are paying (last receipt 27-Jul-2026), so this is concentration risk, not a
leak. Do **not** count it as savings; do secure it (PDC / BG / limit review).

---

## H15 — Customer credit balances: money sitting unmatched or owed back

```sql
SELECT "CardCode","CardName", ROUND(CAST("Balance" AS DOUBLE)/100000,2) BAL_L
FROM <schema>.OCRD WHERE "CardType"='C' AND "Balance" < -100000 ORDER BY "Balance" ASC;
```

| Company | Party | Credit balance | Nature |
|---|---|---:|---|
| Oil | AKAL ROZGAR YOJANA (a unit of JWPL) | −₹218.01 L | intra-group |
| Oil | IDEA PUBLICITY | −₹47.02 L | external, also ₹42.39 L of open invoices |
| Oil | PRIME SALES CORPORATION | −₹23.80 L | external |
| Oil | ARJUN DASS & SONS PUNJAB NEW | −₹23.75 L | external |
| Oil | BRIJ LAL DURGA DASS | −₹14.99 L | external |
| Oil | DEBTORS SUSPENSE | −₹3.37 L | **literally a suspense account** |
| Mart | JIVO MART - HR / PB / KR | −₹494.06 L | intra-group |
| Mart | ANTIZE FOODS PVT LTD | −₹43.88 L | external |
| Bev | VARNAY CO GOODS WHOLESALERS LLC | −₹13.50 L | export advance |

External unmatched customer credit: Oil ₹1.87 Cr + Mart ₹0.52 Cr + Bev ₹0.21 Cr =
**₹2.60 Cr**.

**Verdict: CONFIRMED as a clean-up target, medium confidence on the ₹.** Part is
genuine advance against future supply; part is receipts posted to the wrong
account that should be closing overdue invoices elsewhere. Clearing it is the
first concrete step out of the ₹143 Cr backlog in H2.

---

## H16 — Data-quality checks that could have invalidated the aging

```sql
SELECT CASE WHEN "DocDueDate"<"DocDate" THEN 'DUE_BEFORE_DOC'
            WHEN "DocDueDate"="DocDate" THEN 'SAME_DAY' ELSE 'NORMAL' END K,
       COUNT(*) N, ROUND(SUM(CAST("DocTotal"-"PaidToDate" AS DOUBLE))/100000,2) OPEN_L
FROM JIVO_OIL_HANADB.OINV WHERE "DocStatus"='O' AND "CANCELED"='N' GROUP BY 1;
```

| Pattern | N | Open ₹L | Explanation |
|---|---:|---:|---|
| DUE_BEFORE_DOC | 6,897 | 2,604.50 | migrated openings — `DocDate`=2024-09-30 go-live, `DocDueDate`=true original date. Aging is **correct**. |
| SAME_DAY | 3,851 | 14,744.16 | immediate terms — branch transfers, cash sales, Blessing, AB, BSA |
| NORMAL | 2,042 | 774.00 | avg 33-day term |

Also checked: FX receivables — 7 open USD invoices, ₹12.25 Cr, oldest 27-Jan-2025
(ABU DHABI / QATAR / LEGACY). All are fully covered by unapplied receipts, so the
cash is in; but the **EDPMS/eBRC closure is likely still open** past the FEMA
9-month realisation window. Not a ₹ saving — a compliance exposure worth a
separate check with the banker.

**Verdict: aging method stands.**

---

## Summary — what to do Monday

| # | Action | ₹ | Type |
|---|---|---:|---|
| 1 | Collect BLESSING ADVERTISING (Bev), ₹35.36 L × 8 invoices, immediate terms, 9 months old | ₹2.89 Cr | one-time |
| 2 | Legal notice + settlement on AB ENTERPRISES before the 3-year limitation clock matters | ₹1.29 Cr | one-time |
| 3 | Stop supply + collect B S A ENGINEERING LLP (Oil ₹110.80 L + Bev ₹4.26 L 60+; Mart ₹0.45 L still current) | ₹1.15 Cr | one-time |
| 4 | Three-way set-off with the ad-agency cluster (Blessing / Media Mind / Idea Publicity) — **a collection method for part of #1 and #5, not extra money** | ₹30.37 L | (subset) |
| 5 | Chase the tail — 15 accounts: CSD ₹29.84 L, BigBasket ₹17.26 L, Zomato Hyperpure ₹11.83 L, Cmunity ₹10.67 L, Blessing-B-Sahib ₹7.40 L, Life Essentials ₹4.70 L, Walmart ₹4.09 L, DMart ₹2.35 L, Gulati ₹2.32 L, Super Marche ₹2.28 L, Media Mind ₹2.21 L, Idea Publicity ₹1.51 L, Metro ₹1.23 L, Guru Arjan ₹1.18 L | ₹98.87 L | one-time |
| 6 | Interest saved on the whole ₹7.26 Cr at the derived 8.47% CC rate | ₹61.7 L / yr | recurring |
| 7 | Convert the ₹94.57 L Future Retail provision into a s.36(1)(vii) write-off | ₹23.8 L | one-time (tax) |
| 8 | Introduce an 18% overdue-interest clause; bill chronic small/mid accounts | ₹32.7 L / yr | recurring |
| 9 | Run SAP **Internal Reconciliation** on ₹143.23 Cr of unapplied receipts + ₹12.24 Cr of credit notes; clear the ₹2.60 Cr external credit pool | ₹2.60 Cr | WC release |
| 10 | Fix credit limits: 40 Oil customers with ₹78.58 Cr have no limit; limits elsewhere equal the balance | control | — |
| 11 | Do not ship R K Worldinfocom's ₹11.31 Cr order book beyond the ₹9 Cr limit without security | risk | — |

**No double counting:** items 1 + 2 + 3 + 5 + 7 exactly partition the ₹7.26 Cr
external 60+ book (289.00 + 128.78 + 115.06 + 98.87 + 94.54 = ₹726.25 L).
Item 4 is a *method* of collecting ₹26.26 L of item 1 and ₹4.11 L of item 5.
Item 6 is the interest on the same ₹7.26 Cr — a different kind of money
(recurring P&L), so it does add. Item 9 is separate cash already banked.

**Honest caveats**
- `OCRD.Balance` is treated as ground truth for the net position; open-invoice
  aging is only meaningful after the H4 credit adjustment.
- Branch/intra-group balances (₹116.24 Cr) are excluded everywhere — they net to
  ~zero against BRANCH VENDOR and are not collectible cash.
- CSD (government), Walmart, DMart, Amazon, Flipkart, Zomato are solvent and pay
  on their own reconciliation cycle — their overdue is process friction, not risk.
- Blessing Advertising is an advertising agency that also *sells to* JIVO; the
  ₹2.89 Cr may be intended as an offset against future media spend. Confirm the
  commercial arrangement before treating it as pure recovery.
- The 18% interest recovery (item 8) is the softest number here — low confidence.

Back-links: [[SAVINGS-MOC]] · [[vendor-money-stuck]] · [[duplicate-payments]] · [[returns-leakage]]
