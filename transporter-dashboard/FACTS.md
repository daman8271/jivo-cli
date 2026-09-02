# TRANSPORTER BOARD — verified data facts (binding on every agent)

Every fact below was probed against **live HANA** on 2026-08-22 by the lead
before this build started. Do not re-derive them, do not "improve" them, and do
not contradict them. If your query disagrees with a fact here, your query is
wrong — stop and report it.

Connection (read-only, never writes):
```
cd /Users/damanpreetsingh/jivo-cli/hana-sql
./hana-sql -env ../connections/hana-tunnel.env "<SELECT ...>"
```
Output is TSV, first line = header. Only SELECT/WITH are accepted by the binary.

---

## 1. Who is a transporter

`OCRG.GroupCode = 102`, `GroupName = 'TRANSPORTER'` — **same code in all three
books**. Vendors are `OCRD` rows with `CardType='S'` and `GroupCode=102`.

| Book | Schema | Transporter cards | Active FY26 | A/P invoices FY26 | Gross ₹L | Payments FY26 | Paid ₹L |
|---|---|---|---|---|---|---|---|
| Oil | `JIVO_OIL_HANADB` | 97 | 21 | 194 | 97.01 | 96 | 120.81 |
| Mart | `JIVO_MART_HANADB` | 95 | 16 | 145 | 81.55 | 76 | 99.03 |
| Beverages | `JIVO_BEVERAGES_HANADB` | 96 | 12 | 86 | 34.72 | 31 | 18.98 |

Paid > Gross because FY26 payments also settle **prior-year** invoices. Do not
"fix" this; it is real. See §4.

---

## 2. THE JOIN — the single most important fact in this build

`VPM2` is the payment-allocation table. **Its two key columns are named
backwards from what you would assume:**

- `VPM2."DocNum"`  = the **payment's** `OVPM."DocEntry"`   ← join payments on this
- `VPM2."DocEntry"` = the **target document's** `DocEntry`  ← join invoices on this

```sql
FROM {{SCHEMA}}.OVPM p
JOIN {{SCHEMA}}.VPM2 l ON l."DocNum"   = p."DocEntry"     -- payment -> its lines
JOIN {{SCHEMA}}.OPCH i ON i."DocEntry" = l."DocEntry"     -- line -> the invoice
                      AND l."InvType"  = '18'
```
Getting this backwards silently returns plausible-looking wrong rows. It was
verified live: payment DocNum 826466599 (₹24,656) maps to exactly three
invoices — 11,518 + 3,760 + 9,378 = 24,656. Exact.

### Cancelled flag is spelled differently per table (and is three-valued, C-0021)
- `OPCH."CANCELED"` — upper case
- `OVPM."Canceled"` — mixed case
- Always filter **`= 'N'`**. Never `<> 'Y'` — that keeps the `'C'` system
  mirrors and double-counts.

---

## 3. What a payment can attach to — `VPM2."InvType"`

A payment does **not** only settle A/P invoices. Live mix confirms:

| InvType | Meaning | Table | Handle |
|---|---|---|---|
| `18` | A/P Invoice | `OPCH` | primary — full detail |
| `19` | A/P Credit Note | `ORPC` | reduces what is owed — show it |
| `30` | Journal Entry | `OJDT` | manual settlement (see C-0019) — show as "settled by JE" |
| `46` | Outgoing Payment | `OVPM` | on-account applied later; `SumApplied` is negative |
| `24`/`13`/`14` | incoming pmt / A/R inv / A/R CN | — | rare, contra — label, don't drop |

**Never silently drop a line type you did not expect.** Bucket it as
`OTHER (InvType=nn)` and show it. Dropping is how the totals stop tying.

---

## 4. TDS lives on the INVOICE, not the payment

This is counter-intuitive and it is the fact the operator most needs shown.

- `VPM2."WtAppld"` (withholding applied at payment) is **0.00 across the board**.
- `VPM2."DcntSum"` (discount at payment) is **0.00 across the board**.
- The real TDS is `OPCH."WTSum"` — **152 of 194** Oil transporter FY26 invoices
  carry it, ₹1,40,077 total. `OPCH."DiscSum"` is 0 on all of them.
- `OPCH."WTApplied"` differs slightly from `WTSum` (e.g. 199 vs 208) — show
  `WTSum` as the TDS and treat `WTApplied` as a cross-check, not the headline.

### Two different TDS behaviours coexist in the same book — SURFACE THIS
Verified rows:

| Invoice | Gross | TDS (`WTSum`) | Applied in payment | Status | Pattern |
|---|---|---|---|---|---|
| 626074214 | 12,037 | 208 | 11,518 | `O` | short-paid, gap 519 |
| 626074300 | 3,950 | 68 | 3,760 | `O` | short-paid, gap 190 |
| 626074292 | 9,825 | 169 | 9,378 | `O` | short-paid, gap 447 |
| 626074367 | 110,749 | 2,260 | **110,749 (full gross)** | `C` | TDS **not** deducted at payment |

So: sometimes TDS is withheld from the payment, sometimes the full gross is paid
and TDS is handled elsewhere. **The board must show which, per invoice** — that
is the whole point of the deliverable.

### The reconciliation line every invoice row must carry
```
GROSS (OPCH."DocTotal")
  − TDS            (OPCH."WTSum")
  − DISCOUNT       (OPCH."DiscSum")            -- 0 today, keep the column
  − OTHER_DEDUCTION (balancing figure)
  = NET PAID       (sum of VPM2."SumApplied" for InvType 18 on that invoice)
```
`OTHER_DEDUCTION = GROSS − TDS − DISCOUNT − NET_PAID`. It is a **residual, not a
known quantity.** Label it exactly that: *"unexplained — shortage/damage claim or
settled by journal"*. Per the build contract, **never render it as a confident
zero** and never present it as a verified deduction. When it is non-zero, the
row is flagged for the operator to look at. That flag is a feature.

---

## 5. On-account payments — the thing that causes repeated searching

**16 of 96** Oil FY26 transporter payments have **no `VPM2` line at all**. They
are money paid against no invoice. They must appear in their own explicit
bucket — "Paid, not yet matched to a bill" — with the amount. Hiding them is the
single easiest way to make this board useless.

`OVPM` also splits the money across `CashSum` / `CheckSum` / `TrsfrSum`; the
headline is `OVPM."DocTotal"`.

---

## 6. Fetch window

FY26 payments settle invoices dated back to **2025-07-31**. Therefore:
- fetch **A/P invoices from `2025-04-01`** (FY25 start) so every payment can
  resolve its invoice,
- fetch **payments from `2025-04-01`** too,
- the board's **default view** is FY26 (`>= 2026-04-01`), with FY25 available.

An invoice referenced by a payment but outside the window must still render —
as `(invoice outside window)` with its DocEntry — never as a blank.

---

## 7. Useful `OPCH` columns

`DocEntry, DocNum, DocDate, TaxDate, NumAtCard (vendor's own bill no), CardCode,
CardName, DocTotal, VatSum, WTSum, WTApplied, DiscSum, PaidToDate, DocStatus,
DocDueDate, BPLId (branch), Comments`

`DocStatus` `'O'`/`'C'` is **unreliable at JIVO** (C-0019) — invoices settled by
manual JE stay `'O'`. Never headline "open" from `DocStatus` alone; age from the
money, and say so.

`OVPM`: `DocEntry, DocNum, DocDate, CardCode, CardName, DocTotal, Canceled,
CashSum, CheckSum, TrsfrSum, TrsfrRef, TrsfrDate, Comments`

---

## 8. House rules inherited from the Accounts Board contract

1. **Read-only. Never write to SAP.** No `draft`/`post`/`patch`, no DML. RULE 0.
2. **No CDN, no framework, no build step, no npm.** Plain HTML + ES modules +
   hand-written SVG/CSS. It must open from a file and from Vercel identically.
3. **Never a confident zero.** Uncomputable → `not computed` + the reason.
4. **No horizontal page overflow at any nesting level.** Wide tables scroll in
   their own `overflow-x:auto` box. `*{box-sizing:border-box;min-width:0}`.
5. **Money in INR**, Indian digit grouping (`12,34,567`). Lakhs/crores for
   headlines, exact rupees in detail tables. Never mix units in one column.
6. **Light theme only** — read in office daylight, often on a phone.
7. The three books are **separate**. Never sum Oil + Mart + Bev into one figure.

---

## 9. ADDENDUM (lead, 2026-08-22 22:55) — the `OVER` flag was wrong; new vocabulary

Built data showed Oil 210 / Mart 135 / Bev 62 invoices flagged `OVER`. Checked
every one: **zero are paid above gross.** 195 / 130 / 58 are paid at *exactly*
gross, and on **100% of those `OPCH."WTApplied" = 0`** — SAP holds the TDS on the
invoice (`WTSum`) but never applied it, so the vendor was credited and paid the
full amount. That is evidence from a field in the books, not inference. Say it.

`RESIDUAL_FLAG` is now six values, evaluated in this order:

| Flag | Test | Plain meaning for the operator |
|---|---|---|
| `UNPAID` | PAY_CNT = 0 | no payment touches this bill |
| `OK` | \|GROSS−TDS−DISC−NET_PAID\| ≤ 1 | paid net of TDS, reconciles |
| `GROSS_PAID` | \|NET_PAID−GROSS\| ≤ 1 | **paid in full — TDS on the bill was not deducted at payment** (`WTApplied`=0) |
| `SHORT` | residual > 1 | paid less than gross−TDS; gap is unexplained |
| `OVER` | NET_PAID > GROSS+1 | genuinely paid above the bill (0 rows today) |
| `PART_TDS` | anything else | deducted something, but less than the TDS |

UI: `GROSS_PAID` is a warning tone (it is a TDS-compliance question, not an
overpayment). `OVER` stays danger. `PART_TDS` warning. Never label `GROSS_PAID`
as "overpaid".
