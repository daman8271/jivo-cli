---
type: document
sap_tables: [ORIN, RIN1, RIN12]
objtype: 14
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# A/R Credit Memo — the money we give back to a customer

> Goods came back, or we billed too much, or a marketplace deducted a claim. This is the
> document that takes it off the customer's account and off our sales. 11,417 across the
> three books — and it is the **minus** half of how JIVO measures turnover.

## At a glance

| | |
|---|---|
| SAP tables | `ORIN` header · `RIN1` lines · `RIN12` tax/GST/address |
| ObjType / TransType | **14** |
| Volume, all history | Oil 6,434 · Mart 4,545 · Bev 438 · **11,417** |
| Of which **live** (`CANCELED='N'`) | Oil 6,148 · Mart 4,393 · Bev 400 |
| Of which **actually keyed by a person** | Oil **4,882** · Mart 4,393 · Bev 400 — see the migration batch below |
| Last 120 days (live) | Oil **450** · Mart **416** · Bev **99** |
| Lines per memo (last 120d) | Oil 2.3 · **Mart 8.6** · Bev 1.2 (Mart max 67) |
| Who keys it | Oil: one login does **64%** · Mart: four logins do 92% · Bev: one login does 83%. Table below |
| Drafted first? | Sometimes — `draftKey` set on 38% Oil / 32% Mart / 72% Bev of the last 120 days |
| Needs approval? | Only on the draft route. 1,552 Oil requests ever, **5 rejected** |
| Comes from paper? | Rarely. 75% of documents are **copied** from a Return or an Invoice |
| Moves stock? | **Only a third of the time.** Oil 33% · Mart 26% · Bev 33% |

Everything below is measured live from HANA on 2026-08-24 unless it says *inferred*.

## Why it matters beyond the entry

**Turnover at JIVO is `Invoices` net of GST *minus* `CreditNotes`.** So this document is not
a side note — it is the deduction that makes the sales figure right. Measured for
FY 2026-27 to date (2026-04-01 → 2026-08-24):

| Book | Invoices (net of GST) | Credit memos (net of GST) | **Credited back** | Memos per 100 invoices |
|---|---:|---:|---:|---:|
| Oil | ₹188.83 Cr | ₹15.18 Cr | **8.0%** | 23 |
| Mart | ₹112.78 Cr | ₹20.82 Cr | **18.5%** | 10 |
| Beverages | ₹5.64 Cr | ₹0.16 Cr | 2.9% | 6 |

**Mart gives back nearly one rupee in five.** Any Mart sales number quoted gross of credit
notes is wrong by roughly a fifth. → [[AR-Invoice]]

## The Oil migration batch — 1,266 documents that are not entries

**1,266 Oil credit memos are all dated 2024-09-30, all carry `Handwrtten='Y'`, and all were
created by `UserSign` 1.** They are the go-live cutover load, not keyed work: no item lines,
tax code `Exampt` on every line, ₹88.75 lakh in total, and **not one of them has an original
invoice reference.**

They are 26% of Oil's `ORIN` table and they poison every ratio computed over it. **Filter
`"Handwrtten"='N'` on any Oil A/R credit-memo statistic.** Mart and Bev have none.
Related: [[Opening-Balance-and-Cutover]], and note that `OINV` also starts 2024-09-30 —
pre-cutover invoices are simply not in the books.

## Where it sits in the chain

Three routes in, and the route decides most of the work. Measured over all live
non-migration documents, taking the base type of the first line:

| Route | Oil | Mart | Bev | Stock moves? | Reference auto-filled? |
|---|---:|---:|---:|---|---|
| Copied from an **[[AR-Return]]** (`BaseType` 16) | 2,517 | 2,655 | 102 | **Never** — the return already did it | **No** |
| **Keyed from scratch** (`-1`) | 1,457 | 975 | 161 | Sometimes (800 / 504 / 17) | No |
| Copied from an **[[AR-Invoice]]** (`13`) | 891 | 762 | 137 | Yes (771 / 633 / 116) | **Yes — 99.6%** |
| Copied from an inventory count (`234000031`) | 17 | 1 | 0 | Yes | Yes |

`[[AR-Return]]` → **this** → [[Incoming-Payment]] or [[Internal-Reconciliation]].

### Copying from the invoice does most of the entry for you

On lines copied from an A/R invoice (`BaseType=13`), matched line-for-line against `INV1`:

| Mirrored correctly | Oil | Mart | Bev |
|---|---:|---:|---:|
| Tax code identical to the original | 1,993 / 1,993 (**100%**) | 2,040 / 2,040 (**100%**) | 299 / 299 (**100%**) |
| GL account identical | 1,974 / 1,993 (99%) | 2,016 / 2,040 (99%) | 277 / 299 (93%) |
| Dimension 1 identical | 1,993 / 1,993 (100%) | 2,040 / 2,040 (100%) | 297 / 299 (99%) |
| `RevRefNo` = the invoice's own `DocNum` | 517 / 519 (99.6%) | — | — |

**And it fills the original-invoice reference by itself.** That is the single strongest
argument for copying rather than keying: it satisfies the GST requirement, mirrors the tax
code, and lands on the same GL and dimension without a decision.

## The original-invoice reference — the real rule, and it is not what it looks like

`OriginalRefNo` / `OriginalRefDate` (Service Layer) are stored in HANA as **`RevRefNo` /
`RevRefDate`**. Nothing called `Original*` exists on `ORIN`. → [[Field-Name-Rosetta]]

### The headline figure, and why it is misleading

| Book | Live, non-migration | `RevRefNo` filled | Last 120 days |
|---|---:|---:|---:|
| Oil | 4,882 | 3,568 (**73.1%**) | 363 / 450 (80.7%) |
| Mart | 4,393 | 2,171 (**49.4%**) | 278 / 416 (66.8%) |
| Beverages | 400 | 321 (80.3%) | 75 / 99 (75.8%) |

*(The 59.5% / 50.7% / 81.1% quoted in [[AP-Credit-Memo]] is the same field measured over
every row including the 1,266 Oil migration rows and cancelled documents. Both are correct;
this table is the one to act on.)*

### The rule that actually governs it — measured, zero exceptions

Split the same population by **whether the document is a GST credit note** (`GSTTranTyp='GA'`)
and **whether the buyer carries a GSTIN on the document** (`RIN12.BpGSTType = 1`):

| Document kind | Oil | Mart | Bev | `RevRefNo` blank |
|---|---:|---:|---:|---:|
| GST credit note, **buyer registered (B2B)** | 3,116 | 1,711 | 228 | **0 · 0 · 0** |
| GST credit note, no buyer GSTIN on the document | 1,225 | 2,627 | 82 | 1,158 · 2,203 · 5 |
| Non-GST credit note (`--` series) | 541 | 55 | 90 | 156 · 19 · 74 |

**5,055 B2B GST credit notes across three books, and not one has a blank reference.** That
holds on all three routes in — including 1,405 Oil memos copied from a Return, where SAP
supplies nothing, and 853 keyed entirely from scratch by ten different logins.

*Inferred (high confidence, mechanism unproven):* **SAP's India localization makes Original
Ref. No. and Date mandatory on a GST credit note when the partner has a GSTIN**, and does not
ask for them otherwise. Nothing else survives 100% across three books, three copy routes and
ten operators. It cannot be proved from here without a write, which this vault does not do.
Contrast [[AP-Credit-Memo]], where 44 Oil vendor credit memos *do* have a blank reference —
so the check is not universal, and C-0024 is a real instruction there.

### What is left is still a gap — and it is live

**3,366 GST credit notes carry real output-GST reversal with no original-invoice reference**
(Oil 1,158 · Mart 2,203 · Bev 5). Every one of them has `VatSum ≠ 0`. They are small —
Oil ₹48.91 lakh / ₹2.53 lakh GST, Mart ₹1.50 Cr / ₹7.41 lakh GST — but they are current:

| Last 120 days, `GSTTranTyp='GA'` | Memos | Blank ref | Value | GST reversed |
|---|---:|---:|---:|---:|
| Oil | 401 | **67** | ₹9.22 lakh | ₹43,924 |
| Mart | 399 | **138** | ₹15.18 lakh | ₹72,293 |
| Beverages | 77 | 2 | ₹58,219 | ₹3,539 |

**Not a legacy backlog: 207 in the last four months.** A credit note to an unregistered
person is reported in GSTR-1 CDNUR, which asks for the original invoice number and date, so
these are unsupported in the return as filed. → **new correction candidate**, below.

And **373 of them belong to customers who *do* carry a GSTIN on their own invoices**
(Oil 172, Mart 201) — the credit note lost the registration the invoice had. That is a
document-level defect and a finite cleanup list, not a process. *Confidence medium* — a
GSTIN-less ship-to may be legitimate; it needs an operator's eye.

### A filled reference is not a correct reference

Of the references that *are* filled:

| Oil | Count | Resolves to a real Oil A/R invoice `DocNum` |
|---|---:|---:|
| Looks like one document number (5–11 chars) | 3,222 | 2,545 (79%) |
| Carries more than one number (12–20) | 259 | 0 — legitimately, a credit note against several invoices |
| A list or free text (21+) | 42 | 0 |
| **1–4 characters — junk** (`1`, `12`, `..`) | **45** | 0 |

**669 single-number Oil references point at nothing** — 8 of them resolve in Mart or
Beverages, the rest nowhere. Part is pre-cutover invoices absent from `OINV`; 303 fall in
FY 2025-26 and 81 in FY 2026-27, inside the live period, so those are typos.
Mart: 1,515 of 1,586 single-number references resolve (95.5%).

A worked example is in [[#Real examples]]: a memo copied from the right invoice, whose
auto-filled reference was then **overwritten with a number that is not an invoice at all**,
carrying a date seven months before the document.

Also measured: `RevRefDate` is **later than** `DocDate` on 13 Oil and 40 Mart documents —
an original invoice dated after the credit note that reverses it.

## Before you start — the pre-flight list

Everything decided before the screen opens.

- [ ] **Which book.** Oil, Mart or Beverages. The customer's `CardCode` differs between
      books, and so does the series integer.
- [ ] **Is there already an [[AR-Return]] for this?** If yes, **copy from it** — the stock
      is already back and the quantities are already right. Oil: 1,401 of 1,817 live returns
      have a memo; Mart only 429 of 1,795.
- [ ] **If there is no return, is there one invoice to copy from?** Copy it. It fills the
      reference, mirrors the tax code, and lands on the right GL and dimensions by itself.
- [ ] **GST credit note or not** — this is the series decision and it is irreversible on the
      paper. `<STATE>_G<MMYY>` = GST (`GA`), reaches GSTR-1. `<STATE>_B<MMYY>` = financial
      only (`--`), **zero GST**, measured on all 541 Oil `--` memos.
- [ ] **The original invoice number and date**, exactly as printed → `OriginalRefNo` /
      `OriginalRefDate`. Mandatory in practice on a GST credit note to a registered buyer;
      **get it anyway** on a B2C one, it is what the GST return wants.
- [ ] **Branch** (`BPLId`) → the series. Oil FACTORY 2 / PUNJAB 3 / DELHI 1;
      Mart DELHI 1 / HARYANA 2 / KARNATAKA 5 / PUNJAB 3; Bev FACTORY 2 / DELHI 1 / Punjab 3.
- [ ] **Goods coming back, or value only?** If goods: which **`-GR` warehouse**. Returned
      stock goes to a dedicated goods-return warehouse (`BH-GR`, `DL-GR`, `PB-SG`,
      `PB-RG`), not back into finished goods.
- [ ] **If value only:** which expense GL. Oil uses `5500004` PROMOTIONAL DISCOUNT (526
      lines, ₹1.80 Cr), `5640004` SAMPLING EXPENSES (201), `5680021` LOSS ON EXPIRED
      DAMAGED THEFT GOODS (123), `5680027` FESTIVAL EXPENSE (27). Mart uses `5640002`
      BUSINESS PROMOTION (112 lines, ₹1.86 Cr). Bev: `5640004` SAMPLING (113).
- [ ] **The tax code, matching the original invoice.** Not `VatGroup` — it is blank on 35%
      of Oil memo lines. → [[GST-Tax-Codes]]
- [ ] **The five dimensions**, matching the original line. → [[Cost-Centres-and-Dimensions]]
- [ ] The scan / claim statement → [[Attachments]]. `AtcEntry` is set on **100%** of the
      last 120 days in all three books.

## Fields that matter (`ORIN` header)

Fill rates from `_data/profile-ORIN.md` (all-history, all rows) unless stated. *Filled* =
non-null **and** non-blank **and** non-zero.

| Field | Reads as | Oil / Mart / Bev filled | Required? | Notes |
|---|---|---|---|---|
| `CardCode` / `CardName` | The customer | 100 / 100 / 100 | **required** | 235 distinct in Oil. Different code per book |
| `DocType` | `I` item lines · `S` service lines | 100% | **required** | Oil 4,331 `I` / 551 `S`. **Says nothing about stock** — see traps |
| `Series` | Which numbering series | 100% | **required** | Decides GST vs non-GST. Book-local integer. → [[Numbering-Series]] |
| `DocSubType` / `GSTTranTyp` | GST document subtype | 100% | set by the series | `GA` GST credit note · `--` financial. Always equal to each other |
| `BPLId` / `BPLName` | Branch | 100% | **required** | Group by the **id** — Bev stores both `FACTORY` and `Factory`, `PUNJAB` and `Punjab` |
| `RevRefNo` | **Original invoice no.** | 60 / 51 / 81 | **required on a GST CN** | = `OriginalRefNo`. See the rule above |
| `RevRefDate` | **Original invoice date** | 59 / 51 / 81 | same | = `OriginalRefDate` |
| `DocDate` | Posting date | 100% | **required** | On a credit memo `TaxDate` = `DocDate` on 98.5% and `DocDueDate` = `DocDate` on 99.9%. **Unlike [[AP-Invoice]]**, the three dates collapse to one (C-0017 does not apply here) |
| `TaxDate` | Document date | 100% | auto | |
| `NumAtCard` | Customer's / platform's own reference | 52 / 39 / 19 | optional | Recent 120d: Oil 10% · **Mart 56%** · Bev <1%. 3,233 distinct. Not a duplicate key here |
| `Comments` | Free-text remark | 71 / 76 / 77 | optional | **Partly written by SAP** — a copy stamps `Based On Returns <DocNum>.` in. Operators add the platform and the fortnight |
| `CtlAccount` | Customer control account | 100% | auto from the BP | The channel. Oil 12 values, Mart 6 |
| `VatSum` | GST reversed | 71 / 98 / 79 | computed | Exactly 0 on every `--` memo |
| `DocTotal` | Gross credit | 100% | computed | |
| `PaidToDate` | How much has been set off | 75 / 90 / 92 | auto | Settlement is a separate job — see below |
| `DocStatus` | Open / closed | 100% | auto | Oil 1,097 open. **C-0019 applies** |
| `CANCELED` | `N` live · `Y` cancelled · `C` its mirror | 100% | auto | Oil `N` 6,148 · `Y` 143 · `C` 143. **C-0021** |
| `WddStatus` | Approval | 100% | auto | `P` only where the memo came from a draft |
| `draftKey` | The draft it was posted from | 20 / 22 / 59 | auto | → [[Document-Drafts]] |
| `AtcEntry` | The scan | 79 / 100 / 97 | strongly expected | 100% in the last 120 days, all books |
| `RoundDif` | Rounding | 62 / 82 / 75 | **never type it** | 3,796 Oil memos carry one; **₹593.21 in total across all of them**. SAP posts it to `5680014` SHORT AND EXCESS by itself |
| `Handwrtten` | Migration marker | 100% | — | `Y` on the 1,266 Oil cutover rows and nothing else |
| `IssReason` | GST reason for issue | 100% | auto | `1` on 6,433 of 6,434 Oil. Effectively a constant |
| `EWBGenType` | E-way bill | 100% | auto | Oil `L` 5,547 · `N` 887 |
| `JrnlMemo` | Journal memo | 100% | **auto** | Always `A/R Credit Memos - <CardCode>`. Never typed |
| `Ref1` | — | 100% | auto | The document's own `DocNum`. Not a reference to anything |

### `RIN1` — the line fields a person decides

| Field | Reads as | Oil / Mart / Bev | Notes |
|---|---|---|---|
| `ItemCode` | The item | 86 / 99 / 81 | Blank = a service/value line |
| `Quantity` | Pieces — **single bottles** | 86 / 99 / 81 | **C-0001**: never multiply by the carton count in the name |
| `WhsCode` | Warehouse | 86 / 99 / 81 | 22 values. `-GR` = goods-return warehouse |
| `Price` / `LineTotal` | Rate and value | 83 / 61 / 92 | Mart's 61% is real: 39% of Mart lines are zero-value |
| `AcctCode` | GL account | **100%** | 52 values. Always filled, item or service |
| `TaxCode` | GST code | **100%** | 8 values. **Use this, not `VatGroup`** (65 / 92 / 40) |
| `OcrCode` | Dim 1 — variety / profit centre | 91 / 99 / 89 | 27 values: `OLIVE`, `MUSTARD`, `CANOLA`… |
| `OcrCode2`…`OcrCode5` | Dims 2–5 — month, budget, dept, state | 13 / 4 / 19 and below | Mostly blank here, unlike A/P |
| `CogsAcct` / `CogsOcrCod` | COGS account and its dimension | 86 / 99 / 81 | Auto from the item |
| `BaseType` / `BaseEntry` / `BaseLine` | What it was copied from | 100 / 71 / 56 | The route table above |
| `NoInvtryMv` | No inventory movement | 100% | `Y` on only 150 of 15,431 Oil lines |
| `U_Remarks` | Line remark | 11 / <1 / 20 | A different field from header `Comments` |
| `U_SchemeAgst` | Scheme | 85 / 99 / 80 | **A redundant copy of `OcrCode`** — identical on 13,163 of 13,172 Oil lines. Ignore it |
| `U_Purpose` | Purpose | 3 / 8 / <1 | Only `SALE`, `RETURNABLE`, `CONSUMABLE` |

### `RIN12` — the GST/address row, one per document

Auto-built, but two fields decide how the document is reported:

| Field | Oil / Mart / Bev filled | Reads as |
|---|---|---|
| `BpGSTType` | 4,362 / 1,897 / 275 rows = `1` | `1` = buyer registered. **This is the field the reference rule turns on** |
| `BpGSTN` | same | Buyer GSTIN. **C-0014** — this, never `OCRD.LicTradNum` |
| `IsIGSTAct` | 4,595 / 4,475 / 346 = `Y` | Interstate |
| `NfRef` | 3,621 / 3,490 / 265 | SAP's own "Based On …" trail |

### Fields SAP offers that JIVO never uses

Empty in **every** row of the last 120 days, in all three books: `DiscPrcnt`, `DiscSum`,
`DiscSumSy`, `BaseDiscPr` (header discounts — discounts are given as a **line**, or as a
separate memo, never as a header percentage), `ReopManCls`, `U_First_Floor`, `U_Ship_From`,
`U_AR_NO`, `U_DriverName`, `U_Order_Date`. `OwnerCode` is null on 6,397 of 6,434 Oil rows.
And roughly 90 header columns hold a single value forever — `Posted`, `UpdInvnt`,
`InvntDirec`, `Excised`, `DutyStatus`, the whole `EDoc*` family. They are not decisions.

### Columns that do not exist in every book

`profile-ORIN.md` lists 24. The ones that will break a write:

| Column | Present in | Missing from | Note |
|---|---|---|---|
| `U_SALES_PERSON` | **OIL only** | Mart, Bev | 21 values: `PUNJAB MT`, `ECOM`, `DELHI GT`… |
| `U_GRPO`, `U_PONo`, `U_MartCN`, `U_MartCustomer`, `U_OMS_REF`, `U_CreditCreated` | OIL only | Mart, Bev | |
| `U_BilltyNumber` / `U_VehicleNoM` | Oil, Mart | **Bev** | Bev spells them **`U_BiltyNumber`** and **`U_VechileNom`** |
| `U_BPCODE`, `U_MART_DOC_NO`, `U_POMade`, `U_PO_Ship_To`, `U_JWPL_BASE` | MART only | Oil, Bev | |
| `U_Production_Order`, `U_PRODUCTION_DATE`, `U_Total_Gross_Wt` | Oil, Bev | **Mart** | |

Sending a column to the book that lacks it is an error, not a no-op.

## Dimensions, branches and series

`Series` is the only field on this document that cannot be guessed, and it decides whether
the credit note reaches the GST return. Names read `<STATE>_<G|B><MM><YY>`:

- `G` → `DocSubType` = **`GA`** → a GST credit note. 128 such series per book for ObjType 14.
- `B` → `DocSubType` = **`--`** → a financial credit note. **Zero GST on all 541 Oil ones.**
- `CN<STATE><MMYY>` → `IsForCncl='Y'`, a **cancellation** series. SAP picks it; an operator never does.

**August 2026, ObjType 14** — measured from `NNM1`, and note the same name is a different
integer in every book:

| Series name | Branch | Oil | Mart | Bev |
|---|---|---:|---:|---:|
| `HR_G0826` (Haryana/Factory, GST) | 2 | **3152** | **2658** | **3237** |
| `HR_B0826` (Haryana/Factory, non-GST) | 2 | 3092 | 2574 | 3110 |
| `DL_G0826` (Delhi, GST) | 1 | 3140 | 2634 | 3225 |
| `DL_B0826` (Delhi, non-GST) | 1 | 3104 | 2586 | 3122 |
| `PB_G0826` (Punjab, GST) | 3 | 3189 | 2670 | 3249 |
| `KN_G0826` (Karnataka, GST) | 5 | — | 2682 | — |
| `HP_G0826` (BPL 4) | 4 | 3201 | — | 3286 |

Series exist for branches nobody uses: Oil has `HP_*` series and BPL 4 has never appeared on
an Oil credit memo. → [[Numbering-Series]], [[Branches-and-BPLId]]

Actual use in August 2026: Oil `HR_G0826` 45 · `HR_B0826` 7 · `PB_G0826` 3.
Mart `HR_G0826` 35 · `DL_G0826` 13. Bev `HR_G0826` 8.

Branch split, all live non-migration documents:

| Book | Branches used |
|---|---|
| Oil | FACTORY 2,954 · PUNJAB 1,548 · DELHI 380 |
| Mart | DELHI 3,890 · HARYANA 442 · KARNATAKA 41 · PUNJAB 20 |
| Bev | FACTORY 365 (two spellings) · DELHI 24 · Punjab 11 |

Line dimensions are much thinner here than on [[AP-Invoice]]: `OcrCode` (variety) is on 91%
of Oil lines, but dims 2–5 are on 13% / 11% / 10% / 8%. On the journal, `ProfitCode` reaches
38% of Oil lines, 47% Mart, 32% Bev.

## Tax

- **`GSTTranTyp='GA'`** → 4,341 Oil memos, 4,335 with GST, **₹2.29 Cr of output GST
  reversed**. These land in GSTR-1 as credit notes.
- **`GSTTranTyp='--'`** → 541 Oil memos, **₹2.03 Cr of value and exactly zero GST**. A
  post-sale commercial credit with no tax effect. Whether that is right for a given claim is
  a policy question for Accounts, not a query. → **Open questions**
- The reversal debits the same **output** tax account the invoice credited: `2132002`
  OUTPUT IGST @5% on 1,166 Oil lines, `2132007`/`2132008` OUTPUT SGST/CGST @2.5% on 784 each.
- **Copy from the invoice and the tax code mirrors it 100% of the time** (4,332 lines
  across three books, zero mismatches). Key it by hand and nothing checks you.
- **Hand-keyed Oil lines use `Exampt` on 904 of them** (excluding the migration batch) —
  a value credit with no GST. Mart does this on only 155 lines. A genuine difference in
  practice between the two books, not a data artefact.
- Tax codes in play on `RIN1` (Oil): `IGST@5` 6,729 · `CG+SG@5` 5,578 · `Exampt` 2,194 ·
  `IGST@12` 357 · `CG+SG@12` 332 · `CG+SG@18` 175 · `IGST@18` 63 · `CG+SG@0` 3.
  Mart adds `IG28+C12` and `IGST@40` / `CG+SG@40`.
- **`Exampt` is misspelled in the master.** A filter on `Exempt` returns nothing.
  → [[GST-Tax-Codes]]
- **No TDS.** `WtLiable='N'` on every line in all three books. → [[TDS-Withholding]]

## The journal it posts

TransType **14**. Last 365 days: Oil 2,211 journals / 12,116 lines / ₹50.09 Cr each side;
Mart 2,191 / 13,417 / ₹52.98 Cr; Bev 265 / 1,224 / ₹1.06 Cr.

It is the [[AR-Invoice]] fingerprint run backwards:

- **Cr** the customer control account (`1101005` E-COM, `1101004` MT, `1101001` GT…) —
  reducing what they owe
- **Dr** the sales account (`4110014` SALES OIL @5%, `4110005` SALES MUSTARD @5%…) —
  reversing the sale
- **Dr** the output GST account — reversing the tax
- **and only if goods came back:** **Dr** `1103001` FINISHED GOODS, **Cr** the COGS account
- **plus** a paise line on `5680014` SHORT AND EXCESS — SAP's rounding, on 1,627 of 2,211
  Oil journals

Line-count shape, Oil: 4 lines ×595 · 6 ×388 · 5 ×355 · 7 ×301 · 2 ×194 · 3 ×125. **A
2-line journal is a pure value credit** (debtor + sales, no tax, no stock) and 194 Oil
journals look like that. Mart's shape is similar; Bev has 44 two-line journals out of 265.

### How to tell a correct posting from a plausible one

1. **Is the stock leg there when it should be, and absent when it should not be?**
   `1103001` FINISHED GOODS appears on 631 of 2,211 Oil journals — 29%. If you copied from a
   Return and the stock leg is present, the stock has come back **twice**.
2. **Did the sales account match the original?** `4110014` SALES OIL @5% carries 759 lines
   across only 415 documents in Oil — a catch-all that absorbs mixed-variety memos.
3. **Is the tax leg on the same rate account as the invoice?**
4. **Does `5680014` carry paise and nothing more?** Oil's whole-year rounding through this
   document type is ₹78 Dr and ₹249 Cr. A rupee figure there is a mis-key.
5. **Bev only:** 4 journals debit `2131021`/`2131022` **INPUT** CGST/SGST @20% on a credit
   memo. Unexplained — see Open questions.

Full fingerprints: `_data/gl-14-OIL.md`, `gl-14-MART.md`, `gl-14-BEV.md`.

## Goods return or value adjustment — measure it, don't read `DocType`

`DocType` says `I` (item lines) on 89% of Oil and 98% of Mart memos. **That does not mean
stock came back.** Testing for a `1103…` inventory line in the journal:

| Book | Live non-migration memos | Stock actually moved | Value only |
|---|---:|---:|---:|
| Oil | 4,882 | **1,588 (33%)** | 3,294 |
| Mart | 4,393 | **1,138 (26%)** | 3,255 |
| Beverages | 400 | **133 (33%)** | 267 |

The reason is clean: **a memo copied from an [[AR-Return]] never moves stock** — 0 of 2,517
in Oil, 0 of 2,655 in Mart, 0 of 102 in Bev. The return did it. So the memo is the *money*
half of a two-document return, and the item lines are there only to price it.

This is the exact opposite of [[AP-Credit-Memo]], where 81% of documents are service-type
`S` value adjustments. On the sales side the item lines are nearly always present and the
stock movement nearly always is not.

The genuine value-only credits — no item line at all — are small in number and large in
money, and they name themselves in the GL: Oil 526 PROMOTIONAL DISCOUNT lines (₹1.80 Cr),
201 SAMPLING EXPENSES, 123 LOSS ON EXPIRED DAMAGED THEFT GOODS, 27 FESTIVAL EXPENSE.
Mart: 112 BUSINESS PROMOTION (₹1.86 Cr), 18 PROMOTIONAL DISCOUNT (₹81.00 lakh), 8 FREIGHT
AND CARTAGE. Bev: 113 SAMPLING EXPENSES, 16 LOSS ON EXPIRED.

## Credit memo or [[AR-Return]]? — the decision, with counts

Both exist. `ORDN` (return) holds 4,065 documents against `ORIN`'s 11,417.

| | A/R Return (`ORDN`, ObjType 16) | A/R Credit Memo (`ORIN`, 14) |
|---|---|---|
| Volume, all history | Oil 2,031 · Mart 1,847 · Bev 187 | Oil 6,434 · Mart 4,545 · Bev 438 |
| Moves stock | **Always** | Only when it is not based on a return |
| Reduces the customer's balance | **No** | **Yes** |
| GST effect | None | The reversal |

**They are not alternatives — they are two halves.** Goods physically come back → key the
**Return**; then copy it to a **Credit Memo** for the money and the GST. Value only, nothing
coming back → **Credit Memo** alone.

But that is not what the books show:

| Book | Live returns | Which got a credit memo |
|---|---:|---:|
| Oil | 1,817 | 1,401 (**77%**) |
| Mart | 1,795 | **429 (24%)** |
| Beverages | 161 | 105 (65%) |

And in Mart the 429 that did got **2,668 credit memos between them — 6.2 memos per return.**
One large marketplace return batch is split into many credit notes. That is why Mart memos
average 8.6 lines and 67 at the maximum.

The 1,366 Mart returns with no memo total only ₹48.22 lakh — an average of ₹3,592 each, and
1,342 of them are closed. *Inferred:* small e-commerce returns closed without crediting the
customer separately. **Unconfirmed** — see Open questions.

## Who keys it, and the one desk that changes the numbers

Live, non-migration, all history. Names as they appear in `OUSR` and in `acc/INVENTORY.md`.

| Book | Login | Memos | With reference |
|---|---|---:|---:|
| Oil | `USER11` Preshit | 3,105 | 3,018 (**97%**) |
| Oil | `USER16` Gurleen | 1,214 | **82 (7%)** |
| Oil | `USER15` Harpreet | 208 | 196 (94%) |
| Oil | `USER13` Sumit | 163 | 106 (65%) |
| Oil | `USER10` Mansi | 113 | 106 (94%) |
| Mart | `USER16` Babli | 1,852 | **280 (15%)** |
| Mart | `USER18` Shoaib | 1,152 | 917 (80%) |
| Mart | `USER14` Jaspal | 716 | 545 (76%) |
| Mart | `USER33` Audit | 333 | 203 (61%) |
| Bev | `USER11` Preshit | 333 | 297 (89%) |
| Bev | `USER13` Sumit | 34 | 3 (9%) |

`USER16` is **the e-commerce claims desk** in both books — and the split inside that one
login is the whole story:

| `USER16` | Documents | With reference |
|---|---:|---:|
| Oil, E-COM control account | 1,204 | **72 (6%)** |
| Oil, everything else | 10 | **10 (100%)** |
| Mart, E-COM | 1,806 | **234 (13%)** |
| Mart, everything else | 46 | **46 (100%)** |

The same person fills the field on every non-e-com memo and almost none of the e-com ones.
It is the **document kind**, not the desk: the e-com claim memos are the ones with no buyer
GSTIN, where SAP stops asking. Meanwhile `USER11` fills it on **517 of 517** Oil e-com
memos, so the field is obtainable on e-com work — one desk simply does not.

Last 120 days, unchanged and current: `USER16` 67 Oil + 98 Mart memos, **zero references**;
`USER11` 345/345 Oil; `USER18` 232/232 Mart; `USER13` 5 Oil (1) and 9 Bev (0); `USER10`
7 Oil (0); `USER38` Aqib 15 Mart (1).

*Note:* `USER16` is **`GURLEEN` in Oil and `BABLI` in Mart** — user IDs are per-book and the
same number is a different person. Never carry a `UserSign` across books.
→ [[SAP-Users-and-Logins]]

## Why Mart runs almost as many as Oil on a smaller sales base

Answered, and it is not a puzzle: **Mart's A/R credit-memo book is the e-commerce book.**

| Channel (`CtlAccount`) | Oil memos | Oil value | Mart memos | Mart value |
|---|---:|---:|---:|---:|
| `1101005` SUNDRY DEBTORS **E-COM** | 1,818 (37%) | **₹31.96 Cr** | **4,030 (92%)** | **₹30.11 Cr** |
| `1101004` SUNDRY DEBTORS MT | 1,895 (39%) | ₹5.78 Cr | 0 | — |
| `1101001` SUNDRY DEBTORS GT | 731 | ₹7.93 Cr | 150 | ₹6.90 Cr |
| `1101006` SUNDRY DEBTORS ROI | 226 | ₹1.62 Cr | 83 | ₹8.46 Cr |
| everything else | 212 | ₹1.23 Cr | 130 | ₹0.07 Cr |

92% of Mart's credit memos are e-commerce claims, against 37% of Oil's. That matches
**C-0008** — the ecom app's SAP surface *is* `JIVO_MART`. Marketplace claim settlement runs
through Mart, and marketplace claims are settled by credit note, fortnight by fortnight. The
`Comments` on them are literally `<PLATFORM> <SITE> RETURN 1-16 MAR` plus SAP's own
`Based On Returns <DocNum>.`

Beverages, by contrast, is a GT book: 225 of 400 memos on SUNDRY DEBTORS GT, 48 on SANGAT
(of which **1** carries a reference), 50 on STAFF.

## How the credit actually reaches the customer

The memo does not settle itself. Of Oil's 3,785 closed memos, **3,783 were closed by
[[Internal-Reconciliation]]** (`ITR1`) — the client's reconciliation screen, which carries no
`UserSign` at all — and 1,778 additionally carry a `ReceiptNum` linking them to an
[[Incoming-Payment]]. Mart: 3,923 of 3,925.

So "credit the customer" and "match it against their invoices" are two separate keying jobs,
exactly as with vendor payments in `acc/INVENTORY.md`.

Left over, `DocStatus='O'` (live documents, **including** the Oil migration batch — 586 of
Oil's 1,683 are those 2024-09-30 rows):

| Book | Open memos | Unapplied value | Oldest |
|---|---:|---:|---|
| Oil | 1,683 (1,097 excl. migration) | **₹1.24 Cr** | 2024-09-30 |
| Mart | 468 | **₹11.60 Cr** | 2025-01-13 |
| Beverages | 46 | ₹6.31 lakh | 2024-10-09 |

**C-0019 applies** — `DocStatus='O'` at JIVO is unreliable, so read the customer's real
position from `OCRD.CurrentAccountBalance`, not from this list. But ₹11.60 Cr of Mart credit
notes on 468 documents is a large enough figure to be worth someone looking.

## Approval

| Book | Requests ever | Approved | Rejected | Still pending |
|---|---:|---:|---:|---:|
| Oil | 1,552 | 1,463 | **5** | 84 |
| Mart | 1,041 | 986 | 9 | 46 |
| Beverages | 352 | 315 | 2 | 35 |

A 0.3% rejection rate: approval is a record, not a filter. But 165 requests across the three
books are still waiting, and `WddStatus='P'` appears only on memos that went through a
draft — so the direct-post route skips approval entirely. → [[Approval-Workflow]]

## Real examples

### 1. The normal shape — copied from an invoice, one line, three journal rows

Oil `DocEntry` 14192, `DocNum` 626082645, 2026-08-24, series 3152 (`HR_G0826`), branch 2
FACTORY, `DocType` `I`, `GSTTranTyp` `GA`.

One `RIN1` line: `BaseType` 13, `BaseEntry` 75379, `BaseRef` 626060377, item FG0000032
COLD PRESS 1 LTR, `Quantity` 320 (pieces — **C-0001**), `Price` ₹210, `LineTotal` ₹67,200,
`TaxCode` `IGST@5`, `AcctCode` 4110014, `WhsCode` GP-FG, `OcrCode` CANOLA,
`CogsAcct` 5000049, **`NoInvtryMv`=`Y`**.

Journal, three lines: Cr `1101004` SUNDRY DEBTORS MT ₹70,560 · Dr `2132002` OUTPUT IGST @5%
₹3,360 · Dr `4110014` SALES OIL @5% ₹67,200. **No stock leg** — `NoInvtryMv='Y'`, even
though the header says `DocType='I'`.

**And the awkward part.** `RevRefNo` = `626085018`, `RevRefDate` = 2026-01-08. The base
invoice is `626060377` dated 2026-06-17. **626085018 is not an invoice number in any of the
three books**, and the date is five months before the document. `Comments` holds
`626060377.` — the right number, in the wrong field. The auto-filled reference was
overwritten with something that resolves to nothing. This document counts as "filled" in
every fill-rate table in this note.

### 2. Copied from a Return, reference typed by hand — the good case

Oil `DocEntry` 14183, `DocNum` 626082644. Line `BaseType` 16 (a Return, `DocNum`
1626086533). `Comments` = `1626086533.` (SAP's stamp). **`RevRefNo` = `626080325`,
`RevRefDate` = 2026-08-12** — and 626080325 *is* a real Oil invoice for the same customer,
dated 2026-08-12. SAP supplied nothing; the operator looked the invoice up and typed it.
That is the standard to hold.

### 3. The e-commerce claim batch — where the reference goes missing

Recurring `Comments` on Oil memos with a blank reference, keyed by `USER16`:
`JIOMART LUHARI RETURN 1 TO 16 MAR 1625031033.` · `SMYTTEN RETURN 04.01.2025 1625011112.` ·
`OUTSIDE BASED ON RETURNS 1625066564.` · `B 1625086543.`

A fortnight of marketplace returns, one credit note, several dozen lines, the **Return**
number in `Comments` and no invoice number anywhere. The document has no buyer GSTIN, so SAP
never asks. There is no *single* original invoice — which is the honest reason the field is
hard, and not a reason to leave it empty on a GST credit note.

## Traps

1. **`DocType='I'` does not mean stock came back.** 89% of Oil memos say `I`; only 33% move
   inventory. Test the journal for a `1103…` line, or `RIN1.NoInvtryMv`.
2. **A memo copied from an [[AR-Return]] must not move stock.** 0 of 5,274 across the three
   books do. If yours does, the return already booked it and you have doubled the stock.
3. **`OriginalRefNo` is `RevRefNo` in HANA, `OriginalRefDate` is `RevRefDate`.** Nothing
   named `Original*` exists on `ORIN`. → [[Field-Name-Rosetta]]
4. **Filled is not correct.** 45 Oil references are 1–4 characters of junk; 669
   single-number references resolve to no invoice anywhere; 13 Oil and 40 Mart `RevRefDate`
   values are *after* the credit note's own date. Read the number back and look it up.
5. **The 1,266 Oil `Handwrtten='Y'` rows are the go-live load, not entries.** They drag
   Oil's reference fill rate from 73% to 60% and its exempt-line count by 1,266.
   Always filter them out.
6. **`CANCELED` is three-valued** — Oil `N` 6,148 / `Y` 143 / `C` 143. A `<> 'Y'` test keeps
   the mirrors and double-counts. **C-0021**
7. **The series decides the tax, and it is on the paper.** `_B` series = `DocSubType` `--` =
   **zero GST** on all 541 Oil documents. Pick `_G` for anything that must reverse output tax.
8. **The series integer is different in every book.** `HR_G0826` is 3152 in Oil, 2658 in
   Mart, 3237 in Beverages. **C-0018**'s lesson, same shape, different object type.
9. **`Quantity` is in single bottles.** **C-0001** — the `20 PCS` in the item name is carton
   configuration.
10. **Returned stock belongs in a `-GR` warehouse**, not in finished goods. Mart's `DL-GR`
    carries 9,883 of ~14,400 recent lines.
11. **`Exampt` is misspelled in the master** and is on 2,194 Oil lines. A filter on `Exempt`
    finds nothing. **→ [[GST-Tax-Codes]]**
12. **`VatGroup` is not the tax code.** 65% filled in Oil against `TaxCode`'s 100%.
13. **Do not touch rounding.** SAP posts `RoundDif` to `5680014` SHORT AND EXCESS on 3,796
    Oil memos, totalling ₹593.21 for the entire history.
14. **`UserSign` 16 is Gurleen in Oil and Babli in Mart.** User IDs are per-book.
15. **Bev spells two UDFs differently** — `U_BiltyNumber` / `U_VechileNom` where Oil and
    Mart have `U_BilltyNumber` / `U_VehicleNoM`. And Bev stores `BPLName` as both `FACTORY`
    and `Factory`. Group by `BPLId`.
16. **`U_SALES_PERSON` exists in Oil only.** Sending it to Mart or Beverages is an error,
    not a no-op.
17. **`JrnlMemo` and `Ref1` are auto-filled and carry no information** — `A/R Credit Memos -
    <CardCode>` and the document's own number. Do not read them as references.
18. **`DocStatus='O'` does not mean unapplied.** **C-0019.** Age from
    `OCRD.CurrentAccountBalance`.
19. **Intercompany credit memos are real.** **C-0005** lists the 23 group `CardCode`s; Oil's
    `CUSTA000606` alone carries 2,674 journal lines in this document type. Exclude and name
    them in any sales figure.

## How to create one from the CLI

**Draft only.** `sapb1 draft credit-note` maps to the `CreditNotes` entity set (ObjType 14),
so this document type *is* reachable — but **no skill exists for it yet.** The
[[AP-Credit-Memo]] path has `jivo-ap-credit-memo`; the sales side has nothing, and the
payload below has **not been sent even as a dry run** from this session (this vault is
read-only). Treat it as a starting point derived from the data, not as a proven payload.

Pre-checks worth running before anything is composed:

```bash
# 1. Is there already a Return to copy from?  (copy it — stock is already back)
./hana-sql/hana-sql -env connections/hana-office-bridge.env \
 "SELECT \"DocEntry\",\"DocNum\",\"DocDate\",\"DocTotal\",\"DocStatus\"
  FROM \"JIVO_MART_HANADB\".\"ORDN\" WHERE \"CardCode\"='CUSTA000xxx' AND \"CANCELED\"='N'
  AND \"DocStatus\"='O' ORDER BY \"DocDate\" DESC"

# 2. Find the original invoice, and take its DocNum and DocDate verbatim
./hana-sql/hana-sql -env connections/hana-office-bridge.env \
 "SELECT \"DocEntry\",\"DocNum\",\"DocDate\",\"DocTotal\" FROM \"JIVO_MART_HANADB\".\"OINV\"
  WHERE \"CardCode\"='CUSTA000xxx' AND \"CANCELED\"='N' ORDER BY \"DocDate\" DESC"

# 3. The series for this book, branch, month and GST sub-type
./hana-sql/hana-sql -env connections/hana-office-bridge.env \
 "SELECT \"Series\",\"SeriesName\",\"DocSubType\",\"BPLId\",\"NextNumber\",\"LastNum\"
  FROM \"JIVO_MART_HANADB\".\"NNM1\"
  WHERE \"ObjectCode\"='14' AND \"SeriesName\" LIKE '%0826' AND \"IsForCncl\"='N'"

# 4. Has it already been keyed?  (there is no NumAtCard discipline here — check by value)
./hana-sql/hana-sql -env connections/hana-office-bridge.env \
 "SELECT \"DocEntry\",\"DocNum\",\"DocDate\",\"DocTotal\",\"RevRefNo\"
  FROM \"JIVO_MART_HANADB\".\"ORIN\" WHERE \"CardCode\"='CUSTA000xxx'
  AND \"DocDate\">=ADD_DAYS(CURRENT_DATE,-60) AND \"CANCELED\"='N'"
```

The payload must carry, beyond the obvious:

```
Series                 -> from NNM1 for (ObjType 14, branch, month, GST sub-type)
BPL_IDAssignedToInvoice-> the branch id (never the name)
OriginalRefNo          -> the original invoice DocNum, exactly as printed
OriginalRefDate        -> that invoice's DocDate
DocumentSubType        -> the GST sub-type the series carries (GA for a GST credit note)
per line: ItemCode | AccountCode, Quantity, Price, TaxCode (matching the original),
          WarehouseCode (a -GR warehouse for returned goods), CostingCode
```

**Prefer copying.** A credit memo built from the invoice or the return arrives with the
reference, the tax code, the GL, the dimensions and the quantities already right — every one
of which is a measured failure mode when keyed by hand.

## Verify after saving

- [ ] **`RevRefNo` and `RevRefDate` are both set, and the number is a real invoice.** Look
      it up in `OINV` for that customer in that book. SAP will not warn you, and a filled
      wrong number is invisible to every audit.
- [ ] **The stock leg is right.** Copied from a Return → there must be **no** `1103…` line.
      Not from a return but goods came back → there must be one.
- [ ] **The tax code matches the original invoice** and the GST landed on the same output
      account. A `_B` series posted zero GST — was that intended?
- [ ] **The right series** — `_G` for a GST credit note, `_B` for a financial one, and the
      integer belongs to *this* book.
- [ ] **The warehouse is the branch's `-GR`**, not finished goods.
- [ ] `Quantity` is in pieces, and matches the return.
- [ ] The five dimensions match the original line.
- [ ] `AtcEntry` points at the claim statement or credit note scan. → [[Attachments]]
- [ ] The journal is the invoice run backwards, account for account — not merely balanced.
- [ ] Rounding sits on `5680014` and is paise.

## New correction candidate

> **A/R credit memos: `OriginalRefNo` / `OriginalRefDate` must be set even when SAP does not
> ask for them.**
>
> *Measured:* on a GST credit note (`GSTTranTyp='GA'`) whose buyer carries a GSTIN, the pair
> is filled on **5,055 of 5,055 documents** — all three books, all three copy routes,
> ten logins, **zero** blanks. Where the document has no buyer GSTIN, SAP does not appear to
> ask, and **3,366 GST credit notes** have been posted carrying real output-GST reversal with
> no original-invoice reference: Oil 1,158 · Mart 2,203 · Bev 5, **207 of them in the last
> 120 days**. GSTR-1 CDNUR asks for the original invoice number and date for exactly these.
>
> *Measured:* one login (`USER16`, the e-com claims desk) accounts for 2,704 of the 3,366 —
> 1,132 in Oil, 1,572 in Mart, every one of its memos a `GA` document. `USER11` fills the
> field on **517 of 517** Oil e-com memos, so the number is obtainable on e-com work.
>
> *Inferred:* that the 100% is SAP's India localization enforcing a mandatory field rather
> than habit. Nothing else survives 100% across hand-keyed documents by ten operators, but
> proving it needs a deliberate write and this vault does not write.

This extends **C-0024** from the purchase side to the sales side. **It is a candidate, not a
correction:** it needs an operator to confirm that a marketplace fortnightly claim genuinely
has an original invoice that can be named, and to say which one when a batch spans many.
Filing it needs the `jivo-correct` skill, and a correction reaches nobody until it is pushed
to `main`.

Secondary candidate, weaker: **`DocType` on an A/R credit memo does not indicate a stock
movement** — 89% say `I`, 33% move stock. Anyone reading `ORIN` for returns volume from
`DocType` is wrong by a factor of nearly three.

## Open questions

1. **Is SAP really enforcing the reference on B2B GST credit notes, or is it discipline?**
   The measurement is airtight (5,055 / 0); the *mechanism* is inferred. Settling it needs
   one deliberate draft with `OriginalRefNo` omitted on a registered customer — **a write,
   which this vault does not do.** Ask an operator to try it in the client instead.
2. **Should a fortnightly marketplace claim name one original invoice, or a list?** 259 Oil
   and 514 Mart references already carry more than one number. If a list is acceptable, the
   gap is closable today; if GST wants one credit note per invoice, the process changes.
   **Needs an operator's answer, not a query.**
3. **373 credit notes to customers who carry a GSTIN on their own invoices have no GSTIN on
   the credit note** (Oil 172, Mart 201). Data defect, or a legitimate GSTIN-less ship-to?
   A finite cleanup list either way.
4. **Why do 1,366 Mart A/R returns (76%) never get a credit memo?** All closed, ₹48.22 lakh
   total, ₹3,592 average. Closed manually? Credited by journal entry? *Unconfirmed.*
5. **₹11.60 Cr of Mart credit memos sit `DocStatus='O'` on 468 documents.** C-0019 says the
   status is unreliable — but is the credit actually reaching those customers?
6. **541 Oil credit notes worth ₹2.03 Cr reversed no GST** (`--` series). Post-sale discount
   with no tax adjustment is a defensible position and also a contestable one. A policy
   question for Accounts.
7. **Beverages debits INPUT CGST/SGST @20% (`2131021`/`2131022`) on 4 credit-memo journals**,
   ₹54,017 each side. Input tax on a sales credit note is backwards. Four documents — worth
   opening.
8. **Why does Oil key `Exampt` on 904 hand-keyed lines and Mart on only 155?** Both books
   issue promotional-discount credits. One of them is treating the same commercial event
   differently.
9. `U_CreditCreated` and `U_MartCN` exist in Oil only and are almost entirely empty — an
   abandoned Oil↔Mart credit-note link? → [[Add-on-Tables-and-UDFs]]
10. `IssReason` is `1` on 6,433 of 6,434 Oil rows and `4` on one. What are the codes, and
    does GSTR-1 read it?

## Queries used

```sql
-- 1. The reference pair, live and excluding the migration batch
SELECT COUNT(*) TOTAL,
       SUM(CASE WHEN "RevRefNo" IS NOT NULL AND TRIM("RevRefNo")<>'' THEN 1 ELSE 0 END) REFNO,
       SUM(CASE WHEN "DocDate">=ADD_DAYS(CURRENT_DATE,-120) THEN 1 ELSE 0 END) T120
FROM "JIVO_OIL_HANADB"."ORIN" WHERE "CANCELED"='N' AND "Handwrtten"='N';
-- Oil 4882 / 3568 / 450 · Mart 4393 / 2171 / 416 · Bev 400 / 321 / 99

-- 2. The migration batch — 1,266 rows, one date, one user, no reference
SELECT "Handwrtten", COUNT(*), MIN("DocDate"), MAX("DocDate"),
       SUM(CASE WHEN "RevRefNo" IS NOT NULL AND TRIM("RevRefNo")<>'' THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ORIN" WHERE "CANCELED"='N' GROUP BY "Handwrtten";
-- Y: 1266, 2024-09-30 → 2024-09-30, 0 references

-- 3. THE RULE — GST credit note x buyer registered x reference blank
SELECT CASE WHEN t."BpGSTType"=1 THEN 'B2B' ELSE 'no GSTIN' END BUYER,
       CASE WHEN o."RevRefNo" IS NULL OR TRIM(o."RevRefNo")='' THEN 'BLANK' ELSE 'filled' END REF,
       COUNT(*), SUM(o."VatSum")
FROM "JIVO_OIL_HANADB"."ORIN" o JOIN "JIVO_OIL_HANADB"."RIN12" t ON t."DocEntry"=o."DocEntry"
WHERE o."CANCELED"='N' AND o."Handwrtten"='N' AND o."GSTTranTyp"='GA'
GROUP BY CASE WHEN t."BpGSTType"=1 THEN 'B2B' ELSE 'no GSTIN' END,
         CASE WHEN o."RevRefNo" IS NULL OR TRIM(o."RevRefNo")='' THEN 'BLANK' ELSE 'filled' END;
-- B2B: 3116 filled, 0 blank.  no GSTIN: 67 filled, 1158 blank (GST Rs 2,52,545)
-- Mart 1711/0 and 424/2203.  Bev 228/0 and 77/5.

-- 4. ...and it holds on every copy route, including the ones SAP does not help with
SELECT q."BT", COUNT(*), SUM(q."BLANK") FROM (
  SELECT o."DocEntry",
         (SELECT MIN(l."BaseType") FROM "JIVO_OIL_HANADB"."RIN1" l WHERE l."DocEntry"=o."DocEntry") "BT",
         CASE WHEN o."RevRefNo" IS NULL OR TRIM(o."RevRefNo")='' THEN 1 ELSE 0 END "BLANK"
  FROM "JIVO_OIL_HANADB"."ORIN" o JOIN "JIVO_OIL_HANADB"."RIN12" t ON t."DocEntry"=o."DocEntry"
  WHERE o."CANCELED"='N' AND o."Handwrtten"='N' AND o."GSTTranTyp"='GA' AND t."BpGSTType"=1) q
GROUP BY q."BT";
-- base 16 (Return): 1405 documents, 0 blank.  base -1 (keyed): 853, 0 blank.  base 13: 842, 0.

-- 5. Copying from the invoice auto-fills the reference
SELECT COUNT(*), SUM(CASE WHEN TRIM(o."RevRefNo")=TO_VARCHAR(l."BaseDocNum") THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ORIN" o
JOIN "JIVO_OIL_HANADB"."RIN1" l ON l."DocEntry"=o."DocEntry" AND l."LineNum"=0
WHERE o."CANCELED"='N' AND l."BaseType"=13 AND o."RevRefNo" IS NOT NULL;
-- 519 / 517 (99.6%); RevRefDate matches the invoice DocDate on 518

-- 6. Does the filled reference resolve to a real invoice?
SELECT COUNT(*) FILLED,
       SUM(CASE WHEN EXISTS (SELECT 1 FROM "JIVO_OIL_HANADB"."OINV" i
             WHERE TO_VARCHAR(i."DocNum")=TRIM(o."RevRefNo")) THEN 1 ELSE 0 END) RESOLVES
FROM "JIVO_OIL_HANADB"."ORIN" o
WHERE o."CANCELED"='N' AND o."RevRefNo" IS NOT NULL AND TRIM(o."RevRefNo")<>'';
-- Oil 3568 / 2545 · Mart 2171 / 1515 · Bev 321 / 277
-- bucketed by LENGTH: 5-11 chars 3222/2545; 12-20 chars 259/0; 21+ 42/0; 1-4 chars 45/0

-- 7. Stock actually moved, versus what DocType claims
SELECT COUNT(*), SUM(CASE WHEN q."STK">0 THEN 1 ELSE 0 END) FROM (
  SELECT o."DocEntry", (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."JDT1" j
     WHERE j."TransId"=o."TransId" AND j."Account" LIKE '1103%') "STK"
  FROM "JIVO_OIL_HANADB"."ORIN" o WHERE o."CANCELED"='N' AND o."Handwrtten"='N') q;
-- Oil 4882 / 1588 (33%) · Mart 4393 / 1138 (26%) · Bev 400 / 133 (33%)
-- by base type: BaseType 16 -> 0 of 2517 Oil, 0 of 2655 Mart, 0 of 102 Bev

-- 8. Copying mirrors the tax code, GL and dimension
SELECT COUNT(*), SUM(CASE WHEN l."TaxCode"=b."TaxCode" THEN 1 ELSE 0 END),
       SUM(CASE WHEN l."AcctCode"=b."AcctCode" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."RIN1" l
JOIN "JIVO_OIL_HANADB"."INV1" b ON b."DocEntry"=l."BaseEntry" AND b."LineNum"=l."BaseLine"
WHERE l."BaseType"=13;
-- Oil 1993 / 1993 / 1974 · Mart 2040 / 2040 / 2016 · Bev 299 / 299 / 277

-- 9. The series rule: name letter -> DocSubType -> GST or not
SELECT SUBSTRING("SeriesName",1,4) PREFIX, "DocSubType", "BPLId", "IsForCncl", COUNT(*)
FROM "JIVO_OIL_HANADB"."NNM1" WHERE "ObjectCode"='14'
GROUP BY SUBSTRING("SeriesName",1,4), "DocSubType", "BPLId", "IsForCncl";
-- *_G -> GA (128 each) · *_B -> '--' (128) · CN* -> GA with IsForCncl='Y' (cancellation)
SELECT "GSTTranTyp", COUNT(*), SUM(CASE WHEN "VatSum"<>0 THEN 1 ELSE 0 END), SUM("DocTotal")
FROM "JIVO_OIL_HANADB"."ORIN" WHERE "CANCELED"='N' AND "Handwrtten"='N' GROUP BY "GSTTranTyp";
-- GA 4341 (4335 with GST, Rs 46.50 cr) · '--' 541 (0 with GST, Rs 2.03 cr)

-- 10. Who keys it, and the E-COM split inside one login
SELECT u."USER_CODE", CASE WHEN o."CtlAccount"='1101005' THEN 'E-COM' ELSE 'other' END,
       COUNT(*), SUM(CASE WHEN o."RevRefNo" IS NOT NULL AND TRIM(o."RevRefNo")<>'' THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ORIN" o LEFT JOIN "JIVO_OIL_HANADB"."OUSR" u ON u."USERID"=o."UserSign"
WHERE o."CANCELED"='N' AND o."Handwrtten"='N'
GROUP BY u."USER_CODE", CASE WHEN o."CtlAccount"='1101005' THEN 'E-COM' ELSE 'other' END;
-- USER16 E-COM 1204/72, other 10/10.  USER11 E-COM 517/517, other 2588/2501.

-- 11. Credit-note intensity against the sales base, FY26-27 to date
SELECT (SELECT COUNT(*) FROM "JIVO_MART_HANADB"."OINV"
          WHERE "CANCELED"='N' AND "DocDate">='2026-04-01') INV_N,
       (SELECT SUM("DocTotal"-"VatSum") FROM "JIVO_MART_HANADB"."OINV"
          WHERE "CANCELED"='N' AND "DocDate">='2026-04-01') INV_NET,
       (SELECT COUNT(*) FROM "JIVO_MART_HANADB"."ORIN"
          WHERE "CANCELED"='N' AND "DocDate">='2026-04-01') CM_N,
       (SELECT SUM("DocTotal"-"VatSum") FROM "JIVO_MART_HANADB"."ORIN"
          WHERE "CANCELED"='N' AND "DocDate">='2026-04-01') CM_NET FROM DUMMY;
-- Oil 2768 / 188.83 cr / 637 / 15.18 cr · Mart 4644 / 112.78 cr / 487 / 20.82 cr
-- Bev 1874 / 5.64 cr / 121 / 0.16 cr

-- 12. Returns that never got a credit memo, and Mart's fan-out
SELECT COUNT(*) RET_N, SUM(CASE WHEN EXISTS (SELECT 1 FROM "JIVO_MART_HANADB"."RIN1" l
        WHERE l."BaseType"=16 AND l."BaseEntry"=r."DocEntry") THEN 1 ELSE 0 END) HAS_MEMO
FROM "JIVO_MART_HANADB"."ORDN" r WHERE r."CANCELED"='N';
-- Oil 1817/1401 · Mart 1795/429 · Bev 161/105
SELECT COUNT(DISTINCT "BaseEntry"), COUNT(DISTINCT "DocEntry")
FROM "JIVO_MART_HANADB"."RIN1" WHERE "BaseType"=16;   -- 429 returns -> 2668 memos

-- 13. How the credit is settled, and what is left open
SELECT COUNT(*), SUM(CASE WHEN EXISTS (SELECT 1 FROM "JIVO_OIL_HANADB"."ITR1" r
        WHERE r."SrcObjTyp"='14' AND r."SrcObjAbs"=o."DocEntry") THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ORIN" o
WHERE o."CANCELED"='N' AND o."Handwrtten"='N' AND o."DocStatus"='C';
-- 3785 closed, 3783 via internal reconciliation
SELECT COUNT(*), SUM("DocTotal"-"PaidToDate"), MIN("DocDate")
FROM "JIVO_MART_HANADB"."ORIN" WHERE "CANCELED"='N' AND "DocStatus"='O';
-- Mart 468 / Rs 11.60 cr · Oil 1683 / Rs 1.24 cr · Bev 46 / Rs 6.31 lakh

-- 14. Rounding is SAP's, and it is paise
SELECT COUNT(*), SUM(CASE WHEN "RoundDif"<>0 THEN 1 ELSE 0 END), SUM(ABS("RoundDif"))
FROM "JIVO_OIL_HANADB"."ORIN" WHERE "CANCELED"='N' AND "Handwrtten"='N';
-- 4882 / 3796 / Rs 593.21 for the whole history

-- 15. U_SchemeAgst is a duplicate of OcrCode
SELECT COUNT(*), SUM(CASE WHEN "U_SchemeAgst"="OcrCode" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."RIN1" WHERE "U_SchemeAgst" IS NOT NULL AND "OcrCode" IS NOT NULL;
-- 13172 / 13163
```

Corpus files: `_data/profile-ORIN.md`, `_data/profile-RIN1.md`,
`_data/flow-ORIN-{OIL,MART,BEV}.md`, `_data/gl-14-{OIL,MART,BEV}.md`,
`_data/sample-ORIN-OIL.md`.

Related: [[AR-Invoice]] · [[AR-Return]] · [[AP-Credit-Memo]] · [[Field-Name-Rosetta]] ·
[[GST-Tax-Codes]] · [[Numbering-Series]] · [[Document-Status-and-Cancellation]] ·
[[Cost-Centres-and-Dimensions]] · [[Attachments]] · [[Incoming-Payment]] ·
[[Internal-Reconciliation]] · [[Document-Drafts]] · [[Approval-Workflow]] ·
[[Entry-Types-Census]] · [[Opening-Balance-and-Cutover]]
