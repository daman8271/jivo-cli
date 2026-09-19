---
name: cash-voucher-bill
description: CASH VOUCHER TYPE 2 — the voucher whose paper is a REGISTERED VENDOR'S GST TAX INVOICE, with no GRPO behind it. Use when a JIVO WELLNESS cash voucher slip arrives clipped to a printed tax invoice carrying a GSTIN and CGST/SGST (or IGST) — internet, service, small supplier — and there is no Goods Receipt Note print and no open GRPO on the imprest card. The A/P invoice goes to the REAL VENDOR on the letterhead, never the FACTORY IMPREST card, because the input credit has to land on that vendor's GSTIN. Service draft, GST tax invoice subtype, posting date = the gate stamp, document date = the bill, vendor ref = the bill number. For a voucher with a GRPO behind it see `cash-voucher-1-grpo`.
---

# Cash voucher · TYPE 2 · the voucher WITH A VENDOR'S BILL

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

Daman named this type on **2026-09-12**: **"cash voucher bill"**. It is the type
where the cash holder paid a **registered vendor** who issued a **proper GST tax
invoice**, and nothing went through PO → GRPO.

Taught line by line on 2026-09-12 against voucher **421** of the factory cash
book — SUNRISE INTERNET PVT LTD bill `26-27/103`, ₹1,180 → **Oil draft 56919**.
Every rule below is one Daman gave or confirmed on that voucher. Follow them; do
not re-derive them.

RULE 0 in `CLAUDE.md` governs the write. Shared rules live in `ap-rm-pm`.

---

## How to know it is TYPE 2

Two papers in the pack, and only two:

1. a **JIVO WELLNESS VOUCHER** slip (No. + Dated + the amount), and
2. a **printed tax invoice** from a registered vendor — vendor GSTIN on it,
   **CGST + SGST** (or IGST) broken out, an invoice number, a JIVO gate stamp.

**No Goods Receipt Note print in the pack**, and **no open GRPO** on the imprest
card at that amount. Search all three books before calling a GRPO missing
(C-0073) — the query is in `cash-voucher-1-grpo`. If a GRPO turns up, stop and
use that skill instead.

The quickest tell: **type 1 has VatSum 0, type 2 carries real GST.** An imprest
GRPO is raised against an unregistered supplier; a type-2 bill exists precisely
because the vendor is registered.

---

## 🔴 THE RULE — the A/P goes to the VENDOR, not the imprest card

**Daman, 2026-09-12, pointing at the letterhead: "this is the vendor in here."**

`CardCode` is the **real vendor** — SUNRISE INTERNET PVT LTD, `VENDA001500` —
**never** `ORGV000465` ARVINDER SINGH IMPREST. That is the whole difference from
type 1, and the reason is GST: the input credit must sit against the vendor's own
GSTIN or JIVO cannot claim it.

**So this document does NOT reduce anybody's cash float.** It books a payable to
the vendor. The cash Arvinder already handed over is closed off **later, by a
journal voucher against his imprest** — Daman, 2026-09-12: *"we gonna close
arvinder's imprest voucher later by posting a journal voucher."* That JV is **not
your job in this skill** and he is teaching it separately. Do not invent it, and
do not "fix" the open payable.

**Find the vendor before you build.** Fetch `BusinessPartners --all --json` and
match the letterhead name in code — `toupper()` is unsupported (C-0036) — and
never clone a CardCode between books ([[sap-named-connections]]).

---

## The document shape

**Service draft, GST tax invoice.** There is no GRPO to copy and no item, so every
field is set by hand:

```json
{
  "CardCode": "<vendor>",
  "DocType": "dDocument_Service",
  "DocumentSubType": "bod_GSTTaxInvoice",
  "Series": <HR_G for the posting month>,
  "DocDate":    "<gate stamp date>",
  "TaxDate":    "<bill date>",
  "DocDueDate": "<gate stamp date>",
  "NumAtCard":  "<the bill number, exactly as printed>",
  "BPL_IDAssignedToInvoice": 2,
  "SalesPersonCode": 38,
  "WTLiable": "tNO",
  "DocumentLines": [
    { "AccountCode": "<expense head>",
      "UnitPrice": <taxable value>,
      "TaxCode": "<CG+SG@18 | IGST@…>",
      "LocationCode": 2,
      "CostingCode":  "<CANOLA | WATER>",
      "CostingCode2": "<MM-YYYY>",
      "CostingCode3": "<FACT_COM | Factory>",
      "CostingCode5": "HR",
      "U_Remarks": "<voucher number>" }
  ]
}
```

`DocType` is **`dDocument_Service`** — `AccountCode`, no `ItemCode`, and
**`UnitPrice`, never `LineTotal`** ([[ap-copy-set-unitprice-not-linetotal]]).

---

## 0 · This type is NEVER grouped

Plain (type-3) vouchers are grouped onto one A/P since 2026-09-12. **This type is
not**, and the reason is mechanical rather than a preference: the document is
made out to the **vendor**, and two vendors cannot share one `CardCode`. One
bill, one draft — even when three Porter receipts arrive on the same day.

## 1 · Dates — the stamp posts it, the bill dates it

**Daman, 2026-09-12: "Always take the stamp date as a posting date, okay, and
bill date and document date."**

| SAP B1 screen | OData field | Reads from | Voucher 421 |
|---|---|---|---|
| **Posting Date** | **`DocDate`** | the **gate stamp** on the bill | `G.No.155  Date 17/8/26` → **2026-08-17** |
| **Document Date** | **`TaxDate`** | the **bill** | Dated 13-08-2026 → **2026-08-13** |
| — | `DocDueDate` | follows `DocDate` | 2026-08-17 |
| costing date = Dim2 | `CostingCode2` | the month of the **bill** | → **`08-2026`** |

**🔴 The slip's own date is NOT the posting date here.** This is the single
biggest difference from type 1, where the slip *is* the posting date. Voucher 421
is dated **27/8/26** on its face (checked at 600 dpi — it is a 2, not a 1) and it
posts **17-08**, the gate stamp. Read the stamp, not the slip.

On voucher 421 the bill month and the posting month were both August, so Dim2 was
unambiguous. When they differ, Dim2 follows the **bill**
([[effective-month-is-the-invoice-date]]).

⚠️ **Patching `Series` silently resets `TaxDate` to `DocDate`** (measured on 56767).
If you patch the series, **send `TaxDate` again in a second PATCH and read it back.**

## 2 · Series — the `HR_G` family, and you cannot see it on the document

**Daman asked where HR_G is visible in the draft. It is not.** The document stores
only a number — `Series: 3684`. `HR_G0826` is that series' *name*, and it lives in
SAP's numbering-series table `NNM1`. In the SAP B1 client it is the **series
dropdown beside the document number** on the A/P Invoice form.

Oil branch 2 runs **three** A/P families for the same month. Pick by name:

| Family | Aug-26 | Sep-26 | Used by |
|---|---|---|---|
| `HR_B<MMYY>` | 3324 | 3325 | **type 1** — imprest cash vouchers |
| **`HR_G<MMYY>`** | **3684** | **3685** | **this type** |
| `HR_D<MMYY>` | 3857 | 3858 | not yet identified |

`HR_G` runs consecutively through the year — Oil FY26-27: Aug **3684**, Sep
**3685**, Oct **3686**, Nov **3687**, Dec **3688**, Jan **3689**, Feb 3690,
Mar 3691. Read it back rather than trusting this list after Mar-27.

```sql
SELECT "Series","SeriesName","Indicator","Locked"
FROM   <DB>.NNM1
WHERE  "ObjectCode"='18' AND "SeriesName" = 'HR_G<MMYY>';
```

The `HR` prefix is the branch's state (Haryana, BPL 2); `DL_`, `HP_`, `PB_`
families exist for the other branches.

**🟡 OPEN — what B / G / D mean has not been told to me.** Until Daman says,
match the family off a **precedent document for the same kind of paper**, and say
out loud that is what you did. A wrong series is refused safely
(`[SAP -10] … define the numbering series`), so probe rather than guess.

## 3 · `NumAtCard` — the vendor's invoice number, nothing else

**Daman: "whenever this type comes just take the invoice number."**

`26-27/103` — exactly as printed on the bill, prefix and slash and all.

**Not** the `<MON> YY/<bunch>/<amount>` shape type 1 uses. That shape exists to tie
a voucher to its cash-sheet bunch; a type-2 bill is a real vendor document and
carries its own reference.

## 4 · `U_Remarks` — the bare voucher number

**`421`.** Not `VCH 421 - RS 1180`.

**Daman, 2026-09-12: "we wrote 421 for remarks cuz that is the voucher number.
The one I told you on 10 September might be for a different skill."** The
`VCH <no> - RS <amount>` rule belongs to **type 1**; this type carries the number
alone.

## 5 · Description and Comments — both empty, on purpose

**Daman: "leave it empty pls" / "leave it blank pls."**

- the line's **description**: empty. No `ItemDescription`, no free text.
- the header's **`Comments`**: blank. No `BEING EXPENSE BOOKED AGAINST …` line.

Type 1 fills both. This type does not. Do not be helpful here.

## 6 · Dimensions

| Dim | Field | Value | Rule |
|---|---|---|---|
| 1 | `CostingCode` | **`CANOLA`** (Oil) / **`WATER`** (Beverages) | **Daman: when no variety is named on the voucher, an oil bill takes CANOLA and a beverage bill takes WATER** |
| 2 | `CostingCode2` | `MM-YYYY` of the **bill** | `08-2026` |
| 3 | `CostingCode3` | **`FACT_COM`** if the slip says **Common**, else `Factory` | see below |
| 5 | `CostingCode5` | **`HR`** | |

**Dim3 — the slip's word wins (C-0027).** Daman, 2026-09-12: *"if the voucher has
written on it common then we gonna take the budget as factory common."*
`Common` → **`FACT_COM`** (FACTORY COMMON), confirmed active in `OOCR` `DimCode=3`.

The mark is **handwritten, often in a different pen, and often crossed by the
Manager's signature.** On voucher 421 it is a green "Common" sitting in the CREDIT
block under the signature — invisible at full-page zoom. **Read the slip in tiles**
(`ap-rm-pm/bin/zoom.py --dpi 600 --box …`) before deciding Dim3, and say your
confidence if the pen crosses it.

Confirm any code is active before sending it:
`SELECT "OcrCode","OcrName" FROM <DB>.OOCR WHERE "DimCode"=3 AND "Active"='Y';`

## 7 · The expense head — you pick it, and you say so

There is no GRPO here, so nothing is inherited. Use the map in `cash-voucher` §7
and **state out loud that you chose the head** rather than inherited it.

Voucher 421: "Internet Service at Site" → **`5680003` TELEPHONE MOBILE AND
INTERNET**, which is what the map says and what the precedent used.

`5680000 GENERAL EXPENSES` is not a bucket (C-0071).

### The commonest type-2 voucher is a Porter / courier trip

A **SmartShift (Porter)** receipt is a registered vendor's GST invoice, so it is
this type — `CardCode` **`VENDA000531`**, `NumAtCard` = the **`CRN…`** number
printed on it.

| Field | Value |
|---|---|
| G/L | **`5680028` FREIGHT INWARD-INDIRECT** — goods coming IN. *Not* `5670001`, which is the Delhi **sales-dispatch** flow (Dim5 `DL`, Dim3 `Sales RE`) |
| Tax | **reverse charge** — the receipt adds no GST to the fare, so `RIGST@5` when the supplier is out of state (GSTIN `07…` vs a Haryana place of supply) and `RCGSG@5` intra-state. `VatSum` 0 |

Precedent: cash-sheet freight vouchers sit on `5680028` with RCM codes and a
bunch-format `NumAtCard` (`JUN 26/35366/700`), SmartShift among them.

**Careful — the ₹ on the bill must equal the ₹ on the voucher.** A supplier's
invoice for a different amount is the *consignment* the trip carried, not what the
cash bought; that voucher is type 3. Voucher 441 (₹186 Rapido fare, clipped to a
₹24,780 Chanchal chemicals bill) is the worked case.

### The bill's PERIOD may split the amount across two months

This type is where period bills arrive — internet, AMC, subscriptions. If the
bill's period crosses a month end, the amount is **prorated by days into one line
per month**, each carrying its own `CostingCode2`. Voucher 421 (12 Aug → 12 Sep,
₹1,000 + 18%) is **625.00 / `08-2026`** and **375.00 / `09-2026`**.

Full recipe and the day-count convention: `cash-voucher` → **A bill for a PERIOD
that crosses a month**. The header — `DocDate`, `TaxDate`, `Series`, `NumAtCard`
— does not change.

## 8 · Tax — take it off the bill, do not compute it

Read the bill's own tax block and mirror it.

| Bill shows | `TaxCode` |
|---|---|
| CGST 9% + SGST 9% (supplier and JIVO in the same state) | **`CG+SG@18`** |
| IGST (different states) | the matching `IGST@…` |
| **no GST at all** | **`Exampt`** — and then it is not this type; check you are not in `cash-voucher-manual` |

**This type is the exception to the family's tax rule.** Every other cash voucher
takes **`Exampt`** (Daman, 2026-09-12, for all cash-voucher skills); type 2 takes
the bill's own code *because* a registered vendor's GST is the whole reason the
type exists. No GST on the paper means you are in the wrong skill.

Voucher 421: supplier Panipat (06), JIVO branch 2 Sonipat (06) → intra-state →
`CG+SG@18` on a taxable value of ₹1,000 → **VatSum 180**, DocTotal 1,180.

`WTLiable` is `tNO` unless the vendor is `SubjectToWithholdingTax boYES` — the
`add-draft` preview prints both, so read it there.

## 9 · Header constants (Oil, factory)

| Field | Value |
|---|---|
| `BPL_IDAssignedToInvoice` | **2** (FACTORY) |
| `SalesPersonCode` | **38** |
| `LocationCode` (line) | **2** |
| `DocumentSubType` | **`bod_GSTTaxInvoice`** |

## 10 · Attach — the DocScanner pack, one row

The pack is **slip + bill in one PDF**; there is no GRPO file and no cash sheet to
add. One line on the draft's own `Attachments2` row.

Upload with `sapb1 attach <pack> --yes` (recipe: `ap-rm-pm/reference/attachments-upload.md`).
The traps that bit here:

- `sapb1 attach` ticks **`CopyToTargetDoc = 'tYES'` on every line, every book** (C-0090)
  and, where `ATC1` has them (Oil, Bev), stamps `U_CHK = <size KB>`, `U_CHK2 = 'OK'` —
  without that SAP refuses the `AttachmentEntry` patch with `-1116 (1120025)` (C-0082).
- Each **file** must be under 1 MB. Voucher 421's pack was 922 KB and went as-is;
  re-render a fatter one per `cash-voucher` §8 and say the attached copy is a
  re-render.
- Prove it: pull `$value` back and `cmp` — byte-identical or it did not work.

Name it `CASH-VCH-<no>-<dd-mm-yyyy>.pdf`.

## 11 · ₹10,000 cap

No cash-voucher document may exceed **₹10,000** — one document, one voucher. If a
voucher is over, **stop and tell the operator**; never split it and never merge
vouchers. (s.40A(3): cash expenditure over ₹10,000 to one person in one day is
disallowed.)

## 12 · Where the draft actually is — operators cannot find it

This cost real time on 2026-09-12. **The posting date is the gate stamp, which is
usually a PREVIOUS month**, so the Document Drafts Report's default date range
shows nothing. Tell the operator all four filters:

```
Purchasing - A/P → Purchasing Reports → Document Drafts Report
  ☑ A/P Invoice          ☑ Open Only
  User          = the login that created it
  Posting date  = a range that covers the GATE STAMP month
```

Fastest: **Find on the A/P Invoice draft by `DocNum`.**

**Report `DocEntry`, never `DocNum`** — all drafts in one series share the same
provisional `DocNum`.

## 13 · Stop at the draft

`WddStatus` stays `-`.

**🛑 SETTLED 2026-09-19 · C-0101 — a cash-voucher batch STOPS AT THE DRAFT.**

Daman, asked directly whether to hold the batch: *"Hold the batch at draft, wait
for my approval."* Build the draft, attach the bill, add it to the list, and
**wait for his word on that list** before `sapb1 add-draft`.

Cash vouchers are the **one documented exception** to `CLAUDE.md`'s rule that a
bill is not finished until the approver has it — every other bill still goes
draft → attach → submit the same day.

Why: once a draft is in the approval queue SAP refuses to delete it (**-10**),
refuses to change its party (**-2028**) and cannot drop a line. On 2026-09-19 ten
drafts were submitted in nine seconds, problems surfaced 33 minutes later, and
four of them are still stuck waiting for Bhawani to reject them. Held at the
draft it would have been one clean delete-and-rebuild.

---

## Worked example — voucher 421, end to end

Paper: **JIVO WELLNESS voucher 421**, dated 27/8/26, "Cash Paid to Sumit ji for
Internet Service at Site. (Party: Sunrise Internet) Bill No. 103", ₹1,180, marked
**Common** in green · **SUNRISE INTERNET PVT LTD** tax invoice `26-27/103` dated
13-08-2026, MONTHLY NETWORKING BILL 12 Aug → 12 Sep, HSN 9984, ₹1,000 + CGST 90 +
SGST 90 = ₹1,180, gate stamp `G.No.155 Date 17/8/26`.

```json
{ "CardCode": "VENDA001500",
  "DocType": "dDocument_Service", "DocumentSubType": "bod_GSTTaxInvoice",
  "Series": 3684,
  "DocDate": "2026-08-17", "TaxDate": "2026-08-13", "DocDueDate": "2026-08-17",
  "NumAtCard": "26-27/103",
  "BPL_IDAssignedToInvoice": 2, "SalesPersonCode": 38, "WTLiable": "tNO",
  "DocumentLines": [
    { "AccountCode": "5680003", "UnitPrice": 1000, "TaxCode": "CG+SG@18",
      "LocationCode": 2,
      "CostingCode": "CANOLA", "CostingCode2": "08-2026",
      "CostingCode3": "FACT_COM", "CostingCode5": "HR",
      "U_Remarks": "421" } ] }
```

→ Oil draft **56919** (`DocNum` 626084439), ₹1,180, VatSum 180, attachment row
177007 read back byte-identical, `WddStatus '-'`.

---

## What I got wrong, so nobody repeats it

Built against the paper alone, before Daman corrected it:

| # | Field | I had | Correct | Root cause |
|---|---|---|---|---|
| 1 | `CostingCode3` | `Factory` | **`FACT_COM`** | did not tile-zoom the slip; the green "Common" was under the Manager's signature and I took a precedent document's value instead of the paper (C-0027, again) |
| 2 | Posting date | would have used the **slip's 27/8** | **17-08, the gate stamp** | carried type 1's rule across to a type that does not share it |
| 3 | `U_Remarks` | would have written `VCH 421 - RS 1180` | **`421`** | same — applied type 1's rule to type 2 |

**The pattern: type 1's rules do not transfer.** The two types share a name and a
slip and nothing else. Check which type you are in before reaching for any rule.

Honest note on how this one was built: the voucher had **already been entered** by
another operator (draft 56898, USER08), and its number was pencilled on the slip.
Most of the field values above were read off that document, not derived. Where a
rule here says "Daman said", he said it; everywhere else, treat it as **one
precedent** and check it against the next voucher.

---

## Pre-flight — tick before `--yes`

- [ ] **no GRPO** behind this voucher, searched in all three books (C-0073)
- [ ] `CardCode` = the **vendor on the letterhead**, in **this** book — never the
      imprest card
- [ ] `DocType` `dDocument_Service`, `DocumentSubType` `bod_GSTTaxInvoice`
- [ ] `DocDate` = the **gate stamp** on the bill
- [ ] `TaxDate` = the **bill's** date
- [ ] `Series` = `HR_G<MMYY>` for the posting month, period open
      (`OFPR.PeriodStat='N'`); if patched, **`TaxDate` re-sent and read back**
- [ ] `NumAtCard` = the **bill number exactly as printed**
- [ ] `U_Remarks` = the **bare voucher number**
- [ ] line description **empty**, header `Comments` **blank**
- [ ] Dim1 `CANOLA` (oil) / `WATER` (bev); Dim2 = bill's month; Dim3 from the
      **tile-zoomed slip**; Dim5 `HR`
- [ ] expense head chosen from the map, and **said out loud** that it was chosen
- [ ] `TaxCode` mirrors the **bill's own tax block**; VatSum matches the bill
- [ ] `UnitPrice` set, not `LineTotal`
- [ ] document **≤ ₹10,000**
- [ ] attachment row carries the pack, < 1 MB, `U_CHK2='OK'`, `$value` `cmp`'d
- [ ] **`DocEntry` reported**, with the Document Drafts Report filters (§12)
- [ ] **not submitted** — §13 is still open
