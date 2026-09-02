---
type: document
sap_tables: [OPCH, PCH1, PCH12, PCH3]
objtype: 18
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# A/P Invoice — the vendor's bill, entered in our books

> The paper a supplier sends us, turned into a liability and a cost. 24,368 of them
> across the three books. It is the entry Accounts keys most often after receipts, and
> the one where a missed field costs the most.

## At a glance

| | |
|---|---|
| SAP tables | `OPCH` header · `PCH1` lines · `PCH12` tax/address · `PCH3` freight |
| ObjType / TransType | **18** |
| Volume | Oil 16,334 · Mart 4,864 · Bev 3,170 · **24,368** total |
| Last 120 days | Oil 2,051 · Mart 930 · Bev 431 |
| History starts | Oil 2024-09-30 · Mart 2025-01-01 · Bev 2024-10-01 |
| Who keys it | 19 logins in Oil. Three do 68%: `UserSign` 17 (4,164), 16 (4,014), 18 (2,925) → see [[Operators-and-Logins]] |
| Drafted first? | **Yes, always** — 1.02 drafts per posted document |
| Needs approval? | **Yes** — 15,302 approval requests raised for ObjType 18 |
| Comes from paper? | Half. See the split below |

## The one split that decides everything: `DocType`

Every A/P invoice is one of two completely different jobs, and SAP tells you which
in a single character.

| `DocType` | Means | Docs (Oil, 365d) | Item lines | What you type |
|---|---|---:|---:|---|
| **`I`** | **Item** bill — goods | 3,313 | 8,409 of 8,409 (**100%**) | Almost nothing. It comes off a [[GRPO]] |
| **`S`** | **Service** bill — expenses, freight, fees, rent | 4,107 | **0 of 11,184** | Everything. Vendor, amount, GL, tax, dimensions |

That is not an approximation — a service invoice carries **zero** item lines and an item
invoice carries **only** item lines. There is no mixed case. *(Measured: 365-day Oil,
`OPCH` joined to `PCH1`, grouped by `DocType`.)*

Oil is **55% service** by document count (9,562 `S` vs 6,772 `I` over all history). So
the majority of A/P work at JIVO is *not* the easy GRPO-copy case. Plan for the hard one.

## Where it comes from — and how much arrives free

| Base document | Lines (Oil, 365d) | Share |
|---|---:|---:|
| `20` — [[GRPO]] | 11,187 | **57.1%** |
| `-1` — **keyed from scratch** | 8,374 | **42.7%** |
| `18` — another A/P invoice | 32 | 0.2% |

Counting *documents* rather than lines, and treating any hand-keyed line as a hand-keyed
job:

| Kind | Documents | Share |
|---|---:|---:|
| fully keyed | 3,795 | **51.1%** |
| fully copied from a GRPO | 3,622 | 48.8% |
| mixed | 3 | 0.0% |

**Half of all A/P invoices are typed from the paper.** A line copied from a GRPO arrives
with vendor, item, quantity, rate, branch, warehouse and the scanned bill already on it.
A keyed line arrives with nothing.

Downstream: 1,754 Oil lines carry `TargetType` 19, meaning they were later reversed by an
[[AP-Credit-Memo]]. 54.1% of lines were copied onward in some form.

## Before you start — the pre-flight list

Everything to have decided *before* the screen opens. This is the list today's misses
would have caught.

- [ ] **Which company book.** Oil, Mart or Beverages. A vendor's `CardCode` is **not**
      the same across books — see [[Business-Partner-Master]]. Getting this wrong means
      re-keying, not editing.
- [ ] **The vendor's `CardCode`**, found by GSTIN or name, not guessed.
- [ ] **Is it already in SAP?** Check `NumAtCard` for this vendor before anything —
      `NumAtCard` is filled on **99–100%** of invoices with 15,209 distinct values in
      Oil, so it is the real duplicate key. Neetu pre-keys drafts, so a draft may exist.
- [ ] **Item bill or service bill** (`DocType` `I` or `S`) — decides everything below.
- [ ] **Is there a [[GRPO]]?** If yes, copy from it. If no, you are keying 100% of it,
      and a bill with no GRPO and no [[Purchase-Order]] may not be enterable at all.
- [ ] **`DocDate`** = the posting date = the **gate-in date** = the GRPO's `DocDate`.
      Not today. Not the vendor's date. (C-0017, and see the warning in Traps.)
- [ ] **`TaxDate`** = the date printed on the vendor's invoice.
- [ ] **Branch** (`BPLId`) — 6 in Oil, and `FACTORY` is 9,558 of 16,334.
- [ ] **`Series`** for that document type + branch + month → [[Numbering-Series]].
      220 distinct series values appear on Oil A/P invoices. Wrong one = error `-10`.
- [ ] **The GL account** for every service line → [[Chart-of-Accounts]].
- [ ] **The tax code** → 16 values, listed below. Note the two misspelled ones.
- [ ] **The five dimensions**, especially the budget code read off the paper → below.
- [ ] **TDS**: is this vendor and this expense liable? 34% of lines are.
- [ ] **The scan**, ready to attach → [[Attachments]]. If uploading by API, send
      `curl -H 'Expect:'` — without it the Service Layer returns `400 Bad Post content`.

> **Transporter / freight bills are their own sheet.** They are 100 % `DocType S`, 98 %
> copied from a **service GRPO** (one per bilty), and the only field the copy cannot give
> you is TDS. Do not treat them as hand-keyed service bills →
> [[Transport-Bill-Playbook]].

## Fields that matter — header (`OPCH`)

Fill rates are Oil, all history / last 120 days. A dash means empty in every row.

| Field | Reads as | Filled | Required? | Notes |
|---|---|---:|---|---|
| `CardCode` | The vendor | 100% | **yes** | 1,161 distinct. Book-specific |
| `CardName` | Copied from the master | 100% | auto | 1,177 distinct — 16 more than CardCode, so some names were edited on the document |
| `NumAtCard` | **The vendor's own invoice number** | 100% / 99% | **yes** | 15,209 distinct. This is the duplicate check. Blank on staff imprest vouchers, which have no vendor bill |
| `DocDate` | Posting date = gate-in | 100% | **yes** | See C-0017 / C-0022 |
| `TaxDate` | Date on the vendor's paper | 100% | **yes** | 1,043 distinct vs 684 for DocDate — they genuinely differ |
| `DocDueDate` | When we must pay | 100% | auto | From payment terms → [[Payment-Terms-and-Banks]] |
| `DocType` | `I` item / `S` service | 100% | **yes** | The fork in the road |
| `Series` | Numbering series | 100% | **yes** | 220 distinct → [[Numbering-Series]] |
| `BPLId` / `BPLName` | Branch | 100% | **yes** | `2` FACTORY 9,558 · `1` DELHI 4,220 · `5` HARYANA SALES 1,513 · `3` PUNJAB 639 · `6` DELHI ISD 395 · `4` HIMACHAL PRADESH 9 |
| `CtlAccount` | Vendor control account | 100% | auto | 14 values — driven by the vendor, see below |
| `DocTotal` | Gross including GST | 100% | **yes** | |
| `VatSum` | The GST on the bill | 56% / 59% | conditional | **44% of Oil A/P invoices carry no GST at all.** Mart 86%, Bev 45% |
| `Comments` | Free text — what the bill is for | 98% / 87% | in practice yes | 15,566 distinct. People genuinely write here, e.g. `CONVEYANCE MONTH OF JULY-26` |
| `JrnlMemo` | Journal memo | 100% | auto | Only 1,213 distinct — SAP generates `A/P Invoices - <CardCode>`. **Not** a place anyone writes |
| `Rounding` | Rounding applied | 100% | auto | `Y` on 6,784 of 16,334 (42%) |
| `PaidToDate` | Settled so far | 75% / 56% | auto | |
| `GroupNum` | Payment terms | 100% | auto | `-1` on 9,629 (no terms) then `1` on 5,278 |
| `FinncPriod` / `PIndicator` | Fiscal period | 100% | auto | `PIndicator` reads `AUG-26-27`, `JUL-26-27` — the period naming that [[Numbering-Series]] uses |
| `WddStatus` | Approval state | 100% | auto | `P` 14,250 · `-` 2,084 |
| `CANCELED` | **Three-valued** | 100% | auto | `N` 16,108 · `Y` 113 · `C` 113 — see Traps |
| `DocStatus` | Open / closed | 100% | auto | `C` 12,025 · `O` 4,309 — **unreliable**, see C-0019 |
| `ReceiptNum` | Links to the receipt | 46% / 44% | conditional | |
| `DocCur` | Currency | 100% | auto | `INR` 16,237 · `USD` 73 · `EUR` 22 · `AUD` 2 |

### Header fields JIVO never uses

`DiscPrcnt` and `DiscSum` (<1%, and the non-zero values look like rounding artefacts, not
discounts) · `DocTotalFC` / `PaidFC` outside the 97 foreign-currency bills · `selfInv`,
`Exported`, `NetProc`, `submitted`, `PoPrss`, `RevisionPo`, `PickStatus`, `BlockDunn`,
`PayBlock`, `MaxDscn`, `Reserve`, `DeferrTax`, `BoeReserev`, `VATFirst` — all single-valued
across 16,334 rows. SAP offers them; nobody here touches them.

### Header user fields that *are* used — the transporter block

| Field | Filled (Oil all / 120d) | Reads as |
|---|---:|---|
| `U_BilltyNumber` | 7% / **11%** | The LR / bilty number on a freight bill. 1,004 distinct |
| `U_BiltyDate` | 7% / 11% | Bilty date |
| `U_TransporterName` | 7% / 11% | 155 distinct carriers |
| `U_VehicleNoM` | 7% / 11% | Vehicle number, 258 distinct |
| `U_LRNUmber` | 5% / 2% | A second LR field — 99 distinct. *Inferred:* overlaps `U_BilltyNumber`; which one is canonical is an **open question** |
| `U_BOEDate` | 5% / 2% | Bill-of-entry date — import bills, see [[Landed-Costs]] |
| `U_AR_NO` | 4% / 2% | 97 distinct. Purpose **not determined** |
| `U_deldocnum` / `U_deldocdate` / `U_delbranch` | 5% / — | A delivery reference. Not used at all in the last 120 days — *inferred:* abandoned |
| `U_UNE_ACTH` | Oil 1% · **Bev 99–100%** | A Beverages-only add-on field. Purpose **not determined** — see [[Add-on-Tables-and-e-Invoicing]] |

These are rising, not falling: `U_BilltyNumber` runs 11% of recent Oil bills against 7%
all-time. Transporter bills are 340 per 90 days (≈4.4/day) per `acc/INVENTORY.md`.

## Fields that matter — lines (`PCH1`)

Oil has 40,247 lines over 16,334 documents — a shade over 2 lines each.

| Field | Reads as | Filled (Oil all / 120d) | Required? | Notes |
|---|---|---:|---|---|
| `AcctCode` | **The GL account** | **100% / 100%** | **yes** | 161 distinct. On *every* line, item or service. **Codes are not portable across books** — only 437 of Oil's 1,313 postable accounts exist in Mart and Beverages under the same name → [[Chart-of-Accounts]] |
| `TaxCode` | **The GST code** | **100% / 100%** | **yes** | 16 values, below |
| `LocCode` | **Location** | **100% / 100%** | **yes** | Only 5 values. C-0025: `2` = factory / Haryana |
| `WtLiable` | **TDS liable?** | 100% | **yes** | `Y` on 6,401 of 18,957 recent lines (**34%**) |
| `LineTotal` | Line amount | 98% / 97% | **yes** | |
| `Price` | Rate | 98% / 97% | **yes** | |
| `OcrCode` | Dimension 1 — profit centre | 96% / 100% | **yes** | 63 distinct |
| `OcrCode2` | Dimension 2 — **the month** | 74% / 81% | usually | `10-2024`, `01-2026`, `08-2026` … |
| `OcrCode3` | Dimension 3 — **the budget** | 70% / 79% | usually | The C-0027 field. Values below |
| `OcrCode4` | Dimension 4 — **department / channel** | 21% / 26% | sometimes | |
| `OcrCode5` | Dimension 5 — **the state** | 66% / 62% | usually | |
| `ItemCode` | The item | 43% / 49% | item lines only | 1,119 distinct. Zero on service bills |
| `Quantity` | Quantity | 43% / 49% | item lines only | **In pieces, not cartons** — C-0001 |
| `unitMsr` | UoM | 43% | auto | `PCS` 16,023 · `MTS` 854 · `KGS` 182 · `LTR` 72 … |
| `WhsCode` | Warehouse | 43% / 49% | item lines only | 33 distinct → [[Warehouses-and-Locations]] |
| `Dscription` | Line description | 66% / 70% | **yes on service** | 1,953 distinct |
| `HsnEntry` | HSN — goods | 43% / 49% | goods only | 279 distinct |
| `SacEntry` | SAC — services | 33% / 33% | services only | 168 distinct. **Mutually exclusive with HSN** — C-0013 |
| `VatPrcnt` | GST rate | 62% / 61% | auto | `0` ×15,129 · `18` ×12,532 · `5` ×11,015 · `12` ×1,559 · `28` ×12 |
| `VatSum` | GST on the line | 60% / 58% | auto | |
| `BaseType` | Where the line came from | 100% | auto | `20` ×22,125 · `-1` ×17,778 · `18` ×344 |
| `BaseRef` / `BaseEntry` / `BaseDocNum` | The GRPO it came from | 56–58% | auto | |
| `BaseAtCard` | The GRPO's vendor ref | 48% / 64% | auto | 8,995 distinct |
| `U_Remarks` | **Free-text line remark** | 36% / 41% | optional | 7,935 distinct — people really use this. Bev 48% |
| `U_SchemeAgst` | Scheme the line is against | 41% / 49% | conditional | 36 distinct |
| `U_UNE_LTS` | Litres | Oil 18% · **Bev 50%** | conditional | 2,725 distinct |
| `U_ARNO` | A reference number | Oil 23% · **Bev 57%** | conditional | 7,323 distinct. Purpose **not determined** |
| `U_CardCode` | A second party on the line | 19% / 19% | conditional | 362 distinct. *Inferred:* the party the cost belongs to, distinct from the biller |
| `U_Sub_Account` | Sub-account | 16% | conditional | `SALES` ×5,978 · `BST` ×544 · `SALES RETURN` ×35 |
| `U_Recvd_Qty` | **Qty off the paper** | **2% / 3%** | see Traps | Only 704 lines ever. C-0025 asks for it; the books say it is almost never done |

### `VatGroup` is a trap — use `TaxCode`

Both fields look like the tax code. Only one is real:

- `TaxCode` — **100% filled**, 16 values.
- `VatGroup` — **18% filled** in Oil (blank on 28,120 of 40,247 lines, NULL on another
  4,963).

Read the tax code from `TaxCode`. A report keyed on `VatGroup` silently drops four fifths
of Oil's lines.

## The five dimensions — decoded

Nobody had written this down. Each `OcrCode` slot carries a different *kind* of thing, and
the vocabulary is what tells you which:

| Slot | What it actually is | Filled (Oil) | Values (Oil, with counts) |
|---|---|---:|---|
| `OcrCode` | Profit centre | 96% | 63 distinct → [[Cost-Centres-and-Dimensions]] |
| `OcrCode2` | **The month** | 74% | `10-2024` 1,723 · `11-2024` 1,512 · `01-2026` 1,445 · … 30 values, one per month |
| `OcrCode3` | **The budget** | 70% | `Del Bkhp` 8,322 · `Factory` 8,055 · `BackOff` 4,222 · **`FACT_COM` 2,046** · `Sales` 1,983 · `Sales RE` 1,745 · `Med MKT` 591 · `OTE` 386 · `Transprt` 245 · `Del Mayp` 244 · `NPD1` 205 · `NPD3` 182 · `NPD2` 63 · `Interest` 5 · `Sal CF` 3 · `R & D` 2 |
| `OcrCode4` | **Department / channel** | 21% | `Admin` 2,695 · `E-COM` 1,878 · `IT` 872 · `MT` 487 · `CSD` 453 · `GT` 429 · `DIGTAL M` 398 · `Legal` 268 · `Accounts` 258 · `ROI` 194 · `CAL CNTR` 187 · `POP` 177 · `HR_DEPT` 72 · `IMPORT` 56 · `MIS` 54 · `GP-GDWN` 49 · `EXPORT` 25 · `HORECA` 14 · … |
| `OcrCode5` | **The state** | 66% | `HR` 12,487 · `DL` 9,226 · `PB` 2,521 · `UP` 473 · `MH` 313 · `WB` 228 · … 27 states |

`OcrCode3` is the field behind **C-0027**: a handwritten *Common* on a factory bill means
`FACT_COM` (FACTORY COMMON), never the GRPO's `Factory`. The counts show why the mistake
is easy — `Factory` is used four times as often as `FACT_COM`, so inheriting is usually
right and occasionally wrong.

Beverages fills these far more consistently than Oil (`OcrCode2` 90%, `OcrCode3` 89%,
`OcrCode5` 90% versus Oil's 74/70/66). Mart fills them least (35/34/24%). Do not carry a
habit from one book into another.

## Tax — the 16 codes actually in use

From `PCH1."TaxCode"`, Oil, all history:

| Code | Lines | Reads as |
|---|---:|---|
| `Exampt` | 9,935 | Exempt / nil-rated. **Note the spelling** — the master data is misspelled |
| `CG+SG@18` | 7,656 | CGST 9% + SGST 9%, intra-state |
| `IGST@18` | 4,680 | Inter-state 18% |
| `IGST@5` | 4,651 | Inter-state 5% |
| `CG+SG@0` | 4,041 | Intra-state, zero rate |
| `RIGST@5` | 3,000 | **Reverse charge**, IGST 5% |
| `GST05R` | 2,900 | **Reverse charge**, 5% (a second naming) |
| `IGST@0` | 1,141 | |
| `IGST@12` | 782 | |
| `CG+SG@12` | 777 | |
| `CG+SG@5` | 415 | |
| `RISGT@18` | 135 | **Reverse charge**, IGST 18% — **also misspelled** (`RISGT`, not `RIGST`) |
| `RCGSG@18` | 72 | Reverse charge, CGST+SGST 18% |
| `RCGSG@5` | 50 | Reverse charge, CGST+SGST 5% |
| `CG+SG@28` | 8 | |
| `IGST@28` | 4 | |

Six of the sixteen are reverse-charge codes (`R`-prefixed plus `GST05R`), covering 6,157
lines. RCM posts a matched pair — input and output on the same journal — see the GL
fingerprint below.

**Two of these codes are misspelled in the master data** (`Exampt`, `RISGT@18`). Anything
matching on the correct spelling finds nothing. → [[GST-Tax-Codes]]

## TDS

`WtLiable` = `Y` on **6,401 of 18,957** recent Oil lines (**34%**). TDS is a routine part
of A/P here, not an exception.

The journal shows the sections in use, each with its own account:

| Account | Section |
|---|---|
| `2133022` | TDS @ 0.1% 393(1)[8(ii)] code 1031 — 169 lines |
| `2133018` | TDS on contractor others @ 2% 393(1)[6(ii)] code 1024 — 161 |
| `2133010` | TDS @ 0.1% 194Q — 133 |
| `2133006` | TDS on contractor others @ 2% 194C — 107 |
| `2133019` | TDS on commission or brokerage @ 2% 393(1)[1(ii)] code 1006 — 67 |

> [!warning] Those are **Oil** codes, and they are **post-2026-06-01** codes.
> TDS was renumbered on 2026-06-01 and the new section-393(1) numbering **differs per
> book**: contractor-others @2% is `2133018` in Oil, `2133021` in Mart, `2133016` in
> Beverages. Even in the old block the numbers diverged — `2133009` meant technical
> services @2% 194JA in Oil and Beverages but @0.05% 194C in Mart.
> **Identify a TDS account by its name, never by its number.** → [[TDS-Withholding]]

### The CLI trap — and the fix, proven live

Correction C-0018 records that a draft created through `sapb1 draft purchase-invoice` comes
out with TDS 0. **That is a payload defect, not a limit of the API path** — and the fix is
one field.

Draft **54937** (the C-0018 case) sent no withholding block at all, so TDS was 0. Draft
**55177** (GAAP & Associates, 2026-08-24) sent just this:

```json
"WithholdingTaxDataCollection": [ { "WTCode": "1027" } ]
```

…plus `WTLiable: "tYES"` on the line. **SAP computed the rest by itself** — verified by
reading the draft back:

| Field | Value |
|---|---|
| `WTCode` | `1027` |
| `TaxableAmount` | 1,00,000 |
| `WTAmount` | **10,000** (SAP derived the 10% rate) |
| `DocTotal` | **1,08,000** — i.e. 1,00,000 + 18% GST − 10,000 TDS |

So: **send the `WTCode` and let SAP do the arithmetic.** You do not need to compute the
rate, the base or the account.

> [!warning] Read back `WTAmount`, **not** `WTApplied`.
> On draft 55177 `WTAmount` is 10,000 while `WTApplied` and `AppliedWTAmount` are both **0**
> — `WTApplied` only fills when the document posts. Anyone checking `WTApplied` on a draft
> concludes TDS is missing when it is there. This is why C-0018 says check **`WTAmount`**.

And the flag alone does nothing: **67 hand-keyed Oil drafts since 2026-06-01 carry
`DRF1."WtLiable"` = `Y` with zero withholding rows.** The line flag without the header
collection produces no TDS. → [[TDS-Withholding]]

## The journal it posts

TransType 18. Oil, 365 days: **7,420 journals, ~33,000 lines**, balanced Dr = Cr.

Line count per journal — an unusual count is the cheapest signal something was keyed
differently:

| Lines | Journals |
|---:|---:|
| 5 | 1,864 |
| 6 | 1,401 |
| 4 | 1,284 |
| 2 | 1,269 |
| 3 | 1,050 |
| 7+ | ~570 |

The accounts, 120-day Oil window:

| Account | Name | Lines | Side | What it is |
|---|---|---:|---|---|
| `2140001` | Goods received but not invoiced | 617 | Dr | **GRNI** — the receipt parked the cost here; the bill clears it |
| `2110004` | Sundry creditor service | 863 | Cr | The liability, service vendors |
| `2110005` | Sundry creditor domestic purchase | 575 | Cr | |
| `2110003` | Sundry creditor staff | 345 | Cr | Imprest / expense claims |
| `2110001` | Sundry creditor domestic oil | 202 | Cr | |
| `5680014` | **Short and excess** | **1,091 of 2,051** | both | See Traps |
| `2131012` / `2131011` | Input CGST / SGST @ 9% | 505 each | Dr | Always paired |
| `2131004` | Input IGST @ 18% | 430 | Dr | |
| `2131002` | Input IGST @ 5% | 246 | Dr | |
| `2137109` / `2137509` | Input IGST @5% **RCM** / Output IGST @5% RCM | 95 each | Dr / Cr | The RCM pair, equal and opposite |
| `5670001` | Freight & cartage outward | 660 | Dr | The biggest single expense account |
| `5640001` | Advertisement | 55 | Dr | ₹2.41 Cr in 120 days — small count, large value |

Dimensions the journal carries: `ShortName` (the vendor subledger) on 100% of lines,
`BPLId` on 100%, and the `OcrCode` family on 23–26%.

> [!important] That 23–26% is **misleading if you read it as "dimensions are optional"**.
> Dimensions live on the **expense line only**, and there they are effectively mandatory:
> every one of the 31 indirect-expense accounts with 20 or more lines is at **100%** for
> dimension 1 (Variety), 2 (Effective Month) and 3 (Budget). The average is dragged down by
> the 3,921 undimensioned `5680014` rounding lines and by GRPO-sourced `5400xxx` purchase
> lines. GST, TDS and creditor-control lines carry **no** dimensions at all — by design.
> Dimension 4 (Sub Budget) is the only genuinely optional one.
> → [[Cost-Centres-and-Dimensions]]

**How to tell a correct posting from a plausible-but-wrong one:** the vendor's control
account must be credited with the gross; the GRNI account must be debited only for the
portion that came off a GRPO; input GST must land in an *input* account (`2131xxx`), and an
RCM code must produce **two** lines, not one.

`JrnlMemo` is auto-generated (`A/P Invoices - <CardCode>`, only 1,213 distinct across
16,334 documents). It carries no information. The information is in `Comments` on the
header and `U_Remarks` on the line.

## The control account is the vendor's, not the group's

`CtlAccount` takes 14 values in Oil and is filled automatically — but it comes from the
**business partner**, and the vendor group only predicts it:

| Vendor group | Control account | Docs (365d) |
|---|---|---:|
| SERVICE | `2110004` Sundry creditor service | 1,674 |
| PURCHASE | `2110005` Sundry creditor domestic purchase | 1,564 |
| STAFF VENDOR | `2110003` Sundry creditor staff | 1,334 |
| E-COMMERCE | `2110004` | 643 |
| PURCHASE OIL | `2110001` Sundry creditor domestic oil | 623 |
| TRANSPORTER | `2110004` | 403 |
| BRANCH VENDOR | `2120002` JIVO Wellness Haryana | 254 |
| SERVICE | `2110008` **Sundry creditors clearing** | 95 |
| PURCHASE OIL | `2110005` | 93 |
| FIXED ASSETS | `2110005` / `2110004` | 53 / 51 |
| E-COMMERCE | `2121002` **Sundry creditors Jivo Mart** | 32 |

The same group maps to different accounts (SERVICE → `2110004`, `2110008` *and* `2110005`),
because the group is only a **default** that Accounts overrides per vendor.

The actual source is the vendor card: `OPCH."CtlAccount"` equals `OCRD."DebPayAcct"` on
**16,285 of 16,334** Oil A/P invoices (**99.7%**). So **if a control account looks wrong,
the vendor card is wrong — fix the card, never override the document.**

Also worth knowing: this ranking is a *vendor-population* ranking, not a money ranking. The
money runs the other way — `2110001` DOMESTIC OIL took **₹198.04 Cr** across 633 documents
while `2110004` SERVICE took ₹14.29 Cr across 3,166.

The `212xxxx` accounts are inter-branch and `2121xxx` are intercompany → C-0020,
[[Business-Partner-Master]].

## Traps

1. **`CANCELED` has three values, not two.** Oil: `N` 16,108, `Y` 113, `C` 113. Every
   cancellation creates a mirror row. A `<> 'Y'` filter keeps the mirrors and
   double-counts. Always test `= 'N'`. **(C-0021)**
2. **`DocStatus = 'O'` does not mean unpaid.** Documents settled by manual journal or by
   an unapplied on-account payment stay open. Age from `OCRD."Balance"`, not from open
   documents. **(C-0019)** Oil has 4,309 "open" A/P invoices; treat that number as
   meaningless on its own.
3. **`DocDate` = gate-in date is a posting *rule*, not a description of the books.**
   C-0017 says post on the GRPO's date. C-0022 measured that this actually holds on only
   51% of Oil pairs, 84% Mart, **21% Bev**. So: follow the rule when posting; never
   *infer* a gate-in date from an existing invoice.
4. **`5680014` SHORT AND EXCESS appears on more than half of all A/P journals — and it is
   SAP's rounding account, not a shortage or a claim.** The line amount equals
   **`|OPCH."RoundDif"|` to the paisa on all 3,921 Oil A/P lines in 365 days**, and the
   count of documents with a non-zero `RoundDif` is the same 3,921 — one-to-one. 3,904 of
   the lines are under ₹1; the largest in a whole year is ₹58.88; the year totals ₹665 Dr
   and ₹442 Cr. And **no operator ever types it**: zero `PCH1` lines in a year carry
   `AcctCode` = `5680014`. SAP adds it.

   The header `Rounding` flag is **not** the trigger — 1,130 documents are `Rounding` = `N`
   with a non-zero `RoundDif` and still get the line. `RoundDif` is what decides.

   The real inventory-variance account is **`5000048` STOCK SHORT AND EXCESS** (Oil only —
   and that same code is COGS TEA in Mart). Do not confuse them, and do not chase `5680014`
   at month-end. → [[Chart-of-Accounts]]
5. **`U_Recvd_Qty` is asked for and almost never filled.** C-0025 says put the paper's
   litres/quantity there on service lines. Reality: 704 lines ever, 2% of Oil, 3% recent.
   Either the correction describes an intention rather than a practice, or the field is
   only for a narrow subset. **Ask an operator before treating it as required.**
6. **A CLI-created draft comes out with TDS 0** even when the vendor is liable, and 34%
   of lines are. Check `WTAmount` before Add. **(C-0018)**
7. **Two tax codes are misspelled in the master** — `Exampt` and `RISGT@18`.
8. **`VatGroup` is 18% populated; `TaxCode` is 100%.** Use `TaxCode`.
9. **A vendor's `CardCode` differs between books.** Nexton is `VENDA001548` in Oil and
   `VENDA001235` in Beverages with the same GSTIN. Never carry a code across books.
10. **44% of Oil A/P invoices have no GST** (`VatSum` empty). That is normal here — exempt
    purchases and RCM — not a data defect. **(C-0016)**

## How to create one from the CLI

Draft only. Never `post` a document-shaped entity.

```bash
# 1. Pre-check first — the skill's precheck finds the GRPO, branch, series and any
#    existing draft before anything is sent.
#    Use the jivo-ap-draft skill; do not hand-roll the payload.

# 2. What the payload must carry (beyond the obvious):
#    Series                -> from NNM1 for (ObjType 18, branch, month)
#    DocumentSubType       -> bod_GSTTaxInvoice
#    DocDate               -> the GRPO's DocDate (gate-in), NOT today
#    TaxDate               -> the vendor's invoice date
#    NumAtCard             -> the vendor's invoice number, exactly as printed
#    BPLID                 -> the branch
#    per line: AccountCode, TaxCode, LocationCode, CostingCode..CostingCode5,
#              and U_Recvd_Qty on service lines
```

Then **read it back**. SAP silently leaves things blank — `WTAmount` for TDS is the known
one. → [[AP-Invoice-Playbook]], and the `jivo-ap-draft` skill, which was built from live
mistakes on 2026-08-21.

## Verify after saving

- [ ] **`WTAmount`** — is TDS there if the vendor is liable? (Not `WTApplied`, which is 0 on
      every draft by design.)
- [ ] `DocTotal` matches the paper's gross to the paisa.
- [ ] `VatSum` matches the paper's GST, and the input GST accounts are *input* accounts.
- [ ] An RCM code produced **two** journal lines.
- [ ] Line count on the journal is in the normal 2–6 band.
- [ ] `CostingCode3` matches the handwritten allocation, not the GRPO's default. **(C-0027)**
- [ ] The attachment is on the draft, with `U_CHK2` = `OK`. **(C-0026)**
- [ ] `NumAtCard` is populated and not a duplicate.

## Open questions

1. Is `U_Recvd_Qty` genuinely required on service lines, given it is filled on 2%?
2. `U_BilltyNumber` versus `U_LRNUmber` — which is canonical for a freight bill?
3. What are `U_AR_NO` (header, 97 values) and `U_ARNO` (line, 7,323 values)? Different
   fields with nearly the same name, and the line one is filled on 57% of Beverages lines.
4. What is `U_UNE_ACTH`, filled on 99–100% of Beverages invoices and almost nothing in Oil?
5. Why does Beverages fill the dimensions at ~90% and Mart at ~30%? Different policy, or
   different automation?
6. `CardName` has 16 more distinct values than `CardCode` — which documents had the vendor
   name edited by hand, and does that matter for GST?

## Queries used

```sql
-- the DocType split: is 'S' really service?
SELECT H."DocType", COUNT(DISTINCT H."DocEntry") DOCS,
       SUM(CASE WHEN L."ItemCode" IS NOT NULL AND L."ItemCode"<>'' THEN 1 ELSE 0 END) ITEM_LINES,
       COUNT(*) ALL_LINES
FROM "JIVO_OIL_HANADB"."OPCH" H
JOIN "JIVO_OIL_HANADB"."PCH1" L ON L."DocEntry"=H."DocEntry"
WHERE H."DocDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY H."DocType";

-- TDS liability on lines
SELECT "WtLiable", COUNT(*) N FROM "JIVO_OIL_HANADB"."PCH1"
WHERE "DocDate" >= ADD_DAYS(CURRENT_DATE,-365) GROUP BY "WtLiable";

-- vendor group -> control account (it is NOT one-to-one)
SELECT G."GroupName", H."CtlAccount", MAX(A."AcctName") NM, COUNT(*) N
FROM "JIVO_OIL_HANADB"."OPCH" H
JOIN "JIVO_OIL_HANADB"."OCRD" C ON C."CardCode"=H."CardCode"
JOIN "JIVO_OIL_HANADB"."OCRG" G ON G."GroupCode"=C."GroupCode"
LEFT JOIN "JIVO_OIL_HANADB"."OACT" A ON A."AcctCode"=H."CtlAccount"
WHERE H."DocDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY G."GroupName", H."CtlAccount" ORDER BY N DESC;

-- SHORT AND EXCESS: rounding sink or real variance?
SELECT COUNT(*) LINES, SUM(L."Debit") DR, SUM(L."Credit") CR,
       MAX(L."Debit") MAXDR, MAX(L."Credit") MAXCR,
       SUM(CASE WHEN L."Debit"<1 AND L."Credit"<1 THEN 1 ELSE 0 END) SUB_RUPEE
FROM "JIVO_OIL_HANADB"."OJDT" J
JOIN "JIVO_OIL_HANADB"."JDT1" L ON L."TransId"=J."TransId"
WHERE J."TransType"=18 AND L."Account"='5680014'
  AND J."RefDate" >= ADD_DAYS(CURRENT_DATE,-365);
-- 3,921 lines, 3,904 of them under Rs 1, year total Rs 665 Dr / Rs 442 Cr

-- ...and does it track the Rounding flag?
SELECT H."Rounding", COUNT(DISTINCT H."DocEntry") DOCS,
       SUM(CASE WHEN X."TransId" IS NOT NULL THEN 1 ELSE 0 END) WITH_SHORTEXCESS
FROM "JIVO_OIL_HANADB"."OPCH" H
LEFT JOIN (SELECT DISTINCT "TransId" FROM "JIVO_OIL_HANADB"."JDT1"
           WHERE "Account"='5680014') X ON X."TransId"=H."TransId"
WHERE H."DocDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY H."Rounding";
-- Y: 2,791 of 2,831 (98.6%)   N: 1,130 of 4,589 (24.6%)
```

Field fill rates, value vocabularies, the GL fingerprint and the copy-from split all come
from the mined corpus, reproducible with:

```bash
python3 sap-b1/entry-vault/bin/profile.py OPCH --co OIL,MART,BEV --days 120 --vocab-max 30
python3 sap-b1/entry-vault/bin/profile.py PCH1 --co OIL,MART,BEV --days 120 --vocab-max 30
python3 sap-b1/entry-vault/bin/gl.py 18 --co OIL --days 365 --memo
python3 sap-b1/entry-vault/bin/flow.py OPCH --co OIL --days 365
python3 sap-b1/entry-vault/bin/sample.py OPCH --n 3 --co OIL
```
