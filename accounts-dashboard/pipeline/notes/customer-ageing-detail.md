# customer-ageing-detail — build note

**Section:** `customer-ageing-detail`
**File:** `/Users/damanpreetsingh/jivo-cli/accounts-dashboard/pipeline/sql/customer-ageing-detail.sql`
**One statement, no trailing semicolon.** Placeholders `{{SCHEMA}}` and `{{ASOF}}`.
**Built and verified live 2026-08-21** against all three books over the HANA tunnel.
**Runtime:** 2.3 s Oil / 1.6 s Mart / 2.2 s Bev.
**Money units:** every money column is **INR rupees** (no `_L` / `_CR` suffix), 2 dp —
same convention as `vendor-ageing.sql`. The dashboard divides by 1e5 / 1e7 to display.

---

## What it is

Per-customer A/R ageing, **one row per customer, buckets as columns**. It is the
drill-down behind `customer-ageing.sql` (the KIND summary) and the A/R twin of
`vendor-ageing.sql`. The column shape is a deliberate **positional mirror of
vendor-ageing.sql — 40 columns, slot for slot** — so one dashboard renderer serves
both sections. Only the words PAY/BILL/VENDOR become RCPT/INV/CUSTOMER.

| # | vendor-ageing.sql | customer-ageing-detail.sql |
|---|---|---|
| 7 | `PAYABLE` | `RECEIVABLE` |
| 8 | `VENDOR_ADVANCE` = `GREATEST(0, +Balance)` | `CUSTOMER_ADVANCE` = `GREATEST(0, -Balance)` |
| 9 | `N_OPEN_BILLS` | `N_OPEN_INV` |
| 26/27 | `N_UNAPPLIED_PAY` / `UNAPPLIED_PAY` | `N_UNAPPLIED_RCPT` / `UNAPPLIED_RCPT` |
| 3 | `VENDOR_GROUP` | `CUSTOMER_GROUP` |

Slot 8 flips sign because A/R and A/P sit on **opposite sides of the same
`OCRD."Balance"` column** (JIVO convention: positive = DEBIT = the party owes JIVO).
Slot 13 keeps the vendor name `UNBACKED_CREDIT` for renderer compatibility, but on
the A/R side it is an unbacked **debit**: `GREATEST(0, RECEIVABLE − RAW_OPEN)` —
ledger debit carried by no open invoice. It is the summary's `BAL_NOT_IN_INV_INR`.

**Rows returned (live):** 641 Oil · 100 Mart · 454 Bev. Hundreds, not thousands.
Ordered TRADE-first, then worst-first by `ADJ_OVERDUE_60PLUS`.

---

## Tables and columns chosen, and why

| Table | Used for | Filter |
|---|---|---|
| `OCRD` (CardType='C') | **the ground truth.** `"Balance"` → `RECEIVABLE` / `CUSTOMER_ADVANCE` | `"CardType"='C'` |
| `OCRG` | `"GroupName"` → `CUSTOMER_GROUP` and the BRANCH test | join on `"GroupCode"` **and** `"GroupType"="CardType"` |
| `OINV` | open A/R invoices → `RAW_OPEN`, the buckets | `"DocStatus"='O'` AND `"CANCELED"='N'` AND `"DocTotal"-"PaidToDate">0` AND `"DocDate" <= {{ASOF}}` |
| `ORCT` | unapplied receipts → `UNAPPLIED_RCPT` (**diagnostic only**) | `"DocType"='C'` AND `"Canceled"='N'` AND `"OpenBal"<>0` AND `"DocDate" <= {{ASOF}}` |
| `ORIN` | open sales credit notes → `OPEN_CN` (**diagnostic only**) | `"DocStatus"='O'` AND `"CANCELED"='N'` AND `"DocDate" <= {{ASOF}}` |

Not used, on purpose: `JDT1`/`OJDT`. The journal settlements are what make
`DocStatus` unreliable, but their effect is **already inside `OCRD."Balance"`**, so
the balance absorbs them without touching a 526,820-row table.

### The credit adjustment (the whole point of the file)

```
RECEIVABLE     = GREATEST(0,  OCRD."Balance")                  -- ground truth
CREDIT_APPLIED = GREATEST(0,  SUM(open invoices) - RECEIVABLE) -- the fiction
```
`CREDIT_APPLIED` is then consumed **oldest-due-invoice-first** with a running
window sum (`SUM(OPENAMT) OVER (PARTITION BY CardCode ORDER BY DocDueDate, DocEntry
ROWS UNBOUNDED PRECEDING)`), and only the remainder is aged.

**Independently verified end-to-end** on Oil `CUSTA000041` BLESSING ADVERTISING:
raw SAP says `OCRD."Balance"` = 739,630 and 113 open invoices totalling 16,988,318.
The file reports `RAW_OPEN` 16,988,318, `CREDIT_APPLIED` 16,248,688, `ADJ_OPEN`
739,630 — and puts the survivor in `B6_365PLUS` at `OLDEST_DUE` 2024-01-09,
which is exactly the due date of the newest-due open invoice (799,110, partially
consumed). The credit ate the older 111 invoices, oldest first, as designed.
That customer also holds 14,290,000 across 4 receipts banked but never applied —
reported in `UNAPPLIED_RCPT`, **never subtracted**.

### Per-row identities — checked on all 1,195 rows, zero failures

```
SUM(B0..B6) + UNBACKED_CREDIT = RECEIVABLE     0 failures (worst drift 0.0000)
ADJ_OPEN                      = SUM(B0..B6)    0 failures
RAW_OPEN - CREDIT_APPLIED     = ADJ_OPEN       0 failures
ADJ_OVERDUE_60PLUS            = B3+B4+B5+B6    0 failures
negative money cells                           0
rows with RECEIVABLE>0 AND CUSTOMER_ADVANCE>0  0
```

---

## Reconciliation to `customer-ageing.sql` — it ties

Summing these rows by `ACCT_KIND` reproduces the summary row for row.
**105 checks per book, 315 across the three books. All 307 money and date checks
tie. The only 8 failures are the `N_CUSTOMERS` headcount** (Oil 3, Mart 2, Bev 3),
explained below — never an amount.

| summary column | detail aggregate |
|---|---|
| `RAW_OPEN_INR` | `SUM(RAW_OPEN)` |
| `UNAPPLIED_CREDIT_INR` | `SUM(CREDIT_APPLIED)` |
| `EFF_OPEN_INR` | `SUM(ADJ_OPEN)` |
| `NOTDUE_INR` … `D365P_INR` | `SUM(B0_NOTDUE)` … `SUM(B6_365PLUS)` |
| `OVERDUE_INR` | `SUM(B1..B6)` |
| `OD60P_INR` | `SUM(ADJ_OVERDUE_60PLUS)` |
| `MIGRATED_OPEN_INR` | `SUM(MIGRATED_OPEN)` |
| `BAL_NOT_IN_INV_INR` | `SUM(UNBACKED_CREDIT)` |
| `OCRD_DEBIT_INR` | `SUM(RECEIVABLE)` |
| `OCRD_CREDIT_INR` | `−SUM(CUSTOMER_ADVANCE)` |
| `UNAPPLIED_RECEIPTS_INR` | `SUM(UNAPPLIED_RCPT)` |
| `OPEN_CREDIT_NOTES_INR` | `SUM(OPEN_CN)` |
| `OLDEST_OPEN_DUE` | `MIN(OLDEST_DUE)` |

Live Oil TRADE row, summary vs detail-summed (INR):

```
KIND     COLUMN                              SUMMARY         DETAIL_SUM         DIFF
TRADE    N_OPEN_INV                         11489.00           11489.00         0.00
TRADE    RAW_OPEN_INR                   757095795.41       757095795.45         0.04
TRADE    UNAPPLIED_CREDIT_INR           682816665.94       682816665.95         0.01
TRADE    EFF_OPEN_INR                    74279129.47        74279129.49         0.02
TRADE    NOTDUE_INR                      22736536.12        22736536.12         0.00
TRADE    D1_30_INR                       14429429.93        14429429.94         0.01
TRADE    D31_60_INR                       8154976.87         8154976.87         0.00
TRADE    D61_90_INR                        574135.80          574135.80         0.00
TRADE    D91_180_INR                      1895372.44         1895372.44         0.00
TRADE    D181_365_INR                    14855972.52        14855972.52         0.00
TRADE    D365P_INR                       11632705.80        11632705.80         0.00
TRADE    OD60P_INR                       28958186.55        28958186.56         0.01
TRADE    MIGRATED_OPEN_INR               11039649.45        11039649.45         0.00
TRADE    BAL_NOT_IN_INV_INR               6507488.01         6507488.01         0.00
TRADE    OCRD_DEBIT_INR                  80786617.48        80786617.50         0.02
TRADE    OCRD_CREDIT_INR                -12675574.86       -12675574.80         0.06
TRADE    UNAPPLIED_RECEIPTS_INR         659246898.71       659246898.61        -0.10
TRADE    OPEN_CREDIT_NOTES_INR           11856063.13        11856063.14         0.01
TRADE    OVERDUE_INR                     51542593.35        51542593.37         0.02
TRADE    OLDEST_OPEN_DUE                  2017-08-04         2017-08-04           OK
```

Worst drift anywhere in the three books: **0.10 rupee**, on Oil's
`UNAPPLIED_RECEIPTS` across 641 rows. That is per-row `ROUND(x,2)` here vs the
summary's sum-then-round. Not a difference in the numbers.

### The one thing that does NOT match: row count

Assert the money, not the headcount. Two reasons, both harmless:

1. **This file keeps more rows.** Like `vendor-ageing.sql`, it keeps a card that
   has *any* of: open invoice, non-zero balance, unapplied receipt, open credit
   note. The summary's `N_CUSTOMERS` only counts `EFF_OPEN>0 OR Balance<>0`.
   Oil: 641 rows vs 378 counted.
2. **Sub-paise dust.** Applying the summary's own rule to this file's output gives
   353, not 378 — because **25 Oil cards (3 Mart, 9 Bev) carry dust balances**
   (smallest 0.0001; all 25 together worth **−0.0377 rupee**) that are
   `Balance <> 0` in SQL but round to `0.00` in a 2-dp output column.
   Verified: `SELECT COUNT(*) … WHERE "Balance"<>0 AND ROUND(CAST("Balance" AS DOUBLE),2)=0`
   → 25 / 3 / 9. Examples: `ORGC000006` −0.0002, `CUSTA000789` −0.0001,
   `CUSTA000484` −0.0009.

---

## Traps found and how they are handled

1. **`DocStatus='O'` is not solvency.** Raw open vs credit-adjusted, measured live:

   | book | all kinds | TRADE only |
   |---|---|---|
   | Oil | 180.69 → 108.86 Cr (1.7x) | 75.71 → **7.43 Cr** (10.2x) |
   | Mart | 128.12 → 15.90 Cr (8.1x) | 112.04 → **9.34 Cr** (12.0x) |
   | Bev | 6.34 → 4.81 Cr (1.3x) | 5.00 → **3.85 Cr** (1.3x) |

   The error is worst exactly where it matters — on the only collectable book.
   Handled by the credit adjustment above.
2. **Never subtract `ORCT."OpenBal"`.** Unapplied receipts are already inside
   `OCRD."Balance"`; subtracting again double-counts. Oil holds 71.32 Cr of
   receipts banked but never knocked off against a 108.86 Cr book — subtracting
   would have wiped two thirds of the receivable. Reported as a diagnostic only.
   Same for `OPEN_CN`.
3. **`"CANCELED"` is one `l` and has three values** on OINV/ORIN — `N` live, `Y`
   was cancelled, `C` *is* the cancelling document. Only `'N'` is counted.
   `ORCT` spells the same idea `"Canceled"` — different table, different spelling.
   Getting this wrong on ORCT throws, which is the good failure mode.
4. **Branch is not trade.** Oil's four `BRANCH CUSTOMER` cards alone carry
   **77.56 Cr** of "debtors" that are JIVO's own state GST registrations
   (JIVO WELLNESS − DL / DL ISD / HR / PB). Flagged `ACCT_KIND='BRANCH'`,
   `IS_EXCLUDED=1`, **never dropped**.
5. **Intercompany hides outside the branch groups.** Oil `CUSTA000606`
   "JIVO MART PVT LTD" sits in group **DELHI** and carries **23.86 Cr** — a
   group-only test calls it a Delhi trade customer. Caught by the name test.
   Mart `CUSTA000001` "JIVO WELLNESS PVT LTD" (2.07 Cr) sits in `PARENT COMPANY`.
   `CUSTA000236` "AKAL ROZGAR YOJANA A U O JWPL" sits in `PAN INDIA` in both Oil
   (−2.16 Cr, a credit) and Bev, caught by the `%A U O JWPL%` test.
   The C-0005 CardCode list is **AND-ed with a name test** because the same code is
   a different party in another book (`CUSTA000874` = "JIVO MART PVT LTD - DL" in
   Mart but "RAKESH BROTHER" in Oil).
6. **Staff imprest cards are not trade** — `STAFF CUSTOMER` group, 28 Oil / 8 Mart
   / 18 Bev rows. Flagged `ACCT_KIND='STAFF'`, `IS_EXCLUDED=1`, not dropped.
7. **Migrated openings.** SAP go-live 2024-09-30. Those documents carry their
   *true* original `DocDueDate` (back to 2017), so the bucket is right, but a
   3,304-day overdue is inherited history, not rot since go-live. Split into
   `MIGRATED_OPEN`: **1.10 Cr in Oil, zero in Mart and Bev.**
8. **Backdated due dates** (`DocDueDate < DocDate`) split into
   `BACKDATED_DUE_OPEN`: Oil 1.1039 Cr (essentially the same documents as the
   migrated block), Mart 28,394, Bev 60.
9. **Orphan invoices** — checked live: **zero** open invoices in any of the three
   books belong to a card that is not `CardType='C'`, and **zero** open invoices
   are dated after today. So the join drops nothing.

---

## LIVE OUTPUT — 2026-08-21, all three companies

Company totals, read off the `CO_*` columns of any row:

```
COLUMN (INR)                                    OIL                 MART                  BEV
ROWS RETURNED                                   641                  100                  454
CO_RAW_OPEN                        1,806,911,987.07     1,281,214,356.71        63,447,112.02
CO_RECEIVABLE                      1,095,113,954.14       233,528,645.03        48,284,209.06
CO_ADJ_OPEN                        1,088,606,466.13       158,971,909.77        48,142,346.06
CO_UNBACKED_CREDIT                     6,507,488.01        74,556,735.26           141,863.00
CO_UNAPPLIED_RCPT                    713,188,876.71       889,981,117.62        15,328,931.75
CO_OPEN_CN                            12,394,248.13       115,894,469.00           622,143.05
CO_CUSTOMER_ADVANCE                   34,385,774.15        51,706,403.06         3,241,245.58
CO_MIGRATED_OPEN                      11,039,649.45                 0.00                 0.00
CO_BACKDATED_DUE_OPEN                 11,039,011.86            28,394.00                60.00
CO_ADJ_OPEN_TRADE                     74,279,129.47        93,353,449.91        38,463,711.06
CO_ADJ_OVERDUE_60PLUS_TRADE           28,958,186.55         3,014,261.42        31,994,813.06

same, in CRORE                                  OIL                 MART                  BEV
CO_RAW_OPEN                                180.6912             128.1214               6.3447
CO_RECEIVABLE                              109.5114              23.3529               4.8284
CO_ADJ_OPEN                                108.8606              15.8972               4.8142
CO_UNBACKED_CREDIT                           0.6507               7.4557               0.0142
CO_UNAPPLIED_RCPT                           71.3189              88.9981               1.5329
CO_OPEN_CN                                   1.2394              11.5894               0.0622
CO_CUSTOMER_ADVANCE                          3.4386               5.1706               0.3241
CO_MIGRATED_OPEN                             1.1040               0.0000               0.0000
CO_BACKDATED_DUE_OPEN                        1.1039               0.0028               0.0000
CO_ADJ_OPEN_TRADE                            7.4279               9.3353               3.8464
CO_ADJ_OVERDUE_60PLUS_TRADE                  2.8958               0.3014               3.1995
```

Rows by `ACCT_KIND`:

| | TRADE | BRANCH | INTERCO | STAFF | total |
|---|---|---|---|---|---|
| Oil | 607 | 4 | 2 | 28 | 641 |
| Mart | 86 | 5 | 1 | 8 | 100 |
| Bev | 431 | 3 | 2 | 18 | 454 |

Worst 10 TRADE customers per book, in file order (INR):

```
===== JIVO_OIL_HANADB -- worst 10 TRADE customers by 60+ overdue (INR) =====
CARD_CODE     CARD_NAME                          GROUP               RAW_OPEN      CRED_APPL       ADJ_OPEN           60+      OLDEST  DAYS
CUSTA001014   AB ENTERPRISES                     DELHI             12,877,772              0     12,877,772    12,877,772  2025-10-14   311
CUSTA000891   FUTURE RETAIL LTD.                 PAN INDIA          9,453,888              0      9,453,888     9,453,888  2019-12-12  2444
CUSTA000636   THE AREA MANAGER CANTEEN STORE DEP PAN INDIA         20,836,040        163,772     20,672,269     3,157,122  2017-08-04  3304
CUSTA000496   INNOVATIVE RETAIL CONCEPTS PVT LTD PAN INDIA          1,680,598        486,814      1,193,784     1,193,784  2025-03-31   508
CUSTA000041   BLESSING ADVERTISING PVT LTD B SAH PUNJAB            16,988,318     16,248,688        739,630       739,630  2024-01-09   955
CUSTA000587   LIFE ESSENTIALS PERSONAL CARE PVT  HARYANA              470,183         19,000        451,183       451,183  2023-09-28  1058
CUSTA000486   WAL MART INDIA PVT LTD             PAN INDIA         10,006,206        112,632      9,893,574       347,960  2025-12-11   253
CUSTA000168   AVENUE SUPERMARTS LTD              PAN INDIA          1,132,491        916,654        215,837       215,837  2025-10-09   316
CUSTA000482   METRO CASH & CARRY INDIA PVT LTD   PAN INDIA          6,643,505            791      6,642,715       122,635  2024-12-23   606
CUSTA000356   FREE SAMPLE                        DELHI                220,925        129,686         91,239        85,509  2025-11-11   283

===== JIVO_MART_HANADB -- worst 10 TRADE customers by 60+ overdue (INR) =====
CARD_CODE     CARD_NAME                          GROUP               RAW_OPEN      CRED_APPL       ADJ_OPEN           60+      OLDEST  DAYS
CUSTA000376   ZOMATO HYPERPURE PVT LTD           DELHI              5,863,697      4,560,699      1,302,998     1,210,598  2025-06-10   437
CUSTA000880   CMUNITY INNOVATIONS PRIVATE LIMITE HARYANA            1,066,724              0      1,066,724     1,066,724  2025-08-30   356
CUSTA000496   INNOVATIVE RETAIL CONCEPTS PVT LTD PAN INDIA          1,208,061        810,518        397,543       397,543  2025-11-17   277
CUSTA000879   FLIPKART INDIA PRIVATE LIMITED     PAN INDIA          1,789,694      1,581,223        208,471       208,471  2026-03-05   169
CUSTA000680   B S A ENGINEERING LLP              DELHI                 86,219         41,135         45,084        45,084  2026-01-27   206
CUSTA000890   FLIPKART HARYANA FBF               HARYANA           10,144,097     10,101,258         42,839        42,839  2026-02-28   174
CUSTA000929   PRABHJOT SINGH                     DELHI                 30,000              0         30,000        30,000  2026-01-10   223
CUSTA000844   ILAHI CO. (BTCPN5063N)             DELHI                 96,036              0         96,036         8,555  2026-04-17   126
CUSTA000902   DEL JITENDER SINGH                 DELHI                 16,187         13,062          3,125         3,125  2026-01-29   204
CUSTA000782   GURPREET SINGH MAYAPURI STORE      DELHI                635,279        634,029          1,250         1,250  2026-01-28   205

===== JIVO_BEVERAGES_HANADB -- worst 10 TRADE customers by 60+ overdue (INR) =====
CARD_CODE     CARD_NAME                          GROUP               RAW_OPEN      CRED_APPL       ADJ_OPEN           60+      OLDEST  DAYS
CUSTA000175   BLESSING ADVERTISING PVT LTD       PUNJAB            31,675,134              0     31,675,134    29,482,566  2025-10-15   310
CUSTA000680   B S A ENGINEERING LLP              DELHI                426,205              0        426,205       426,205  2026-03-19   155
CUSTA000931   GULATI TRADERS                     DELHI                231,946              0        231,946       231,946  2025-03-31   508
CUSTA000235   SUPER MARCHE 37 TRADERS LLP        DELHI                228,469              0        228,469       228,469  2024-10-15   675
CUSTA001040   M/S MEDIA MIND                     DELHI                260,422              0        260,422       221,421  2026-01-19   214
CUSTA000900   IDEA PUBLICITY                     DELHI/NCR            150,663              0        150,663       150,663  2025-04-19   489
CUSTA000966   M/S GURU ARJAN DEV TRADING COMPANY PUNJAB               117,999              0        117,999       117,999  2025-10-03   322
CUSTA000356   FREE SAMPLE                        DELHI                 57,809              0         57,809        57,809  2026-05-11   102
CUSTA000603   RMMT HYPERMARKET LLP               DELHI                 56,250              0         56,250        56,250  2026-06-01    81
CUSTA000988   ADITYA AGENCY                      DELHI                 48,750              0         48,750        48,750  2025-10-31   294
```

### Three things worth an operator's attention (VERIFIED, from the rows above)

- **Beverages is a one-name book.** `CUSTA000175` BLESSING ADVERTISING carries
  2.95 Cr of Bev's 3.20 Cr 60+-overdue TRADE — **92%**, with nothing credited
  against it. Bev's 60+ is **83% of its entire 3.85 Cr real trade receivable**.
- **Oil's 60+ is 2.90 Cr of 7.43 Cr (39%)**, and the top three names are
  AB ENTERPRISES (1.29 Cr, 100% overdue 60+), FUTURE RETAIL LTD (0.95 Cr, oldest
  item 2,444 days — Future Retail is in insolvency) and CSD (0.32 Cr of a 2.07 Cr
  account, oldest item 3,304 days).
- **Mart is clean on ageing and dirty on reconciliation.** 60+ is only 0.30 Cr of
  9.34 Cr (3.2%) — but Mart carries **88.998 Cr of unapplied receipts** and
  **11.59 Cr of open credit notes** against a 23.35 Cr receivable, and 7.46 Cr of
  balance backed by no open invoice at all (7.32 Cr of it on the one branch card
  `CUSTA000874` JIVO MART PVT LTD - DL). Mart's books are settled almost entirely
  outside SAP's matching.

---

## Unresolved / stated plainly

1. **Back-dated `{{ASOF}}` is not a true point-in-time A/R, and the gap is large.**
   SAP keeps no history of `PaidToDate` or `Balance`, so a past as-of date ages
   *today's* open items against an older date. Measured: `{{ASOF}}=2026-03-31` on
   Oil returns `CO_ADJ_OPEN` 80.34 Cr vs 108.86 Cr today, and TRADE 2.87 Cr vs
   7.43 Cr. Use as-of = today for any number that leaves the building.
2. **Two classification divergences left in on purpose** (fixing them here would
   break the tie to `customer-ageing.sql` — fix both files together or neither):
   - Oil `CUSTA000242` **AKAL INFORMATION SYSTEMS LTD** (group DEBTORS, 10,000) is
     `TRADE` here, but `vendor-ageing.sql` classifies `%AKAL INFO%` as `INTERCO` on
     the A/P side. The two sections disagree about one card worth **0.013%** of
     Oil's TRADE book.
   - **8 employee imprest cards** (`ORGC*`, "… IMPREST JWPLnnnn") sit in a state
     group instead of `STAFF CUSTOMER`, so the group-only STAFF test misses them
     and they read TRADE: 3 in Oil (3,555), 2 in Mart (1,957), 3 in Bev (1,590).
     Under **0.005%** of TRADE in every book.
3. **`OLDEST_DUE` means something slightly different here than in
   `vendor-ageing.sql`.** This file reports the oldest due date that still carries
   money *after* credit application (matching the A/R summary's
   `OLDEST_OPEN_DUE`); `vendor-ageing.sql` reports the raw oldest open bill.
   Deliberate — the effective date is the one a collector should chase, and it is
   what makes `MIN(OLDEST_DUE)` tie to the summary. Worth aligning the two files
   eventually; not aligned today.
4. **`FREE SAMPLE` (`CUSTA000356`) is a real card with a real ageing** in both Oil
   (85,509 at 60+) and Bev (57,809). It is almost certainly not a collectable
   debtor, but nothing in OCRG or the card name marks it as internal, so it is
   left in TRADE. **Not checked** with the Accounts team.
5. **`ORIN` open credit notes are summed without a `>0` guard**, matching the
   summary exactly. If a credit note ever carries `PaidToDate > DocTotal` it would
   contribute a negative. **Not checked** whether any such row exists.
6. **The `{{ASOF}}` cut-off is on `DocDate` only**, not on `PaidToDate` or
   cancellation date. An invoice cancelled yesterday disappears from a
   `{{ASOF}}`-as-of-last-month run. Consequence of trap 1, same fix: use today.
