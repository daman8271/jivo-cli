---
title: "Adversarial verification of finding #4 — Mart return rate 13.3% / ₹9.91 Cr"
created: 2026-07-28
lens: verify-returns-leakage-mart
tags: [savings-audit, verification, returns, credit-notes, sap-b1, mart]
---

# Verify #4 — "Mart return rate is 13.3%, ₹9.91 Cr/yr above a 10% allowance"

Part of [[SAVINGS-MOC]] · verifies [[finding-excess-returns-above-benchmark]] · source note [[returns-leakage]]

**Verdict: REVISED — ₹9.91 Cr → ₹0.60 Cr/yr (range ₹0.5–0.9 Cr).**
The *pattern* is real and the finder's arithmetic replicates exactly. The *money* does not:
₹9.91 Cr is reversed **revenue** in a book whose measured gross margin is 8.36%, on goods
that provably re-enter stock and get re-sold.

**Window:** 2025-07-28 → 2026-07-29 unless stated. Company: `JIVO_MART_HANADB`.
**Tool:** `/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql` (read-only SELECT).

---

## V0 — Does the headline replicate? (different query shape: scalar subqueries, not UNION ALL)

```sql
SELECT
 (SELECT ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/10000000,4)
    FROM JIVO_MART_HANADB.OINV
   WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29') AS SALES_CR,
 (SELECT ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/10000000,4)
    FROM JIVO_MART_HANADB.ORIN
   WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29') AS RET_CR
FROM DUMMY
```

| | Finder | Me | Δ |
|---|---:|---:|---:|
| Mart sales 12M | ₹204.69 Cr | **₹204.96 Cr** | +0.1% |
| Mart returns 12M | ₹27.45 Cr | **₹27.47 Cr** | +0.1% |
| Rate | 13.31% | **13.40%** | ok |

And the excess calc replicates to the rupee:

```sql
SELECT ROUND(SUM(GREATEST(0,R-S*0.05))/10000000,2) AS EXC5,
       ROUND(SUM(GREATEST(0,R-S*0.10))/10000000,2) AS EXC10
FROM (SELECT x.CC AS CC, SUM(x.S) AS S, SUM(x.R) AS R FROM (
   SELECT "CardCode" AS CC, CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE) AS S, 0.0 AS R
     FROM JIVO_MART_HANADB.OINV WHERE "CANCELED"='N'
      AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29' GROUP BY "CardCode"
   UNION ALL
   SELECT "CardCode", 0.0, CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)
     FROM JIVO_MART_HANADB.ORIN WHERE "CANCELED"='N'
      AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29' GROUP BY "CardCode") x
 GROUP BY x.CC HAVING SUM(x.S)>0)
```

| EXC>5% | EXC>10% |
|---:|---:|
| ₹18.04 Cr | **₹9.89 Cr** (finder: ₹9.91 Cr) |

**No arithmetic error. No cancelled-doc error, no GST error, no sign error.** The attack has to be
on the *definition* and the *economics*, not the SQL.

---

## V1 — ₹1.90 Cr of the "returns" are not returns at all (DocType split)

`ORIN` mixes item credit notes (`DocType='I'`, goods came back) with **service** credit notes
(`DocType='S'` — business promotion, promotional discount, brand fund). The finder counted both.

```sql
SELECT 'ORIN' AS TBL, "DocType", COUNT(*) AS DOCS,
       ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/10000000,3) AS CR
  FROM JIVO_MART_HANADB.ORIN WHERE "CANCELED"='N'
   AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29' GROUP BY "DocType"
UNION ALL
SELECT 'OINV', "DocType", COUNT(*),
       ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/10000000,3)
  FROM JIVO_MART_HANADB.OINV WHERE "CANCELED"='N'
   AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29' GROUP BY "DocType"
```

| Table | DocType | Docs | ₹ Cr |
|---|---|---:|---:|
| OINV | I (goods) | 13,918 | 195.86 |
| OINV | S (service) | 61 | 9.10 |
| ORIN | **I (goods)** | 2,164 | **24.71** |
| ORIN | **S (promo)** | 73 | **2.76** |

**Goods return rate = 24.71 / 195.86 = 12.62%, not 13.31%.**

Worse — this is a **cross-finding double count**. The finder's own H11 /
[[finding-trade-spend-as-credit-notes]] claims ₹3.87 Cr of promo-spend-as-credit-notes as a
*separate* saving. The Mart slice of that (₹2.76 Cr) is sitting inside this finding too.
Re-running the excess calc on goods only:

| Basis | Rate | EXC>5% | EXC>10% |
|---|---:|---:|---:|
| Finder (all DocTypes) | 13.29% | ₹18.04 Cr | ₹9.89 Cr |
| **Goods returns only** | **12.62%** | ₹15.56 Cr | **₹7.99 Cr** |

**Verdict: −₹1.90 Cr. Already outside the ±10% CONFIRMED band.**

---

## V2 — ₹1.90 Cr more is a single-month July-2026 event, not a run-rate

The trailing-12M window ends mid-month and captures a large July-2026 stock pullback.

```sql
SELECT h."CardCode", TO_VARCHAR(h."DocDate",'YYYY-MM') AS M, COUNT(*) AS DOCS,
       ROUND(CAST(SUM(h."DocTotal"-IFNULL(h."VatSum",0)) AS DOUBLE)/100000,1) AS RET_L
  FROM JIVO_MART_HANADB.ORIN h
 WHERE h."CANCELED"='N' AND h."DocType"='I'
   AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
   AND h."CardCode" IN ('CUSTA000048','CUSTA000907','CUSTA000592','CUSTA000927')
 GROUP BY h."CardCode", TO_VARCHAR(h."DocDate",'YYYY-MM')
```

July-2026 alone (28 days) = **₹5.85 Cr of the top-4's ₹19.87 Cr annual returns — 29% in one
partial month.** Two accounts returned more than they bought that month:

| Account | Jul-26 sales ₹L | Jul-26 returns ₹L | Ratio |
|---|---:|---:|---:|
| SUSTAINQUEST | 199.6 | 186.1 | 93% |
| **ANTIZE FOODS** | 70.2 | **130.0** | **185%** |
| KNOWTABLE | 284.5 | 133.1 | 47% |
| R K WORLDINFOCOM | 617.6 | 136.2 | 22% |

Re-run over windows that exclude the event:

```sql
-- same excess query, DocType='I', varying the date window
```

| Window | Sales ₹Cr | Returns ₹Cr | Rate | EXC>10% |
|---|---:|---:|---:|---:|
| Finder 12M (all DocTypes) | 204.98 | 27.25 | 13.29% | ₹9.89 Cr |
| 12M goods only | 195.86 | 24.71 | 12.62% | ₹7.99 Cr |
| **12M ex-Jul-26** (2025-07→2026-07) | 190.39 | 20.93 | **10.99%** | **₹6.09 Cr** |
| **FY25-26** (clean fiscal yr) | 162.93 | 16.92 | **10.38%** | **₹5.31 Cr** |
| FY24-25 | 38.87 | 4.34 | **11.16%** | ₹1.87 Cr |

**Two things die here.**
1. Steady-state Mart goods-return rate is **10.4–11.0%**, not 13.3%. A "10% allowance" is
   therefore ~the company's own mean — the "excess" is largely **dispersion around the average**,
   which no contract clause recovers.
2. The finder's H6 "deterioration 9.5% → 10.8% → 18.5%" does not survive on goods returns:
   **FY24-25 11.16% → FY25-26 10.38% is flat-to-improving.**

---

## V3 — Two of the "top 4" fall below the cap once the event is removed

```sql
SELECT x.CC, MAX(x.NM) AS NAME, ROUND(SUM(x.S)/100000,1) AS SALES_L,
       ROUND(SUM(x.R)/100000,1) AS RET_L,
       ROUND(100*SUM(x.R)/NULLIF(SUM(x.S),0),1) AS PCT,
       ROUND(GREATEST(0,SUM(x.R)-SUM(x.S)*0.10)/100000,1) AS EXC10_L
FROM ( ...OINV/ORIN UNION ALL, DocType='I', 2025-07-01 → 2026-07-01... ) x
GROUP BY x.CC HAVING SUM(x.R)>2000000 ORDER BY 6 DESC
```

| Account | 12M ex-Jul rate | Excess >10% ₹L | Finder's claimed rate |
|---|---:|---:|---:|
| **R K WORLDINFOCOM** | **16.1%** | **386.1** | 14.7% |
| SUSTAINQUEST | 13.4% | 88.3 | 19.5% |
| FLIPKART INDIA | 19.5% | 53.4 | 22.0% |
| SCOOTSY (Swiggy) | 216% | 37.6 | 188% |
| KIRANAKART (Zepto) | 31.5% | 24.5 | 108% |
| **KNOWTABLE** | **9.7%** | **0** | 16.8% |
| **ANTIZE FOODS** | below threshold | **0** | 10.1% |

**Only ONE account (R K Worldinfocom) is a persistent, material offender** — ₹3.86 Cr of the
₹6.09 Cr steady-state excess (63%). Knowtable and Antize sit at/under the 10% cap; their
appearance in the top-4 is entirely the July-2026 pullback plus (for Knowtable) ₹55 L of
*promotional* credit notes miscounted as returns.

**Concentration claim itself is CONFIRMED and in fact stronger** — on goods returns the top-4 are
₹19.87 Cr of ₹24.71 Cr = **80.4%** (finder said 74%), across **318 documents**.

---

## V4 — Are these real goods or price corrections? (test that FAILS to refute)

```sql
SELECT CASE WHEN IFNULL(r."Quantity",0)=0 THEN 'ZERO_QTY_pricecorr' ELSE 'has_qty' END AS K,
       COUNT(*) AS LINES, ROUND(CAST(SUM(r."LineTotal") AS DOUBLE)/100000,2) AS VAL_L
  FROM JIVO_MART_HANADB.RIN1 r JOIN JIVO_MART_HANADB.ORIN h ON h."DocEntry"=r."DocEntry"
 WHERE h."CANCELED"='N' AND h."DocType"='I'
   AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29' GROUP BY 1
```

| | Lines | ₹ lakh |
|---|---:|---:|
| has_qty | **15,600** | 2,471.15 |
| zero-qty | 0 | 0 |

**Refutation attempt fails — 100% of item credit notes carry real quantities.** These are genuine
physical returns, not disguised discounts. Credit to the finder.

---

## V5 — THE KILLER: reversed revenue ≠ lost money. Mart's gross margin is 8.36%.

The finder's own caveat says `OITM."AvgPrice"=0` so costs are unknown, then reports the revenue
figure as an annual saving anyway. Costs *are* derivable — from Mart's own purchase invoices.

```sql
SELECT ROUND(SUM(SV)/10000000,2) AS SALES_CR, ROUND(SUM(GP)/10000000,2) AS GP_CR,
       ROUND(100*SUM(GP)/SUM(SV),2) AS WTD_GM_PCT, COUNT(*) AS ITEMS
FROM (SELECT s."ItemCode" AS IC, SUM(s.SV) AS SV,
             SUM(s.SV)/NULLIF(SUM(s.SQ),0) AS SELLPR,
             SUM(s.PV)/NULLIF(SUM(s.PQ),0) AS BUYPR,
             SUM(s.SQ)*(SUM(s.SV)/NULLIF(SUM(s.SQ),0)
                      - SUM(s.PV)/NULLIF(SUM(s.PQ),0)) AS GP
      FROM (SELECT l."ItemCode" AS "ItemCode",
                   CAST(SUM(l."Quantity") AS DOUBLE) AS SQ,
                   CAST(SUM(l."LineTotal") AS DOUBLE) AS SV, 0.0 AS PQ, 0.0 AS PV
              FROM JIVO_MART_HANADB.INV1 l
              JOIN JIVO_MART_HANADB.OINV h ON h."DocEntry"=l."DocEntry"
             WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
             GROUP BY l."ItemCode"
            UNION ALL
            SELECT p."ItemCode", 0.0, 0.0,
                   CAST(SUM(p."Quantity") AS DOUBLE), CAST(SUM(p."LineTotal") AS DOUBLE)
              FROM JIVO_MART_HANADB.PCH1 p
              JOIN JIVO_MART_HANADB.OPCH ph ON ph."DocEntry"=p."DocEntry"
             WHERE ph."CANCELED"='N' AND ph."DocDate">='2025-07-28' AND ph."DocDate"<'2026-07-29'
             GROUP BY p."ItemCode") s
      GROUP BY s."ItemCode")
WHERE SELLPR>0 AND BUYPR>0 AND BUYPR < 2*SELLPR
```

| Sales covered | Gross profit | **Weighted GM** | Items |
|---:|---:|---:|---:|
| ₹197.59 Cr | ₹16.52 Cr | **8.36%** | 170 |

*(Self-check: the raw run gave 0.93% because three items — FG0000319/311/317 — carry corrupt
purchase prices of ₹55k–90k per PCS against ₹430–898 sell prices, injecting −₹14.6 Cr of fake
negative GP. Excluded via `BUYPR < 2*SELLPR`. UoM verified identical on both sides: `unitMsr`='PCS',
`NumPerMsr`=1 on INV1 and PCH1, so no case-vs-piece distortion.)*

Corroborated by Mart's P&L identity: net sales ₹177.5 Cr vs net purchases ₹175.3 Cr — Mart is a
near-pass-through distributor. Oil's own P&L (JDT1 × OACT, FY25-26) gives group GM ~11.5–15.7%
(sales ₹396.79 Cr vs COGS ₹334.6–351.1 Cr).

**₹7.99 Cr of reversed Mart revenue ≈ ₹0.67 Cr of gross profit. Not ₹7.99 Cr.**

---

## V6 — The goods are re-sold, not destroyed (unit reconciliation)

```sql
SELECT s.IC, MAX(s.NM) AS ITEM, ROUND(SUM(s.SOLDQ)) AS SOLD_U, ROUND(SUM(s.RETQ)) AS RET_U,
       ROUND(SUM(s.BUYQ)) AS BOUGHT_U, ROUND(SUM(s.RTVQ)) AS RET_TO_OIL_U
FROM ( ...INV1 / RIN1 / PCH1 / RPC1 UNION ALL over the same 12M... ) s
GROUP BY s.IC ORDER BY 4 DESC
```

| Item | Sold u | Returned u | **Bought u** | Returned to Oil u |
|---|---:|---:|---:|---:|
| POMACE OLIVE 1 LTR | 474,824 | 81,142 | **449,016** | 39,989 |
| MUSTARD KACHI GHANI 1 LTR | 1,000,161 | 67,311 | **974,754** | 52,341 |
| COLD PRESS GROUNDNUT 1 LTR | 686,497 | 33,281 | **654,036** | 14,957 |
| SANO POMACE OLIVE 1 LTR | 214,933 | 50,227 | 219,578 | 29,496 |

**Mart sold 474,824 units of POMACE OLIVE 1L having purchased only 449,016.** The 25,808-unit gap
is returned stock going back out the door. Returns are re-sold, and ~61% of the rest
(₹15.02 Cr of ₹24.71 Cr) is pushed straight back to the manufacturer at cost:

```sql
SELECT h."CardCode", MAX(h."CardName") AS NM, h."DocType", COUNT(*) AS DOCS,
       ROUND(CAST(SUM(h."DocTotal"-IFNULL(h."VatSum",0)) AS DOUBLE)/100000,1) AS CR_L
  FROM JIVO_MART_HANADB.ORPC h WHERE h."CANCELED"='N'
   AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
 GROUP BY h."CardCode", h."DocType" ORDER BY 5 DESC
```

| Vendor | Docs | ₹ lakh |
|---|---:|---:|
| **JIVO WELLNESS PVT LTD** (= Oil) | 255 | **1,502.0** |

**Mart bears almost no economic loss on returns — it is a conduit.** The revenue is *deferred*,
not destroyed.

---

## V7 — What cash actually leaves? Freight and write-off

```sql
SELECT a."AcctName", ROUND(CAST(SUM(j."Debit"-j."Credit") AS DOUBLE)/10000000,2) AS NET_CR
  FROM JIVO_MART_HANADB.JDT1 j JOIN JIVO_MART_HANADB.OACT a ON a."AcctCode"=j."Account"
 WHERE j."RefDate">='2025-07-28' AND j."RefDate"<'2026-07-29'
   AND (UPPER(a."AcctName") LIKE '%FREIGHT%' OR UPPER(a."AcctName") LIKE '%CARTAGE%'
     OR UPPER(a."AcctName") LIKE '%EXPIR%'   OR UPPER(a."AcctName") LIKE '%DAMAGE%'
     OR UPPER(a."AcctName") LIKE '%WRITE%')
 GROUP BY a."AcctName"
```

| Account | ₹ Cr / yr |
|---|---:|
| FREIGHT AND CARTAGE | **2.28** |
| FREIGHT INWARD CHARGES-DIRECT | 0.00 |
| *(no expiry / damage / write-off account exists)* | – |

Mart's **entire** annual freight bill is ₹2.28 Cr (1.1% of sales). The return leg attributable to
the *excess-above-10%* volume is ≈ **₹0.09 Cr/yr**. Total goods issues (OIGE, incl. stock
revaluation and physical audit) = ₹8.03 Cr over 55 docs — not attributable to returns.

---

## Re-derived number

| Component | ₹ |
|---|---:|
| Finder's figure | ₹9.91 Cr |
| − promo/service credit notes misread as returns (also double-counted in [[finding-trade-spend-as-credit-notes]]) | −₹1.90 Cr |
| − July-2026 one-off stock pullback misread as run-rate | −₹1.90 Cr |
| **= steady-state excess reversed REVENUE above a 10% cap** | **₹6.09 Cr** |
| × Mart measured gross margin **8.36%** | **₹0.51 Cr** |
| + avoided return-leg freight | **₹0.09 Cr** |
| **= realistic annual-recurring profit impact** | **₹0.60 Cr** |

Range **₹0.5–0.9 Cr/yr** (upper bound = a 15% restocking-fee chargeback on the ₹6.09 Cr excess).

**Why not the full ₹9.91 Cr:** you cannot both take the goods back into stock and charge the
customer the invoice value — that is double recovery, and no counterparty signs it. The goods are
demonstrably re-sold (V6), so the loss is margin + logistics, not revenue.

---

## What survives — genuinely real, act on these

- ✅ **R K WORLDINFOCOM (CUSTA000048) at 16.1% persistent return rate**, ₹3.86 Cr excess revenue
  (≈ ₹0.32 Cr margin). One counterparty, one contract. → [[finding-rkworldinfocom-return-rate]]
- ✅ **Concentration is real and understated** — 80.4% of Mart goods returns from 4 accounts,
  318 documents.
- ✅ **All returns carry real quantities** — physical goods, a genuine ops problem.
- ✅ **July-2026 pullback (₹5.85 Cr in 28 days) is a live event worth a same-week explanation** —
  Antize returned 185% of its July sales, Sustainquest 93%. Possible channel wind-down.
  Treat as one-time, not recurring. → [[finding-july26-mart-pullback]]

## What does not survive

- ❌ 13.3% return rate → **10.4–11.0%** steady state on goods.
- ❌ "Deteriorating" → FY24-25 11.16% vs FY25-26 10.38%, **flat to improving**.
- ❌ Knowtable (9.7%) and Antize (<10%) as offenders — both at/below the proposed cap.
- ❌ ₹9.91 Cr as annual-recurring savings — it is revenue in an 8.4%-margin pass-through book.
- ❌ A 10% "allowance" as a benchmark — it is the company's own mean, so the excess is mostly
  statistical dispersion.

## Caveats on my own work

1. My 8.36% GM excludes 3 items with corrupt purchase prices; including them gives a nonsense
   0.93%. Master-data cleanup is a real prerequisite (the finder was right about that).
2. Item-level GM assumes purchases and sales in the same 12M are matched; inventory build/drawdown
   adds noise. The P&L cross-check (₹177.5 Cr net sales vs ₹175.3 Cr net purchases) and Oil's
   11.5–15.7% bracket both support single-digit-to-low-teens, not 100%.
3. E-com RTO is partly structural and not contractually preventable at any price.
4. Excluding July-2026 could under-state if the pullback proves to be the new normal — revisit
   after Aug-2026 closes.

Back-links: [[SAVINGS-MOC]] · [[returns-leakage]] · [[2026-07-28]]
