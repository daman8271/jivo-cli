# goods-return — build note

Section id: `goods-return` · SQL: `pipeline/sql/goods-return.sql` (+ `goods-return-detail.sql`)
Written as an adversarial review of the original query, 2026-08-21, as-of `2026-08-21`.
Every number below was pulled live from HANA through `hana-sql` unless marked INFERRED.

**Verdict: FIXED** — four defects found and corrected, two of them material to the
headline. The query now runs clean on all three schemas and through the real pipeline.

---

## 1. What the question is

*"We sent stock back to a supplier. Did we ever get the money back on paper?"*

A goods return (SAP `ORPD`, ObjType 21) takes stock out and debits **GRNI —
2140001 GOODS RECEIVED BUT NOT INVOICED**; it does **not** touch the vendor's A/P
account. The vendor's liability only moves when the follow-on **A/P credit note**
(`ORPC`, ObjType 19) is raised, which clears GRNI against the vendor. So a return
with no credit note is value parked in GRNI that nobody has billed back.
**VERIFIED** — the journal behind every live return was read (see §6, "route C").

## 2. Tables and columns, and why

| Table | Used for | Key columns |
|---|---|---|
| `ORPD` | the return header — one row per document, the money the ledger actually posted | `DocEntry`, `DocDate`, `DocStatus`, `CardCode`, `CardName`, `DocTotal`, `VatSum`, `CANCELED`, `DocType` |
| `RPD1` | the line link to the follow-on credit note (summary) and line counts/qty/warehouse (detail) | `DocEntry`, `TargetType`, `TrgetEntry`, `BaseType`, `BaseEntry`, `Quantity`, `WhsCode`, `ItemCode` |
| `ORPC` | the A/P credit note that recovers the money | `DocEntry`, `DocNum`, `DocDate`, `DocTotal`, `CANCELED` |
| `OPDN` | the denominator: goods actually received, so a return can be read as a rate | `DocEntry`, `DocDate`, `CardCode`, `DocTotal`, `VatSum`, `CANCELED`, `DocType` |
| `OCRD` + `OCRG` | party classification — external supplier vs JIVO's own branch / sister company / dummy write-off card | `CardCode`, `CardName`, `CardType`, `GroupCode` → `GroupName` |

Money comes off the **header** (`DocTotal`, `DocTotal − VatSum`), not off the lines.
Both were computed and they agree to under ₹120 on ₹2.5 crore across the three books
(§6 route B) — the header is the posted figure, so the header wins.

**Money-unit contract:** no column carries an `_L` or `_CR` suffix, and no value is
scaled — **every amount in this section is raw INR**. VERIFIED by re-deriving each
column name against the dashboard's `scale()`/`isMoneyCol()` rules (§7.8).

## 3. Defects found and fixed

### D1 — the denominator counted service receipts (MAJOR, fixed)
`OPDN` is not only goods. It also carries **service-type receipts** (`DocType='S'`):
freight, job work, imprest, civil work. A goods return can never be raised against one
— every goods return ever posted in all three books is `DocType='I'` (VERIFIED, 103/49/19
of 103/49/19). The original query divided an item-only numerator by an item+service
denominator.

| book | GRPO docs before → after | GRPO net before → after | headline ratio before → after |
|---|---|---|---|
| Oil | 10,640 → **6,776** | ₹749.46 Cr → **₹743.61 Cr** | 0.0864% → **0.0871%** |
| Mart | 3,010 → **2,932** | ₹278.66 Cr → **₹278.32 Cr** | 0.4257% → **0.4262%** |
| Bev | 4,563 → **1,293** | ₹20.90 Cr → **₹18.82 Cr** | 1.9853% → **2.2052%** |

Beverages was the bad one: **72% of its "GRPO documents" were service receipts** and
10% of the money. Fix: `AND h."DocType" = 'I'` on the `GR` CTE. VERIFIED.

Side effect, checked: the only rows this removed are Oil's and Bev's `MONTH 2024-09`
rows. Both books' single pre-October-2024 GRPO is dated exactly **2024-09-30** (the
SAP go-live migrated opening) and both are service documents — so the migrated
opening is now out of the month chart entirely, and no month that has a return was
lost (row-key diff run before/after). VERIFIED.

### D2 — "returned, never credited" was mostly not a supplier claim (MAJOR, fixed)
`RET_GROSS_NO_CN` counts **every** live return with no live credit note. But two kinds
of return can never attract a supplier credit note by construction:

* **`STOCK GOODS ISSUE`** — a dummy vendor card used to write off physical shortage.
  Its journal is `DR STOCK SHORT AND EXCESS / CR stock` (Oil) or `DR GRNI + short-and-excess
  wash / CR stock` (Bev). No supplier is involved. VERIFIED on the JE.
* **intercompany** — Mart returning stock to Oil (`VENDA000001 JIVO WELLNESS PVT LTD`,
  in group `PURCHASE`, so only the *name* test catches it).

| book | RET_GROSS_NO_CN (all) | of which internal / intercompany | **RET_NOCN_EXT_GROSS** (supplier could still be billed) |
|---|---|---|---|
| Oil | ₹13,30,874 (19 docs) | ₹6,75,937 — 9 STOCK GOODS ISSUE | **₹6,54,937 (10 docs)** |
| Mart | ₹35,19,206 (16 docs) | ₹32,96,024 — 13 intercompany | **₹2,23,182 (3 docs)** |
| Bev | ₹21,25,711 (7 docs) | ₹19,57,750 — 4 STOCK GOODS ISSUE | **₹1,67,961 (3 docs)** |

Beverages' headline was **12.7x** the recoverable figure. Fix: two **new** columns,
`RET_NOCN_EXT_DOCS` and `RET_NOCN_EXT_GROSS`, on every scope row. `RET_GROSS_NO_CN`
is deliberately left untouched so the CLASS rows still fold back to TOTAL and nothing
downstream breaks; the dashboard KPI now leads with the external figure and names the
rest ("… more is branch, intercompany or stock write-off"). VERIFIED.

### D3 — the credit-note link ignored the as-of date (MINOR, fixed)
`build_data.py --as-of` is supported and used for month-end positions, but the
`HASCN` join accepted *any* live credit note, including one raised after the position
date. Fix: `AND n."DocDate" <= DATE'{{ASOF}}'` in both the summary and the detail.

| position | NO_CREDIT_NOTE before → after |
|---|---|
| Oil @ 2025-12-31 | 6 docs ₹6,02,832 → **7 docs ₹7,14,164** (+₹1,11,332) |
| Mart @ 2026-06-30 | 16 docs ₹35,19,206 → **17 docs ₹36,96,709** (+₹1,77,503) |

Zero effect at today's as-of: no live `ORPC` is dated after 2026-08-21 in any book
(VERIFIED). This is a latent-only defect that would have shown up the first time
somebody asked for a back-dated position.

### D4 — the TOTAL row emitted NULL instead of 0 in an empty book (MINOR, fixed)
`SUM()` over no rows is NULL, so a book with zero returns produced
`RET_NET/RET_GST/RET_GROSS = NULL` on the TOTAL row while every CLASS row said 0.
`goods-return` is in `build_data.py`'s `MAY_BE_EMPTY` set, so this is a real path.
Fix: `IFNULL(...,0)` in `R_TOT`/`G_TOT`. Tested by running at `--as-of 2020-01-01`
(one clean TOTAL row, no error) and `2024-10-05` (5 rows, GRPO but no returns).
VERIFIED.

## 4. Traps the query handles (and the evidence)

1. **`CANCELED` has three values, not two.** VERIFIED on all three tables and all
   three books: `'N'` live, `'Y'` the cancelled original, `'C'` the auto-generated
   mirror — and `'Y'` and `'C'` are numerically identical twins (Oil ORPD: 7 docs
   ₹9,37,728 each; OPDN: 473 docs ₹94.63 Cr each; ORPC: 14 docs ₹5,82,400 each).
   Filtering `<> 'Y'` would double-count every cancellation. The query keeps only
   `'N'`, on `ORPD`, `OPDN` **and** `ORPC`.
2. **Branch and intercompany are flagged, never dropped.** `PARTY_CLASS` splits
   EXTERNAL / BRANCH / INTERCOMPANY / INTERNAL_ADJ on both sides of the ratio, and the
   CLASS scope publishes all four. The group test alone is **not** enough — Mart's
   `VENDA000001 JIVO WELLNESS PVT LTD` sits in group `PURCHASE`, and it is 94% of
   Mart's returns; the name test catches it. VERIFIED: the only cards in any book whose
   name contains "JIVO" are genuine JIVO entities, and no third-party supplier is
   caught by it (checked `AWL AGRI BUSINESS`, `PARAS AGRI BUSINESS`, `ZENITHZEPHYR
   WELLNESS`, `LAXMI SUPER MEGAMART`, `CAPITAL WHEEL MART`, `PRINT MART` — all
   correctly EXTERNAL, none has a return).
3. **Dummy write-off cards.** `STOCK GOODS ISSUE` **and** `STOCK GOODS RECEIPTS` exist
   in Oil (VENDA001613/1614) and Bev (VENDA001307/1306); `LIKE 'STOCK GOODS%'` catches
   both, which is why Oil's INTERNAL_ADJ class shows 20 GRPOs (the RECEIPTS card) against
   9 returns (the ISSUE card). Mart has neither. VERIFIED.
4. **A return can have more than one credit note.** Bev has one return with two live
   CNs (13 CN documents pointing at 12 returns). `HASCN` is `SELECT DISTINCT DocEntry`,
   so it cannot fan the header row out. VERIFIED — `R` yields exactly 103/49/19 rows.
5. **Cancelled credit notes don't count as recovery.** `n."CANCELED"='N'` on the ORPC
   join. VERIFIED that no live return points *only* at a cancelled CN today.
6. **Card codes are not portable across books.** `VENDA000942` is a real supplier in
   Oil (PIONEER PET) and `JIVO MART PVT LTD - DL` in Mart. Classification is by group
   name + card name only; there is no hard-coded code list anywhere in this section.
   VERIFIED.
7. **Migrated openings (2024-09-30).** Zero goods returns are dated on go-live day in
   any book, so the numerator is clean. Both go-live GRPOs are service documents and
   now fall outside the denominator (see D1). VERIFIED.

## 5. Live numbers, 2026-08-21 (real output, `pipeline/raw/goods-return.*.tsv`)

```
OIL                RET_DOCS  RET_NET      RET_GST    RET_GROSS   OPEN  NOCN  NOCN_GROSS  GRPO_DOCS  GRPO_NET        PCT     EXT_DOCS  EXT_GROSS
TOTAL  ALL              103  6476726.51  984582.83  7461309.34     8    19    1330874        6776  7436076567.79  0.0871        10     654937
CLASS  BRANCH             0        0.00       0.00        0.00     0     0          0         759   582761456.04  0.0000         0          0
CLASS  EXTERNAL          94  5865157.16  920215.18  6785372.34     8    10     654937        5986  6845471791.28  0.0857        10     654937
CLASS  INTERCOMPANY       0        0.00       0.00        0.00     0     0          0          11     5020600.42  0.0000         0          0
CLASS  INTERNAL_ADJ       9   611569.34   64367.66   675937.00     0     9     675937          20     2822720.06 21.6660         0          0
CN     HAS_CREDIT_NOTE   84  5303848.50  826586.84  6130435.34     1     0          0        NULL          NULL     NULL         0          0
CN     NO_CREDIT_NOTE    19  1172878.01  157995.99  1330874.00     7    19    1330874        NULL          NULL     NULL        10     654937

MART               RET_DOCS  RET_NET      RET_GST    RET_GROSS   OPEN  NOCN  NOCN_GROSS  GRPO_DOCS  GRPO_NET        PCT     EXT_DOCS  EXT_GROSS
TOTAL  ALL               49 11863242.32  686654.20 12549896.52    16    16   3519206.18      2932  2783188117.43  0.4262         3     223182
CLASS  BRANCH             0        0.00       0.00        0.00     0     0          0         118   116201319.18  0.0000         0          0
CLASS  EXTERNAL           3   189137.25   34044.75   223182.00     2     3     223182         216    45327766.90  0.4173         3     223182
CLASS  INTERCOMPANY      46 11674105.07  652609.45 12326714.52    14    13   3296024.18      2598  2621659031.35  0.4453         0          0
CN     HAS_CREDIT_NOTE   33  8551301.63  479388.70  9030690.33     1     0          0        NULL          NULL     NULL         0          0
CN     NO_CREDIT_NOTE    16  3311940.69  207265.49  3519206.18    15    16   3519206.18      NULL          NULL     NULL         3     223182

BEV                RET_DOCS  RET_NET      RET_GST    RET_GROSS   OPEN  NOCN  NOCN_GROSS  GRPO_DOCS  GRPO_NET        PCT     EXT_DOCS  EXT_GROSS
TOTAL  ALL               19  4149869.34  722804.66  4872674.00     3     7   2125711        1293   188189292.02  2.2052         3     167961
CLASS  BRANCH             0        0.00       0.00        0.00     0     0          0          55     3114562.50  0.0000         0          0
CLASS  EXTERNAL          15  2476392.41  438531.59  2914924.00     3     3     167961        1222   158534712.92  1.5621         3     167961
CLASS  INTERNAL_ADJ       4  1673476.94  284273.06  1957750.00     0     4    1957750          16    26540016.61  6.3055         0          0
CN     HAS_CREDIT_NOTE   12  2327952.41  419010.59  2746963.00     0     0          0        NULL          NULL     NULL         0          0
CN     NO_CREDIT_NOTE     7  1821916.94  303794.06  2125711.00     3     7    2125711        NULL          NULL     NULL         3     167961
```

Headline, plain English:

* **Oil** — ₹74.61 L of stock sent back to suppliers on 103 documents, **0.087%** of the
  ₹743.61 Cr of goods received. **₹6.55 L on 10 external returns still has no credit
  note**; another ₹6.76 L of "no credit note" is the STOCK GOODS ISSUE write-off.
* **Mart** — ₹1.25 Cr on 49 documents, **0.426%** of ₹278.32 Cr — but 46 of the 49 are
  stock going back to Oil (intercompany). **Real supplier exposure: ₹2.23 L on 3
  returns**, all to S.N. INDUSTRIES.
* **Beverages** — ₹48.73 L on 19 documents, **2.205%** of ₹18.82 Cr — by far the highest
  return rate of the three books. **₹1.68 L on 3 external returns has no credit note**;
  the other ₹19.58 L of uncredited returns is the stock write-off card.

Biggest single vendors by returned value: Oil `PIONEER PET SWASTIC` ₹10.86 L / 10 docs,
`FRYSTAL PET` ₹10.62 L / 1 doc, `ECHO PLAST` ₹9.54 L / 20 docs. Bev `S.N. INDUSTRIES`
₹15.47 L / 6 docs, `A.J.SHRINK WRAP` ₹9.25 L / 1 doc. Mart is a single vendor,
intercompany, plus S.N. INDUSTRIES.

## 6. Re-deriving the headline three ways

* **Route A (shipped)** — `ORPD` header: Oil ₹74,61,309.34 gross / ₹64,76,726.51 net.
* **Route B (independent)** — sum `RPD1` lines instead (`LineTotal`, `VatSum`, `GTotal`),
  grouped up and joined back: Oil ₹64,76,734.98 net / ₹74,61,317.18 gross;
  Mart ₹1,18,63,251.89 net; Bev ₹41,49,870.66 net. **Agrees with route A to ₹8.47 (Oil),
  ₹9.57 (Mart), ₹1.32 (Bev)** — document-level rounding, not a defect. VERIFIED.
* **Route C (independent, mechanism)** — the general ledger. Every live return posts
  through `JDT1` on `TransId`: Oil 92 of 103 documents debit GRNI 2140001 (₹58.21 L),
  Mart 49 of 49 (₹1.15 Cr), Bev 19 of 19 (₹32.97 L). Against that, A/P credit notes
  credit GRNI by ₹52.34 L (Oil), ₹87.66 L (Mart), ₹23.69 L (Bev). Oil's ₹5.88 L
  return-minus-CN residual in GRNI is the same order as the ₹6.55 L external
  uncredited figure — corroboration, **not** an exact tie: the GL moves stock at
  *moving-average cost*, the document at *return price*, so the two can never be equal
  (checked on FRYSTAL: doc net ₹9,00,029.60 vs GL ₹8,72,100). VERIFIED, and stated as
  corroboration only.

## 7. What was attacked, and what survived

1. **Double counting / join fan-out** — SURVIVED. `ORPD ⋈ OCRD ⋈ OCRG` returns exactly
   103/49/19 rows and `OPDN ⋈ …` exactly 10,640/3,010/4,563 (pre-fix) — no fan.
   `OCRD.CardCode` and `OCRG(GroupCode,GroupType)` are both unique in all three books
   (0 duplicates), and no return or GRPO references a missing master. The credit-note
   join is `SELECT DISTINCT DocEntry` so a two-CN return cannot duplicate its header.
2. **Faceted stacking** — REAL RISK, documented not removed. Five scopes re-partition
   the same documents; summing the whole table gives ~5x. The renderer keys on `SCOPE`
   so the page cannot do it, but a human reading the TSV can. A `NEVER SUM ACROSS
   SCOPES` banner is now the first thing in the file header. Within each scope the
   partition is exact — CLASS, CREDIT_NOTE, MONTH and VENDOR each fold back to the
   TOTAL row on all 8 measure columns, in all three books (checked programmatically
   against the published `data.json`). VERIFIED.
3. **Cancelled documents** — SURVIVED after checking; `'N'` is applied on all three
   document tables, and the three-value domain was confirmed live (§4.1).
4. **Branch / intercompany** — SURVIVED, and quantified: 98.2% of Mart's returned
   value is intercompany (₹1,23,26,714.52 of ₹1,25,49,896.52 gross), as is 94.2% of its
   GRPO value (₹262.17 Cr of ₹278.32 Cr); Oil's branch GRPO is ₹58.28 Cr on 759
   receipts with zero returns. Group test alone would have missed Mart's biggest card;
   the name test catches it. Reverse direction checked too — no genuine third party is
   swept up by `%JIVO%`.
5. **Unapplied money / open-item shape** — NOT APPLICABLE, verified rather than assumed.
   This section never touches `ORCT`/`OVPM`/`OpenBal`, so there is nothing to
   double-subtract. `RET_DOCS_OPEN` is a document count, not money.
   And `DocStatus='O'` is confirmed unreliable here as elsewhere at JIVO: Oil has **12
   CLOSED returns worth ₹11.45 L with no credit note at all**, and 1 OPEN return that
   does have one. That is why "never credited" is built on the document link and not on
   `DocStatus`. VERIFIED.
6. **Migrated openings** — SURVIVED (§4.7).
7. **Three-schema portability** — SURVIVED. Run against all three schemas at as-of
   2026-08-21, 2025-12-31, 2026-06-30, 2024-10-05 and 2020-01-01. No UDF, no account
   code, no card code, no group code is hard-wired; the only literals are the SAP
   object types (19/20/21), `DocType='I'`, `CANCELED='N'` and the two name patterns.
   Bev has no INTERCOMPANY class and Mart no INTERNAL_ADJ class — the FULL OUTER JOIN
   handles the missing bucket without emitting a phantom row.
8. **Money units** — SURVIVED after audit. Every column name was re-tested against the
   dashboard's `scale()` and `isMoneyCol()` rules. Nothing is scaled and no name claims
   a scale, so nothing can render 100,000x wrong. Two naming quirks were found and
   neutralised rather than renamed (renaming would have broken the KPI cards if a
   concurrent edit to `index.html` were lost):
   * `RET_GROSS_NO_CN` ends in `_CN`, which `isMoneyCol()` does not recognise, so a
     generic table printed it as a bare integer next to real money. The CLASS block now
     formats it explicitly with `money()`.
   * `RET_DOCS_OPEN` ends in `OPEN`, which `isMoneyCol()` *does* match — it would print
     "₹8" if it ever landed in a table. It appears in no table column list (checked),
     only in a KPI that calls `num()`. Left as a documented landmine.
   * `RET_PCT_OF_GRPO` is a percent with four decimals; the generic table formatter
     rounds numbers to integers, so 0.0871% displayed as "0". The CLASS block now
     formats it explicitly to 3 decimals.
9. **Headline re-derived independently** — three routes, §6.
10. **Performance** — SURVIVED comfortably. Summary 1.0–1.5 s per company, detail
    1.1–1.5 s. Full section through `build_data.py`: **6.2 s for all six queries**.
    Nowhere near the 60 s bar or the 300 s pipeline timeout.

## 8. Pipeline proof

```
$ python3 build_data.py --only goods-return --no-guard
connection: home bridge (127.0.0.1:13015 -> VPS -> hanadb)
as-of 2026-08-21 — 1 section(s): goods-return
  goods-return
    summary   oil        61 rows    1.0s
    summary   mart       28 rows    1.0s
    summary   bev        38 rows    1.0s
    detail    oil       117 rows    1.1s
    detail    mart       59 rows    1.1s
    detail    bev        33 rows    1.1s
wrote .../site/data.json  (10184.3 KB, 7923 summary rows, 6.2s)
```

No FAILED line, `errors: {}` for all six queries. Row counts are far under the caps
(200 summary / 500 detail), so nothing is being silently truncated: VENDOR rows are
31 / 2 / 9.

⚠️ `site/data.json` is a shared file and several agents were rebuilding their own
sections at the same time. `build_data.py` merges a partial run onto whatever
`data.json` it read at start-up, so a concurrent run that started earlier can write
back an older copy of this section. The section was rebuilt after that happened once
and verified in place. **Anyone re-running a full build afterwards gets the correct
values from these `.sql` files regardless** — the SQL is the source of truth, not the
JSON.

## 9. Still unresolved — stated plainly

1. **"No credit note" means no *linked* credit note.** SAP is the only evidence of a
   link, and a credit note raised standalone or copied from the A/P *invoice* instead of
   from the return is invisible to it. Hunting for an unlinked live credit note to the
   same vendor, same amount (±₹1), within 120 days after the return finds:
   * Oil return 2126076512 (ROYAL PRIME LABELS, ₹13,806) — CN 626075053 four days
     later, exactly ₹13,806, **based on an A/P invoice**. Almost certainly the same
     goods. That is **₹13,806 of Oil's ₹6,54,937 (2.1%)** probably already recovered.
   * Mart return 1025214702 (S.N. INDUSTRIES, ₹79,134) — CN 612255906, same amount,
     also invoice-based. **₹79,134 of Mart's ₹2,23,182 (35%)**.
   * Mart return 126214700 (₹3,000, intercompany) — two standalone ₹3,000 CNs;
     ambiguous, and outside the external headline anyway.
   * Beverages: **no match at all** — its ₹1,67,961 looks genuinely unrecovered.
   No fix applied on purpose: an amount-and-date match is a hint, not a link, and
   building the KPI on a fuzzy match would manufacture certainty SAP does not have.
   Someone in Accounts has to confirm these two by eye. INFERRED (the match is
   verified; the *conclusion* that it is the same goods is not).
2. **The ratio's denominator is still all item receipts, not "returnable materials".**
   Even item GRPO includes staff-imprest receipts (Oil 820 documents, ₹26.08 L, group
   `STAFF VENDOR`, card prefix `ORGV`) and fixed-asset receipts. Immaterial in money
   (0.03% of Oil's denominator) but it inflates document counts. Not split — there is no
   clean field that says "returnable"; the CLASS breakdown is the honest cut available.
   VERIFIED figures, judgement call on the fix.
3. **Four Oil returns have no journal entry at all** (`TransId` NULL): docs 2125116503,
   2125126500 (ECHO PLAST) and 2126076505, 2126076513 (STOCK GOODS ISSUE), ₹22,207
   gross combined. They are real documents and stay in the register; they just mean the
   GL and the document register can never be tied 1:1. VERIFIED, cause not established.
4. **`BRANCH` beats `INTERCOMPANY` in the CASE order.** In Beverages, `JIVO WELLNESS
   PVT LTD - PB` sits in group `BRANCH VENDOR`, so it is labelled BRANCH even though
   from Beverages' point of view it is a sister company. Either way it is flagged as
   non-trade, which is what the rule requires — but the BRANCH/INTERCOMPANY split is not
   meaningful across books. VERIFIED.
5. **SAP's internal reconciliation is unused here too** — `JDT1."IntrnMatch" = 0` on
   **100%** of the lines behind every goods return in all three books. Consistent with
   the rest of this dashboard; nothing in this section relies on it. VERIFIED.
6. **Detail rows include cancelled documents on purpose** (Oil 117 rows = 103 live + 7
   cancelled + 7 cancellation mirrors; Mart 59 = 49+5+5; Bev 33 = 19+7+7), decoded in
   `CANCEL_STATUS`. Every flag and total in the detail is computed for `'N'` only, but
   **anyone summing `GROSS_AMT` straight down the detail file will over-count by the
   cancelled pairs**. The dashboard does not render the detail for this section.
   VERIFIED.
