---
type: document
sap_tables: [OINV, INV1, INV12, INV3]
objtype: 13
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# A/R Invoice — the tax invoice we give the customer

> The piece of paper that makes a sale a sale. **62,426** of them across the three
> books — more than any other document JIVO keys — and the one whose definition
> decides every turnover number the business quotes. Nothing else in the vault is
> read as often by people who are about to say a number out loud.

## At a glance

| | |
|---|---|
| SAP tables | `OINV` header · `INV1` lines · `INV12` tax/address/GSTIN (one row per invoice, always) · `INV3` freight — **3 rows in Oil ever, 0 in Mart and Bev** |
| ObjType / TransType | **13** |
| Volume (all history) | Oil 31,084 · Mart 25,752 · Bev 5,590 · **62,426** |
| Last 120 days | Oil 2,513 · Mart 4,195 · Bev 1,693 |
| History starts | Oil 2024-09-30 · Mart 2024-10-03 · Bev 2024-10-04 |
| Of which real sales | Oil **20,006** · Mart **25,747** · Bev 5,590 — the rest is migration, see below |
| Who keys it | The **billing desk**, not Accounts. 6,384 in 90 days group-wide (~83/working day). Oil: HARPREET · SUMIT · MANSI. Mart: BABLI · PARAM BILLING · JASPAL. Bev: KARANPREET |
| Drafted first? | **Depends entirely on the book.** Last 120 d: Oil **87%** · Mart **17%** · Bev **88%** |
| Needs approval? | Approval requests ever raised for ObjType 13 — Oil 10,607 · Mart 3,940 · Bev 5,934 |
| Comes from paper? | Almost never. 90–97% is copied from a [[Sales-Order]] or a [[Delivery]] |

---

## 1. The house turnover definition — say it once, exactly

**Turnover = A/R invoices net of GST, minus A/R credit notes, by `DocDate`, excluding
cancelled.** GST-inclusive is `DocTotal`; net of GST is `DocTotal − VatSum`.

```sql
-- HOUSE TURNOVER, one book, one date range. Swap the schema for MART / BEVERAGES.
SELECT SUM("DocTotal" - "VatSum") AS INVOICES_NET
FROM   "JIVO_OIL_HANADB"."OINV"
WHERE  "CANCELED" = 'N'
  AND  "DocDate" >= '2026-04-01' AND "DocDate" < '2026-08-25';

SELECT SUM("DocTotal" - "VatSum") AS CREDIT_NOTES_NET
FROM   "JIVO_OIL_HANADB"."ORIN"
WHERE  "CANCELED" = 'N'
  AND  "DocDate" >= '2026-04-01' AND "DocDate" < '2026-08-25';
-- turnover = INVOICES_NET − CREDIT_NOTES_NET
```

Measured on **2026-08-24** for FY26-27 to date (2026-04-01 → 2026-08-24):

| Book | Invoices | Net of GST | Credit notes | Net of GST | **Turnover** |
|---|---:|---:|---:|---:|---:|
| Oil | 2,768 | ₹188.83 Cr | 637 | ₹15.18 Cr | **₹173.65 Cr** |
| Mart | 4,644 | ₹112.78 Cr | 487 | ₹20.82 Cr | **₹91.96 Cr** |
| Beverages | 1,874 | ₹5.64 Cr | 121 | ₹0.16 Cr | **₹5.48 Cr** |

Mart's credit notes are **18.5% of its invoiced value** — marketplace returns. Oil's are
8%, Beverages' 3%. Never quote a Mart sales figure gross of returns.

### The same figure, with intercompany taken out (C-0005)

| Book | External turnover | Intercompany | Note |
|---|---:|---:|---|
| Oil | **₹86.96 Cr** | ₹86.69 Cr | 526 invoices to `CUSTA000606` (JIVO Mart) = **52% of Oil's invoiced net** |
| Mart | **₹90.02 Cr** | ₹1.94 Cr | 88 invoices, no credit notes |
| Beverages | **₹5.47 Cr** | ₹0.01 Cr | negligible |
| **Group external** | **₹182.45 Cr** | | Oil→Mart is stock moving inside the group, not a sale |

**Half of Oil's invoiced turnover is a sale to Mart.** Quote Oil turnover without the
[[Cost-Centres-and-Dimensions|C-0005]] exclusion list and you double it. The full
intercompany CardCode list is in **C-0005**; use it, do not re-derive it.

### Four things that are in `OINV` and are not turnover

| # | What | Oil | Mart | Bev | How to exclude |
|---:|---|---:|---:|---:|---|
| 1 | **Go-live opening balances** posted as invoices | 11,078 docs, ₹74.74 Cr | 5 docs, ₹5.74 Cr | none | `"Handwrtten" = 'N'` |
| 2 | **Cancellation mirrors** (`CANCELED='C'`) | 320 docs, ₹35.39 Cr | 260, ₹8.71 Cr | 122, ₹0.77 Cr | `"CANCELED" = 'N'` |
| 3 | **Intercompany** | ₹98.47 Cr FY26-27 | ₹1.94 Cr | ₹0.01 Cr | C-0005 CardCode list |
| 4 | **Indirect income** — scrap, rent, manpower | 389 docs | 62 docs | 0 ever | `"DocType" = 'I'`, or exclude accounts `42000xx` |

Each of those is a separate filter. All four together, or the number is wrong.

---

## 2. The migration batch — 11,078 Oil "invoices" that are not sales

This is the single biggest trap in the whole table, and it is worth its own section
because it is invisible unless you look for it.

*Verified live 2026-08-24, all three books:*

| Book | `Handwrtten='Y'` | Every one dated | `DocTotal` | Posted to | Parties |
|---|---:|---|---:|---|---:|
| Oil | **11,078** | 2024-09-30 | ₹74,73,61,309 (**₹74.74 Cr**) | `3200003` OPENING BALANCE ACCOUNT | 313 |
| Mart | **5** | 2024-12-31 | ₹5,74,20,601 (**₹5.74 Cr**) | `3200003` OPENING BALANCE ACCOUNT | 5 |
| Beverages | **0** | — | — | — | — |

Every one of them:

- is `DocType = 'S'` (service, no item), one line, `TaxCode = 'Exampt'`
- carries `Dscription = 'OPENING BALANCE ACCOUNT'` (Oil) / `'OPENING BALANCE'` (Mart)
- posts the credit to **`3200003`, not a `4110xxx` sales account**
- has `DocSubType = '--'` and `GSTTranTyp = '--'` — no GST sub-type
- has **no buyer GSTIN** in `INV12.BpGSTN` and **no IRN**
- has a hand-typed `DocNum` (Mart's read `31122024`, `724122001` — dates, not series numbers)

**This confirms finding 9 in [[GST-Tax-Codes]]** — all 11,078 Oil `Exampt` sales lines are
the migration — and adds three things that note did not have: the flag (`Handwrtten='Y'`)
is a clean one-field filter, the account is `3200003`, and **Mart has 5 of them too while
Beverages has none**.

> **Anyone computing exempt turnover must exclude these.** Oil's entire `Exampt` sales
> figure is the go-live balance transfer. Filter `"Handwrtten" = 'N'` and Oil's exempt
> sales drop to essentially nothing. An "exempt sales ₹74.74 Cr" line in a GST working
> paper is a data-migration artefact, not a return position.

Sales-account queries are safe by accident (the batch never touches `4110xxx`).
`OINV`-level queries are not.

---

## 3. Cancelling one — why the same invoice appears three times

When an A/R invoice is cancelled, SAP writes a **second `OINV` row**. Traced live on Oil
`DocNum 626080260`:

| Row | `DocNum` | Series | `CANCELED` | `DocTotal` | Journal |
|---|---|---|---|---:|---|
| the original | 626080260 | 2855 `HR_G0826` | **`Y`** | +₹46,971 | Debtor Dr, Sales Cr, COGS Dr, FG Cr |
| the mirror | 626082107 | 2903 **`CNHR0826`** (`IsForCncl='Y'`) | **`C`** | **+₹46,971** | the exact same lines, **sides flipped**, memo `A/R Invoice - Cancellation - …` |

The mirror keeps the **same `DocDate`**, the **same positive `DocTotal`**, gets its number
from the month's **cancellation series**, and its lines carry `BaseType = 13` pointing at
the original. Its `Comments` gains `… Based On A/R Invoices 626080260.`

Three consequences, all measured:

1. **C-0021 is exactly this.** A `<> 'Y'` filter keeps the mirror and double-counts:
   Oil +₹35.39 Cr, Mart +₹8.71 Cr, Bev +₹0.77 Cr of phantom turnover. Always `= 'N'`.
2. **The ledger is fine either way.** The mirror's journal is an exact reversal, so a
   `JDT1`-based figure nets to zero on its own. Only document-level sums break.
3. **`flow-OINV-*.md`'s "copied from A/R Invoice" row is cancellations, not re-issues.**
   Oil's 142 documents / 472 lines with `BaseType=13` in 365 days are cancellation
   mirrors. Do not read that 1.7% as "invoices copied from invoices".

→ [[Document-Status-and-Cancellation]] · [[Numbering-Series]]

---

## 4. How an invoice arrives — and why Mart is upside-down

Copy source, `INV1.BaseType`, last 365 days (from `_data/flow-OINV-*.md`):

| Base | Oil lines | Oil docs | Mart lines | Mart docs | Bev lines | Bev docs |
|---|---:|---:|---:|---:|---:|---:|
| `17` [[Sales-Order]] | **80.5%** | 7,026 | 12.6% | 3,263 | **88.1%** | 3,174 |
| `15` [[Delivery]] | 11.8% | 1,030 | **84.4%** | 9,871 | 2.7% | 65 |
| `-1` keyed from scratch | 6.0% | 940 | 1.4% | 444 | 6.0% | 143 |
| `13` A/R invoice | 1.7% | 142 | 1.6% | 178 | 3.1% | 65 | ← cancellations (§3) |
| **fully hand-keyed documents** | **935 (10.2%)** | | **443 (3.2%)** | | **143 (4.1%)** | |

### The inversion, explained

The census looks backwards: **Mart has 6,126 deliveries to Oil's 2,842, yet Oil issues
31,084 invoices to Mart's 25,752.** Both halves are real, and there is one mechanism
behind them.

**Oil bills straight off the sales order.** `UpdInvnt = 'I'` on all 31,084 Oil invoices —
the invoice *is* the stock issue. Goods leave against the invoice, so no delivery note is
needed. Oil's 2,842 deliveries are the exceptions where stock moves *before* a sale
exists — **1,256 of its 2,792 live deliveries (45%) are not third-party sales at all**:
746 branch transfers to our own registrations (`CUSTA000001/2/3/4`), 256 free samples
(`CUSTA000356`) and 254 consignments to Mart (`CUSTA000606`).

**Mart cannot do that**, because its business is marketplaces. Goods must sit in a
Flipkart/Amazon fulfilment centre before any consumer has bought anything, so a bulk
delivery challan moves them and the tax invoices are carved off it afterwards, in
batches, as the platform settles. Measured:

- 9,871 Mart invoices in 365 days came off just **2,892 distinct deliveries** — a
  **3.4 : 1 fan-out**.
- The worst case: delivery `DocEntry 10645` / `DocNum 1504264835` → **143 invoices**,
  ₹7.07 Cr, all to one marketplace customer, all dated 2026-04-30.
- Mart's operators label them in `Comments`, on top of SAP's auto text:
  `FLIPKART HARYANA 01-21 APRIL Based On Deliveries 1504264835.` ×127 ·
  `MARKETPLACE FLIPKART BULK DELIVERY NOTE · 1265 ORDERS · FLIPKART B2C HARYANA · 2026-07-30 …` ×72

So Mart needs *fewer, larger* deliveries and gets *more* invoices per delivery. Mart
invoices are also long: 96,005 lines over 9,871 documents ≈ **9.7 lines each**, against
Oil's ~3.

*Measured; the "goods must be at the FC first" reason is inferred from the delivery
comments and the marketplace customer, and matches [[Delivery]].*

### Drafted first — three different houses

| | Oil | Mart | Bev |
|---|---:|---:|---:|
| `WddStatus='P'` (came via an approved draft), all history | 8,370 (27%) | 3,618 (14%) | 4,936 (**88%**) |
| same, last 120 days | **2,186 (87%)** | 715 (17%) | 1,494 (**88%**) |
| `ODRF` drafts of ObjType 13 ever | 9,790 | 4,015 | 5,948 |

`WddStatus = 'P'` ⟺ `draftKey` is set (Oil 2,188 vs 2,186 in the window — the two
disagree on two rows). **Beverages has always drafted and approved every invoice. Oil has
moved to it recently:** 43% of invoices in Apr-2025, 78% in Mar-2026, 88% in Jul-2026.
Mart still posts direct. If someone tells you "we always draft A/R invoices here", ask
which company they work in.

---

## 5. Before you start — the pre-flight list

- [ ] **Which company?** Oil / Mart / Beverages are three separate books. A CardCode,
      a series number and even a UDF's spelling differ between them.
- [ ] **Is there a sales order or delivery to copy?** 90–97% of the time there is, and
      copying brings customer, item, price, tax code, warehouse, HSN, branch and the
      Variety dimension for free. Find it before you start typing.
- [ ] **Which branch** — Delhi (`BPLId` 1) / Factory-Haryana (2) / Punjab (3) / HP (4) /
      Karnataka (5, Mart only). It sets the series, the GSTIN we bill under, and
      `INV12.LocGSTN`.
- [ ] **The series for this branch, this month, this sub-type.** `GA` for a GST tax
      invoice, `--` for non-GST, `GD` for a debit memo. Never a `CN…` series — that is
      SAP's. → [[Numbering-Series]]
- [ ] **Does the customer have a GSTIN?** It decides B2B vs B2C, which decides whether an
      IRN must be generated (§8). Read it from `INV12.BpGSTN` on a comparable past
      invoice — **never** from `OCRD.LicTradNum` (empty for every customer) or
      `CRD7.TaxId0` (that is the 10-character PAN). **C-0014.**
- [ ] **Same state or different?** `CG+SG@5` intra-state, `IGST@5` inter-state. SAP
      determines it, but check what it chose. → [[GST-Tax-Codes]]
- [ ] **Goods or a service?** Item invoice (`DocType='I'`) vs service invoice (`'S'`,
      posts to a `42000xx` income account, no stock movement). Beverages has never
      raised a service invoice.
- [ ] **The buyer's PO number**, if this is an e-commerce or CSD customer — they reject
      invoices without it. Goes in `NumAtCard`. General-trade invoices have none.
- [ ] **Transport details** — bilty/LR number, vehicle, transporter, mobile. Hand-typed
      UDFs, filled on 62–89% of recent Oil and Beverages invoices. Have the paper.
- [ ] **Payment terms.** 72% of live Oil invoices are `GroupNum = -1` = *ADVANCE/CASH/
      0 DAYS*. Do not leave the customer's real credit term on a cash sale.
- [ ] **Quantity is in PIECES — single bottles.** `unitMsr='PCS'`, `NumPerMsr=1` on 5,300
      of 5,412 recent Oil lines. The "20 PCS" in an item name is carton configuration.
      Multiplying by it inflates volume ~20×. **C-0001.**

---

## 6. Fields that matter — header (`OINV`)

Fill rates from `_data/profile-OINV.md`. **Filled = non-null *and* non-blank *and*
non-zero.** `—` means empty in every row of that book; `n/a` means the column does not
exist there at all.

| Field | Reads as | Filled (Oil / Mart / Bev, 120 d) | Required? | Notes |
|---|---|---|---|---|
| `CardCode` / `CardName` | the customer | 100 / 100 / 100 | **required** | 628 distinct in Oil. Check it against C-0005 before it lands in a turnover figure |
| `DocDate` | posting date = invoice date | 100 / 100 / 100 | **required** | Drives every turnover query |
| `TaxDate` | GST date | 100 / 100 / 100 | auto | **= `DocDate` on 19,945 of 20,006 live Oil invoices (99.7%).** The A/P rule that they differ (**C-0017**) does **not** apply on the sales side |
| `DocDueDate` | when payment is due | 100 / 100 / 100 | auto | = `DocDate` on 76% of Oil — because most terms are cash/advance |
| `Series` | numbering series | 100 / 100 / 100 | **required** | 139 distinct. Wrong one = wrong number on a GST document → [[Numbering-Series]] |
| `DocNum` | the printed invoice number | 100 / 100 / 100 | auto | **Decoded differently per book** — see trap 6 |
| `DocType` | `I` item · `S` service | 100 / 100 / 100 | **required** | Live: Oil 18,977 `I` / 389 `S`; Mart 25,165 / 62; **Bev 5,346 / 0** |
| `BPLId` / `BPLName` | branch | 100 / 100 / 100 | **required** | Oil: FACTORY 14,994 · DELHI 13,444 · PUNJAB 2,580 |
| `VATRegNum` | **our** GSTIN for that branch | 100 / 100 / 100 | auto | Three values in Oil, one per branch. Not the customer's |
| `DocSubType` / `GSTTranTyp` | `GA` GST invoice · `--` non-GST · `GD` debit memo | 100 / 100 / 100 | **required** | Always identical to each other. `--` on Oil is 11,078 migration rows + 0 real |
| `CtlAccount` | debtor control account = the channel | 100 / 100 / 100 | auto from the customer | Oil, 18 of them: `1101005` E-COM 15,988 · `1101001` GT 4,659 · `1101004` MT 3,413 · `1101008` CALL CENTRE · `1101014` CASH SALE · `1101013` CSD · `1101015` STAFF · `1102003/5` inter-branch |
| `NumAtCard` | the buyer's PO / order ref | 28 / 36 / 5 | **conditional** | Oil last 120 d: ECOM 430/526, CSD 210/211, **PUNJAB GT 1/317, DELHI GT 0/165**. E-com and CSD need it; GT has none |
| `Comments` | remarks on the document | 97 / 100 / 99 | auto, mostly | Oil 2,146 auto `Based On …` vs 301 typed. **Mart is the opposite: 2,949 typed** (the marketplace batch labels) |
| `JrnlMemo` | journal memo | 100 / 100 / 100 | auto | Always `A/R Invoices - <CardCode>`, or `A/R Invoice - Cancellation - <CardCode>` |
| `GroupNum` | payment terms | 100 / 100 / 100 | auto from the customer | **`-1` is not blank** — it is the term *ADVANCE/CASH/0 DAYS*, 14,323 of 20,006 live Oil invoices. Then NET-30 (2,050), NET-10 (1,729), NET-21 (667), LC 60 (638), 45% ADV (527) |
| `SlpCode` | sales employee | "100%" | **misleading** | `-1` = *-No Sales Employee / Buyer-* on **916/2,513 Oil (36%), 1,444/4,195 Mart (34%), 196/1,693 Bev (12%)** in the last 120 days. The profiler counts `-1` as filled |
| `VatSum` | GST on the document | 100 / 100 / 100 | auto | 64% all-history in Oil only because the 11,078 migration rows carry zero |
| `DocTotal` | invoice value incl. GST | 100 / 100 / 100 | auto | |
| `RoundDif` | rounding to the rupee | 71 / 81 / 95 | auto | Posts to `5680014` SHORT AND EXCESS. `Rounding` says `N` even when `RoundDif` is non-zero — **test `RoundDif`, not `Rounding`** |
| `PaidToDate` / `ReceiptNum` / `LastPmnTyp` | settlement write-back | 60 / 60 / 64 | **not yours** | `ReceiptNum` = the `ORCT.DocEntry` of the **last** [[Incoming-Payment]] applied. Written by the payment, dated later. One receipt settles several invoices |
| `draftKey` / `WddStatus` | came from an approved draft | 87 / 18 / 88 | auto | §4 |
| `AtcEntry` | attachment | 43 / 77 / 65 | customary | → [[Attachments]] |
| `CANCELED` | `N` live · `Y` cancelled · `C` mirror | 100 / 100 / 100 | auto | §3, **C-0021** |
| `Handwrtten` | at JIVO: **"this is a migration row"** | 100 / 100 / 100 | auto | §2. SAP means "keyed with a manual number"; at JIVO that only ever happened at go-live |
| `U_SALES_PERSON` | **channel** (Oil only) | 93 / n/a / n/a | customary | 22 values. Last 120 d: ECOM 526 (₹87.12 Cr) · PUNJAB GT 317 · PRIVATE 256 · CSD 211 · DELHI GT 165 · CASH SALE 131 · HARYANA GT 124 · PUNJAB MT 90 · FREE SAMPLE · EXPORT · CSD. **This, not `SlpCode`, is how Oil segments channel** |
| `U_BilltyNumber` · `U_BiltyDate` · `U_TransporterName` · `U_VehicleNoM` · `U_Mob_No` · `U_Dipatch_Date` | the transport block, hand-typed | 71 / 24 / n/a · 69 / 24 / 88 · 66 / 24 / 83 · 62 / 24 / n/a · 54 / 24 / 82 · 76 / 24 / 88 | customary | **Beverages spells two of them differently** — `U_BiltyNumber` (one L) and `U_VechileNom`. Under its own names Bev fills them on 1,502 and 1,403 of 1,693 recent invoices — 89% and 83%. A group-wide query on the Oil spelling reports "Beverages records no transport", which is false |
| `U_UNE_ACTH` (header) / `U_UNE_ACTD` (line) | redirect the sale to `1102007` SALES BRANCH TRANSFER | <1 / 3 / 100 | add-on | Branch-transfer invoices in Oil: **176 documents, 738 lines, ₹4.71 Cr, and only since 2025-12-22** — billed to `CUSTA000001/2/3`, our own Delhi / Haryana / Punjab registrations. Filled on **98% of all Beverages invoices**, where it is the norm rather than the exception |
| `U_OMS_Order_No` | OMS order reference | <1 / n/a / 3 | dead-ish | See trap 12 |
| `U_PONo`, `U_GRPO`, `U_MartCustomer`, `U_MartCN`, `U_OMS_REF`, `U_CreditCreated` | Oil-only UDFs | ≤18% | | `n/a` in Mart and Beverages — sending them there is an error, not a no-op |

### Header fields SAP offers that JIVO never uses

Empty in **every** row of every book: `DiscPrcnt` / `DiscSum` (no header discount is ever
given — discounting is done in the price), `DocTotalFC` / `PaidFC` / `GrosProfFC` /
`RoundDifFC` (9 USD invoices in Oil ever), `TotalExpns` / `ExpAppl` / `TaxOnExp*`
(freight on an A/R invoice — 3 documents in Oil, ever, and `INV3` is otherwise unused),
`BaseDiscPr`, `RevRefNo` / `RevRefDate` (24 of 31,084).

Single-valued in every row, so not decisions: `Transfered='N'`, `PartSupply='Y'`,
`Confirmed='Y'`, `CreateTran='Y'`, `UpdInvnt='I'`, `UpdCardBal='B'`, `InvntDirec='X'`,
`Posted='Y'`, `Excised='O'`, `DutyStatus='Y'`, `OpenForLaC='Y'`, `ComTrade='E'`,
`EDocStatus='C'`, `EDocProces='C'`, `EDocType='F'`, `Installmnt=1`, `LangCode=8`,
`ReqType=12`, `OriginType='M'`. **The whole `EDoc*` family is inert** — SAP's own
e-document engine is switched off; e-invoicing runs through an add-on instead (§8).

`OwnerCode` (document owner) is filled on 3% of Oil, **never** in Mart, <1% in Bev.
`Notify` has one value (`N`) on the 12–50% of rows where it is set at all — a dead flag.

---

## 7. Fields that matter — lines (`INV1`)

| Field | Reads as | Filled (Oil / Mart / Bev, 120 d) | Notes |
|---|---|---|---|
| `ItemCode` · `Dscription` | the item | 99 / 100 / 100 | 791 distinct items in Oil. Blank on service lines |
| `Quantity` · `unitMsr` · `NumPerMsr` | **pieces — single bottles** | 99 / 100 / 100 | `PCS` on 5,300 of 5,412 recent Oil lines, `NumPerMsr=1`. Also `LTR` (19, loose oil), `DRM`, `KGS`, `MTR`. **C-0001** |
| `Price` · `LineTotal` · `PriceBefDi` | rate and value, net of GST | 86 / 63 / 97 | Mart's 63% is the zero-value marketplace/promo lines |
| `WhsCode` | warehouse shipped from | 99 / 100 / 100 | 33 distinct in Oil |
| `AcctCode` | revenue account | 100 / 100 / 100 | 60 distinct in Oil. `4110xxx` = product sales by variety; `4200xxx` = indirect income |
| `TaxCode` | **the GST code — this is the field** | 100 / 100 / 100 | Oil: `IGST@5` 48,567 · `CG+SG@5` 32,026 · `Exampt` 11,078 (all migration) · `IGST@12` · `CG+SG@12` · `CG+SG@18` · `IGST@18`. → [[GST-Tax-Codes]] |
| `VatGroup` | **not the field** | 23 / 89 / 15 | Blank on more than three-quarters of recent Oil lines while `TaxCode` is 100%. Never key a report on it |
| `VatPrcnt` | rate | 100 / 100 / 100 | 5 values in Oil: 5%, 0%, 12%, 18%, 0.1% |
| `HsnEntry` | HSN for goods | 99 / 100 / 100 | 103 distinct in Oil |
| `SacEntry` | SAC for services | 1 / <1 / — | **Mutually exclusive with HSN, cleanly.** On live Oil invoices: 83,712 lines HSN-only (all `DocType='I'`), 392 SAC-only (all `'S'`), **zero both, zero neither**. **C-0013** confirmed exactly |
| `OcrCode` | **dimension 1 = Variety** | 100 / 100 / 100 | 36 distinct. Auto from the item — `OLIVE`, `MUSTARD`, `SUNFLOWR` |
| `CogsOcrCod` · `CogsAcct` | Variety and COGS account for the cost side | 97 / 98 / 97 | Auto |
| `OcrCode2..5` | dimensions 2–5 | **—** / <1 / **—** | **An A/R invoice needs no Budget or Sub-Budget.** Those are gated on `5xxxxxx` expense accounts, and a sale line posts to `4xxxxxx`. → [[Cost-Centres-and-Dimensions]] |
| `LocCode` | location | 100 / 100 / 100 | 3 values in Oil: 2 (55,549) · 1 (31,920) · 3 (10,701) |
| `BaseType` · `BaseEntry` · `BaseRef` | what it was copied from | 93 / 98 / 93 | §4. `BaseType=13` means a cancellation, not a copy |
| `TargetType` · `TrgetEntry` | what was built on it | 3 / 3 / 3 | `14` = credited later (1,968 Oil lines), `13` = the cancellation mirror |
| `VatGrpSrc` | where the tax code came from | 100 | Recent Oil: `N` 4,681 · `D` 799 (SAP's determination table) · `M` 170 (typed by hand). **Only 3% of tax codes are typed** — the rest arrive with the copy or are determined. *`N` = inherited from the base document is inferred, from the fact that 93% of lines are copied* |
| `U_Purpose` | `SALE` / `CONSUMABLE` / `RETURNABLE` / `BST` | 3 / 85 / — | **Mart uses it on 85% of lines, Oil on 3%, Beverages never** |
| `U_SchemeAgst` | scheme tag, mirrors the Variety | 100 / 100 / 100 | |
| `U_Disp_Qty` · `U_Recvd_Qty` | dispatched / received quantity | 80 / 11 / 86 · 47 / <1 / 61 | Oil and Bev use them; Mart does not |
| `LineNum` · `VisOrder` · `BaseLine` | "filled 70 / 87 / 59%" | | Another `0`-is-not-blank artefact: line 0 reads as empty. Ignore the fill rate |

### Line fields never used

`Rate`, `DiscPrcnt` (10 values in 98,170 rows, and 4 of them are corrupt — `-542847.43`,
`-2952752.35`), `TotalFrgn`, `OpenSumFC`, `DistribSum`, `GrssProfFC`, `StockSumFc`,
`GTotalFC`, `FreeTxt`, `Text`, `CountryOrg`, `ListNum`, `U_UNE_LTS`, `U_F_Year`.
`RevCharge='N'` and `WtLiable='N'` on all but 104 lines — **reverse charge and TDS do not
happen on the sales side.**

---

## 8. E-invoicing and the IRN — it runs **inside** SAP, and it is the B2B test

**Plainly: yes, e-invoicing happens in SAP.** Not through SAP's own e-document engine
(every `EDoc*` field is inert), but through the **"UTL" statutory add-on**, which stores
one row per attempt in **`@UTL_MDEXTH`** — 18,346 rows in Oil, 9,372 in Mart, 4,933 in
Beverages. `@AUTL_MDEXTH` is its audit shadow, same counts.

| | Oil | Mart | Bev |
|---|---:|---:|---:|
| IRNs obtained for A/R invoices (`U_UTL_DocType='13'`, `U_UTL_IST='S'`) | **13,101** | **7,435** | **3,223** |
| failed attempts (`'F'`) | 1,570 | 302 | 1,348 |
| also for A/R credit memos (`'14'`) | 3,089 | 1,566 | 229 |
| latest | 2026-08-24 | 2026-08-24 | 2026-08-24 |

It is **live today** in all three books. The row carries `U_UTL_IRN`, `U_UTL_AckNo`,
`U_UTL_QRPT` (the QR payload), `U_UTL_IRNGENDT` and `U_UTL_CANDT`.

### The rule, measured in all three books

An invoice needs an IRN if and only if the buyer has a GSTIN. Live, non-migration,
non-cancelled invoices:

| Book | B2B (`INV12.BpGSTN` set) | of which have an IRN | B2C (no GSTIN) | of which have an IRN |
|---|---:|---:|---:|---:|
| Oil | 12,869 | **12,753 (99.1%)** | 6,497 | 12 (0.2%) |
| Mart | 7,706 | **7,267 (94.3%)** | 17,521 | 12 (0.1%) |
| Beverages | 3,127 | **3,093 (98.9%)** | 2,219 | 14 (0.6%) |

That also explains the odd `BpGSTN` fill rates in `_data/profile-INV12.md` (57 / 31 /
59%): **Mart is 69% B2C by document count** — marketplace consumers have no GSTIN — while
Oil and Beverages are two-thirds B2B. A low `BpGSTN` fill in Mart is the business model,
not a data-quality defect (**C-0016**).

**The join is a trap.** `@UTL_MDEXTH."U_UTL_BaseEntry"` is `NVARCHAR`, not an integer:

```sql
LEFT JOIN (SELECT DISTINCT TO_INTEGER("U_UTL_BaseEntry") BE
           FROM "JIVO_OIL_HANADB"."@UTL_MDEXTH"
           WHERE "U_UTL_DocType" = '13' AND "U_UTL_IST" = 'S') x
       ON x.BE = h."DocEntry"
```

### The two smaller tables, so nobody chases them

- **`@UTL_ST_EICO` — 1 row in each book, and it is *configuration*, not data.** The
  e-invoice gateway's endpoint and login for the add-on. The GSP is **Logitax**
  (`api.logitax.in`); last edited 2026-06-08. It stores a credential in clear text —
  do not select `*` from it into anything shared.
- **`OMS_IRN_LOG` — Oil 50 rows, Bev 26, Mart 2.** Same shape as `@UTL_MDEXTH`, but
  `Creator = 'OMS'`: an OMS-driven attempt at getting IRNs, **all** on FACTORY-branch A/R
  invoices, running only **2026-07-28 → 2026-08-13**, 41 of 50 successful in Oil. A pilot,
  not the production path. Not the table to read for e-invoice coverage.

### The 116 / 439 / 34 B2B invoices with no IRN

Oil's 116 are spread thin — 1 to 4 a month, except **25 in Aug-2026 and 7 in Jul-2026**.
Some of the current month's will be pending; the rest are genuine misses. This is the
single most useful read-back check on this document type (§11).

---

## 9. The e-way bill — mostly **outside** SAP, and stalled inside it

`@UTL_ST_EWAYDT` records e-way bills raised from SAP. It links the same way
(`U_UTL_ST_BaseEntry` → `DocEntry`, `U_UTL_ST_DocType` = `'13'` invoice / `'67'` stock
transfer) and holds `U_UTL_ST_EwayNo`, `EWBGenDt`, `EWBExpDt`, `AckNo`, `PDFURL`.

| Book | rows | successful for A/R invoices | latest one | coverage of live invoices |
|---|---:|---:|---|---:|
| Oil | 1,333 | 805 | **2026-06-01** | ~4% |
| Mart | 2,560 | 2,217 | **2026-06-27** | ~9% |
| Beverages | 279 | 229 | **2025-10-29** | ~4% |

**Nothing has been generated from inside SAP in any book since 2026-06-27** — nearly two
months before this note was mined. So today the e-way bill is raised **outside** SAP: on
the government portal, or by the transporter, or through the GSP directly.

**Is an invoice incomplete without one?** In the books, no. 96% of Oil's live invoices
have no `@UTL_ST_EWAYDT` row and post perfectly well. What SAP *does* hold is the
transport paperwork, hand-typed into the header UDFs — bilty number, vehicle, transporter,
mobile, dispatch date (§6). **That block is the e-way-bill evidence in SAP, not the add-on
table.** `@UTL_ST_INTREWBILL` (Oil 117, Bev 2, Mart 0) is the inter-state variant and is
effectively dead.

> `OINV.EWBGenType` looks like it should answer this and does not. Oil: `L` on all 11,078
> migration rows plus 6,874 others, `N` on 13,132 — and 767 of the 802 actual e-way bills
> sit on `EWBGenType='N'`. The field is near-inverted. Only the add-on table knows.

---

## 10. The journal it posts

TransType **13**, last 365 days (`_data/gl-13-{OIL,MART,BEV}.md`):

| | Oil | Mart | Bev |
|---|---:|---:|---:|
| Journals | 9,130 | 13,749 | 3,447 |
| Lines | 66,667 | 95,909 | 21,572 |
| Dr = Cr | ₹902.12 Cr | ₹422.69 Cr | ₹23.55 Cr |
| Most common line count | **6** (3,075) | **4** (2,394) | **6** (2,603) |

### The shape of a correct one

```
Dr  1101xxx  SUNDRY DEBTORS <channel>   the customer, gross of GST
  Cr  2132xxx  OUTPUT IGST / CGST / SGST @ rate      the tax
  Cr  4110xxx  SALES <variety> @ rate                one line per variety
  Cr  1103001  FINISHED GOODS <OIL|BEVERAGES>        stock leaving      ┐ only if the
Dr  5000xxx  COGS <variety>                          cost of that stock ┘ stock moves here
Dr/Cr 5680014 SHORT AND EXCESS                       the rounding paise
```

**Two lines tell you instantly whether it was keyed the normal way:**

1. **`5680014` SHORT AND EXCESS** is on 7,145 of Oil's 9,130 journals (78%) and carries
   `OINV.RoundDif` with the sign flipped — total ₹2,239 Dr / ₹737 Cr across 7,145 lines,
   i.e. **paise**. Verified line by line. A large amount there is not rounding.
2. **The stock pair (`1103001` Cr / `5000xxx` Dr) is present only when the invoice itself
   moves the stock.** And its frequency matches the copy source exactly:

   | Book | journals | with a FINISHED GOODS line | **documents** off an order or keyed |
   |---|---:|---:|---:|
   | Oil | 9,130 | 7,024 (**77%**) | 7,966 of 9,133 (87%) |
   | Mart | 13,749 | 3,415 (**25%**) | 3,707 of 13,756 (**27%**) |
   | Bev | 3,447 | 3,302 (**96%**) | 3,317 of 3,447 (**96%**) |

   Mart and Beverages match almost exactly. **A Mart invoice off a delivery has no COGS
   line — the stock left at the delivery.** That is correct, not a missing posting. An Oil
   invoice off a sales order without a COGS line is wrong. Oil's 10-point gap (87% vs 77%)
   is its 389 service invoices, its zero-value free-sample billing and its branch
   transfers — none of which move finished goods.

### Dimensions on the journal lines

Variety travels as **`JDT1.ProfitCode`**, not `OcrCode` — filled on 41% of Oil lines, 49%
Mart, 34% Bev (the sales and COGS lines; not the debtor or tax lines). Dimensions 2–5 are
0% on all three. `ShortName` (the subledger) is 100%. → [[Cost-Centres-and-Dimensions]]

### Odd accounts you will meet

- **`1102007` SALES BRANCH TRANSFER** — Oil 213 journal lines, ₹10.54 Cr credited. Stock
  moving between JIVO's own GST registrations, which the law requires be invoiced. §6.
- **`5640001` ADVERTISEMENT** in Mart, 42 lines, ₹9.27 Cr credited *through A/R invoices* —
  marketplace advertising billed back. Worth understanding before anyone reads Mart's ad
  spend.
- **`2131020/21/22` INPUT IGST/CGST/SGST @ 20/40%** appearing on **Beverages A/R
  invoices** — an *input* tax account credited through a sales document: `2131021` and
  `2131022` on 39 lines each, **₹49.83 lakh apiece**, plus `2131020` on 17 lines,
  ₹1.16 lakh. Unexplained; see Open questions.
- **`4300001/2` SALES / COST OF FIXED ASSETS SOLD** in Beverages — an asset disposal keyed
  as an A/R invoice. Two documents. Not turnover.

Never group by account *number* across books: `4110014` is `SALES OIL @ 5%` in Oil,
`SALES SESAME @ 5%` in Mart and `SALES @ 5%` in Beverages. → [[Chart-of-Accounts]]

---

## 11. Real examples

**The common shape** — Oil `DocEntry 78973` / `DocNum 626080517`, 2026-08-24, off a sales
order (`_data/sample-OINV-OIL.md`):

| | |
|---|---|
| Customer | `CUSTA000606` JIVO MART PVT LTD — **intercompany** |
| Branch / GSTIN | FACTORY (`BPLId` 2), our Haryana registration |
| Series / DocNum | 2855 `HR_G0826` → 626080517 |
| From | Sales Order 1726086707 (`BaseType=17`), `Comments` auto: `Based On Sales Orders 1726086707.` |
| Buyer PO | `NumAtCard` = the customer's PO |
| Lines | 3, all `PCS`, warehouse `BH-BT`, `TaxCode = CG+SG@5` (both in Haryana), `OcrCode` = SUNFLOWR / OLIVE / MUSTARD, `AcctCode 4110014` |
| Buyer GSTIN | `INV12.BpGSTN` set → B2B → IRN required |
| Total | ₹24,36,000 incl. ₹1,16,000 GST |
| Journal | 8 lines: Debtor Dr 24,36,000 · CGST Cr 58,000 · SGST Cr 58,000 · three Sales Cr · FG Cr 18,29,714 · COGS Dr 18,29,714. **No rounding line** — the total was exact |

Note `VatGroup` is **blank on line 1** and populated on lines 2 and 3 of the *same*
document. `TaxCode` is on all three. That is the trap in one document.

**The awkward variant** — Oil `DocNum 626080260` cancelled and mirrored as 626082107 in
`CNHR0826`, both `DocTotal +₹46,971`, journals exact reversals. §3.

**The Mart variant** — one bulk delivery `1504264835` → 143 invoices, ₹7.07 Cr, one
marketplace customer, one date, operator-labelled `FLIPKART HARYANA 01-21 APRIL Based On
Deliveries 1504264835.` §4.

**The migration variant** — Mart `DocEntry 706`, `DocNum 31122024` (a date typed as an
invoice number), 2024-12-31, one `Exampt` line reading `OPENING BALANCES` for
₹1,43,48,180 posted to `3200003`. §2.

---

## 12. Traps

1. **11,078 Oil "invoices" and 5 Mart ones are the go-live opening balance, ₹80.48 Cr
   between them.** Filter `"Handwrtten" = 'N'`. They are `DocType='S'`, `TaxCode='Exampt'`,
   account `3200003`, dated 2024-09-30 / 2024-12-31. **Beverages has none.** Confirms
   [[GST-Tax-Codes]] finding 9 — and any exempt-turnover figure that includes them is wrong.
2. **`CANCELED` is three-valued and the `'C'` mirror carries a positive `DocTotal`.**
   `<> 'Y'` overstates Oil by ₹35.39 Cr, Mart by ₹8.71 Cr, Bev by ₹0.77 Cr. Always
   `= 'N'`. **C-0021.**
3. **52% of Oil's FY26-27 invoiced turnover is a sale to Mart** (₹98.47 Cr of ₹188.83 Cr,
   `CUSTA000606`). Apply the C-0005 list before quoting any Oil sales figure. **C-0005.**
4. **`flow-OINV-*.md`'s "copied from A/R Invoice" is cancellations.** Oil's 142
   documents / 472 lines with `BaseType=13` in 365 days are the `CANCELED='C'` mirrors,
   not re-invoicing.
5. **Quantity is single bottles.** `PCS`, `NumPerMsr=1`, on 5,300 of 5,412 recent Oil
   lines — 69.2 lakh pieces in 120 days. The "20 PCS" in an item name is carton
   configuration; multiplying by it inflates volume ~20×. **C-0001.**
6. **`DocNum` decodes differently in Mart than in Oil and Beverages.** Verified against
   the live Aug-2026 series ranges: Oil `626080101` and Bev `626087951` are
   `<state><YY><MM><serial>`; **Mart `608260101` is `<state><MM><YY><serial>`.** A
   DocNum parser written on Oil silently reads Mart's month as a year.
7. **`SlpCode` reads "100% filled" and is blank a third of the time.** `-1` = *no sales
   employee* on 36% of recent Oil, 34% Mart, 12% Bev invoices. Same class of error as
   `GroupNum = -1` (which is a real payment term, *ADVANCE/CASH/0 DAYS*, not "none") and
   `LineNum = 0`. Any `IS NOT NULL` test on this table lies.
8. **`VatGroup` is not the tax field. `TaxCode` is.** `VatGroup` is blank on 77% of
   recent Oil lines while `TaxCode` is 100% — and it can be blank on one line of a
   document and set on the next. → [[GST-Tax-Codes]]
9. **Buyer GSTIN is `INV12.BpGSTN` and nowhere else.** `OCRD.LicTradNum` is empty for
   every customer; `CRD7.TaxId0` is the 10-character PAN. Deciding B2B vs B2C from either
   is wrong, and B2B/B2C decides whether an IRN was needed. **C-0014.**
10. **HSN and SAC are mutually exclusive** and on live Oil invoices perfectly so: 83,712
    HSN-only item lines, 392 SAC-only service lines, zero both, zero neither. A blank
    `HsnEntry` on a service line is correct. **C-0013.**
11. **Beverages spells two transport UDFs differently** — `U_BiltyNumber` (one L) and
    `U_VechileNom`, against Oil/Mart's `U_BilltyNumber` and `U_VehicleNoM`. Eleven Oil
    UDFs do not exist in Mart or Beverages at all. A group-wide query on the Oil spelling
    reports "Beverages records no transport"; it records it on 89% of invoices.
12. **`U_OMS_Order_No` is a decayed integration, not a reference you can rely on.**
    Oil, by month: 0 in Oct-2024, 315–592 (40–75% of invoices) Nov-2024 → Jul-2025, then
    158, 17, 14, 13, 10, 9, 1, **0 for Mar–Jul 2026**, 11 in Aug-2026. Never join Oil
    invoices to OMS orders on it for a period you have not checked. And source the report
    from SAP regardless — **C-0012**.
13. **The e-way bill is currently raised outside SAP.** Nothing in any book since
    2026-06-27. `OINV.EWBGenType` does not tell you whether one exists (it is
    near-inverted). Only `@UTL_ST_EWAYDT` knows, and it covers 4–9% of invoices.
14. **`OMS_IRN_LOG` is not the e-invoice table.** 50 rows in Oil from a two-week pilot.
    The real one is `@UTL_MDEXTH`, 18,346 rows, live today.
15. **`ReceiptNum` is written by the payment, not by you**, and it holds only the **last**
    receipt applied — one receipt settles several invoices. Use [[Internal-Reconciliation]]
    or `JDT1` for a proper settlement trail, and remember **C-0019**: `DocStatus='O'`
    is unreliable at JIVO.
16. **Turnover from `OINV` includes indirect income.** Oil's 389 live service invoices are
    scrap sales (318), rent received (26), manpower and technical services — accounts
    `4200003/5/6/12/13/14`, not `4110xxx`. Fine for a turnover figure; wrong for a
    "product sales" figure. Beverages has never raised one.
17. **`@UTL_ST_EICO` holds a plaintext gateway credential.** One row per book. Never
    `SELECT *` it into a shared document, a log, or this repo.
18. **A Mart invoice with no COGS line is not broken.** 75% of Mart's A/R journals have no
    stock pair, because the stock left at the delivery. In Oil and Beverages the same
    absence is a real problem. §10.

---

## 13. How to create one from the CLI

`sapb1 draft invoice` exists and maps to `DocObjectCode = oInvoices` (13), creating an
`ODRF` draft that a human then adds in SAP B1 → Document Drafts.

**It has never been used at JIVO.** The shared write log
(`queries/*/sap-writes.jsonl`, read 2026-08-24) contains 28 `oPurchaseInvoices` drafts,
6 `oQuotations`, 2 `oPurchaseCreditNotes` — and **no A/R invoice, ever**. There is no
`jivo-ar-invoice` skill and no proven payload. Treat the skeleton below as untested.

```
# Preview first, always:  --dry-run
sapb1 draft invoice --dry-run --company JIVO_OIL_HANADB --data '{
  "CardCode":  "CUSTA0000xx",
  "DocDate":   "2026-08-24",          # = TaxDate on the sales side (99.7%)
  "Series":    2855,                  # NNM1: ObjType 13 × branch × month × sub-type
  "DocumentSubType": "bod_GSTTaxInvoice",   # GA. '--' is bod_None, GD is a debit memo
  "BPL_IDAssignedToInvoice": 2,       # branch — API name differs from HANA BPLId
  "NumAtCard": "<buyer PO>",          # e-com and CSD reject invoices without it
  "DocumentLines": [
    { "ItemCode":"FG00000xx", "Quantity":960, "Price":800,
      "WarehouseCode":"BH-BT", "TaxCode":"CG+SG@5",
      "CostingCode":"SUNFLOWR" }      # dimension 1 = Variety; 2-5 not needed on a sale
  ]
}'
```

Pre-checks worth running before you send anything:

1. **Is there already a draft or an invoice for this order?** `ODRF` ObjType 13 and `OINV`
   on the same `CardCode` + `NumAtCard`.
2. **Copy, don't key.** 90–97% of real invoices come off an order or delivery. A payload
   built by hand loses the price, the tax code, the HSN, the warehouse and the Variety —
   and `BaseType` will say `-1` forever, which is how the copy chain gets broken.
3. **The series exists for *this* branch, *this* month, and is not exhausted**
   (`NextNumber <= LastNum`, `Locked='N'`, `IsForCncl='N'`). → [[Numbering-Series]]

**What the CLI cannot do:** no `PUT`; the only OData actions it reaches are
`Cancel` on the 14 marketing document sets (`sapb1 cancel <doctype> <DocEntry>`,
guarded, SAP posts a reversal) and `SaveDraftToDocument` (`sapb1 add-draft`);
`Orders(1)/Close` and every other action stay refused. `sapb1 add-draft <DocEntry>` presses Add on a draft — a live posting nothing here can
undo — and the project `CLAUDE.md` documents it as one of the six write commands, with
the approval-template rule that decides whether the draft reaches the approver or posts
LIVE. An A/R invoice becomes real when a human adds it. → [[Document-Drafts]]

---

## 14. Verify after saving

Read the document back and check the six things SAP fills in for itself, or quietly does
not:

- [ ] **`DocNum` came from the series you meant** — not a `CN…` cancellation series, and
      the branch digit matches the branch.
- [ ] **`VatSum` is non-zero and the tax split is right.** Intra-state must be two lines
      (CGST + SGST), inter-state one (IGST). Compare `INV12.LocStatCod` with
      `INV12.BpStateCod`.
- [ ] **An IRN row exists, if the buyer has a GSTIN.** This is the check that catches the
      most:

      ```sql
      SELECT h."DocNum", h."DocDate", t."BpGSTN"
      FROM   "JIVO_OIL_HANADB"."OINV"  h
      JOIN   "JIVO_OIL_HANADB"."INV12" t ON t."DocEntry" = h."DocEntry"
      LEFT JOIN (SELECT DISTINCT TO_INTEGER("U_UTL_BaseEntry") BE
                 FROM "JIVO_OIL_HANADB"."@UTL_MDEXTH"
                 WHERE "U_UTL_DocType"='13' AND "U_UTL_IST"='S') x ON x.BE = h."DocEntry"
      WHERE  h."Handwrtten"='N' AND h."CANCELED"='N'
        AND  t."BpGSTN" IS NOT NULL AND t."BpGSTN" <> '' AND x.BE IS NULL
        AND  h."DocDate" >= ADD_DAYS(CURRENT_DATE, -30);
      ```
- [ ] **The journal has the stock pair — if it should.** Off an order or keyed: `1103001`
      Cr and `5000xxx` Dr must both be there. Off a delivery: they must not.
- [ ] **`5680014` SHORT AND EXCESS is in paise.** Anything larger means the rounding
      picked up something it should not have.
- [ ] **`SlpCode` is not `-1`** and, in Oil, **`U_SALES_PERSON` is set** — otherwise the
      invoice will never appear in a channel report.
- [ ] **The transport block is filled** if goods are moving: bilty, vehicle, transporter.
      In Beverages check `U_BiltyNumber` / `U_VechileNom`, not the Oil spellings.

---

## Open questions

1. **Why did 25 Oil B2B invoices in Aug-2026 get no IRN**, against 1–4 a month before?
   Either an add-on failure or a legitimate exemption. The GSP log (Logitax) or the
   billing desk would settle it; the tables only show the absence.
2. **Why does a Beverages A/R invoice ever touch `2131020/21/22` INPUT IGST/CGST/SGST @
   20/40%?** 17–39 lines, ₹49.83 lakh each on CGST and SGST, credited to an *input* tax
   account through a sales
   document. Could be the new 40% slab wired to the wrong authority accounts. Needs the
   GST consultant plus `OSTA`, not a query.
3. **What does `OINV.EWBGenType` actually mean?** `L` on 18,000 Oil rows, `N` on 13,000,
   and it does not predict whether an e-way bill exists. Nobody has documented it and
   nothing at JIVO appears to read it.
4. **Why are 143 invoices carved off one marketplace delivery on a single date?** A GST
   line limit, a platform settlement window, or a habit. I measured the fan-out; I did not
   establish the reason. Ask Mart billing.
5. **Is `VatGrpSrc='N'` really "inherited from the base document"?** It fits (93% of lines
   are copied) but is not proven. `'D'` = determination and `'M'` = manual are safe.
6. **Was the in-SAP e-way bill feature deliberately abandoned in June 2026, or did it
   break?** All three books stop within four weeks of each other, which looks like a
   decision. Nobody has confirmed it.
7. **Oil is issuing fewer, much larger invoices, and nobody has explained why.** Live Oil
   invoices per month fell from **965 (Oct-2025) to 458 (Jun-2026)** while the net value
   *rose* from **₹39.91 Cr to ₹37.09 Cr and then ₹52.33 Cr in Jul-2026** — average invoice
   value roughly doubled, from ₹4.1 lakh to ₹7.3 lakh. Consolidation of GT billing, a
   channel shift into e-com, or a change in who invoices? It needs a per-channel value
   series, which is a report and not this note.

---

## Queries used

Every figure above came from one of these, run on **2026-08-24** through
`./hana-sql/hana-sql -env connections/hana-office-bridge.env "<one SELECT>"`. Swap
`JIVO_OIL_HANADB` for `JIVO_MART_HANADB` / `JIVO_BEVERAGES_HANADB`.

```sql
-- 1. the migration batch, all three books
SELECT "Handwrtten", COUNT(*), MIN("DocDate"), MAX("DocDate"), SUM("DocTotal")
FROM   "JIVO_OIL_HANADB"."OINV" GROUP BY "Handwrtten";

-- 2. what it posted to
SELECT l."AcctCode", a."AcctName", COUNT(*), SUM(l."LineTotal"),
       MIN(l."Dscription"), COUNT(DISTINCT h."CardCode")
FROM   "JIVO_OIL_HANADB"."OINV" h
JOIN   "JIVO_OIL_HANADB"."INV1" l ON l."DocEntry" = h."DocEntry"
LEFT JOIN "JIVO_OIL_HANADB"."OACT" a ON a."AcctCode" = l."AcctCode"
WHERE  h."Handwrtten" = 'Y' GROUP BY l."AcctCode", a."AcctName";

-- 3. house turnover (and the ORIN half); add a CardCode CASE for the C-0005 split
SELECT COUNT(*), SUM("DocTotal"), SUM("VatSum"), SUM("DocTotal" - "VatSum")
FROM   "JIVO_OIL_HANADB"."OINV"
WHERE  "CANCELED" = 'N' AND "DocDate" >= '2026-04-01' AND "DocDate" < '2026-08-25';

-- 4. the three-valued CANCELED, and what a <>'Y' filter costs
SELECT "CANCELED", COUNT(*), SUM("DocTotal" - "VatSum")
FROM   "JIVO_OIL_HANADB"."OINV" GROUP BY "CANCELED";

-- 5. the cancellation mirror, end to end
SELECT h."DocNum", h."Series", h."CANCELED", h."DocTotal", h."Comments",
       j."Line_ID", j."Account", j."Debit", j."Credit", j."LineMemo"
FROM   "JIVO_OIL_HANADB"."OINV" h
JOIN   "JIVO_OIL_HANADB"."JDT1" j ON j."TransId" = h."TransId"
WHERE  h."DocNum" IN (626080260, 626082107) ORDER BY h."DocNum", j."Line_ID";

-- 6. the Mart delivery fan-out
SELECT COUNT(DISTINCT l."DocEntry") INVOICES, COUNT(DISTINCT l."BaseEntry") DELIVERIES,
       COUNT(*) LINES_
FROM   "JIVO_MART_HANADB"."INV1" l
JOIN   "JIVO_MART_HANADB"."OINV" h ON h."DocEntry" = l."DocEntry"
WHERE  l."BaseType" = 15 AND h."DocDate" >= ADD_DAYS(CURRENT_DATE, -365);

-- 7. e-invoice coverage by B2B/B2C  (see §11 for the full LEFT JOIN form)
SELECT "U_UTL_DocType", "U_UTL_IST", COUNT(*), MAX("U_UTL_IRNGENDT")
FROM   "JIVO_OIL_HANADB"."@UTL_MDEXTH" GROUP BY "U_UTL_DocType", "U_UTL_IST";

-- 8. e-way bills raised from inside SAP
SELECT "U_UTL_ST_DocType", "U_UTL_ST_EwayST", COUNT(*), MAX("U_UTL_ST_EWBGenDt")
FROM   "JIVO_OIL_HANADB"."@UTL_ST_EWAYDT"
GROUP BY "U_UTL_ST_DocType", "U_UTL_ST_EwayST";

-- 9. HSN vs SAC, mutually exclusive (C-0013)
SELECT CASE WHEN l."HsnEntry" IS NOT NULL AND l."SacEntry" IS NOT NULL THEN 'both'
            WHEN l."HsnEntry" IS NOT NULL THEN 'HSN only'
            WHEN l."SacEntry" IS NOT NULL THEN 'SAC only' ELSE 'NEITHER' END,
       h."DocType", COUNT(*)
FROM   "JIVO_OIL_HANADB"."OINV" h
JOIN   "JIVO_OIL_HANADB"."INV1" l ON l."DocEntry" = h."DocEntry"
WHERE  h."CANCELED" = 'N' AND h."Handwrtten" = 'N' GROUP BY 1, 2;

-- 10. quantity really is pieces (C-0001)
SELECT l."unitMsr", l."NumPerMsr", COUNT(*), SUM(l."Quantity")
FROM   "JIVO_OIL_HANADB"."OINV" h
JOIN   "JIVO_OIL_HANADB"."INV1" l ON l."DocEntry" = h."DocEntry"
WHERE  h."CANCELED" = 'N' AND h."DocDate" >= ADD_DAYS(CURRENT_DATE, -120)
GROUP BY l."unitMsr", l."NumPerMsr";

-- 11. draft-and-approve adoption, by month
SELECT TO_VARCHAR("DocDate",'YYYY-MM'), COUNT(*),
       SUM(CASE WHEN "WddStatus" = 'P' THEN 1 ELSE 0 END)
FROM   "JIVO_OIL_HANADB"."OINV" WHERE "DocDate" >= '2025-04-01' GROUP BY 1 ORDER BY 1;

-- 12. who keys them
SELECT u."USER_CODE", u."U_NAME", COUNT(*), SUM(h."DocTotal" - h."VatSum")
FROM   "JIVO_OIL_HANADB"."OINV" h
LEFT JOIN "JIVO_OIL_HANADB"."OUSR" u ON u."USERID" = h."UserSign"
WHERE  h."DocDate" >= ADD_DAYS(CURRENT_DATE, -120) GROUP BY 1, 2 ORDER BY 3 DESC;

-- 13. live A/R series for this month, per branch
SELECT "Series", "SeriesName", "BPLId", "DocSubType", "NextNumber", "LastNum",
       "Locked", "IsForCncl"
FROM   "JIVO_OIL_HANADB"."NNM1" WHERE "ObjectCode" = '13' AND "SeriesName" LIKE '%0826';

-- 14. buyer PO discipline by channel
SELECT "U_SALES_PERSON", COUNT(*),
       SUM(CASE WHEN "NumAtCard" IS NOT NULL AND "NumAtCard" <> '' THEN 1 ELSE 0 END)
FROM   "JIVO_OIL_HANADB"."OINV"
WHERE  "DocDate" >= ADD_DAYS(CURRENT_DATE, -120) AND "CANCELED" = 'N'
GROUP BY "U_SALES_PERSON" ORDER BY 2 DESC;

-- 15. SHORT AND EXCESS is the rounding
SELECT h."DocNum", h."Rounding", h."RoundDif", j."Account", j."Debit", j."Credit"
FROM   "JIVO_OIL_HANADB"."OINV" h
JOIN   "JIVO_OIL_HANADB"."JDT1" j ON j."TransId" = h."TransId"
WHERE  j."Account" = '5680014' AND h."DocDate" >= ADD_DAYS(CURRENT_DATE, -30);
```

Corpus files this note is built on, all mined 2026-08-24:
`_data/profile-OINV.md` · `profile-INV1.md` · `profile-INV12.md` ·
`gl-13-{OIL,MART,BEV}.md` · `flow-OINV-{OIL,MART,BEV}.md` · `sample-OINV-OIL.md` ·
`rosetta-OINV.md` · `profile-NNM1.md`.

Related: [[Entry-Types-Census]] · [[AR-Credit-Memo]] · [[Sales-Order]] · [[Delivery]] ·
[[Incoming-Payment]] · [[AP-Invoice]] · [[GST-Tax-Codes]] · [[Numbering-Series]] ·
[[Document-Status-and-Cancellation]] · [[Cost-Centres-and-Dimensions]] ·
[[Chart-of-Accounts]] · [[Business-Partner-Master]] · [[Fiscal-Periods-and-Posting-Dates]] ·
[[Attachments]] · [[Document-Drafts]] · [[Approval-Workflow]] · [[Add-on-Tables-and-UDFs]] ·
[[Opening-Balance-and-Cutover]] · [[Field-Name-Rosetta]] · [[Internal-Reconciliation]]
