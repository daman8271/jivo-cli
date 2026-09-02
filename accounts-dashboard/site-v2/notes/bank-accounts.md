# bank-accounts — Bank & Cash Register

**Section id:** `bank-accounts` · **Query:** `pipeline/sql/bank-accounts.sql`
(one statement, no `-detail` companion) · **51 columns**
**As-of for everything below:** 2026-08-21 · every figure run live this session
through `hana-sql -env connections/hana-tunnel.env` (VPS-parked hanadb bridge).
**Money unit:** every money column is **INR lakhs**, suffix `_L`. Verified against
raw rupees, not assumed — see §5.
**Rows:** Oil 70 · Mart 44 · Beverages 18. **Runtime:** 1.0–1.5 s per book.

This note was written by the adversarial verifier. Claims are marked **VERIFIED**
(I ran the query and read the output) or **INFERRED** (I reasoned to it).
Verdict: **FIXED** — three defects found, two of them material, all corrected;
SQL now runs clean on all three schemas and through `build_data.py`.

---

## 1. Tables and columns, and why

| Table | Columns used | Why this table |
|---|---|---|
| `OACT` (chart of accounts) | `AcctCode`, `AcctName`, `FatherNum`, `Postable`, `CurrTotal` | The only place that knows which G/L accounts are bank/cash accounts. The bank account NUMBER lives inside `AcctName`, which is why the raw name is never emitted. |
| `JDT1` (journal lines) | `Account`, `Debit`, `Credit`, `RefDate`, `TransType`, `TransId`, `ShortName` | The ledger itself: balance as-of, 12-month movement, first/last movement, opening. |
| `OJDT` (journal headers) | `TransId`, `StornoToTr` | Identifies cancellation/reversal pairs. This is the fix for defect #1. |
| `ODSC` (bank master) | `BankCode`, `BankName` | Canonical bank name. A shipped directory of banks; nothing JIVO-specific in it. |
| `DSC1` (house bank accounts) | `GLAccount`, `BankCode`, `Account`, `Branch`/`BranchName` | The *intended* source of account number + branch. Nearly empty and partly wrong — trap 2. |
| `OCRD` + `OCRG` | `CardCode`, `CardName`, `GroupCode`, `CardType`, `GroupName` | Identifies JIVO group/branch counterparties for the inter-company flag. |

Deliberately **not** used, and why:

* `OACT."ActType"` / `"CashBox"` — they do not mark bank accounts in these books (trap 3).
* `ORCT`/`OVPM` as the account *selector* — used only as an independent completeness
  cross-check (§3) and as the independent re-derivation route (§5). On their own they
  drag in two non-bank accounts.
* `OBNK` (bank statements) — belongs to the `bank-reco` section, not to a
  position/movement register. **Not examined here.**

### The universe: parent drawer NAME, resolved through `FatherNum`

Eight drawers. **VERIFIED** live — all eight exist, spelled identically, in all
three books, and the postable-child counts add up exactly to the row counts:

```
DRAWER (parent AcctName)   CATEGORY          KIND        Oil  Mart  Bev
BANK ACCOUNTS              CURRENT_ACCOUNT   BANK          6    13    8
PAYMENT BANK ONLINE        PAYMENT_WALLET    BANK          2     2    2
CASH IN HAND               CASH_IN_HAND      CASH          3     3    3
BANK CASH CREDIT LOAN      CASH_CREDIT_OD    BANK          9     2    0
FDR                        FIXED_DEPOSIT     DEPOSIT      32    17    1
TERM LOAN                  TERM_LOAN         BORROWING    13     3    4
VEHICLE LOAN               VEHICLE_LOAN      BORROWING     4     3    0
CREDIT CARD                CREDIT_CARD       BORROWING     1     1    0
                                            TOTAL        70    44   18
```

**Out of scope on purpose:** `2202000 UNSECURED LOAN` — directors', subsidiary and
NBFC borrowings. **VERIFIED** live: Oil ≈ 2,330 L (₹23.3 Cr: directors 1,043 L,
subsidiary 1,212 L net, NBFC 75 L), Mart ≈ 233 L, Beverages nil. That is real debt
but not a bank facility, so it is **not** in this register and **not** in
`TOT_BORROWINGS_L`. Anyone quoting "total borrowings ₹85.6 Cr" for Oil off this
page is quoting *bank* borrowings; total debt is ~₹109 Cr.

---

## 2. Every trap, and how the SQL handles it

**Trap 1 — ODSC is not the house-bank table.** It is SAP's generic bank directory
(65 rows Oil / 55 Mart / 59 Bev — they differ). `"DfltAcct"` is empty on every row
in all three books (**VERIFIED**). Used only as a name lookup.

**Trap 2 — DSC1 is almost empty AND partly wrong.** **VERIFIED**: Oil 5 rows,
Beverages 3, Mart 1, against 13–30 live bank G/L accounts a book. Two rows carry a
NULL `GLAccount` (Mart's only row is one, so Mart gets zero house-bank matches).
Beverages' DSC1 rows were copied from Oil's chart and still carry Oil's G/L codes —
its `GLAccount` 2201101 does not exist in the Bev chart at all, and its 1104102 row
names a different account than Bev's own 1104102. The SQL cross-checks the DSC1
account digits against the digits inside the G/L account name and only trusts it on
`HOUSE_BANK_AGREES='AGREE'`; on `MISMATCH` it falls back to the chart and suppresses
the DSC1 branch and bank code. Live: **Oil 5/5 AGREE, Beverages' one joinable row
MISMATCHes (1104102, correctly falls back), Mart has no joinable row.**

**Trap 3 — `ActType` / `CashBox` do not mark bank accounts.** Every one of Oil's 70
banking accounts is `ActType='N'`, `CashBox='N'`, and so are ~984 other postable
accounts in the same book. Useless as a selector. (**VERIFIED** by the prior author;
I did not re-run this one — I re-ran the `FatherNum` universe instead, which is what
actually matters.)

**Trap 4 — the account-code prefix lies.** Oil's 1104106/07/08/10 carry `1104*`
("BANK ACCOUNTS") codes but hang under 2201100 BANK CASH CREDIT LOAN; 1103114–17
carry `1103*` (STOCKS) codes but hang under FDR; 2201104 and 2201402 hang under TERM
LOAN. **VERIFIED** in this session's output — e.g. 1104107 and 1104106 both come out
`CASH_CREDIT_OD`. `LIKE '1104%'` would have been wrong.

**Trap 5 — cancelling a payment does not delete it. THIS WAS THE BIG DEFECT.**
SAP posts the original *and* a mirror-image reversal and marks both ORCT/OVPM rows
`Canceled='Y'`. The old query applied no filter anywhere, so gross movement counted
the same money twice on both sides. **VERIFIED, quantified, and fixed** — see §4.

**Trap 6 — most of the bank traffic is not trade.** Branch/inter-company money is
real bank movement, so it is **flagged, not dropped**: `INTERCO_IN_12M_L` /
`INTERCO_OUT_12M_L`. The test is
`OCRG."GroupName" LIKE '%BRANCH%' OR OCRD."CardName" LIKE '%JIVO%'`.
**VERIFIED**: that two-part test covers all 23 known group CardCodes in all three
books, and — unlike hardcoding those CardCodes — does not mis-flag real third
parties (the code list is book-specific: `CUSTA000874` is a JIVO Mart branch in
Mart but MANJEET GENERAL STORE in Beverages). The group test alone is **not**
enough: Mart's `VENDA000001` "JIVO WELLNESS PVT LTD", its largest payable, sits in
group 106 PURCHASE and is caught only by the name test.

**Trap 7 — migrated openings.** `BOOK_OPENING_DATE` is *derived*, never hardcoded to
the 2024-09-30 go-live. **VERIFIED** live: Oil's banking ledger opens 2024-09-30
(32 TransType-30 lines, net −2,352.99 L), Beverages' 2024-09-30 (2 lines, net 0),
but **Mart's opens 2024-12-31** (6 TransType-30 lines, +83.17 L, nothing before it).
A hardcoded go-live date returns 0 for every Mart account.

**Trap 8 — 'CASH IN HAND' is both a drawer (1105000, `Postable='N'`) and one of its
own postable children (1105002).** The `a."Postable"='Y'` test keeps the drawer out
and the child in. **VERIFIED** the grandchild count is 0 in all three books, so the
single father-hop is sufficient today. **INFERRED risk:** if anyone ever files an
account *under* 1105002, the name-based drawer match would silently pick it up as a
top-level cash account. Latent, not live.

**Trap 9 — HANA's `CAST(<double> AS DECIMAL(n,2))` truncates, it does not round.**
The series rounds inside the DECIMAL domain (`TO_DECIMAL` first, `ROUND` second).
**VERIFIED**: the monthly series now adds back to the 12-month totals within
**±0.02 L** on every account in every book. (The old header claimed "exact"; twelve
2-dp values cannot sum to a 2-dp total exactly. Comment corrected.)

**Trap 10 — account numbers are sensitive.** They live inside `AcctName`, so the raw
name is never emitted: `GL_ACCT_LABEL_MASKED` replaces every digit with `x`, and
`ACCT_NO_MASKED` is `xxxx` + last 4. `GL_ACCT_CODE` is a chart code, not a bank
account number — safe. **VERIFIED**: no unmasked account number appears in any of
the 132 output rows.

---

## 3. Completeness — is any real bank account missing?

**VERIFIED**, re-run this session on all three books. Every distinct G/L account
ever used as `ORCT`/`OVPM` `CashAcct`/`CheckAcct`/`TrsfrAcct` is inside the universe,
with exactly two exceptions, both correctly outside it:

```
JIVO_OIL_HANADB   3200003  OPENING BALANCE ACCOUNT   (the migration offset)
JIVO_OIL_HANADB   5200015  EXCHANGE FLUCTUATIONS     (-89.15 L)
JIVO_MART_HANADB  (none)
JIVO_BEVERAGES_HANADB (none)
```

So the payment-account list on its own would have been a *worse* selector than the
chart of accounts. No real bank account is missed.

---

## 4. The defects I found, and the fixes

### DEFECT 1 (CRITICAL, fixed) — cancelled payments double-counted in gross movement

`RECEIPTS_IN_12M_L`, `PAYMENTS_OUT_12M_L`, `AVG_MONTHLY_OUT_L`, `N_LINES_12M`,
`ACTIVE_MONTHS_12M`, `MANUAL_JE_LINE_PCT_12M` and all three `MONTHLY_*_SERIES`
counted both halves of every cancelled payment. **VERIFIED** magnitude:

```
                     RECEIPTS_IN_12M_L      PAYMENTS_OUT_12M_L        lines
             before  →  after  (delta)   before  →  after  (delta)   before→after
Oil       101,144.62 → 86,464.88  −14.5%  102,404.46 → 87,724.70 −14.3%  14,380→13,112
Mart       23,788.93 → 18,914.52  −20.5%   23,817.19 → 18,942.78 −20.5%   9,154→ 8,512
Beverages   2,578.18 →  2,279.75  −11.6%    2,541.45 →  2,243.03 −11.7%   3,718→ 3,512
```

**Independent proof it is now right** (attack #9 — second route, document tables
instead of the ledger), Oil 2201101, the largest account, 2025-09-01…2026-08-21:

```
RECEIPTS_IN_12M_L  = 34,503.22 L
  ORCT (Canceled='N') into 2201101 .......... 32,451.07
  + manual-JE (TransType 30) debits .............. 922.15
  + outgoing-payment debits (refunds) .......... 1,130.00
                                    total = 34,503.22   EXACT MATCH

PAYMENTS_OUT_12M_L = 34,077.66 L
  OVPM (Canceled='N') out of 2201101 ........ 24,621.87
  + manual-JE (TransType 30) credits ............ 777.80
  + incoming-payment credits ................. 8,677.98
                                    total = 34,077.65   MATCH (1 paisa rounding)

Before the fix the same account reported 35,903.92 / 27,013.01 on TransType 24/46
against document totals of 32,451.07 / 24,621.87 — i.e. +₹34.5 Cr and +₹23.9 Cr
of money that never moved.
```

**The fix** uses `OJDT."StornoToTr"`, not the ORCT/OVPM `Canceled` flag, because it
is doc-type agnostic and also catches reversed *manual journal entries*, which the
payment flag misses (**VERIFIED**: 4 extra lines Oil, 8 Mart, 0 Bev). The storno set
is a strict superset of the cancelled-payment set — **VERIFIED**, `CANC_NOT_STORNO=0`
in all three books — and nets to **exactly 0** per account in all three books.

`BALANCE_L` and `OPENING_BAL_L` deliberately keep **all** lines, so the balance still
equals what SAP itself reports even at an as-of that falls between an original and a
later reversal. **VERIFIED**: zero accounts changed balance after the fix.
`NET_12M_L` is also unchanged (the pair nets to zero) — only the gross sides moved.

The removed churn is not hidden: it is reported in the new **`CANCELLED_GROSS_12M_L`**
(debit side = credit side, **VERIFIED** equal per account in all three books).

### DEFECT 2 (MAJOR, fixed) — inter-company money was neither flagged nor measurable

**VERIFIED**, 12 months to 2026-08-21, after the storno fix:

```
                 real payments out   to JIVO group/branch    share
Mart                  18,942.78 L         16,593.56 L        87.6%
Oil                   87,724.70 L             88.30 L         0.1%
Beverages              2,243.03 L              0.00 L         0.0%

                 real receipts in    from JIVO group/branch  share
Oil                   86,464.88 L         16,531.11 L        19.1%
Beverages              2,279.75 L             40.45 L         1.8%
Mart                  18,914.52 L             15.00 L         0.1%
```

Mart's bank account is, in effect, a conduit: **88% of everything it pays out goes to
a JIVO company or branch.** Reading `PAYMENTS_OUT_12M_L` for Mart as third-party
spend overstates it roughly eight-fold. Oil's ₹165 Cr of group receipts and Mart's
₹166 Cr of group payments are the two sides of the same flow — a useful sanity check
that the flag is picking up the real thing (**VERIFIED**, they agree to ~0.4%; the
residual is Beverages, branch-vendor flows and cross-book timing).

New columns `INTERCO_IN_12M_L` / `INTERCO_OUT_12M_L`. Money is **not** dropped —
it genuinely moved through the bank.
**Caveat, stated plainly:** attribution is at *transaction* level. A journal that
touches a group party at all has its whole bank line counted, so these two are an
**upper bound, not an allocation**. **INFERRED**, not measured — I did not decompose
multi-party payment journals.

### DEFECT 3 (MINOR, fixed) — opening balance leaked from the future

At an as-of *before* the book opened, `openday` took `MIN(RefDate)` with no as-of
guard. **VERIFIED** on Mart at `--as-of 2024-11-30`: `BOOK_OPENING_DATE` came back
**2024-12-31 (a future date)** with `OPENING_BAL_L` of 80.03 L on account 1104108
whose `BALANCE_L` was 0 and whose `FIRST_MOVE_DATE` was NULL. After the fix the same
run returns `BOOK_OPENING_DATE=NULL` and 0 openings everywhere, which is correct.
Only reachable via `--as-of`; today's daily refresh was never affected.

### NOT a defect — things I attacked and left alone

* **`TOT_CASH_AND_BANK_L` includes CC/OD.** It is the *net treasury* position, is
  documented as such, and is not read by the dashboard at all (**VERIFIED** by grep
  of `site/index.html`). I added an OVERLAP WARNING to the header instead of renaming
  a column a future consumer might depend on. The seven `TOT_*` columns are **not
  disjoint and must never be added together**; the per-account columns **are** safe
  to sum (one row per G/L account, no faceting, no fan-out).
* **`TOT_BORROWINGS_L` is gross drawn, not net.** Oil 8,561.17 L gross vs 7,041.08 L
  net, because two CC/OD accounts sit in debit (2201105 +806.68 L, 1104107 +713.40 L).
  Gross is the right reading for "what the banks have lent us". Left as is.
* **`EST_ANNUAL_INTEREST_L` at 8.47%.** An input constant handed to the section, not
  derived. The live cross-check comes out *below* it (Oil 12m: 463.37 L of debits to
  5610001 INTEREST ON BANK LOAN against ~6,149 L average drawn = 7.5% gross). Treat
  it as an upper-bound run-rate on today's drawn balance. **Not re-measured by me.**

---

## 5. Live numbers, all three companies (pasted from `pipeline/raw/`, as-of 2026-08-21)

```
== JIVO_OIL_HANADB  (70 rows) ==
  TOT_BANK_CURRENT_L       5.00   TOT_CASH_IN_HAND_L    0.12   TOT_WALLET_L     0.10
  TOT_CC_OD_NET_L      -3697.83   TOT_FIXED_DEPOSIT_L 1113.34   TOT_BORROWINGS_L 8561.17
  TOT_CASH_AND_BANK_L  -3692.61
  12m: in 86,464.88  out 87,724.70  net -1,259.79  cancelled-removed 14,679.73
       interco-in 16,531.11  interco-out 88.30  lines 13,112
  book opening 2024-09-30  never-used 4  dormant90 44  overdrawn 0  house-bank 5
   CASH_CREDIT_OD  2201101 INDIAN BANK CC A/C xxxxxxxxxx     bal -2885.59 in12 34503.22 out12 34077.66
   CASH_CREDIT_OD  2201106 TRADEPAY HSBC-xxxxx               bal -2289.02 in12  3856.72 out12  4844.43
   TERM_LOAN       2201211 LOAN TERM AXIS BANK A/C xxxxxxxxx bal -1500.00 in12     0.00 out12  1500.00
   CASH_CREDIT_OD  2201105 HSBC BANK A/C - xxxxxxxxxxxx      bal   806.68 in12 24631.15 out12 23932.80
   CASH_CREDIT_OD  1104107 ICICI BANK- xxxxxxxxxxxx          bal   713.40 in12  6235.46 out12  5525.34
   TERM_LOAN       2201210 LOAN TERM INDIAN BANK A/C- xxxxxx bal  -709.23 in12     8.77 out12   718.00

== JIVO_MART_HANADB  (44 rows) ==
  TOT_BANK_CURRENT_L       7.01   TOT_CASH_IN_HAND_L    0.00   TOT_WALLET_L    -0.73
  TOT_CC_OD_NET_L          0.00   TOT_FIXED_DEPOSIT_L    0.00   TOT_BORROWINGS_L    0.00
  TOT_CASH_AND_BANK_L      6.28
  12m: in 18,914.52  out 18,942.78  net -28.27  cancelled-removed 4,874.42
       interco-in 15.00  interco-out 16,593.56  lines 8,512
  book opening 2024-12-31  never-used 33  dormant90 34  overdrawn 3  house-bank 0
   CURRENT_ACCOUNT 1104108 ICICI BANK xxxxxxxxxxxx     bal  51.88 in12 12309.06 out12 12266.20 interco-out 10558.00
   CURRENT_ACCOUNT 1104112 HSBC BANK - xxxxxxxxxxxx    bal -49.43 in12  5994.33 out12  6055.56 interco-out  6035.56
   CURRENT_ACCOUNT 1104111 ICICI BANK - xxxxxxxxxxxx   bal   1.89 in12   145.70 out12   145.72
   CURRENT_ACCOUNT 1104109 HDFC BANK - xxxxxxxxxxxxxx  bal   1.42 in12     1.07 out12     0.04
   CURRENT_ACCOUNT 1104113 HDFC BANK - xxxxxxxxxxxxxx  bal   1.23 in12   244.00 out12   248.50
   PAYMENT_WALLET  1104202 RAZORPAY BANK               bal  -0.54 in12    13.65 out12    13.82

== JIVO_BEVERAGES_HANADB  (18 rows) ==
  TOT_BANK_CURRENT_L      44.41   TOT_CASH_IN_HAND_L    0.65   TOT_WALLET_L     0.00
  TOT_CC_OD_NET_L          0.00   TOT_FIXED_DEPOSIT_L    1.08   TOT_BORROWINGS_L    0.00
  TOT_CASH_AND_BANK_L     45.05
  12m: in 2,279.75  out 2,243.03  net 36.73  cancelled-removed 298.41
       interco-in 40.45  interco-out 0.00  lines 3,512
  book opening 2024-09-30  never-used 12  dormant90 14  overdrawn 0  house-bank 1
   CURRENT_ACCOUNT 1104106 INDIAN BANK-xxxxxxxxxx        bal 32.34 in12 1047.65 out12 1019.08
   CURRENT_ACCOUNT 1104107 ICICI BANK- xxxxxxxxxxxx      bal 12.06 in12  870.84 out12  860.67
   FIXED_DEPOSIT   1106101 FDR-ICICI BANK - xxxxxxxxxxxx bal  1.08 in12    0.07 out12    0.00
   CASH_IN_HAND    1105001 CASH SALE                     bal  0.65 in12  347.67 out12  349.76
```

**Headline, in plain money:** Oil holds ₹0.05 Cr in current accounts + ₹0.01 Cr cash
and ₹11.13 Cr in fixed deposits, against **₹85.61 Cr of bank borrowings** (of which
₹36.98 Cr is drawn cash credit / OD). Mart holds ₹0.06 Cr and owes the banks nothing.
Beverages holds ₹0.45 Cr and owes the banks nothing.

---

## 6. What I attacked, and what survived

| # | Attack | Result |
|---|---|---|
| 1 | **Double counting / fan-out.** | **SURVIVED (after fix).** No header↔line join, no UNION, no faceting. Proved no fan-out from the two new `LEFT JOIN`s: JDT1 lines in the window with and without the joins are identical (Oil 14,380 = 14,380; Mart 9,154; Bev 3,718). `grptx` is `DISTINCT` — load-bearing. Per-account rows are safe to sum; the seven `TOT_*` window columns are **not** (documented). |
| 2 | **Cancelled documents.** | **BROKEN → FIXED.** Defect 1 above. 14.5% / 20.5% / 11.6% of gross movement was cancelled churn. |
| 3 | **Branch + inter-company.** | **BROKEN → FIXED.** Defect 2 above. Was invisible; now flagged and quantified. Nothing is dropped. Name test applied, not just the group test. |
| 4 | **Unapplied money / open items.** | **N/A, correctly.** This is a G/L position, not an ageing. It never touches `OpenBal`, never uses `DocStatus='O'`, and so cannot inflate the way an open-item ageing does. `BALANCE_L` ties to `OACT."CurrTotal"`, which is ground truth. Also **VERIFIED** the session's reconciliation finding holds on *these* tables: `JDT1."IntrnMatch"=0` and `"Closed"='N'` on **100%** of banking lines in all three books (Oil 30,863 / Mart 15,579 / Bev 6,711). |
| 5 | **Migrated openings at 2024-09-30.** | **SURVIVED, plus a bug found.** Derived, not hardcoded; Mart's 2024-12-31 opening proves why that matters. The as-of leak (defect 3) was found and fixed. |
| 6 | **Three-schema portability.** | **SURVIVED.** Ran all three schemas myself, before and after. No UDF, no hardcoded account code, no Oil-only group name anywhere. The one thing that *was* book-specific — the 23 group CardCodes — is exactly why the inter-company test is written on `GroupName`/`CardName` instead. |
| 7 | **Empty and NULL.** | **SURVIVED.** Forced the universe to zero rows (drawer names replaced with junk): exit 0, header intact, **0 rows, 51 columns**, no error. The renderer has an explicit empty state. `build_data.py`'s guard only complains if all three books are empty. |
| 8 | **Money units.** | **SURVIVED.** Every money column ends `_L` and is divided by 100,000. Checked to the rupee: Oil 2201101 `BALANCE_L = -2885.59` against a raw ledger sum of **−288,559,063.04 rupees** = −₹28.86 Cr. Non-money columns (`N_LINES_12M`, `ACTIVE_MONTHS_12M`, `DAYS_SINCE_LAST_MOVE`, `ACCT_NO_NDIGITS`, `MANUAL_JE_LINE_PCT_12M`) carry no `_L`. `MONTHLY_*_L_SERIES` are strings and the renderer's `/_L$/` scaler correctly does not touch them. |
| 9 | **Re-derive the headline a different way.** | **SURVIVED.** Oil `TOT_BORROWINGS_L`: **8,561.17 L** by summing `OACT."CurrTotal"` and **8,561.17 L** by summing `JDT1` — two independently maintained stores, exact agreement. Per-account, the JDT1 sum equals `CurrTotal` on all 132 accounts with a worst absolute difference of **8e-6 rupees**. And the movement headline re-derived from the *document* tables (§4) matched to the paisa. |
| 10 | **Performance.** | **SURVIVED.** 1.5 s / 1.5 s / 1.0 s through `build_data.py`, unchanged by the fix. Hard-bounded by the chart of accounts; the largest JDT1 scan is 30,863 lines. Nowhere near the 60 s concern. |

Also attacked and clean: **ODSC over-matching** — no empty bank names, no name
shorter than 8 chars, no `%`/`_` wildcard characters, and **zero** accounts matching
more than one ODSC row in any book, so the `ROW_NUMBER` tie-break is never exercised.
**DSC1 multi-row** — exactly one row per `GLAccount` in every book, so the `MIN()`
aggregates cannot mix an account number from one row with its digits from another.
**JDT1 hygiene** — no NULL `RefDate`, no negative `Debit`/`Credit`, no line with both
sides populated, no all-zero line, in any book.

---

## 7. Still unresolved — stated plainly

1. **The inter-company columns are an upper bound, not an allocation.** Transaction-
   level attribution. A payment journal that settles ten vendors, one of them a group
   company, contributes its whole bank line. **Not measured** how often that happens.
2. **`EST_ANNUAL_INTEREST_L` is not a measured cost.** 8.47% is an input constant.
   The live cross-check on Oil comes out lower (~7.5% gross), and some borrowing cost
   sits on other accounts (2163024 TRADEPAY interest payable, 2163026 term-loan
   interest payable). The gap is explainable but **not closed**.
3. **`OBNK` / bank statements were not examined.** Whether the G/L position agrees
   with what the banks say is the `bank-reco` section's job, not this one.
4. **Trap 3 (`ActType`/`CashBox`) was not re-verified by me** — I took the prior
   author's measurement. It does not affect any output, because the universe is built
   from `FatherNum`, not from those flags.
5. **A grandchild under 1105002 would be silently picked up** as a top-level cash
   account (§2, trap 8). Zero grandchildren exist today in any book; latent only.
6. **`TOT_CASH_AND_BANK_L` is emitted but unused** by the dashboard. Kept for contract
   stability, with an overlap warning in the SQL header. If nothing ever reads it, it
   is a candidate for removal — that is a decision for whoever owns the contract, not
   a defect.
