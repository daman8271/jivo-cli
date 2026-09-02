---
type: foundation
sap_tables: [OPCH, ORPC, OPDN, OINV, OPOR, PCH1]
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Field-name Rosetta — the same thing has four different names

> The paper calls it one thing. The SAP screen calls it another. The API wants a third
> name. The database stores it under a fourth. **Nothing warns you** — a wrong name just
> silently finds nothing, or writes nowhere.

This is the note that stops the guessing. Every mapping below was derived from live data,
not from documentation.

## Why this is not a curiosity

`OriginalRefNo` — the field correction **C-0024** says you must always set on a credit
memo — is stored in a HANA column called **`RevRefNo`**. The two names share no substring.

So anyone who checked "are we filling the original reference?" by searching the database for
a column called `Original*` found **nothing**, and would have reported that the field is
never populated and the correction is being ignored. It is populated on **97%** of A/P
credit memos. The audit was looking in the wrong place, and the answer it would have given
was the opposite of the truth.

*(And once you can see the field, the interesting finding is not the fill rate but its
shape: on A/R credit memos SAP appears to make the pair mandatory whenever the buyer carries
a GSTIN — 5,055 B2B documents across three books, zero blanks — while leaving it optional
otherwise. See [[AR-Credit-Memo]].)*

That is the cost of a name mismatch: not confusion, but a confident wrong answer.

## Derive it, don't guess it

`bin/rosetta.py` reads the **same real document through both doors** — the Service Layer
and HANA — and matches on **value**. Names lie; values do not. A property and a column
holding the identical value on the same document are the same field.

```bash
# from the repo root
python3 sap-b1/entry-vault/bin/rosetta.py PurchaseCreditNotes ORPC --co OIL --n 8
python3 sap-b1/entry-vault/bin/rosetta.py PurchaseInvoices OPCH --n 8 --out ../_data/rosetta-OPCH.md
```

**Choosing documents matters more than sampling more of them.** Two fields that happen to
hold the same value on every document you looked at come out *ambiguous*, and the fix is a
document where they **differ**. That is exactly what happened here: on eight consecutive
credit memos the vendor's own number and the original invoice number were identical, so
`OriginalRefNo` matched both `NumAtCard` and `RevRefNo`. One predicate separated them:

```bash
python3 sap-b1/entry-vault/bin/rosetta.py PurchaseCreditNotes ORPC --n 8 \
  --where '"NumAtCard" <> "RevRefNo" AND "RevRefNo" IS NOT NULL'
# -> OriginalRefNo = RevRefNo, OriginalRefDate = RevRefDate
```

That found in one command what cost an hour by hand.

> [!note] A bug worth knowing about, in case you extend the tool.
> The first version intersected candidate columns across **all** sampled documents,
> including ones where the property was NULL — so a field blank on a single sampled line
> lost its mapping entirely. That silently hid `CostingCode4`, `CostingCode5` and
> `AccountCode`. The rule is now: **a property is only judged on the pairs where it actually
> had a value.** Fixing it took the line map from 7 renamed pairs to 9, and the header maps
> from 12 to 15. A tool that under-reports is worse than one that reports nothing, because
> the gap looks like an answer.

## Layer 1 — API property ↔ HANA column

**33 distinct renamed pairs**, derived across nine entity maps: `PurchaseInvoices`/`OPCH`,
`PurchaseCreditNotes`/`ORPC`, `PurchaseDeliveryNotes`/`OPDN`, `Invoices`/`OINV`,
`PurchaseOrders`/`OPOR`, `IncomingPayments`/`ORCT`, `VendorPayments`/`OVPM`, `Drafts`/`ODRF`,
and the line map `DocumentLines`/`PCH1`. 8 documents each, Oil. A pair had to agree on every
document where the property actually had a value.

The **Seen on** column is how many of the nine maps confirmed the pair — a 6 or 8 means it
is a general SAP convention, a 1 means check it for your entity.

| API property (what you **send**) | HANA column (what you **query**) | Seen on | Why it bites |
|---|---|---:|---|
| `OriginalRefNo` | **`RevRefNo`** | 1 | C-0024's field. No shared substring |
| `OriginalRefDate` | **`RevRefDate`** | 1 | Same |
| `ContactPersonCode` | **`CntctCode`** | 8 | |
| `SalesPersonCode` | **`SlpCode`** | 7 | Header **and** line |
| `BPL_IDAssignedToInvoice` | **`BPLId`** | 6 | The branch |
| `ControlAccount` | **`CtlAccount`** | 6 | The vendor liability account — **but see payments below** |
| `DocCurrency` | **`DocCur`** | 6 | **`DocCurr`** on payments |
| `FinancialPeriod` | **`FinncPriod`** | 6 | |
| `JournalMemo` | **`JrnlMemo`** | 6 | **`JournalRemarks`** on payments |
| `LanguageCode` | **`LangCode`** | 6 | |
| `PeriodIndicator` | **`PIndicator`** | 6 | The `AUG-26-27` period name |
| `AttachmentEntry` | **`AtcEntry`** | 5 | C-0026's field — the scan link |
| `DraftKey` | **`draftKey`** | 5 | Note the lower-case `d` |
| `ShipFrom` | **`ShipToCode`** | 5 | Semantically odd, but measured across 557 distinct values — on a *purchase* document "ship from" **is** the vendor address |
| `DataVersion` | **`DataVers`** | 4 | |
| `TransNum` | **`TransId`** | 4 | The journal key — how you reach the GL side |
| `PaymentGroupCode` | **`GroupNum`** | 3 | Payment terms — unguessable |
| `DocumentsOwner` | **`OwnerCode`** | 1 | |
| `Reference1` | **`Ref1`** | 1 | |

### On **lines** (`DocumentLines` ↔ `PCH1`) — 29 real line pairs

Every field an operator decides on a line is renamed. All nine:

| API property (what you send on a line) | HANA column |
|---|---|
| `AccountCode` | **`AcctCode`** — the GL account |
| `LocationCode` | **`LocCode`** — C-0025's field |
| `CostingCode` | **`OcrCode`** — dim 1, profit centre |
| `CostingCode2` | **`OcrCode2`** — dim 2, the month |
| `CostingCode3` | **`OcrCode3`** — dim 3, **the budget** (C-0027) |
| `CostingCode4` | **`OcrCode4`** — dim 4, department |
| `CostingCode5` | **`OcrCode5`** — dim 5, the state |
| `SalesPersonCode` | **`SlpCode`** |
| `VisualOrder` | **`VisOrder`** |

Note the pattern: **the API says `CostingCode`, the screen says Dimension/Budget, HANA says
`OcrCode`.** Three names for the field that caused one of today's misses.

Same on both sides (safe to assume): `CardCode`, `CardName`, `Comments`, `DocDate`,
`TaxDate`, `DocDueDate`, `DocTotal`, `NumAtCard`, `Series`, `BPLName`, `VATRegNum`,
`DocEntry`, `DocNum`.

### The same concept is renamed **per entity type** — this is the worst one

Payments are not documents, and SAP renames the same fields for them. Derived from
`IncomingPayments`/`ORCT` and `VendorPayments`/`OVPM`, 8 documents each:

| The concept | On a **document** (invoice, credit memo, GRPO, order) | On a **payment** (incoming, outgoing) | HANA column |
|---|---|---|---|
| Free-text remark | `Comments` | **`Remarks`** | `Comments` on both |
| Vendor/customer control account | `ControlAccount` → `CtlAccount` | `ControlAccount` → **`BpAct`** | **different column entirely** |
| Journal memo | `JournalMemo` | **`JournalRemarks`** | `JrnlMemo` on both |
| Branch | `BPL_IDAssignedToInvoice` | **`BPLID`** (all-caps `ID`) | `BPLId` on both |
| Currency | `DocCurrency` → `DocCur` | `DocCurrency` → **`DocCurr`** | **one letter apart** |
| Transfer account | — | `TransferAccount` → `TrsfrAcct` | payments only |

Read that table twice. **A payment written with `Comments` instead of `Remarks` sets
nothing, and SAP does not complain** — the property is simply ignored. The same goes for
`JournalMemo` on a payment and `BPL_IDAssignedToInvoice` on a payment.

The HANA side has its own version of the joke: document tables store currency in `DocCur`,
payment tables in `DocCurr`, and the control account is `CtlAccount` on a document but
**`BpAct`** on a payment. A query written for one and pointed at the other fails with
*invalid column name* — which is at least loud. The API version is silent.

So: **never carry a property name from a document to a payment.** Run the rosetta for the
entity you are actually writing.

### Two more traps in this layer

- **`DocumentStatus` vs `DocStatus`.** The API says `DocumentStatus` with values
  `bost_Open` / `bost_Close`; HANA says `DocStatus` with `O` / `C`. And on a **draft** the
  API's cancelled state (`dasCancelled`) is HANA's **`WddStatus = 'C'`**, not the `CANCELED`
  column — which on a draft is always `N` and carries no information.
  → [[Document-Drafts]]
- **`Cancelled` is spelled with two `l`s on every API entity**, including payments, whose
  HANA columns say `Canceled` with one. And in HANA it is three-valued (`N`/`Y`/`C`), not a
  boolean. **(C-0021)**

## Layer 1b — the same *entity* under different codes: the cross-book maps

Renaming is not only about fields. **The same vendor has a different `CardCode` in each
book**, and the same GL account can have a different number — which is the identity version
of the same problem.

There are undocumented UDFs that map across, and the fixed profiler surfaced them by
detecting columns that exist in one book and not another:

| Map | Lives in | Points at | Filled | Resolves |
|---|---|---|---:|---|
| `OCRD."U_OIL_CardCode"` | **Beverages** | Oil's `CardCode` | 2,417 of 2,964 (82%) | **2,414** resolve · 2,380 same name (98.5%) |
| `OCRD."U_WG_CardCode"` | **Oil** | mostly **Beverages** | 2,413 of 3,411 (71%) | 2,412 in Bev · 2,093 also in Mart |
| `OACT."U_WG_GLNO"` | **Oil** | Beverages' account | 494 of 1,429 (35%) | all 494 exist · 462 same name |
| `OACT."U_OIL_GLNO"` | **Beverages** | Oil's account | — | the reverse direction |

So a bidirectional partner map and a bidirectional account map both exist, and where
populated they are accurate — 98.5% name agreement is not an accident.

> [!warning] But it is **not** an authority, and here is why.
> The canonical example of the problem — Nexton, `VENDA001548` in Oil and `VENDA001235` in
> Beverages, same GSTIN — has **`U_WG_CardCode` NULL in Oil and `U_OIL_CardCode` NULL in
> Beverages.** The map is missing exactly the case everyone quotes.
>
> Treat these fields as a **hint that saves a lookup when present**, never as the lookup
> itself. **Match on GSTIN.** → [[Business-Partner-Master]]

*(These columns appear in no SAP documentation. They were found by the profiler's
schema-drift check, which reports columns present in one book and absent in another — a
check that only exists because the earlier version of the tool rendered "column absent" and
"column empty" identically. 45 of 73 profiles report drift.)*

## Layer 2 — SAP screen label ↔ field

What the operator sees in the SAP B1 client, and what it actually is. *(Screen labels are
from the client and the paper trail rather than from a query — treated as **conventional**,
not measured. The field side is measured.)*

| Screen label | Field | Note |
|---|---|---|
| Vendor Ref. No. | `NumAtCard` | The vendor's own invoice number. **Our duplicate key** — 15,209 distinct in Oil |
| Posting Date | `DocDate` | = the gate-in date = the [[GRPO]]'s date. **(C-0017)** |
| Document Date | `TaxDate` | The date printed on the vendor's paper |
| Due Date | `DocDueDate` | Derived from payment terms |
| Original Ref. No. / Date | `RevRefNo` / `RevRefDate` | **(C-0024)** |
| Branch | `BPLId` | Group by the **id**, never `BPLName` — GRPOs carry `FACTORY` and `Factory` as separate strings |
| Series | `Series` | **Book-local**: Aug-26 factory A/P GST is 3684 in Oil, 2766 in Mart, 2777 in Bev |
| G/L Account | `AcctCode` (line) | 100% filled on every line, item or service |
| Tax Code | `TaxCode` (line) | 100% filled — **not** `VatGroup`, which is only 18% |
| Location | `LocCode` (line) | Only 5 values. **(C-0025)** |
| Dimension 1–5 / Cost Centre | `OcrCode`…`OcrCode5` (line) | The API calls these `CostingCode`…`CostingCode5` |
| Budget | **`OcrCode3`** | The C-0027 field. API name `CostingCode3` |
| WTax Liable | `WtLiable` (line) | `Y` on 34% of Oil lines |
| Remarks | `Comments` (header) / `U_Remarks` (line) | Two different fields, both used |

### The dimension names are a three-way mismatch

| Slot | API | HANA | What it actually holds at JIVO |
|---|---|---|---|
| 1 | `CostingCode` | `OcrCode` | Profit centre / Variety |
| 2 | `CostingCode2` | `OcrCode2` | **The month** (`08-2026`) |
| 3 | `CostingCode3` | `OcrCode3` | **The budget** (`Factory`, `FACT_COM`, `Del Bkhp`…) |
| 4 | `CostingCode4` | `OcrCode4` | Department / channel (`Admin`, `E-COM`, `IT`…) |
| 5 | `CostingCode5` | `OcrCode5` | **The state** (`HR`, `DL`, `PB`…) |

Three names per slot, and the *meaning* is JIVO-specific and written nowhere in SAP.
→ [[Cost-Centres-and-Dimensions]]

## Layer 3 — what the paper says ↔ the field it sets

The printed vendor tax invoice. This is the layer that decides how fast an entry goes.

| Printed on the bill | Sets | Notes |
|---|---|---|
| Invoice No. / Bill No. / Tax Invoice No. | `NumAtCard` | Check it first — it is how you detect a duplicate |
| Invoice Date / Bill Date / Dated | `TaxDate` | **Not** `DocDate` |
| Gate Entry / G.No stamp date | **`DocDate`** | The posting date belongs to the receipt, not the bill |
| Buyer GSTIN / GSTIN of recipient | selects the **branch** (`BPLId`) | Match it to the branch's registration → [[Branches-and-BPLId]] |
| Supplier GSTIN | finds the **vendor** | The same vendor has **different `CardCode`s per book** |
| Place of Supply | decides **CGST+SGST vs IGST** | → [[GST-Tax-Codes]] |
| HSN Code | `HsnEntry` | Goods only |
| SAC Code | `SacEntry` | Services only — **mutually exclusive with HSN (C-0013)** |
| Taxable Value / Amount before tax | `LineTotal` | |
| CGST / SGST / IGST | `VatSum`, and the `TaxCode` that produces it | |
| Reverse Charge: Yes | an **R-prefixed** tax code | Posts a matched input+output pair |
| Round Off | nothing you type | SAP posts `RoundDif` to `5680014` by itself |
| Grand Total / Invoice Value | `DocTotal` | Must match to the paisa |
| TDS / TDS deducted | `WtLiable`, `WTAmount` | A CLI draft comes out with **0** — check it **(C-0018)** |
| PO No. / Order No. | the [[Purchase-Order]] to copy from | |
| LR No. / Bilty No. / GR No. | `U_BilltyNumber` | On the **invoice**, never on the receipt |
| Bilty Date | `U_BiltyDate` | |
| Transporter / Carrier name | `U_TransporterName` | 155 distinct in Oil |
| Vehicle No. | `U_VehicleNoM` | |
| Bill of Entry / BoE date | `U_BOEDate` | Imports → [[Landed-Costs]] |
| Qty / Litres / Weight on a service bill | `U_Recvd_Qty` | **(C-0025)** — though filled on only 2% in practice |
| "Original invoice no. & date" box on a credit note | `RevRefNo` / `RevRefDate` | **(C-0024)** |

**Handwritten marks are a separate vocabulary and they are instructions, not remarks.** That
glossary lives in `.claude/skills/jivo-ap-draft/reference/handwriting.md` and grows with
every paper — a handwritten *Common* means `OcrCode3` = `FACT_COM`, not a comment. **(C-0027)**

## The four-name chain, end to end

One field, all the way through:

```
paper:   "Original invoice no. & date"   (a box on the vendor's credit note)
screen:  Original Ref. No.
API:     OriginalRefNo                   (what sapb1 draft sends)
HANA:    RevRefNo                        (what you must query to check it)
```

Miss any link and you get a different kind of failure: wrong on the paper is a wrong entry,
wrong in the API writes nothing, wrong in HANA reports nothing. **Only the last one lies to
you quietly.**

## Traps

1. **Never infer a storage column from an API name.** Derive it from one known value.
2. **A plausible column name is not evidence.** `RetInvoice` looks exactly like the original
   reference and is a flag — one distinct value (`N`) across all 1,595 rows. **Check the
   distinct count before believing a column holds data.**
3. **"I searched for the field and found nothing" is a statement about your search**, not
   about the data.
4. **`VatGroup` and `TaxCode` both look like the tax code.** `TaxCode` is 100% filled,
   `VatGroup` 18%.
5. **`Comments` and `U_Remarks` are different fields**, header and line, both genuinely used.
6. **`U_AR_NO` (header) and `U_ARNO` (line) are different fields** with nearly the same
   name. Neither purpose is established yet.
7. **The ambiguous list in a rosetta run is not noise to ignore** — it means those fields
   agreed on every document you sampled. Find one where they differ.

## Open questions

1. `JournalEntries`/`OJDT` is not yet derived — its key is `TransId`, not `DocEntry`, so
   `rosetta.py` cannot pick its documents as written. Worth extending the tool.
2. Do the same for **line** tables (`PCH1` etc.), where `CostingCode`↔`OcrCode` is already
   known to diverge — the full line-level map is not yet derived.
3. `U_AR_NO` vs `U_ARNO` — what are they?
4. Are any of these mappings **book-specific**? All were derived in Oil. A UDF added to one
   book only would break the map.

## Queries used

```bash
# the whole mapping, derived not guessed
python3 sap-b1/entry-vault/bin/rosetta.py IncomingPayments      ORCT --co OIL --n 8
python3 sap-b1/entry-vault/bin/rosetta.py VendorPayments        OVPM --co OIL --n 8
python3 sap-b1/entry-vault/bin/rosetta.py Drafts                ODRF --co OIL --n 8
python3 sap-b1/entry-vault/bin/rosetta.py PurchaseInvoices      OPCH --co OIL --n 8
python3 sap-b1/entry-vault/bin/rosetta.py PurchaseCreditNotes   ORPC --co OIL --n 8 \
    --where '"NumAtCard" <> "RevRefNo" AND "RevRefNo" IS NOT NULL'
python3 sap-b1/entry-vault/bin/rosetta.py PurchaseDeliveryNotes OPDN --co OIL --n 8
python3 sap-b1/entry-vault/bin/rosetta.py Invoices              OINV --co OIL --n 8
python3 sap-b1/entry-vault/bin/rosetta.py PurchaseOrders        OPOR --co OIL --n 8
```

```sql
-- the check that proves a plausible column is a decoy
SELECT "RetInvoice" V, COUNT(*) N FROM "JIVO_OIL_HANADB"."ORPC" GROUP BY "RetInvoice";
-- N x 1595 -- one distinct value: it is a flag, not a reference
```

Raw output: `_data/rosetta-OPCH.md`, `rosetta-ORPC.md`, `rosetta-OPDN.md`,
`rosetta-OINV.md`, `rosetta-OPOR.md`.
