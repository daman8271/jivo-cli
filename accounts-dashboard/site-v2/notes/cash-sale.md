# cash-sale — verification note

**Section id:** `cash-sale` · **SQL:** `pipeline/sql/cash-sale.sql` (no `-detail` companion)
**Reviewed:** 2026-08-21, as-of `2026-08-21`, all three books, live HANA via the home bridge.
**Verdict: FIXED.** Six defects found, six fixed. SQL now runs clean on all three
schemas and end-to-end through `build_data.py --only cash-sale`.

Every claim below is tagged **VERIFIED** (I ran the query and read the rows) or
**INFERRED** (I reasoned it and did not, or could not, prove it).

---

## 1. What the section means

**VERIFIED.** At JIVO "cash sale" is a **sales channel** (counter / walk-in /
no-credit), **not a tender type**. It is carried by dedicated customer cards that
post to the dedicated receivables control account **1101014 SUNDRY DEBTORS CASH
SALE**.

Proof I ran: a `JDT1` sweep of account 1101014 grouped by `"ShortName"` returns
*exactly* the card list the scope CTE derives from `OCRD` — nobody else posts
there, in any of the three books.

```
Oil   1101014  CUSTA000238 CASH SALE DL              53 lines  DR 2,441,924  CR 2,441,922
               CUSTA000025 HARPREET SINGH CASH SALE 1232       DR 1,080,304  CR 1,071,973
               CUSTA000893 CASH SALE PB                2       DR    56,750  CR    56,750
               CUSTA000886 KAMALPREET SINGH (CASH SALE) 8       DR     7,970  CR    12,782
Mart  1101014  (account exists, zero lines)
Bev   1101014  CUSTA000238 CASH SALE DL             119        DR 4,865,061  CR 5,962,900
               CUSTA000997 KAMALJEET CASH SALE J3    96        DR   128,893  CR   128,893
               CUSTA000881 HARPREET SINGH CASH SALE 112        DR    62,806  CR    58,460
               CUSTA000025 CASH SALE FACTORY          9        DR    22,159  CR    15,120
```

Because two cash cards sit on *other* control accounts (Oil `CUSTA000250` ONLINE
CASH SALE WEBSITE → 1101005 E-COM, `CUSTA001015` KAMALJEET J3 → 1101008 CALL
CENTRE), scope = **control account 1101014 OR the name phrase 'CASH SALE'**, the
union of both. **VERIFIED** against the full card list in each book.

A second, different thing — **physical cash tendered** on customer receipts
(`ORCT."CashSum"`) — is kept as a clearly separated alternative definition
(sections `6_TENDER_MONTH`, `9_TOTAL C/D`). It is *not* the register: it is cash
collected against ordinary credit sales by route salesmen. **VERIFIED** (the
payer cards are ordinary "DEL …" trade customers, not the cash-sale cards).

---

## 2. Tables and columns used, and why

| Table | Columns | Why |
|---|---|---|
| `OCRD` | `CardCode, CardName, CardType, GroupCode, DebPayAcct, validFor, Balance` | The scope. `DebPayAcct` is the control-account link (the actual marker); `CardName` catches the two cards on other control accounts; `Balance` is JIVO's ground truth for what a party owes (+DR / −CR). Master, so it survives renames. |
| `OCRG` | `GroupCode, GroupType, GroupName` | Branch test `'%BRANCH%'` and the group label in `ROW_NOTE`. |
| `OACT` | `AcctCode, AcctName, Postable, FatherNum` | Resolves 1101014 by NAME (`'%DEBTORS CASH SALE%'`), and the cash tills as the postable children of the non-postable parent `CASH IN HAND`. No account code is hard-coded. |
| `OINV` | `DocEntry, DocDate, CardCode, BPLId, BPLName, DocTotal, VatSum, DocStatus, PaidToDate, CANCELED` | The register. Turnover = `DocTotal − VatSum` per the JIVO definition. |
| `ORIN` | same shape | Credit notes, subtracted from turnover. |
| `INV1` / `RIN1` | `DocEntry, WhsCode` | The dominant-warehouse bucket. One bucket per document — never joined row-for-row, so it cannot fan. |
| `OWHS` | `WhsCode, WhsName` | Warehouse label. |
| `OBPL` | `BPLId, BPLName` | Branch label. **Master**, deliberately, not the per-document `OINV."BPLName"` snapshot — see T9. |
| `ORCT` | `DocDate, CardCode, CashSum, OpenBal, DocType, Canceled` | Alternative "cash tendered" definition, and `OpenBal` as the unapplied-money diagnostic. |
| `JDT1` | `Account, RefDate, Debit, Credit, ShortName, IntrnMatch, TransType` | GL cross-check on the tills and the AR control account. |

**No UDFs anywhere** (`U_…`), so nothing can be present in Oil and missing in
Beverages. **VERIFIED** by reading the SQL and by running it on all three schemas.

---

## 3. Defects found and fixed

### D1 — the breakdowns did not add up to the headline (major, FIXED)
**VERIFIED.** `3_BRANCH`, `4_WAREHOUSE` and `5_CUSTOMER` silently *included* the
35 migrated go-live openings that `9_TOTAL` *excluded*, and carried no tag saying
so. On Oil the customer table added to **₹38,00,716 of turnover against a
₹13,58,792 headline — 2.8×**. An Accounts reader adding the breakdown got a
number 2.8 times the register.

Fix: the three breakdowns are now `TAG = 'REAL'` only, so every cut of the
register reconciles to the same headline, and the openings get their own explicit
total row `9_TOTAL B MIGRATED_OPENINGS` (₹24,41,924, card named in `ROW_NOTE`).
They stay visible in `2_MONTH` under their own `ROW_KEY '2024-09 (opening)'`.

After: Oil `2_MONTH`(REAL) = `3_BRANCH` = `4_WAREHOUSE` = `5_CUSTOMER` =
`9_TOTAL A` = 1,094 invoices / ₹14,38,780 gross / ₹13,58,792.41 turnover /
₹3,31,174.70 open. **VERIFIED** by summing the emitted TSV.

### D2 — duplicate `ROW_KEY` in Beverages `3_BRANCH` (major, FIXED)
**VERIFIED.** `OINV."BPLName"` is a per-document snapshot. Bev branch 2 is stored
as `'FACTORY'` on 97 invoices and `'Factory'` on 7, and grouping by
`(BPLId, BPLName)` emitted **two rows both keyed `'2'`** — breaking the section's
own "one row per (SECTION, ROW_KEY)" contract and showing the branch twice.

Fix: group on `"BPLId"` only; label from `OBPL` (master). Bev branch 2 is now one
row, 104 invoices, ₹1,08,405. **VERIFIED** — a duplicate-key check over the
emitted rows now returns none for all three books.

### D3 — Beverages/Oil "open" is not a receivable, and nothing said so (major, FIXED)
**VERIFIED, and this is the one that would have cost money.** Cash-sale invoices
stay `DocStatus='O'` forever because settlement is a lump on-account receipt that
is never internally applied. `JDT1."IntrnMatch" = 0` on **100%** of the 1101014
lines (Oil 1,295 of 1,295; Bev 336 of 336) — SAP's internal reconciliation is
simply unused here, exactly as the customer-ageing work found elsewhere.

Bev `CUSTA000238` CASH SALE DL:

| measure | value |
|---|---|
| "open" invoices (`DocTotal − PaidToDate`, `DocStatus='O'`) | **₹43,55,961** |
| unapplied receipts (`ORCT."OpenBal"`) | **₹57,86,550** |
| **`OCRD."Balance"` — what is actually owed** | **−₹10,97,839 (a CREDIT)** |

The old output showed `OPEN_INR 43,67,346` on a column called "OPEN" with no
counterweight. The truth for the book is a **credit balance of ₹10,86,454** —
not a receivable at all. Oil is the same shape: open ₹3,31,175 against a real
balance of ₹4,806, a 69× overstatement.

Fix: two new columns, `UNAPPLIED_RCT_INR` (`ORCT."OpenBal"`) and
`LEDGER_BAL_INR` (`OCRD."Balance"`), sit beside `OPEN_INR` on `1_SCOPE`,
`5_CUSTOMER` and `9_TOTAL A`, and the total row's `ROW_NOTE` says in words that
`OPEN_INR` is not a receivable. **The receipts are never subtracted from the
balance** — the receipt is already inside `OCRD."Balance"`, and subtracting would
double-count. Reported as a diagnostic only, per the settled rule.

### D4 — Mart's total row was all NULLs (major, FIXED)
**VERIFIED.** Mart has zero cash-sale documents. `SUM(…)` over an empty set
returns NULL, and the `9_TOTAL` row has no `GROUP BY`, so it still emitted — as a
row of NULLs. `build_data.coerce()` maps `'NULL'` → `None` and the renderer prints
`—`, so the Mart Cash Sale card read **"unknown"** where the truth is **zero**.

Fix: every `9_TOTAL` aggregate is `IFNULL(…,0)`. `7_GL_CASH` now `LEFT JOIN`s
`JDT1` so an account that exists with no postings still reports at zero — Mart's
1101014 now shows up as "exists, 0 lines, 0 movement" instead of vanishing.
**VERIFIED**: Mart's four `9_TOTAL` rows are now numeric zeros, no NULL cell
anywhere in any book.

### D5 — intercompany cash silently inside the cash-tender total (major, FIXED)
**VERIFIED.** `6_TENDER_MONTH` and the old `9_TOTAL B` swept **every** customer
cash receipt with no branch/intercompany test at all. Oil's total carried
**₹1,47,000 of cash from `CUSTA000606` JIVO MART PVT LTD** — a group company.
That is not trade, and the rule is that it must be flagged, never silently
dropped or included.

Also fixed here: the 23 C-0005 group CardCodes are **per company**, and the old
SQL applied all of them to every book. `CUSTA001099` is a group card in Oil but
is **HK TRADERS**, an ordinary Beverages customer (₹2,56,000 of genuine cash), in
Beverages; `CUSTA001113` is **BABA HARIDAS TRADERS** there. A flat list
mislabels real trade as intercompany in the wrong book.

Fix: a `grp_card` CTE keyed on `'{{SCHEMA}}'` (the house pattern already used by
`transporter.sql`) holds the right codes per book; the classification also applies
the group-name test (`'%BRANCH%'`) **and the name test** (`'%JIVO%'`), because
C-0005 says a group test alone is not enough. Tender is now split:
`9_TOTAL C` = external, `9_TOTAL D` = the group/branch slice, quantified and
labelled. `6_TENDER_MONTH` is external only.

Also confirmed **VERIFIED**: not one branch/intercompany card is a cash-sale card
in any book, so the *register* itself was and is 100% external. The bar drops
nothing.

### D6 — 128 money cells rendered as raw float noise (critical, FIXED)
**VERIFIED, and it was live on the page.** `build_data.coerce()` refuses to
`float()` a token longer than 15 digits — it protects document numbers and
GSTINs. A raw HANA `DOUBLE` such as `1358792.4106999983` is 17 digits, so it
landed in `data.json` as a **string**; `index.html` switches on
`typeof v === 'number'`, so it printed the string verbatim. The Cash Sale table
was showing `1358792.4106999983` and `₹13.59 L` in the same column:

```
oil : 75 money cells stuck as strings   (INV_NET_INR, TURNOVER_NET_INR, OPEN_INR,
                                         CASH_TENDER_INR, GL_DEBIT_INR, GL_CREDIT_INR)
mart: 11
bev : 42
```

`cash-sale.sql` was the **only** section in the pipeline with zero `ROUND(` calls
— every other one of the sixteen rounds (bank-reco 42, return-note 35,
vendor-ageing 32, …).

Fix: the outer `SELECT` was expanded from `SELECT *` to an explicit column list
that wraps each money column in `ROUND(…, 2)` — one place, so no UNION branch can
escape it. **VERIFIED after the fix: 0 money or count cells left as strings in
any book.**

---

## 4. What I attacked, and what survived

| # | Attack | Result |
|---|---|---|
| 1 | **Double counting / fan-out.** Header-to-line fan; UNION overlap; a document in two buckets. | **SURVIVED.** `dwhs` is keyed `(DocEntry, KIND)` and assigns exactly one bucket per document; `cc` is one row per card. Counts prove it: every facet sums to the same 1,094 (Oil) / 284 (Bev) invoices as the headline. `docs`' `UNION ALL` cannot overlap — `OINV` and `ORIN` are different tables and `KIND` separates them. |
| 1b | **Faceted table summed across scopes.** | **DEFECT, FIXED (D1).** Plus `INV_CNT` was being used to carry receipt counts and JDT1 line counts, so the `9_TOTAL` block summed to 2,170 "invoices" on Oil. Those counts moved to a new `TXN_CNT`; `INV_CNT` now means invoices, everywhere. The renderer does not total columns, so nothing was mis-added on screen — but the column name was lying. |
| 2 | **Cancelled documents.** | **SURVIVED, and the trap is real.** `"CANCELED"` carries three values: Oil `OINV` = 1,129 `'N'`, 18 `'Y'`, 18 `'C'` (the reversing document, ₹29,885 each side); Bev = 284 / 2 / 2. `= 'N'` is correct; `<> 'Y'` would have inflated Oil by ₹29,885. `ORCT` spells it `"Canceled"` and carries only `Y`/`N` — it excludes ₹2,84,090 (Oil) and ₹3,56,122 (Bev) of cancelled cash receipts. Applied on **every** document table touched. **VERIFIED.** |
| 3 | **Branch + intercompany.** | **DEFECT on the tender side, FIXED (D5).** Register side clean and quantified: zero branch/group cards in scope in any book. Name test applied, not only the group test. |
| 4 | **Unapplied money / open items.** | **DEFECT, FIXED (D3).** No double-subtraction existed and none was introduced — `ORCT."OpenBal"` is reported beside `OCRD."Balance"`, never netted off it. Inflation quantified: Bev 43.67 L "open" vs a −10.86 L real balance; Oil 3.31 L vs 4,806. |
| 5 | **Migrated openings at 2024-09-30.** | **DEFECT, FIXED (D1).** All 35 Oil openings are on one card, `VatSum` 0, no warehouse on the lines — genuinely openings, no false positives. Mart and Bev have none. |
| 6 | **Three-schema portability.** | **SURVIVED after D5.** Ran on all three. 1101014 exists in all three; the `CASH IN HAND` parent and its three postable children exist in all three; `OBPL` exists in all three (Oil 8 branches, Mart 20, Bev 6); `validFor` exists in all three; no UDFs. The one book-specific assumption — the flat 23-code group list — was found and made per-book. |
| 7 | **Empty and NULL.** | **DEFECT, FIXED (D4).** Mart is the empty case and is now zeros, not NULLs. `cash-sale` is already in `build_data.MAY_BE_EMPTY`, so the guard tolerates it. |
| 8 | **Money units.** | **SURVIVED on naming, DEFECT on rendering (D6).** Every money column is `_INR` and every value is in **rupees, unscaled** — no `_L`, no `_CR`, nothing mislabelled. Checked against the GL: `9_TOTAL A INV_GROSS_INR` for Oil = 1,438,780 rupees, and `JDT1` debits on 1101014 = 3,586,948 rupees = 35.87 L. The new `TXN_CNT` ends in `_CNT`, which `isMoneyCol()` explicitly excludes, so it can never be rendered as money. |
| 9 | **Re-derive the headline a second way.** | **SURVIVED — twice, see below.** |
| 10 | **Performance.** | **SURVIVED.** 1.3–1.6 s per company end to end over the home bridge (VPS tunnel), against a 300 s ceiling and a ~60 s concern threshold. 76 / 31 / 64 rows out. |

### Attack 9 in detail — two independent re-derivations

**Definition A (the register).** Independent route: sum `INV1."LineTotal"` per
document and compare with the header's `DocTotal − VatSum`, which shares no
column with the first route.

```
Oil  1094 docs  header net 1,358,963.8393   line total 1,358,964.4149
                freight 0   rounding −0.5759   UNEXPLAINED  0.0003
Bev   284 docs  header net 4,316,492.6175   line total 4,316,490.6322
                freight 0   rounding  1.9826   UNEXPLAINED  0.0027
```

Agreement to **three-tenths of a paisa**. Same query confirmed **1 currency, INR,
`DocRate` 1.0 min and max** — no foreign-currency `DocTotal` trap. **VERIFIED.**

Third route, the G/L: Oil `JDT1` debits on 1101014 = **₹35,86,948** vs
**₹34,64,703** of invoices on the 1101014 cards. The ₹1,22,245 gap is fully
itemised non-invoice debits — a ₹56,750 journal entry on CASH SALE PB (which has
no invoices at all), ₹58,995 on HARPREET, ₹6,500 on KAMALPREET. **VERIFIED.**

**Definition C+D (cash tendered).** Independent route: `JDT1` debits with
`"TransType" = 24` (Incoming Payment) on the cash tills, decomposed by the
receipt behind each transaction. This ties **exactly**:

```
Oil till TT24 debits                                    13,417,185.02
  ORCT DocType=C, not cancelled, CashSum>0   1076 rcpt   8,297,884.75  <- 9_TOTAL C + D
  ORCT DocType=A (till-to-till transfer)       87        4,103,144.00  <- T7, excluded
  storno reversals of cancelled payments       34          481,755.00  <- excluded
  ORCT DocType=C cancelled                     16          284,090.00  <- T5, excluded
  ORCT DocType=S (vendor cash refunds)         64          135,686.26  <- excluded
  ORCT DocType=A cancelled / S cancelled        4          114,625.00  <- excluded
                                                        --------------
                                              sum        13,417,185.01   (₹0.01 rounding)

Bev till TT24 debits                                    49,922,582.01
  ORCT DocType=C, not cancelled, CashSum>0   1294 rcpt  46,964,730.01  <- 9_TOTAL C + D
  storno reversals                             22        1,202,620.00
  DocType=A 856,190 + A-cancelled 540,520 + C-cancelled 356,122 + S 2,400
                                                        --------------
                                              sum        49,922,582.01   exact
```

Every rupee of till movement is accounted for and every exclusion is one of the
documented traps. **VERIFIED.** The 34 / 22 "no `ORCT` match" transactions were
chased down: they are storno entries (`OJDT."StornoToTr"` set, memo
"Reverse Entry for Incoming Payment No. …") — the reversal legs of cancelled
receipts, correctly outside the total.

---

## 5. Live numbers, 2026-08-21 (pasted from `pipeline/raw/cash-sale.*.tsv`)

```
#### oil
SECTION  SORT_KEY  ROW_KEY               INV_CNT  INV_GROSS_INR  TURNOVER_NET_INR  OPEN_CNT  OPEN_INR   UNAPPLIED_RCT_INR  LEDGER_BAL_INR  TXN_CNT  CASH_TENDER_INR
9_TOTAL  A         CASH_SALE_INVOICES    1094     1438780        1358792.41        254       331174.70  380985.86          4805.83         0        0
9_TOTAL  B         MIGRATED_OPENINGS     35       2441924        2441924           1         2          0                  0               0        0
9_TOTAL  C         CASH_TENDER_RECEIPTS  0        0              0                 0         0          0                  0               1070     8150884.75
9_TOTAL  D         CASH_TENDER_GROUP     0        0              0                 0         0          0                  0               6        147000

#### mart
9_TOTAL  A         CASH_SALE_INVOICES    0        0              0                 0         0          0                  0               0        0
9_TOTAL  B         MIGRATED_OPENINGS     0        0              0                 0         0          0                  0               0        0
9_TOTAL  C         CASH_TENDER_RECEIPTS  0        0              0                 0         0          0                  0               2081     14241306.63
9_TOTAL  D         CASH_TENDER_GROUP     0        0              0                 0         0          0                  0               0        0

#### bev
9_TOTAL  A         CASH_SALE_INVOICES    284      4568259        4311886.24        104       4367346    5786550            -1086454        0        0
9_TOTAL  B         MIGRATED_OPENINGS     0        0              0                 0         0          0                  0               0        0
9_TOTAL  C         CASH_TENDER_RECEIPTS  0        0              0                 0         0          0                  0               1292     46964730.01
9_TOTAL  D         CASH_TENDER_GROUP     0        0              0                 0         0          0                  0               2        0
```

**In words:**

| | Oil | Mart | Bev |
|---|---|---|---|
| Cash-sale register, turnover net of GST (all time to 2026-08-21) | **₹13.59 L** | **₹0** | **₹43.12 L** |
| — invoices | 1,094 | 0 | 284 |
| Migrated go-live openings, excluded | ₹24.42 L | — | — |
| What those cards actually owe (`OCRD."Balance"`) | ₹4,806 DR | ₹0 | **₹10.86 L CR** |
| Cash physically tendered by external customers | **₹81.51 L** | **₹1.42 Cr** | **₹4.70 Cr** |
| — group/branch cash, excluded and flagged | ₹1.47 L | ₹0 | ₹0 |

Scope, for the record (**VERIFIED**): Oil 6 cards, Mart 3, Bev 5.
`CASHEW`, `METRO CASH & CARRY` (a ₹66.4 L credit customer), `CASH PURCHASE HR`
and `ONE97 … CASH BACK` are all correctly out.

---

## 6. Still unresolved — stated plainly

1. **The cash-tender number is not a cash-sale number, and the dashboard has no
   bespoke renderer to keep them apart.** `cash-sale` falls through to the generic
   table, so all ~76 rows land in one flat table and the reader has to slice on
   `SECTION` themselves. The `ROW_NOTE` on every total row says which population
   it is, but a purpose-built renderer (headline = `9_TOTAL A`, tender shown as a
   clearly separate block) would be safer. **Not a SQL defect — a renderer gap.**
2. **Bev's ₹43.12 L of cash-sale turnover is concentrated in two months**
   (2026-05 ₹8.54 L, 2026-06 ₹32.53 L on `CUSTA000238` CASH SALE DL, avg invoice
   ≈ ₹44,700) after eleven months of ₹600–₹67,000 months. The figures are
   correct — they reconcile to 1101014 — but that is a *business* question
   (is a distributor being billed through the counter card?) I did not chase.
   **INFERRED that it is worth asking; not verified either way.**
3. **`CASH SALE PB` (Oil) has ₹56,750 of journal-entry movement on 1101014 and
   zero invoices.** It appears in `1_SCOPE` with a zero balance and in no other
   section. Correct behaviour for an invoice register, but the money is only
   visible in `7_GL_CASH`. **VERIFIED as a fact; left as-is deliberately.**
4. **The migrated-opening test is `DocDate = 2024-09-30`.** Today every document
   on that date is a genuine opening (Oil: one card, `VatSum` 0, no warehouse on
   the lines). If a real cash sale is ever back-dated to the go-live date it will
   be misfiled into `9_TOTAL B`. **INFERRED** — no way to distinguish them beyond
   the current heuristic without a `U_` flag SAP does not carry.
5. **`4_WAREHOUSE` uses `MIN(WhsCode)` as the "dominant" warehouse** for a
   single-warehouse document and buckets anything else as `(multi-warehouse)`
   (Oil 14 docs, Bev 2). It is a bucket, not a value split — no money is
   apportioned, so nothing is double-counted, but a multi-warehouse document's
   full value sits in one synthetic row. **VERIFIED as intended behaviour.**
6. **The other sections still use the flat 23-code group list across all three
   books** (`customer-ageing.sql`, `customer-ageing-detail.sql`). Same over-barring
   risk I fixed here — in Beverages that list bars HK TRADERS and BABA HARIDAS
   TRADERS, which are ordinary customers there. **VERIFIED as a fact about those
   files; outside this section's remit, flagged for whoever owns them.**

---

## 7. How to re-run

```bash
cd /Users/damanpreetsingh/jivo-cli/accounts-dashboard/pipeline
python3 build_data.py --only cash-sale --no-guard
#   summary   oil        76 rows    1.5s
#   summary   mart       31 rows    1.4s
#   summary   bev        64 rows    1.6s
```

Ad-hoc against one book:

```bash
cd /Users/damanpreetsingh/jivo-cli/hana-sql
sed -e 's/{{SCHEMA}}/JIVO_OIL_HANADB/g' -e 's/{{ASOF}}/2026-08-21/g' \
    ../accounts-dashboard/pipeline/sql/cash-sale.sql | sed -n '/^WITH/,$p' > /tmp/cs.sql
./hana-sql -env ../connections/hana-tunnel.env -f /tmp/cs.sql
```
The `sed -n '/^WITH/,$p'` strips the comment header — `hana-sql`'s read-only guard
reads the first token and a leading `--` line is not `SELECT`/`WITH`.
`build_data.read_sql()` does the same thing (it pops leading comment and blank
lines). **VERIFIED: this exact command returns the 9_TOTAL rows above.**
