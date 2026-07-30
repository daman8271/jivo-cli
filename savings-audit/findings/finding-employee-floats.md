---
title: "Employee advances + imprest floats — ₹1.06 Cr claimed, ₹42.81 L bankable"
created: 2026-07-29
verdict: REVISED
amount_verified_inr: 4280875
amount_claimed_inr: 10626569
kind: working-capital-release
company: ALL
lens: payroll-leakage
ranks: [31]
tags: [savings-audit, finding]
---

# Employee cash floats (rank 31) — REVISED, ₹42,80,875 bankable

**Claimed:** ₹1,06,26,569 of company cash "permanently parked with employees" across all three companies.
**Re-derived population:** ₹1,06,25,474 — the sweep's arithmetic is right to 0.01%.
**Re-derived bankable:** **₹42,80,875** (₹42.81 lakh) — 40.3% of the claim.
**Interest released at the measured 8.25% CC rate:** ₹3,53,172 a year *(overlay on the ₹42.81 L, not extra money)*.

Part of [[SAVINGS-MOC]] · Evidence: [[payroll-leakage]]

---

## Plain-language summary for the CFO

There genuinely is about **₹1.06 crore of JIVO's cash sitting with its own staff today**, in two
completely separate places that nobody has ever looked at together: 69 personal *advance* ledgers
in the chart of accounts (₹67.85 L) and 69 *imprest* supplier/customer cards in the partner master
(₹38.41 L). I reproduced both to the rupee and confirmed they are **not the same money counted
twice** — not a single accounting entry in SAP touches both an advance ledger and an imprest card.

But three things stop ₹1.06 Cr being the number Accounts can go and get:

**1. ₹13.79 lakh of the "advances" is not an advance at all — it is JIVO's own staff insurance bill.**
This is the important discovery and it is not in the original finding. On 01-Feb-2025 and again on
01-Feb-2026, the **company group medical policy premium** was split across individual employees'
advance ledgers instead of being charged to staff-welfare expense — 20 people, ₹12,47,627, funded
through the Mart intercompany account. Of that, exactly **₹5,824 has ever been recovered.** A ₹5,00,000
**visa fee** for one senior employee was booked the same way. So ₹13.79 L of what looks like "money
employees owe us" is really **company expenditure that was never expensed**. It cannot be collected,
and while it sits there JIVO's profit and its balance sheet are both overstated by that amount.

**2. The imprest half was measured on a peak day.** Imprest floats revolve: cash goes out, expense
vouchers come back. On 29-Jul-2026 the float stood at ₹38.41 L — the highest reading in eleven months.
Nine days earlier it was ₹22.08 L; a month earlier ₹17.53 L; on 31-Mar-2026 it was **₹9.62 L**.
₹16.33 L of today's balance was handed out between 23 and 28 July as routine month-end replenishment
(Avtar Singh ₹6.83 L on the 28th, Ziyaul Haque ₹6.59 L on the 27th, Arvinder Singh ₹6.22 L on the 23rd).
The float that is *permanently* tied up is the **₹17.94 L median**, not ₹38.41 L. Roughly ₹20.5 L of the
claim is transaction timing.

**3. Just under half the advance book collects itself.** These advances are recovered by monthly salary
deduction, and that machinery works: ₹45.98 L came back in the last twelve months. Counting the whole
₹67.85 L as an audit saving would be taking credit for business-as-usual.

**What is real, and what makes it worth doing anyway:** stripping all three, **₹42.81 lakh** is money a
deliberate policy releases that the status quo does not. And the status quo is getting worse, not better —
the advance book has grown from ₹38.4 L at go-live to ₹47.0 L a year ago to **₹67.8 L today**, because
JIVO issued ₹45.3 L of fresh advances in the last six months while recovering only ₹20.7 L. It is an
**interest-free staff loan book, growing about ₹21 L a year, funded by cash-credit borrowing at 8.25%.**

The reassuring part: **96% of the money is held by people who are on the payroll today** (I matched every
SAP account name's `JWPL` code against the live 611-person TankhaPay roster), and the top holders are HODs,
managers and core-team members. This is collectible by payroll deduction — the enforcement rail already
exists. Exit clearance is also clean: the 16 July leavers hold nothing.

---

## Verdict: REVISED — ₹42,80,875 bankable

| Component | Claimed ₹ | Verified ₹ | Verdict |
|---|---:|---:|---|
| Pool A — employee advance GL accounts (staff loan book), all 3 companies | 67,84,517 | 35,96,774 | **REVISED** |
| Pool B — IMPREST / employee business-partner floats, all 3 companies | 38,42,052 | 6,84,101 | **REVISED** |
| **Bundle (rank 31)** | **1,06,26,569** | **42,80,875** | **REVISED** |

---

## 0. The population replicates — and the two pools are genuinely distinct

```sql
-- Pool A: one GL per employee, name carries the TankhaPay code
SELECT 'OIL' AS "CO", COUNT(*) AS "N",
       SUM(CASE WHEN CAST("CurrTotal" AS DECIMAL(18,2))>0
                THEN CAST("CurrTotal" AS DECIMAL(18,2)) ELSE 0 END) AS "POS"
FROM   JIVO_OIL_HANADB.OACT
WHERE  UPPER("AcctName") LIKE '%ADVANCE%' AND UPPER("AcctName") LIKE '%JWPL%'
UNION ALL /* + MART + BEV arms */ ;

-- Pool B: employee cards in the partner master
SELECT 'OIL', COUNT(*), SUM(CASE WHEN CAST("Balance" AS DECIMAL(18,2))>0
                                 THEN CAST("Balance" AS DECIMAL(18,2)) ELSE 0 END)
FROM   JIVO_OIL_HANADB.OCRD
WHERE  UPPER("CardName") LIKE '%IMPREST%' OR UPPER("CardName") LIKE '%JWPL%'
UNION ALL /* + MART + BEV arms */ ;
```

| | Claimed ₹ | Re-derived ₹ | Δ |
|---|---:|---:|---:|
| Pool A — Oil (56 accounts with a balance) | 62,61,363 | 62,61,363 | ✓ |
| Pool A — Mart (10) | 4,40,554 | 4,40,554 | ✓ |
| Pool A — Beverages (3) | 82,600 | 82,600 | ✓ |
| Pool B — Oil (36) | 17,94,945 | 17,94,945 | ✓ |
| Pool B — Mart (17) | 18,04,469 | 18,03,374 | −1,096 |
| Pool B — Beverages (16) | 2,42,638 | 2,42,638 | ✓ |
| **Total** | **1,06,26,569** | **1,06,25,474** | **−1,095** |

**No mechanical double count.** The advance ledgers post directly (`JDT1."Account"` = `1113xxx`/`11133xxx`)
while the imprest cards post through the control accounts `2110003 SUNDRY CREDITOR STAFF` /
`1101015 SUNDRY DEBTORS STAFF`:

```sql
SELECT COUNT(*) FROM JIVO_OIL_HANADB.JDT1 j
WHERE  j."Account" IN (SELECT "AcctCode" FROM JIVO_OIL_HANADB.OACT
                       WHERE UPPER("AcctName") LIKE '%ADVANCE%' AND UPPER("AcctName") LIKE '%JWPL%')
  AND  j."ShortName" LIKE 'ORG%';                              -- 0 rows
```

Zero. Two different constructs, two different populations. And netting each employee across *every*
account they hold in all three companies changes almost nothing — per-head net exposure is ₹98.97 L +
₹2.13 L on uncoded cards, i.e. only ₹5.4 L of offset. The pool is genuinely net-debit at employee level.

**The cash is real.** In Oil alone the advance ledgers carry **₹67,32,049 of `TransType` 46 outgoing bank
payments** against ₹16,42,115 of `TransType` 24 cash returned. Money left the bank.

**Trap 1 cleared.** No journal that touches an employee advance ledger touches any `1203*`/`1204*`/`121*`
fixed-asset, LAND, KILA or KEVAT account — zero rows. None of this is Bakharpur land or Beverages capex
in disguise.

---

## 1. ₹13,79,174 of "advances" is JIVO's own insurance bill (the finding inside the finding)

```sql
SELECT h."TransId", TO_VARCHAR(h."RefDate") AS "DT", j."Account", a."AcctName",
       j."Debit", j."Credit", j."LineMemo"
FROM   JIVO_OIL_HANADB.JDT1 j
JOIN   JIVO_OIL_HANADB.OJDT h ON h."TransId"=j."TransId"
LEFT   JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  h."TransId" IN (93636, 188448)
ORDER  BY h."TransId", j."Line_ID";
```

| Journal | Date | Employee advance ledgers debited | ₹ | Contra |
|---|---|---:|---:|---|
| 93636 | 2025-02-01 | 11 | 3,49,906 | `2202201 JIVO MART PVT. LTD SUBSIDIARY` |
| 188448 | 2026-02-01 | 16 | 8,29,431 | intercompany |
| | | **Total medical/staff insurance** | **12,47,627** | memo *"Medical Staff Insurance 18-12-2025 to 17-12-2026"* |

Memo-level scan of every line ever posted to an Oil advance ledger:

| Memo class | Lines | Debits ₹ | Credits ₹ |
|---|---:|---:|---:|
| MEDICAL / STAFF INSURANCE | 30 | 12,47,627 | **5,824** |
| VISA FEES | 1 | 5,00,000 | **0** |
| Other insurance | 4 | 40,801 | 31,076 |
| Everything else (genuine advances, salary recoveries) | 1,606 | 1,64,52,725 | 1,19,58,618 |

The premium is a **company group policy for a stated policy period**, allocated across staff and never
recovered — ₹5,824 out of ₹12.48 L in eighteen months. The ₹5,00,000 line reads
*"VISA FEES PAID TO 5LAC FROM JIVO MART"* (20-Sep-2025, on `1113035`).

Still inside today's positive balances, across 18 accounts:

```sql
WITH pos AS (SELECT "AcctCode" AC, CAST("CurrTotal" AS DECIMAL(18,2)) BAL FROM JIVO_OIL_HANADB.OACT
             WHERE UPPER("AcctName") LIKE '%ADVANCE%' AND UPPER("AcctName") LIKE '%JWPL%'
               AND CAST("CurrTotal" AS DECIMAL(18,2))>0),
 med AS (SELECT "Account" AC, SUM(CASE WHEN UPPER("LineMemo") LIKE '%MEDICAL%' OR UPPER("LineMemo") LIKE '%VISA%'
              THEN IFNULL("Debit",0)-IFNULL("Credit",0) ELSE 0 END) NONADV
         FROM JIVO_OIL_HANADB.JDT1 GROUP BY "Account")
SELECT SUM(LEAST(p.BAL, GREATEST(m.NONADV,0))) FROM pos p JOIN med m ON m.AC=p.AC;
-- 13,79,174  (22% of the ₹62.61 L Oil advance pool)
```

The single largest "advance" in the company — `1113035 GURVINDERJEET SINGH ADVANCE JWPL0139`,
₹13,07,164 — is **₹6,38,857 insurance-and-visa** and only ₹6,68,307 actual advance. He borrowed
₹17.20 L between Oct-2024 and Aug-2025 and repaid ₹9.50 L in cash across five receipts in nine days
in Sep-2025; the residue is largely company costs parked on his name.

**Verdict on ₹13,79,174: REFUTED as recoverable.** It is an unrecorded staff-welfare expense.
Reclass it to `5630xxx` staff welfare — that is a P&L correction, not a collection.

*Control note:* several credits to `1113035` carry the memo *"Salary Ziaul Jun 2026"* — one employee's
salary deduction is being credited to another employee's advance ledger. Immaterial in rupees, but it
means the per-person advance balances cannot be trusted line by line until reconciled.

---

## 2. ₹1,95,203 of the "employee float" is not an employee

Two `AKAL ROZGAR YOJANA` masters were swept in because the string `JWPL` appears in their names
(it is the Baru Sahib institution's account, not a payroll code):

| Co | Card | ₹ | What the ledger says |
|---|---|---:|---|
| Bev | `CUSTA000236` AKAL ROZGAR YOJANA A U O JWPL | 1,65,203 | **A/R invoices** — `4110014 SALES @ 5%`, `2132002 OUTPUT IGST @ 5%`, `5000016 COGS FINISHED`, contra `1102002 AKAL ROZGAR YOJANA BARUSAHIB`. A trade debtor. |
| Oil | `VENDA000687` AKAL ROZGAR YOJANA A U/O JWPL BS | 30,000 | `TransType` 46 outgoing payment, 25-May-2026, contra `SUNDRY CREDITORS ARY` / ICICI. A supplier. |

**Verdict: REFUTED as employee float (₹0 here).** The ₹1.65 L Beverages balance is a genuine
receivable and belongs to the receivables workstream, not to payroll.

---

## 3. The imprest half was sampled on a peak day

```sql
-- positive imprest-card balances reconstructed from JDT1 at each date, all 3 schemas
SELECT d.DT, SUM(CASE WHEN BAL>0 THEN BAL ELSE 0 END)
FROM ( SELECT d.DT, j."ShortName", SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)) BAL
       FROM <dates> d JOIN <SCHEMA>.JDT1 j ON 1=1 JOIN <SCHEMA>.OJDT h ON h."TransId"=j."TransId"
       WHERE j."ShortName" IN (SELECT "CardCode" FROM <SCHEMA>.OCRD
                               WHERE UPPER("CardName") LIKE '%JWPL%' OR UPPER("CardName") LIKE '%IMPREST%')
         AND h."RefDate"<=d.DT GROUP BY d.DT, j."ShortName" ) GROUP BY DT;
```

| Date | Positive imprest float ₹ |
|---|---:|
| 31-Aug-2025 | 65,34,013 |
| 30-Sep-2025 | 26,46,995 |
| 31-Oct-2025 | 28,14,028 |
| 30-Nov-2025 | 22,38,145 |
| 31-Dec-2025 | 18,34,680 |
| 31-Jan-2026 | 16,90,154 |
| 28-Feb-2026 | 17,07,436 |
| **31-Mar-2026** | **9,62,099** ← trough |
| 30-Apr-2026 | 10,03,849 |
| 31-May-2026 | 12,62,253 |
| 30-Jun-2026 | 17,52,888 |
| 20-Jul-2026 | 22,07,900 |
| **29-Jul-2026** | **38,40,957** ← the sweep's snapshot |

The float **more than doubled in the last four weeks and rose ₹16.33 L in the final nine days** —
month-end replenishment that will be settled against expense vouchers. **Median of the twelve
month-end readings = ₹17,93,784**; that, not ₹38.41 L, is the cash structurally tied up in floats.
₹20,47,173 of the claim is timing.

**Float control barely exists.** Where a sanctioned limit is written into the card name I tested it:

| | Accounts | ₹ |
|---|---:|---:|
| Card name states a limit | 11 | 9,39,303 |
| **No limit anywhere in the master** | **58** | **29,01,654 (76%)** |
| Of the 11 capped, **over limit** | 4 | **excess 2,67,542** |

`ARVINDER SINGH IMPREST JWPL0115 FACTORY IMPREST 5 LAKH` holds ₹6,22,142 (₹1.22 L over);
`SUSHIL KUMAR SINGH IT 20000 IMPREST JWPL0010` holds ₹91,069 — **4.6× his ₹20,000 sanction**;
`ARSHDEEP SINGH SO GT DL 15000` ₹60,217 on a ₹15,000 float. The four largest floats of all —
Avtar Singh ₹6,83,066, Ziyaul Haque ₹6,58,701, Bhupinder Singh Ginni ₹2,86,886, Manav Jot Singh
₹1,96,937 — have **no sanctioned limit at all**.

**Dormant floats, recall in full:** 13 cards, no movement for 181–635 days, **₹74,447** —
AJIT SINGH ECOM (Mart) ₹20,000 / 425 d · KAMALDEEP-ASM-DL ₹15,000 / 225 d · SURJEET SINGH (Bev)
₹15,000 / 267 d · BAKSHISH SINGH ₹8,624 / 383 d, and nine smaller.

---

## 4. The advance book is a growing interest-free staff loan book

```sql
-- same date-walk over the advance ledgers, all 3 schemas
```

| Date | Positive advance balances ₹ | Accounts |
|---|---:|---:|
| 30-Sep-2024 (go-live) | 38,44,945 | 29 |
| 31-Mar-2025 | 51,97,838 | 60 |
| 30-Sep-2025 | 47,03,625 | 58 |
| 31-Mar-2026 | 50,90,533 | 58 |
| 31-May-2026 | 67,68,303 | 69 |
| **29-Jul-2026** | **67,84,517** | **69** |

It has **never fallen back**, and in the last six months JIVO issued **₹45,32,453** of fresh advances
against **₹20,68,786** recovered — net **+₹24.6 L in six months**. Twelve-month recoveries are ₹45,97,814,
so at the current rate the book would take 17.7 months to clear *if issuance stopped*, which it has not.

Recovery is by salary deduction and it works for some people and not at all for others:

| Employee (TankhaPay role) | Balance ₹ | Recovered in 12 m ₹ | Months to clear |
|---|---:|---:|---:|
| Gurvinderjeet Singh — CORE TEAM MEMBER | 13,07,164 | 10,90,311 | 14.4 |
| Gagandeep Singh — CORE TEAM MEMBER | 6,48,714 | 1,02,567 | 75.9 |
| Gurpreet Singh Winkal — SALES | 5,70,000 | 30,000 | **228** |
| Navdeep Singh Bhatia — JIVO_ACCOUNTS, MANAGER | 5,05,651 | 34,656 | **175** |
| Jasneet Kaur — JIVO_LEGAL, MANAGER | 4,80,000 | 2,37,500 | 24.3 |
| Ravinder Singh Malhotra — JIVO_ACCOUNTS, HOD | 4,47,860 | 1,18,620 | 45.3 |
| Prabhjot Singh Narang — JIVO MART_ECOM, HOD | 2,08,250 | **0** | never |
| Atul Sharma — PLANT & PRODUCTION, MANAGER | 2,00,000 | **0** | never |

**₹5,13,581 across 13 accounts has had no recovery whatsoever in twelve months.**

**Every one of these people is on the payroll today.** Matching each account name's `JWPL` code to the
live 611-person TankhaPay roster: **₹1,02,02,850 (96%)** is held by current staff, ₹2,10,063 sits on
16 codes absent from the roster — and the largest of those (`JWPL0010`, ₹93,429) is a duplicate-identity
artefact, the same Sushil Kumar Singh appearing as `JWPL3037` on the roster. Recovery is enforceable.

---

## 5. Nobody can see any of this

25 employees hold **₹73,38,098 (69% of the pool) across two or more accounts**, and 15 of them hold
**₹53,10,911 spread across two or more companies**. Gurvinderjeet Singh appears in Oil and Mart;
Arvinder Singh across four positive masters in Oil and Beverages (seven masters in total once
credit balances are included); Ziyaul Haque in Oil and Mart. There is no report anywhere in SAP that
shows a person's total exposure, because half of it lives in the chart of accounts and half in the
partner master, in three separate databases.

---

## What is bankable — ₹42,80,875

### Pool A — advances: ₹35,96,774

For each account: strip the medical/visa contamination, then take only what will **still be outstanding
in twelve months at that employee's own demonstrated repayment rate**. Everything else comes back anyway
and must not be claimed as a programme saving.

```sql
GREATEST(0, LEAST(BAL - non_advance_contamination, BAL - credits_last_12_months))
```

| | Balance ₹ | Contamination ₹ | Recovered 12 m ₹ | **Bankable ₹** |
|---|---:|---:|---:|---:|
| Oil (56 accounts) | 62,61,363 | 13,79,174 | 41,07,300 | **32,83,988** |
| Mart + Beverages (13) | 5,23,154 | — | 2,10,368 | **3,12,786** |
| **Pool A** | **67,84,517** | | | **35,96,774** |

### Pool B — imprest floats: ₹6,84,101

| | ₹ |
|---|---:|
| Structural float (12-month median, not the 29-Jul peak) | 17,93,784 |
| less AKAL ROZGAR YOJANA — not an employee | (1,95,203) |
| less dormant cards recalled in full | (74,447) |
| **Live float to be re-sized** | **15,24,134** |
| 40% squeeze via per-head caps tied to actual monthly spend | **6,09,654** |
| plus dormant cards recovered outright | **74,447** |
| **Pool B** | **6,84,101** |

### Bundle

| | ₹ |
|---|---:|
| Pool A — advances | 35,96,774 |
| Pool B — imprest floats | 6,84,101 |
| **Total working-capital release** | **42,80,875** |

**Interest at the measured 8.25% CC rate = ₹3,53,172 a year.** Per the audit convention this is an
**overlay on the ₹42.81 L, not additional bankable money.**

Separately, and *not* counted as savings: **₹13,79,174 of understated staff-welfare expense** must be
reclassified out of employee advances. It reduces reported profit; it does not release cash.

---

## Action

| # | Action | Owner |
|---|---|---|
| 1 | **Reclassify the ₹13,79,174 of group medical premium and visa fees** out of the 18 employee advance ledgers into staff welfare / director perquisite. Decide explicitly whether staff are meant to bear the medical premium — if not, stop allocating it to advance ledgers from the FY27 renewal (18-Dec-2026). If yes, it is a perquisite and needs Form 16 treatment. **No cash effect; it is a P&L and disclosure correction.** | **CFO + Accounts** |
| 2 | **Put every advance on a written EMI schedule through TankhaPay payroll.** Priority: the eight names above ₹2 L clearing in 24+ months or never — Gurpreet Singh Winkal ₹5.70 L (228 months), Navdeep Singh Bhatia ₹5.06 L (175), Gagandeep Singh ₹6.49 L (76), Ravinder Singh Malhotra ₹4.48 L (45), Prabhjot Singh Narang ₹2.08 L and Atul Sharma ₹2.00 L (zero recovery in 12 months). Target full clearance in 12 months → **₹35.97 L**. | **HR + Accounts** |
| 3 | **Freeze fresh advances above a written cap** (e.g. one month's gross, one advance at a time, prior advance cleared first). Without this the book keeps absorbing ~₹21 L a year and the release in #2 refills. | **CFO** |
| 4 | **Give all 69 imprest cards a sanctioned limit in the master name and enforce it.** 58 cards holding ₹29.02 L have no limit at all; 4 of the 11 that do are ₹2,67,542 over. Size each cap on the holder's actual average monthly spend, then re-measure the float on a *month-end* date, never mid-cycle. Target **₹6.10 L**. | **Accounts + Internal Audit** |
| 5 | **Recall the 13 dormant floats (₹74,447)** — 181 to 635 days without a movement. Cash or a voucher by 30 Sep 2026. | **Accounts** |
| 6 | **Build the one employee-wise net exposure view** keyed on the `JWPL` code, unioning `OACT` advance ledgers and `OCRD` imprest cards across Oil + Mart + Beverages. 25 people hold ₹73.38 L across multiple masters and 15 of them across multiple companies; today no single screen shows it. Add it to exit clearance so no full-and-final is released while any `JWPL`-coded balance is open in any company. | **IT + HR** |
| 7 | **Fix the identity break** — `JWPL0010` in SAP is `JWPL3037` on the TankhaPay roster (same Sushil Kumar Singh, ₹93,429). Any code-based recovery misses him. Reconcile SAP account names to the TankhaPay roster once, then lock naming. | **HR + IT** |
| 8 | **Stop the cross-posting** — credits memoed *"Salary Ziaul …"* are landing on Gurvinderjeet Singh's advance ledger. Reconcile each advance ledger to the employee's own payroll deduction before starting the EMI schedules in #2. | **Accounts** |

---

## Overlaps — state these before adding anything to a total

- **Internal to this bundle.** Pools A and B are **not** the same rupees — verified: zero `JDT1` lines
  carry both a `JWPL` advance ledger and an `ORGV`/`ORGC` partner code. They *are* the same **people**:
  25 employees hold ₹73,38,098 across both pools and 15 hold ₹53,10,911 across companies. Every rupee
  in my ₹42,80,875 is counted **once**; the per-employee view is a management tool, not a second claim.
- **[[finding-no-invoice-vendors]]** — its verified ₹6,55,011 includes Beverages `VENDA001090`
  GAGANDEEP SINGH ₹1,00,000, which that note itself identifies as a duplicate master of employee
  `ORGV000003 GAGANDEEP SINGH IMPREST JWPL0018`. **That ₹1 L is NOT in my pool** (the master carries
  neither `IMPREST` nor `JWPL` in its name), so there is no rupee double count — but it is the **same
  employee's money**, and his true group exposure is ₹7,18,490 + ₹1,00,000 = **₹8,18,490 across seven
  masters in three companies**. Manage it on one view (action #6); claim it once, there.
  That note also *excluded* Mart `ORGV000216 PRABHJOT SINGH IMPREST` ₹91,379 and `ORGV000212 JASNEET
  KAUR IMPREST` ₹59,380 from its ₹6.55 L as "employees, not suppliers" — those two **are** inside my
  Pool B, correctly and only here.
- **[[finding-advances-vs-open-bills]]** — its Oil vendor-group breakdown carries **`STAFF VENDOR
  (imprest) ₹7.5 L`**, a subset of my Oil Pool B (₹17,94,945). That finding is **REFUTED at ₹0**, so no
  double count arises; stated for completeness.
- **[[finding-dormant-vendor-advances]]** — no rupee overlap (trade vendors). Same theme though: it
  refuted Beverages `VENDA000945 BONUS PAYABLE` ₹66,748 as a payroll clearing residual, and my action #6
  is the general fix for payroll money hiding in the partner master.
- **[[finding-payroll-attendance]]** — same employee population and the same TankhaPay roster, but a
  **different mechanism** (attendance/pay-days vs cash advances). It is REFUTED at ₹0, so nothing to
  net. I re-use its roster join and confirm its finding that the 16 July exits hold no advances.
- **[[finding-cc-interest-conversion-rate]]** — the ₹3,53,172/yr figure is the 8.25% multiplier applied
  to my ₹42,80,875. **Overlay, never additive** to the bundle total.
- **[[finding-hs-filling-advance]]**, **[[finding-blessing-advertising-overdue]]**,
  **[[finding-trade-spend-as-credit-notes]]** — no overlap; different counterparties, different
  mechanisms.
- **Trap 2 note (intercompany).** The ₹12.48 L insurance allocation and the ₹5 L visa fee were funded
  from `2202201 JIVO MART PVT. LTD SUBSIDIARY`. Oil's advance ledgers are the debit side; if a Mart-side
  finding ever claims the mirror, that is the **same money** and must not be claimed twice.
