# vendor-ageing — adversarial review note

**Reviewed 2026-08-21 · as-of 2026-08-21 · verdict: FIXED**
(2 defects found and corrected; the core credit-adjustment method survived every attack.)

Every claim below is tagged **VERIFIED** (I ran the query and read the result) or
**INFERRED** (I reasoned it and did not prove it live).

---

## 1. What the query uses, and why

| Table | Columns | Why |
|---|---|---|
| `OPCH` | `CardCode`, `DocEntry`, `DocDate`, `DocDueDate`, `DocTotal`, `PaidToDate`, `DocStatus`, `CANCELED` | The A/P bills to be aged. `DocTotal - PaidToDate` is the open amount; ageing is on `DocDueDate`, not `DocDate`. |
| `JDT1` | `ShortName`, `Debit`, `Credit`, `RefDate` | The **ledger position** — what JIVO actually owes. `ShortName` holds the `CardCode` for a BP posting. |
| `OCRD` | `CardCode`, `CardName`, `CardType`, `GroupCode` | Vendor master; `CardType='S'` is the scope. |
| `OCRG` | `GroupCode`, `GroupType`, `GroupName` | Branch detection (`GroupName LIKE '%BRANCH%'`). Joined on **both** `GroupCode` and `GroupType` because customer and vendor groups share the code space. |
| `OVPM` | `CardCode`, `DocType`, `Canceled`, `OpenBal` | Unapplied vendor payments — **diagnostic only**. |
| `ORPC` | `CardCode`, `DocStatus`, `CANCELED`, `DocTotal`, `PaidToDate` | Open A/P credit notes — **diagnostic only**. |

**The method.** A naive `OPCH` ageing overstates JIVO's payables by ~3x
(Oil: ₹309.20 Cr of "open" bills against a ₹102.63 Cr real payable — **VERIFIED**),
because bills get settled by manual journal entries and by on-account payments that
are never internally reconciled, so `DocStatus` stays `'O'` long after the money moved.
So per vendor:

```
PAYABLE = GREATEST(0, -ledger balance)
CREDIT  = GREATEST(0, SUM(open bills) - PAYABLE)
```

`CREDIT` is consumed **oldest-due-bill-first** via a running window sum, and only the
remainder is aged. The identity `SUM(buckets) + UNBACKED_CREDIT = PAYABLE` is
structural — it holds by construction in both branches of the `GREATEST`, and holds
on **every row of all three books** with zero violations (**VERIFIED**).

---

## 2. Defects found and fixed

### D1 — `--as-of` re-bucketed but never moved the position (MAJOR, fixed)

`build_data.py` documents `--as-of 2026-07-31 # a month-end position`. The old query
read the position from `OCRD."Balance"`, which is a running *right-now* figure, while
ageing the buckets against `{{ASOF}}`. The result was a hybrid true on neither date —
and it read as good news rather than as an error. **VERIFIED** with the old SQL:

| as-of | CO_RAW_OPEN | CO_PAYABLE | CO_ADJ_OVERDUE_60PLUS_TRADE |
|---|---|---|---|
| 2026-08-21 | 309.20 Cr | 102.63 Cr | 20.04 Cr |
| 2026-06-30 | 309.20 Cr *(frozen)* | 102.63 Cr *(frozen)* | 15.42 Cr |
| 2025-12-31 | 309.20 Cr *(frozen)* | 102.63 Cr *(frozen)* | 8.77 Cr |

A reader would conclude the 60+ payable had fallen from ₹20 Cr to ₹8.8 Cr. Nothing had
fallen; only the clock moved under a frozen balance.

**Fix.** A `bal` CTE derives the position from the general ledger
(`SUM(JDT1."Debit" - "Credit")` per `ShortName`, `"RefDate" <= {{ASOF}}`), and `bill`
gained `AND p."DocDate" <= DATE'{{ASOF}}'`.

Safe because JDT1 reproduces `OCRD."Balance"` **exactly** — 5,174 vendor cards across
all three books, `SUM(ABS(diff)) = 0`, `0` mismatches at ₹1 tolerance (**VERIFIED**).
No book has a future-dated `OPCH`, and Beverages' only 10 future-dated `JDT1` rows sit
on G/L accounts `5650016`/`1109005`, not on vendor cards (**VERIFIED**), so at
as-of=today the change is a provable no-op.

After the fix (**VERIFIED**, and each payable cross-checked against a standalone JDT1
aggregation that returned the identical figure):

| as-of | CO_RAW_OPEN | CO_PAYABLE | CO_UNBACKED_CREDIT | CO_ADJ_OVERDUE_60PLUS_TRADE |
|---|---|---|---|---|
| 2026-08-21 | 309.20 Cr | 102.63 Cr | 0.48 Cr | 20.04 Cr |
| 2026-06-30 | 276.10 Cr | 106.56 Cr | 6.51 Cr | 16.48 Cr |
| 2025-12-31 | 206.40 Cr | 110.67 Cr | 23.83 Cr | 12.88 Cr |

**Known limit, stated plainly.** `OPCH."PaidToDate"` is itself a *right-now* field and
cannot be rewound without the reconciliation history. So on a past as-of the **total is
now correct but the bill side is still today's**, and the part that no visible bill can
explain lands in `UNBACKED_CREDIT` (0.48 → 6.51 → 23.83 Cr above). The identity keeps
it visible instead of losing it. **Read `UNBACKED_CREDIT` before trusting the bucket
split on any as-of that is not today.** The daily refresh (as-of = today) is unaffected.

### D2 — 30 sub-paise dust rows reported as vendors JIVO owes (MINOR, fixed)

The scope test is `v.BAL <> 0`. Thirty cards carry a balance of **−₹0.0001** (TDS
rounding dust) and were being published as vendors with a payable — Oil 29, Mart 1,
e.g. `VENDA000177 PASCO AUTOMOBILES` at `-0.000100`, JDT1 agreeing to 6 dp
(**VERIFIED**). Rounding the ledger balance to paise in the `bal` CTE drops them.

`ROUND(...,2)` is load-bearing for a second reason: `SUM()` over `DOUBLE` leaves a
~1e-9 residue on cards whose postings net to exactly zero, which would have *admitted*
15 more all-zero rows (**VERIFIED** — I saw all 15 before adding the rounding).

Row counts moved **676/87/164 → 647/86/164**. Set-compared old vs new (**VERIFIED**):
`0 rows added, 30 removed, and every surviving row byte-identical` — the only value
change anywhere is ≤ ₹0.01 on the `CO_*` totals, from no longer accumulating dust.

### The executable diff is 4 lines

```
+    AND p."DocDate"  <= DATE'{{ASOF}}'
+bal AS (SELECT "ShortName" AS CC,
+        ROUND(SUM(CAST("Debit" AS DOUBLE) - CAST("Credit" AS DOUBLE)), 2) AS BAL
+        FROM {{SCHEMA}}.JDT1 WHERE "RefDate" <= DATE'{{ASOF}}' GROUP BY "ShortName"),
-         CAST(c."Balance" AS DOUBLE)         AS BAL,
+         IFNULL(b.BAL, 0)                    AS BAL,
+  LEFT JOIN bal b ON b.CC = c."CardCode"
```

No column was added, removed, renamed or rescaled. The contract is untouched.

---

## 3. Live numbers — all three companies, as-of 2026-08-21

Straight from `pipeline/raw/vendor-ageing.*.tsv` after the fix. All figures INR crores.

```
        rows  trade  excl |     RAW_OPEN      PAYABLE     ADJ_OPEN   UNBACKED |  TRADE_ADJ  TRADE_60+ |      BR/IC
oil      647    638     9 |      309.20C      102.63C      102.15C      0.48C |     22.32C     20.04C |     79.83C
mart      86     80     6 |      219.60C       29.22C       29.18C      0.03C |      1.59C      0.46C |     27.60C
bev      164    161     3 |        3.56C        2.24C        2.21C      0.03C |      1.42C      0.47C |      0.79C

OIL  trade buckets (Cr): NOTDUE=0.53 1_30=0.71 31_60=1.03 61_90=3.80 91_180=0.96 181_365=8.95 365PLUS=6.32
MART trade buckets (Cr): NOTDUE=0.16 1_30=0.63 31_60=0.34 61_90=0.08 91_180=0.28 181_365=0.01 365PLUS=0.10
BEV  trade buckets (Cr): NOTDUE=0.21 1_30=0.26 31_60=0.49 61_90=0.30 91_180=0.08 181_365=0.04 365PLUS=0.06
```

**The headline the dashboard shows** (hero KPI "JIVO owes vendors" / "Overdue to pay"):
**Oil ₹22.32 Cr, of which ₹20.04 Cr is 61 days or more overdue · Mart ₹1.59 Cr / ₹0.46 Cr
· Beverages ₹1.42 Cr / ₹0.47 Cr** — external trade only.

Pipeline run, all three companies, no FAILED line (**VERIFIED**):

```
  vendor-ageing
    summary   oil       647 rows    2.0s
    summary   mart       86 rows    1.0s
    summary   bev       164 rows    1.6s
```

---

## 4. What I attacked, and what survived

### Survived — no defect found

**Double counting.** No fan-out anywhere. `OCRD` `CardType='S'` count equals the count
after the `OCRG` join in all three books (2231/1248/1695), and `OCRG` has zero duplicate
`(GroupCode, GroupType)` pairs (**VERIFIED**). `tot`/`vpm`/`cn`/`agg` are all
`GROUP BY CardCode`, one row per vendor. No duplicate `CARD_CODE` in any output
(**VERIFIED**). No orphan bills — every open `OPCH` has a matching `CardType='S'` card,
so the `LEFT JOIN`s drop no money: standalone `OVPM`/`ORPC` totals (2017.11/185.56/2.74
and 0.34/15.52/0.02 Cr) equal `CO_UNAPPLIED_PAY`/`CO_OPEN_CN` exactly (**VERIFIED**).

**The faceted-sum trap.** The eleven `CO_*` columns are company totals repeated on every
row — summing one down the table multiplies it by the row count. The renderer never
does: `renderPartyAgeing` restricts the table to
`[CARD_CODE, CARD_NAME, ACCT_KIND, ADJ_OPEN] + buckets`, `table()` emits no totals row,
and the hero reads `sumOf('vendor-ageing','ADJ_OPEN', r => r.ACCT_KIND==='TRADE')`,
which reproduces `CO_ADJ_OPEN_TRADE` (**VERIFIED** in `data.json`). Left as-is, but the
header now warns in capitals.

**Cancelled documents.** `CANCELED='N'` on `OPCH` and `ORPC`, `Canceled='N'` on `OVPM`
(payments genuinely use the different spelling). 226/82/16 cancelled `OPCH` exist; none
is `DocStatus='O'` with a positive open amount, so the filter is correct but not
load-bearing today (**VERIFIED**).

**Foreign currency.** Oil has 57 non-INR open bills (USD/EUR/AUD, ₹142 Cr). `DocTotal`
equals `DocTotalSy` on every one, so `DocTotal` is **local currency** and the ageing is
not mixing USD into INR (**VERIFIED**). This was my strongest suspicion going in.

**`PaidToDate` validity.** Zero closed non-cancelled `OPCH` in any book has
`|DocTotal - PaidToDate| > 1`, so `PaidToDate` fully explains closure and `RAW_OPEN` is
a sound open figure (**VERIFIED**).

**Unapplied money — not double-subtracted.** `UNAPPLIED_PAY` and `OPEN_CN` are reported
and deliberately **not** subtracted; they are already inside the ledger balance.
Subtracting them would be catastrophic: Oil's `OVPM."OpenBal"` totals **₹2,017 Cr**
against a ₹102.63 Cr real payable. Oil holds 9,038 uncancelled supplier payments worth
₹3,638 Cr and **8,355 of them carry a non-zero `OpenBal`** (**VERIFIED**) — SAP internal
reconciliation is simply not used here, so `OpenBal` means "never matched", not "money
still unspent". Mart's ₹15.52 Cr of open A/P credit notes is ₹15.41 Cr on the interco
card `VENDA000001` alone (**VERIFIED**). Neither column reaches the rendered page.

**Branch / intercompany.** Flagged (`IS_EXCLUDED=1`), never dropped, never silently
included. This is the single most material fact in the section: branch+interco is
**78% of Oil's aged book** (₹79.83 of ₹102.15 Cr, 9 accounts), **95% of Mart's**
(₹27.60 of ₹29.18 Cr, 6 accounts) and **36% of Bev's** (₹0.79 of ₹2.21 Cr, 3 accounts)
(**VERIFIED**). The name test earns its keep exactly as the brief warned: Mart's
`VENDA000001 JIVO WELLNESS PVT LTD` (−₹20.93 Cr, Mart's largest payable) sits in group
106 PURCHASE and Oil's `VENDA000483 JIVO MART PVT LTD` (−₹2.25 Cr) in group 103
E-COMMERCE — a group-only test misses both (**VERIFIED**). I swept every `CardType='S'`
card in all three books for `JIVO`/`AKAL`/`WELLNESS`/`MART`/`BEVERAG` tokens and branch-ish
groups: no group entity is missed and nothing external is falsely caught
(`RELIANCE RETAIL LIMITED JIOMART` does **not** match `%JIVO%`) (**VERIFIED**).

**Migrated openings.** Oil's go-live load is real and large: 949 bills / ₹102.5 Cr dated
2024-09-30, of which **268 still read open (₹57.0 Cr raw) with due dates back to
2017-11-28** (**VERIFIED**). Because credit is consumed oldest-first these absorb the
adjustment and only ₹0.26 Cr survives into `MIGRATED_OPEN` — the correct outcome, since
the whole reason the credit exists is that the ledger says JIVO owes far less than the
bills claim. ₹56.99 Cr of the ₹57.0 Cr sits on TRADE vendors, so this is not hidden
inside the branch accounts (**VERIFIED**).

**`MIGRATED_OPEN`'s hardcoded date is correct, not an Oil-ism.** It tests
`DocDate = 2024-09-30` and returns 0 for Mart and Bev. That is the *true* answer:
Mart's `OPCH` starts 2025-01-01 and Bev's 2024-10-01, and neither book carried its A/P
openings in as invoices (**VERIFIED**). I nearly "generalised" this to `MIN(DocDate)` per
schema — that would have been a churn edit that made it **wrong**, relabelling Bev's
ordinary first trading day as a migration. Left alone; the reasoning is now in the header.

**Three-schema portability.** Ran on all three schemas myself. `BRANCH VENDOR` (group
101) exists in all three. No UDF is referenced anywhere. No account code is hardcoded.
The only date constant is the migration flag above.

**Empty / NULL.** No `NULL` `DocDueDate` in any book, so no bill can vanish between the
buckets and silently break the identity. No `NULL` vendor balance, no negative open
bill. The renderer already guards `if (!summary.length)`; the section is not in
`MAY_BE_EMPTY`, correctly — all three books have rows (**VERIFIED**).

**Money units.** Every money column is bare INR rupees. **No column name ends in `_L`
or `_CR`** (**VERIFIED** by scanning the output keys), which is what the renderer's
`scale()` requires — it multiplies by 1e5/1e7 purely on the suffix. Nothing renders
100,000x wrong. `ADJ_OVERDUE_60PLUS` is `B3+B4+B5+B6` = **61 days and over**; the
renderer labels it "61 d +", so the label is right even though the column name rounds
to 60. **I deliberately did not rename it** — `index.html` hardcodes
`sumOf('vendor-ageing','ADJ_OVERDUE_60PLUS')` in the hero, and renaming would blank a
headline KPI to fix nothing.

**Performance.** 2.0s / 1.0s / 1.6s per company through the real pipeline. Standalone
over the home bridge, including CLI startup: 2.1/1.3/1.7s before the fix and 3.1–3.6 /
1.7–2.2 / 2.0–2.6s after, so the JDT1 aggregation costs roughly 0.5–1.5s of wall clock.
JDT1 is only 526,820 / 344,144 / 86,414 rows. Nowhere near the 60s daily-refresh
concern (**VERIFIED**).

### Re-derived the headline a second, independent way

I reimplemented the whole credit-adjusted ageing in Python from raw rows — pulling
`OPCH` bills and JDT1 balances separately and redoing the FIFO credit consumption,
bucketing and branch/interco classification in application code with no shared logic:

```
                              python recompute        SQL section        delta
trade ADJ_OPEN            223,183,905.18      223,183,905.18      ₹0.0000
trade ADJ_OVERDUE_60PLUS  200,444,146.96      200,444,146.96      ₹0.0000
total PAYABLE           1,026,332,806.70    1,026,332,806.70      ₹0.0000
```

Exact to the paise on all three (**VERIFIED**). I also bill-level reconciled two of the
largest trade vendors by hand: `VENDA001347 INDRANI FOODS` (6 bills summing to ₹5.06 Cr,
zero credit, all 61+) and `VENDA001490 MAHA MAYA` (5 bills, ₹5.04 Cr raw, ₹1.34 Cr credit
consumed oldest-first leaving ₹3.70 Cr) — both tie to the rupee (**VERIFIED**).

### One suspicious-looking result that turned out to be real

90% of Oil's trade payable sits in 61+ days, which looks like a bucketing bug — credit is
consumed oldest-first, so what remains *should* skew new. It is genuine: JIVO's oil
suppliers are on **due-on-receipt terms** (`DocDueDate = DocDate` on every INDRANI and
MAHA MAYA bill) and the newest unpaid bills are themselves 232–261 days old
(**VERIFIED**). The distribution is the business, not the SQL.

---

## 5. Still unresolved — stated plainly

1. **Past-as-of bucket split is approximate.** As in D1: on `--as-of` runs the total is
   right and the bill side is today's, with the gap parked in `UNBACKED_CREDIT`. Fixing
   it properly needs `PaidToDate` reconstructed from the reconciliation history
   (`OITR`/`ITR1`), which is a bigger job than this section. **Not attempted.**
2. **Oldest-due-first is an assumption, not a fact.** The credit is real (the ledger
   proves the total) but *which* bills it settled is inferred. FIFO is the standard and
   conservative choice; where a vendor's genuinely-unpaid old bill sits behind newer
   settled ones, the total stays right and the bucket split shifts newer. Unfalsifiable
   without the reconciliation history. **INFERRED.**
3. **`ACCT_KIND` is a name/group heuristic.** It is correct for every material account
   today (swept and checked). A newly-created group entity whose name contains neither
   `JIVO` nor `AKAL` and which is not in a `%BRANCH%` group would be misclassified as
   TRADE. Groups 146/144 `COMPANY UNIT VENDOR` hold **0 cards** today and would not be
   caught by either test if populated (**VERIFIED**, now warned about in the header).
4. **`AKAL INFORMATION SYSTEMS LIMITED` is treated as intercompany.** Balance is
   −₹0.004 Cr in Oil, so it is immaterial either way, but I did not confirm with anyone
   at JIVO that it is in fact a group entity. **INFERRED.**
5. **The section blurb in `index.html`** says the ageing nets off "advances paid but
   never applied to a bill, and open debit notes". The SQL nets against the *ledger
   balance*, which contains those effects but is not the same statement. Defensible as
   written; I did not edit `index.html` because other agents are working in it. **Flagged only.**
6. **638 Oil "trade parties" but only 258 carry any `ADJ_OPEN`** (170 are advances). The
   renderer's KPI subtitle counts rows, so it reads "638 parties" against a ₹22.32 Cr
   figure. The money is right, the party count is breadth not exposure. Renderer-side;
   noted in the SQL header, **not changed**.
