---
title: Payroll attendance — mis-punch days and zero-attendance headcount (adversarial re-derivation)
created: 2026-07-29
verdict: REFUTED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding, payroll, tankhapay, attendance, refuted]
---

# Payroll attendance — both money claims fail; the control gap is real

Part of [[SAVINGS-MOC]] · Evidence: [[payroll-leakage]]

## CFO summary in plain language

Two payroll findings were put forward, worth a combined **₹33.92 lakh a year**: that ~1,530 mis-punch days a month are being paid as full days without verifiable hours (₹18.72 L/yr), and that 100 people sit on the roll with no attendance and no punches (₹15.20 L/yr).

I re-tested both against the raw data, joining employee-day to employee-day rather than comparing totals. **Neither survives as money. Verified bankable: ₹0.**

- **The mis-punch days are overwhelmingly real, full days worked.** On the 1,058 mis-punch days where the employee punched more than once, the first-to-last punch span is a median **9.1 hours**, and **91% span 8 hours or more**. The odd punch count is a stray double-tap at the reader, not a short day. When I isolate the only days where the biometric record itself proves a short day *and* the day was still paid in full, there are **6 of them in 30 days — ₹28,440 a year**, not ₹18.72 lakh.
- **HR is not letting mis-punch days slip through.** Half-days are applied to **14.4%** of mis-punch days versus a **13.0%** company-wide baseline. Mis-punch days are docked at essentially the same rate as every other day — there is no escape hatch to close.
- **228 of the 1,580 "no OUT punch" days are a reporting artifact.** The report was generated at mid-day on 28 Jul; those people had punched in and had not yet gone home. They are not mis-punches.
- **The "100 employees with zero biometric punches" cannot be established from this data.** The mis-punch workbook contains *only* days with an odd punch count. An employee who punches perfectly twice a day appears nowhere in it. 242 of the 611 roster employees have no row in that file, and **142 of them were marked present by HR**. So "no row in the mis-punch file" proves nothing about whether someone punched.
- **TankhaPay credits those 100 people zero paid days, not full pay.** Their Paid-day-equivalent is 0.0. If payroll ran off the portal they would be *under*-paid. The exposure runs in the opposite direction to the claim.
- **The 5% capture rate has no evidential basis.** It was anchored on the ₹17.65 lakh unclaimed-salary write-back of Mar-2026 — but that write-back is money JIVO **already recovered** at year-end. Using a control that is already working as the basis for new savings double-counts the recovery.

**What is genuinely real and worth acting on:** JIVO has no per-employee payroll record in SAP (74 summary journal lines a month), so TankhaPay attendance is the only control — and on the day of the pull it showed **0 months approved, 376 pending, 219 unmarked** for July, with the July run not yet booked. That is a live control gap. It is worth fixing on control grounds, not because a specific rupee amount has been proven to leak.

---

## Component verdicts

| # | Component | Claimed | Verified | Verdict |
|---|---|---:|---:|---|
| 56 | ≥1,530 mis-punch days/month paid as full days | ₹18,72,300/yr | **₹0** (de-minimis ₹28,440/yr) | **REFUTED** |
| 58 | 100 employees on roll, zero attendance & zero punches | ₹15,20,000/yr | **₹0** | **REFUTED** |
| | **Bundle** | **₹33,92,300/yr** | **₹0** | **REFUTED** |

---

### Component 56 — mis-punch days paid as full days → REFUTED

The raw counts reproduce exactly: **2,638** mis-punch employee-days, distribution `1→1580, 3→869, 5→137, 7→27, 9→15, 11→6, 13→2, 15→2`, **372** of 383 punching employees affected. The counting is sound. The *inference* from those counts is not.

**Test 1 — join every mis-punch day to the attendance code actually applied.** The original compared 2,638 mis-punch days against 1,108 company-wide half-days at the aggregate level. That comparison is invalid: company-wide half-days include half-days on days that had no mis-punch. Joining `(emp code, date)` to the Daily-grid cell:

```
attendance code applied ON the 2,638 mis-punch employee-days
  PP       2224   85.1%      <- paid full
  HD        191    7.3%
  HD-AA     189    7.2%      <- half-dayed: 381 total = 14.4%
  MP          5    0.2%
  AA          2    0.1%
  OD / blank  2    0.1%
```

Company-wide half-day rate over all present-type days = `(204 + 901) / 8,519 = 13.0%`. Mis-punch days are docked at **14.4%** — a 1.11× ratio. Mis-punching is **not** associated with escaping the half-day control. The lens's own cohort comparison (0.05 half-days for clean punchers vs 4.14 for ≥10-mis-punch employees) is confounded: employees with many mis-punch days simply have many more punch-days in total.

**Test 2 — measure the punch span, which the original never did across the whole set.** For the 1,058 multi-punch mis-punch days:

```
span   <4h   4-6h   6-8h   8-10h  10-12h  >=12h
        17     27     53     771     133     57
median span 9.12 h  ·  >=8h: 961 (90.8%)
```

A 9-hour first-to-last span is a full day worked. There is no overpayment on these days at all.

**Test 3 — isolate the only evidenced overpayment.** Days where the span itself proves a short day *and* the day was paid `PP`:

| Threshold | Days / 30d | ₹/yr at ₹790/day × 0.5 |
|---|---:|---:|
| span < 6h & paid PP | **6** | **₹28,440** |
| span < 7h & paid PP | 14 | ₹66,360 |
| span < 8h & paid PP (most generous) | 26 | ₹1,23,240 |

Even the most generous reading — dock half a day on every multi-punch day that failed to reach a standard 8-hour shift and was still paid full — yields **₹1.23 lakh/yr, 6.6% of the ₹18.72 lakh claimed**. The evidence-tight number is ₹28,440/yr. Notably, of the 42 days with a span under 6 hours, **36 were already half-dayed or MP-flagged by HR** — the control caught them.

**Test 4 — the single-punch base is inflated and unactionable.**
- **228 of the 1,580** single-punch days fall on **28 Jul**, the day the report was generated mid-day (the workbook's own Summary says "excl. today = 2,408"). Those employees had punched in and not yet left. Correct base: **1,352**.
- Of those 1,352, **1,123 (83%) have a morning IN punch** (before 13:00, median 10:17) — positive proof the person reported for work. Only 197 are OUT-only after 17:00.
- **834 of 1,352 (62%) are field/mobile roles** — SALES OFFICER 492, PROMOTER 111, Delivery Boy 108, AREA SALES MANAGER 109. These staff punch once at a market or store and never return to a reader. A single punch is their normal pattern, not a defect.
- With 97% of punchers affected, this is an employer-side device/configuration failure. Deducting wages for it is not defensible under the Payment of Wages Act, so the "capture" is not legally available even where it is arithmetically imaginable.

Re-running the original formula on the corrected base gives `1,352 × 25% × 0.5 × ₹790 = ₹16.02 L/yr` — but the 25% is an unevidenced assumption, and Tests 1–3 show the true evidenced rate is nearer 0.4% (6 of 1,580), not 25%.

**Verdict: REFUTED.** Real as a data-quality and overtime-integrity control observation — any OT computed off unpaired punches is unreliable, and 57 days show a ≥12h span. Not real as money.

---

### Component 58 — 100 employees with zero attendance evidence → REFUTED

The cohort reproduces exactly: 611 on roll → **101** never marked in the window → **100** with no row in the mis-punch file → **83** also Unmarked in June → 93 with 30 days on roll. Unit split Sales Office 40 / Factory 31 / Head Office 15 / Above-40K 10 / Interns 4; 99 Permanent, 1 Contractual. The Daily grid confirms the blankness: 86 of the 100 have **zero** non-blank cells across 30 days; the other 14 have 1–2 cells, all `AA`. Sum of Present = 0, sum of Paid-day-equivalent = 0.0.

**Kill 1 — the corroborating evidence leg does not exist.** The claim's strength came from "100 also had **zero biometric punches**". The mis-punch workbook contains **only employee-days with an ODD punch count**. A perfectly-punching employee (in + out, 2 punches) generates no row. Testing this: **242 of 611** roster employees have no row in the mis-punch file, and **142 of those were marked present by HR** — they clearly exist and punch. "Absent from the mis-punch file" therefore carries no information about punching. The only established fact is **HR never marked their attendance**, which is a single data point, not two corroborating ones.

**Kill 2 — the direction of risk is inverted.** TankhaPay assigns these 100 a Paid-day-equivalent of **0.0**. The workbook Read-me states unmarked months are blank and excluded from the rate. If payroll is computed from the portal, these people receive **nothing** — the exposure is under-payment and a grievance queue, which is exactly what H15 of the lens note flags. The ₹25.33 L/month "exposure" figure assumes the opposite.

**Kill 3 — the ₹25.33 L/month exposure is circular.** It is built as `10 × ₹40,000 + 90 × ₹23,699`, where ₹23,699 is itself `group payroll ÷ 611` — the divisor *includes* the 100. It is a proportional allocation of a total, presented as an incremental amount at risk. I verified the payroll base is right (Oil ₹1,19,09,761 + Mart ₹13,33,606 + Beverages ₹12,36,555 = **₹1,44,79,922** for Jun-2026, so ₹23,699/month and ₹790/day are correct), but a correct denominator does not make the allocation an exposure.

**Kill 4 — the 5% haircut is anchored on a control that already works.** The ₹17.65 lakh anchor is the Mar-2026 write-back on GL 5630017 `REVERSAL OF UNCLAIMED SALARY` — salary accrued, never collected, and **credited back to P&L at year end**. JIVO already recovers this money. Reusing it as the basis for new savings counts the same recovery twice.

**Kill 5 — the cohort does not look like ghost payroll.** Date-of-joining spread: 22 joined 2024 or earlier (earliest **2010-04-15**), 38 in 2025, 36 in 2026 H1, 4 from Jun-2026. Ghost-payroll schemes cluster in recent, bulk additions; this is a tenure-diverse cross-section. Further: **13 of the 100 had June APPROVED** by HR, **4 are 'Not on roll' in July** (they cannot be overpaid in July), and the 25 non-blank cells in the cohort are all `AA` — marked absent, which pays zero.

**Kill 6 — salary does not respond to attendance, so gating it saves nothing mechanically.** Oil salary expense over 15 months: ₹1.13, 1.11, 1.08, 1.10, 1.11, 1.05, 1.05, 1.14, 1.10, 1.14, 1.11, 1.12, 1.17, 1.16, 1.19 Cr — a coefficient of variation near 3% against unit attendance rates that swing 63–76%. JIVO runs a fixed monthly salary roll. Withholding pay against attendance is not an existing mechanism, so no cash is released by approving the month.

**The one real signal, which is an audit trigger and not money.** Matching the roster's `JWPL` codes against every employee-named account in `OACT` and `OCRD` across all three companies, then testing recent journal activity:

| Cohort | with a SAP employee account | transacting since 1-Jun-2026 |
|---|---:|---:|
| 510 marked employees | 190 (37%) | 71 (**14%**) |
| 100 zero-attendance | 24 (24%) | 2 (**2%**) |

A **7× dormancy differential**, and **zero** of the 100 has a July-2026 transaction. That is a genuine anomaly and justifies physically verifying the named list — starting with the 31 Factory staff (21 in `JIVO_PLANT & PRODUCTION (BACK END)`, designations WORKER ×12, EXECUTIVE ×9, Operator ×2, Supervisor, Helper, DRIVER) who should touch a reader daily. But only 14% of *confirmed-working* employees transact in SAP at all, so low SAP activity is weak evidence, and it cannot carry a rupee figure.

**Verdict: REFUTED as money. CONFIRMED as a control gap** — the payroll run should not be released against 0 approved / 376 pending / 219 unmarked.

---

## Key SQL / analysis

```sql
-- payroll base, per company (repeat for MART / BEVERAGES)
SELECT SUBSTRING(TO_VARCHAR(T1."RefDate",'YYYY-MM'),1,7) AS MTH,
       SUM(CAST(T0."Debit" AS DOUBLE))-SUM(CAST(T0."Credit" AS DOUBLE)) AS SALARY,
       COUNT(*) AS NLINES
FROM JIVO_OIL_HANADB.JDT1 T0
JOIN JIVO_OIL_HANADB.OJDT T1 ON T1."TransId"=T0."TransId"
WHERE T0."Account"=CAST(5630001 AS NVARCHAR) AND T1."RefDate">=TO_DATE('2025-04-01')
GROUP BY SUBSTRING(TO_VARCHAR(T1."RefDate",'YYYY-MM'),1,7) ORDER BY 1;
-- 15 months, 69-89 summary lines/month, CV ~3% -> fixed roll, attendance-insensitive

-- dormancy test: last journal activity on every employee-coded account
SELECT T2."AcctName" AS NM, MAX(T1."RefDate") AS LASTTXN, COUNT(*) AS NLINES,
       SUM(CASE WHEN T1."RefDate">=TO_DATE('2026-06-01') THEN 1 ELSE 0 END) AS N_SINCE_JUN
FROM <DB>.JDT1 T0
JOIN <DB>.OJDT T1 ON T1."TransId"=T0."TransId"
JOIN <DB>.OACT T2 ON T2."AcctCode"=T0."Account"
WHERE UPPER(T2."AcctName") LIKE '%JWPL%'
GROUP BY T2."AcctName";
```

```python
# the join the original never ran: mis-punch employee-day -> attendance code applied
grid[(emp_code, date)]           # from 'Daily grid' sheet
org2emp[JWPL_code] -> emp_code   # from 'Summary' sheet
Counter(grid[(org2emp[m['code']], m['date'])] for m in mispunch_raw_data)
# -> PP 2224 (85.1%) | HD 191 | HD-AA 189 | MP 5 | AA 2

# span test on multi-punch days
spans = [max(ts)-min(ts) for ts in punch_times if len(ts)>=3]
# -> median 9.12h, 90.8% >= 8h
```

---

## Concrete action

1. **Fix the reader configuration, do not dock the staff.** 97% of punchers mis-punched — shift masters, geo-fence radius and device-clock sync are the defect. Track the 2,638 count as an IT/HR KPI. **Owner: HR Head + IT.** No money attaches to this; it protects overtime integrity (57 days carry a ≥12h span computed off unpaired punches).
2. **Exclude the report-generation day from every future mis-punch count** — 228 of 1,580 single-punch days on 28 Jul were open shifts, not defects. **Owner: whoever owns the TankhaPay report.**
3. **Physically verify the 100-name list, starting with the 31 Factory staff**, and prioritise the 2 with zero SAP activity and 60 days of no attendance evidence. Treat it as a headcount audit with an unknown yield, not a budgeted saving. **Owner: Plant HR + Factory Supervisor.**
4. **Close the July month before the run** (0 approved / 376 pending / 219 unmarked). This is a control requirement and also prevents the ~1,125 unapplied Sunday weekly-offs from *under*-paying staff by ~₹8.89 lakh. **Owner: HR Head, this week.**
5. **Do not carry ₹33.92 lakh/yr in any savings total.** If a headcount audit later finds named non-workers, book that amount then, on names.

---

## Overlaps — do not double-count

- The two components **cannot be summed**: both are captured by the same single control fix (gate the payroll run on attendance approval), so adding ₹18.72 L and ₹15.20 L counts one action twice. Their employee-days are also mutually exclusive by construction — the 100 zero-attendance staff have no punches, so they contribute nothing to the mis-punch population.
- **38 of the 100** zero-attendance employees hold SAP employee accounts totalling **₹4,47,154**. That money already sits inside the ₹1.06 Cr pool in [[finding-employee-cash-float]] and must not be re-counted here.
- The ₹17.65 lakh unclaimed-salary write-back used as the 5% anchor belongs to [[finding-unclaimed-salary]]; it is an already-executed recovery, not headroom for this bundle.
- Both components share one cost basis — group salary ₹1,44,79,922/month ÷ 611 = ₹23,699/month = ₹790/day. An error in that rate would move both together.
- Neither component is a working-capital item, so the **8.25%** multiplier in [[finding-cc-interest-conversion-rate]] does not apply and no interest saving is claimed.
- No overlap with the separately-verified [[finding-blessing-advertising-overdue]], [[finding-trade-spend-as-credit-notes]] or [[finding-no-invoice-vendors]].

Links: [[finding-employee-cash-float]] · [[finding-unclaimed-salary]] · [[finding-cc-interest-conversion-rate]]

---

## Caveats

- Everything here is SELECT-only against SAP HANA and read-only against two exported workbooks. Nothing was created, changed or approved in SAP or TankhaPay.
- The TankhaPay CLI was not called live. A per-employee salary register would settle Component 58 definitively — if the 100 appear in the July payout register with amounts, the exposure becomes measurable; if they do not, the finding is closed.
- 24 mis-punch rows carry `JWPL` codes absent from the 611 roster (3 distinct codes) and could not be joined; at 0.9% of rows this does not move any conclusion.
- July 2026 is an unclosed month in TankhaPay. I leaned on structural counts (never-marked, punch spans, punch times) that do not move as HR processes the month.
