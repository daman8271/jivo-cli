---
type: document
sap_tables: [OPDN, PDN1, PDN12]
objtype: 20
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# GRPO — the goods receipt, and why Accounts cares about it

> The factory (or a branch) says "this arrived". SAP takes the stock in and parks the
> cost in a holding account until the vendor's bill turns up. 19,697 of them across the
> three books.

Accounts does not usually *make* a GRPO. Accounts *inherits* one — and its quality
decides how much of the [[AP-Invoice]] has to be typed. Read this note as "what arrives
free, and what to check before trusting it".

## At a glance

| | |
|---|---|
| SAP tables | `OPDN` header · `PDN1` lines · `PDN12` tax/address |
| ObjType / TransType | **20** |
| Volume | Oil 11,649 · Mart 3,222 · Bev 4,826 · **19,697** total |
| Last 120 days | Oil 1,827 · Mart 562 · Bev 1,201 |
| Who keys it | **26 logins in Oil** — factory and stores, not Accounts. Top three: `UserSign` 28 (3,450), 36 (2,529), 31 (1,583) |
| Drafted first? | **Usually not** — 0.39 drafts per posted document, against 1.02 for an A/P invoice |
| Needs approval? | Sometimes — `WddStatus` is `-` on 7,368 of 11,649, `P` on 4,148, `A` on 133 |
| Where it goes | **87.7% of lines are copied onward**, nearly all into an [[AP-Invoice]] |

## Two kinds of GRPO, and the second one surprises people

| `DocType` | Means | Oil docs | What it receives |
|---|---|---:|---|
| `I` | **Item** receipt | 7,379 | Physical goods into a warehouse |
| `S` | **Service** receipt | 4,270 (**37%**) | Freight, transport, and other services "received" |

A **service GRPO** is how JIVO books an incoming freight or transporter service before the
carrier's bill arrives. `acc/INVENTORY.md` counts 260 service-GRPO-based A/P invoices in
90 days, 231 of them TRANSPORTER. So when a transporter bill lands, check for a service
GRPO before keying anything — a third of the receipt population is this shape.

## Where a GRPO itself comes from

| Base document | Lines (Oil, 365d) | Share |
|---|---:|---:|
| `22` — [[Purchase-Order]] | 8,055 | **62.2%** |
| `-1` — keyed from scratch | 4,211 | 32.5% |
| `20` — another GRPO | 689 | 5.3% |

By document: **62.7% fully copied from a PO, 37.3% fully keyed.** So roughly a third of
receipts happen with no purchase order behind them — which is exactly the situation that
blocked a real entry today (a bill with neither gate entry nor PO). The absence of a PO is
common enough to be normal, and it is still the thing that stops you.

## What Accounts inherits — the free fields

When an [[AP-Invoice]] line is copied from a GRPO line (57.1% of Oil A/P lines), these
arrive already filled and correct:

| Arrives free | Why it matters |
|---|---|
| Vendor (`CardCode`, `CardName`) | No lookup, no risk of the wrong book's code |
| Item, quantity, rate | The bulk of an item bill |
| Branch (`BPLId`) | 90% of Oil GRPOs are FACTORY |
| Warehouse (`WhsCode`) | |
| **Tax code** | And it is reliable — see below |
| HSN / SAC | |
| The **scanned bill** (`AtcEntry`) | → [[Attachments]] |
| `BaseAtCard` | The vendor reference the receipt recorded |

That is the whole argument for copy-from-target: a GRPO-copied line is a click, a keyed
line is fifteen decisions.

## The tax code is trustworthy — measured, against expectation

Today's batch produced a case where a gate entry showed 0% GST while the bill carried GST,
and the input credit was lost. That looked like it might be systemic. **It is not.**

Matching every GRPO-copied A/P line back to its source line over 365 days in Oil:

| | Lines | Documents |
|---|---:|---:|
| Tax code **same** on GRPO and invoice | **10,617** | 3,504 |
| Tax code **different** | **9** | 6 |

Nine lines in a year — 0.08%. The disagreements, in full:

| GRPO tax | A/P tax | Lines |
|---|---|---:|
| `IGST@18` | `CG+SG@18` | 7 |
| `IGST@5` | `IGST@18` | 2 |

Both patterns are *place-of-supply* corrections (inter-state recorded, intra-state billed,
or a rate correction), not a zero-rated receipt. So: **the GRPO's tax code is a reliable
default.** When it is wrong it is wrong in a specific way — the state, not the rate — and
it is worth checking on inter-state receipts specifically.

*(This is a case where the number contradicted the impression a single incident left.
Worth stating plainly rather than generalising from one bill.)*

## Timing — when does the bill follow the receipt?

Days from the GRPO's `DocDate` to its A/P invoice's `DocDate`, Oil, 365 days:

| Gap | Lines | |
|---|---:|---|
| **Same day or earlier** | **6,360** | 57% — the C-0017 rule being followed |
| 1–3 days | 906 | |
| 4–7 days | 566 | |
| 8–15 days | 889 | |
| 16–30 days | 1,127 | |
| 31–90 days | 1,154 | |
| 90+ days | 185 | |

The 57% matches C-0022's independently measured 51% for Oil closely enough to trust both.
So: **post on the GRPO's date** (that is the rule), but **never infer a gate-in date from
an existing A/P invoice** (that is the trap) — 43% of them were posted on some other day.

The long tail matters too: 1,339 lines were billed more than a month after receipt. Those
are the GRNI balance, sitting in `2140001` waiting.

## Fields that matter (`OPDN` header)

| Field | Reads as | Oil filled | Notes |
|---|---|---:|---|
| `CardCode` / `CardName` | The vendor | 100% | |
| `DocDate` | **Gate-in date** | 100% | This is the date the A/P invoice should post on |
| `DocType` | `I` item / `S` service | 100% | 7,379 / 4,270 |
| `BPLId` / `BPLName` | Branch | 100% | `2` FACTORY 10,527 (**90%**) · `1` DELHI 666 · `3` PUNJAB 455 · `8` HARYANA INFO 1 |
| `CtlAccount` | Vendor control account | 100% | 13 values, same family as the invoice |
| `NumAtCard` | Vendor reference | see note | Feeds `BaseAtCard` on the invoice |
| `DocStatus` | Open / closed | 100% | `C` 11,279 · `O` **370** — only 370 receipts still unbilled |
| `CANCELED` | **Three-valued** | 100% | `N` 10,703 · `Y` **473** · `C` 473 |
| `WddStatus` | Approval | 100% | `-` 7,368 · `P` 4,148 · `A` 133 |
| `Rounding` | | 100% | `Y` on 3,129 (27%) |
| `Printed` | | 100% | `Y` on 2,498 — a printed GRPO is the gate copy |
| `PIndicator` | Fiscal period | 100% | Same `AUG-26-27` naming as [[Numbering-Series]] |

### A data-quality defect worth knowing

`BPLId` has **4** distinct values but `BPLName` has **7**:

```
FACTORY ×10,523   Factory ×4
DELHI   ×665      Delhi   ×1
PUNJAB  ×451      Punjab  ×4
HARYANA INFO ×1
```

The same three branches appear under two capitalisations each. `BPLName` is a denormalised
copy, so **group by `BPLId`, never by `BPLName`** — a name-based branch report silently
splits FACTORY into two rows. (Compare `OPCH`, where `BPLId` and `BPLName` both have
exactly 6 values and agree.)

### Header user fields — nearly all dead

Unlike the A/P invoice, the GRPO's UDFs are almost entirely unused: `U_Recv_Date` has 2
rows, `U_TransporterInvoice` 11, `U_UNE_ACTH` 1, `U_TotalAmt` 11 non-zero. Only
`U_delbranch` / `U_delbranchnam` carry anything (766 rows: FACTORY 562, PUNJAB 149,
DELHI 55) and none in the last 120 days.

**So the transporter detail (`U_BilltyNumber`, `U_VehicleNoM`, `U_TransporterName`) is
captured on the A/P *invoice*, not on the receipt** — 11% of recent Oil invoices carry it,
the GRPO essentially never does. If you need the LR number, it comes off the paper at
billing time, not from the receipt.

## The journal it posts

TransType 20. Oil, 365 days: 5,176 journals. The characteristic entry is:

- **Dr** the inventory or expense account (the goods are ours now)
- **Cr** `2140001` **Goods received but not invoiced** — the GRNI holding account

Then the [[AP-Invoice]] reverses the GRNI side and credits the vendor. That two-step is
why `2140001` shows ₹118 Cr of debits on A/P journals in a 120-day window: it is not a
cost, it is the receipt being cleared.

Full fingerprint: `_data/gl-20-OIL.md`.

## Traps

1. **`CANCELED` has three values and GRPOs are cancelled far more often than invoices** —
   473 of 11,649 (4.1%), against 113 of 16,334 (0.7%) for A/P invoices. A `<> 'Y'` filter
   keeps the `C` mirrors and double-counts. Memory records this inflating an Oil OPDN total
   by ₹94.63 Cr. Always test `= 'N'`. **(C-0021)**
2. **`BPLName` has duplicate capitalisations; `BPLId` does not.** Group by the id.
3. **A third of GRPOs have no purchase order.** Do not treat a missing PO as an anomaly —
   but do treat it as a blocker if the bill also has no gate entry.
4. **The GRPO is usually not drafted** (0.39 per posted document) while the A/P invoice
   always is (1.02). So a GRPO you cannot find may genuinely not exist yet, whereas an A/P
   invoice you cannot find may be sitting in Document Drafts.
5. **`DocStatus = 'O'` is more meaningful here than on an invoice** — only 370 open, and an
   open GRPO really does mean unbilled stock. But C-0019's warning still applies to
   anything settled by manual journal.
6. **Quantity is in pieces, not cartons** — same as everywhere. **(C-0001)**

## For the operator holding a bill

1. Search for a GRPO by vendor and by date around the gate-in date.
2. Found one? Copy from it. Take its `DocDate` as your posting date, and trust its tax
   code unless the receipt is inter-state and the bill is not.
3. Service bill from a transporter? Look for a **service** GRPO (`DocType` `S`) — 37% of
   receipts are that shape.
4. No GRPO and no PO? You cannot complete the entry from the paper alone. Go back to
   whoever received the goods, do not invent a receipt.

## Open questions

1. What are the 689 lines copied from another GRPO (5.3%)? *Inferred:* a receipt split or
   corrected by re-receipting, but not confirmed.
2. `WddStatus` = `A` on 133 documents while the other 11,516 are `P` or `-`. What makes
   those 133 different? → [[Approval-Workflow]]
3. Why does Beverages run 4,826 GRPOs against Oil's 11,649 on a much smaller book — is
   Beverages receiving in smaller lots, or receipting differently?
4. 185 lines were billed more than 90 days after receipt. Is that a real ageing problem in
   GRNI or a handful of long-running projects?

## Queries used

```sql
-- does the GRPO's tax code survive onto the invoice?
SELECT CASE WHEN G."TaxCode"=P."TaxCode" THEN 'same' ELSE 'DIFFERENT' END K,
       COUNT(*) LINES, COUNT(DISTINCT P."DocEntry") DOCS
FROM "JIVO_OIL_HANADB"."PCH1" P
JOIN "JIVO_OIL_HANADB"."PDN1" G
  ON G."DocEntry"=P."BaseEntry" AND G."LineNum"=P."BaseLine"
WHERE P."BaseType"=20 AND P."DocDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY CASE WHEN G."TaxCode"=P."TaxCode" THEN 'same' ELSE 'DIFFERENT' END;
-- same 10,617 lines / DIFFERENT 9 lines

-- and when it differs, how?
SELECT G."TaxCode" GRPO_TAX, P."TaxCode" AP_TAX, COUNT(*) LINES
FROM "JIVO_OIL_HANADB"."PCH1" P
JOIN "JIVO_OIL_HANADB"."PDN1" G
  ON G."DocEntry"=P."BaseEntry" AND G."LineNum"=P."BaseLine"
WHERE P."BaseType"=20 AND G."TaxCode"<>P."TaxCode"
  AND P."DocDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY G."TaxCode", P."TaxCode" ORDER BY LINES DESC;

-- days from receipt to bill
SELECT DAYS_BETWEEN(GH."DocDate", PH."DocDate") D
FROM "JIVO_OIL_HANADB"."PCH1" P
JOIN "JIVO_OIL_HANADB"."OPCH" PH ON PH."DocEntry"=P."DocEntry"
JOIN "JIVO_OIL_HANADB"."OPDN" GH ON GH."DocEntry"=P."BaseEntry"
WHERE P."BaseType"=20 AND PH."DocDate" >= ADD_DAYS(CURRENT_DATE,-365);
```

Field fill rates, vocabularies, the GL fingerprint and the copy-from split come from the
mined corpus:

```bash
python3 sap-b1/entry-vault/bin/profile.py OPDN --co OIL,MART,BEV --days 120 --vocab-max 30
python3 sap-b1/entry-vault/bin/profile.py PDN1 --co OIL,MART,BEV --days 120
python3 sap-b1/entry-vault/bin/gl.py 20 --co OIL --days 365 --memo
python3 sap-b1/entry-vault/bin/flow.py OPDN --co OIL --days 365
```
