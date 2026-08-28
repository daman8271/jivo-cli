---
type: foundation
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Business shape — what ARY is, in numbers

What the business actually looks like before any question about assortment. Everything
here is measured; nothing is inferred.

ARY is the only shop for ~5,000 people on a closed 450-acre campus. That single fact drives
[[Population]], [[Seasonality]] and every per-resident figure in this vault.

## The wallet ARY captures

12-month window, `ary assort wallet`:

| | |
|---|---|
| Sales | **₹7.55 Cr** |
| Bills | 365,087 |
| Average bill | **₹207** |
| Spend per resident per month | **₹1,259** |
| Bills per resident per month | **6.08** |

Denominator is the **stated** 5,000-resident headcount, not a queried one.

## Revenue by financial year

| FY | Net sales | Bills |
|---|---|---|
| FY23-24 | ₹6.22 Cr | 322,561 |
| FY24-25 | ₹5.84 Cr | 267,576 |
| FY25-26 | ₹6.92 Cr | 329,589 |
| FY26-27 to 21-Aug | ₹3.51 Cr | 168,881 |

Lifetime: **₹22.49 Cr net** on 1,088,607 bills; 1,891 return documents worth ₹33.84 L
(1.48% of gross).

## The books

| Group | Balance (debit-positive) |
|---|---|
| Sales A/C | ₹21.22 Cr Cr |
| Sales Return | ₹0.32 Cr Dr |
| Purchase | ₹16.54 Cr Dr |
| Purchase Return | ₹0.44 Cr Cr |
| Profit & Loss A/C | **₹2.70 Cr DEBIT** |
| Salary Expenses (6 accounts) | ₹1.51 Cr |
| Indirect Expenses (56 accounts) | ₹0.82 Cr |
| Direct Expenses (12) | ₹0.20 Cr |
| Vehicle Expenses (5) | ₹0.02 Cr |
| Deposits (Asset, 10) | ₹1.93 Cr |
| Fixed Assets (64) | ₹0.88 Cr |
| Bank Accounts (7) | ₹0.55 Cr |
| Reserves & Surplus | ₹0.51 Cr Cr |
| Secured Loans (3) | ₹0.47 Cr Cr |
| Sundry Creditors (648) | ₹0.71 Cr Cr |
| **Akal Academy Cs (3,604 accounts)** | ₹0.22 Cr Dr |
| Local Debtors - Baru Sahib (15) | ₹0.37 Cr Cr |
| Employee Customer Account (112) | ₹0.11 Cr Dr |
| Branch / Divisions (4) | ₹0.94 Cr Dr |

Crude trading margin: ₹21.22 Cr − ₹16.54 Cr ≈ **₹4.68 Cr on ₹21.22 Cr ≈ 22%** before
stock movement. **The ₹2.70 Cr debit on Profit & Loss A/C is not yet interpreted** — under
Indian convention a debit P&L balance is an accumulated loss, but this CLI presents all
balances debit-positive, so the sign has to be proved from the ledger before anyone
repeats it. Flagged, not concluded.

## Is ARY profitable? — RESOLVED

§8 flagged this as unresolved and warned nobody should repeat it. It is now settled.

### The ₹2.70 Cr is a migration opening entry

`TransactionChild` where `AccountID = 15` (Profit & Loss A/C) returns **exactly one line**:
a debit of **₹2,70,44,148**, and its voucher is **serial 1638345.0001 dated 2023-04-01** —
the first day of the books. That voucher's other legs are the whole opening balance sheet:
Cash ₹70,881 Dr, Credit Card Receivable ₹17,068 Dr, Cess @12% ₹8,280 Dr, Advance Against
Order ₹2,84,763 Cr, and a long list of creditors — Raja Ram Jai Prakash ₹2,76,950 Cr,
Himachal Wholesale Syndicate ₹3,34,070 Cr, Parhlad Chand Batra ₹2,07,815 Cr, Sunil Trading
₹1,16,222 Cr, Mangla Sales ₹1,41,719 Cr, CM Trading ₹1,12,100 Cr and others.

**It is the balancing figure of a data migration on day one, not three years of trading.**
An accumulated loss would be thousands of postings; this is one.

### ARY's actual trading result, computed from the ledger

`TransactionChild` × `AccountMaster` × `GroupMaster`, all-time (2023-04-01 → 2026-08-27):

| Group | Accounts | Debit | Credit | Net |
|---|---|---|---|---|
| Sales Accounts | 2 | ₹33,09,643 | ₹21,22,93,067 | **−₹20,89,83,423** (income) |
| Indirect Incomes | 5 | ₹1,22,557 | ₹6,08,000 | −₹4,85,443 |
| Direct Incomes | 1 | ₹5,580 | ₹2,69,421 | −₹2,63,841 |
| Purchase Accounts | 2 | ₹16,54,02,193 | ₹44,66,085 | **₹16,09,36,108** |
| Salary Expenses | 6 | ₹15,12,07,15 | ₹31,582 | ₹1,50,89,133 |
| Indirect Expenses | 38 | ₹82,74,869 | ₹63,539 | ₹82,11,331 |
| Direct Expenses | 7 | ₹19,71,016 | 0 | ₹19,71,016 |
| Vehicle Expenses | 5 | ₹2,03,041 | 0 | ₹2,03,041 |

| | |
|---|---|
| Total income | **₹20.97 Cr** |
| Total purchases + expenses | **₹18.64 Cr** |
| **Trading surplus before stock** | **+₹2.33 Cr** |
| Closing stock at cost (`ary stock value`) | +₹1.18 Cr |
| Physical-count variance (§9) | −₹0.91 Cr |
| **Cumulative surplus, 3.4 years** | **≈ +₹2.60 Cr** |
| **Annualised** | **≈ ₹0.76 Cr/yr on ~₹6.6 Cr revenue ≈ 11.6%** |

**ARY is profitable — roughly ₹76 lakh a year at an 11-12% net margin.** For a single-store
captive retailer that is a healthy result, and it is consistent with the measured 31% retail
gross margin (§25) less ~19 points of salary, indirect and direct expense.

**Two honest caveats.** (a) There is no opening-stock figure in the books (the "Opening Stock"
account sits at zero), so the closing-stock addition assumes purchases were expensed as
incurred — the standard reading, but an accountant should confirm it. (b) The physical audit
in progress will move the −₹0.91 Cr variance figure. **Confidence: high that ARY is
profitable and the ₹2.70 Cr is not a loss; medium on the exact ₹0.76 Cr/year.**

It is a coincidence worth noting rather than a finding: the cumulative surplus (₹2.60 Cr)
and the migration opening balance (₹2.70 Cr) are close in size. They are unrelated numbers.

## See also

- [[Growth-Decomposition]] — where the growth actually came from
- [[Counters]] — the eleven counters, and the three that are switched off
- [[Pricing-Fairness]] — the margin evidence, read as a fairness question
- [[Data-Quality-Traps]] — what these numbers cannot tell you
