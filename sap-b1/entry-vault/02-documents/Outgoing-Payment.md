---
type: document
sap_tables: [OVPM, VPM1, VPM2, VPM3, VPM4, VPM6]
objtype: 46
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Outgoing Payment — paying a vendor, and the separate job of saying what it paid

> 19,063 payments across the three books. **Two thirds of them settle nothing specific at
> the time.** "Pay the vendor" and "which bills did that pay" are two different keying jobs
> here, and only the first one has an owner.

## At a glance

| | |
|---|---|
| SAP tables | `OVPM` header · `VPM2` applied documents · `VPM4` GL lines · `VPM3` (76 rows) · `VPM1`, `VPM6` **empty** |
| ObjType / TransType | **46** |
| Volume | Oil 14,851 · Mart 2,294 · Bev 1,925 · **19,070** |
| Last 120 days | Oil 2,307 · Mart 533 · Bev 252 |
| Who keys it | Highly concentrated — Taran keys 1,492 of 2,358 in 90 days |
| Drafted first? | Own table — [[Payment-Draft]] (`OPDF`), 1,788 rows |
| Needs approval? | Rarely — `WddStatus` is `-` on 13,540 of 14,851; only 1,311 go through approval |
| Branch | Oil is **DELHI-first** (`BPLId` 1 ×9,062) unlike every purchasing document, which is FACTORY-first |

## Three kinds, and `DocType` tells you which

| `DocType` | Oil count | Pays | `CardCode` |
|---|---:|---|---|
| **`S`** | 9,705 | A **supplier** (vendor) | always present |
| **`A`** | 5,061 | Straight to a **GL account** | present on 5,059 — so a GL payment still carries a party |
| **`C`** | 85 | A **customer** (a refund) | always present |

`DocType` `A` is a third of all payments. Those are the ones with no invoice behind them by
construction — salary, statutory dues, bank charges — and they land in `VPM4`, not `VPM2`.

## The two thirds problem

Oil, 365 days, cancelled excluded:

| | Payments | Share |
|---|---:|---:|
| **On-account — settles nothing** | **4,050** | **58.4%** |
| Settles exactly 1 document | 1,920 | 27.7% |
| Settles 2–5 | 845 | 12.2% |
| Settles 6+ | 144 | 2.1% |

So the money moves first and the matching happens later, through 49,840
[[Internal-Reconciliation]] rows — **86% of them created automatically by SAP** when a
payment is applied, the rest by a person in the reconciliation screen. That is why
`DocStatus = 'O'` on an invoice does not mean unpaid — **(C-0019)** — and why "has this bill
been paid?" is answered from `OCRD."Balance"` and `ITR1`, not from the document.

## `VPM2` — both key columns are misnamed, and this will cost you a day

This is the single most dangerous thing in the note.

| Column | Its name suggests | What it **actually holds** |
|---|---|---|
| `VPM2."DocNum"` | the payment's document number | **the payment's `DocEntry`** |
| `VPM2."DocEntry"` | the row's own key | **the settled document's `DocEntry`** |

Measured, not guessed:

```
VPM2 joined to OVPM on H."DocEntry" = L."DocNum"  ->  11,856 rows
VPM2 joined to OVPM on H."DocNum"   = L."DocNum"  ->          0 rows
```

**Zero.** A join written on the obvious reading returns nothing at all — which is at least
loud. The dangerous half is the second column: `VPM2."DocEntry"` joined to `OPCH."DocEntry"`
matches **8,503 of 8,503** `InvType` 18 rows, while joining `InvoiceId` matches **6**. So
`InvoiceId` is *not* the invoice link either, despite the name.

The correct join, for the record:

```sql
-- which documents did payment <DocEntry> settle?
SELECT L."InvType", L."DocEntry" AS SETTLED_DOCENTRY, L."SumApplied"
FROM "JIVO_OIL_HANADB"."VPM2" L
WHERE L."DocNum" = <the payment's DocEntry>;
```

*(This confirms and pins down a memory note dated 2026-08-23 that said "VPM2 keys are
backwards" — now with the exact columns and the row counts.)*

## What a payment actually settles — and it is not just invoices

`VPM2."InvType"`, Oil, all history:

| `InvType` | Document | Rows | Applied ₹ |
|---:|---|---:|---:|
| 18 | [[AP-Invoice]] | 8,503 | 241.09 Cr |
| **30** | **[[Journal-Entry]]** | **2,189** | 1.07 Cr |
| 46 | Another outgoing payment | 779 | **−41.76 Cr** (negative — see below) |
| 19 | [[AP-Credit-Memo]] | 169 | 0.58 Cr |
| 24 | [[Incoming-Payment]] | 109 | 5.95 Cr |
| 13 | [[AR-Invoice]] | 80 | 4.12 Cr |
| 14 | [[AR-Credit-Memo]] | 27 | 0.42 Cr |

Two things worth reading twice:

1. **2,189 payments settle a manual journal entry, not an invoice.** This is the mechanism
   behind C-0019 — an invoice cleared by a journal, with the payment applied to the journal,
   leaves the invoice looking open forever. If you are chasing "unpaid" bills, these are the
   false positives.
2. **779 rows are negative and point at another payment**, totalling −₹41.76 Cr. *Inferred,
   not confirmed:* this is most likely the **on-account clearing** mechanism rather than
   error reversal — when an unapplied payment is later applied, SAP appears to write a
   negative row against the original payment and a positive one against the document. The
   same pattern is far larger on the receipt side (−₹616 Cr against `InvType` 24, 93% of the
   positive value), which is what makes clearing the better explanation than error. Either
   way the arithmetic conclusion holds: **any sum over `SumApplied` that ignores the negative
   rows is overstated** — by ₹41.76 Cr in Oil payments alone. → [[Incoming-Payment]]

## Where the money leaves from

`TrsfrAcct` — 25 accounts, and 99.6% of payments are bank transfer:

| Account | Payments |
|---|---:|
| `1104107` | 6,157 |
| `1104104` | 2,449 |
| `2201102` | 2,200 |
| `2201101` | 2,182 |
| `1104106` | 750 |
| `3200003` | 425 |
| …19 more | |

`CashAcct` is populated on **14 payments out of 14,851** — cash payment is essentially
extinct on the vendor side (unlike receipts, where `acc/INVENTORY.md` counts 657 cash
receipts in 90 days). → [[Payment-Terms-and-Banks]]

## Field names — payments are renamed, and a wrong name writes nothing

Payments do **not** use the document property names. Derived from
`VendorPayments`/`OVPM` and `IncomingPayments`/`ORCT`:

| The concept | On a document | On a **payment** | HANA |
|---|---|---|---|
| Free text | `Comments` | **`Remarks`** | `Comments` |
| Journal memo | `JournalMemo` | **`JournalRemarks`** | `JrnlMemo` |
| Branch | `BPL_IDAssignedToInvoice` | **`BPLID`** | `BPLId` |
| Control account | `ControlAccount` → `CtlAccount` | `ControlAccount` → **`BpAct`** | different column |
| Currency | → `DocCur` | → **`DocCurr`** | one letter apart |
| Transfer account | — | `TransferAccount` → `TrsfrAcct` | |

**A payment written with `Comments` instead of `Remarks` sets nothing, and SAP does not
complain.** → [[Field-Name-Rosetta]]

## The journal it posts

TransType 46. Oil, 365 days: 15,782 journals. Characteristic shape:

- **Dr** the vendor control account (`BpAct`) — reducing what we owe
- **Cr** the bank account (`TrsfrAcct`)

For a `DocType` `A` payment there is no vendor leg — it debits the GL account named in
`VPM4` directly.

**TDS at payment:** `OVPM` has no `WTSum` column at all, so withholding is not represented
on the payment header the way it is on an invoice. That is consistent with a memory note
saying TDS is mostly *not* withheld at payment time — but the absence of the column means
the memory's claim cannot be checked this way. **Open question**, below. → [[TDS-Withholding]]

## Before you start

- [ ] **Which book.** Series are book-local (24 values in Oil).
- [ ] **`DocType`** — vendor (`S`), GL account (`A`), or customer refund (`C`)?
- [ ] **Which bank account** the money leaves from (`TrsfrAcct`).
- [ ] **Are you applying it to specific documents?** If yes you need their `DocEntry`s and
      the amount per document. If no, it is on-account and someone matches it later — which
      is the norm, but it is a decision, not a default.
- [ ] **Branch** — note that payments skew DELHI, not FACTORY.
- [ ] **Series** for (payment, branch, month) → [[Numbering-Series]].
- [ ] Use `Remarks`, **not** `Comments`.

## Traps

1. **`VPM2."DocNum"` is the payment's `DocEntry`; `VPM2."DocEntry"` is the settled
   document's.** Both names are wrong. `InvoiceId` is not the invoice. **This is systematic,
   not a one-off** — `RCT2` on the receipt side behaves identically (19,514 rows join on
   `DocEntry`, 0 on `DocNum`). Assume every SAP payment-application table is named this way
   and verify with a count before trusting a join.
2. **58% of payments settle nothing** — an unapplied payment is normal here, not an error.
3. **A payment can settle a journal entry** (2,189 of them). This is why an invoice can be
   paid and still look open. **(C-0019)**
4. **779 `VPM2` rows are negative reversals** pointing at other payments. Sum with care.
5. **Payments use different property names from documents** — and a wrong one is silently
   ignored on write.
6. **`Canceled` on payment tables has one `l`** in HANA while the API spells it `Cancelled`.
   And it is three-valued. **(C-0021)**
7. **`VPM1` and `VPM6` are empty** — 0 rows. Don't look for cheque data there; `VPM3` has 76
   rows and is the only other populated line table. Same on the receipt side: `RCT1`, `RCT3`
   and `RCT5` are all empty, only `RCT2` (19,514) and `RCT4` (2,176) carry anything.
8. **Approval barely applies** — 91% of payments never enter a workflow, unlike A/P invoices
   where it is universal. Do not assume a payment will be reviewed.

## Open questions

1. **Is TDS ever deducted at payment?** `OVPM` has no `WTSum` column, so the invoice-side
   method does not transfer. Find where payment-side withholding would live (a `VPM…`
   table? `OWHT` linkage?) or establish that it never happens here.
2. What is `VPM3` (76 rows)? Cheque detail is the obvious guess; unverified.
3. What is `InvoiceId` for, given it matches an invoice on only 6 of 8,503 rows?
4. ~~Who performs the 49,840 internal reconciliations?~~ **Answered 2026-08-24:** 86% are
   automatic (`IsSystem` = `Y`), 14% are people in the reconciliation screen with names
   attached. → [[Internal-Reconciliation]]
5. Why are payments DELHI-first (9,062 of 14,851) when purchasing is FACTORY-first? Probably
   because the bank accounts sit at the Delhi branch — unverified.
6. Can `sapb1 draft payment` reach all three `DocType`s, or only vendor payments?
   → [[Payment-Draft]]

## Queries used

```sql
-- the join everyone gets wrong
SELECT (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."VPM2" L
          JOIN "JIVO_OIL_HANADB"."OVPM" H ON H."DocEntry"=L."DocNum") AS JOIN_ON_DOCENTRY,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."VPM2" L
          JOIN "JIVO_OIL_HANADB"."OVPM" H ON H."DocNum"=L."DocNum")   AS JOIN_ON_DOCNUM
FROM DUMMY;
-- 11,856 / 0

-- and the second misnamed column
SELECT (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."VPM2" L
          JOIN "JIVO_OIL_HANADB"."OPCH" I ON I."DocEntry"=L."DocEntry"
        WHERE L."InvType"=18) AS DOCENTRY_TO_OPCH,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."VPM2" L
          JOIN "JIVO_OIL_HANADB"."OPCH" I ON I."DocEntry"=L."InvoiceId"
        WHERE L."InvType"=18) AS INVOICEID_TO_OPCH
FROM DUMMY;
-- 8,503 / 6

-- what payments actually settle
SELECT "InvType", COUNT(*) N, ROUND(SUM("SumApplied"),0) APPLIED
FROM "JIVO_OIL_HANADB"."VPM2" GROUP BY "InvType" ORDER BY N DESC;

-- on-account share
SELECT CASE WHEN X."N" IS NULL THEN 'on-account' WHEN X."N"=1 THEN '1 doc'
            WHEN X."N"<=5 THEN '2-5' ELSE '6+' END K, COUNT(*) PAYMENTS
FROM "JIVO_OIL_HANADB"."OVPM" H
LEFT JOIN (SELECT "DocNum" DE, COUNT(*) N FROM "JIVO_OIL_HANADB"."VPM2"
           GROUP BY "DocNum") X ON X."DE"=H."DocEntry"
WHERE H."DocDate" >= ADD_DAYS(CURRENT_DATE,-365) AND H."Canceled"='N'
GROUP BY 1;
-- on-account 4,050 (58.4%) | 1 doc 1,920 | 2-5 845 | 6+ 144
```

Profiles: `_data/profile-OVPM.md`, `profile-VPM2.md`, `profile-VPM4.md`. Name map:
`_data/rosetta-OVPM.md`.
