# transporter — who moves our goods, and what we pay them

Adversarial review and repair, 2026-08-21, as-of 2026-08-21.
Verdict: **FIXED.** One material defect found and corrected; the rest survived.

Every claim below is tagged **VERIFIED** (I ran the query in this session and
pasted the answer) or **INFERRED** (I reasoned it and did not prove it).

---

## 1. What the query reads, and why

| Table | Columns used | Why |
|---|---|---|
| `OINV` | `DocEntry`, `DocDate`, `DocTotal`, `VatSum`, `CardCode`, `CANCELED`, `U_TransporterName`, `U_DriverName`, `U_TransporterInvoice`, `U_BiltyDate`, `U_BiltAmt`, `U_Ship_From`, and the per-book bilty/vehicle UDFs | **The A/R invoice is the dispatch document at JIVO.** The standard SAP shipping table `OSHP` is empty and deliveries are barely used, so the transport facts live in UDFs on the invoice. |
| `OCRD` | `CardCode`, `CardName`, `CardType`, `GroupCode` | Customer side: whose goods moved. Vendor side: who the carrier is. |
| `OCRG` | `GroupCode`, `GroupType`, `GroupName` | Branch detection on the customer side; the transporter supplier group on the vendor side. |
| `OPCH` / `ORPC` | `CardCode`, `DocDate`, `DocTotal`, `VatSum`, `CANCELED` | **The cost side.** Freight is not on the dispatch document (`U_BiltAmt` is filled on 4 of 19 309 Oil invoices), so spend can only come from A/P. `ORPC` (A/P credit notes) is netted off. |
| `CUFD` / `UFD1` | `TableID`, `AliasID`, `Descr`, `TypeID`, `FieldID` | Reads each UDF's real SAP caption and whether it has a valid-value list. This is how the `U_LRNUmber` trap below was caught. |
| `ODLN` / `OPDN` | `CANCELED`, `DocDate`, `U_TransporterName` | Only to prove the transporter data is *not* kept on deliveries or GRPOs. |

Not used anywhere, deliberately: `DocStatus`, `ORCT`/`OVPM` `OpenBal`, `JDT1.IntrnMatch`.
Nothing in this section is ageing- or open-item-shaped, so the double-subtraction
trap cannot arise here. **VERIFIED** — `grep -n 'DocStatus\|OpenBal\|IntrnMatch'`
returns only the comment line that says it is not used.

---

## 2. THE DEFECT THAT WAS FIXED

### The freight-vendor universe was defined by supplier group alone, and the biggest carrier in the book is not in that group

`VEND` used to select supplier cards whose **OCRG group name** matched
`%TRANSPORT% / %FREIGHT% / %LOGIST% / %COURIER% / %CARRIAGE%` — in practice group
102 TRANSPORTER, ~96 cards per book.

**R K TANKER SERVICE (Oil `VENDA000671`) is filed under supplier group 110
PURCHASE OIL.** It is not a purchase vendor. **VERIFIED:**

```
ItemCode  DESC                                   N    L
NULL      TPT FREIGHT FROM SHEMLA TO SONIPAT ...  737  993.72
```

₹945.12 L of A/P over the period, every line pure road freight. On the group-only
test the entire ₹945 L was invisible — **more than the whole freight figure the
section reported (₹520.09 L).** Worse, R K Tanker is the *4th largest transporter
by dispatch value in the Oil book* (92 invoices, ₹5 485 L), and the dashboard
printed next to it:

> `NO FREIGHT VENDOR CARD MATCHED`

That is a factually false statement on a page Accounts makes decisions from. It
was not a rounding issue; it inverted the answer to "do we pay this carrier?".

**The fix.** `VEND` now admits a supplier card on **either** the supplier group
**or** a road-carrier token in the card's own name (`TRANSPORT, LOGISTIC, CARRIER,
CARGO, ROADLINE, FREIGHT, COURIER, TANKER, CARTAGE, ROADWAY, SUPPLYCHAIN,
PACKERSMOVER`, tested against the same punctuation-stripped key used for
transporter names). `IN_GRP` records which test let each card in, and every
`FREIGHT_VENDOR` row now says so in its `NOTE`, so the widening is auditable
rather than silent:

```
R K TANKER SERVICE   152 docs  945.12 L
  OUTSIDE the transporter group -- filed under "PURCHASE OIL", pulled in on the
  carrier token in its name; ships under transporter family "RKTANKER"
```

**Effect on the headline — VERIFIED:**

| Book | freight before | freight after | as % of dispatch |
|---|---|---|---|
| Oil | ₹520.09 L | **₹1 802.06 L** | 0.6% → **2.0%** |
| Mart | ₹289.49 L | **₹325.30 L** | 0.9% → **1.0%** |
| Bev | ₹168.47 L | **₹203.04 L** | 7.7% → **9.3%** |

The Oil figure was **understated 3.5×**. 2.0% of dispatch value is also the more
credible number for an FMCG oil business; 0.6% never was.

**False positives: none.** **VERIFIED** — I listed every card the widening adds,
in all three books, and read them one by one. All 32 Oil / 14 Mart / 12 Bev
additions are unambiguous road carriers (R K TANKER SERVICE, ARSH TRANSPORT,
OM LOGISTICS SUPPLY CHAIN, BALMUKUND ROADWAYS, TEJAJI ROADLINES, BHARGAVE ROAD
CARRIER, ROHIT CARGO MOVERS, GATI EXPRESS & SUPPLY CHAIN …). Every one that also
matched a dispatch name matched the *correct* family — checked line by line.

**Wider tokens were tested and deliberately rejected. VERIFIED:** adding
`SHIPPING / EXPRESS / FORWARD / TEMPO / LOGIS / TRANS` pulls in ocean lines,
container agents and clearing-and-forwarding houses — COSCO, MSC, EVERGREEN,
TRANSGLOBE SHIPTRANS, OCEAN NETWORK EXPRESS, AIYER SHIPPING, SHREE SAI CLEARINGS
AND FORWARDING — which are **import freight on goods bought**, a different cost
family from road transport of goods dispatched. `%TRANS%` also produces an
outright false positive (`KAMAL TRANSFORMERS`). That excluded remainder is
**Oil ₹192.58 L, Mart ₹0, Bev ₹2.08 L**. If someone later wants "all logistics
spend" rather than "road carriers", that is the number to add back.

`transporter-detail.sql` carries the identical `VEND`, or the grid would disagree
with the summary.

---

## 3. THE LIVE NUMBERS, all three books

Straight from `pipeline/raw/transporter.<book>.tsv` after the fix. Money columns
end `_L` and are **INR lakhs**. **VERIFIED.**

```
### oil
SCOPE      GRP_KEY       DISP_DOCS  DISP_VAL_L  EXT_DISP_DOCS  EXT_DISP_VAL_L  NAMED_PCT  LR_PCT  VEH_PCT  FRT_DOCS  FRT_SPEND_L  FRT_PCT_OF_DISP
TOTAL      ALL           19309      92379.73    15410          54661.61        39.6       48.6    45.3     1455      1802.06      2
NAMECLASS  THIRD_PARTY   7637       60232.62    5661           41614.44        NULL       98.2    96.6     NULL      NULL         NULL
NAMECLASS  UNNAMED       10238      21564.92    9111           10887.16        NULL       4.9     1.5      NULL      NULL         NULL
NAMECLASS  OWN_OR_SELF   1224       8369.74     544            2149.09         NULL       95.8    94.4     NULL      NULL         NULL
NAMECLASS  UNUSABLE      210        2212.45     94             10.93           NULL       100     35.2     NULL      NULL         NULL
PARTY      EXTERNAL      15410      54661.61    15410          54661.61        36.7       42.9    39.5     NULL      NULL         NULL
PARTY      INTERCOMPANY  2968       30398.62    0              0               47.2       72.4    69.9     NULL      NULL         NULL
PARTY      BRANCH        931        7319.5      0              0               61.7       67.6    62.9     NULL      NULL         NULL

### mart
SCOPE      GRP_KEY       DISP_DOCS  DISP_VAL_L  EXT_DISP_DOCS  EXT_DISP_VAL_L  NAMED_PCT  LR_PCT  VEH_PCT  FRT_DOCS  FRT_SPEND_L  FRT_PCT_OF_DISP
TOTAL      ALL           25109      32252.11    24845          30891.23        2.5        3.8     3.9      644       325.3        1
NAMECLASS  UNNAMED       24149      24828.17    23908          23467.29        NULL       0.1     0.1      NULL      NULL         NULL
NAMECLASS  THIRD_PARTY   625        5193.74     607            5193.74         NULL       99.2    100      NULL      NULL         NULL
NAMECLASS  OWN_OR_SELF   335        2230.2      330            2230.2          NULL       96.7    100      NULL      NULL         NULL
PARTY      EXTERNAL      24845      30891.23    24845          30891.23        2.4        3.8     3.8      NULL      NULL         NULL
PARTY      INTERCOMPANY  35         777.33      0              0               0          0       0        NULL      NULL         NULL
PARTY      BRANCH        229        583.54      0              0               7.9        9.6     10       NULL      NULL         NULL

### bev
SCOPE      GRP_KEY       DISP_DOCS  DISP_VAL_L  EXT_DISP_DOCS  EXT_DISP_VAL_L  NAMED_PCT  LR_PCT  VEH_PCT  FRT_DOCS  FRT_SPEND_L  FRT_PCT_OF_DISP
TOTAL      ALL           5314       2174.24     5061           2067.37         73.3       84.4    79.5     437       203.04       9.3
NAMECLASS  THIRD_PARTY   3894       1823.9      3794           1785.44         NULL       99.5    99.2     NULL      NULL         NULL
NAMECLASS  UNNAMED       1065       237.05      987            201.39          NULL       26.2    3.1      NULL      NULL         NULL
NAMECLASS  OWN_OR_SELF   251        108.9       193            77.72           NULL       92      91.6     NULL      NULL         NULL
NAMECLASS  UNUSABLE      104        4.39        87             2.82            NULL       96.2    95.2     NULL      NULL         NULL
PARTY      EXTERNAL      5061       2067.37     5061           2067.37         75         85.2    80.1     NULL      NULL         NULL
PARTY      BRANCH        86         59.71       0              0               27.9       51.2    52.3     NULL      NULL         NULL
PARTY      INTERCOMPANY  167        47.17       0              0               45.5       78.4    75.4     NULL      NULL         NULL
```

Read in one line: **Oil dispatched ₹923.80 Cr on 19 309 invoices, ₹546.62 Cr of it
to external customers, and paid carriers ₹18.02 Cr (2.0%). Mart ₹322.52 Cr /
₹308.91 Cr external / ₹3.25 Cr freight. Beverages ₹21.74 Cr / ₹20.67 Cr external /
₹2.03 Cr freight.**

The coverage story is the real finding for Accounts: **Oil names a transporter on
only 39.6% of dispatches and an LR number on 48.6%; Mart on 2.5% and 3.8%.**
Beverages is the only book that keys it properly (73.3% / 84.4%).

---

## 4. Traps in the data, and how the SQL handles each

1. **`U_LRNUmber` is not the LR number.** Its SAP caption in `CUFD."Descr"` is
   *"Bill Of Entry No."* — a customs field. Filled on 39 of 19 309 Oil dispatches
   (0.2%), 1 of Mart's, and the column does not exist at all in Beverages. The real
   lorry receipt is the **bilty**. `LR_PCT` is built on the bilty; `U_LRNUmber` is
   reported as its own `FIELD` row with its true caption so nobody re-makes the
   mistake. **VERIFIED** from the live `FIELD` rows.

2. **The UDF names differ between books**, and HANA fails at *compile* time on a
   column a schema does not have:
   `Oil/Mart "U_BilltyNumber" "U_VehicleNoM"` vs `Bev "U_BiltyNumber" "U_VechileNom"`.
   Handled by the `UDFX` shim: three `UNION ALL` branches, each naming only its own
   schema's columns, each gated on the constant predicate `'{{SCHEMA}}' = '<that
   schema>'`. All three compile; the two false branches return nothing.
   **The safety here is semantic, not optimiser-dependent** — a constant-false
   `WHERE` filters the rows whether or not HANA prunes the scan, so cross-book
   `DocEntry` collision is impossible. **VERIFIED:** `COUNT(*)` out of `D` is
   19 309 / 25 109 / 5 314, identical to a plain single-table `OINV` count, so the
   `LEFT JOIN` to `UDFX` fans out zero rows.

3. **`U_TransporterInvoice` is captioned "Gate Pass No."**, not a transporter
   invoice number, and is filled on 1 document in Oil and 0 elsewhere. Reported in
   `FIELD` for completeness, used for nothing. **VERIFIED.**

4. **Migrated openings at 2024-09-30.** Oil has 11 078 live invoices dated exactly
   that day, ₹74.74 Cr, **none of which carries a transporter name** — they are
   go-live opening balances and would dilute every coverage percentage by a third.
   Excluded from dispatches and from freight. **VERIFIED**, including the
   30 387 − 11 078 = 19 309 arithmetic. Also **VERIFIED: that date exists only in
   the Oil book** — Mart and Bev have zero rows on it in `OINV`, `OPCH`, `ORPC` and
   `ODLN`, so the exclusion is a no-op for them. The same exclusion drops ₹43.5 L of
   *opening* transporter A/P in Oil (R K TANKER ₹15.76 L, CARGO CLEARING ₹13.34 L,
   MAHADEV TEMPO ₹6.21 L …) — correct and symmetric, since the dispatch side those
   bills belong to is excluded too, but it does mean freight is "since go-live".

5. **`U_TransporterName` is free text.** `CUFD."EditType"` is blank and `UFD1` holds
   zero valid values in all three books, so nothing is validated on entry. Oil holds
   234 raw spellings. `TN_KEY` strips case, spaces and punctuation **including the
   LIKE wildcards `%` and `_`**, so a stray one cannot widen a match. `VARIANTS`
   reports how many raw spellings fed each row. **VERIFIED** — the family collapse
   is sane (`RKTANKER` absorbs 7 spellings, `DELHIPUNJAB` 6, `MAHADEV` 5), and I
   inspected every multi-key family in Oil for over-merge and found none.

6. **Not every name is a transporter.** `NAMECLASS` splits `THIRD_PARTY /
   OWN_OR_SELF / UNUSABLE / UNNAMED`, and the `TRANSPORTER` scope counts
   `THIRD_PARTY` only, so freight-per-carrier is never divided by dispatches nobody
   was paid for. **VERIFIED** by listing every non-third-party key with its value:
   `JIVOVEHICLE` 848 docs ₹6 053 L, `SELFPICKUP` 205, `SELF` 99, `BARUSAHIBVEHICLE`,
   `AMAZONVEHICLE`, `PARTYVEHICLE`, and `NA` 180 docs ₹2 208 L. Every one is
   genuinely own-fleet, customer-collected or a keystroke. **No real carrier is
   being thrown out**, including the misspellings `JIVOVECHILE`, `JIVOVEHCLE`,
   `BARUVEHICLE`.

7. **Branch and intercompany are flagged, never silently dropped or included.**
   Every scope carries both `DISP_VAL_L` (all) and `EXT_DISP_VAL_L` (external only),
   and `PARTY` splits them three ways. The classification uses the group test
   (`OCRG."GroupName" LIKE '%BRANCH%'` on `GroupCode` + `GroupType` = `CardType`)
   **and** the card-name test (`%JIVO%`), because the group test alone is not enough
   at JIVO. **VERIFIED against the settled list: all 23 group CardCodes are caught**
   — Oil's 9, Mart's 8, Bev's 6 — nine land as BRANCH via the group name, and the
   rest (`CUSTA000606 JIVO MART PVT LTD` in group 116 DELHI, `CUSTA000906 JIVO
   BEVERAGES-CUST`, Mart's `CUSTA000001 JIVO WELLNESS PVT LTD` in group 143 PARENT
   COMPANY) only by the name test. Not-trade is **₹377.18 Cr of Oil's ₹923.80 Cr —
   41% of the headline.**

8. **Vendor matching is many-to-many.** `OM LOGISTICS`, `OM LOGISTICS LTD` and
   `OM LOGISTICS LTD.` are one carrier. Matching is a two-sided prefix test on the
   squashed key with a 6-character floor, reduced to **one family per vendor card**
   (`ROW_NUMBER() PARTITION BY CARD_CODE`), so no vendor's spend lands under two
   transporters. Several cards may share a family — that is intended, `FILLED`/
   `NVEND` says how many merged. Freight from vendors matching no dispatch name is
   not discarded: it becomes `FREIGHT_VENDOR` rows and is quantified in the `TOTAL`
   note (Oil 89.8% of freight is tied to a named transporter, Bev 99.1%, **Mart only
   32.3%** — Mart barely keys transporter names at all). "NEVER BILLED" (card
   exists, no A/P) and "no card matched" are deliberately different strings.

9. **Cancellation.** `"CANCELED" = 'N'` on every document table touched — `OINV`,
   `OPCH`, `ORPC`, `ODLN`, `OPDN`. **VERIFIED that the column takes three values,
   not two**: `'N'` 30 387 / `'Y'` 320 / `'C'` 320 in Oil's `OINV`. `'Y'` is the
   cancelled document and `'C'` the cancelling one, so `= 'N'` correctly drops both
   halves of a cancellation pair. `"DocStatus"` is deliberately unused — at JIVO
   documents are settled by journal entry and stay open long after the money moved.

---

## 5. What I attacked, and what survived

| Attack | Result |
|---|---|
| **Headline re-derived a second way.** Independent single-table `OINV` aggregate, no CTEs. | **SURVIVED, exact.** Oil 19 309 docs / ₹92 379.73 L, Mart 25 109 / ₹32 252.11 L, Bev 5 314 / ₹2 174.24 L — identical to the section's `TOTAL` row to the paisa. |
| **Freight headline re-derived a second way.** A completely separate scalar-subquery formulation reusing none of the CTEs. | **SURVIVED, exact.** Oil 1 455 docs / ₹1 802.06 L, Mart 644 / ₹325.30 L, Bev 437 / ₹203.04 L. |
| **Freight sanity-checked against the G/L**, which the query never touches. | **Consistent.** Oil's group-only figure (₹520.09 L) sat right on the P&L freight accounts (₹496.25 L net). The repaired ₹1 802.06 L is larger than the *net* P&L because Oil's inward-freight accounts 5100002 and 5500001 are **clearing accounts** — ₹684.16 L and ₹1 239.44 L of debits against almost equal credits — so inward freight is relieved into stock cost and nets to near zero in the P&L while the cash still went out. **VERIFIED** from `JDT1`. This is why the A/P route, not the P&L route, is the right one for "what we pay them". |
| **Join fan-out.** `OINV → OCRD → OCRG`, and `D → UDFX`. | **SURVIVED.** `COUNT(DISTINCT DocEntry)` = `COUNT(*)` = the section's `DISP_DOCS` in all three books; `GroupCode` is unique in `OCRG` (**VERIFIED**, `HAVING COUNT(*)>1` returns nothing), and 0 supplier cards fail to resolve to a `GroupType='S'` group in any book. |
| **Faceted double-count.** Seven scopes stacked in one table. | **Structurally present, correctly handled.** `(SCOPE, GRP_KEY)` is unique — **VERIFIED**, zero duplicates in all three books — and `NAMECLASS`, `PARTY` and `MONTH` each foot **exactly** to `TOTAL` (Oil ₹92 379.73/74 L on all three). `TRANSPORTER` and `FREIGHT_VENDOR` are deliberate subsets. **Summing `FRT_SPEND_L` across scopes double-counts**: the same rupee appears once on a `TRANSPORTER` row and once on a `FREIGHT_VENDOR` row. The renderer filters by facet and never does this. |
| **Cancelled documents.** | **SURVIVED** — see trap 9. |
| **Branch / intercompany.** | **SURVIVED** — see trap 7. All 23 CardCodes caught, quantified at 41% of Oil's headline. |
| **Unapplied money / open items.** | **NOT APPLICABLE, verified rather than assumed.** No `DocStatus`, no `OpenBal`, no `IntrnMatch` anywhere in either file. Nothing is ageing-shaped, so there is no inflation to quantify. |
| **Migrated openings.** | **SURVIVED** — see trap 4, and the date exists only in Oil. |
| **Three-schema portability.** | **SURVIVED for the three books that exist.** Ran end to end against all three: 107 / 81 / 107 rows, 21 columns each. But see "unresolved" below — the old header's claim that a *fourth* book would degrade gracefully is false, and I have corrected it. |
| **Empty and NULL.** | **SURVIVED.** Forced an empty book with `--as-of 2020-01-01`: 12 rows, no error, `TOTAL` present with `NULL` money and a renderable shape. `BASE` and `FRTTOT` are un-grouped aggregates so they always return exactly one row. |
| **Money units.** | **SURVIVED.** Every money column ends `_L` and is `ROUND(x/100000, 2)` — genuinely lakhs. Confirmed against the renderer, which scales `_L` by `1e5`. `*_PCT` are 0–100 and carry no unit suffix; `DISP_DOCS` / `FRT_DOCS` / `FILLED` / `VARIANTS` are counts. No column name lies about its scale. |
| **Performance.** | **SURVIVED, comfortably.** 1.3–1.5 s per book for the summary, 1.4–1.9 s for the detail, ~8.8 s for the whole section end to end. Slightly faster than before, because three dead UDF reads were removed. |

---

## 6. Also changed

- **Three dead columns removed** from `DISP`: `HAS_GATEPASS`, `HAS_BDATE`,
  `HAS_DDATE` were computed and never referenced. Dropping them also removes the
  only reference to `"U_Dipatch_Date"` — a misspelled UDF that a new company book
  would almost certainly lack. Cannot change any output column; **VERIFIED** by
  re-running (21 columns before and after).
- **The `TOTAL` note's variant count was misleading.** It read *"name spread 234
  raw spellings → 147 keys → 106 families"*, mixing 234 (all classes, including
  own-fleet and placeholders) with 147/106 (third-party only). It now reports both
  explicitly: *"196 third-party spellings (234 incl. own-fleet/placeholder)"*.
- **Every piece of the `TOTAL` note is now `IFNULL`-guarded.** In HANA a single
  `NULL` blanks a whole concatenation, so on an empty book the note used to
  disappear entirely.
- **`site/index.html`**: added a note under the transporter `PARTY` table saying the
  "Dispatched" KPI is *all* dispatches and only the EXTERNAL row is real trade, and
  that "Freight paid" is A/P only. Mirrors what the `grpo` section already does. No
  other change to the renderer.

---

## 7. Still unresolved — stated plainly

1. **Freight accrued straight to the ledger by journal entry is invisible here.**
   This section measures A/P to carriers. Oil's account 5670001 FREIGHT AND CARTAGE
   OUTWARD carries ₹1 562.05 L of debits, of which only ₹484.61 L arrives via
   transporter-group A/P invoices — the balance comes through month-end freight
   provisions (accounts 2165001–2165012 FREIGHT PAYABLE APR…MAR) and manual JEs.
   **VERIFIED** from `JDT1`. Closing that gap means reading `JDT1` by account, which
   is a different query and arguably belongs in `provisions`. **The number on this
   page is "what we billed from carriers", not "total freight cost".**

2. **Service A/R invoices (`DocType = 'S'`) are counted as dispatches.**
   **VERIFIED:** Oil 387 docs ₹556.04 L (0.6% of the headline), Mart 67 docs
   ₹1 567.49 L (**4.9%**), Bev none. **None of them carries a transporter name**
   (0 of 387 and 0 of 67), so they can only dilute the coverage percentages — they
   never invent a carrier. Mart's are mostly listing/marketing fees to Zomato
   Hyperpure, Flipkart Grocery and Kiranakart, plus ₹774.40 L of intercompany that
   is already flagged. Left in deliberately: excluding them would require the same
   predicate in eight `UNION` branches to keep `FIELDSTAT`'s `TOTN` consistent with
   `DISP_DOCS`, and 0.6% / 4.9% / 0% does not change a decision. **Quantified here
   so nobody has to rediscover it.**

3. **`DISP_VAL_L` is invoices only — sales returns (`ORIN`) are not netted off.**
   This is dispatch value, not turnover; a return does not un-dispatch a truck. It
   will not tie to the turnover figure elsewhere on the dashboard, and it is not
   meant to. **INFERRED** that this is the right convention for a transport view;
   nobody has ruled on it.

4. **The detail grid's freight column is short, by design and now disclosed.**
   **VERIFIED:** the grid carries ₹404.62 L less Oil freight than the same families
   show in the summary (28.6%), Mart ₹39.78 L, Bev ₹13.46 L. Two structural causes,
   both inherent to the (family, month) grain: families outside the top 20 fold into
   `ZZ_OTHER`, whose freight is `NULL` by design; and a freight bill booked in a
   month that carrier happened not to dispatch in has no cell to land in, because
   the grid is driven off dispatch rows. A `FULL OUTER JOIN` on (family, month)
   would fix it but changes the row grain and the row-count contract. **Do not total
   the grid's freight column** — `transporter.sql` is the authority. Warning added
   to the detail file's header.

5. **Spelling variants that are not prefixes of each other stay separate.**
   `BOMBAYSRINAGAR`, `BOMBEYSRINAGAR` and `BOMBESRINAGAR` are three families;
   `MAHAVEERTRANSPORT` and `MAHAVIRTRANSPORT` are two, and only the second has a
   vendor card. This *under*-merges — it splits one carrier across rows — so it
   never inflates anything, and `VARIANTS` makes it visible. Fixing it needs a
   hand-written normalisation map, which is a data-entry decision for Accounts, not
   a SQL one.

6. **`FIELDSTAT` and `DISP` name six UDFs literally** (`U_TransporterName`,
   `U_TransporterInvoice`, `U_DriverName`, `U_BiltyDate`, `U_BiltAmt`,
   `U_Ship_From`), outside the `UDFX` shim. The old header claimed a fourth or
   renamed company book *"would return no LR or vehicle rows … never an error"*.
   **That was false** and I have corrected the header: only the bilty and vehicle
   columns are shimmed; a book missing any of the other six fails at compile time.
   All six exist in all three current books — **VERIFIED**, the query runs — so this
   is a landmine for a future 4th company, not a live fault.

7. **The query reads all three schemas by name** inside the `UDFX` shim, so the
   HANA user needs `SELECT` on all three even to run one book. Fine today; it would
   break for a single-schema user. **INFERRED**, not tested with a restricted user.

8. **`CARGO CLEARING AGENCY GUJ` (₹21.54 L, Oil) is in** on the `%CARGO%` token
   while `SHREE SAI CLEARINGS AND FORWARDING` is out. Both are customs clearing
   agents. Mildly inconsistent; ₹21.54 L on ₹1 802 L, and I chose not to add a
   `CLEARING` token because it would drag the ocean-freight family in with it.
