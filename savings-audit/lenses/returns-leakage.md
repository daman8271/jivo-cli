---
title: Returns / credit-notes eating sales — evidence note
created: 2026-07-28
lens: returns-leakage
tags: [savings-audit, returns, credit-notes, sap-b1]
---

# Returns leakage — credit notes eating sales

Part of [[SAVINGS-MOC]]

**Window:** rolling 12 months `2025-07-28 → 2026-07-28` unless stated.
**Definitions:** sales = `OINV` net (`"DocTotal" - "VatSum"`), `"CANCELED"='N'`; returns = `ORIN` net, same filter. Line detail from `INV1` / `RIN1`.
**Tool:** `/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql` (read-only SELECT).

## Headline

| Company | Sales 12M | Returns 12M | Rate |
|---|---:|---:|---:|
| Oil (JIVO_OIL_HANADB) | ₹460.08 Cr | ₹28.24 Cr | **6.1%** |
| Mart (JIVO_MART_HANADB) | ₹204.69 Cr | ₹27.45 Cr | **13.4%** |
| Beverages | ₹13.17 Cr | ₹0.71 Cr | 5.4% |
| **Group** | **₹677.94 Cr** | **₹56.40 Cr** | **8.3%** |

₹56.40 Cr of invoiced sales was reversed by credit note in 12 months.

---

## H1 — What is the return rate per company, per month?

```sql
SELECT M, ROUND(SUM(S)/10000000,2) AS SALES_CR, ROUND(SUM(R)/10000000,2) AS RET_CR,
       ROUND(100*SUM(R)/NULLIF(SUM(S),0),1) AS PCT
FROM (
  SELECT TO_VARCHAR("DocDate",'YYYY-MM') AS M,
         CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE) AS S, 0.0 AS R
  FROM JIVO_OIL_HANADB.OINV
  WHERE "CANCELED"='N' AND "DocDate">='2025-07-01' AND "DocDate"<'2026-07-29'
  GROUP BY TO_VARCHAR("DocDate",'YYYY-MM')
  UNION ALL
  SELECT TO_VARCHAR("DocDate",'YYYY-MM'), 0.0,
         CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)
  FROM JIVO_OIL_HANADB.ORIN
  WHERE "CANCELED"='N' AND "DocDate">='2025-07-01' AND "DocDate"<'2026-07-29'
  GROUP BY TO_VARCHAR("DocDate",'YYYY-MM')
) GROUP BY M ORDER BY M
```

| Month | Oil sales | Oil ret | Oil % | Mart sales | Mart ret | Mart % |
|---|---:|---:|---:|---:|---:|---:|
| 2025-07 | 47.27 | 2.30 | 4.9 | 14.02 | 3.13 | 22.3 |
| 2025-08 | 40.86 | 1.02 | 2.5 | 13.51 | 1.04 | 7.7 |
| 2025-09 | 37.49 | 1.55 | 4.1 | 14.81 | 1.27 | 8.5 |
| 2025-10 | 39.91 | 1.68 | 4.2 | 14.18 | 1.29 | 9.1 |
| 2025-11 | 31.56 | 3.21 | 10.2 | 12.42 | 1.72 | 13.9 |
| 2025-12 | 37.85 | 1.90 | 5.0 | 14.10 | 1.40 | 9.9 |
| 2026-01 | 45.61 | 1.21 | 2.6 | 14.29 | 0.69 | 4.8 |
| 2026-02 | 31.67 | 1.07 | 3.4 | 13.75 | 2.10 | 15.3 |
| 2026-03 | 31.59 | 1.59 | 5.0 | 22.09 | 2.29 | 10.4 |
| 2026-04 | 32.09 | 2.70 | 8.4 | 18.64 | 2.26 | 12.1 |
| 2026-05 | 41.64 | 1.54 | 3.7 | 21.63 | 3.38 | 15.6 |
| 2026-06 | 37.09 | 0.85 | 2.3 | 26.04 | 2.86 | 11.0 |
| **2026-07** | **37.17** | **9.74** | **26.2** | **15.71** | **6.65** | **42.4** |

**Verdict:** July 2026 is a 5-10x outlier in both books. Calibration check passes: Oil Jul-26 ₹35.9–37.2 Cr gross less ₹9.74 Cr returns ≈ ₹26 Cr net — matches the known figure.

---

## H2 — Decompose the July 2026 spike: who?

```sql
SELECT "CardCode", MAX("CardName") AS NAME, "DocType", COUNT(*) AS DOCS,
       ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/100000,2) AS RET_LAKH
FROM JIVO_OIL_HANADB.ORIN
WHERE "CANCELED"='N' AND "DocDate">='2026-07-01'
GROUP BY "CardCode","DocType" ORDER BY 5 DESC
```

| Customer | Docs | ₹ lakh |
|---|---:|---:|
| **JIVO MART PVT LTD** (CUSTA000606, related party) | 19 | **930.59** |
| WAL MART INDIA PVT LTD | 13 | 9.19 |
| BACHAN SINGH KULJIT SINGH | 2 | 6.35 |
| AGGARWAL AGENCIES | 9 | 5.61 |
| _all others_ | ~50 | ~28 |

**Verdict:** 95.5% of Oil's July return spike is ONE related-party account. → [[finding-intercompany-stock-reversal]]

---

## H3 — Is the July intercompany event real (two-sided)?

11 credit notes dated 22–23 Jul 2026, each ₹74–93 lakh, **all `BaseType = -1` (no base document)**, full SKU range, huge quantities (57,292 units Cold Press 1L; 30,749 Pomace Olive 1L).

```sql
SELECT TO_VARCHAR(h."DocDate",'YYYY-MM') AS M, h."CardCode", MAX(h."CardName") AS NM,
       COUNT(*) AS DOCS, ROUND(CAST(SUM(h."DocTotal"-IFNULL(h."VatSum",0)) AS DOUBLE)/100000,2) AS LAKH
FROM JIVO_MART_HANADB.ORPC h
WHERE h."CANCELED"='N' AND h."DocDate">='2026-07-01'
GROUP BY TO_VARCHAR(h."DocDate",'YYYY-MM'), h."CardCode" ORDER BY 5 DESC
```

| Mart-side A/P credit memo | Docs | ₹ lakh |
|---|---:|---:|
| JIVO WELLNESS PVT LTD (= the Oil company) | 15 | **878.53** |

**Verdict: mirrored, so not a booking fraud** — but ₹8.79–9.31 Cr of finished goods physically flowed back from the related distributor to the manufacturer in two days. Over 12M the Oil→Jivo Mart return rate is **10.3%** (₹18.51 Cr on ₹179.59 Cr). This is systematic over-push of stock into the related party. Working-capital, not P&L.

---

## H4 — Top customers by return value and return rate (Oil, 12M)

```sql
SELECT s."CardCode", MAX(s.NM) AS NAME, ROUND(SUM(s.SAL)/100000,2) AS SALES_L,
       ROUND(SUM(s.RET)/100000,2) AS RET_L,
       ROUND(100*SUM(s.RET)/NULLIF(SUM(s.SAL),0),1) AS RET_PCT
FROM ( SELECT "CardCode", MAX("CardName") AS NM,
         CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE) AS SAL, 0.0 AS RET
       FROM JIVO_OIL_HANADB.OINV
       WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
       GROUP BY "CardCode"
       UNION ALL
       SELECT "CardCode", MAX("CardName"), 0.0,
         CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)
       FROM JIVO_OIL_HANADB.ORIN
       WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
       GROUP BY "CardCode" ) s
GROUP BY s."CardCode" HAVING SUM(s.RET)>0 ORDER BY 4 DESC
```

| Customer | Sales ₹L | Ret ₹L | Rate |
|---|---:|---:|---:|
| JIVO MART PVT LTD (related) | 17,959 | 1,850.5 | 10.3% |
| WAL MART INDIA PVT LTD | 1,103 | 96.8 | 8.8% |
| SAI TRADERS LUDHIANA | 519 | 52.0 | 10.0% |
| ONENESS TRADERS | 393 | 48.4 | **12.3%** |
| OJAS TRADERS | 565 | 46.5 | 8.2% |
| R K WORLDINFOCOM PVT LTD | 58 | 38.4 | **66.7%** |
| **CHAUDHARY MARKETING** | 26.75 | 26.75 | **100.0%** |
| KAILIAN FOODS PVT LTD | 55.5 | 26.0 | **46.9%** |
| **DIN DAYAL DULI CHAND** | 22.86 | 22.87 | **100.1%** |
| JIOMART LUHARI Q1 | 95.4 | 18.6 | 19.4% (449 docs) |
| COMED CHEMICALS LIMITED | 37.0 | 12.3 | 33.1% |

**Verdict:** two accounts had **every rupee of sales reversed** (₹49.62 lakh combined). → [[finding-total-reversal-accounts]]

---

## H5 — Top customers by return value and rate (Mart, 12M)

| Customer | Sales ₹L | Ret ₹L | Rate |
|---|---:|---:|---:|
| R K WORLDINFOCOM PVT LTD | 6,540 | **963.9** | 14.7% |
| SUSTAINQUEST PRIVATE LIMITED | 2,675 | 520.9 | 19.5% |
| KNOWTABLE ONLINE SERVICES | 2,357 | 395.8 | 16.8% |
| ANTIZE FOODS PRIVATE LIMITED | 1,585 | 160.3 | 10.1% |
| CHIRAG ENTERPRISES MUMBAI | 1,430 | 139.8 | 9.8% |
| **KIRANAKART TECHNOLOGIES (Zepto)** | 114 | 122.6 | **107.9%** |
| FLIPKART INDIA PRIVATE LIMITED | 444 | 97.7 | 22.0% |
| HANDS ON TRADE PVT LTD | 442 | 86.0 | 19.5% |
| FLIPKART B2C Q1 | 807 | 57.7 | 7.1% (998 docs) |
| **SCOOTSY LOGISTICS (Swiggy)** | 18 | 34.3 | **188.2%** |
| OCTAVOS ENTERPRISE SOLUTIONS | 0 | 21.9 | **∞ (no sales)** |
| ZOMATO HYPERPURE | 75 | 19.2 | 25.7% |

Concentration test:

```sql
SELECT CASE WHEN "CardCode" IN ('CUSTA000048','CUSTA000907','CUSTA000592','CUSTA000927')
            THEN 'TOP4_ECOM' ELSE 'rest' END AS SEG,
       COUNT(*) AS DOCS,
       ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/10000000,2) AS RET_CR
FROM JIVO_MART_HANADB.ORIN
WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
GROUP BY 1
```

| Segment | Docs | ₹ Cr |
|---|---:|---:|
| **TOP-4 e-com accounts** | 323 | **20.41** |
| everything else | 1,913 | 7.04 |

**Verdict: 74% of Mart's ₹27.45 Cr returns come from 4 accounts and only 323 documents.** → [[finding-ecom-return-concentration]]

---

## H6 — Are return rates getting worse over time?

```sql
SELECT P, ROUND(SUM(S)/10000000,2) AS SALES_CR, ROUND(SUM(R)/10000000,2) AS RET_CR,
       ROUND(100*SUM(R)/NULLIF(SUM(S),0),1) AS PCT
FROM ( ... CASE WHEN "DocDate"<'2025-04-01' THEN 'FY24-25'
              WHEN "DocDate"<'2026-04-01' THEN 'FY25-26' ELSE 'FY26-27ytd' END ... )
GROUP BY P ORDER BY 1
```

| Period | Oil (all) | Oil ex-intercompany | Mart |
|---|---:|---:|---:|
| FY24-25 | 3.4% | **1.7%** | **9.5%** |
| FY25-26 | 4.3% | **3.0%** | **10.8%** |
| FY26-27 YTD | 10.0% | **4.3%** | **18.5%** |

**Verdict: structural deterioration, not noise.** Oil's third-party return rate has **2.5x'd in two years** (1.7% → 4.3%); Mart has nearly doubled (9.5% → 18.5%). → [[finding-return-rate-deterioration]]

---

## H7 — Credit notes issued with NO linked base document

```sql
SELECT l."BaseType",
       CASE WHEN l."BaseEntry" IS NULL THEN 'NO_BASE' ELSE 'LINKED' END AS LNK,
       COUNT(*) AS LINES, ROUND(CAST(SUM(l."LineTotal") AS DOUBLE)/100000,2) AS VAL_LAKH
FROM JIVO_OIL_HANADB.RIN1 l
JOIN JIVO_OIL_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
GROUP BY 1,2 ORDER BY 4 DESC
```

| Company | BaseType | Meaning | Lines | ₹ lakh |
|---|---|---|---:|---:|
| Oil | **-1** | **no base doc** | 1,336 | **1,279.38** |
| Oil | 13 | based on A/R invoice | 1,101 | 1,150.46 |
| Oil | 16 | based on goods return | 2,547 | 350.85 |
| Mart | **-1** | **no base doc** | 2,895 | **1,303.93** |
| Mart | 13 | based on A/R invoice | 1,074 | 1,270.74 |
| Mart | 16 | based on goods return | 11,783 | 170.80 |

**₹25.83 Cr/yr of credit notes (46% of all returns) are issued standalone** — no invoice, no goods-receipt document to prove the goods came back or that the credit matches an actual sale.

No-base share by account (Mart):

| Customer | No-base ₹L | Total ret ₹L | No-base % |
|---|---:|---:|---:|
| R K WORLDINFOCOM | 698.2 | 963.9 | **72.4%** |
| CHIRAG ENTERPRISES MUMBAI | 135.7 | 139.8 | **97.1%** |
| KIRANAKART (Zepto) | 97.5 | 122.6 | **79.6%** |
| HANDS ON TRADE | 61.4 | 86.0 | 71.4% |
| EVARA ENTERPRISES | 47.2 | 60.1 | 78.5% |
| SCOOTSY (Swiggy) | 24.0 | 34.3 | 70.0% |
| KNOWTABLE | 83.9 | 395.8 | 21.2% |
| SUSTAINQUEST | 74.4 | 520.9 | 14.3% |

**Verdict: the single biggest control gap in this lens.** → [[finding-unlinked-credit-notes]]

---

## H8 — Returns arriving long after the original invoice (policy breach)

```sql
SELECT CASE WHEN DD<=30 THEN 'a 0-30d' WHEN DD<=60 THEN 'b 31-60d'
            WHEN DD<=90 THEN 'c 61-90d' WHEN DD<=180 THEN 'd 91-180d'
            WHEN DD<=365 THEN 'e 181-365d' ELSE 'f >365d' END AS BUCKET,
       COUNT(*) AS LINES, ROUND(SUM(V)/100000,2) AS LAKH
FROM ( SELECT DAYS_BETWEEN(i."DocDate", h."DocDate") AS DD,
              CAST(l."LineTotal" AS DOUBLE) AS V
       FROM JIVO_MART_HANADB.RIN1 l
       JOIN JIVO_MART_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
       JOIN JIVO_MART_HANADB.OINV i ON i."DocEntry"=l."BaseEntry"
       WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
         AND l."BaseType"=13 )
GROUP BY 1 ORDER BY 1
```

| Bucket | Oil lines | Oil ₹L | Mart lines | Mart ₹L |
|---|---:|---:|---:|---:|
| 0–30d | 913 | 1,097.04 | 495 | 1,054.59 |
| 31–60d | 133 | 39.85 | 124 | 68.11 |
| **61–90d** | 38 | 3.04 | 117 | **83.07** |
| **91–180d** | 17 | 10.53 | 215 | **43.67** |
| **181–365d** | – | – | 123 | **21.30** |

**Verdict: Mart accepted ₹1.48 Cr of returns more than 60 days after the sale** (₹0.14 Cr for Oil). Note this covers only the ~46% of returns that carry an invoice link — the true figure is likely higher because unlinked credits cannot be aged at all. → [[finding-stale-returns-accepted]]

---

## H9 — Are returns credited at a higher price than the original sale? (rate leakage)

```sql
SELECT CASE WHEN r."Price" > i."Price"*1.001 THEN 'CREDITED_HIGHER'
            WHEN r."Price" < i."Price"*0.999 THEN 'credited_lower' ELSE 'same' END AS CMP,
       COUNT(*) AS LINES,
       ROUND(CAST(SUM(r."LineTotal") AS DOUBLE)/100000,2) AS CREDIT_L,
       ROUND(CAST(SUM((r."Price"-i."Price")*r."Quantity") AS DOUBLE)/100000,2) AS EXCESS_L
FROM JIVO_OIL_HANADB.RIN1 r
JOIN JIVO_OIL_HANADB.ORIN h ON h."DocEntry"=r."DocEntry"
JOIN JIVO_OIL_HANADB.INV1 i ON i."DocEntry"=r."BaseEntry" AND i."LineNum"=r."BaseLine"
WHERE h."CANCELED"='N' AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
  AND r."BaseType"=13 AND IFNULL(i."Price",0)>0
GROUP BY 1
```

| Company | same | credited higher | excess ₹L |
|---|---:|---:|---:|
| Oil | 1,046 lines / ₹1,149.76 L | 5 lines / ₹0.42 L | **+0.38** |
| Mart | 1,040 lines / ₹1,269.76 L | 2 lines / ₹0.01 L | **0.00** |

**Verdict: KILLED — no rate leakage on linked returns.** SAP copies the invoice price correctly. Clean control. (Caveat: only testable on the 46% with a base link.)

---

## H10 — Do returned goods actually re-enter stock?

```sql
SELECT "DocType", IFNULL("UpdInvnt",'?') AS UPDINV, IFNULL("InvntSttus",'?') AS INVSTAT,
       COUNT(*) AS DOCS, ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/100000,2) AS LAKH
FROM JIVO_OIL_HANADB.ORIN
WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' AND "DocDate"<'2026-07-29'
GROUP BY 1,2,3
```

Every `ORIN` in both companies has `"UpdInvnt" = 'I'` — all item-type credit notes post an inventory receipt.

**Verdict: KILLED as a leakage vector** — returns are booked back into stock in the books. (Whether the physical goods are saleable is a separate question this lens cannot answer from SAP.)

---

## H11 — "Service" credit notes: trade spend disguised as returns

```sql
SELECT UPPER(SUBSTR(IFNULL(l."Dscription",'(blank)'),1,50)) AS DESCR, COUNT(*) AS LINES,
       ROUND(CAST(SUM(l."LineTotal") AS DOUBLE)/100000,2) AS LAKH
FROM JIVO_MART_HANADB.RIN1 l
JOIN JIVO_MART_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
WHERE h."CANCELED"='N' AND h."DocType"='S'
  AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
GROUP BY 1 ORDER BY 3 DESC
```

| Line description | Company | Lines | ₹ lakh |
|---|---|---:|---:|
| BUSINESS PROMOTION | Mart | 108 | 176.54 |
| PROMOTIONAL DISCOUNT | Oil | 258 | 129.10 |
| PROMOTIONAL DISCOUNT | Mart | 17 | 80.89 |
| FREIGHT AND CARTAGE | Mart | 8 | 9.31 |
| RENT RECEIVED | Oil | 5 | 7.90 |
| DIWALI GIFT | Oil | 20 | 6.66 |
| BRAND FUND DISCOUNT | Mart | 3 | 5.93 |
| SAMPLING EXPENSES | Mart | 19 | 2.85 |
| LOSS ON EXPIRED DAMAGED THEFT GOODS | Oil | 13 | 0.70 |

Service-type credit notes total: Oil ₹1.48 Cr + Mart ₹2.76 Cr + Bev ₹0.05 Cr = **₹4.29 Cr/yr**, of which **₹3.87 Cr is pure trade spend** (business promotion / promotional discount / brand fund).

**Verdict:** ₹3.87 Cr/yr of promotional spend is routed through credit notes instead of a trade-spend expense head. It (a) suppresses reported turnover, (b) escapes any promo-budget control, (c) is 100% unlinked to a base document so no one can verify the claim was earned. → [[finding-trade-spend-as-credit-notes]]

---

## H12 — Which SKUs get returned most?

| Item | Oil sales ₹L | Oil ret ₹L | Oil % | Mart sales ₹L | Mart ret ₹L | Mart % |
|---|---:|---:|---:|---:|---:|---:|
| SANO POMACE OLIVE 5 LTR TIN | 1,235.8 | 147.4 | 11.9 | 645.5 | 214.5 | **33.2** |
| POMACE OLIVE 1 LTR 16 PCS | 2,116.6 | 160.4 | 7.6 | 1,600.8 | 211.1 | 13.2 |
| POMACE OLIVE 5 LTR TIN | 2,647.8 | 142.1 | 5.4 | 1,497.9 | 209.3 | 14.0 |
| COLD PRESS 1 LTR 20 PCS | 1,697.3 | 158.0 | 9.3 | 635.4 | 139.4 | **21.9** |
| SANO POMACE OLIVE 1 LTR | 1,254.1 | 110.2 | 8.8 | 533.0 | 115.8 | **21.7** |
| EXTRA LIGHT OLIVE 5 LTR TIN | 756.7 | 146.5 | **19.4** | – | – | – |
| MUSTARD KACCHI GHANI 5 LTR | 1,693.6 | 158.1 | 9.3 | 1,070.6 | 97.2 | 9.1 |
| COLD PRESS GROUNDNUT 5 LTR | 874.3 | 103.5 | 11.8 | – | – | – |

**Verdict:** returns are **not** a single-SKU defect — they are broad-based across the whole portfolio, and the SAME SKU returns 2-3x more through Mart (e-com) than through Oil (general trade). This points at **channel behaviour, not product quality**. Worst offender: SANO POMACE OLIVE 5 LTR TIN at 33.2% through Mart.

---

## H13 — Returns by geography / customer group

| Oil group | Sales ₹Cr | Ret ₹Cr | % | | Mart group | Sales ₹Cr | Ret ₹Cr | % |
|---|---:|---:|---:|---|---|---:|---:|---:|
| DELHI | 258.33 | 20.45 | 7.9 | | PAN INDIA | 75.68 | 11.51 | **15.2** |
| PUNJAB | 70.48 | 2.66 | 3.8 | | HARYANA | 33.79 | 6.69 | **19.8** |
| PAN INDIA | 31.80 | 2.09 | 6.6 | | KARNATAKA | 23.58 | 3.99 | **16.9** |
| HARYANA | 17.20 | 0.97 | 5.6 | | DELHI | 31.15 | 2.81 | 9.0 |
| ANDHRA PRADESH | 0.95 | 0.19 | **19.4** | | MAHARASHTRA | 14.43 | 1.40 | 9.7 |
| STAFF CUSTOMER | 0.36 | 0.09 | **25.4** | | PUNJAB | 13.30 | 0.60 | 4.5 |

**Verdict:** Mart's "PAN INDIA" + "HARYANA" + "KARNATAKA" groups (the e-com/q-commerce fulfilment geographies) run 15–20%, versus 4.5% for Punjab general trade. Confirms H12's channel conclusion.

---

## H14 — Accounts where returns EXCEED sales (all-time sanity check)

```sql
SELECT x.CC, MAX(x.NM) AS NAME, ROUND(SUM(x.S)/100000,2) AS SALES_ALLTIME_L,
       ROUND(SUM(x.R)/100000,2) AS RET_ALLTIME_L
FROM ( ...OINV UNION ALL ORIN, no date filter... ) x GROUP BY x.CC
```

| Account | All-time sales ₹L | All-time returns ₹L | All-time rate |
|---|---:|---:|---:|
| **KIRANAKART TECHNOLOGIES (Zepto)** | 490.8 | 206.5 | **42.1%** |
| SCOOTSY LOGISTICS (Swiggy) | 708.4 | 78.8 | 11.1% |
| **OCTAVOS ENTERPRISE SOLUTIONS** | 63.6 | 33.2 | **52.2%** |
| FREE SAMPLE | 3.79 | 3.97 | 104.7% |
| FASHNEAR (Meesho) Q1 | 0.12 | 3.07 | n/m — code migration |

**Verdict:** the >100% 12-month rates for Scootsy and Fashnear are **timing/card-code artefacts** (prior-period sales, split Q1 codes) — honest caveat, not leakage. But **Kiranakart/Zepto is real: 42% of everything ever sold to them has come back** (₹2.07 Cr on ₹4.91 Cr), and Octavos 52%. → [[finding-zepto-return-rate]]

---

## H15 — Credit notes to customers with zero sales in the window

| Company | Customer | Docs | ₹ lakh |
|---|---|---:|---:|
| Mart | OCTAVOS ENTERPRISE SOLUTIONS B2B | 1 | 21.88 |
| Oil | SHREE SHYAM ENTERPRISES | 1 | 2.00 |
| Oil | M/S GOPAL ENTERPRISES | 1 | 0.68 |
| Oil | HARSIRJAN SINGH BAKSHI | 2 | 0.42 |

**Verdict: mostly KILLED** — only ₹0.25 Cr, and plausibly legitimate returns against prior-year sales. Flag the ₹21.88 lakh Octavos credit for one document review.

---

## H16 — Month-end window dressing, and salesperson concentration

Month-end clustering (Mart):

| Bucket | Docs | ₹ Cr |
|---|---:|---:|
| days 1–25 | 730 | 20.30 |
| last 5 days | 1,506 | 7.16 |

**Verdict: KILLED.** More documents at month-end but far less value — routine e-com reconciliation batches, not value stuffing.

Salesperson (Oil, ex-intercompany): ₹6.04 Cr of ₹9.70 Cr returns carry **"-No Sales Employee / Buyer-"**. Worst named reps: KAMALDEEP SINGH 18.7%, HARPREET SINGH 12.9%, PRINCE 7.4% vs 3.5% company average.

**Verdict: partial.** 62% of returns have no salesperson attribution at all, so return rate cannot be put into any incentive scheme today. That is itself the finding.

---

## H17 — Sizing: what if the worst offenders returned at benchmark?

```sql
SELECT ROUND(SUM(S)/10000000,2) AS SALES_CR, ROUND(SUM(R)/10000000,2) AS RET_CR,
       ROUND(100*SUM(R)/SUM(S),2) AS RATE_PCT,
       ROUND(SUM(GREATEST(0, R - S*0.05))/10000000,2) AS EXCESS_OVER_5PCT_CR,
       ROUND(SUM(GREATEST(0, R - S*0.10))/10000000,2) AS EXCESS_OVER_10PCT_CR
FROM ( SELECT x.CC, SUM(x.S) AS S, SUM(x.R) AS R FROM ( ... ) x
       GROUP BY x.CC HAVING SUM(x.S)>0 )
```

| Book | Sales | Returns | Rate | Excess >3% | Excess >5% | Excess >10% |
|---|---:|---:|---:|---:|---:|---:|
| Oil (ex-intercompany) | ₹280.49 Cr | ₹9.70 Cr | 3.46% | ₹4.90 Cr | **₹3.56 Cr** | – |
| Mart | ₹204.69 Cr | ₹27.24 Cr | 13.31% | – | ₹18.04 Cr | **₹9.91 Cr** |

**Verdict:** capping every customer at a 10% return allowance in Mart and 5% in Oil recovers **₹13.47 Cr/yr of reversed sales**. → [[finding-excess-returns-above-benchmark]]

---

## ⚠️ Material caveats (read before acting)

1. **Item costs are not maintained.** `OITM."AvgPrice"` is **zero for every item in every warehouse**, so SAP reports gross profit at 95–99% on both sales and returns. **The ₹ figures in this note are reversed net sales, not lost gross margin.** True P&L damage = margin on those sales + two-way freight + any goods that come back unsaleable. Fixing item costing is a prerequisite to sizing this properly.
2. **Intercompany distortion.** JIVO MART PVT LTD is a related party. Its ₹18.51 Cr of Oil returns is internal stock movement, correctly mirrored on Mart's A/P side. It must be excluded from "customer return" KPIs — the Oil headline drops from 6.1% to 3.46% once removed.
3. **>100% return rates** for Scootsy/Fashnear are card-code and period artefacts, not leakage. Kiranakart's 42% all-time rate is not.
4. **Aging (H8) is only measurable on the 46% of credit notes that carry an invoice link.** The ₹1.48 Cr stale-return figure is a floor.
5. E-commerce and q-commerce returns are partly a **structural channel cost** (marketplace RTO, FBF reconciliation, near-expiry pullbacks). The recoverable share is the excess over a negotiated allowance, not the whole number.
6. Overlaps: [[finding-zepto-return-rate]] and [[finding-total-reversal-accounts]] sit **inside** [[finding-excess-returns-above-benchmark]]. Do not add them together.

---

## Actions, ranked

1. **Freeze standalone credit notes.** Require `BaseType` 13 or 16 (invoice or goods-return) on every A/R credit note; route exceptions through a named approver. Kills the ₹25.83 Cr/yr unverifiable-credit exposure.
2. **Put a contractual return cap in the top-4 Mart e-com contracts** (R K Worldinfocom, Sustainquest, Knowtable, Antize) — 74% of Mart returns, only 323 documents to police. Target 10%.
3. **Stop or re-price Kiranakart/Zepto** — 42% all-time return rate, 80% of it unlinked.
4. **Enforce the 60-day return window.** ₹1.48 Cr of Mart returns breached it in 12 months.
5. **Move promotional spend out of credit notes** into a trade-spend expense head (₹3.87 Cr/yr) so it is budgeted and claim-verified.
6. **Populate item standard costs** so returns can be measured in margin, not revenue.
7. **Review the 2 total-reversal accounts** (Chaudhary Marketing, Din Dayal Duli Chand — ₹49.62 lakh) and the ₹21.88 lakh Octavos credit as individual documents.
8. **Attribute every return to a salesperson** and net returns off sales incentives — 62% of Oil returns currently have no rep attached.

Back-links: [[SAVINGS-MOC]] · [[2026-07-28]]
