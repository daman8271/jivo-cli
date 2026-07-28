---
title: Payroll leakage — TankhaPay attendance vs SAP pay — evidence note
created: 2026-07-28
lens: payroll-leakage
tags: [savings-audit, payroll, tankhapay, attendance, sap-b1, imprest]
---

# Payroll leakage — TankhaPay attendance vs what SAP actually pays

Part of [[SAVINGS-MOC]]

**Window:** attendance/biometric `2026-06-29 → 2026-07-28` (30 days, pulled live from TankhaPay account 2719). SAP payroll ledgers all-time / FY25-26 / FY26-27.
**Sources**
- `/Users/damanpreetsingh/jivo-cli/portals/tankhapay/reports/TankhaPay-Attendance-30d_2026-06-29_to_2026-07-28.xlsx` (611 employees × 30 days, `Summary` + `Daily grid` + `Daily totals` + `Legend`)
- `/Users/damanpreetsingh/jivo-cli/portals/tankhapay/TankhaPay-Mispunch-Report-29Jun-28Jul-2026.xlsx` (2,638 mis-punch employee-days, `Raw Data`)
- `/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql` — read-only SELECT against `JIVO_OIL_HANADB`, `JIVO_MART_HANADB`, `JIVO_BEVERAGES_HANADB`
- The TankhaPay CLI was **not** called live (cached JWT expired 2026-07-26 and the brief forbids a login-refresh). Everything below comes from the two exported workbooks + SAP.

---

## The payroll baseline (the ₹/day used everywhere below)

```sql
SELECT SUBSTRING(TO_VARCHAR(T0."RefDate",'YYYY-MM'),1,7) AS MTH,
       SUM(CAST(T1."Debit" AS DOUBLE))-SUM(CAST(T1."Credit" AS DOUBLE)) AS NET
FROM JIVO_OIL_HANADB.OJDT T0
JOIN JIVO_OIL_HANADB.JDT1 T1 ON T1."TransId"=T0."TransId"
WHERE T1."Account"=CAST(5630001 AS NVARCHAR) AND T0."RefDate">=TO_DATE('2025-04-01')
GROUP BY SUBSTRING(TO_VARCHAR(T0."RefDate",'YYYY-MM'),1,7) ORDER BY 1;
-- repeated on JIVO_MART_HANADB.5630001 ("SALARY") and JIVO_BEVERAGES_HANADB
```

| Company | GL | Jun-2026 salary expense |
|---|---|---:|
| Oil | 5630001 SALARY EXPENSE | ₹1,19,09,761 |
| Mart | 5630001 SALARY | ₹13,33,606 |
| Beverages | SALARY EXPENSE | ₹12,36,555 |
| **Group** | | **₹1,44,79,922 / month** |

Oil runs a flat ₹1.05–1.19 Cr every month for 15 straight months — payroll is the single most predictable big spend in the business.

- **Group annual payroll ≈ ₹17.38 Cr**
- Headcount on roll in the window (TankhaPay): **611**
- **Average cost per employee ≈ ₹23,699 / month ≈ ₹790 / calendar day ≈ ₹911 / working day**

> Caveat carried through the whole note: this is a blended average. Factory workers sit below it, the 61 people in the `Above 40K` unit sit above it. Where a finding is concentrated in the `Above 40K` band I use the ₹40,000/month floor that the unit name guarantees.

**A structural fact that matters:** SAP books salary in **74 summary journal lines per month** (`"Salary Ziaul Jun 2026"`, `"BACK OFFICE BELOW"`, `"sales below june-26"` …), never per employee. There is **no per-employee payroll record in SAP**. TankhaPay attendance is therefore the *only* control over who gets paid — which is why every gap below is un-caught by the books.

---

## H1 — Are there employees on the roll with **no attendance evidence at all**? ✅ BIG

Cross of the two workbooks: roster (611) × everyone who produced a biometric punch.

```python
# Summary sheet: Marked? != 'Marked'  →  HR never marked the month
# Mis-punch Raw Data: set of emp codes that produced ANY punch in 30 days
never   = [r for r in roster if r['Marked?'] != 'Marked']          # 101
ghost   = [r for r in never  if r['Org code'] not in punch_codes]  # 100
```

| Cut | Count |
|---|---:|
| On roll for the full 30 days | 611 |
| Attendance never marked in the window | **101** |
| …of which **zero biometric punches too** | **100** |
| …of which **also `Unmarked` in June** (60 days, no evidence) | **83** |
| Days on roll = 30 (not new joiners) | 93 of 100 |

By unit: Sales Office 40 · Factory 31 · Head Office 15 · Above 40K 10 · Interns 4.
By job type: Permanent 100, Contractual 1.

The Factory slice is the loudest: 31 people posted to `JIVO_PLANT & PRODUCTION`, `CANOLA FACTORY`, `Warehouse`, designations `WORKER` / `Operator` / `Helper` / `Supervisor`, who neither punched a biometric machine nor had a single day marked in two months. A plant worker who never touches the reader is not a field-sales exception.

**Month status confirms nobody is watching:**

| | Approved | Pending | Unmarked | Not on roll |
|---|---:|---:|---:|---:|
| June 2026 | 498 | 23 | 87 | 3 |
| **July 2026** | **0** | 376 | **219** | 16 |

And SAP confirms July payroll has **not been booked yet** (`SALARY PAYABLE JUL` = ₹22,215 only). The July run is about to go out with **zero months approved and 219 employees unmarked**.

**Money.** Exposure = 10 × ₹40,000 (Above 40K floor) + 90 × ₹23,699 = **₹25.33 lakh/month = ₹3.04 Cr/year of payroll released against no attendance record whatsoever.**
That is exposure, not proven loss — most of these people are certainly working. The honest recoverable is the ghost/left-but-still-paid slice. JIVO's own books give the empirical floor for that rate (see H5): ₹15.98 lakh of salary was written back as unclaimed in Mar-2026 ≈ 1% of annual payroll. At a conservative **5%** of the 100-person zero-evidence pool: **₹15.2 lakh/year**.

→ [[finding-zero-attendance-headcount]]

---

## H2 — Are mis-punch days being paid as full days? ✅ BIG

```python
# Mis-punch Raw Data, 30 days
punch-count distribution: 1→1580, 3→869, 5→137, 7→27, 9→15, 11→6, 13→2, 15→2   (total 2,638)
```

| Metric | Value |
|---|---:|
| Employee-days with ≥1 punch in the window | 8,222 |
| Mis-punch days (odd punch count — day cannot be closed) | **2,638 (32%)** |
| …single punch, **no OUT at all** | **1,580** |
| Employees affected | 372 of the 383 who punch (**97%**) |
| Company-wide half-days actually applied (`HD` + `HD-AA`) | 1,108 |
| ⇒ mis-punch days that could **not** have been docked | **≥1,530** |

The 97% number is the tell: this is not employee indiscipline, it is a broken punch process (device/shift/geo-punch configuration), and it has been running for the whole month — 87.9 mis-punches a day, every day (`Daily Trend` sheet: 99, 112, 106, 112 …).

**Is HR docking them?** Partly, and I checked rather than assumed:

| Cohort | n | avg half-days in 30d |
|---|---:|---:|
| Employees with **0** mis-punch days but present > 0 | 140 | **0.05** |
| Employees with **≥10** mis-punch days | 95 | **4.14** |

So mis-punchers do get half-dayed ~80× more often than clean punchers — real control, but only 1,108 half-days against 2,638 mis-punch days. The other ≥1,530 days were credited at 1.0 with **no verifiable hours** (TankhaPay's own `Legend` confirms `MP` = "1.0 day (counted by the portal dashboard)").

Shape of the unpaired punches:
- 1,383 in-only days (arrived, never punched out) — cannot prove they stayed.
- 197 out-only days after 17:00 (no IN recorded) — cannot prove when they arrived.
- Span check on the 1,058 multi-punch mis-punch days: 17 days with a **<4 h** total span, 57 days with **≥12 h** (mostly `WORKER`/`PANTRY BOY`/`EXECUTIVE` — any OT computed off those unpaired punches is unreliable).

**Money.** ≥1,530 full-paid unverifiable days × ₹790 = **₹12.09 lakh/month = ₹1.45 Cr/year of payroll riding on days that cannot be time-verified.**
Conservative capture, assuming only **25%** of the 1,580 no-OUT days are genuinely short by half a day:
`1,580 × 0.25 × 0.5 × ₹790 = ₹1,56,025 / month = ₹18.72 lakh / year`.

→ [[finding-mispunch-paid-full]]

---

## H3 — How much company cash is sitting with employees? ✅ BIG

Two separate pools, and nobody looks at them together.

**(a) Employee advance GL accounts** — one GL per person, recovered through payroll:

```sql
SELECT COUNT(*) AS N,
       SUM(CASE WHEN CAST("CurrTotal" AS DOUBLE)>0 THEN CAST("CurrTotal" AS DOUBLE) ELSE 0 END) AS DEBIT_OUT
FROM JIVO_OIL_HANADB.OACT
WHERE UPPER("AcctName") LIKE '%ADVANCE%' AND UPPER("AcctName") LIKE '%JWPL%';
```

| Company | accounts | outstanding (debit) |
|---|---:|---:|
| Oil | 285 defined / 55 with a balance | ₹62,61,363 |
| Mart | 100 | ₹4,40,554 |
| Beverages | 67 | ₹82,600 |
| **Sub-total** | | **₹67,84,517** |

**(b) IMPREST / employee business-partner accounts** (`OCRD`, positive `"Balance"` = debit = employee holds JIVO's money):

```sql
SELECT COUNT(*) AS N,
       SUM(CASE WHEN CAST("Balance" AS DOUBLE)>0 THEN CAST("Balance" AS DOUBLE) ELSE 0 END) AS DEBIT_ADV
FROM <DB>.OCRD
WHERE UPPER("CardName") LIKE '%IMPREST%' OR UPPER("CardName") LIKE '%JWPL%';
```

| Company | accounts | outstanding |
|---|---:|---:|
| Oil | 495 defined | ₹17,94,945 |
| Mart | 231 | ₹18,04,469 |
| Beverages | 274 | ₹2,42,638 |
| **Sub-total** | | **₹38,42,052** |

### **Total sitting with employees: ₹1,06,26,569 (₹1.06 Cr)**

Top individual exposures (advance GL): GURVINDERJEET SINGH `JWPL0139` ₹13,07,164 · GAGANDEEP SINGH `JWPL0018` ₹6,48,714 · GURPREET SINGH WINKAL `JWPL0138` ₹5,70,000 · NAVDEEP SINGH BHATIA `JWPL2245` ₹5,05,651 · JASNEET KAUR `JWPL0012` ₹4,80,000 · RAVINDER SINGH SHUNTY `JWPL0035` ₹4,47,860.
Top imprest floats: ARVINDER SINGH `JWPL0115` ₹6,22,142 (Oil) · AVTAR SINGH RUPAL `JWPL0014` ₹6,83,066 (Mart) · ZIYAUL HAQUE `JWPL0042` ₹6,58,701 (Mart) · BHUPINDER SINGH GINNI `JWPL1556` ₹2,86,886 (Oil).

**The visibility hole:** 28 employees hold money in **2 or more** accounts spread across the three companies — **₹65,84,993 in total** — so no single ledger shows their net exposure:

| Emp | net held | accounts |
|---|---:|---|
| `JWPL0139` Gurvinderjeet Singh | ₹13,08,849 | 3 (Oil-BP, Mart-BP, Oil-ADV) |
| `JWPL0042` Ziyaul Haque | ₹9,42,798 | 3 (Oil ₹82k + Mart ₹6.59L + Oil-ADV ₹2.02L) |
| `JWPL0018` Gagandeep Singh | ₹7,18,490 | 2 |
| `JWPL0014` Avtar Singh Rupal | ₹6,89,214 | 2 |
| `JWPL0115` Arvinder Singh | ₹4,29,886 net | **7 accounts across all 3 companies** |
| `JWPL0012` Jasneet Kaur | ₹5,42,665 | 4 |

Ageing is decent (51 of 55 advance accounts moved in the last 3 months — payroll recovery is running), so this is a **float-sizing** problem, not a rot problem. But ₹1.06 Cr is real cash out of the business at all times.

→ [[finding-employee-cash-float]]

---

## H4 — Is any of it with people who have **left**? ⚠️ small but clean

Every SAP account name carries the TankhaPay code (`… IMPREST JWPL0042`). Extracted the code and matched it against the live 611-person roster.

| Pool | accts off-roster | ₹ |
|---|---:|---:|
| Oil IMPREST/BP | 38 | ₹1,02,269 |
| Mart IMPREST/BP | 7 | ₹37,124 |
| Bev IMPREST/BP | 12 | ₹2,510 |
| Advance GL (Oil) | 2 | ₹44,360 |
| BP accounts with **no employee code at all** | 6 | ₹2,12,560 |
| **Total** | **65** | **₹3,98,823** |

Largest: `SUSHIL KUMAR SINGH IT 20000 IMPREST JWPL0010` ₹91,069 — and this one is instructive. The account is **still transacting today** (last JE 2026-07-28, 278 lines), yet `JWPL0010` does not exist on the roster; the roster has "Sushil Kumar Singh" as **`JWPL3037`**. Same person, two identities — the advance is invisible to any code-based recovery. Others: `UNMEET SINGH JWPL2296` ₹5,410, `AJIT SINGH ECOM JWPL1994` ₹20,000 (Mart), `BAKSHISH SINGH JWPL2648` ₹8,624, `PARAMVEER SINGH JWPL1647` ₹2,000, `RANJEET SINGH DRIVER JWPL0034` ₹2,000.

Good news, tested and negative: the **16 July exits** (14 interns + 2 sales) hold **no** advances or imprest. Exit-clearance on interns is clean.

→ [[finding-offroster-advances]]

---

## H5 — Do the salary-payable accounts reconcile? ✅ REAL, and it points back at H1

```sql
SELECT T2."AcctName" AS NM,
       SUM(CAST(T0."Debit" AS DOUBLE))-SUM(CAST(T0."Credit" AS DOUBLE)) AS NET_ALLTIME
FROM JIVO_OIL_HANADB.JDT1 T0
JOIN JIVO_OIL_HANADB.OJDT T1 ON T1."TransId"=T0."TransId"
JOIN JIVO_OIL_HANADB.OACT T2 ON T2."AcctCode"=T0."Account"
WHERE T2."AcctName" LIKE 'SALARY PAYABLE%'
GROUP BY T2."AcctName";
```

| Account (Oil) | all-time net | reading |
|---|---:|---|
| SALARY PAYABLE JAN | −₹1,14,160 | credit — still owed since Jan |
| SALARY PAYABLE FEB | −₹1,12,152 | still owed since Feb |
| SALARY PAYABLE MAR | −₹3,55,914 | still owed since Mar |
| SALARY PAYABLE APR | −₹1,14,530 | still owed since Apr |
| **SALARY PAYABLE MAY** | **+₹12,01,292** | **DEBIT — paid more than accrued** |
| SALARY PAYABLE JUN | +₹9,88,455 | debit (June run still in flight) |
| SALARY PAYABLE JUL | +₹22,215 | debit |
| AUG / SEP / OCT / NOV / DEC | ≈ 0 | properly cleared |

Plus Mart `SALARY PAYABLE FEB` +₹62,176 and `MAR` +₹79,717 debit, Bev `APR` +₹3,500.

**A payable account in debit means cash left against a liability that was never booked.** Excluding June (genuinely still processing), the hard exception is **₹13,68,900** — money disbursed under "salary payable" with no matching accrual. Including June it is ₹23,57,355.

**The other side — salary accrued for people who never collect it.** Account `5630017 REVERSAL OF UNCLAIMED SALARY`:

```
2026-03-31  Reversal of salary payable.            CR ₹15,97,540
2026-03-31  Reversal of Employee Bonus Payable.    CR ₹   93,750
2026-03-31  Employee Bonus payable to be written off. CR ₹ 73,755
```

**₹17,65,045 of salary and bonus was accrued and never claimed in FY25-26** — ~1.0% of annual payroll, written back at year end. That is the empirical floor for the ghost-payroll rate used in H1, straight out of JIVO's own books. And the ₹6,96,756 still sitting in JAN–APR payable (plus Mart JAN ₹23,298 = **₹7,20,054**) is this year's batch queueing up for the same treatment.

Related: `2110003 SUNDRY CREDITOR STAFF` carries a **debit** balance of ₹13,23,205 (a staff creditor account in debit), and `2202203 JIVO MART PVT. LTD. SALARY` ₹11,55,979 — Mart payroll paid by Oil and recharged. Both are reconciliation items, not counted again in the headline to avoid double-counting with H3.

→ [[finding-salary-payable-debits]] · [[finding-unclaimed-salary]]

---

## H6 — Duplicate employee records on the payroll? ⚠️ 9 candidates

Exact `name + posting department` collisions in the 611 roster:

| Name | Department | Records |
|---|---|---|
| **PARVEEN KUMAR** | JIVO_PLANT & PRODUCTION (BACK END) | `JWPL2693` (Above 40K, 21 present) · `JWPL2281` (Factory, 26 present) · `JWPL2883` (Factory, **not marked**) |
| LALIT KUMAR | JIVO_OIL_GT | `JWPL2925` · `JWPL2092` (not marked) |
| BHUPINDER SINGH | JIVO WELLNESS PVT LTD | `JWPL1556` (DOJ 2010) · `JWPL3000` (DOJ Apr-2026) |
| TARANDEEP SINGH | JIVO_ACCOUNTS | `JWPL2639` · `JWPL0346` |
| AMIT KUMAR | JIVO_OIL_GT | `JWPL2501` · `JWPL1868` |
| JYOTI | JIVO_OIL_GT | `JWPL0151` · `JWPL0949` |
| MUSKAN | JIVO_OIL_GT | `JWPL2420` · `JWPL1998` |
| POOJA | JIVO_OIL_GT | `JWPL2243` · `JWPL2823` |
| NEELAM | JIVO_OIL_MT | `JWPL2117` (not marked) · `JWPL0676` |

10 excess records. Across the whole roster there are 44 duplicate-name groups covering 104 of 611 records — most are genuinely different people (common names), which is exactly why name-matching alone is not enough and why the `JWPL0010` / `JWPL3037` case in H4 slipped through.

**Money.** If only 3 of the 10 excess records are true payroll duplicates: `3 × ₹23,699 × 12 = ₹8,53,164 / year`. **Low confidence** — this needs a PAN/Aadhaar/bank-account dedupe in TankhaPay to confirm, which is a read I could not run (expired token).

→ [[finding-duplicate-employee-records]]

---

## H7 — Is the highest-paid band the worst attended? ✅ yes, but caveated

`By unit` sheet:

| Org unit | Employees | Marked | Never marked | Scheduled days | Paid-day equiv. | Attendance % |
|---|---:|---:|---:|---:|---:|---:|
| **Above 40K** | 61 | 51 | **10** | 1,416 | 897 | **63.3%** ← worst |
| Confidential | 17 | 17 | 0 | 365 | 225.5 | 61.8% |
| Sales Office | 202 | 162 | 40 | 1,998 | 1,332.5 | 66.7% |
| Head Office | 120 | 104 | 16 | 2,765 | 1,854 | 67.1% |
| Interns | 43 | 39 | 4 | 836 | 600 | 71.8% |
| Factory | 168 | 137 | 31 | 4,003 | 3,059 | 76.4% |

The 61 people in the `Above 40K` band (guaranteed ≥₹40,000/month) attend worse than the factory floor, and **10 of them have zero attendance evidence at all** — that slice alone is `10 × ₹40,000 × 12 = ₹48 lakh/year` paid with no record. It is already inside the H1 exposure, so **not counted separately** in the headline.

**Honest caveat (from the workbook's own Read-me):** July is unprocessed — weekly-offs were not applied, so ~1,125 employee-days show `AA` on the four Sundays instead of `WO`. That deflates every July attendance % including these. The `Absent excl. Sun` column is what I used for the low-attendance cut below; the unit `Attendance %` above still carries the July drag.

---

## H8 — Employees marked present with no punch behind it? ⚠️ small

140 roster employees never appear in the punch data yet were credited attendance — **406.5 paid-day equivalents** in 30 days (≈₹3.21 lakh at ₹790/day). But 100+ of those are 2-day credits (29–30 June marked, July blank), and the pool is 102 Sales Office / promoter staff who legitimately mark via mobile geo-punch rather than the biometric reader. Real ones worth an eyeball: `JWPL3067` RAMLAL (GARDNER, 25 present days, zero punches), `JWPL2160` Santosh (WORKER, 24), `JWPL0215` Santosh Thakur (PROMOTER, 21), `JWPL2575` Karan Singh (WORKER, 15), `JWPL3034` Manisha (Helper, 14). **Not counted** in the headline — too entangled with H1 and with legitimate mobile punching.

---

## H9 — Duplicate salary / imprest payments? ❌ killed

```sql
SELECT T0."CardCode", T1."CardName", SUBSTRING(TO_VARCHAR(T0."DocDate",'YYYY-MM'),1,7) AS MTH,
       CAST(T0."DocTotal" AS DOUBLE) AS AMT, COUNT(*) AS N
FROM JIVO_OIL_HANADB.OVPM T0 JOIN JIVO_OIL_HANADB.OCRD T1 ON T1."CardCode"=T0."CardCode"
WHERE T0."Canceled"='N' AND (UPPER(T1."CardName") LIKE '%IMPREST%' OR UPPER(T1."CardName") LIKE '%JWPL%')
  AND T0."DocDate">=TO_DATE('2025-04-01')
GROUP BY T0."CardCode", T1."CardName", SUBSTRING(TO_VARCHAR(T0."DocDate",'YYYY-MM'),1,7), CAST(T0."DocTotal" AS DOUBLE)
HAVING COUNT(*)>1 ORDER BY AMT*COUNT(*) DESC;
```

Plenty of hits (`BHUPINDER SINGH GINNI` ₹1,00,000 × 3 in Mar-26, `ARVINDER SINGH` ₹1,00,000 × 3 in Jul-26, `PARAMDEEP SINGH` ₹20,000 × 4 in May-26) — but these are **round-number imprest replenishments**, the normal top-up rhythm of a float account, not duplicates. No finding. (Genuine duplicate-payment hunting belongs to [[duplicate-payments]].)

## H10 — Employees below 50% attendance still on full pay? ❌ not a leak here

59 of 378 properly-marked employees (≥20 scheduled days) came in under 50% attendance — 1,165 days of shortfall. But TankhaPay's `Paid-day equiv.` already excludes those days, i.e. the docking is computed. Unless payroll overrides the sheet, this is not leakage — it is an HR/productivity problem. Also July-drag affected (H7 caveat). **No ₹ claimed.**

## H11 — Overtime anomalies? ⚠️ noted, not quantified

57 mis-punch days with a ≥12 h punch span (`EXECUTIVE` 15, `WORKER` 13, `PANTRY BOY` 7, `MANAGER` 6). Any OT computed off a day whose punches are unpaired is computed off garbage. Too small and too assumption-heavy to put a number on; folded into the H2 control recommendation.

## H12 — Are statutory contributions under-declared? ❌ no signal

EPF employee contribution ₹16,67,403 and ESIC employee ₹2,94,742 YTD; employer matches exactly (`5630015` = `5630010` = ₹16,67,403; ESIC employer ₹12,73,920). Contribution bases are consistent with a 611-person roster mixing above- and below-ceiling wages. Nothing anomalous. **No finding.**

## H13 — Exit clearance leaking? ❌ clean

All 16 July `Not on roll` employees checked against every advance/imprest pool — one carries −₹365 (a credit, i.e. JIVO owes *them*). Exit clearance works.

## H14 — Is SAP an independent check on payroll? ❌ no — and that is the finding behind H1

74 summary journal lines a month, memos like `"BACK OFFICE BELOW"` and `"sales below june-26"`. There is no employee-level payroll data in SAP at all. Cross-verification of who was paid what is **impossible from the books** — TankhaPay is the sole control, and per H1 it is unmarked for 219 people.

## H15 — Reverse risk: is the July data going to *under*-pay people? ⚠️ operational risk, not a saving

July weekly-offs are unapplied — ~1,125 employee-days sit as `AA` on Sundays that should be `WO`. If payroll is run off the raw July grid, staff get docked ~₹8.89 lakh they are owed, generating a correction cycle and a grievance queue. Flagged because it is the *same* root cause (unprocessed month) as H1 — fixing the month fixes both directions.

---

## Scoreboard

| # | Finding | ₹ | Type | Conf. |
|---|---|---:|---|---|
| 1 | [[finding-employee-cash-float]] — ₹1.06 Cr with employees across 3 companies | ₹1,06,26,569 | working-capital-release | high |
| 2 | [[finding-mispunch-paid-full]] — ≥1,530 unverifiable full-paid days/month | ₹18,72,300 /yr | annual-recurring | medium |
| 3 | [[finding-zero-attendance-headcount]] — 100 employees, no attendance & no punch (₹3.04 Cr/yr exposure) | ₹15,20,000 /yr | annual-recurring | medium |
| 4 | [[finding-salary-payable-debits]] — payable accounts in debit | ₹13,68,900 | one-time-recovery | medium |
| 5 | [[finding-duplicate-employee-records]] — 9 same-name-same-dept groups | ₹8,53,164 /yr | annual-recurring | low |
| 6 | [[finding-unclaimed-salary]] — Jan–Apr salary payable never paid | ₹7,20,054 | one-time-recovery | medium |
| 7 | [[finding-offroster-advances]] — advances held under codes not on roll | ₹3,98,823 | one-time-recovery | medium |

**Exposure (not claimed as savings):** ₹3.04 Cr/yr of payroll with no attendance evidence + ₹1.45 Cr/yr of payroll on unverifiable punch days.

## What to actually do

1. **Gate the July payroll run** on 100% attendance approval — 0 approved / 376 pending / 219 unmarked today, and SAP shows July salary not yet booked. This is the one action that must happen *this week*.
2. **Audit the 100 zero-evidence employees** (list is reproducible from the two workbooks) — confirm each is a live, working person; start with the 31 Factory workers who should be hitting a biometric reader daily.
3. **Fix the punch process**, not the punchers — 97% of punchers mis-punched at least once; that is configuration (shift masters, geo-fence, device sync), not discipline. Set a rule: unresolved single-punch day auto-flags to the manager before month close.
4. **Cap and settle imprest floats** — ₹1.06 Cr out with employees, ₹65.85 lakh of it split across multiple accounts in multiple companies. Build a single employee-wise net exposure view keyed on `JWPL` code, halve the top-10 floats.
5. **Reconcile the salary-payable accounts** — a payable in debit (₹13.69 lakh hard, ₹23.57 lakh including June) is an accounting exception, not an opinion.
6. **Dedupe the TankhaPay roster** on PAN/bank account, and align `JWPL` codes between TankhaPay and SAP (the `JWPL0010`/`JWPL3037` case is one person with two identities and ₹93,429 attached).

## Caveats, stated plainly

- The blended ₹23,699/employee/month hides real spread; findings concentrated in `Above 40K` use the ₹40,000 floor instead.
- July 2026 is an **unclosed month** in TankhaPay. Every July absence/attendance-% figure is provisional and will improve as HR processes weekly-offs and leave. I have leaned on June (closed, 498 approved) and on structural counts (never-marked, never-punched) which do not move with processing.
- "No biometric punch" ≠ "not working" for field sales and promoters who mark via mobile geo-punch; that is why H8 is not monetised and why H1's capture rate is haircut to 5%.
- The TankhaPay CLI was not called live (token expired 2026-07-26, refresh forbidden). Salary-per-employee, payout registers and leave balances are therefore **not** in this note — a live pull would sharpen findings 2, 3 and 5 considerably.
- Everything here is SELECT-only. No SAP or TankhaPay record was created, changed or approved.
