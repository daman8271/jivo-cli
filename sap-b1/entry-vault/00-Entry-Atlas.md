---
type: index
companies: [OIL, MART, BEV]
mined: 2026-08-24
---

# Entry Atlas — how JIVO actually keys entries

> **Start here.** This vault answers one question: *when someone sits down with a piece of
> paper, what do they need to know before they touch SAP?*
>
> Not what SAP can do — [[00-SAP-B1-Atlas|the other vault]] covers that. What **JIVO**
> does, measured from the live books, with the query behind every number.

## Why this exists

On 2026-08-24 we entered nine A/P invoices from vendor scans. Most were right. The misses
were all the same shape:

| The miss | What it really was |
|---|---|
| A budget code inherited from the receipt | A handwritten *Common* on the paper meant `FACT_COM`, not `Factory` |
| A reference number nobody set | `OriginalRefNo` on a credit memo — SAP accepts null silently |
| A series looked up by hand | A field that blocks the draft entirely if wrong |

None of those were hard. All of them were **unknown in advance**. That is the gap this
vault closes.

## The rules this vault is built on

- Every number was measured against the live books, and the note carries the SQL.
- **Measured / inferred / unverified** are labelled separately. A well-structured
  explanation is not evidence.
- The team's [corrections](../../harness/corrections/INDEX.md) outrank every note here. A
  note that contradicts one is flagged as a finding, not quietly filed as fact.
- Read-only. Nothing in this vault was produced by writing to SAP.

## Read this first

- **[[Entry-Types-Census]]** — every entry type JIVO actually makes, with volumes. Also the
  list of what JIVO *never* uses (no purchase requests, no inventory counting, no down
  payments, no deposits, no cheque printing) — which stops future work hunting for data
  that was never there.
- **[[Transport-Bill-Playbook]]** — the transporter / freight bill, end to end. 433 of
  them in the first five months of FY26-27 and the single most GRPO-driven entry JIVO makes: the
  factory has already keyed one service GRPO per bilty, so the only thing you decide is
  **TDS**. Measured 2026-08-27; evidence in [[transport-ap-evidence]].
- **[[Purchase-to-Pay]]** — the meta-level answer. What surrounds an A/P invoice, what it
  inherits, and the five things it **never** inherits and you must decide every time.

## The five things you always decide yourself

Whatever else exists upstream, these are never handed to you. They are where the mistakes
live:

| | Field | Note |
|---|---|---|
| 1 | Numbering series | [[Numbering-Series]] — and it is **book-local**; the Aug-26 factory A/P GST series is 3684 in Oil, 2766 in Mart, 2777 in Beverages |
| 2 | Location code | [[Warehouses-and-Locations]] |
| 3 | Budget dimension (`CostingCode3`) | [[Cost-Centres-and-Dimensions]] — read the handwritten note, never inherit |
| 4 | TDS | [[TDS-Withholding]] — 34% of lines are liable, and a CLI draft comes out with zero |
| 5 | The vendor's own invoice number | [[AP-Invoice]] — it is the duplicate key |

Plus one that belongs to a document you did not create: the **posting date**, which is the
[[GRPO]]'s date, not today's and not the vendor's.

## Foundations — the machinery every entry depends on

| Note | Decides |
|---|---|
| **[[Field-Name-Rosetta]]** | **The same thing has four names** — paper, screen, API, database. Start here whenever a field "doesn't exist" |
| [[Chart-of-Accounts]] | Which GL account, and the expense picklist for service bills |
| [[Numbering-Series]] | Whether the draft saves at all |
| [[Cost-Centres-and-Dimensions]] | The five `OcrCode` slots — profit centre, month, **budget**, department, state |
| [[Branches-and-BPLId]] | Branch, GST registration, which series apply |
| [[GST-Tax-Codes]] | Which of the 16 codes, and the two that are misspelled in the master |
| [[TDS-Withholding]] | Section, rate, and what SAP will *not* do for you |
| [[Warehouses-and-Locations]] | Warehouse and `LocationCode` |
| [[UDF-Dictionary]] | Every `U_*` field, what it means, and how often it is really used |
| [[Business-Partner-Master]] | Finding the right vendor — and why their code differs per book |
| [[Item-Master]] | `U_TYPE`, `U_Sub_Group`, `U_Variety`, UoM, HSN/SAC |
| [[Approval-Workflow]] | Who sees your draft, and what bounces it |
| [[Operators-and-Logins]] | Who keys what, and which login can reach which book |
| [[Fiscal-Periods-and-Posting-Dates]] | `DocDate` vs `TaxDate` vs `DueDate`, and closed periods |
| [[Document-Status-and-Cancellation]] | Why "open" and "cancelled" both lie |
| [[Attachments]] | Getting the scan onto the document, with its flags |
| [[Payment-Terms-and-Banks]] | Due dates, and how money actually moves |
| [[Add-on-Tables-and-e-Invoicing]] | The nine non-standard tables holding real entry data |

## Documents — one note per entry type

**Purchasing**
[[AP-Invoice]] · [[AP-Credit-Memo]] · [[GRPO]] · [[Purchase-Order]] · [[Goods-Return]] ·
[[Landed-Costs]]

**Sales**
[[AR-Invoice]] · [[AR-Credit-Memo]] · [[Delivery]] · [[Sales-Order]] · [[AR-Return]] ·
[[Sales-Quotation]] · [[Return-Request]]

**Money**
[[Incoming-Payment]] · [[Outgoing-Payment]] · [[Payment-Draft]] ·
[[Internal-Reconciliation]] · [[Bank-Statement]]

**Ledger**
[[Journal-Entry]] · [[Journal-Voucher]] · [[Opening-Balance-and-Cutover]]

**Stock & factory**
[[Stock-Transfer]] · [[Inventory-Transfer-Request]] · [[Goods-Receipt]] · [[Goods-Issue]] ·
[[Production-Order]] · [[Inventory-Revaluation]]

**Meta**
[[Document-Drafts]] — the unit of work, and all the CLI can create

## Flows — the chains

[[Purchase-to-Pay]] · [[Order-to-Cash]] · [[Month-End-Close]] · [[Imports-and-Landed-Cost]] ·
[[Intercompany]] · [[Factory-to-Books]] · [[Returns-and-Claims]] · [[Payroll-and-Statutory]]

## Findings worth knowing even if you read nothing else

Each of these was measured today and none of them is in SAP's documentation.

1. **The five dimensions are (profit centre, month, budget, department, state).** Nobody had
   written that down. `OcrCode3` is the budget field behind C-0027, and `Factory` (8,055
   uses) outnumbers `FACT_COM` (2,046) four to one — which is exactly why inheriting it is
   usually right and occasionally wrong.
2. **`DocType` splits A/P invoices into two different jobs.** `S` carries **zero** item
   lines, `I` carries only item lines. No mixed case. Oil is 55% `S`, so the majority of A/P
   work is the hard, fully-typed kind.
3. **Half of all A/P invoices are typed from paper** — 51.1% of Oil documents have no line
   copied from a receipt.
4. **`OriginalRefNo` is stored as `RevRefNo`.** The API name and the column name share no
   substring, so a HANA-side audit by name finds nothing and concludes the field is never
   filled. It is filled on 97% of A/P credit memos. → [[Field-Name-Rosetta]]
   And once visible, the shape matters more than the rate: on A/R credit memos SAP makes the
   pair **mandatory when the buyer has a GSTIN** — 5,055 B2B documents, **zero** blanks — so
   the real gap is the 3,366 credit notes to *unregistered* buyers (207 in the last four
   months), which GSTR-1 **CDNUR** requires. → [[AR-Credit-Memo]]
5. **SAP renames the same field depending on the entity.** A document's free text is
   `Comments`; a payment's is `Remarks`. A document's branch is `BPL_IDAssignedToInvoice`;
   a payment's is `BPLID`. **A payment written with `Comments` sets nothing and SAP does not
   complain.** The database stores document currency in `DocCur` and payment currency in
   `DocCurr` — one letter apart.
6. **75% of "open" A/P drafts are cancelled, not pending** — 817 of 1,088 in Oil. Count the
   backlog on `WddStatus`, never `DocStatus`.
7. **The GRPO's tax code is trustworthy**: it matches the invoice on 10,617 of 10,626 lines.
   The nine exceptions are place-of-supply corrections, not rate errors. One incident today
   suggested otherwise; the data says it is rare.
8. **`5680014` SHORT AND EXCESS touches more than half of all A/P journals and is pure
   rounding** — 3,904 of 3,921 lines under ₹1, ₹665 for the whole year. Not a variance
   account. Do not chase it.
9. **`VatGroup` is 18% populated; `TaxCode` is 100%.** A tax report keyed on `VatGroup`
   silently drops four fifths of Oil's purchase lines.
10. **Two tax codes are misspelled in the master** — `Exampt` and `RISGT@18`. Matching the
   correct spelling returns nothing.
11. **`BPLName` has duplicate capitalisations on GRPOs** (`FACTORY` and `Factory`) while
    `BPLId` does not. Group by the id.
12. **`CN…` in a series name means CANCELLATION, not credit note** — proven, not guessed.
13. **The chain is broken at every link, routinely.** 37% of receipts have no PO, 51% of
    invoices have no receipt, 59% of payments settle nothing specific. Any automation that
    assumes the happy path handles under half the work.

13. **Cross-book identity maps exist and are undocumented** — Beverages' `OCRD.U_OIL_CardCode`
    maps 2,417 partners back to Oil's codes with 98.5% name agreement, and `OACT.U_WG_GLNO`
    does the same for accounts. **But the map is missing the exact vendor everyone cites as
    the example** (Nexton), so it is a shortcut, never the lookup. Match on GSTIN.
14. **Journal vouchers are the main road, not a siding** — 59% of manual journals in Oil were
    posted from a parked voucher. And joining `OBTF` to `BTF1` on `TransId` explodes to 67.8
    million rows from 21,093 lines, silently. Use `BatchNum`.
15. **On a stock transfer, `DocStatus = 'C'` means cancelled, not completed** — `O` on all
    12,170 live documents, forever.

## The tools — re-run any of this yourself

All read-only, all through the guarded `hana-sql` binary. From the repo root:

```bash
# What operators actually fill in: per-field fill rate over all history AND a recent
# window, all three books side by side, plus the value list for every drop-down field
python3 sap-b1/entry-vault/bin/profile.py OPCH --co OIL,MART,BEV --days 120

# The journal a document type posts: accounts, sides, amounts, line-count shape, memos
python3 sap-b1/entry-vault/bin/gl.py 18 --co OIL --days 365 --memo

# Copied-from vs keyed-from-scratch, drafted-first ratio, approval volume
python3 sap-b1/entry-vault/bin/flow.py OPCH --co OIL --days 365

# Real finished documents: header, every line table, and the journal they made
python3 sap-b1/entry-vault/bin/sample.py OPCH --n 3 --co OIL

# Mine the whole corpus again (no model needed, ~40 min)
python3 sap-b1/entry-vault/bin/sweep.py --jobs 5
```

**Why the fill rate is the load-bearing number:** SAP stores `''` and `0` in fields nobody
ever types in, so a plain NULL test reports every field as fully used. The profiler counts a
field as filled only when it is non-null **and** non-blank **and** non-zero. That is what
separates *SAP offers this field* from *JIVO uses this field*.

If a query fails with connection refused, the SSH bridge to the SAP box dropped:
`bash sap-b1/entry-vault/bin/bridge.sh`. A watchdog also repairs it every 20 seconds.

## Where the raw measurements live

`_data/` — 221 files, 2.6 MB, mined 2026-08-24:

| Pattern | What it holds |
|---|---|
| `profile-<TABLE>.md` | 73 field profiles |
| `gl-<TransType>-<CO>.md` | 50 GL fingerprints |
| `flow-<TABLE>-<CO>.md` | 78 document-flow measurements |
| `sample-<TABLE>-OIL.md` | 20 real document dumps |

Every note is reproducible from these plus the SQL it quotes.

## Status

[[Build-Log]] · [the plan](PLAN.md)
