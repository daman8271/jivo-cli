# provisions — Provisions & Accruals Register

Section id: `provisions` · SQL: `pipeline/sql/provisions.sql` (summary only, no `-detail`)
Adversarially reviewed and fixed 2026-08-21. As-of used throughout: **2026-08-21**.

Every claim below is tagged **VERIFIED** (I ran the query and read the result) or
**INFERRED** (I reasoned it from something else I verified).

---

## 1. What it reads, and why

One row per **provision / accrual liability G/L account**. This is a G/L-account
register, not a document or party register — that choice is what makes most of the
usual JIVO traps (cancelled documents, unapplied money, branch parties) not apply,
and it is why the balance ties to SAP's own trial balance exactly.

| Table | Columns used | Why |
|---|---|---|
| `OACT` | `AcctCode`, `AcctName`, `FatherNum`, `Postable`, `GroupMask`, `CurrTotal` | The chart of accounts. `FatherNum` is walked to find which accounts sit under a provision/accrual title account. `CurrTotal` is the independent lifetime cross-check. `GroupMask=2` = liabilities. |
| `JDT1` | `Account`, `TransId`, `Line_ID`, `Debit`, `Credit`, `RefDate`, `TransType`, `LineMemo` | Every G/L posting. This is the only source of money in the section. |
| `OJDT` | `TransId`, `Memo` | Only for the header memo, used by the `C_OTHER_BY_MEMO` rule. 1:1 with `JDT1.TransId`. |

**Nothing else is read.** No `OINV`/`OPCH`/`ORCT`/`OVPM`/`OCRD`.

### How an account enters the register (`FAMILY`)

- `A_PROVISIONS` — under the non-postable title account named `PROVISIONS`
  (2180000 in all three books; Bev also has a second, empty `PROVISIONS` at 2162000).
- `B_EXPENSES_PAYABLE` — under `EXPENSES PAYABLE` (2160000). Oil and Bev book their
  monthly freight/salary accruals here, so a provisions register without it is a lie.
- `C_OTHER_BY_MEMO` — any other postable liability account whose JE memo or line memo
  contains `PROVISION`, **and** where provisioning is a material part of what the
  account does (≥ ₹5 L memo-tagged credit **and** ≥ 25 % of the account's total credit).

Families are found by **walking `FatherNum`**, not by account-code prefix.

---

## 2. Headline (LIVE, as-of 2026-08-21) — VERIFIED

| Book | "Still provided for" | Accounts published | Carrying a balance | > 1 yr old | Never reversed | Over-reversed |
|---|---|---|---|---|---|---|
| **Oil** (`JIVO_OIL_HANADB`) | **₹550.62 L** (₹5.51 Cr) | 53 | 19 | ₹159.71 L | ₹156.79 L | 8 accts, ₹129.53 L |
| **Mart** (`JIVO_MART_HANADB`) | **₹359.38 L** (₹3.59 Cr) | 40 | 9 | ₹0.70 L | ₹0.00 L | 7 accts, ₹16.63 L |
| **Bev** (`JIVO_BEVERAGES_HANADB`) | **₹41.76 L** | 39 | 10 | ₹0.00 L | ₹0.00 L | 4 accts, ₹1.45 L |

Headline = `SUM(OUTSTANDING_CR_L)` — the same figure the dashboard KPI renders.

### Live output — every account still carrying a credit balance

```
BOOK FAMILY             ACCT     ACCT_NAME                            OUT_L   0-30   31-90  91-365   365+  OLDEST_OPEN  DAYS
oil  A_PROVISIONS       2180008  PROVISION FOR BAD AND DOUBTFUL DEBTS  94.57      0       0       0  94.57  2024-09-30   690
oil  A_PROVISIONS       2180002  PROVISION FOR GRATUITY                62.22      0       0    7.04  55.18  2024-09-30   690
oil  A_PROVISIONS       2180001  PROVISION FOR DEFERRED TAX             7.26      0       0       0   7.26  2024-09-30   690
oil  A_PROVISIONS       2180004  PROVISION FOR AUDIT FEES               3.15      0       0    0.45    2.7  2024-09-30   690
oil  B_EXPENSES_PAYABLE 2163022  COGS PAYABLE                         228.63  53.97  105.97    68.7      0  2026-04-02   141
oil  B_EXPENSES_PAYABLE 2165003  FREIGHT PAYABLE JUN                   37.95      0   37.95       0      0  2026-06-30    52
oil  B_EXPENSES_PAYABLE 2165002  FREIGHT PAYABLE MAY                   34.51      0   34.51       0      0  2026-05-30    83
oil  B_EXPENSES_PAYABLE 2163025  BLOWING CONVERSION PAYABLE            18.12   8.52    5.63    3.97      0  2026-04-02   141
oil  B_EXPENSES_PAYABLE 2165001  FREIGHT PAYABLE APR                   10.67      0       0   10.67      0  2026-04-30   113
oil  B_EXPENSES_PAYABLE 2163003  EXPENSES PAYABLE IMPORT               10.59  10.38    0.21       0      0  2026-06-30    52
oil  B_EXPENSES_PAYABLE 2161003  SALARY PAYABLE MAR                     3.56      0       0    3.56      0  2026-04-01   142
oil  B_EXPENSES_PAYABLE 2165012  FREIGHT PAYABLE MARCH                  1.36      0       0    1.36      0  2026-03-31   143
oil  B_EXPENSES_PAYABLE 2161004  SALARY PAYABLE APR                     1.15      0    1.15       0      0  2026-05-26    87
oil  B_EXPENSES_PAYABLE 2161001  SALARY PAYABLE JAN                     1.14      0       0    1.14      0  2026-02-17   185
oil  B_EXPENSES_PAYABLE 2161002  SALARY PAYABLE FEB                     1.12      0       0    1.12      0  2026-03-14   160
oil  B_EXPENSES_PAYABLE 2163017  LWF PAYABLE                            0.55      0    0.17    0.38      0  2026-01-31   202
oil  B_EXPENSES_PAYABLE 2163008  EXPENSE CLEARING A/C                   0.14   0.14       0       0      0  2026-08-06    15
oil  C_OTHER_BY_MEMO    2110008  SUNDRY CREDITORS CLEARING ACCOUNTS    33.93   1.98   31.95       0      0  2026-07-01    51

mart A_PROVISIONS       2180010  PROVISION FOR CLAIMS PAYABLE -RK     269.30 174.98   94.33       0      0  2026-05-31    82
mart A_PROVISIONS       2180014  PROVISION FOR JULY                    62.41  62.41       0       0      0  2026-07-31    21
mart A_PROVISIONS       2180022  PROVISION FOR MARCH                   15.98      0   15.98       0      0  2026-06-30    52
mart A_PROVISIONS       2180004  PROVISION FOR AUDIT FEES               1.00      0       0     0.3    0.7  2024-12-31   598
mart A_PROVISIONS       2180013  PROVISION FOR JUNE                     0.10      0     0.1       0      0  2026-06-30    52
mart B_EXPENSES_PAYABLE 2161005  SALARY PAYABLE MAY                     8.76      0    8.76       0      0  2026-05-31    82
mart B_EXPENSES_PAYABLE 2161006  SALARY PAYABLE JUN                     1.58      0    1.58       0      0  2026-06-30    52
mart B_EXPENSES_PAYABLE 2161001  SALARY PAYABLE JAN                     0.23      0       0    0.23      0  2026-01-31   202
mart B_EXPENSES_PAYABLE 2163019  ESIC PAYABLE                           0.02      0    0.02       0      0  2026-06-30    52

bev  A_PROVISIONS       2180005  PROVISION FOR ELECTRICITY              9.50      0     9.5       0      0  2026-06-30    52
bev  B_EXPENSES_PAYABLE 2161005  SALARY PAYABLE MAY                    12.25      0   12.25       0      0  2026-05-31    82
bev  B_EXPENSES_PAYABLE 2161006  SALARY PAYABLE JUN                    11.71      0   11.71       0      0  2026-06-30    52
bev  B_EXPENSES_PAYABLE 2165003  FREIGHT PAYABLE JUN                    5.66      0    5.66       0      0  2026-06-30    52
bev  B_EXPENSES_PAYABLE 2161003  SALARY PAYABLE MAR                     1.39      0       0    1.39      0  2026-03-31   143
bev  B_EXPENSES_PAYABLE 2165001  FREIGHT PAYABLE APR                    0.71      0       0    0.71      0  2026-04-30   113
bev  B_EXPENSES_PAYABLE 2163016  ESIC PAYABLE                           0.28      0    0.28       0      0  2026-04-30   113
bev  B_EXPENSES_PAYABLE 2163015  EPF PAYABLE                            0.15      0    0.15       0      0  2026-04-30   113
bev  B_EXPENSES_PAYABLE 2163017  LWF PAYABLE                            0.07      0    0.07       0      0  2026-05-31    82
bev  B_EXPENSES_PAYABLE 2165002  FREIGHT PAYABLE MAY                    0.04      0    0.04       0      0  2026-05-30    83
```

All amounts in **INR lakhs** (`_L`). The remaining published rows carry a nil balance
and are listed so a dormant provision account is visibly dormant, not absent.

---

## 3. The defect found and fixed

### FIXED — the FIFO ageing leaked on negative-signed postings (major)

`credits` selected `WHERE l.CR > 0` and `resid` consumed with `agg.TOT_DR`, while
`OUTSTANDING_CR_L` used `SUM("Credit") − SUM("Debit")`. JIVO's books contain lines
posted with a **negative Credit** instead of a positive Debit. Those lines were netted
out of the balance but **skipped by the FIFO**, so the age buckets came out higher
than the balance they are supposed to decompose.

- **VERIFIED, live**: Oil `2110008 SUNDRY CREDITORS CLEARING ACCOUNTS` — age buckets
  summed to **34.53 L** against `OUTSTANDING_CR_L` of **33.93 L**. Gap **₹60,030**,
  traced to exactly one JDT1 line with `Credit = −60,030.44`.
- **VERIFIED**: negative-sided lines exist across the books generally —
  Oil 470 negative-Debit / 683 negative-Credit lines, Mart 43 / 105, Bev 63 / 76
  (out of 526,820 / 344,144 / 86,404 lines). Only one of them currently lands on a
  register account, so today's exposure is ₹60 k — but the size is entirely
  data-dependent and would have grown silently.
- The SQL's own header comment asserted *"SUM of the four buckets always equals
  OUTSTANDING_CR_L exactly."* That claim was **false**.

**Fix** (surgical, in `lines` / `agg` / `credits` / `resid`): the FIFO now runs on the
**signed movement** `NET_CR = Credit − Debit`, and the consuming pool is
`TOT_CONSUME = SUM(−NET_CR) where NET_CR < 0` instead of `SUM("Debit")`. This makes
`SUM(RESID) ≡ TOT_CR − TOT_DR` by construction, and also handles negative Debits.

Safe because **VERIFIED**: no JDT1 line in any of the three books has both `Debit`
and `Credit` non-zero (`BOTH_SIDES = 0` in all three), so `NET_CR` is exactly one
signed amount and equals `Credit` (or `−Debit`) on every ordinary line.

**Blast radius — VERIFIED**: re-ran all three books before and after and diffed every
cell. Exactly **one cell** changed in the entire section:
Oil `2110008 AGE_31_90_L`: `32.55 → 31.95`. Row counts, column list and all three
headlines are unchanged.

### FIXED — header comment corrected (minor)

The comment claimed **26** columns returned; the query returns **30**. Corrected, and
the ageing paragraph now states that `CROSSED_YEAREND_L` and `MIGRATED_OPENING_L`
are re-cuts of the same residual, never extra buckets.

---

## 4. What I attacked, and what survived

### Double counting — SURVIVED (VERIFIED)
- `OJDT."TransId"` is unique (Oil 136,327 rows / 136,327 distinct; Mart 64,404/64,404;
  Bev 23,501/23,501), so the `JDT1 → OJDT` join **cannot fan out**.
- **Zero** orphan `JDT1` lines with no `OJDT` header in any book, so the inner join
  drops nothing either.
- `reg` is `GROUP BY ACCT`, and every downstream join (`OACT` on PK, `agg`, `aged`) is
  on a unique key — **one row per account**, no account in two families. `MIN(FAMILY)`
  resolves an account matched by both the tree and the memo rule to A or B over C.
- Independent cross-check: I recomputed `N_LINES`, `CREATED_CR_L`, `REVERSED_DR_L`,
  `OUTSTANDING_CR_L` and `OACT_CURRTOTAL_L` for **every published row** from a
  standalone `GROUP BY "Account"` over `JDT1` alone (no CTEs, no `OJDT`). After the
  fix: **0 mismatches in 132 rows across the three books.**
- Faceted-stacking risk: `CROSSED_YEAREND_L` and `MIGRATED_OPENING_L` overlap the
  `AGE_*` buckets by design. **VERIFIED** the renderer never sums them — it uses only
  the four `AGE_*` columns for the stack and `OUTSTANDING_CR_L` for the KPI. Now
  called out in the SQL header so nobody adds them later.

### Cancelled documents — SURVIVED, does not apply (VERIFIED)
- `OJDT` has **no `CANCELED` column** (checked `SYS.TABLE_COLUMNS`); reversals are
  separate storno JEs (`StornoToTr`), 160 of them touching Oil's register accounts.
  Both legs live in `JDT1` and net to zero.
- Directly tested the source documents feeding Oil's register accounts —
  `OPCH`(18), `OPDN`(20), `ORCT`(24), `OVPM`(46), `OIGE`(60) with `CANCELED='Y'`:
  **0 lines, 0 rupees** on every one.
- Structural proof: the section's balance equals `OACT."CurrTotal"` on every row, and
  `CurrTotal` is SAP's own trial-balance figure — definitionally net of cancellation.

### Branch / intercompany — SURVIVED, genuinely absent (VERIFIED)
Ran the **name test as well as the group test**: for every JE line on a register
account in all three books, joined `JDT1."ShortName" → OCRD → OCRG` and looked for
`GroupName LIKE '%BRANCH%'`, for `CardName LIKE '%JIVO%'`, and for all 23 group
CardCodes plus Mart's `VENDA000001 JIVO WELLNESS PVT LTD`.
**Result: zero rows, all three books.** Provisions/accruals are internal G/L
accruals — no group party appears on them, so there is nothing to flag or strip.

Two related observations kept for honesty:
- Oil `2163027 ADVERTISEMENT PAYABLE - MART` is intercompany **by name**. It is fully
  reversed (CR 193.22 L, DR 193.22 L, **outstanding 0**), so it contributes nothing to
  today's headline. If it ever carries a balance it belongs in the intercompany view.
- The only BP-linked lines on any register account are Oil `2110008` (906 lines) and
  Bev `2110008` (171). **VERIFIED** their counterparties are five internal clearing
  vendor cards — `EXPENSE PAYABLE`, `BONUS PAYABLE`, `INCENTIVE TA/DA/PAYABLE`,
  `FREIGHT PAYABLE`, `NIRMAL KAUR DIRECTOR` — not trade vendors. See §6.

### Unapplied money / open-item inflation — does not apply (VERIFIED)
This section reads no `ORCT`/`OVPM`/`ORIN`/`ORPC` and never touches `DocStatus`, so
the `OpenBal` double-subtraction trap and the ~3× open-document overstatement have no
purchase here. The balance is the G/L account balance, which is ground truth.

Related, and confirmed **for these tables specifically** (the brief asked me to verify
it rather than assume it): across **15,630** register-account JE lines
(Oil 13,482 / Mart 1,120 / Bev 1,028), `JDT1."IntrnMatch"` is **0 on 100 %**,
`"ExtrMatch"` is **0 on 100 %**, and `"Closed"` is `'N'` on **100 %**. SAP's internal
G/L reconciliation really is unused here, so SAP cannot tell us which provision is
still open and FIFO is the only defensible method. `AdjTran='Y'` on 1 Mart line only.

### Migrated openings at 2024-09-30 — SURVIVED, but READ THIS (VERIFIED)
Aged correctly (they fall in `365 d +`) **and** separately flagged in
`MIGRATED_OPENING_L`. But the size matters:

- Oil `MIGRATED_OPENING_L` total = **₹152.22 L**, which is **95 %** of Oil's
  `AGE_365P_L` of ₹159.71 L and **28 %** of Oil's whole headline.
- Mart and Bev: **₹0.00** migrated.

So the Oil KPI *"Older than a year — ₹1.60 Cr"* is almost entirely **the go-live
opening balance**, not a provision that has been sitting unreviewed since SAP came in.
The four accounts are `PROVISION FOR BAD AND DOUBTFUL DEBTS` (94.57), `GRATUITY`
(48.14 of its 62.22), `DEFERRED TAX` (7.26) and `AUDIT FEES` (2.25) — all dated
exactly 2024-09-30, all with `OLDEST_OPEN_DAYS = 690`. Those are balance-sheet
carry-forwards, and the "690 days old" reading is an artefact of the migration date.

### Three-schema portability — SURVIVED (VERIFIED)
- Ran the query myself against **all three schemas**: 53 / 40 / 39 rows, no errors.
- Nothing Oil-specific: no hard-coded account code, no UDF, no group name. The two
  root accounts are found **by name**, and both exist in all three books — Bev's extra
  empty `PROVISIONS` at 2162000 (nested under `EXPENSES PAYABLE`) is handled correctly
  because the `COALESCE` picks the **nearest** root.
- The 4-hop `FatherNum` walk is sufficient: I dumped the whole chart of accounts for
  each book and walked it independently in Python. Deepest register account is
  **2 hops** from its root in every book; **0 accounts** need more than 4. Max COA
  depth is 6 levels, roots sit at level 3.
- The only company-shaped difference is that Mart yields no `C_OTHER_BY_MEMO` row
  while Oil and Bev each yield `2110008`. That is data, not a portability bug.

### Empty and NULL — SURVIVED (VERIFIED)
- Accounts with no postings return through `LEFT JOIN agg/aged` and every money column
  is `IFNULL`-guarded → `0`; `FIRST_POST`/`LAST_POST`/`OLDEST_OPEN_DATE` are `NULL`,
  `MANUAL_JE_PCT` is `NULL` (explicit divide-by-zero guard). Bev publishes 6 such rows
  today and they render fine.
- Ran the query at `--as-of 2020-01-01` (before go-live): 29 / 19 rows, all zeros, **no
  error**. At `2024-09-30` (the migration date itself) and `2026-02-15` (to exercise
  the `MONTH < 4` branch of `FY_START`): clean, and the age invariant holds per row.
- If a book ever produced no rows at all, the renderer prints *"No provision accounts
  found in this book"* and `provisions` is in `build_data.py`'s `MAY_BE_EMPTY` set, so
  the guard would not block the build.

### Money units — SURVIVED (VERIFIED)
Every money column ends `_L` and is divided by exactly `100000`, i.e. lakhs. I
simulated the renderer's `isMoneyCol()` / `scale()` over the real 30-column list:
- all 12 `_L` money columns → detected as money, scaled ×1e5 — correct;
- `N_LINES`, `DAYS_SINCE_LAST_POST`, `OLDEST_OPEN_DAYS`, `MANUAL_JE_PCT`,
  `ACCT_CODE`, `OLDEST_OPEN_DATE`, `NEVER_REVERSED`, `DEBIT_BALANCE_FLAG` → correctly
  **not** money;
- **no mismatches in either direction.**

Note `CREATED_CR_L` / `OUTSTANDING_CR_L` / `PROV_MEMO_CR_L` / `NET_DR_MINUS_CR_L`
contain the substring `_CR` but do **not end** in `_CR`, so `scale()`'s crores branch
does not fire — they correctly take the `_L` branch. That was worth checking; a rename
to `..._CR` would silently render them 100× too large.

Live spot check: Oil `2163022 COGS PAYABLE` — raw `SUM(Credit)−SUM(Debit)` from JDT1 =
**₹22,863,389.64**; published `OUTSTANDING_CR_L` = **228.63** → ×1e5 = ₹2,28,63,000. ✓

### Headline re-derived by a second, independent route — AGREES (VERIFIED)
Route 1 is the section itself (JDT1 → CTE chain → FIFO → `OUTSTANDING_CR_L`).
Route 2 uses **`OACT."CurrTotal"` only** — SAP's own stored account balance, no `JDT1`
and no CTE at all: `SUM(GREATEST(0, −CurrTotal))` over the same account set.

| Book | Route 1 (JDT1 + FIFO) | Route 2 (OACT.CurrTotal) | diff |
|---|---|---|---|
| Oil | 550.62 L | 550.62 L | 0.00 |
| Mart | 359.38 L | 359.40 L | −0.02 |
| Bev | 41.76 L | 41.77 L | −0.01 |

The 1–2 paise-of-a-lakh gaps are per-row 2 dp rounding (round-then-sum vs
sum-then-round), not a modelling difference. Also **VERIFIED** there are **zero
future-dated JE lines** on register accounts in any book, which is why the as-of
figure and the lifetime figure coincide today.

Third, weaker corroboration: `MANUAL_JE_PCT` for Oil `2163022` recomputed by hand from
`JDT1` alone = **48.8 %**; published = **48.8 %**. ✓

### Performance — SURVIVED (VERIFIED)
| Book | before fix | after fix |
|---|---|---|
| Oil | 3.0 s | 1.6 s |
| Mart | 2.5 s | 1.3 s |
| Bev | 1.7 s | 1.2 s |

Through the real pipeline: **1.4 s / 1.0 s / 1.0 s**, 3.5 s for the whole section.
Far inside the 300 s per-statement ceiling and fine for a daily refresh. The
`memo_acct` CTE does scan `JDT1 × OJDT` with an `UPPER(...) LIKE`, which is the one
part that would grow with the books — at 527 k lines it costs about a second.

### Pipeline end-to-end — PASSES (VERIFIED)
```
$ python3 build_data.py --only provisions --no-guard
connection: home bridge (127.0.0.1:13015 -> VPS -> hanadb)
as-of 2026-08-21 — 1 section(s): provisions
  provisions
    summary   oil        53 rows    1.4s
    summary   mart       40 rows    1.0s
    summary   bev        39 rows    1.0s

wrote .../site/data.json  (9289.8 KB, 7920 summary rows, 3.5s)
```
No `FAILED` line, `errors: {}`, 30 columns per row, and all 11 other sections
preserved in `data.json` by the partial-run merge.

---

## 5. Design decisions worth knowing (not defects)

- **FIFO is a choice, not a fact.** SAP cannot tell us which provision is still open
  (§4), so debits consume the **oldest** credit first. This is deliberately
  conservative — it makes the residual look as old as possible. A reversal that
  actually cleared *last month's* accrual will still show *the oldest* accrual as
  consumed. **INFERRED**: no way to do better without `IntrnMatch`, which is unused.
- **`RESID >= 0.01` tolerance.** Running totals are `DOUBLE` (`DECIMAL` overflows on
  the 5,816-line COGS PAYABLE window), so a credit FIFO consumes *exactly* leaves a
  ~1e-7 float residue. Without the tolerance that residue rounds away in the money
  columns but still counts as "open", making a fully-reversed provision report as 386
  days old — seen live on Mart `2180014`. At ₹0.01 per line the tolerance cannot move
  a figure reported to 2 dp of a lakh (₹1,000 granularity).
- **`CREATED_CR_L` is literally `SUM("Credit")`**, so the one negative-credit line
  reduces it rather than being reported as a reversal. That is the faithful reading of
  "created"; the fix deliberately did not change it.
- **The materiality gate on `C_OTHER_BY_MEMO` is doing real work.** VERIFIED what it
  rejects in Oil: `2110004 SUNDRY CREDITOR SERVICE` (only 1.6 % memo-tagged, and it
  carries a debit balance) and the whole `2133xxx` TDS-withholding block
  (`TDS ON CONTRACTOR 194C` ₹31.03 L, `TDS ON RENT 194I` ₹19.81 L, and five more —
  4–12 % memo-tagged). Those are statutory dues, not provisions. Without the gate they
  would all land in the register.
- **Dormant accounts are published, not hidden.** Every `A_PROVISIONS` account is
  listed even at nil, so an unused provision head is visibly unused.
- **Exclusions are safe.** 6 Oil / 15 Mart / 14 Bev family accounts are filtered out by
  the `B_EXPENSES_PAYABLE` activity gate. **VERIFIED** every one of them has
  `CurrTotal = 0.00` and zero JE lines. Nothing material is being dropped.

---

## 6. Still unresolved — stated plainly

1. **The headline is gross, not net.** `SUM(OUTSTANDING_CR_L)` floors each account at
   zero, so **₹129.53 L of Oil over-reversal is not netted off** (₹16.63 L Mart,
   ₹1.45 L Bev). Oil's net G/L position across the register block is ₹421.09 L, not
   ₹550.62 L. The single biggest is `2161007 SALARY PAYABLE JUL` sitting at a
   **₹102.59 L debit** — a payable account with a large debit balance is itself worth
   an Accounts look. This is defensible for a provisions register (you want the gross
   provision carried), and `DEBIT_BAL_L` is published per account, but the dashboard's
   *"Over-reversed (debit bal.)"* KPI renders only the **count** (`String(dr.length)`),
   not the value — so the ₹129.53 L never reaches the page. That is a renderer
   change in `site/index.html`, outside this section's SQL; **I did not make it.**
2. **`MIGRATED_OPENING_L` is computed but never displayed.** The renderer's column list
   omits it, so the reader cannot see that 95 % of Oil's "Older than a year" is the
   go-live opening (§4). Again a renderer change; not made here.
3. **Possible overlap with the vendor-ageing section.** Oil `2110008` (₹33.93 L) and
   Bev `2110008` are fed entirely through five internal clearing **vendor cards**
   (`VENDA001219 EXPENSE PAYABLE` alone is ₹33.08 L net credit). If `vendor-ageing`
   also reports those cards, the same money appears in two sections of the dashboard.
   **INFERRED** — I did not read the vendor-ageing SQL, it is another agent's section.
   Worth one cross-check before the two numbers are ever added together.
4. **The `C_OTHER_BY_MEMO` thresholds (₹5 L, 25 %) are hard-coded and absolute**, not
   scaled to book size. They behave sensibly on all three books today (§5), but a
   materially smaller fourth book would let more through, and a much larger Oil would
   let less. **INFERRED**, no live failure observed.
5. **`NEVER_REVERSED` reads `'N'` for an account that has never been posted at all**
   (`TOT_CR = 0`), which is technically true but reads oddly next to a nil row. Cosmetic;
   the KPI weights by `OUTSTANDING_CR_L` so a nil account contributes nothing. Not changed.
6. **Pre-go-live as-of dates list some `B_EXPENSES_PAYABLE` accounts spuriously**, because
   that family's gate tests lifetime `OACT."CurrTotal"` alongside as-of line count. Harmless
   for the daily refresh (as-of = today) and the money columns are all zero, but a
   historical month-end run before 2024-09-30 will show extra nil rows. Not changed —
   fixing it would mean changing the gate, and the churn is not worth it.
