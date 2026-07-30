---
title: CC interest — the conversion rate for every working-capital finding
created: 2026-07-28
verdict: REVISED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding]
---

# 🏦 CC interest — the conversion rate for every working-capital finding

**Verdict: REVISED — the interest is real and *bigger* than claimed, but ₹0 of it is bankable on its own.**

Part of [[SAVINGS-MOC]] · Evidence: [[expense-outliers]]

---

## What a CFO needs to know

JIVO Oil borrows on an Indian Bank cash-credit (CC) overdraft that stayed drawn between ₹27 Cr and ₹34 Cr every single day of FY25-26. That facility is the company's *marginal* rupee of funding: any cash freed up by collecting a debtor faster, clearing dead stock, or recovering a vendor advance goes straight against it. So the CC's interest rate is the exchange rate that turns every other finding in this audit into money. The original finding put that rate at **7.3%** and the annual CC interest at **₹2.07 Cr**. Both are too low. The bank's interest charges to the CC are posted in SAP as twelve clean month-end entries, so this does not need estimating at all — it can be read straight off the ledger: **JIVO Oil paid ₹2,33,56,352 of interest on the CC in FY25-26**, on a day-weighted average drawn balance of **₹28.32 Cr**, an effective rate of **8.25%**. The current year is running at 8.0%. Nothing here is collectible cash — it is the price tag on locked working capital — but the correction matters, because **every working-capital finding in this audit is worth about 13% more than the audit currently credits it with.**

---

## Verdict and re-derived numbers

| Item | Claimed (rank #21) | Re-derived (this note) | Delta |
|---|---|---|---|
| Total finance cost FY25-26 | ₹4,72,08,352 | **₹4,72,08,353** | ✅ exact |
| Interest on bank loan (5610001) | ₹4,12,67,402 | **₹4,12,67,402** | ✅ exact |
| Interest on the CC facility | ₹2,07,26,406 *(estimated)* | **₹2,33,56,352 *(measured)*** | **+12.7%** |
| CC drawn balance | ₹28,39,23,377 *(snapshot)* | **₹28,31,91,667 *(day-weighted FY25-26 avg)*** | ✅ 0.3% |
| Effective CC rate | 7.3% | **8.25%** (FY25-26) · **8.0%** (FY26-27 YTD) | **+0.95 pp** |
| Blended rate, all bank debt | 7.3% | **8.93%** | +1.6 pp |
| Total bank debt | ₹56,46,88,476 | **₹71,29,86,620** | +₹14.83 Cr |

**Bankable amount: ₹0.** This is a control observation and a multiplier, not a saving. Counting the ₹2.34 Cr here *and* counting the interest saved by the receivables / stock / vendor-advance findings would double count the same rupees.

**The one number to carry forward: use 8.25%, not 7.3%.** Every ₹1 Cr of working capital released is worth **₹8.25 lakh/yr**, not ₹7.30 lakh.

---

## Why the original 7.3% was too low

Two denominator errors, both in the same direction:

1. **The debt stack was measured today; the interest was measured in FY25-26.** Two of the three big items in the ₹56.47 Cr stack did not exist during FY25-26 and therefore bore none of the ₹4.13 Cr of interest: `2201210 LOAN TERM INDIAN BANK 8318195504` (₹7.15 Cr today, **₹0** at 31-Mar-2026) and `2201102 ICICI BANK 629305042195` (₹8.98 Cr today, **+₹4.30 lakh** — i.e. nil — at 31-Mar-2026). Dividing last year's interest by this year's larger balance sheet mechanically depresses the rate.
2. **The stack itself is incomplete.** It omits `2201106 TRADEPAY HSBC-41001`, a supply-chain-finance line that has gone from ₹3.87 Cr at 31-Mar-2026 to **₹28.54 Cr today** — now as large as the CC. Total Oil bank debt is **₹71.30 Cr**, not ₹56.47 Cr.

Neither error changes the conclusion's direction; both mean the true cost of locked capital is higher than the audit assumed.

---

## Key SQL evidence

**1 — CC interest is directly measurable (12 month-end entries, `TransType` 46, Dr 5610001 / Cr 2201101). No estimation needed.**

```sql
SELECT TO_VARCHAR(j."RefDate",'YYYY-MM-DD') AS DT, j."TransId" AS TID,
       TO_BIGINT(ROUND(IFNULL(j."Debit",0),0)) AS INT_DR
FROM JIVO_OIL_HANADB.JDT1 j
WHERE j."Account"='5610001' AND j."RefDate">=DATE'2025-04-01'
  AND j."TransId" IN (SELECT "TransId" FROM JIVO_OIL_HANADB.JDT1 WHERE "Account"='2201101')
ORDER BY j."RefDate";
```

| Month | CC interest | | Month | CC interest |
|---|---|---|---|---|
| 2025-04 | 24,37,679 | | 2025-10 | 19,96,839 |
| 2025-05 | 18,33,587 | | 2025-11 | 19,78,759 |
| 2025-06 | 14,16,651 | | 2025-12 | 23,32,869 |
| 2025-07 | 19,34,186 | | 2026-01 | 22,45,189 |
| 2025-08 | 15,68,885 | | 2026-02 | 19,63,619 |
| 2025-09 | 17,35,956 | | 2026-03 | 19,12,133 |
| | | | **FY25-26** | **₹2,33,56,352** |
| 2026-04 | 20,80,909 | | 2026-05 | 18,24,083 |
| 2026-06 | 15,65,294 | | **FY26-27 annualised** | **₹2,19,41,257** |

**2 — Exhaustive attribution of the ₹4.13 Cr `5610001` head to facilities. Reconciles to the rupee, so the CC slice is complete and nothing is double-assigned.**

```sql
SELECT BUCKET, COUNT(*) AS N, TO_BIGINT(ROUND(SUM(AMT),0)) AS TOTAL FROM (
  SELECT CASE
    WHEN EXISTS(SELECT 1 FROM JIVO_OIL_HANADB.JDT1 z WHERE z."TransId"=j."TransId" AND z."Account"='2201101') THEN '1_CC_INDIAN_BANK'
    WHEN EXISTS(SELECT 1 FROM JIVO_OIL_HANADB.JDT1 z WHERE z."TransId"=j."TransId" AND z."Account"='2201105') THEN '2_HSBC'
    WHEN EXISTS(SELECT 1 FROM JIVO_OIL_HANADB.JDT1 z WHERE z."TransId"=j."TransId" AND z."Account"='2201102') THEN '3_ICICI_WC'
    ELSE '4_TERM_OTHER' END AS BUCKET,
    IFNULL(j."Debit",0)-IFNULL(j."Credit",0) AS AMT
  FROM JIVO_OIL_HANADB.JDT1 j
  WHERE j."Account"='5610001' AND j."RefDate">=DATE'2025-04-01' AND j."RefDate"<DATE'2026-04-01') x
GROUP BY BUCKET ORDER BY BUCKET;
```

| Facility | Entries | FY25-26 interest | Share |
|---|---|---|---|
| Indian Bank CC 7007270527 | 12 | **2,33,56,352** | 56.6% |
| HSBC 166794941001 (bill discounting) | 109 | 92,03,927 | 22.3% |
| ICICI 629305042195 | 59 | 19,26,501 | 4.7% |
| Term & vehicle loans | 133 | 67,80,621 | 16.4% |
| **Total** | **313** | **4,12,67,401** | **= 5610001 ✅** |

**3 — Day-weighted average drawn balance (the correct denominator for an overdraft; month-end balances are distorted by month-end sweeps).**

```sql
SELECT TO_BIGINT(ROUND((op.OPEN_BAL*365 + mv.WTD)/365,0)) AS TIME_WTD_AVG_BAL_FY2526
FROM (SELECT SUM(IFNULL("Debit",0)-IFNULL("Credit",0)) AS OPEN_BAL
      FROM JIVO_OIL_HANADB.JDT1 WHERE "Account"='2201101' AND "RefDate"<DATE'2025-04-01') op,
     (SELECT SUM((IFNULL("Debit",0)-IFNULL("Credit",0)) * DAYS_BETWEEN("RefDate", DATE'2026-04-01')) AS WTD
      FROM JIVO_OIL_HANADB.JDT1 WHERE "Account"='2201101'
        AND "RefDate">=DATE'2025-04-01' AND "RefDate"<DATE'2026-04-01') mv;
```

- Opening 31-Mar-2025: ₹33.40 Cr drawn · Closing 31-Mar-2026: ₹34.03 Cr drawn
- **Day-weighted average FY25-26: ₹28,31,91,667**
- **Rate = 2,33,56,352 ÷ 28,31,91,667 = 8.25%**
- FY26-27 YTD: avg ₹27,44,89,368, interest ₹54,70,286 (91 days) → **7.99%**
- Blended, all bank debt: ₹4,12,67,402 ÷ day-weighted ₹46,20,88,734 = **8.93%**

The CC was drawn every day of the year (lowest month-end ₹17.90 Cr, highest ₹34.57 Cr), so cash released genuinely reduces the drawn balance rather than sitting idle — the marginal-saving logic holds.

**4 — Confirmed unchanged:** finance cost FY25-26 = ₹4,72,08,353 (`5610001` 4,12,67,402 + `5610004` 26,68,589 + `5610003` 32,20,493 + `5200004` 51,869). Related-party loans ₹10,43,23,952 (`2202102` Gurpreet Singh 6,82,10,207 + `2202101` Nirmal Kaur 2,11,00,000 + `2202103` Charanjeet Kaur 1,50,13,745). Term loans ₹19,09,65,399 across 14 accounts — matches to the rupee. **All bank borrowing sits in Oil**; Mart carries only ₹15.55 lakh of unsecured-loan interest and Beverages none.

---

## Two spin-off observations (flagged, not banked)

- **₹12.71 Cr sitting as a debit balance in the HSBC account on 28-Jul-2026** while ₹27.4 Cr of CC is drawn at ~8%. The balance climbed steadily through July (₹0.36 Cr on 6-Jul → ₹12.71 Cr on 28-Jul) as customer receipts were posted there. If that is genuinely un-swept cash it costs ~₹1.02 Cr/yr in avoidable interest; if it is an unreconciled posting it is a bank-reconciliation gap. **Not banked** — needs the HSBC statement, and the audit already establishes that most receipts are never internally reconciled.
- **₹9.84 Cr of FDRs across 31 accounts** earning ₹54,71,782 (5.56%) against CC money costing 8.25% — a ~₹26 lakh/yr negative carry. Most are almost certainly lien-marked as margin for LCs/BGs and cannot be broken, so **not banked** until the lien position is confirmed.

---

## Action

**Owner: CFO** (with Accounts to pull the documents).

1. **Change the audit's conversion rate from 7.3% to 8.25%** in every working-capital finding. Nothing else in this note produces cash; this single change does, by correctly sizing what the other findings are worth.
2. Pull the Indian Bank CC sanction letter and confirm the pricing basis (repo/MCLR + spread) and whether the spread is negotiable — the facility has been drawn ₹27–34 Cr continuously for 16 months, which is a strong renegotiation position. **1 pp off the CC alone = ₹28 lakh/yr.**
3. Add `2201106 TRADEPAY HSBC-41001` (₹28.54 Cr, 7× growth since March) to the monthly debt review — it is now the same size as the CC and is not on the finance dashboard.
4. Ask Accounts to reconcile `2201105` and report whether the ₹12.71 Cr debit is real idle cash; if so, sweep it against the CC.

---

## Overlaps — read this before adding anything up

This finding must **not** be added to the audit total. Its ₹2.34 Cr is the *cost of carrying* working capital; the savings from releasing that capital are claimed by [[receivables-aging]], [[dead-slow-stock]] and [[vendor-money-stuck]]. Adding both double counts. Its correct role is as the multiplier applied inside those findings — at **8.25%**, not 7.3%.

Related: [[expense-outliers]] (parent lens, section 6 "finance cost") · [[verify-ap-subledger-not-reconciled]] (the same reconciliation gap that makes the HSBC ₹12.71 Cr unbankable) · [[receivables-aging]] · [[dead-slow-stock]] · [[vendor-money-stuck]]
