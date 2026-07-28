---
title: Expense Outliers — expense-head spikes, interest & bank charges
created: 2026-07-28
lens: expense-outliers
tags: [savings-audit]
---

# 💸 Expense Outliers — where the P&L bleeds

Part of [[SAVINGS-MOC]]

**Lens question:** which expense heads are bleeding money — through growth that outruns sales, one-off losses nobody recovered, avoidable statutory penalties, or costs that simply stopped being controlled?

**Scope:** all 3 HANA companies — `JIVO_OIL_HANADB` (Oil), `JIVO_MART_HANADB` (Mart), `JIVO_BEVERAGES_HANADB` (Beverages). As-of **2026-07-28**.
**Periods:** FY25-26 = `2025-04-01 … 2026-03-31` (complete). FY26-27 YTD = `2026-04-01 … 2026-07-28` (4 months, current month part-posted). Like-for-like YoY windows are **Apr 1 – Jul 28** in both years.

---

## 0. Method & the traps that would have broken this analysis

**Trap 1 — the HANA driver returns exact rationals, not decimals.** `SUM("Debit")` renders as `3001370429/10`. Every figure below is wrapped in `TO_BIGINT(ROUND(…,0))`. Without this the whole analysis is unreadable and silently mis-parsed.

**Trap 2 — expenses must be measured net, not as gross debits.** Many heads are provisioned monthly and reversed. `SUM("Debit")` alone overstated freight by ₹1.71 Cr. Everything below uses `SUM("Debit") - SUM("Credit")`.

**Trap 3 — the chart of accounts lumps everything into drawer 5.** `OACT."GroupMask"=5` covers COGS (`50000xx`), purchases (`5400xx`), direct costs (`51000xx`) *and* true overhead (`561xxxx`–`569xxxx`). Ranking drawer 5 raw just returns COGS. Overhead analysis is restricted to prefixes `561`–`569`.

**Trap 4 — "duplicate" patterns are mostly legitimate.** Every same-amount/same-date cluster tested here resolved to genuine per-truckload invoices or balanced multi-line JEs. Duplicate hunting without drilling to `PCH1`/`OJDT` would have produced several false ₹-crore "findings". See H6–H8.

**Trap 5 — two of the largest counterparties are group companies.** `VENDA000483` = JIVO MART PVT LTD and `VENDA000001` = JIVO WELLNESS PVT LTD. Intercompany recharges dominate the advertisement head and the Mart purchase-variance head. They net to zero at group level and are flagged as such.

**Sales base used for ratios** (`OINV` net of GST, less `ORIN` returns, `"CANCELED"='N'`):

| Window | Oil net sales |
|---|---|
| Apr–Jul 2025 | ₹158.87 Cr |
| Apr–Jul 2026 | ₹133.16 Cr (**−16.2%**) |
| FY25-26 full | ₹442.19 Cr |

> Caveat: the ₹193.91 Cr FY25-26 turnover figure carried in CLAUDE.md does not reconcile to `OINV`−`ORIN` for the same period (₹442.19 Cr). The monthly figures *do* reconcile (Jul-2026 = ₹27.43 Cr vs the ~₹26 Cr calibration), so the ratio **trends** below are sound; the absolute annual base may be defined differently (e.g. excluding intercompany). Ratio findings are therefore stated as like-for-like deltas, not as absolute percentages of "turnover".

---

## 1. The overhead map (H1) — where the money actually is

```sql
SELECT SUBSTRING(a."AcctCode",1,3) AS GRP,
 TO_BIGINT(ROUND(SUM(CASE WHEN j."RefDate">='2025-04-01' AND j."RefDate"<'2025-07-29' THEN IFNULL(j."Debit",0)-IFNULL(j."Credit",0) ELSE 0 END),0)) AS PY_APRJUL,
 TO_BIGINT(ROUND(SUM(CASE WHEN j."RefDate">='2026-04-01' AND j."RefDate"<'2026-07-29' THEN IFNULL(j."Debit",0)-IFNULL(j."Credit",0) ELSE 0 END),0)) AS CY_APRJUL,
 TO_BIGINT(ROUND(SUM(CASE WHEN j."RefDate">='2025-04-01' AND j."RefDate"<'2026-04-01' THEN IFNULL(j."Debit",0)-IFNULL(j."Credit",0) ELSE 0 END),0)) AS FY2526
FROM JIVO_OIL_HANADB.JDT1 j JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE a."GroupMask"=5 AND SUBSTRING(a."AcctCode",1,3) IN ('561','562','563','564','565','566','567','568','569')
 AND j."RefDate">='2025-04-01'
GROUP BY SUBSTRING(a."AcctCode",1,3) ORDER BY GRP;
```

Oil (₹, net debit):

| Grp | Head | PY Apr–Jul | CY Apr–Jul | FY25-26 |
|---|---|---|---|---|
| 561 | Finance cost | 1,24,74,003 | 1,09,70,859 | **4,71,71,418** |
| 562 | Depreciation | 0 | 0 | 7,98,21,054 |
| 563 | Employee cost | 3,81,86,499 | 3,91,18,945 | **15,05,36,966** |
| 564 | Selling & marketing | 24,45,881 | 1,45,09,445 | 8,09,93,885 |
| 565 | Repairs & maintenance | 17,10,173 | **35,44,945** | 70,70,132 |
| 566 | Rent, rates & taxes | 77,63,621 | 37,48,212 | 2,21,75,831 |
| 567 | Freight & loading out | 1,31,36,980 | **1,44,82,203** | 3,35,54,247 |
| 568 | Admin & other | 2,94,41,960 | 75,61,592 | 5,81,22,319 |
| 569 | Travel | 9,15,328 | 14,04,365 | 44,96,991 |

**Group overhead FY25-26: Oil ₹48.39 Cr · Mart ₹9.31 Cr · Beverages ₹6.07 Cr = ₹63.77 Cr.**

Two heads grew while sales fell 16.2%: **repairs (565, +107%)** and **freight out (567, +10.2%)**. Selling & marketing (564) looks explosive but is a booking-timing artefact — see H18.

---

## 2. [[finding-transit-loss-uninsured]] — ₹1.66 Cr of goods lost, ₹1.40 Cr of claims written off (H11)

The single largest discrete loss in the books.

```sql
SELECT TO_VARCHAR(j."RefDate",'YYYY-MM-DD') AS DT, j."TransId" AS TID,
 TO_BIGINT(ROUND(IFNULL(j."Debit",0),0)) AS DR, TO_BIGINT(ROUND(IFNULL(j."Credit",0),0)) AS CR, j."LineMemo" AS MEMO
FROM JIVO_OIL_HANADB.JDT1 j
WHERE j."Account" IN ('5680031','1107020','4200008') AND j."RefDate">='2024-08-01'
ORDER BY j."Account", j."RefDate";
```

**The loss** — `5680031 LOSS IN TRANSIT`, only 3 entries, all `Goods Issue`:

| Date | Amount | Memo |
|---|---|---|
| 2025-04-16 | 40,38,709 | Goods Issue |
| 2025-05-31 | 99,59,875 | Goods Issue |
| 2025-07-16 | 26,49,514 | Goods Issue |
| | **1,66,48,098** | |

**The claim** — `1107020 INSURANCE CLAIM RECEIVABLE`:

| Date | Dr | Cr | Memo |
|---|---|---|---|
| 2025-04-16 | 40,38,709 | | CLAIM AGAINST ACCIDENT TANKER |
| 2025-05-31 | 99,59,875 | | CLAIM AGAINST ACCIDENT TANKER |
| 2026-03-31 | | 40,38,709 | CLAIM AGAINST ACCIDENT TANKER-**Raversal** |
| 2026-03-31 | | 99,59,875 | CLAIM AGAINST ACCIDENT TANKER-**Reversal** |

₹1,39,98,584 of insurance claim was booked as receivable and then **written back in full on 31-Mar-2026**.

**What was actually recovered** — `4200008 INSURANCE CLAIM RECEIPT A/C`, FY25-26: **₹4,57,664** only ("INSURANCE RECEIVED AGAINST BLACK OLIVES FROM TATA AIG", 2025-07-16). Recovery rate **2.8%**.

**And it cost more than the goods.** ITC on the lost stock had to be reversed via DRC-03 (`5660008`): ₹2,13,835 + ₹5,16,262 + ₹3,25,336 = **₹10,55,433**.

Meanwhile Oil paid **₹32,24,251** of `5680002 INSURANCE INDIRECT` premium in FY25-26.

> **Verdict: ₹1,39,98,584 one-time recovery opportunity.** Two accident-tanker claims were carried for a year and written off without recovery. The write-off may reflect a genuine repudiation — but nothing in SAP records one, and a 2.8% recovery rate against a paid insurance programme is not a normal outcome. **Action:** pull the two claim files, confirm whether they were formally filed, repudiated, or allowed to become time-barred, and re-open with the insurer/broker.

---

## 3. [[finding-production-variance-spike]] — ₹2.04 Cr of production variance in one month, ₹0 in every other (H2)

`5100003 WORK IN PROGRESS VARIANCE PRODUCTION` is a clearing account. It nets to **exactly zero** in 12 of the prior 16 months.

```sql
SELECT SUBSTRING(TO_VARCHAR(j."RefDate",'YYYY-MM-DD'),1,7) AS MON, COUNT(*) AS LINES,
 TO_BIGINT(ROUND(SUM(IFNULL(j."Debit",0)),0)) AS DR, TO_BIGINT(ROUND(SUM(IFNULL(j."Credit",0)),0)) AS CR,
 TO_BIGINT(ROUND(SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)),0)) AS NET
FROM JIVO_OIL_HANADB.JDT1 j WHERE j."Account"='5100003' AND j."RefDate">='2025-04-01'
GROUP BY SUBSTRING(TO_VARCHAR(j."RefDate",'YYYY-MM-DD'),1,7) ORDER BY MON;
```

| Month | Dr | Cr | **Net** |
|---|---|---|---|
| 2025-04 … 2026-05 | — | — | **0** (except Apr-25 ₹17,634 / Aug-25 ₹33,683) |
| 2026-06 | 5,25,54,722 | 5,22,24,048 | 3,30,674 |
| **2026-07** | **8,49,14,207** | **6,44,77,684** | **2,04,36,523** |

**This is not a month-end timing artefact.** At the identical point last year the account was flat:

```sql
SELECT 'PY 01-28 Jul 2025' AS PERIOD, TO_BIGINT(ROUND(SUM(IFNULL("Debit",0)-IFNULL("Credit",0)),0)) AS NET
FROM JIVO_OIL_HANADB.JDT1 WHERE "Account"='5100003' AND "RefDate">='2025-07-01' AND "RefDate"<'2025-07-29'
UNION ALL SELECT 'CY 01-28 Jul 2026', … ;
```

| Period | Net |
|---|---|
| PY 01–28 Jul 2025 | **0** |
| CY 01–28 Jul 2026 | **2,04,36,523** |
| PY 01–28 Jun 2025 | 0 |
| CY 01–28 Jun 2026 | 3,30,674 |

**Where it came from.** 100% `TransType` 202 (production order). ₹1.96 Cr landed on a single day, 2026-07-23, across 204 lines — a bulk close-out of production orders, contra `1103009 WORK IN PROGRESS PRODUCTION`:

| TransId | Dr | Memo |
|---|---|---|
| 221445 | 45,74,634 | Production Order - RM0000001 |
| 221423 | 30,41,609 | Production Order - FG0000030 |
| 221454 | 26,80,081 | Production Order - RM0000002 |
| 221355 | 21,48,153 | Production Order - FG0000011 |
| 221345 | 18,98,770 | Production Order - FG0000008 |
| … | | (204 lines total) |

**It is a real P&L charge, not a balance-sheet parking.** The WIP asset `1103009` is a pass-through — its balance today is **−₹2,72,229**, i.e. essentially nil. So components issued exceeded the value of finished goods received by ₹2.04 Cr. Against July WIP throughput of ₹52.20 Cr that is a **3.92% yield/costing loss**.

> **Verdict: ₹2,04,36,523.** The number is certain; its cause is not. Either (a) genuine accumulated yield loss finally recognised, or (b) a costing/BOM error in the bulk close. Either way the control gap is real — production variance was **not being recognised monthly** for 16 months, so nobody could see it building. **Action:** have production reconcile the 23-Jul close order-by-order, and switch to monthly variance recognition.

---

## 4. [[finding-freight-intensity-drift]] — freight per ₹ of sales up 32% (H4)

```sql
WITH S AS (SELECT SUBSTRING(TO_VARCHAR("DocDate",'YYYY-MM-DD'),1,7) AS MON, SUM("DocTotal"-IFNULL("VatSum",0)) AS NETSALE
           FROM JIVO_OIL_HANADB.OINV WHERE "CANCELED"='N' AND "DocDate">='2025-04-01' GROUP BY …),
     R AS (… ORIN returns …),
     F AS (SELECT …, SUM(CASE WHEN "Account" IN ('5670001','5670003') THEN IFNULL("Debit",0)-IFNULL("Credit",0) ELSE 0 END) AS FRT_OUT
           FROM JIVO_OIL_HANADB.JDT1 WHERE "RefDate">='2025-04-01' GROUP BY …)
SELECT S."MON", TO_BIGINT(ROUND(S."NETSALE"-IFNULL(R."RET",0),0)) AS NETSALES, TO_BIGINT(ROUND(IFNULL(F."FRT_OUT",0),0)) AS FRT_OUT
FROM S LEFT JOIN R ON R."MON"=S."MON" LEFT JOIN F ON F."MON"=S."MON" ORDER BY MON;
```

| Window | Freight out | Net sales | **Ratio** |
|---|---|---|---|
| Apr–Jul **2025** | 1,25,82,528 | 158.87 Cr | **0.792%** |
| Apr–Jul **2026** | 1,39,51,794 | 133.16 Cr | **1.048%** |

Sales **−16.2%**, freight **+10.9%**. Intensity up **+25.6 bps (+32% relative)**.

Excess at current volumes = 0.2557% × ₹133.16 Cr = **₹34.05 lakh over 4 months → ₹1.02 Cr annualised**.

**The transporter base is fragmented** (FY25-26, `5670001`, top vendors):

| Vendor | Amount | Docs |
|---|---|---|
| DELHI PUNJAB TRANSPORT CO | 71,75,170 | 108 |
| OM LOGISTICS SUPPLY CHAIN PVT LTD | 53,58,578 | 68 |
| MAHADEV TEMPO SERVICE | 31,42,237 | 56 |
| ARNAV TRANSPORT SERVICE | 21,57,675 | 63 |
| BOMBAY SRINAGAR TRANSPORT REGD | 20,81,494 | 23 |
| GURU NANAK TRANSPORT SERVICE | 18,08,400 | 34 |
| OM LOGISTICS LTD | 16,55,676 | 17 |
| …11 more >₹2 lakh | | |

Note **OM LOGISTICS appears under two vendor codes** (`VENDA001367`, `VENDA000055`) totalling ₹70,14,254 — spend is invisible as a single relationship, which weakens rate negotiation.

> **Caveat (important):** freight is provisioned monthly and trued-up at year-end. On 2026-03-31 Oil reversed **₹1,71,02,522** "Reversal of Provision of Freight" plus Dec/Jan/Feb reversals. Both Apr–Jul windows are pre-reversal so the comparison is like-for-like *only if* provisioning intensity was the same in both years. Confidence: **medium**.
>
> **Verdict: ₹1.02 Cr/yr annual-recurring.** Action: consolidate the two OM Logistics codes, put the top-8 lanes on rate contracts, and reconcile the freight provision monthly instead of annually.

---

## 5. [[finding-gst-itc-reversals]] — ₹71.46 lakh/yr of input credit thrown away (H10)

`5660008 GST EXPENSE/INELIGIBLE CREDIT`, Oil, FY25-26 = **₹71,45,770** over 16 entries.

| Date | Amount | Memo |
|---|---|---|
| 2025-06-30 | 34,16,870 | GST input reversal related to GSTR-9 return |
| 2025-06-30 | 8,67,607 | GST input reversal as per GST annual return |
| 2025-06-30 | 25,533 | GST reversal related to annual return FY 2024-25 |
| 2025-08-01 | 2,13,835 | DRC-03 reversal for goods lost in transit |
| 2025-08-01 | 5,16,262 | DRC-03 file for ITC reversal on goods lost in transit |
| 2025-08-18 | 3,25,336 | DRC-03 filed for loss on Black Olive |
| 2026-02-02 | 51,986 | Outgoing Payments |
| 2026-03-01 | 7,88,848 | GST input reversal in books (annual return-**HR**) |
| 2026-03-01 | 54,688 | GST input reversal in books (annual return-**DL**) |
| 2026-03-01 | 8,84,804 | **GST audit period 2020-21 to 2023-24** (6 entries) |

Three distinct root causes, three different fixes:
1. **₹51.5 lakh — annual-return (GSTR-9) reversals.** ITC claimed in-year that did not survive the 2A/2B match, i.e. suppliers who did not file. Recoverable from those suppliers.
2. **₹10.55 lakh — DRC-03 on goods lost in transit.** Mandatory under s.17(5)(h); avoidable only by avoiding the loss (see §2).
3. **₹8.85 lakh — GST audit demands for 2020-21 → 2023-24.** Legacy.

> **Verdict: ₹71,45,770/yr annual-recurring.** The ~₹51.5 lakh GSTR-9 slice is the addressable one. **Action:** enforce GSTR-2B reconciliation *before* releasing vendor payment, and recover reversed credit from non-filing vendors.

---

## 6. [[finding-financing-cost]] — ₹4.72 Cr/yr, and the price of every locked rupee (H3)

```sql
SELECT a."AcctCode", a."AcctName", TO_BIGINT(ROUND(SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)),0)) AS BAL_NOW
FROM JIVO_OIL_HANADB.JDT1 j JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE (UPPER(a."AcctName") LIKE '%BANK%' OR UPPER(a."AcctName") LIKE '%LOAN%') AND a."GroupMask" IN (1,2)
GROUP BY a."AcctCode", a."AcctName" HAVING SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)) < -1000000 ORDER BY BAL_NOW;
```

**Cost (Oil, FY25-26):**

| Head | Amount |
|---|---|
| 5610001 Interest on bank loan | 4,12,67,402 |
| 5610004 Interest on unsecured loan | 26,68,589 |
| 5610003 Bank charges | 32,20,493 |
| 5200004 Bank charges — import | 51,869 |
| **Total finance cost** | **4,72,08,353** |

**Debt carried:**

| Facility | Balance |
|---|---|
| INDIAN BANK **CC** A/C 7007270527 | 28,39,23,377 |
| ICICI BANK LTD 629305042195 | 8,97,99,700 |
| Term loans (14 accounts, Indian Bank + ICICI) | 19,09,65,399 |
| **Bank debt** | **56,46,88,476** |
| Related-party loans (Gurpreet Singh, Nirmal Kaur, Charanjeet Kaur) | 10,43,23,952 |

**Blended effective rate on bank debt = 4,12,67,402 / 56,46,88,476 = 7.3%.**

Interest is *not* rising — Apr–Jul fell from ₹1,24,74,003 to ₹1,09,70,859 YoY. The finding is the **conversion rate for the other lenses**: the ₹28.39 Cr Indian Bank CC is revolving working-capital funding, so every ₹1 Cr released by [[receivables-aging]] or [[dead-slow-stock]] pays it down and saves **₹7.3 lakh/yr**.

> **Verdict: ₹2,07,26,406/yr of interest is carried purely on the CC facility** — the standing price tag on locked working capital. Not a saving on its own; it is the multiplier that makes the receivables and stock findings bankable.

One spike worth a note: April 2026 bank charges were ₹10,33,258 vs a ₹1–3 lakh norm, driven by a single ₹7,75,000 HSBC charge on 2026-04-17 (`TransId` 207122) — consistent with a facility/renewal fee, verified as a balanced 2-line JE, not a duplicate.

---

## 7. [[finding-repairs-escalation]] — repairs & maintenance +₹55.5 lakh/yr (H17)

| Company | FY25-26 | CY Apr–Jul | PY Apr–Jul | CY annualised | **Δ/yr** |
|---|---|---|---|---|---|
| Oil (565) | 70,70,132 | 35,44,945 | 17,10,173 | 1,06,34,835 | **+35,64,703** |
| Beverages (565) | 73,35,612 | 31,08,040 | 23,72,289 | 93,24,120 | **+19,88,508** |
| | | | | | **+55,53,211** |

Oil's plant & machinery head (`5650016`) has already spent ₹17,70,096 in 4 months against ₹14,80,139 for the *whole* of FY25-26.

**Control gap:** ₹13,91,161 of that (79%) is booked against `VENDA001219 = "EXPENSE PAYABLE"` — a generic accrual counterparty, not an identified supplier. Across all heads, ₹2.20 Cr of FY25-26 expense ran through this code (reversed in FY26-27, so it is a provisioning mechanism rather than a leak — but it hides who was actually paid).

Oil's building-repairs spend is largely construction material — SHREE RAM RMC (ready-mix concrete) ₹2,67,595, GUPTA CEMENT STORE ₹1,46,972, BAGGA & SONS ₹1,11,156 — which reads like **capital work expensed as repairs**. Classification issue, not a cash saving.

> **Verdict: ₹55,53,211/yr annual-recurring.** Confidence medium — a genuine step-up in maintenance activity is plausible for ageing plant. **Action:** require a named vendor on every P&M repair, and review the RMC/cement spend for capitalisation.

---

## 8. [[finding-statutory-penalties]] — ₹18.92 lakh/yr of pure avoidable waste (H9)

| Company | Account | FY25-26 | Detail |
|---|---|---|---|
| Oil | 5660009 Income tax previous periods | 11,44,647 | ₹10,16,599 "Interest on Income Tax" + ₹1,28,048 refund adjusted against demand |
| Oil | 5680005 Penalty charges | 2,60,450 | 22 entries |
| Oil | 5660011 Interest on TDS | 2,22,625 | single entry, 2025-05-31 |
| Mart | 5660009 Income tax previous periods | 2,64,341 | |
| | **Total** | **18,92,063** | |

Every rupee here is interest or penalty for paying a statutory due late. There is no business justification.

> **Verdict: ₹18,92,063/yr annual-recurring, 100% avoidable.** **Action:** statutory payment calendar with owner + reminder; this is the cheapest saving in the whole audit.

---

## 9. [[finding-related-party-recurring]] — ₹1.05 Cr/yr of fixed related-party payments (H14, H7)

**Professional retainers** (`5680025`, Oil, FY25-26) — three parties, each exactly ₹1,50,000 × 12:

| Party | Amount | Docs |
|---|---|---|
| JITENDER THUKRAL HUF | 18,00,000 | 12 |
| SUMIR TAGRA HUF | 18,00,000 | 12 |
| NIRMAL KAUR **DIRECTOR** | 18,00,000 | 12 |
| | **54,00,000** | |

That is **50% of the entire ₹1.09 Cr legal & professional head**. Genuine third-party advisers are a minority of it (KHANNA HIMANSHU & ASSOCIATES ₹11,00,500, JAGDEEP SINGH & CO ₹7,66,500, PwC ₹5,00,000).

**Mayapuri rent** (`5660002`) split across three members of one family for the same premises:

| Party | Amount |
|---|---|
| ARVIND TULI MAYAPURI RENT | 25,52,980 |
| AMIT SAIN TULI | 15,19,385 |
| RANJIT SAIN TULI MAYAPURI RENT | 10,33,595 |
| | **51,05,960** |

(Largest single landlord GEETA GUPTA ₹47,25,000 is separate; relationship not established from SAP.)

> **Verdict: ₹1,05,05,960/yr.** Confidence **low as a saving** — these are almost certainly deliberate related-party structures (HUF retainers and co-owned property are standard Indian promoter arrangements), not leakage. Recorded because it is ₹1.05 Cr of *fixed, discretionary, non-market-tested* annual cost. **Action:** benchmark the Mayapuri rent against market rate per sq ft and confirm the retainers have deliverables and s.40A(2)(b) documentation.

---

## 10. [[finding-mart-return-variance]] — ₹46.85 lakh absorbed on a 2-day intercompany return (H3b)

Mart's `5100014 PURCHASE VARIANCE ACCOUNT`: FY25-26 whole year **₹1,61,925**; FY26-27 YTD **₹46,81,551** — a 289× jump, all of it on 22–23 Jul 2026.

Every line is an A/P Credit Memo to `VENDA000001` = **JIVO WELLNESS PVT LTD** (Oil). Mart returned ~₹10.0 Cr of goods to Oil in two days across 12 credit memos (₹78–98 lakh each), and absorbed ₹46.85 lakh of price variance because the returns were credited below carrying cost.

| DocNum | Date | Total |
|---|---|---|
| 607265906 | 2026-07-22 | 97,65,000 |
| 607265915 | 2026-07-23 | 93,84,375 |
| 607265911 | 2026-07-23 | 91,79,336 |
| … 9 more | | |

> **Verdict: ₹46,81,551 one-time.** **Group-level impact is nil** — it nets against Oil. At Mart entity level it is a real P&L hit, and a ₹10 Cr two-day intercompany return with no comments recorded is a transfer-pricing and inventory-control question worth asking.

---

## 11. Hypotheses tested and killed — the controls that are working

These are recorded because each would have produced a large false finding.

**H6 — duplicate journal postings (same account + date + amount).** 40+ clusters surfaced; all drilled resolved to legitimate multi-party or multi-line postings (e.g. three ₹1,50,000 professional retainers on the same date = three different retainers; two ₹69,750 bank-charge lines in `TransId` 206896 = one balanced JE crediting HSBC ₹1,39,500).

**H7 — duplicate supplier invoices (same vendor + same `NumAtCard`).** All three companies:

```sql
SELECT p."CardCode", p."NumAtCard", COUNT(*) AS N, TO_BIGINT(ROUND(SUM(p."DocTotal")-MAX(p."DocTotal"),0)) AS DUP_EXPOSURE
FROM <S>.OPCH p WHERE p."CANCELED"='N' AND p."DocDate">='2025-04-01' AND p."NumAtCard" IS NOT NULL
GROUP BY p."CardCode", p."NumAtCard" HAVING COUNT(*)>1 AND SUM(p."DocTotal")-MAX(p."DocTotal")>50000;
```

Oil: 3 hits, **all dated a year apart** (2025 vs 2026) — suppliers reusing invoice numbers annually. Mart: **0**. Beverages: **0**.

**H8 — duplicate A/P invoices (same vendor + date + amount).** The largest cluster, ILAHI CO ₹25,41,202 × 7 in one week, resolved cleanly in `PCH1`: invoices ILAHI/001–ILAHI/010, each 1,500 tins × ₹1,615, each against its own Goods Receipt PO. Same for VAISHNODEVI AGRO (₹31,23,397 × 2, two GRPOs) and JIVO WELLNESS-HR (distinct inventory transfers).

> **A/P duplicate-payment control at JIVO is genuinely strong.** No recoverable duplicate payment was found in any of the three companies.

**H12 — import demurrage & detention.** Immaterial: Oil `5200007` = −₹1,386 FY25-26; Mart ₹2,44,401. Import heads are mostly *net credits*.

**H13 — cash-heavy expense accounts.** Negligible: `1105002 CASH IN HAND` balance ₹0, FY25-26 outflow ₹139. No account carries `OACT."CashBox"='Y'`. Low cash-control risk.

**H18 — advertisement "up 2,522%".** `5640001` Apr–Jul went ₹5,35,055 → ₹1,40,30,819. **Artefact.** FY25-26's ₹7.58 Cr was booked almost entirely on 2026-03-31 as a catch-up of intercompany recharges from JIVO Mart (`VENDA000483`) covering June-2025 → Jan-2026 — verified against Mart's `OINV` (invoices 703260270–703260320, comments "JUNE", "JULY", "Aug-25", "SEPTEMBER"…). Two apparent duplicates (₹57,60,304 × 2 and ₹61,48,650 × 2) are genuine consecutive monthly recharges of an equal fixed fee. FY26-27 is being booked monthly; annualised ₹4.2 Cr is **below** FY25-26.

**H21 — Beverages electricity "up from ₹680".** Artefact: `5680011` only started being used in Sep-2025. Steady ₹5–12 lakh/month since. No growth.

**H20 — salary intensity.** Oil salary Apr–Jul +6.1% (₹3.32 Cr → ₹3.52 Cr) on sales −16.2%; intensity 2.09% → 2.65%. This is ordinary operating leverage on a down quarter, not leakage — recorded as context, not a finding.

**Net gains found (the opposite of leakage):** `5200015 EXCHANGE FLUCTUATIONS` net credit ₹52,42,721 FY25-26 (₹43,11,473 YTD) and `5200013 UNLOADING SHORTAGE-IMPORT` net credit ₹18,17,065 (₹9,10,265 YTD).

---

## 12. Summary

| # | Finding | Company | ₹ | Kind | Confidence |
|---|---|---|---|---|---|
| 1 | [[finding-production-variance-spike]] | Oil | 2,04,36,523 | one-time | high (number) / med (cause) |
| 2 | [[finding-transit-loss-uninsured]] | Oil | 1,39,98,584 | one-time | medium |
| 3 | [[finding-related-party-recurring]] | Oil | 1,05,05,960 | recurring | low (as saving) |
| 4 | [[finding-freight-intensity-drift]] | Oil | 1,02,15,000 | recurring | medium |
| 5 | [[finding-gst-itc-reversals]] | Oil | 71,45,770 | recurring | high |
| 6 | [[finding-repairs-escalation]] | Oil + Bev | 55,53,211 | recurring | medium |
| 7 | [[finding-mart-return-variance]] | Mart | 46,81,551 | one-time | medium |
| 8 | [[finding-statutory-penalties]] | Oil + Mart | 18,92,063 | recurring | high |
| 9 | [[finding-financing-cost]] | Oil | 2,07,26,406 | wc-release enabler | high |

**23 hypotheses tested. 9 findings with money. 8 killed cleanly.**

Back-links: [[SAVINGS-MOC]] · [[receivables-aging]] · [[dead-slow-stock]] · [[purchase-price-variance]] · [[duplicate-payments]]
