---
name: cash-voucher-1-grpo
description: CASH VOUCHER TYPE 1 — the voucher that HAS an existing GRPO behind it. Use when a JIVO WELLNESS cash voucher slip arrives with a supplier's bill and a SAP "Goods Receipt Note" printout, or when a cash-sheet row matches an open GRPO on ANY card in any of the three books - the GRPO is often raised on the supplier's own card, not the imprest card. Builds the A/P as a COPY of that GRPO, so the G/L comes from the GRPO's item and never from the wording of the voucher; where the GRPO sits on the vendor's own card the A/P goes to that vendor plus a JV off the holder's float. Posting date = the slip, document date = the bill, Dim2 and Dim3 set by hand. For a voucher with NO GRPO behind it, that is a different type — see the parent skill `cash-voucher`.
---

# Cash voucher · TYPE 1 · the voucher WITH a GRPO

> 🔴 **ATTACHMENT RULE — every file goes up with `sapb1 attach`, never by hand (Daman, 16 Sept 2026 · C-0090).**
> Whatever this skill attaches — to a draft, GRPO, A/P, credit memo, payment, JV, A/R, anything —
> upload it with **`sapb1 attach <file> [<file>...] --company <DB>`** (`--dry-run` first, then `--yes`).
> It puts all the files on ONE `Attachments2` row, ticks **Copy to Target Document = `tYES`** on
> every line (plus the Approve stamp `U_CHK`/`U_CHK2 OK` in Oil and Bev — Mart has no such fields),
> reads the row back, and exits non-zero unless every line is `tYES` and every file downloads
> back byte-identical. An upload by any other route
> lands `tNO`, and then the scan does NOT follow the document onward (GRPO → A/P, draft → posted).
> - It prints `"AttachmentEntry": N` — point the document at row N (in the payload, or `sapb1 patch`).
> - Exit 8 = the row exists but is not finished — the message names the fix (usually
>   `sapb1 attach --row N --yes`). Exit 7 = an answer never came back: look at the row
>   (`sapb1 query Attachments2 --filter "AbsoluteEntry eq N"`) before sending any file again.
> - Never `curl -X POST …/Attachments2` or hand-PATCH the tick any more. Proven live 17 Sept 2026:
>   Oil 177963 (two files, byte-identical), Mart 59373, Bev 43331.

Daman named this type on 2026-09-12: **"cash voucher 1 GRPO"**. It is the type
where the purchase already went through **PO → GRPO** against the cash holder's
FACTORY IMPREST card before the paper reached Accounts.

Taught line by line on **2026-09-10** against voucher **437** of Arvinder sir's
cash sheet dated 04-09-2026 → **Oil draft 56767**, ₹5,190. Every rule below is a
correction Daman made to a draft I had already built and reported as finished.
Follow them; do not re-derive them.

RULE 0 in `CLAUDE.md` governs the write. Shared rules live in `ap-rm-pm`.

---

## How to know it is TYPE 1

You have a **GRPO printout** in the pack (SAP "Goods Receipt Note", `GRPO No.`,
`Reff. Po No.`), **or** the cash-sheet row matches an **open** GRPO.

🔴 **Search EVERY card, not just the imprest one, in ALL THREE books**
(C-0102). The old query here filtered `CardCode = '<imprest card>'` and **that is
why four GRPOs were missed** on 2026-09-19: 26731/26732/26733 sat on
**VENDA001090 ASHOK KITAB GHAR** and 26734 on **VENDA001182 BAJAJ ELECTRICAL**.
Vouchers 467/472/473/475 were reported "no GRPO" and retyped by hand.

```sql
-- no CardCode filter. Run it in Oil, Mart AND Beverages (C-0073).
SELECT h."DocEntry", h."DocNum", h."DocDate", h."CardCode", h."CardName",
       h."NumAtCard", h."DocTotal",
       l."ItemCode", l."Dscription", l."AcctCode", l."OcrCode", l."OcrCode3"
FROM   <DB>.OPDN h JOIN <DB>.PDN1 l ON l."DocEntry" = h."DocEntry"
WHERE  h."CANCELED" = 'N' AND h."DocStatus" = 'O' AND l."LineNum" = 0
  AND (h."NumAtCard" LIKE '%<bill no>%' OR h."DocTotal" = <amount>)
ORDER  BY h."DocDate";
```

**Match on the bill number in `NumAtCard` — it is exact.** Never on the
handwritten gate number off a phone scan: `634` was misread as `684`, `675` as
`678`.

🔴 **Whose card the GRPO sits on changes the document** (C-0098). On the
**imprest** card → copy it there, the float comes down by itself. On the
**vendor's own** card → the A/P is a GRPO copy **on that vendor**, plus a **JV**
(Dr vendor / Cr FACTORY IMPREST) — `cash-voucher-jv`. One JV per voucher, never
combined. **Never retype a vendor-card GRPO by hand on the imprest card.**

Open GRPOs on the card carry `NumAtCard` = **`<amount>/<dd-mm-yy>`**
(`5190/31-08-26`) — the supplier's bill reference. Match on the amount, then
**confirm with the `G.No.`** printed in the GRPO's `Comments` against the gate
stamp on the supplier's bill. Two vouchers can share an amount; they cannot
share a G.No.

`DocStatus 'O'` + line `TargetType = -1` = not yet copied. A **closed** GRPO
already has its A/P invoice — never copy it twice.

**No GRPO found in any of the three books (C-0073)?** Then it is not this type.
Stop and use the parent skill `cash-voucher`.

## The four papers

| Paper | What it is the authority for |
|---|---|
| **Supplier's bill** (Estimate Bill / handwritten slip) | the **document date**, the bill ref, the gate stamp `G.No.` |
| **Cash voucher slip** (JIVO WELLNESS VOUCHER, No. + Dated) | the **voucher number**, the **posting date**, the **costing date**, the **budget** mark |
| **GRPO printout** | the **G/L account**, item, tax, HSN, warehouse, qty, price, Dim1, Dim5 — and the `DocEntry` to copy |
| **Cash sheet** ("front sheet") | the **bunch** total and the `Unit` column (which book) |

---

## 🔴 THE RULE — copy the GRPO, and override exactly three things

`DocType` is **`dDocument_Items`**. One draft **per voucher**, never grouped —
and unlike a type-3 voucher this is still true after 2026-09-12: a `BaseType 20`
copy carries exactly one GRPO, so it cannot share a document. Plain vouchers ARE
grouped now; see `cash-voucher` → **Document shape**.
Lines are sent as a copy:

```json
{"BaseType": 20, "BaseEntry": <grpoDocEntry>, "BaseLine": <n>}
```

**What the copy brings — do not touch any of it:** the item, the **G/L account**,
the tax code, the HSN entry, the warehouse, the quantity, the price, **Dim1**,
**Dim5**.

**What the copy gets WRONG — set on every line, by hand:**

| Field | Set to | What the copy wrongly carries |
|---|---|---|
| `CostingCode2` (Dim2, costing date) | month of the **voucher slip's** date | the GRPO's month |
| `CostingCode3` (Dim3, budget) | the **slip's** handwritten mark | the GRPO's `Factory` |
| `U_Remarks` | `VCH <no> - RS <amount>` | nothing |
| **`TaxCode`** | **`Exampt`**, unless a **GST bill** is in the pack | the GRPO's code, usually `IGST@0` |

⚠️ **The `TaxCode` override is new (Daman, 2026-09-12)** and it is the one thing
you now change that the copy supplied. *"Tax code would be Exempt unless there is
GST on any bill provided — for all the cash vouchers."* Both codes are 0%, so no
amount moves. Everything else the copy brings still stands untouched. Full rule:
`cash-voucher` → **Rules that hold for EVERY cash-voucher type**.

### Never pick the G/L from the wording — measured 4 wrong out of 9

| Vch | Row wording | Guessing gives | GRPO's item → the truth |
|---|---|---|---|
| 437 | "some chemical for park maintain use" | R&M Building 5650001 ❌ | `CG0000005` HOUSEKEEPING → **5680015 HOUSE KEEPING** |
| 435 | "mcb for G.C lab use" | Lab & Testing 5680013 ❌ | `CG0000003` → **5650016 R&M PLANT & MACHINERY** |
| 436 | "tape roll for w.g plant use" | Stationery 5680012 ❌ | `CG0000021` TAPE ROLL → **5100006 PACKAGING MATERIALS** |
| 434 | "room temp machine" | R&M Plant 5650016 ❌ | `CG0000007` → **5650001 R&M OFFICE & BUILDING** |

**The item on the GRPO decides the head.** There is no expense-head map in this
skill on purpose — reaching for one here is the mistake.

---

## 1 · Dates — THREE papers, THREE different dates

SAP's screen labels do not match the OData field names. This is where the most
corrections landed:

| SAP B1 screen | OData field | Reads from | Voucher 437 |
|---|---|---|---|
| **Posting Date** | **`DocDate`** | the **cash voucher slip** | slip 01/09/26 → **2026-09-01** |
| **Document Date** | **`TaxDate`** | the **supplier's bill** | bill 31-08-26 → **2026-08-31** |
| — | `DocDueDate` | follows `DocDate` | 2026-09-01 |
| costing date = Dim2 | `CostingCode2` | the **voucher slip** | → **`09-2026`** |
| — | `Series` | the month **`DocDate`** lands in | **3325** (Sep) |

A voucher routinely **posts in one month against a bill from the previous one**,
and costs to the posting month. **That is correct, not a mismatch to fix.**
Precedent: posted doc 50035 has posting date 06-08-2026 against document date
31-07-2026.

**There is no "Costing Date" column** — checked every column and UDF of `ODRF`
and `DRF1`. The costing date **is** Dimension 2, written `MM-YYYY`. Confirm the
code is active in `OOCR` `DimCode = 2` before sending it.

**Series** (BPL 2, A/P invoice, `NNM1 ObjectCode 18`) — the `HR_B` family, not
`HR_D`:

| Month | Oil | Bev |
|---|---|---|
| Jul-26 | 3323 | 2677 |
| Aug-26 | 3324 | 2678 |
| Sep-26 | **3325** | **2679** |
| Oct-26 | 3326 | 2680 |

Probe an unknown month rather than guessing — a wrong number is refused safely
with `[SAP -10] 10000521 … define the numbering series`. Check the period is
open (`OFPR.PeriodStat = 'N'`).

⚠️ **Patching `Series` silently resets `TaxDate` to `DocDate`.** Measured on
56767: one PATCH set `DocDate` 01-09 + `Series` 3325 + `TaxDate` 31-08, and the
read-back showed `TaxDate` had become 01-09. **Send `TaxDate` again in a second
PATCH and read it back.**

## 2 · `NumAtCard` (Vendor Ref. No.)

```
<MON> YY / <bunch> / <this document's total>
```

**The bunch is the printed Total of the TABLE the voucher sits in** — not the two
tables added. Daman: *"bunch no. is wrong — 39940 was the bunch for ours but it
is written here 49097."*

| Table on the sheet | Book | Bunch |
|---|---|---|
| `Common` / `Canola` | **Oil** | **39940** |
| `Wg` | **Beverages** | **9157** |

**Month prefix follows the DOCUMENT date (the bill), not the posting date.**
Voucher 437 posts 01-09-2026 but its bill is 31-08-26 → **`AUG 26/39940/5190`**.
Precedent 50035 proves it: posted 06-08-2026, document date 31-07-2026,
`NumAtCard` `JUL 26/32820/3800`. Three letters — `AUG 26`, never `AUGUST 26`.

*Trap for whoever reads the history: grouping posted docs on the middle token
does show complete batches summing to it across two books (`64544` = Oil 48,934
+ Bev 15,610, exact). That is a red herring. Take the bunch off the sheet.*

## 3 · `U_Remarks` = voucher number **AND** amount

**`VCH 437 - RS 5190`**, on **every** line. `NVARCHAR(100)`.

Older posted lines carry the bare number (230, 226, 205 …). Daman changed this
on 2026-09-10 — the amount goes in too.

## 4 · Dim3, the budget — the paper overrides the GRPO (C-0027)

**Decide in order: a voucher carrying a DISPATCH INVOICE takes `Del Bkhp`;
otherwise a slip marked Common takes `FACT_COM`; otherwise `Factory`.** Added
2026-09-12 — full rule and the supplier-bill exclusion in `cash-voucher` →
**Dim3, the budget**. The GRPO's own value never decides this.


The **voucher slip** carries a handwritten allocation mark, and the cash sheet
repeats it in the `Unit` column. `Common` → **`FACT_COM`** (FACTORY COMMON).
The GRPO says `Factory`; the paper wins, every time.

Daman: *"Budget is wrong on all. It should be common."* — 56767 had been built as
a clean GRPO copy and carried `Factory` on all four lines, even though the slip
had `Common` underlined in the CREDIT block **and** the sheet's `Unit` column
said `Common`. Two independent tellings, both ignored because the copy looked
complete.

`Canola` → **ASK.** Not yet confirmed. Do not assume `Factory`.

## 5 · Which book, and whose card

The `Unit` column on the cash sheet picks the book:

| Unit | Book |
|---|---|
| `Wg` (water / beverage / "w.g plant") | **Beverages** |
| `Canola` | **Oil** |
| `Common` | **Oil** (and Dim3 `FACT_COM`, §4) |

| Book | Imprest CardCode |
|---|---|
| Oil (`JIVO_OIL_HANADB`) | **`ORGV000465`** |
| Beverages (`JIVO_BEVERAGES_HANADB`) | **`ORGV000245`** |
| Mart (`JIVO_MART_HANADB`) | `ORGV000217` |

All three are "ARVINDER SINGH IMPREST JWPL0115 **FACTORY IMPREST 5 LAKH**".
`ORGV000019` (plain, no "FACTORY IMPREST") is the decoy — never use it. **Never
clone a CardCode across books** ([[sap-named-connections]]). Match names in code,
not by OData filter (`toupper` unsupported, C-0036).

**Dim1 and Dim5 come from the GRPO — do not derive them.** The Bev GRPOs of
29–31 Aug 2026 carry Dim1 **`DRINKS`**, not the `WATER` the posted service lines
use. Both are live Bev codes.

Other holders carry this class historically: `ORGV000041` BHUPINDER SINGH GINNI,
`ORGV000207` LOVPREET SINGH.

## 6 · Header constants

| Field | Value |
|---|---|
| `DocType` | `dDocument_Items` |
| `DocumentSubType` | `bod_None` |
| `BPL_IDAssignedToInvoice` | **2** (FACTORY, Haryana, GSTIN 06AACCJ4223F1Z0) |
| `SalesPersonCode` | **Oil: `7`** (= ARVINDER SINGH), header and line. **Bev: omit** |
| `WTLiable` | `tNO` — no TDS, no `WithholdingTaxDataCollection` |
| `VatSum` | must read **0** |

`Comments`, **≤ 254 characters** (`[SAP -8112] … Value too long` above it):

```
BEING EXPENSE BOOKED AGAINST <HEAD> <total>/-, CASH VCH <no> DT <dd-mm-yy>,
BILL <ref> <SUPPLIER>, G.NO.<n>
```

## 7 · Attach — three files on the draft's own row

Never point two documents at one `Attachments2` row.

| Line | File |
|---|---|
| 1 | the **cash voucher pack** — slip + supplier's bill (+ GRPO print), named `CASH-VCH-<no>-<dd-mm-yyyy>.pdf` |
| 2 | the **GRPO's own file** — download `Attachments2(<grpo AtcEntry>)/$value`, re-upload |
| 3 | the **cash sheet / front sheet** — `CASH-SHEET-FRONT-<HOLDER>-<date>.pdf` |

Daman, 2026-09-10: *"this front sheet — this also normally goes through it."*
The cash sheet goes on **every** voucher's draft, in both books.

Upload all three with ONE `sapb1 attach <pack> <grpo-file> <front-sheet> --yes`
(recipe: `ap-rm-pm/reference/attachments-upload.md`). Traps:

- **`[SAP -1116] (1120026) Attachment Size Should be Less Than 1 MB`** — the cap
  is **per FILE, not per row** (761 + 115 + 463 KB on one row was accepted).
  Re-render a fat photographed pack:
  `pdftoppm -r 100 -jpeg -jpegopt quality=45 pack.pdf out/pg` then
  `magick out/pg-*.jpg -quality 45 pack-small.pdf` (13 pages, 4.1 MB → 738 KB).
  **Spot-check a page** — the voucher number and amount must stay readable — and
  say in the report that the attached copy is a re-render.
- `sapb1 attach` stamps `U_CHK = <size KB>`, `U_CHK2 = 'OK'` on **every** line before
  you patch `AttachmentEntry` — without it SAP refuses with `-1116 (1120025)` (C-0082) —
  and ticks **`CopyToTargetDoc = 'tYES'` on every line, every book** (C-0090), so the bill
  follows the document onward. Exit non-zero = not done; never hand-PATCH around it.
- SAP **auto-renames** a filename already on the share (name + ddmmyyyy + time).
  Harmless; the file is correct.
- A refused `AttachmentEntry` patch leaves an **orphan `Attachments2` row**. It
  cannot be deleted from this CLI — report it, don't hide it.
- Prove it: pull `$value` back and `cmp`. For any line but the first the filename
  selector must be **quoted**: `$value?filename='NAME.pdf'`.

## 8 · Editing a draft afterwards

- **Field-only PATCH is safe** — dims, remarks, dates, `NumAtCard`. Send the
  **complete** `DocumentLines` array with every `LineNum` (a partial collection
  rewrites what you omit), then read the whole line back. Verified on 56767:
  G/L, Dim1/5, tax, HSN, prices, remarks, `AttachmentEntry`, `DocTotal` all
  survived.
- **Changing the line COUNT by PATCH corrupts the price fields** — rebuild
  instead (`jivo-service-vehicle-expense` §8): detach
  (`{"AttachmentEntry": null}`) → `sapb1 delete draft` → create fresh. Detaching
  first means the `--with-attachment` override is not needed and all six delete
  guards pass on a same-day draft of your own.
- **All drafts in one series share the same provisional `DocNum`.** Report
  `DocEntry`, never `DocNum`.

## 9 · ₹10,000 cap

**Daman: "10k is the hard limit."** No cash-voucher document may exceed
**₹10,000**. Since 2026-09-19 GRPO vouchers are **grouped by PO** like every
other type (C-0097), so the cap is the live constraint here too — it is the only
thing allowed to split one PO into two documents, and it splits at voucher
boundaries. **If a single voucher is over, stop and tell the operator** — do not split the voucher and do
not merge vouchers. Context, not a lecture: s.40A(3) disallows cash expenditure
over ₹10,000 to one person in one day.

## 10 · Stop at the draft

`WddStatus` stays `-`. It reaches nobody until a human presses **Add** in
*Purchasing – A/P → Purchasing Reports → Document Drafts Report* — tick **A/P
Invoice**, **Open Only**, **User = the creating login**, and a **posting-date
range that covers the posting date** (a September filter will not show an
August-posted draft). `ODRF.OwnerCode` is NULL, so anyone can Add it once the
User dropdown is changed.

🛑 **A cash-voucher batch STOPS HERE until Daman has seen the list** (C-0101).
Build every draft, attach every pack, print the list, and **wait for his word**.
Cash vouchers are the one documented exception to `CLAUDE.md`'s "a bill is not
done at the draft" rule. Once a draft is in the approval queue SAP will not let
you delete it (**-10**), change its party (**-2028**) or drop a line — on
2026-09-19 ten drafts went in nine seconds and four of them are still stuck.

`sapb1 add-draft` also needs a login an Always-terms template names. Oil 103 now
lists **USER08, USER39 and USER07** (C-0104 — check `WTM1`, the list changes).
From a login no template names it posts **LIVE** — `jivo-add-and-new`.

---

## Worked example — voucher 437, end to end

Paper: **Estimate Bill** from NEW SWAMI KHAD & BEEJ BHANDAR (Ganaur) ₹5,190 dated
31-08-26, gate stamp `G.No.639` · **voucher slip 437** dated 01/09/26 "Cash Paid
to Jasmeet ji for Purchase Some Chemical for Park Maintain use ₹5190/-", marked
`Common`, ₹100 revenue stamp · **GRPO print** 2026086899 (DocEntry 26374, PO
220826156) · the cash sheet.

```json
{ "CardCode": "ORGV000465", "DocType": "dDocument_Items",
  "DocumentSubType": "bod_None",
  "DocDate": "2026-09-01", "TaxDate": "2026-08-31", "DocDueDate": "2026-09-01",
  "NumAtCard": "AUG 26/39940/5190", "Series": 3325,
  "BPL_IDAssignedToInvoice": 2, "SalesPersonCode": 7, "WTLiable": "tNO",
  "Comments": "BEING EXPENSE BOOKED AGAINST HOUSE KEEPING 5190/-, CASH VCH 437 DT 01-09-26, BILL 5190/31-08-26 NEW SWAMI KHAD & BEEJ BHANDAR, G.NO.639",
  "DocumentLines": [
    {"BaseType":20,"BaseEntry":26374,"BaseLine":0,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"},
    {"BaseType":20,"BaseEntry":26374,"BaseLine":1,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"},
    {"BaseType":20,"BaseEntry":26374,"BaseLine":2,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"},
    {"BaseType":20,"BaseEntry":26374,"BaseLine":3,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"}
  ] }
```

→ **Oil draft 56767**, ₹5,190, VatSum 0. Read back: `CG0000005` /
**5680015 HOUSE KEEPING** / `CANOLA` / `HR` / `IGST@0` / HSN 237 / LocCode 2 all
inherited from the GRPO; Dim2 and Dim3 set by hand. Attachment row 176525 carries
the voucher pack (761 KB), the GRPO's bill photo (115 KB) and the front sheet
(463 KB), all `U_CHK2='OK'`, all read back byte-identical.

---

## What I got wrong on this exact voucher

Every one was a correction Daman made **after** I had built the draft and
reported it as finished.

| # | Field | I had | Correct | Root cause |
|---|---|---|---|---|
| 1 | Document shape | one draft per book, grouped to fill the ₹10k cap | one draft per voucher ⚠️ **SUPERSEDED — see below** | invented a grouping rule from posted history instead of asking |
| 2 | G/L | hand-picked from the row's wording | **from the GRPO's item** | never looked for a GRPO; assumed the class was service-only |
| 3 | Dim3 budget | inherited the GRPO's `Factory` | **`FACT_COM`** from the slip's "Common" | treated a GRPO copy as authoritative for *everything* (C-0027 was in context and ignored) |
| 4 | Dim2 costing | inherited the GRPO's `08-2026` | **`09-2026`** from the slip's date | same |

> ⚠️ **Row 1 is history, not the live rule.** "One draft per voucher" was right
> on 2026-09-10. It was superseded on 09-12 (grouping) and again on **2026-09-19**
> by **ONE ENTRY PER PO** (C-0097). Live proof: drafts **57454** (vouchers 454 +
> 459), **57456** (466 + 468) and **57457** (469 + 470) each carry two or more
> GRPO-copy vouchers on one document. The rest of the rows still stand.
| 5 | Vendor ref bunch | `49097` (both tables added) | **`39940`** (that table's own Total) | trusted an inference from history over the sheet in hand |
| 6 | Posting date | 31-08-2026 | **01-09-2026** (the slip's date) | mapped SAP's screen label "Document Date" to `DocDate` instead of `TaxDate` |

**The pattern in all six: a derived rule beat the paper in front of me.** The
paper wins. The slip wins for the posting date, Dim2 and Dim3; the GRPO wins for
the G/L; the bill wins for the document date; the sheet wins for the bunch. When
none of them is clear, **ask** — do not infer from history.

---

## Pre-flight — tick before `--yes`

- [ ] a real **open** GRPO found, matched on amount **and** `G.No.`, `TargetType = -1`
- [ ] **ONE ENTRY PER PO** (C-0097) — vouchers sharing a PO share the document,
      **even across months**; only the ₹10,000 cap splits a PO, at voucher
      boundaries; never split one voucher across two documents
- [ ] lines sent as a **copy** (`BaseType 20`); no G/L, item, tax, HSN, Dim1 or
      Dim5 set by hand
- [ ] FACTORY IMPREST `ORGV…` for **this book** — not the plain twin, not another
      book's code
- [ ] `DocDate` (posting) = the **voucher slip's** date
- [ ] `TaxDate` (document) = the **supplier's bill** date
- [ ] `Series` = `HR_B<MMYY>` for **`DocDate`**'s month, period open; if `Series`
      was patched, **`TaxDate` re-sent and read back**
- [ ] `CostingCode2` = month of the **slip's** date, every line
- [ ] `CostingCode3` = the **slip's** mark (`Common` → `FACT_COM`), every line
- [ ] `U_Remarks` = `VCH <no> - RS <amount>`, every line
- [ ] `NumAtCard` = `<bill's MON> YY/<that table's Total>/<this doc's total>`
- [ ] `VatSum` 0 · `WTLiable` tNO · `DocTotal` = the voucher amount
- [ ] attachment row carries **voucher pack + GRPO's file + front sheet**, every
      file < 1 MB, `U_CHK2='OK'` on each, `$value` read back and `cmp`'d
- [ ] `DocEntry` reported, never `DocNum`
- [ ] `WddStatus` still `-` — stopped at the draft
