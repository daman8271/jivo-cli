# open-item-list — adversarial review + fixes

**Section id:** `open-item-list` · **SQL:** `pipeline/sql/open-item-list.sql` (no `-detail` companion)
**Reviewed:** 2026-08-21, against live JIVO_OIL_HANADB / JIVO_MART_HANADB / JIVO_BEVERAGES_HANADB
**Verdict:** **FIXED** — two real defects found and corrected, plus four wrong figures in the
header comment. Everything else on the attack list was tested and survived.

Every claim below is tagged **VERIFIED** (a query was run and its output is reproduced or
summarised here) or **INFERRED** (reasoned, not proven).

---

## 1. What the section is, and what it reads

One row per **open SAP document**, on both sides of the ledger, unioned across six tables with a
`DOCTYPE` discriminator and a debit/credit `SGN` so the list nets. It is the document-level
drill-down that sits behind `customer-ageing` and `vendor-ageing`.

| Table | DOCTYPE | Open test | SGN | Why this table |
|---|---|---|---|---|
| `OINV` | `AR_INV` | `DocStatus='O'` and `DocTotal-PaidToDate > 0` | +1 debit | customer owes JIVO |
| `ORIN` | `AR_CN`  | same | −1 credit | A/R credit note, JIVO owes it back |
| `ORCT` | `AR_RCT` | `OpenBal > 0` | −1 credit | money received, never applied to a bill |
| `OPCH` | `AP_INV` | `DocStatus='O'` and `DocTotal-PaidToDate > 0` | −1 credit | JIVO owes the vendor |
| `ORPC` | `AP_CN`  | same | +1 debit | A/P credit note |
| `OVPM` | `AP_PMT` | `OpenBal > 0` | +1 debit | money paid out, never applied |

Supporting reads:

| Table | Columns | Why |
|---|---|---|
| `OCRD` | `CardCode`, `CardName`, `CardType`, `Balance`, `GroupCode` | `Balance` is the ledger ground truth (positive = DEBIT, party owes JIVO). Drives `CARD_BALANCE`, `CARD_STALE_GAP`, `CARD_REAL_PCT`, `CO_OCRD_NET`. |
| `OCRG` | `GroupCode`, `GroupType`, `GroupName` | BP group name → `BP_GROUP` and the BRANCH / STAFF legs of `ACCT_KIND`. Joined on **`GroupCode` + `GroupType`=`CardType`** — the group-code space is separate for customers and vendors, so joining on code alone would cross-wire them. |
| `ITR1` + `OITR` | `SrcObjTyp`, `SrcObjAbs`, `ReconSum`, **`IsCredit`**, `ReconNum`, `Canceled`, `ReconDate` | SAP's own internal reconciliation, exposed **as a diagnostic only** (`OITR_RECON_AMT`, `OITR_LINES`, `RECON_STATE`). |

Money-unit contract: **every money column is plain INR rupees.** No `_L`, no `_CR` suffix
anywhere in the 51-column output — checked column by column against the renderer's
`scale()` (`/_CR$/i`→1e7, `/_L$/i`→1e5). Nothing in this section matches either pattern, so
nothing is scaled and nothing can render 100,000× wrong. **VERIFIED.**

---

## 2. Defects found and fixed

### D1 — payment rows landed on the wrong ledger SIDE (MAJOR, fixed)

`SIDE` was hard-coded per table: everything out of `ORCT` was `'AR'`, everything out of `OVPM`
was `'AP'`. But a payment's side is its **`DocType`**, not its table:

```
ORCT/OVPM open rows by DocType (Canceled='N', OpenBal>0, DocDate<=2026-08-21)   VERIFIED
                       Oil                    Mart                 Bev
ORCT DocType='C'  2,905  Rs  71.32 Cr    1,580  Rs 89.00 Cr   331  Rs 1.53 Cr
ORCT DocType='S'    146  Rs   2.25 Cr        6  Rs  0.03 Cr    18  Rs 0.0005 Cr   <-- vendor refunds
OVPM DocType='C'     26  Rs   0.26 Cr        -            -     2  Rs 0.007 Cr    <-- customer refunds
OVPM DocType='S'    801  Rs 2,017.11 Cr    466  Rs 185.56 Cr   96  Rs 2.74 Cr
```

So 146 Oil rows of cash **received back from a vendor** were filed as customer receipts, and 26
rows of cash **refunded to a customer** were filed as vendor payments. Anyone filtering the
drill-down by `SIDE='AR'` got vendor refunds mixed into their receivables list.

Row-level proof, before the fix: 13 shown Oil rows (Rs 2.40 Cr) and 1 Bev row had `SIDE='AR'`
with `OCRD.CardType='S'`, or vice versa — e.g. `AR_RCT` DocEntry 6855, **AL GHURAIR RESOURCES
OILS**, a vendor, Rs 26.12 L. **VERIFIED.**

**Fix:** `SIDE` now comes from the payment's own `"DocType"` (`'C'`→AR, `'S'`→AP). After the fix
the SIDE-vs-`CardType` mismatch count is **0 in all three books. VERIFIED.**

`DOCTYPE` deliberately did **not** change — it names the *document* (which table, which money
direction), and the renderer's label map keys on it. The header now states the two axes
explicitly so nobody re-conflates them. **`SGN` was already right on all six types** (money in
from a vendor really is a credit to that vendor), so no total moved.

### D2 — `OITR_RECON_AMT` summed a signed column, producing impossible values (MAJOR, fixed)

`ITR1."IsCredit"` takes `'D'` and `'C'`, and **the same document can appear on both sides** —
104 documents in Oil's open set, 57 Mart, 16 Bev. **VERIFIED.** The CTE did
`SUM(CAST("ReconSum" AS DOUBLE))` across both sides, double-counting one settlement.

Worked example, pulled live — **OPCH DocEntry 42554**, `VENDA001203` GRAINCORP, DocTotal
Rs 5.93 Cr:

```
ReconNum LineSeq IsCredit ReconSum      Account  ReconType IsSystem IsCard
40148    1       D        59,283,335.10 2140001  13        Y        A     <- system, account level
41914    4       C        59,283,335.10 2110002  0         N        C     <- manual, BP level
```

One settlement, written twice, on opposite sides. Naive sum = Rs 11.86 Cr — **twice the
document itself**.

Damage across the open set, **VERIFIED**:

| | Oil | Mart | Bev |
|---|---|---|---|
| open docs with an ITR1 row | 3,903 | 2,695 | 484 |
| **`RECON_AMT > DocTotal` (arithmetically impossible)** — before | **128** (Rs 18.24 Cr excess) | **47** (Rs 8.50 Cr) | **15** (Rs 0.80 Cr) |
| after fix | **87** (Rs 0.95 Cr) | **14** | **1** |
| `RECON_STATE='FULL_PER_OITR'` — before | 468 | 93 | 88 |
| after fix | 436 | 60 | 76 |

In the **shown** rows the false-`FULL_PER_OITR` count went 93→81 (Oil), 17→6 (Mart), 3→0 (Bev).
That flag is the section's headline stale-open signal ("SAP's own reconciliation says settled
while the document still reads open"), so firing it on documents SAP has *not* fully reconciled
was the worst kind of wrong — a confident false positive.

**Fix:** `RECON_AMT = GREATEST(SUM(D-side), SUM(C-side))` — one settlement, counted once,
whichever way SAP booked it. Chosen over three alternatives that were all measured first:

| rule | impossible rows (Oil) | negative results | verdict |
|---|---|---|---|
| naive `SUM` (was) | 128 | 0 | wrong |
| own-side minus opposite-side | 0 | **1,232** | over-corrects, nonsense output |
| own-side only | 1 | 0 | needs a per-objtype side map that the data contradicts |
| **`GREATEST(D, C)`** | **87** | **0** | shipped |

**Residual, and it is SAP's data, not the query — VERIFIED, NOT fixed.** The 87 survivors are
**account-level** system reconciliations that stamp the reconciliation's whole total onto each
participant line. Oil `OPCH` DocEntry 15558 (`VENDA000003`, Rs 15.73 L) carries **one** ITR1
line of Rs 23.51 L, from ReconNum 13511 — a system recon on account 1102007 clearing a GRPO
(`SrcObjTyp` 20, DocEntry 6450) worth Rs 23.51 L against it. The invoice really was reconciled,
so `FULL_PER_OITR` still reads true; only the *amount* is the reconciliation's, not the
document's. This is exactly why `OITR_RECON_AMT` is documented as a diagnostic and never a
settlement figure.

### D3 — four wrong figures in the header comment (MINOR, fixed)

The header is the operating manual for this query, so a wrong number in it is a defect.
All corrected against live output:

| claim | was | is (VERIFIED 2026-08-21) |
|---|---|---|
| Mart uncapped open value | Rs 1,027 Cr | **Rs 649.43 Cr** |
| Bev uncapped open value | Rs 154 Cr | **Rs 14.27 Cr** |
| row cap | "ROW CAP = 1200" | `SIZE_RANK<=1500 OR DT_SIZE_RANK<=400` → 2,162 / 2,191 / 1,090 |
| Oil migrated OVPM rows | 71 | **77**, Rs 1,874.81 Cr |
| Oil OCRD credit vs open A/P | Rs 106.1 Cr | **Rs 93.65 Cr** (2,231 `CardType='S'` cards), 3.3× not 3× |
| COLUMN LIST | 47 names | **51** — was missing `DT_SIZE_RANK`, `DT_ITEMS_SHOWN`, `DT_OPEN_SHOWN` |

### D4 — dead code (MINOR, removed)

`co` computed `CO_ITEMS_MATERIAL` / `CO_OPEN_MATERIAL`; neither was ever selected. Removed.

### D5 — `CARD_REAL_PCT` rounded to a misleading `0.00` (MINOR, fixed)

Oil's AL GHURAIR card carries Rs 1,741.69 Cr of open items against a Rs 2.35 L ledger balance —
0.0014% real. Rounded to 2 dp that printed `0.00` beside a non-zero `ITEM_REAL_EST`, which reads
as a bug. Now `ROUND(...,4)`. `ITEM_REAL_EST` is still computed from the *unrounded* percentage,
so it will not re-derive exactly from the printed figure — noted in the header; trust
`ITEM_REAL_EST`.

### D6 — `APPLIED` rendered as a bare integer (MINOR, fixed in `site/index.html`)

`isMoneyCol()` matches `DOC_TOTAL` (via `total$`) and `OPEN_AMT` (via `_amt$`) but **not** the
bare word `APPLIED`, so a money column printed as `18,00,000` with no ₹ next to `₹1.20 Cr` and
read as a document count. Fixed with a `cell:` formatter scoped to this section's renderer only
— **no SQL column was renamed**, so the contract is untouched.

Also in the same renderer: the doctype bar chart summed the *shown* rows while the KPI above it
showed the *uncapped* total (Oil Rs 2,516 Cr of bars under a Rs 2,582 Cr headline). The bars now
read `DT_OPEN_ALL`, the uncapped per-doctype total that rides on every row, with the old sum
kept as a fallback.

---

## 3. What was attacked and survived

**1. Double counting — SURVIVED. VERIFIED.**
Six independent single-table aggregates were written from scratch and compared to the query's
own `DT_ITEMS_ALL` / `DT_OPEN_ALL`. **Every count and every rupee matched exactly, in all three
books.** No join fans (the `oitr` CTE is grouped, `OITR.ReconNum` has zero duplicates in any
book, `OCRD.CardCode` and the `card`/`dt`/`co` CTEs are all one row per key). Zero duplicate
`(DOCTYPE, DOC_ENTRY)` pairs in the output. The six tables cannot overlap.

The netting identity was re-derived by hand from the independent aggregates:

```
Oil : 1,806,911,987.07 − 12,394,248.13 − 735,732,412.11 − 3,091,996,881.73
      + 3,412,961.00 + 20,173,708,514.13 = 18,143,909,920.23  = CO_OPEN_NET  exact
Mart: ... = 89,925,395.93   exact
Bev : ... = 39,577,074.29   exact
```

**Consumer hazard, documented not fixed:** `CARD_*`, `DT_*` and `CO_*` are per-card /
per-doctype / per-company totals **repeated on every row they describe**. Summing them down the
table multiplies by the row count. Only `DOC_TOTAL`, `APPLIED`, `OPEN_AMT`, `SIGNED_OPEN`,
`OPEN_AMT_FC`, `ITEM_REAL_EST`, `OITR_RECON_AMT` are per-row. The renderer reads `CO_*` off
`summary[0]`, which is correct. A warning block was added to the header.

**2. Cancelled documents — SURVIVED. VERIFIED.**
`"CANCELED"='N'` on OINV/ORIN/OPCH/ORPC (one `l`, three values) and `"Canceled"='N'` on
ORCT/OVPM (mixed case, two values) — applied on **every** table, and on `OITR` too. Full value
distribution pulled for all three books: every `'Y'` (was-cancelled) and `'C'` (is-the-cancelling
doc) row is `DocStatus='C'` with **zero** open amount, and every cancelled ORCT/OVPM has
`OpenBal=0`. The filter is correct and also belt-and-braces — nothing would leak without it.

**3. Branch + intercompany — SURVIVED, quantified. VERIFIED.**
Flagged, never dropped: `ACCT_KIND` ∈ BRANCH / INTERCO / STAFF / TRADE, plus `IS_GROUP`.
All 23 known group `CardCode`s that appear in the output carry `IS_GROUP=1`. The **name** test
does the work a group test cannot: Oil's `VENDA000483` "JIVO MART PVT LTD" sits in group
E-COMMERCE and `VENDA001084` "JIVO WELLNESS(AKAL INFOSYS)" in PURCHASE — both caught. Scanned
every `OCRD` row in all three books whose name contains JIVO / JWPL / WELLNESS / AKAL / BEVERAG /
`A U O`, or whose group mentions BRANCH or COMPANY: **no group entity is misfiled as TRADE.**
The TRADE hits are genuine outside parties (SR BEVERAGES, AGGARWAL BEVERAGES, ZENITHZEPHYR
WELLNESS…).

Share of the shown list, **VERIFIED**:

| book | TRADE | BRANCH | INTERCO | STAFF |
|---|---|---|---|---|
| Oil | 1,185 / Rs 2,346.47 Cr | 724 / Rs 128.18 Cr | 190 / Rs 40.96 Cr | 63 / Rs 0.52 Cr |
| Mart | 1,060 / Rs 167.11 Cr | 25 / Rs 5.77 Cr | **1,093 / Rs 357.01 Cr** | 13 / Rs 0.18 Cr |
| Bev | 744 / Rs 11.51 Cr | 124 / Rs 1.55 Cr | 18 / Rs 0.07 Cr | 204 / Rs 0.86 Cr |

**Mart's list is 67% intercompany by value** — read Mart's headline with that in front of you.

Known limit, measured and deliberately left alone: `STAFF` is a group-name test only, so employee
imprest cards filed under a geography group (`ORGC000031` "ARVINDER SINGH IMPREST JWPL0115",
group DELHI) come out TRADE. Cost: **11 items / Rs 1.27 L (Oil), 2 / Rs 1,957 (Mart), 6 /
Rs 11,562 (Bev)**. Immaterial against Rs 2,582 Cr, and widening the test risks catching a real
trading party. Also: the `'%A U O JWPL%'` pattern never fires — the live spelling is `A U/O`
(`VENDA000687` "AKAL ROZGAR YOJANA A U/O JWPL BS") — but those cards are caught by the group and
`%AKAL ROZGAR%` tests anyway, so **zero** rows are affected. Left as-is.

**4. Unapplied money — SURVIVED. VERIFIED.**
This section does **not** subtract `OpenBal` from `OCRD."Balance"` anywhere, so it cannot
double-subtract. Unapplied receipts/payments are reported as their own rows (`AR_RCT`/`AP_PMT`)
with `OPEN_AMT = OpenBal`, which is by definition the portion *not* already inside any invoice's
`PaidToDate` — so no double count between the payment row and the invoice row. `CARD_STALE_GAP`
and `CO_STALE_GAP` are presented as diagnostics against `OCRD.Balance`, never netted into it.
Open `ORIN`/`ORPC` are carried as first-class rows with the correct sign, not ignored.

**5. Migrated openings at 2024-09-30 — SURVIVED, and the date is right for all three books.
VERIFIED.**
`IS_MIGRATED` hard-codes Oil's go-live. Checked whether that silently misses Mart's and Bev's:

```
first DocDate per table          OINV        OPCH        ORCT        OVPM        ORIN        ORPC
Oil                              2024-09-30 (11,078 / 949 / 2,293 / 425 / 1,266 / 12 rows on the day)
Mart                             2024-10-03  2025-01-01  2025-01-01  2025-01-01  2025-01-13  2025-01-21
Bev                              2024-10-04  2024-10-01  2024-09-30(1 row)  2024-10-15  2024-10-09  2024-10-01
```

Mart's whole 2025-01-01 opening day leaves **Rs 1,800** of open A/P and **Rs 1.69 L** of open
payments; Bev's first days leave nothing open at all. So `CO_MIGRATED_OPEN = 0` for Mart and Bev
is the truth, not a missed date. Oil's Rs 1,982.49 Cr was **re-derived independently** table by
table and matched to the paisa (see §4). Migrated rows keep their true original `DocDueDate`, so
they age correctly rather than all piling into one bucket — Oil's shown list has 211 migrated
rows spread across buckets, not one lump.

**6. Three-schema portability — SURVIVED. VERIFIED.**
Run end to end against all three schemas, both standalone and through `build_data.py`. No UDF is
referenced anywhere (no `U_*` column), no hard-coded account code, no hard-coded `CardCode`, no
group **code** — only group *names* and BP *names*, all of which exist in all three books. Every
column referenced exists in all three (`ITR1."IsCredit"` and `OVPM."DocType"`, the two columns
the fixes lean on, confirmed present and populated in each). Identical 51-column header in all
three outputs.

**7. Empty and NULL — SURVIVED. VERIFIED.**
Forced the empty case with `--as-of 2020-01-01` (before any book exists): all three schemas
returned **header only, 0 rows, exit 0, ~1s** — no error, no divide-by-zero, no NULL blow-up.
`parse_tsv` yields `[]`, and the renderer's `if (!summary.length)` draws the empty state. The
guard only complains when *all* companies are empty, so one empty book is safe.
`DocDueDate` is NULL on **zero** rows in all six tables in all three books, so `DAYS_BETWEEN`
never returns NULL and no row can fall through the `AGE_BUCKET` `CASE` into a wrong bucket —
`AGE_BUCKET` was re-derived in Python for every output row and matched 100%.

**8. Money units — SURVIVED. VERIFIED.**
All 51 column names checked against the renderer's `scale()`. None ends in `_L` or `_CR`.
Every money value is rupees, as the header promises. `money()` formats to L/Cr at display time.

**9. Headline re-derived by a second route — AGREES. VERIFIED.**
The dashboard's headline for Oil is *"23,230 documents SAP has not closed, face value
Rs 2,582.42 Cr."*
Route 2 was a per-table `GROUP BY "CANCELED", "DocStatus"` scan — a different shape of query with
different predicates:

```
OINV N/O 13,008 rows  Rs 1,806,911,987.07   (query: 13,007 — the 1 extra has zero remaining)
OPCH N/O  4,343       Rs 3,091,996,881.73
ORIN N/O  1,683       Rs    12,394,248.13
ORPC N/O    319       Rs     3,412,961.00
ORCT N     —          Rs   735,732,411.20   (query: 735,732,412.11; delta −0.91 = 2 negative-OpenBal rows)
OVPM N     —          Rs 20,173,708,514.13
```

Both routes agree **to the rupee** apart from Rs 1,025.91 of negative `OpenBal` across all three
books (see §5). The Rs 1,982.49 Cr migration figure was re-derived the same way:
265,062,153.03 + 2,139,127.26 + 238,739,009.21 + 570,328,846.14 + 474,044.00 + 18,748,132,768.43
= **19,824,875,948.07** vs `CO_MIGRATED_OPEN` 19,824,875,948.08 — one paisa of rounding.

**10. Performance — FINE. VERIFIED.** Oil 5.2–6.8 s, Mart 5.4–6.6 s, Bev 3.2–3.7 s. Whole
section through the pipeline in **15.6 s**. Ceiling is 60 s/company; the `SQL_TIMEOUT` is 300 s.

---

## 4. Live numbers, all three books (as-of 2026-08-21, after the fixes)

```
##### OIL  (shown 2,162 of 23,230)
  CO_OPEN_ALL          25,824,157,004.17   Rs 2,582.42 Cr
  CO_OPEN_SHOWN        25,161,288,080.75   Rs 2,516.13 Cr
  CO_OPEN_NET          18,143,909,920.23   Rs 1,814.39 Cr
  CO_OCRD_NET             124,205,801.98   Rs    12.42 Cr    <-- what the ledgers actually net to
  CO_STALE_GAP         18,019,704,118.26   Rs 1,801.97 Cr
  CO_MIGRATED_OPEN     19,824,875,948.08   Rs 1,982.49 Cr    <-- 77% of the face value

  DOCTYPE   items_all  open_all(Cr)   shown  shown(Cr)
  AP_CN           319          0.34      21       0.32
  AP_INV        4,343        309.20     535     287.03
  AP_PMT          827      2,017.37     400   2,016.95
  AR_CN         1,683          1.24     147       0.97
  AR_INV       13,007        180.69     659     142.35
  AR_RCT        3,051         73.57     400      68.50
  RECON_STATE: NONE 1,546 | PARTIAL 535 | FULL_PER_OITR 81
  SIDE: AR 1,201 | AP 961        IS_MIGRATED=1: 211
  AGE_BUCKET: 0_NOTDUE 27 | 1-30 279 | 31-60 102 | 61-90 94 | 91-180 210 | 181-365 358 | 365+ 1,092

##### MART  (shown 2,191 of 10,017)
  CO_OPEN_ALL           6,494,257,931.67   Rs   649.43 Cr
  CO_OPEN_SHOWN         5,300,681,704.98   Rs   530.07 Cr
  CO_OPEN_NET              89,925,395.93   Rs     8.99 Cr
  CO_OCRD_NET            -102,946,891.25   Rs   -10.29 Cr   (negative = JIVO Mart owes, net)
  CO_STALE_GAP            192,872,287.18   Rs    19.29 Cr
  CO_MIGRATED_OPEN                     0   Rs     0.00 Cr

  DOCTYPE   items_all  open_all(Cr)   shown  shown(Cr)
  AP_CN           368         15.52     201      15.48
  AP_INV        2,879        219.60     605     155.54
  AP_PMT          466        185.56     400     185.49
  AR_CN           463         11.59     185      11.51
  AR_INV        4,255        128.12     400      82.94
  AR_RCT        1,586         89.03     400      79.11
  RECON_STATE: NONE 1,544 | PARTIAL 641 | FULL_PER_OITR 6
  SIDE: AP 1,206 | AR 985        IS_MIGRATED=1: 0
  AGE_BUCKET: 0_NOTDUE 19 | 1-30 394 | 31-60 207 | 61-90 149 | 91-180 426 | 181-365 648 | 365+ 348

##### BEV  (shown 1,090 of 2,206)
  CO_OPEN_ALL             142,657,109.30   Rs    14.27 Cr
  CO_OPEN_SHOWN           139,911,692.71   Rs    13.99 Cr
  CO_OPEN_NET              39,577,074.29   Rs     3.96 Cr
  CO_OCRD_NET              38,257,365.85   Rs     3.83 Cr    <-- the only book where the two nearly agree
  CO_STALE_GAP              1,319,708.43   Rs     0.13 Cr
  CO_MIGRATED_OPEN                     0   Rs     0.00 Cr

  DOCTYPE   items_all  open_all(Cr)   shown  shown(Cr)
  AP_CN             2          0.02       2       0.02
  AP_INV          550          3.56     184       3.44
  AP_PMT           98          2.75      71       2.74
  AR_CN            45          0.06      12       0.05
  AR_INV        1,162          6.34     679       6.23
  AR_RCT          349          1.53     142       1.50
  RECON_STATE: NONE 946 | PARTIAL 144 | FULL_PER_OITR 0
  SIDE: AR 834 | AP 256          IS_MIGRATED=1: 0
  AGE_BUCKET: 0_NOTDUE 41 | 1-30 198 | 31-60 185 | 61-90 158 | 91-180 178 | 181-365 117 | 365+ 213
```

Pipeline run, **VERIFIED**:

```
$ python3 build_data.py --only open-item-list --no-guard
connection: home bridge (127.0.0.1:13015 -> VPS -> hanadb)
as-of 2026-08-21 — 1 section(s): open-item-list
  open-item-list
    summary   oil      2162 rows    5.8s
    summary   mart     2191 rows    5.8s
    summary   bev      1090 rows    3.7s
wrote .../site/data.json  (10219.0 KB, 15.6s)
```

No `FAILED` line, `errors: {}` for all three companies, 51 columns each.

---

## 5. The one thing to say out loud about this section

**Rs 2,582 Cr of "open" Oil items sit against Rs 12.42 Cr of actual ledger balance.** That is not
a rounding problem, it is the section's whole point, and it comes from two causes that are now
both measured:

1. **Rs 1,982.49 Cr (77%) is migration openings** dated 2024-09-30 — 77 unapplied vendor payments
   alone carry Rs 1,874.81 Cr, seven of them to AL GHURAIR (USD ~41 M each) on a card whose
   balance today is **Rs 2.35 L**. `IS_MIGRATED` and `CO_MIGRATED_OPEN` flag them; nothing is
   hidden.
2. **The rest is `DocStatus='O'` being unreliable at JIVO** — documents settled by manual journal
   entry or by an on-account payment that was never internally reconciled. Independently
   re-confirmed for this section's tables: `JDT1."IntrnMatch" <> 0` returns **0 rows** and
   `JDT1."Closed"='Y'` returns **0 rows** in **all three** books (Oil 526,820 / Mart 344,144 /
   Bev 86,414 JDT1 rows). SAP's journal-level match state is simply not maintained here.

**Read this list as "documents SAP has not closed", never as money outstanding.** The receivable
and payable numbers come from `customer-ageing` / `vendor-ageing`, which are anchored on
`OCRD."Balance"`. The renderer already leads with that caveat.

---

## 6. Still unresolved — stated plainly

1. **`--as-of` is only half as-of.** `{{ASOF}}` filters `DocDate`, but `PaidToDate`, `OpenBal`
   and `OCRD."Balance"` are **live** values with no history in these tables. Back-dating the run
   gives *"documents that existed on that date, with today's settlement state"* — **not** the
   open position as it stood that day. Rebuilding a true historical position needs JDT1 replayed
   by `RefDate` and is out of scope. For the daily refresh (`ASOF` = today) it is exact.
   **INFERRED from the schema; not separately measured.**

2. **87 Oil / 14 Mart / 1 Bev documents still show `OITR_RECON_AMT` above their own
   `DocTotal`.** Root-caused (§2 D2) to SAP's account-level system reconciliations, with a worked
   example. Not corrected, because correcting it would mean inventing a document-level split SAP
   never recorded. `OITR_RECON_AMT` is a diagnostic; it is never used to compute `OPEN_AMT`.
   **VERIFIED as SAP's data, not the query's arithmetic.**

3. **Rotten exchange rates in SAP.** Oil `OVPM` DocEntry 26317 (DocNum 726466747, AL GHURAIR)
   was keyed with `DocRate = 0.0001`, so **USD 44.34 L is booked as Rs 443.40** — ~87,000×
   too small. `OPEN_AMT` reports the local figure SAP holds, so rows like this sink below the
   Rs 10,000 materiality floor and vanish from the list. This is a **data-entry defect in SAP
   that Accounts should fix at source**; it is deliberately not patched here. `OPEN_AMT_FC` +
   `CURRENCY` expose it. **VERIFIED — one row found; no systematic sweep for others was run.**

4. **Negative `OpenBal` rows are dropped** by the `> 0` filter: Oil 2 rows (−Rs 0.91), Mart 1
   (−Rs 25) + 1 (−Rs 1,000), Bev none. Total effect across all three books **Rs 1,025.91** —
   left alone as immaterial. **VERIFIED.**

5. **STAFF classification is group-name-only**, so a handful of employee imprest cards read as
   TRADE. Cost measured at 11 / 2 / 6 items and Rs 1.27 L / Rs 1,957 / Rs 11,562. Left alone
   deliberately. **VERIFIED.**

6. **Latent, not currently a problem: TSV-hostile characters.** A tab or newline inside
   `CardName`, `NumAtCard` or `BPLName` would make `parse_tsv` drop that row. Checked today —
   **zero** such characters in any of those fields in any of the three books, and `build_data.py`
   *reports* dropped rows rather than swallowing them, so it would be visible. No defensive
   `REPLACE` was added, to avoid churn. **VERIFIED clean as of 2026-08-21; re-check if the row
   count ever drops without the SQL changing.**

7. **`ITEM_REAL_EST` cannot be re-derived from the printed `CARD_REAL_PCT`** (it uses the
   unrounded percentage). 719 Oil / 920 Mart / 356 Bev rows differ by more than 5 paise.
   Documented in the header; `ITEM_REAL_EST` is the one to trust. **VERIFIED.**
