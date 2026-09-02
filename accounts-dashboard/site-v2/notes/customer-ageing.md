# customer-ageing — adversarial review note

**Section:** `customer-ageing` (summary; the per-customer twin is `customer-ageing-detail`)
**File:** `/Users/damanpreetsingh/jivo-cli/accounts-dashboard/pipeline/sql/customer-ageing.sql`
**One statement, no trailing semicolon.** Placeholders `{{SCHEMA}}` and `{{ASOF}}`.
**Reviewed adversarially and fixed 2026-08-21**, live against all three books over the HANA tunnel.
**Verdict: FIXED** — one material defect found and corrected (the counts, not the money).
**Runtime:** 1.0 s Oil / 0.8 s Mart / 0.9 s Bev (summary). Detail adds 2.5 / 1.6 / 2.1 s.
**Money units:** every money column is **INR rupees** and is named `*_INR`. No `_L`, no `_CR`
anywhere in this file. VERIFIED against `OCRD."Balance"` directly — `OCRD_DEBIT_INR` for Oil
BRANCH is `775637171.8`, and the four Oil branch cards sum to `775,637,172` rupees in `OCRD`.
The names do not lie about their scale.

---

## What it returns

One row per **KIND** of customer account plus a `ZZ_TOTAL` roll-up. Five rows per book.

| KIND | what it is |
|---|---|
| `BRANCH` | JIVO's own state GST registrations (`OCRG."GroupName"` LIKE `%BRANCH%`) |
| `INTERCO` | the other JIVO legal entities / units (Oil ↔ Mart ↔ Bev, and `A U O JWPL`) |
| `STAFF` | employee imprest "customer" cards |
| `TRADE` | real external customers — **the only collectable book** |

Branch and interco are **flagged, never dropped and never silently included**. How much of
the headline they are (VERIFIED, `EFF_OPEN_INR`, 2026-08-21):

| book | BRANCH+INTERCO | ZZ_TOTAL | share that is JIVO's own money |
|---|---:|---:|---:|
| Oil | ₹101.42 Cr | ₹108.86 Cr | **93.2 %** |
| Mart | ₹6.56 Cr | ₹15.90 Cr | **41.3 %** |
| Bev | ₹0.85 Cr | ₹4.81 Cr | **17.8 %** |

---

## Tables and columns, and why

| table | columns | why |
|---|---|---|
| `OCRD` | `CardCode`, `CardName`, `Balance`, `GroupCode`, `CardType` | `Balance` is the **anchor**: the ground-truth net position. `CardType='C'` scopes to customers. |
| `OCRG` | `GroupCode`, `GroupType`, `GroupName` | the BRANCH / STAFF / PARENT-COMPANY classification |
| `OINV` | `DocEntry`, `DocDate`, `DocDueDate`, `DocTotal`, `PaidToDate`, `DocStatus`, `CANCELED` | the open items to age. `DocTotal − PaidToDate` is the open amount; `DocDueDate` drives the bucket. |
| `ORCT` | `CardCode`, `DocType`, `Canceled`, `OpenBal`, `DocDate` | **diagnostic only** — unapplied customer receipts |
| `ORIN` | `CardCode`, `DocStatus`, `CANCELED`, `DocTotal`, `PaidToDate`, `DocDate` | **diagnostic only** — unapplied sales credit notes |

**Why it is not a naive open-invoice ageing.** `DocStatus='O'` is not solvency at JIVO:
invoices are settled by manual journal entries and by on-account receipts that were never
internally reconciled, so they stay `'O'` long after the cash landed. Per customer the query
derives `UNAPPLIED = max(0, Σ open invoices − max(0, OCRD."Balance"))`, consumes it
oldest-due-invoice-first with a HANA window sum, and ages only the remainder. On the Oil
TRADE book that is the difference between **₹75.71 Cr and ₹7.43 Cr — a factor of 10.2**.

---

## THE DEFECT FOUND — and fixed

**The section corrected the money and then quoted SAP's uncorrected counts next to it.**

`N_CUSTOMERS` and `N_OPEN_INV` are SAP's raw counts. After the credit netting most of those
invoices carry nothing at all. The dashboard KPI read:

> **External trade — really owed  ₹7.43 Cr**
> 355 customers · 11,489 invoices

Both counts are wrong for that figure. VERIFIED live, TRADE book:

| book | customers reported | actually carry it | invoices reported | actually carry it |
|---|---:|---:|---:|---:|
| Oil | 355 | **89** | 11,489 | **1,360** (11.8 %) |
| Mart | 54 | **23** | 3,975 | **674** (17.0 %) |
| Bev | 361 | **192** | 796 | **454** (57.0 %) |

A reader divides ₹7.43 Cr by 11,489 and gets ₹6,466 an invoice. The truth is ₹54,617 across
1,360 invoices. On a page whose entire thesis is *"SAP's headline number is wrong, read the
second one"*, pairing the corrected money with SAP's uncorrected count reintroduces exactly
the error the section exists to remove.

**Fix (strictly additive — no existing value moved):**
- `ag` CTE now carries `SUM(CASE WHEN EFFOPEN > 0 THEN 1 ELSE 0 END) AS NEFFINV`.
- Two new output columns: **`N_EFF_CUSTOMERS`** and **`N_EFF_INV`**, beside their raw twins.
- `site/index.html` `renderKindAgeing()` now reads the effective counts for the KPI subtitle
  (with a `== null` fallback so a stale `data.json` still renders), strikes SAP's count
  through beside them, and shows both pairs in the section table.

**Proved additive:** the post-fix run was diffed cell-by-cell against the pre-fix raw TSVs —
**330 pre-existing cells compared, 0 changed**, columns added `['N_EFF_CUSTOMERS','N_EFF_INV']`.

Cosmetic residue, stated plainly: `N_EFF_CUSTOMERS` for Oil TRADE is **89**, while summing the
detail file's `ADJ_OPEN > 0` rows gives **85**. The four extra are sub-paise dust balances that
are `> 0` in SQL but round to `0.00` in the detail's 2-dp column — the same dust the detail
note already documents for `N_CUSTOMERS`. It is not a disagreement about any amount.

---

## Every axis I attacked, and what survived

### 1. Double counting — SURVIVED (VERIFIED)
- **Join fan-out.** `OCRD LEFT JOIN OCRG` is the only header-to-header join. Row counts before
  and after the join are identical in all three books (Oil 1176/1176, Mart 943/943, Bev
  1262/1262), and `(GroupCode, GroupType)` is distinct in `OCRG` (47/47, 45/45, 45/45).
  No line table is touched anywhere, so no header-against-line fan.
- **Independent re-derivation, route 2.** I rewrote the whole allocation as a closed form with
  **no window function at all** — `Σ LEAST(TOTOPEN, GREATEST(0, Balance))` per card — and got,
  for Oil: `BRANCH 775,637,171.80 · INTERCO 238,561,817.87 · STAFF 128,347.00 · TRADE
  74,279,129.47`. **Identical to the section, to the paisa, on every KIND.** The window-function
  allocation is arithmetically equivalent to the closed form; it does not double-apply credit.
- **Faceted stacking.** `ZZ_TOTAL` sits in the same result as the four KIND rows, so summing
  every row gives exactly 2×. The renderer does not: the hero filters `KIND === 'TRADE'`, and
  the "branch/interco/staff" KPI excludes both `TRADE` and `ZZ_TOTAL`. **Any new consumer must
  filter by KIND. This is the section's one live landmine.**
- **Detail ↔ summary.** Aggregating the 1,195 detail rows by `ACCT_KIND` and comparing to the
  summary: **276 checks pre-fix and 300 post-fix, 0 mismatches.**

### 2. Cancelled documents — SURVIVED (VERIFIED)
`"CANCELED"` (one `l`) is applied on `OINV` and `ORIN`; `ORCT` spells it `"Canceled"` and is
filtered too. I checked the full distribution: `CANCELED` has **three** values — `N` live,
`Y` was cancelled, `C` *is* the cancelling document. Every `Y` and `C` row in all three books is
`DocStatus='C'` with **zero** open amount, and every cancelled `ORCT` has `OpenBal = 0`. So the
filters are belt-and-braces rather than load-bearing — but they are correct and they are present
on **every** document table touched.

### 3. Branch + intercompany — SURVIVED (VERIFIED), with two documented specks
I dumped every customer card in all three books matching `%JIVO%`, `%JWPL%`, `%WELLNESS%`,
`%A U O%`, a `%BRANCH%` group, `PARENT COMPANY`, `COMPANY UNIT CUSTOMER`, or one of the 23
group CardCodes, and read the result card by card.
- **The name test is the one that matters, and it is applied.** The CardCode list is `AND`-ed
  with `UPPER(CardName) LIKE 'JIVO%'`, so `CUSTA000874` is INTERCO in Mart ("JIVO MART PVT LTD
  - DL") and TRADE in Oil ("RAKESH BROTHER") — correct in both. The same holds for
  `CUSTA000875/876/877/878/906/926/1099/1113` across the three books: every one of them is a
  real outside shop in at least one book and is classified TRADE there.
- **All 23 group CardCodes are caught** in the book where they are intra-group. Every one of
  them starts with `JIVO`, so the code list is in fact redundant — route 2 above, which dropped
  the code clause entirely, produced identical numbers. Harmless; left in as belt-and-braces.
- **The group-only test is genuinely not enough**, and the file knows it. `CUSTA000236 AKAL
  ROZGAR YOJANA A U O JWPL` sits in group `PAN INDIA` — a trade group — carrying **−₹2.16 Cr**
  in Oil. It is caught only by the `%A U O JWPL%` name clause. Without it, Oil's TRADE credit
  balance would be overstated by ₹2.16 Cr.
- **Beverages has no `PARENT COMPANY` and no `COMPANY UNIT CUSTOMER` group at all** — its two
  INTERCO cards are found by the name test alone. The group test is not portable; the name test
  is. Both are present, so all three books classify correctly.
- **Nothing intra-group is hiding in TRADE.** The top twelve TRADE debtors in each book are
  Canteen Stores Department, Walmart, Metro, Future Retail, Flipkart, Amazon, Zomato Hyperpure,
  BigBasket, Zepto (`KNOWTABLE ONLINE SERVICES`), R K Worldinfocom, Blessing Advertising — all
  external.

### 4. Unapplied money — SURVIVED (VERIFIED), and it is *not* double-subtracted
This is where an A/R ageing usually breaks, so I checked it hardest.
- `ORCT."OpenBal"` and open `ORIN` are **diagnostics only**. Neither is netted off anything.
  `EFF_OPEN_INR` is derived purely from `OCRD."Balance"` and `OINV`, and `OCRD."Balance"`
  already contains both. **There is no double subtraction, and the figure is not inflated.**
- `ORCT."OpenBal"` really is the unapplied amount, not a blanket document total. Oil, customer
  receipts: 8,513 rows at `OpenBal = 0` (fully applied), 2,773 at `OpenBal = DocTotal` (fully
  on account), 133 partial. `Σ OpenBal` = **713,188,876.71**, which is `UNAPPLIED_RECEIPTS_INR`
  in the Oil `ZZ_TOTAL` row **to the paisa**. Same tie for Mart (889,981,117.62) and Bev
  (15,328,931.75). Zero orphan receipts — every `ORCT` `CardCode` resolves to a `CardType='C'`
  card in all three books.
- Open `ORIN` ties the same way: Oil 12,394,248.13, Mart 115,894,469.00, Bev 622,143.05, each
  equal to a straight `ORIN` table scan. Nothing lost to the join.
- `ODPI` (A/R down-payment invoices) is **empty in all three books** — nothing missed there.

### 5. Migrated openings at 2024-09-30 — SURVIVED (VERIFIED)
Oil has **11,078** invoices dated exactly 2024-09-30 with `DocDueDate` back to **2017-08-04** —
the migrated opening A/R, carrying its true original due date, so the bucket is right.
`MIGRATED_OPEN_INR` splits it out: **₹1.10 Cr** of Oil's ₹7.43 Cr TRADE book (14.9 %) is
inherited history, and it is **95 %** of Oil's `D365P_INR` (₹1.10 Cr of ₹1.16 Cr) — the
oldest bucket on the Oil trade book is almost entirely pre-SAP history.
`MIGRATED_OPEN_INR = 0.00` for Mart and Bev is a **true zero, not a missed date**: Mart's first
invoice is 2024-10-03, Bev's 2024-10-04, and neither book has an opening batch. Confirmed by the
detail file's independent `BACKDATED_DUE_OPEN` (due date before doc date): Oil ₹1,10,39,012 —
the same money — Mart ₹28,394, Bev ₹60. The hard-coded date is now documented in the SQL header
as an Oil fact to re-check if a fourth book is ever added.

### 6. Three-schema portability — SURVIVED (VERIFIED)
Run against all three schemas myself, twice (pre- and post-fix). No UDF is referenced anywhere,
no account code is hard-coded, and the only group names used are `%BRANCH%` (present in all
three), `STAFF CUSTOMER` (all three), and `PARENT COMPANY` / `COMPANY UNIT CUSTOMER` (**absent
in Beverages** — which is why the name test carries the classification, see §3). All four KINDs
are present in all three books.

### 7. Empty and NULL — SURVIVED (VERIFIED by forcing it)
I ran the statement with the card filter flipped to `CardType='X'` so that **zero** customers
match. It returns a **header and no data rows** — HANA's `GROUPING SETS ((KIND),())` emits no
grand-total row over empty input — and does **not** error. The renderer's first line is
`if (!summary.length) return '<div class="empty">No open customer balances.</div>'`, so a book
with no customers renders a clean empty state rather than crashing or showing a confident zero.
NULL hazards: `GREATEST(0, NULL)` is NULL in HANA and would silently break the reconciliation
identity, so I checked — **zero** NULL `OCRD."Balance"`, **zero** NULL `DocTotal`/`PaidToDate`,
**zero** NULL `DocDueDate` on open invoices, in all three books. The hazard is real but not live.

### 8. Money units — SURVIVED (VERIFIED)
All 18 money columns are named `*_INR` and hold raw rupees. Cross-checked against `OCRD` and
against the journal (below). The renderer's `scale()` tests `/_CR$/` then `/_L$/`; no column in
this file ends in either, so every value passes through unscaled. **Nothing renders 100,000×
wrong.** The two columns I added are counts and match neither the money regex nor the scaler.

### 9. Re-derive the headline a different way — SURVIVED (VERIFIED), two independent routes
The biggest figure the section reports is Oil `ZZ_TOTAL` `EFF_OPEN_INR` = **₹108.86 Cr**, of
which `BRANCH` **₹77.56 Cr** is the largest single row, and the number the dashboard leads with
is Oil TRADE **₹7.43 Cr**.
- **Route 2 (closed form, no window function):** reproduced every KIND to the paisa — see §1.
- **Route 3 (the journal, not `OCRD` at all):** the model rests entirely on trusting
  `OCRD."Balance"`, so I rebuilt every customer balance from `JDT1` (`Σ Debit − Credit` by
  `ShortName`) and compared card by card:

  | book | Σ `OCRD."Balance"` | Σ from `JDT1` | diff | cards disagreeing |
  |---|---:|---:|---:|---:|
  | Oil | 1,060,728,179.99 | 1,060,728,179.99 | **0.00** | **0 of 1,176** |
  | Mart | 181,822,241.97 | 181,822,241.97 | **0.00** | **0 of 943** |
  | Bev | 45,042,963.48 | 45,042,963.48 | **0.00** | **0 of 1,262** |

  Zero cards disagree in any book. The anchor is sound.
- **Internal identity**, asserted on all 15 rows post-fix:
  `EFF_OPEN_INR + BAL_NOT_IN_INV_INR = OCRD_DEBIT_INR`, and the seven buckets sum to
  `EFF_OPEN_INR`. **0 failures.**

### 10. Performance — SURVIVED (VERIFIED)
**1.0 s Oil / 0.8 s Mart / 0.9 s Bev** for the summary; 2.5 / 1.6 / 2.1 s for the detail.
Nowhere near the 60 s concern or the pipeline's 300 s ceiling. No index hints needed.

---

## The one thing that is an assumption, not a measurement — READ THIS

`EFF_OPEN_INR` **does not depend** on how the unapplied credit is allocated. I re-ran the whole
allocation newest-first instead of oldest-first: the totals are **identical to the paisa** in all
three books. That number is solid.

**The bucket split does depend on it, and on Mart it depends on it enormously.** TRADE, 60+ days
overdue, same day, same data:

| book | oldest-first (shipped) | newest-first | factor |
|---|---:|---:|---:|
| Oil | ₹2.90 Cr | ₹3.42 Cr | 1.18× |
| **Mart** | **₹30.14 L** | **₹8.46 Cr** | **28×** |
| Bev | ₹3.20 Cr | ₹3.24 Cr | 1.01× |

Oldest-first (FIFO) is the accounting convention and is kept. But **Mart's overdue buckets are a
lower bound produced by an assumption**, not a measurement, and the dashboard's "overdue 61 d +
₹30.14 L" for Mart should be read that way. There is no fact available to replace the assumption
with: SAP's internal reconciliation is unused, so nobody recorded which receipt paid which
invoice. This is now stated in the SQL header. It is the single most important caveat in the
section and it was previously undocumented anywhere.

---

## LIVE OUTPUT — 2026-08-21, post-fix, straight from `raw/`

### Oil (`JIVO_OIL_HANADB`)
```
KIND      N_CUSTOMERS  N_EFF_CUSTOMERS  N_OPEN_INV  N_EFF_INV  RAW_OPEN_INR   UNAPPLIED_CREDIT_INR  EFF_OPEN_INR
BRANCH    4            4                931         931        775637171.8    0                     775637171.8
INTERCO   2            1                189         164        269462393.87   30900576              238561817.87
STAFF     17           11               398         23         4716626        4588279               128347
TRADE     355          89               11489       1360       757095795.41   682816665.94          74279129.47
ZZ_TOTAL  378          105              13007       2478       1806911987.07  718305520.94          1088606466.13

KIND      NOTDUE_INR   D1_30_INR     D31_60_INR  D61_90_INR  D91_180_INR  D181_365_INR  D365P_INR    OVERDUE_INR    OD60P_INR
BRANCH    94007        325977        73139       275095      7658420      167642489     599568044.8  775543164.8    775144048.8
INTERCO   15106560     223455257.87  0           0           0            0             0            223455257.87   0
STAFF     0            3346          5658        49109       2115         68119         0            128347         119343
TRADE     22736536.12  14429429.93   8154976.87  574135.8    1895372.44   14855972.52   11632705.8   51542593.35    28958186.55
ZZ_TOTAL  37937103.12  238214010.8   8233773.87  898339.8    9555907.44   182566580.51  611200750.6  1050669363.02  804221578.35

KIND      MIGRATED_OPEN_INR  BAL_NOT_IN_INV_INR  OCRD_DEBIT_INR  OCRD_CREDIT_INR  UNAPPLIED_RECEIPTS_INR  OPEN_CREDIT_NOTES_INR  OLDEST_OPEN_DUE
BRANCH    0                  0                   775637171.8     0                0                       0                      2024-10-04
INTERCO   0                  0                   238561817.87    -21632401.29     49583279                272780                 2026-07-22
STAFF     0                  0                   128347          -77798           4358699                 265405                 2025-10-16
TRADE     11039649.45        6507488.01          80786617.48     -12675574.86     659246898.71            11856063.13            2017-08-04
ZZ_TOTAL  11039649.45        6507488.01          1095113954.14   -34385774.15     713188876.71            12394248.13            2017-08-04
```

### Mart (`JIVO_MART_HANADB`)
```
KIND      N_CUSTOMERS  N_EFF_CUSTOMERS  N_OPEN_INV  N_EFF_INV  RAW_OPEN_INR   UNAPPLIED_CREDIT_INR  EFF_OPEN_INR
BRANCH    5            2                229         116        69057284       24127694              44929590
INTERCO   1            1                35          7          91707409       71027599              20679810
STAFF     3            3                16          3          27504.87       18445                 9059.87
TRADE     54           23               3975        674        1120422158.84  1027068708.94         93353449.91
ZZ_TOTAL  63           29               4255        800        1281214356.71  1122242446.94         158971909.77

KIND      NOTDUE_INR  D1_30_INR    D31_60_INR   D61_90_INR  D91_180_INR  D181_365_INR  D365P_INR    OVERDUE_INR   OD60P_INR
BRANCH    0           823          3777861      359426      16340935     1757570       22692975     44929590      41150906
INTERCO   0           0            20679810     0           0            0             0            20679810      0
STAFF     0           0            9059.87      0           0            0             0            9059.87       0
TRADE     4232896.79  84334195.86  1772095.84   28502       1037926.8    1074442.45    873390.18    89120553.12   3014261.42
ZZ_TOTAL  4232896.79  84335018.86  26238826.71  387928      17378861.8   2832012.45    23566365.18  154739012.99  44165167.42

KIND      MIGRATED_OPEN_INR  BAL_NOT_IN_INV_INR  OCRD_DEBIT_INR  OCRD_CREDIT_INR  UNAPPLIED_RECEIPTS_INR  OPEN_CREDIT_NOTES_INR  OLDEST_OPEN_DUE
BRANCH    0                  73247569.28         118177159.28    -49119876.28     0                       0                      2025-02-08
INTERCO   0                  0                   20679810        0                1500000                 52560                  2026-06-24
STAFF     0                  0                   9059.87         0                0                       0                      2026-07-04
TRADE     0                  1309165.98          94662615.88     -2586526.78      888481117.62            115841909              2025-04-30
ZZ_TOTAL  0                  74556735.26         233528645.03    -51706403.06     889981117.62            115894469              2025-02-08
```

### Beverages (`JIVO_BEVERAGES_HANADB`)
```
KIND      N_CUSTOMERS  N_EFF_CUSTOMERS  N_OPEN_INV  N_EFF_INV  RAW_OPEN_INR  UNAPPLIED_CREDIT_INR  EFF_OPEN_INR
BRANCH    3            3                85          85         7822101       0                     7822101
INTERCO   2            2                50          50         724582        0                     724582
STAFF     11           5                231         48         4939192       3807240               1131952
TRADE     361          192              796         454        49961237.02   11497525.96           38463711.06
ZZ_TOTAL  377          202              1162        637        63447112.02   15304765.96           48142346.06

KIND      NOTDUE_INR  D1_30_INR  D31_60_INR  D61_90_INR  D91_180_INR  D181_365_INR  D365P_INR   OVERDUE_INR  OD60P_INR
BRANCH    0           17078      58244       101062      343041       1412369       5890307     7822101      7746779
INTERCO   0           51902      79804       91085       133762       360478        7551        724582       592876
STAFF     22000       1100242    3140        0           6570         0             0           1109952      6570
TRADE     968411      2440645    3059842     180850.78   972525.79    30068946.55   772489.95   37495300.06  31994813.06
ZZ_TOTAL  990411      3609867    3201030     372997.78   1455898.79   31841793.55   6670347.95  47151935.06  40341038.06

KIND      MIGRATED_OPEN_INR  BAL_NOT_IN_INV_INR  OCRD_DEBIT_INR  OCRD_CREDIT_INR  UNAPPLIED_RECEIPTS_INR  OPEN_CREDIT_NOTES_INR  OLDEST_OPEN_DUE
BRANCH    0                  0                   7822101         0                0                       0                      2024-10-16
INTERCO   0                  96485               821067          0                0                       78486                  2025-01-16
STAFF     0                  0                   1131952         -14654           3380262                 35330                  2026-04-11
TRADE     0                  45378               38509089.06     -3226591.58      11948669.75             508327.05              2024-10-15
ZZ_TOTAL  0                  141863              48284209.06     -3241245.58      15328931.75             622143.05              2024-10-15
```

**Pipeline run, post-fix, all three books, no FAILED line:**
```
  customer-ageing
    summary   oil         5 rows    1.0s
    summary   mart        5 rows    0.8s
    summary   bev         5 rows    0.9s
    detail    oil       641 rows    2.5s
    detail    mart      100 rows    1.6s
    detail    bev       454 rows    2.1s
  wrote site/data.json  (9269.6 KB, 7955 summary rows, 9.0s)   errors: {}
```

---

## Three things an operator should see in those rows (VERIFIED)

1. **Oil's "debtors" are 93 % JIVO's own money.** ₹77.56 Cr of BRANCH plus ₹23.86 Cr of
   INTERCO against ₹7.43 Cr of real external trade. The BRANCH row is also almost entirely
   ancient — **₹59.96 Cr sits in `D365P_INR`** and `OVERDUE_INR` is ₹77.55 Cr of ₹77.56 Cr.
   These are inter-registration GST transfers nobody ever settles, not receivables.
2. **Two customers are two whole books.** Mart TRADE is ₹9.34 Cr, of which
   `CUSTA000048 R K WORLDINFOCOM PVT LTD` alone is **₹8.15 Cr (87 %)** — off ₹85.6 Cr of raw
   open invoices. Bev TRADE is ₹3.85 Cr, of which `CUSTA000175 BLESSING ADVERTISING PVT LTD`
   is **₹3.17 Cr (82 %)** — ₹2.95 Cr of it 181–365 days overdue and ₹21.9 L at 31–60.
   Neither book is a portfolio; each is one counterparty with a tail.
3. **₹71.3 Cr of Oil customer cash is banked and never matched to an invoice**
   (`UNAPPLIED_RECEIPTS_INR`), against a ₹108.9 Cr book — 2,773 receipts sitting fully on
   account. Mart is ₹89.0 Cr. That is the operational cause of the whole correction, and it is
   a reconciliation backlog somebody could actually clear.

---

## Unresolved / stated plainly

1. **Mart's overdue buckets are allocation-dependent by 28×** (§ above). Not fixable with the
   data SAP holds. Documented in the SQL header; treat Mart's "60 d +" as a floor.
2. **`EFF_OPEN_INR` is capped at the ledger debit, so ₹78.6 L of trade debit across the three
   books is carried by no open invoice and is therefore not aged** — Oil ₹65.07 L, Mart ₹13.09 L,
   Bev ₹0.45 L (`BAL_NOT_IN_INV_INR`). It is reported, and the identity
   `EFF_OPEN_INR + BAL_NOT_IN_INV_INR = OCRD_DEBIT_INR` holds on every row, but the hero KPI
   shows `EFF_OPEN_INR` alone and so understates the trade debit book by **3.7 %**. Left as is:
   changing what `EFF_OPEN_INR` means would break the tie to `customer-ageing-detail`. VERIFIED
   as a disclosed understatement, not a hidden one.
3. **`{{ASOF}}` in the past is not a point-in-time A/R.** `OCRD."Balance"` and `PaidToDate` are
   the *current* snapshot — SAP keeps no per-date history — so a back-dated run ages today's open
   items against an older date. `{{ASOF}}` = today is exact. INFERRED from SAP's data model,
   consistent with the header, not separately tested.
4. **Two classification specks, deliberately left** so the summary stays rupee-identical to the
   detail file: `AKAL INFORMATION SYSTEMS LTD` (Oil `CUSTA000242`, group `DEBTORS`, ₹10,000)
   reads TRADE here but INTERCO in `vendor-ageing.sql`; and employee imprest cards filed in a
   state group instead of `STAFF CUSTOMER` read TRADE. I re-counted these myself rather than
   trusting the detail note, and **the detail note undercounts Beverages**: it says 3 cards worth
   ₹1,590, but `CUSTA000902 NAVNEET SINGH ASM GT DL ((JWPL0174))` at ₹9,972 is a fourth — it is a
   `CUSTA` card and its name has no "IMPREST", so a code-or-keyword scan misses it. Measured
   2026-08-21: **Oil 2 cards ₹3,555 · Mart 2 cards ₹1,957 · Bev 4 cards ₹11,562**, ₹17,074 in
   total. That is 0.018 % of Oil's TRADE book, 0.002 % of Mart's, 0.030 % of Bev's — still far
   below anything that moves a decision. **Fix both files together or neither.**
5. **`ZZ_TOTAL` shares the result set with the four KIND rows.** Any consumer that sums the
   column without filtering gets exactly 2× the truth. The current renderer filters correctly;
   this is a standing hazard for the next one.
6. **The 2024-09-30 migration date is hard-coded** and is an Oil fact. Verified as a true zero
   for Mart and Bev today. A fourth company book would need its go-live checked before
   `MIGRATED_OPEN_INR` could be trusted there.
