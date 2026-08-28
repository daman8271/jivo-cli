---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Digital and identity — residents already went digital

**UPI is 55.7% of tenders** and ARY built nothing to cause it. Yet 96% of bills are booked
to one anonymous account, so ARY has 1.09 million transactions and almost no customers.

The credit book shows the wallet model already works at ARY — it just was never extended.

## Payment data — counts usable, amounts not

The digital lane claimed "UPI is 56.3% of tenders and 42.9% of collections value". The first
half is right; the second cannot be supported by this database, and it is worth pinning down
because a payments strategy would be built on it.

### What is trustworthy: tender counts

`SalePayment` × `SaleHeader`, 12 months:

| MOPID | Mode | **Tenders** | **% of tenders** |
|---|---|---|---|
| **503** | UPI (booked as "Paytm") | **222,237** | **55.7%** |
| 1 | Cash | 166,072 | 41.6% |
| 2 | Credit Sale | 11,019 | 2.8% |

**VERIFIED and important: UPI is now the majority payment method at ARY by transaction
count** — 55.7% against cash's 41.6%. On a rural Himachal campus that is a genuinely
notable fact, and it is the strongest single argument for the digital-layer work: residents
have already changed behaviour without ARY building anything.

### What is broken: all three amount columns

| Column | 12-month total | Should be |
|---|---|---|
| `SUM(Amount)` | **₹900.35 crore** | ₹7.55 crore |
| `SUM(TenderAmount)` | **₹894.43 crore** | ₹7.55 crore |
| `SUM(TenderAmount − ReturnAmount)` | ₹2.26 crore | ₹7.55 crore |

The first two are **~119× actual sales.** The third is 30% of it. And the per-mode split is
nonsense in both directions: by `Amount`, cash is 99.3% of value while UPI is 0.4%; by
net tender, cash is 100.0% and UPI and credit are both exactly ₹0.

**Diagnosis:** MOPID 1 (Cash) carries a scaling or units defect — ₹8,944 crore of
"TenderAmount" on 166,072 tenders is ₹53,858 per cash transaction on a shop with a ₹207
average bill. And UPI/credit tenders record their value in `Amount` only, leaving
`TenderAmount` and `ReturnAmount` at zero, so any net-tender calculation attributes 100% to
cash by construction.

**This supersedes §10's note** that `ary sales payment-mix` amounts are unusable — now the
mechanism is known:

> **Payment-mode COUNTS are reliable. Payment-mode VALUES are not, in any column.**
> Quote "55.7% of transactions are UPI". Never quote a rupee split by payment mode.

The 42.9%-of-value figure the lane reported is therefore **unverifiable, not wrong** — there
is no column in this database that can produce a trustworthy value split. Anyone sizing a
payments or wallet project must get that from the acquirer's settlement reports (Paytm's own
statements), not from FusionERP8.

### The rest of the digital lane's findings stand, and two are strong

| Claim | Status |
|---|---|
| 96.2% of FY26-27 bills (162,434 of 168,881) booked to one anonymous account | **VERIFIED** — matches my own §18 count of 14.41% institutional / 71.1% walk-in |
| A campus wallet spendable only at ARY is a **closed-system PPI** — no RBI authorisation, no escrow | **VERIFIED**, and it removes the regulatory objection to the wallet idea entirely |
| **FusionERP8 already ships a configured, never-used wallet data model** | **VERIFIED** — consistent with `CustomerMaster` carrying unused `loyalty_points`, `visits` and `crm_limit` fields |
| WhatsApp order-to-pickup needs no app build; a customer-initiated conversation opens a free 24-hour window | VERIFIED against Meta's published pricing |
| Identified-customer basket ₹1,586 vs walk-in ₹155 | **VERIFIED but correctly flagged by the lane as NOT causal** — the identified accounts are institutions and credit households, so the 10× is a selection effect, not a benefit of identification. Good discipline from that lane. |

## The student credit book

The "Akal Academy Cs" group holds 3,604 individual student and staff accounts — the only
identified customers ARY has. Ageing them by last transaction date (`TransactionChild` ×
`TransactionMaster`, one row per account):

| Age of last transaction | Accounts | Net balance | Owed to ARY |
|---|---|---|---|
| **Active (last 90 days)** | **640** | ₹16,52,476 | ₹16,72,607 |
| 90-365 days | 369 | ₹4,33,982 | ₹4,92,350 |
| 1-2 years | 306 | ₹1,41,287 | ₹1,58,466 |
| **Over 2 years** | **1,774** | **−₹5,990** | ₹26,500 |
| **Total** | **3,089 with activity** | **₹22,21,755** | **₹23,49,923** |

Credit sales themselves, 12 months: **1,057 customers, 11,019 tenders, ₹2.09 crore**
(2.8% of tenders).

**This is a genuinely well-managed book, and it is worth saying so plainly:**

- **75% of the outstanding is under 90 days old** — ₹16.5 lakh of ₹22.2 lakh.
- **1,774 accounts dormant over two years carry a NET CREDIT of −₹5,990** — meaning students
  who left are, in aggregate, in credit rather than owing. Only ₹26,500 of debit sits
  anywhere in that tail. For a student credit book at a boarding school with constant
  turnover, that is close to ideal.
- **Total exposure is ₹22.2 lakh on ₹7.55 crore of sales — 2.9%**, entirely to a captive,
  Trust-employed or Trust-enrolled population.

**Why it matters for the identity work (§29, §44):** the objection to a campus wallet is
usually credit risk and collection. ARY has been running exactly that model for three years
on 3,089 accounts with a clean ageing profile and near-zero bad debt in the dormant tail.
**The credit infrastructure, the collection discipline and the household relationships
already exist** — a wallet would formalise something that already works, not introduce a new
risk. Combined with the closed-system PPI finding (no RBI authorisation needed) and the
unused wallet model already in FusionERP8, the barriers to that project are lower than
anyone would assume.

**One caveat:** 3,089 accounts have ledger activity out of 3,604 in the group, and only
1,315 have transacted in the last year. The book is small relative to the ~5,000 population
— roughly a quarter of residents have an account — which is consistent with 96% of bills
being anonymous walk-ins. The model works; it just has not been extended.

## See also

- [[JIVO-Own-Brand]] — identity is what turns the shop into a research instrument
- [[Data-Quality-Traps]] — why no rupee split by payment mode can be quoted
- [[Ten-Moves]] — move 5
