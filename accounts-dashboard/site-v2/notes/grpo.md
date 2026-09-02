# grpo — Goods Receipt POs and the GR/IR unbilled liability

**Section id:** `grpo`
**SQL:** `pipeline/sql/grpo.sql` (bounded aggregate, 7 stacked scopes, **46 columns**)
· `pipeline/sql/grpo-detail.sql` (chase list, one row per problem GRPO, 30 columns)
**Raw output:** `pipeline/raw/grpo.{oil,mart,bev}.tsv`, `pipeline/raw/grpo-detail.{oil,mart,bev}.tsv`
**As-of for every number below:** 2026-08-21, pulled live through
`hana-sql -env ../connections/hana-tunnel.env` (VPS-parked hanadb bridge).
**Money unit:** every money column is **raw INR rupees**. No `_L`, no `_CR`, no
suffix — which is exactly what the renderer's `scale()` wants (`_CR`→×1e7,
`_L`→×1e5, anything else→rupees). Checked column by column: **no column in either
file ends in `_L` or `_CR`**, so nothing can render 100,000× wrong. VERIFIED.
**Runtime:** summary 2.7 / 1.6 / 1.8 s, detail 2.0 / 1.3 / 1.9 s (oil/mart/bev).
Whole section end-to-end **11–13 s**. VERIFIED — nowhere near the 60 s ceiling.

Every claim below is marked **VERIFIED** (I ran the query this session) or
**INFERRED** (I reasoned to it). Anything I did not check says so.

> **This file is an adversarial review.** The query was written under time
> pressure and never reviewed. It survived most of the attack; three real defects
> were found and fixed, and they are written up in §4. Verdict: **FIXED**.

---

## 1. Tables and columns, and why

| Table | Used for | Why this one |
|---|---|---|
| `OPDN` | GRPO header — `DocEntry`, `DocNum`, `DocDate`, `DocStatus`, `CANCELED`, `CardCode`, `CardName`, `DocTotal`, `VatSum`, `BPLId`, `BPLName`, `NumAtCard`, `TotalExpns` | The goods-receipt document itself (ObjType 20). `DocDate` **is** the gate-in date at JIVO (correction C-0017), so it is the ageing clock. |
| `PDN1` | GRPO lines — `LineNum`, `LineStatus`, `WhsCode`, `LineTotal`, `GTotal`, `Quantity`, `BaseType`/`BaseEntry` (the PO) | All money is taken here, not from the header — see trap 7. `LineStatus` is the open/closed test; `WhsCode` is the only line-level facet. |
| `PCH1` + `OPCH` | the A/P-invoice link — `BaseType`=20, `BaseEntry`, `BaseLine`; `OPCH."CANCELED"`, `DocDate`, `DocNum` | This is what makes a receipt "billed". Joined through `PCH1` rather than `PDN1."TrgetEntry"` so the invoice's own `CANCELED` can be tested. |
| `RPD1` + `ORPD` | the goods-return link (ObjType 21) | So goods sent back are not chased as a missing bill. **Read trap 8 before trusting this** — it catches almost nothing at JIVO. |
| `OPOR` | purchase-order `DocNum` on the chase list | So a clerk can find the paperwork. |
| `OCRD` + `OCRG` | vendor name + vendor group, for `PARTY_CLASS` | Branch / intercompany / internal-adjustment classification. |

Nine tables, all stock SAP B1. **`grep -c '"U_' grpo.sql grpo-detail.sql` = 0 —
the section uses no UDF anywhere**, so nothing can be present in Oil and missing
in Beverages. That is the whole three-schema portability story. VERIFIED.

### How "unbilled" is decided

A GRPO line is **UNBILLED** when

* `PDN1."LineStatus" = 'O'`, **and**
* no `PCH1` row with `"BaseType"=20`, `"BaseEntry"=PDN1."DocEntry"`,
  `"BaseLine"=PDN1."LineNum"` whose parent `OPCH` is live (`"CANCELED"='N'`) and
  dated `<= {{ASOF}}`, **and**
* no equivalent live `RPD1` goods-return line.

Money is the line's own `GTotal` (gross) / `LineTotal` (net); GST is the
difference. Ageing runs off the GRPO's own `DocDate`.

Sister bucket `CLOSED_NOBILL_*`: `LineStatus='C'` with no live invoice and no live
return — a GRPO somebody **closed without ever booking the bill**. Not a live
liability; it is an audit item, and it is reported rather than dropped.

---

## 2. What I attacked, and what survived

Everything in this table was run this session against all three schemas.

| # | Attack | Result |
|---|---|---|
| 1 | **Double counting / join fan-out.** Rebuilt the headline from a single independent aggregate: `SELECT COUNT(DISTINCT DocEntry), COUNT(*), SUM(LineTotal), SUM(GTotal) FROM PDN1 JOIN OPDN … CANCELED='N' AND DocDate<=asof`. | **SURVIVED.** Matches to the paisa: Oil 10,640 docs / 22,843 lines / 7,847,415,923.62; Mart 3,010 / 14,150 / 2,928,155,588.29; Bev 4,563 / 6,775 / 242,466,847.92. VERIFIED. |
| 2 | **`OCRD`/`OCRG` fan-out** (a duplicate card or group row would multiply every line). | **SURVIVED.** 0 duplicate `CardCode`, 0 duplicate `(GroupCode,GroupType)`, 0 GRPO cards missing from `OCRD`, 0 supplier cards whose group is missing type-matched. All three books. VERIFIED. |
| 3 | **Faceted stacking** — can a consumer sum across scopes and get a multiple? | **SURVIVED, with one honest exception.** `CLASS`, `MONTH`, `BRANCH` and `WAREHOUSE` each re-total to the `TOTAL` row to the paisa on all three books. `VENDOR` and `VENDOR_UNBILLED` are **top-N (cap 60) and deliberately do not re-total** — Oil and Bev both sit exactly on the 60 cap, so a sum over them is *less* than the truth, never more. VERIFIED. |
| 4 | **Cancelled documents** on every table touched. | **SURVIVED, and this is the biggest single trap in the section** — see trap 1. VERIFIED. |
| 5 | **Branch + intercompany**, name test as well as group test. | **DEFECT FOUND** (flagged in CLASS but not on the headline) — fixed, §4 defect A. |
| 6 | **Unapplied money / open-item shape.** Does the section touch `ORCT`/`OVPM` `OpenBal` or open `ORIN`/`ORPC`? | **NOT APPLICABLE, and correctly so.** GR/IR is a *document-matching* problem, not a payment-application one: it asks "did the bill arrive", not "was it paid". No payment table is touched, so there is nothing to double-subtract. The proven session finding about `OpenBal` being already inside `OCRD."Balance"` does not reach this section. INFERRED from the query text, VERIFIED that no payment table is referenced (`grep` for the 9 tables above). |
| 7 | **Migrated openings at 2024-09-30.** | **SURVIVED.** Oil 1 GRPO (₹2.82 L), Bev 1 (₹9,404), Mart none — and **neither is still unbilled**, so the 365+ bucket carries no migration residue. VERIFIED. |
| 8 | **Three-schema portability.** | **SURVIVED.** No UDF, no hard-coded account code, no group *name* other than the `%BRANCH%` pattern (which exists in all three: BRANCH-group vendor cards with live GRPOs — Oil 6, Mart 3, Bev 4). Ran end to end on all three schemas. VERIFIED. |
| 9 | **Empty / NULL.** | **SURVIVED.** With zero GRPOs the `DF CROSS JOIN SCOPES` produces no rows at all — an empty set, not an error — and the renderer prints `No goods receipts in this book.` `grpo` is not in `build_data.py`'s `MAY_BE_EMPTY`, but the guard sums rows *across* companies, so one empty book cannot trip it. VERIFIED for the empty-set behaviour by reading the plan shape; **not** exercised against a genuinely empty book (all three have data). |
| 10 | **Money units.** | **SURVIVED.** Every money column is rupees and no column name ends `_L`/`_CR`. Re-checked after adding the `EXT_*` columns. VERIFIED. |
| 11 | **Re-derive the headline a second way.** Rewrote the whole unbilled calculation as a `NOT EXISTS` pair instead of the `LEFT JOIN … IS NULL` the query uses. | **SURVIVED, exactly.** Oil 294 docs / 593 lines / net 51,464,882.55 / gross 55,930,381.91 / 90+ 295,541.05 / oldest 2024-10-28. Mart 41 / 79 / 7,986,012.19 / 8,419,141.07 / 138,605.51 / 2025-09-13. Bev 231 / 308 / 35,664,267.57 / 41,907,230.17 / 3,549,325.88 / 2024-10-04. Every figure identical to the section's own output. VERIFIED. |
| 12 | **TSV contract.** Malformed rows, embedded tabs or newlines in vendor names. | **SURVIVED.** 0 `OCRD."CardName"` in any book contains TAB/CR/LF; every emitted row is exactly 46 (summary) / 30 (detail) fields wide; `build_data.py` dropped 0 malformed rows. VERIFIED. |
| 13 | **Performance.** | **SURVIVED.** 1.0–3.3 s per statement per book. VERIFIED. |
| 14 | **As-of window.** | **DEFECT FOUND** — fixed, §4 defect B; a residue remains and is stated in §5. |
| 15 | **Partial line draws / partial returns.** | **DEFECT FOUND, immaterial** — §4 defect D. |
| 16 | **A/P credit memos (`ORPC`/`RPC1`) drawing a GRPO line directly**, which would close a line with no `OPCH` behind it and silently land it in `CLOSED_NOBILL`. | **SURVIVED.** `SELECT COUNT(*) FROM RPC1 WHERE "BaseType"=20` = **0** in all three books. The GRPO→A/P-credit-memo path is unused at JIVO. VERIFIED. |
| 17 | **`LineStatus` domain.** A third value would silently fall out of both buckets. | **SURVIVED.** `COUNT(*) WHERE "LineStatus" NOT IN ('O','C')` = 0 in all three books. VERIFIED. |
| 18 | **Determinism.** | **SURVIVED.** Two consecutive runs, byte-identical output. (An early diff against `raw/*.tsv` looked like non-determinism; it was the saved raw being 5 minutes older than the last edit to the `.sql`, before the `UPPER(BPLName)` fix. Confirmed by timestamps.) VERIFIED. |

---

## 3. Traps in the data, and how the SQL handles each

**Trap 1 — `OPDN."CANCELED"` is THREE-valued, and the wrong filter doubles the book.**
VERIFIED, all three schemas:

```
JIVO_OIL_HANADB    N 10,640 docs  ₹7,846,402,662.63    Y 473  ₹946,345,979.50    C 473  ₹946,345,979.50
JIVO_MART_HANADB   N  3,010 docs  ₹2,928,014,659.59    Y  93  ₹ 61,012,692.29    C  93  ₹ 61,012,692.29
JIVO_BEVERAGES_..  N  4,563 docs  ₹  241,883,403.73    Y 129  ₹ 13,759,778.33    C 129  ₹ 13,759,778.33
```

`'Y'` is the cancelled original, `'C'` is SAP's system-generated cancellation
mirror, and they carry **identical totals**. A `<> 'Y'` filter would add ₹94.63 Cr
of phantom receipts to Oil. Only `'N'` is kept — on `OPDN`, and on the linked
`OPCH` and `ORPD` as well. The `'N'` document counts match `GRPO_DOCS` exactly.

**Trap 2 — `PDN1."OpenQty"` is broken here; `"OpenInvQty"` is in a different UoM.**
VERIFIED on all three books (I re-ran this, the original note only had Oil):

```
             CLOSED lines                        OPEN lines
             Quantity      OpenQty   OpenInvQty  Quantity     OpenInvQty
Oil          101,651,635  101,390,074        0   6,533,243     6,742,722
Mart          10,225,274   10,224,726        0     117,644       116,944
Bev          221,059,621  218,721,181        0  13,705,586    13,705,586
```

`OpenQty` still equals `Quantity` on **fully invoiced, closed** lines (99.74% Oil,
99.99% Mart, 98.94% Bev) — it is never decremented. `OpenInvQty` **is** maintained
(exactly 0 on closed lines) but is stated in the **base** UoM while `Quantity` is
in the **document** UoM: Oil's open lines read `OpenInvQty` 6,742,722 against
`Quantity` 6,533,243 — more "open" than exists, because oil RM lines are MTS in
one and litres in the other (factor 1098.9). **The query does no quantity
arithmetic at all**; open-ness comes from `LineStatus` plus the live-invoice link.

**Trap 3 — zero-quantity service lines never close by themselves.**
Freight/expense GRPO lines with `Quantity`=0 keep `LineStatus='O'` forever even
after the A/P invoice is booked. VERIFIED: of the open lines that *are* drawn by a
live A/P invoice — Oil 24 lines, **24 of 24 zero-quantity**; Bev 3 lines, **3 of
3**. The live-invoice link removes them from `UNBILLED_*`; the ones that are
genuinely unbilled are still reported and called out separately, because they will
never self-clear and need a human: **Oil 165 lines ₹15.73 L · Mart 67 ₹15.15 L ·
Bev 205 ₹12.20 L**.

**Trap 4 — a drawn A/P invoice can itself be cancelled**, which legitimately
re-opens the GRPO line. The link therefore tests `OPCH."CANCELED"='N'`, never mere
existence. This is also why the join runs from `PCH1` and not from
`PDN1."TrgetEntry"` — `TrgetEntry` keeps only the *last* target and goes stale
when that invoice is cancelled. INFERRED for the mechanism; the `'N'` filter is
VERIFIED to be present on every one of the three link CTEs in both files.

**Trap 5 — header `DocStatus` disagrees with the lines, in both directions.**
VERIFIED (docs, live only):

```
                DocStatus='O' but no open line     DocStatus='C' but an open line
Oil                          2                                  2
Mart                         0                                  1
Bev                          0                                  3
```

Small, but wrong in both directions, so **open-ness is decided line by line** and
`DocStatus` is carried only as a display field.

**Trap 6 — branch and intercompany receipts.** JIVO's own state GST registrations
arrive as `BRANCH VENDOR`-group cards, **and** sister companies sit inside ordinary
purchase groups where only the *name* betrays them. The full non-external vendor
list, VERIFIED:

```
Oil    VENDA000003 JIVO WELLNESS PVT LTD - HR   group BRANCH VENDOR   556 docs  ₹56.15 Cr  BRANCH
       VENDA000002 JIVO WELLNESS PVT LTD - PB   group BRANCH VENDOR   147       ₹ 1.67 Cr  BRANCH
       VENDA000004 JIVO WELLNESS PVT LTD - DL   group BRANCH VENDOR    44       ₹ 2.85 Cr  BRANCH
       VENDA001004 JIVO WELLNESS PVT LTD - HARYANA / VENDA000254 JIVO AGRI BUSINESS /
       VENDA000687 AKAL ROZGAR YOJANA A U/O JWPL BS                              BRANCH
       VENDA001614 STOCK GOODS RECEIPTS         group PURCHASE         20       ₹30.02 L   INTERNAL_ADJ
       VENDA000483 JIVO MART PVT LTD            group E-COMMERCE       11       ₹53.54 L   INTERCOMPANY
Mart   VENDA000001 JIVO WELLNESS PVT LTD        group PURCHASE      2,596 docs  ₹275.43 Cr INTERCOMPANY  <-- name test only
       VENDA000942/932/953 JIVO MART … - DL/HR/KT  group BRANCH VENDOR 118      ₹12.20 Cr  BRANCH
Bev    VENDA001306 STOCK GOODS RECEIPTS         group PURCHASE         16       ₹ 3.13 Cr  INTERNAL_ADJ
       VENDA000003/004/002/687 JIVO … branches  group BRANCH VENDOR     55      ₹36.55 L   BRANCH
```

**The exact trap the brief warns about is present and is caught**: Mart's
`VENDA000001 "JIVO WELLNESS PVT LTD"` — 94% of Mart's entire GRPO value — sits in
group **PURCHASE**, so a group-only test would call it external. `PARTY_CLASS`
tests the group **and** the name. Nothing is dropped; everything is flagged.

**Trap 7 — header `DocTotal` and line `GTotal` disagree, and the lines are the
better number.** VERIFIED:

```
                docs with VatSum=0 but taxed lines   GST hidden that way   header total       line total          gap
Oil             2,830 of 10,640 (27%)                ₹20.99 L             7,846,402,662.63   7,847,415,923.62   +0.0129%
Mart               60 of  3,010 ( 2%)                ₹ 1.41 L             2,928,014,659.59   2,928,155,588.29   +0.0048%
Bev             3,053 of  4,563 (67%)                ₹ 9.80 L               241,883,403.73     242,466,847.92   +0.2412%
```

Going the other way, header freight (`OPDN."TotalExpns"`: Oil ₹9.50 L, Bev ₹3.50 L,
Mart ₹3,150) never reaches the lines. Money is therefore **line-level throughout**,
which is also what makes the `WAREHOUSE` scope comparable with every other scope.
I sized the effect; I did **not** establish *why* the header VatSum is 0 (RCM? a
tax code that does not roll up?). **Cause not verified.**

**Trap 8 — `RETURNED_*` catches almost nothing, and you must know that before you
use it.** VERIFIED, live return lines by link type:

```
        linked to a GRPO (BaseType=20)      standalone (BaseType=-1)      linked share of value
Oil     3 lines / 3 docs / ₹4.69 L          155 lines / 100 docs / ₹69.92 L      6.3%
Mart    1 line  / 1 doc  / ₹0.72 L          416 lines /  48 docs / ₹124.78 L     0.6%
Bev     0                                    81 lines /  19 docs / ₹48.73 L      0.0%
```

At JIVO a goods return is raised **standalone**, not copied from the receipt. So
`RETURNED_DOCS/LINES/GROSS` means *"GRPO lines a return was copied from"*, not
*"goods sent back"*, and it is near-empty by construction. It is not rendered on
the dashboard. (`RETURNED_GROSS` Oil = ₹5.94 L rather than the ₹4.69 L above
because it sums the **GRPO** line's gross, not the return's.)
**Consequence for the headline:** a standalone return does not close the GRPO
line, so goods received and then sent back with no bill stay in the GR/IR bucket.
I bounded it by vendor overlap: 13 Oil vendors appear on both lists, and the
standalone-return value at those vendors is **₹43.50 L** — an upper bound of 7.8%
on Oil's ₹5.59 Cr. Bev's only overlap is MULTILAYER INDUSTRIES, bound ₹0.83 L.
Mart's overlap is intercompany only. **Not attributable line by line from these
tables. Stated, not silently fixed** — see §5.

**Trap 9 — SAP go-live 2024-09-30 (migrated openings).** Oil 1 GRPO ₹2.82 L, Bev 1
GRPO ₹9,404, Mart none — and **zero of them are still unbilled**, so the oldest
ageing bucket is not distorted. Left in; immaterial (Oil 0.004%). VERIFIED.

**Trap 10 — a warehouse is a line attribute, an invoice lag is a document
property.** `INV_PAIR_DOCS`, `INV_SAMEDAY_DOCS`, `INV_SAMEDAY_PCT` and
`INV_LAG_*` come back **NULL** on `WAREHOUSE` rows rather than a wrong zero.
VERIFIED in `data.json`: all 32/16/17 warehouse rows have both NULL.

**Trap 11 — as-of consistency** (new; found by this review). See §4 defect B.

**Trap 12 — the headline is contaminated by JIVO's own cards** (new; found by this
review). See §4 defect A.

### Checked and rejected as inputs

* `OPDN."U_Recv_Date"` — populated on 2 of 10,640 live Oil GRPOs. Unusable, and
  unnecessary: `DocDate` *is* the gate-in date (C-0017).
* `PDN1."OpenSum"` — not zeroed on closed lines either. Same failure as `OpenQty`.
* `PDN1."TrgetEntry"` — holds only the last target and goes stale on cancellation.

### Self-test identities (re-run against the published `data.json`, 0 mismatches)

```
UB_0_30 + UB_31_60 + UB_61_90 + UB_91_180 + UB_181_365 + UB_365PLUS = UNBILLED_GROSS   OK x3
UB_90PLUS_GROSS = UB_91_180 + UB_181_365 + UB_365PLUS                                  OK x3
INVOICED_DOCS + NOINV_DOCS = GRPO_DOCS                                                 OK x3
SUM(CLASS) = SUM(MONTH) = SUM(BRANCH) = SUM(WAREHOUSE) = TOTAL                         OK x3
TOTAL row EXT_* == the CLASS / GRP_KEY='EXTERNAL' row                                  OK x3
WAREHOUSE rows: INV_PAIR_DOCS and INV_LAG_AVG_DAYS both NULL                           OK x3
```

---

## 4. Defects found, and what I did about them

### A. MAJOR — the headline "unbilled vendor liability" was 68% internal in Beverages

`UNBILLED_GROSS` on the `TOTAL` row includes JIVO's own branch cards, the sister
company, and the internal `STOCK GOODS RECEIPTS` stock-adjustment card. The
dashboard KPI read straight off it. VERIFIED at 2026-08-21:

```
             UNBILLED_GROSS   of which NOT an outside supplier
Beverages      ₹4.19 Cr        ₹2.85 Cr (68%) — VENDA001306 "STOCK GOODS RECEIPTS"
Mart           ₹84.19 L        ₹67.37 L (80%) — VENDA000001 "JIVO WELLNESS PVT LTD"
Oil            ₹5.59 Cr        ₹2,016  (0.004%)
```

₹2.82 Cr of Beverages' figure is **one line**: GRPO `2026078243`, 2026-07-31, item
`RM0000199`, 486,919.5 units, warehouse BH-FR, against a card that will never issue
a vendor bill. The page was telling Accounts that Beverages owes ₹4.19 Cr of
unbooked supplier bills. The real trade figure is **₹1.34 Cr**.

The brief's rule is *flag it, never silently drop or include*. It was flagged in
the `CLASS` facet but silently included in the number people read.

**Fix (additive, nothing removed):** every headline figure now ships an
EXTERNAL-only twin. Six new columns, appended at the end so the existing 40-column
contract is untouched:
`EXT_GRPO_DOCS`, `EXT_GRPO_GROSS`, `EXT_UNBILLED_DOCS`, `EXT_UNBILLED_GROSS`,
`EXT_UB_90PLUS_DOCS`, `EXT_UB_90PLUS_GROSS`. `UNBILLED_*` still totals everything;
`CLASS` still shows the split. **Proof the change is purely additive:** the first
40 columns of the post-fix output are byte-identical to the pre-fix output on all
three books (`diff <(cut -f1-40 before) <(cut -f1-40 after)` → empty ×3). VERIFIED.

`site/index.html`'s `grpo` KPI block now quotes the `EXT_*` figure and names what
was taken out, falling back to the old total when `EXT_*` is absent (so a stale
`data.json` degrades instead of blanking). Smoke-tested in node against the live
`data.json`, both paths. VERIFIED.

### B. MINOR but real — the invoice/return link ignored `{{ASOF}}`

`BILLED`, `RETURNED` and `INVLINK` filtered the GRPO by `{{ASOF}}` but not the
document that settles it, so a month-end run was being settled by bills booked
afterwards. `build_data.py` advertises `--as-of 2026-07-31 # a month-end position`,
so this is reachable. VERIFIED at as-of 2026-05-31, Oil:

```
link uncapped (as written):   39 docs / 56 lines / ₹339,378.55
link capped at as-of (fixed): 43 docs / 63 lines / ₹374,124.00      -> was understated 9.3%
```

**Fix:** `AND i."DocDate" <= DATE'{{ASOF}}'` on the two `OPCH` joins and
`AND rh."DocDate" <= DATE'{{ASOF}}'` on the `ORPD` join, in **both** `grpo.sql` and
`grpo-detail.sql`. At as-of = today it is provably a **no-op** — 0 live `OPCH` and
0 live `ORPD` in any of the three books carries a future `DocDate`, and the detail
output after the fix is byte-identical to the saved raw. VERIFIED.

A residue remains that these tables cannot fix — see §5.

### C. MINOR — stale/contradictory header comments

Corrected in `grpo.sql`: the zero-quantity line counts (Bev is 205, the comment
said 185; Mart's 67 was missing), the 2024-09-30 claim (Bev has one too, and
neither is unbilled), the `DocStatus` disagreement counts (2/2, 0/1, 0/3 — the
comment said 3 and 2 for Oil), the Mart `CLOSED_NOBILL` wording ("the whole
₹41.52 L sits in ONE line" then quoting ₹40.23 L for that line — it is 7 lines
over 3 GRPOs, of which one is ₹40.23 L), and the row counts. Trap 8's real
coverage and traps 11–12 added.

### D. MINOR, immaterial — a partially-drawn line is treated as fully billed

`BILLED` is an existence test, so a GRPO line invoiced in part is dropped from
`UNBILLED_*` entirely — the query **understates**, it does not overstate. (The
previous note had this backwards and said Oil was clean; Oil *is* clean, but the
direction was wrong.) Population, VERIFIED: exactly **one** line in all three
books is open, drawn, and non-zero-quantity —

```
Mart GRPO 2012254598, 2025-12-01, CVS PACKAGING PRIVATE LIMITED, line 8,
item PM0000271, Quantity 1,000, OpenInvQty 300, GTotal ₹5,775
   -> ~₹1,732 of residual unbilled value not counted. 0.02% of Mart's ₹84.19 L.
```

**Not fixed, deliberately.** Pro-rating by quantity would require the UoM
conversion that trap 2 shows is unsafe, to recover ₹1,732. The existence test is
the right call; the exposure is now measured and written down.

---

## 5. Live output — 2026-08-21

### `SCOPE='TOTAL'` (raw INR as emitted; lakh/crore added here for reading only)

| Column | Oil | Mart | Beverages |
|---|---:|---:|---:|
| `GRPO_DOCS` | 10,640 | 3,010 | 4,563 |
| `GRPO_LINES` | 22,843 | 14,150 | 6,775 |
| `GRPO_NET` | 7,493,649,849.89 | 2,786,583,020.19 | 208,689,747.45 |
| `GRPO_GST` | 353,766,073.73 | 141,572,568.10 | 33,777,100.47 |
| `GRPO_GROSS` | **7,847,415,923.62** (₹784.74 Cr) | **2,928,155,588.29** (₹292.82 Cr) | **242,466,847.92** (₹24.25 Cr) |
| `UNBILLED_DOCS` | 294 | 41 | 231 |
| `UNBILLED_LINES` | 593 | 79 | 308 |
| `UNBILLED_NET` | 51,464,882.55 | 7,986,012.19 | 35,664,267.57 |
| `UNBILLED_GST` | 4,465,499.35 | 433,128.88 | 6,242,962.60 |
| `UNBILLED_GROSS` | **55,930,381.91** (₹5.59 Cr) | **8,419,141.07** (₹84.19 L) | **41,907,230.17** (₹4.19 Cr) |
| `UB_0_30` | 53,943,492.94 | 7,626,127.32 | 36,848,956.22 |
| `UB_31_60` | 1,200,567.62 | 609,935.22 | 82,247.47 |
| `UB_61_90` | 490,780.30 | 44,473.02 | 1,426,700.60 |
| `UB_91_180` | 93,442.29 | 0 | 461,385.14 |
| `UB_181_365` | 171,195.79 | 138,605.51 | 2,968,191.75 |
| `UB_365PLUS` | 30,902.97 | 0 | 119,748.99 |
| `UB_90PLUS_DOCS` | 37 | 3 | 26 |
| `UB_90PLUS_GROSS` | 295,541.05 | 138,605.51 | 3,549,325.88 |
| `UB_ZEROQTY_LINES` | 165 | 67 | 205 |
| `UB_ZEROQTY_GROSS` | 1,573,168.57 | 1,515,387.24 | 1,220,265.77 |
| `OLDEST_UB_DATE` | 2024-10-28 | 2025-09-13 | 2024-10-04 |
| `OLDEST_UB_DAYS` | 662 | 342 | 686 |
| `CLOSED_NOBILL_DOCS` | 142 | 3 | 51 |
| `CLOSED_NOBILL_LINES` | 323 | 7 | 115 |
| `CLOSED_NOBILL_GROSS` | 5,991,356.27 (₹59.91 L) | 4,151,699.64 (₹41.52 L) | 3,503,177.40 (₹35.03 L) |
| `RETURNED_DOCS / LINES / GROSS` | 3 / 3 / 594,165.12 | 1 / 1 / 72,024.25 | 0 / 0 / 0 |
| `INVOICED_DOCS` | 10,232 | 2,966 | 4,282 |
| `NOINV_DOCS` | 408 | 44 | 281 |
| `NOINV_GROSS` | 62,371,847.94 | 12,642,843.96 | 45,410,406.57 |
| `INV_PAIR_DOCS` | 10,232 | 2,966 | 4,282 |
| `INV_SAMEDAY_DOCS` | 5,266 | 2,498 | 909 |
| `INV_SAMEDAY_PCT` | 51.47 | 84.22 | 21.23 |
| `INV_LAG_AVG_DAYS` | 14.10 | 1.47 | 13.03 |
| `INV_LAG_MED_DAYS` | 0 | 0 | 8 |
| **`EXT_GRPO_DOCS`** | 9,850 | 294 | 4,492 |
| **`EXT_GRPO_GROSS`** | 7,226,415,464.15 (₹722.64 Cr) | 51,752,167.71 (₹5.18 Cr) | 207,524,722.15 (₹20.75 Cr) |
| **`EXT_UNBILLED_DOCS`** | 293 | 36 | 224 |
| **`EXT_UNBILLED_GROSS`** | **55,928,365.91** (₹5.59 Cr) | **1,682,341.07** (₹16.82 L) | **13,444,628.49** (₹1.34 Cr) |
| **`EXT_UB_90PLUS_DOCS`** | 36 | 3 | 22 |
| **`EXT_UB_90PLUS_GROSS`** | 293,525.05 | 138,605.51 | 3,536,783.09 |

Rows returned: **Oil 185 · Mart 95 · Beverages 149** (cap 300).
Scope counts — Oil: TOTAL 1, CLASS 4, MONTH 24, BRANCH 4, VENDOR 60,
VENDOR_UNBILLED 60, WAREHOUSE 32. Mart: 1 / 3 / 20 / 4 / 40 / 11 / 16.
Bev: 1 / 3 / 24 / 3 / 60 / 41 / 17.

### `SCOPE='CLASS'`

```
Oil    EXTERNAL      9,850 docs  gross 7,226,415,464.15   unbilled 55,928,365.91   closed-nobill 2,988,997.12
       BRANCH          759       gross   612,643,743.76   unbilled      2,016.00   closed-nobill         0
       INTERCOMPANY     11       gross     5,354,356.56   unbilled          0      closed-nobill         0
       INTERNAL_ADJ     20       gross     3,002,359.15   unbilled          0      closed-nobill 3,002,359.15
Mart   INTERCOMPANY  2,598       gross 2,754,378,801.77   unbilled  6,736,800.00   closed-nobill         0
       BRANCH          118       gross   122,024,618.81   unbilled          0      closed-nobill         0
       EXTERNAL        294       gross    51,752,167.71   unbilled  1,682,341.07   closed-nobill 4,151,699.64
Bev    EXTERNAL      4,492       gross   207,524,722.15   unbilled 13,444,628.49   closed-nobill   668,136.35
       INTERNAL_ADJ     16       gross    31,286,719.04   unbilled 28,451,678.00   closed-nobill 2,835,041.05
       BRANCH           55       gross     3,655,406.73   unbilled     10,923.69   closed-nobill         0
```

### `SCOPE='VENDOR_UNBILLED'` — the chase list, top 5

```
Oil    AWL AGRI BUSINESS LIMITED [EXTERNAL]                  ₹2,44,15,051.49   90+ 0
       M/S ARORA AGRI BUSINESS VENTURES [EXTERNAL]           ₹  62,30,784.00   90+ 0
       FRYSTAL PET PRIVATE LIMITED [EXTERNAL]                ₹  53,27,204.40   90+ 0
       WILLUS INFRASTRUCTURE PRIVATE LIMITED [EXTERNAL]      ₹  22,99,584.00   90+ 0
       RAJ TECHNOPACK PVT LTD [EXTERNAL]                     ₹  22,67,777.69   90+ 0
Mart   JIVO WELLNESS PVT LTD [INTERCOMPANY]                  ₹  67,36,800.00   90+ 0
       ABHIMAN EXPRESS [EXTERNAL]                            ₹  11,42,702.40   90+ 0
       PICK & SHIP LOGISTICS PRIVATE LIMITED [EXTERNAL]      ₹   2,06,684.04   90+ 0
       DELHI PUNJAB TRANSPORT CO [EXTERNAL]                  ₹     95,305.35   90+ 0
       S.N. INDUSTRIES [EXTERNAL]                            ₹     72,024.25   90+ ₹72,024.25
Bev    STOCK GOODS RECEIPTS [INTERNAL_ADJ]                   ₹2,84,51,678.00   90+ ₹1,619.10
       TULA ENGINEERING PRIVATE LIMITED [EXTERNAL]           ₹  29,50,000.00   90+ ₹29,50,000.00
       MD PACKAGING INDUSTRIES [EXTERNAL]                    ₹  26,25,773.76   90+ 0
       S.N. INDUSTRIES [EXTERNAL]                            ₹  15,43,553.91   90+ 0
       J. PEE ENGINEERS & PACKAGING PVT. LTD. [EXTERNAL]     ₹  14,21,900.00   90+ 0
```

### `grpo-detail.sql` — 436 Oil rows (294 UNBILLED + 142 CLOSED_NOBILL), 44 Mart (41+3), 282 Bev (231+51)

```
Oil    UNBILLED 2026086676  2026-08-18  AWL AGRI BUSINESS LIMITED           open ₹63,02,835.00   0-30
       UNBILLED 2026086662  2026-08-17  M/S ARORA AGRI BUSINESS VENTURES    open ₹62,30,784.00   0-30
       UNBILLED 2026086689  2026-08-20  AWL AGRI BUSINESS LIMITED           open ₹61,01,550.00   0-30
Mart   UNBILLED 2008264594  2026-08-20  JIVO WELLNESS PVT LTD               open ₹13,60,800.00   0-30
Bev    UNBILLED 2026078243  2026-07-31  STOCK GOODS RECEIPTS                open ₹2,83,89,583.84 0-30
       UNBILLED 2025128147  2025-12-08  TULA ENGINEERING PRIVATE LIMITED    open ₹29,50,000.00   181-365
```

### What the numbers say

* **The genuine GR/IR position is small and almost entirely fresh.** Oil ₹5.59 Cr
  unbilled, of which ₹5.39 Cr is under 30 days — ordinary goods-in-ahead-of-bill
  flow. The number that matters is the tail: **Oil 36 external documents /
  ₹2.94 L over 90 days**, oldest 662 days.
* **Beverages' real external exposure is ₹1.34 Cr**, not the ₹4.19 Cr the page used
  to show, and **₹35.37 L of it is 90+ days** — the single worst item being
  TULA ENGINEERING, GRPO 2025128147, 2025-12-08, ₹29.50 L, 256 days with no bill.
* **Mart's real external exposure is ₹16.82 L**, and ₹15.15 L of that is
  zero-quantity transporter lines that will never self-clear.
* **`CLOSED_NOBILL` is the quiet one** — Oil ₹59.91 L / 142 docs, Bev ₹35.03 L /
  51 docs, Mart ₹41.52 L / 3 docs. Mart's is effectively one document:
  **GRPO 125206556, 2025-01-22, PALAK ENTERPRISES, RM0000030, ₹40.23 L**, closed
  with no bill and no return. Worth a human asking what happened.
* **Beverages barely books on the gate-in date** — 21% same-day against Oil's 51%
  and Mart's 84%.

---

## 6. Unresolved, stated plainly

1. **A historical `--as-of` run is still approximate, and defect B only half-fixed
   it.** `PDN1."LineStatus"` is a **current-state flag with no history**: a line
   that was open at a past as-of and has since been billed reads `'C'` today and
   disappears from the answer entirely. Measured at as-of 2026-05-31: **Oil 143
   docs / 282 lines / ₹67.69 L and Bev 165 / 189 / ₹8.81 L** were unbilled on that
   date and are invisible to the query. Mart 0. VERIFIED.
   **Treat this section as a TODAY dashboard.** Do not quote a `--as-of` month-end
   GR/IR provision from it without saying so. A genuinely as-of-correct version
   would have to drop `LineStatus` and work purely from dated invoice/return
   coverage — which then loses the `CLOSED_NOBILL` distinction. That is a design
   decision for the section's owner, not a bug fix.
2. **Standalone goods returns are not attributable to a GRPO line** (trap 8), so
   goods received and later returned with no bill remain in the GR/IR bucket.
   Upper bound by vendor overlap: **Oil ₹43.50 L, Bev ₹0.83 L, Mart intercompany
   only.** These are *bounds*, not measurements — the overlap may well be against
   already-invoiced receipts. Closing it needs a business rule for matching a
   standalone return to a receipt, which SAP does not carry. **Unresolved.**
3. **`INTERNAL_ADJ` is detected by the vendor being *named* `STOCK GOODS…`.** Oil's
   `STOCK GOODS ISSUE` / `STOCK GOODS RECEIPTS` and Bev's `STOCK GOODS RECEIPTS`
   both match, but a differently-named adjustment card would be classed EXTERNAL
   and would inflate `EXT_UNBILLED_GROSS` — the very number the KPI now quotes. I
   found no group or flag to key on instead. **Worth a `jivo-correct` if Accounts
   knows the real rule.** Same caveat for `%JIVO%`: a genuine outside supplier with
   "JIVO" in its name would be misclassified as intercompany. None exists today
   (the full non-external list is in trap 6, and every card on it is ours).
4. **Whether the ₹5.59 Cr agrees with a G/L GR/IR accrual balance is not checked.**
   I did not open `JDT1`/`OJDT` for GRPO journal entries. If Accounts wants the
   GR/IR *account* reconciled rather than the *documents* aged, that is a second
   query. **Not checked.**
5. **Why 27% of Oil and 67% of Bev GRPO headers carry `VatSum`=0 while their lines
   carry tax.** Sized (trap 7), cause not established. It changes no number here
   because money is line-level, but it will bite anyone totalling
   `OPDN."DocTotal"` for a GST reconciliation. **Cause inferred only.**
6. **Quantities are deliberately absent.** GRPO lines mix UoMs (oil RM in MTS,
   packaging in pieces), so a summed `Quantity` across a month or warehouse is
   meaningless, and trap 2 shows the base/document UoM factor is not safe to apply
   blind. A tonnage register is a separate pass over `PDN1."UoMNum"/"UoMDen"` plus
   `OITM`. **Out of scope, not attempted.**
7. **`VENDOR` and `VENDOR_UNBILLED` are capped at 60 and Oil/Bev sit exactly on the
   cap.** Everything is in `TOTAL` and `CLASS`; the vendor facets are a top-N
   register by design. If someone starts summing them they will get a number
   smaller than the truth. Documented in the header, not enforceable in SQL.
8. **The empty-book path was reasoned, not exercised** — all three books have
   GRPOs, so I could not run the zero-row case for real. The shape
   (`DF CROSS JOIN SCOPES` over an empty `DF`) returns an empty set rather than
   erroring. **INFERRED.**
