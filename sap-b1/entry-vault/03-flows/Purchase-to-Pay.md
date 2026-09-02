---
type: flow
sap_tables: [OPOR, OPDN, OPCH, ORPC, OVPM, OITR, OJDT]
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Purchase to pay — everything that surrounds an A/P invoice

> You asked for the meta level: when you think "A/P invoice", what else must you already
> know? This is that list, as a chain, with the measured drop-off at every link.

The whole point: **an A/P invoice is never a standalone entry.** It sits in the middle of a
five-step chain, and almost every mistake is really a mistake about a neighbour — the wrong
posting date (that belongs to the receipt), a missing series (that belongs to the branch),
an inherited budget code (that belongs to the paper), an unmatched payment (that happens
later, by someone else).

## The chain

```
[[Purchase-Order]]  →  [[GRPO]]  →  [[AP-Invoice]]  →  [[Outgoing-Payment]]  →  [[Internal-Reconciliation]]
    (OPOR)            (OPDN)          (OPCH)              (OVPM)                    (OITR)
    7,724             19,697          24,368              19,063                    49,840
       │                 │               │                   │                         │
   raised by         factory /        Accounts            Accounts               86% automatic
   purchase          stores                                                     14% a person
       │                 │               │                   │                         │
   no GL effect      Dr stock         Dr GRNI            Dr vendor              links payment
                     Cr GRNI          Cr vendor          Cr bank                to invoice
                                      Dr input GST
                                      Cr TDS
```

Two side branches leave the main line:

```
[[AP-Invoice]] → [[AP-Credit-Memo]]   (2,624 — short supply, rate difference, claims)
[[GRPO]]       → [[Goods-Return]]     (209 — the rare physical return)
```

## Where the chain actually breaks — measured, Oil, 365 days

| Link | Holds | Breaks | The number |
|---|---|---|---|
| PO → GRPO | 62.7% of GRPOs are copied from a PO | **37.3% have no PO** | 2,097 of 5,625 receipts |
| GRPO → invoice | 48.8% of invoices are copied from a GRPO | **51.1% are typed from paper** | 3,795 of 7,420 invoices |
| Receipt → bill timing | 57% posted on the receipt's date | 43% on some other date | 6,360 of 11,187 lines |
| Invoice → payment | 65% fully paid | **32% nothing paid** | 2,410 of 7,380 invoices, ₹122.4 Cr |
| Payment → invoice match | 41% settle specific invoices | **59% are on-account** | per `acc/INVENTORY.md` |

Read down that column: **the chain is broken at every single link, routinely.** This is not
a broken process — it is what the process is. Any automation that assumes the happy path
handles less than half the work.

## The two consequences that show up in the books

**1. GRNI — goods we have, bills we do not.** Account `2140001` (Goods received but not
invoiced) carries a net credit balance of **₹7.17 Cr** across 8,048 lines, and there are
**370 open GRPOs**. That is the receipt-to-bill gap, sitting on the balance sheet. Every
one of those 370 is a bill someone will eventually key — and 185 lines in the last year were
billed more than 90 days after receipt.

**2. Unmatched payments.** 59% of vendor payments settle nothing specific at the time, and
matching happens later through 49,840 internal reconciliations. **86% of those are automatic**
(SAP creates them when a payment is applied); the remaining 14% are people working the
reconciliation screen — Preshit 989, Bhawani 575, Taran 300 and others, with a name attached
on two thirds of them. So "pay the vendor" and "which bills did that pay" are two separate
jobs, and the second one produces no *document* — but it is not unowned.
→ [[Internal-Reconciliation]]

*(An earlier version of this note said reconciliations "carry no `UserSign` at all",
repeating `acc/INVENTORY.md`. Checked 2026-08-24: `OITR."UserSign"` is never null and 19,693
of 30,085 Oil rows carry a real user.)*

## What an A/P invoice inherits, and from where

This is the practical version of the chain. Each row is a decision you do **not** have to
make if the neighbour exists — and must make if it does not.

| The invoice needs | Comes from | If the neighbour is missing |
|---|---|---|
| Vendor `CardCode` | [[GRPO]] → [[Business-Partner-Master]] | Look it up by GSTIN. **Book-specific** — the same vendor has different codes in Oil and Beverages |
| Item, quantity, rate | [[GRPO]] | Type every line. Quantity is in **pieces**, not cartons (C-0001) |
| `DocDate` (posting) | **The GRPO's `DocDate`** = gate-in | You have no gate-in date. Do not use today's, do not use the vendor's (C-0017) |
| `TaxDate` | The vendor's paper | — |
| Tax code | [[GRPO]] — reliable, 10,617 of 10,626 lines agree | Pick from the 16 codes. Two are misspelled in the master (`Exampt`, `RISGT@18`) → [[GST-Tax-Codes]] |
| Branch `BPLId` | [[GRPO]] | Read it off the paper's GSTIN / unit → [[Branches-and-BPLId]] |
| Warehouse | [[GRPO]] | Item lines only → [[Warehouses-and-Locations]] |
| `LocationCode` | — **never inherited** | Always yours. `2` = factory/Haryana (C-0025) |
| `Series` | — **never inherited** | Look it up for (type, branch, month). **Book-local**: the Aug-26 factory A/P GST series is 3684 in Oil, 2766 in Mart, 2777 in Bev → [[Numbering-Series]] |
| GL account | — for item lines, from the item | **Service lines: entirely yours** → [[Chart-of-Accounts]] |
| `CostingCode3` (budget) | **NOT the GRPO** | Read the handwritten allocation. "Common" → `FACT_COM`, never the GRPO's `Factory` (C-0027) → [[Cost-Centres-and-Dimensions]] |
| TDS | — never inherited | 34% of lines are liable. A CLI draft comes out with 0 (C-0018) → [[TDS-Withholding]] |
| The scan | [[GRPO]]'s attachment, plus your own | Copy the base file **and** attach yours; set `U_CHK2` = `OK` (C-0026) → [[Attachments]] |
| `NumAtCard` | The vendor's invoice number, off the paper | It is the duplicate key — check it first |

**The five rows marked "never inherited" are where the mistakes live.** Series, location,
budget, TDS, and the vendor's own invoice number are yours every single time, whether or not
a GRPO exists. That is the answer to "what else do I need to know": those five, plus the
posting date that belongs to a document you did not create.

## Who does what — the handoffs

| Step | Who | Logins |
|---|---|---|
| [[Purchase-Order]] | Purchase | — |
| [[GRPO]] | **Factory / stores** | 26 in Oil; top three do 65% |
| [[AP-Invoice]] | **Accounts** | 19 in Oil; top three do 68% |
| [[AP-Credit-Memo]] | Accounts | 11 in Oil; four do 96% |
| [[Outgoing-Payment]] | Accounts (concentrated) | Taran keys 1,492 of 2,358 in 90 days |
| [[Internal-Reconciliation]] | **86% SAP, 14% a person** | Preshit 989 · Bhawani 575 · Taran 300 |

Two things follow. The receipt is created by a different department, so its quality is not
Accounts' to control — only to check. And the reconciliation step produces no *document*, so
it is invisible to anyone reading document tables — which is why "is this bill actually
settled?" has to be answered from `OCRD."Balance"` and `ITR1` rather than from the invoice.
→ [[Operators-and-Logins]], [[Internal-Reconciliation]]

## Every step is drafted and approved — except the ones that are not

| Document | Drafted? | Approval requests (90d, all books) |
|---|---|---:|
| [[AP-Invoice]] | **Always** — 1.02 drafts per posted doc | 2,857 |
| [[GRPO]] | Usually not — 0.39 | 970 |
| [[Purchase-Order]] | Sometimes | 555 |
| [[AP-Credit-Memo]] | Yes | 368 |
| [[Outgoing-Payment]] | Own table ([[Payment-Draft]]) | 171 |

So the CLI's draft-first rule is not a safety compromise — **it is what the process already
does** for the document Accounts keys most. → [[Document-Drafts]]

And a warning that changes how you read the backlog: of 1,088 "open" Oil A/P drafts, **817
are cancelled in approval, not pending.** Count the queue on `WddStatus`, not `DocStatus`.

## The full pre-flight list, in order

For any A/P invoice, whether or not there is a GRPO:

1. **Which book.** Oil / Mart / Beverages. Wrong book means re-keying.
2. **Is it already in?** Check `NumAtCard` for this vendor, and check Document Drafts —
   drafts get pre-keyed.
3. **Vendor `CardCode`** for *this* book.
4. **Item bill or service bill** (`DocType` `I` / `S`). 55% of Oil is service.
5. **Find the GRPO.** If it exists: copy from it, take its `DocDate`, trust its tax code.
6. **No GRPO?** Look for a PO. Neither? You cannot finish from the paper alone — go back to
   whoever received the goods.
7. **Series** for (type, branch, month), in this book.
8. **Branch**, from the paper's unit/GSTIN.
9. **GL account** per service line.
10. **Tax code**, matching the place of supply, RCM if applicable.
11. **`LocationCode`**.
12. **Five dimensions** — profit centre, month, **budget off the handwritten note**,
    department, state.
13. **TDS** — liable or not.
14. **`U_Recvd_Qty`** on service lines, if the paper states a quantity.
15. **The scan**, plus the base document's file, with the flags set.
16. **Read it back** — `WTAmount`, `DocTotal`, `VatSum`, the journal's line count.

## Traps that belong to the chain, not to any one document

1. **`DocDate = GRPO's DocDate` is a posting rule, not a fact about the books.** Follow it
   when posting; never *infer* a gate-in date from an existing invoice — only 57% match
   (C-0017 / C-0022).
2. **A missing PO is normal (37%); a missing PO *and* a missing GRPO is a blocker.**
3. **Three-valued `CANCELED` at every step.** GRPOs are cancelled 4.1% of the time against
   0.7% for invoices, so the error is largest exactly where the volume is (C-0021).
4. **`DocStatus = 'O'` is unreliable across the whole chain** (C-0019). 2,410 invoices show
   nothing paid — some of those are settled by journal or by an unapplied on-account payment.
5. **A vendor's code, and a series number, are both book-local.** Neither travels.
6. **The GRPO does not carry the transporter detail** — LR number, vehicle, carrier are
   captured on the *invoice* (11% of recent Oil bills), never on the receipt.

## Open questions

1. The 370 open GRPOs and ₹7.17 Cr of GRNI — how old is the oldest, and is anyone working
   the list?
2. Are the 2,410 "nothing paid" invoices genuinely unpaid, or settled by journal? C-0019
   says the field cannot tell you. Ageing from `OCRD."Balance"` would.
3. Who or what performs the 49,840 internal reconciliations, given no `UserSign`? A person
   in the reconciliation screen, or a scheduled process? → [[Internal-Reconciliation]]
4. 817 cancelled A/P drafts — clustered by operator, vendor, or period? If it is a habit
   rather than noise, it is a process problem worth naming.

## Queries used

```sql
-- settlement state of a year of A/P invoices
SELECT CASE WHEN "PaidToDate" IS NULL OR "PaidToDate"=0 THEN 'nothing paid'
            WHEN ABS("PaidToDate"-"DocTotal")<1        THEN 'fully paid'
            WHEN "PaidToDate">0                        THEN 'part paid'
            ELSE 'other' END K,
       COUNT(*) N, SUM("DocTotal") TOT
FROM "JIVO_OIL_HANADB"."OPCH"
WHERE "DocDate" >= ADD_DAYS(CURRENT_DATE,-365) AND "CANCELED"='N'
GROUP BY 1;
-- fully paid 4,835 (Rs 292.6 Cr) | nothing paid 2,410 (Rs 122.4 Cr) | part paid 135

-- the GRNI balance: goods we have, bills we do not
SELECT SUM("Debit")-SUM("Credit") NET_BALANCE, COUNT(*) LINES
FROM "JIVO_OIL_HANADB"."JDT1" WHERE "Account"='2140001';
-- -7,16,71,876 (credit) over 8,048 lines

-- receipts still unbilled
SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OPDN"
WHERE "DocStatus"='O' AND "CANCELED"='N';
-- 370
```

Chain shares and timings come from `_data/flow-*.md`; the per-desk counts from
`acc/INVENTORY.md` (mined 2026-08-23).
