---
type: operator-profile
subject: TARAN (USER05) — Accounts007@jivo.in
sap_tables: [OVPM, ORCT, OJDT, OITR]
companies: [OIL, BEV]
mined: 2026-08-25
window: FY26-27, DocDate >= 2026-04-01
confidence: high
readonly: true
---

# Operator profile — TARAN, SAP login `USER05`

> **Nothing in this note was produced by writing to SAP.** Every figure is a live
> read via `hana-sql`, measured 2026-08-25. Figures are labelled MEASURED or INFERRED.
>
> Purpose: a specification complete enough to build an agent that does this job.

## The one-line answer

Taran is JIVO's payments desk. He moves **₹201.80 Cr out of Oil across 2,013 bank
transfers** in under five months, and he does it **one document at a time, by hand,
at a median of 3 minutes 46 seconds each**.

## 1. Identity

`USER05` resolves to `USERID` **14 in all three books** (unusual — it normally differs).

| Book | Display name | Mailbox |
|---|---|---|
| Oil | TARAN | Accounts007@jivo.in |
| Beverages | TARAN | accounts007@jivo.in |
| Mart | **TARAN/ KARNAIL** | Accounts007@jivo.in |

**MEASURED:** `USER05` has **zero** documents of any type in Mart this FY (OVPM 0,
ORCT 0). So the shared "TARAN/ KARNAIL" login is dormant in Mart, and no Mart figure
is at risk of misattribution. The shared-login ambiguity is real but currently costs nothing.

A rival candidate exists — Mart `USER15` is literally named "TARANDEEP SINGH"
(`ppc.ho@jivo.in`) — but that is a production-planning login, not accounts.
**Verdict: the payments person is `USER05`.** Confidence ~90%; what would settle
the last 10% is confirming that Accounts007@jivo.in belongs to Tarandeep Singh
(HR record `JWPL2639` / `JWPL0346`, department JIVO_ACCOUNTS).

## 2. What his job actually is

Swept every object table for `UserSign=14` in Oil (all time):

| Table | Count | What it is |
|---|---:|---|
| OVPM | 11,736 | Outgoing payments |
| OJDT | 14,095 | Journal entries |
| OITR | 3,994 | Internal reconciliations |
| ORCT | 2,144 | Receipts |
| OPCH / OINV / OPDN / ODLN / ODRF | **0** | Invoices, receipts of goods, drafts |

**The critical simplification:** all 14,095 journal entries are `TransType` 46 (outgoing
payment) and 24 (incoming payment) — the *automatic* ledger effect of his own payments.
**He posts zero manual journal entries.** There is no free-form accounting judgement
in this job to reproduce.

His job is exactly three things: pay vendors, receive money, reconcile.

## 3. Volume — FY26-27

| Book | Stream | Docs | Value |
|---|---|---:|---:|
| Oil | Outgoing payments | 2,013 | **₹201.80 Cr** |
| Beverages | Outgoing payments | 272 | ₹8.17 Cr |
| Oil | Receipts | 205 | ₹41.48 Cr |
| Beverages | Receipts | 333 | ₹2.88 Cr |
| Mart | anything | 0 | — |

## 4. THE FORMAT — what literally goes in each box

Oil OVPM, his 2,013 live documents. Fill rate = % of his documents where the field is
populated.

| Field | Fill | Modal value | Source |
|---|---:|---|---|
| `CardCode` | 100% | 547 distinct parties | **decided** |
| `TrsfrSum` | **100%** | — | **decided** |
| `CashSum` / `CheckSum` / `CreditSum` | **0%** | never | — |
| `TrsfrAcct` | 100% | `1104107` (1,355 = 67%) | **decided** |
| `U_Pymnt_Mode` | 100% | NEFT 1,413 / RTGS 596 / FT 4 | **decided** |
| `Ref1` | 100% | = `DocNum` | **sap-default** (see §6) |
| `Comments` | 99.1% | hand-typed sentence | **decided** |
| `U_Type_of_Advance` | 92.7% | "One Time Settlement" | **decided** |
| `U_URGENCY` | 21.0% | mostly null | decided, optional |
| `CounterRef` | 2.7% | rarely | ignored |
| `Ref2` | 2.7% | rarely | ignored |
| **`TrsfrRef`** | **0%** | **never filled** | — |
| `JrnlMemo` | 100% | `Outgoing Payments - <CardCode>` | **sap-default** |

**`DocType`:** `S` supplier 1,684 (84%) · `A` GL account 318 (16%) · `C` customer 11.
**`Series`:** five in use — 2596, 2597, 2598, 2599, 2600 — one per month
(Apr→Aug), shared across branches. Confirms correction **C-0018**: payment series are
*monthly*, unlike the per-branch A/P invoice series.
**`BPLId`:** branch 2 (1,012) and branch 1 (945), roughly even; 5/6/4 negligible.

### The two fields that matter most

**`TrsfrRef` is never filled — 0 of 2,013.** That is the bank's own transaction
reference. It means **the bank UTR never enters SAP**, so no payment in Oil can be
automatically tied back to a bank statement line. Every bank reconciliation is therefore
manual or matched on amount alone.

**`Comments` is hand-typed, and the typos prove it.** Real values:

```
BEING PAYMENT PAID TO ARVINDER SINGH IMPREST JWPL0115
BEING PAYMENT PAID AWL AGRI BUSINESS LIMITED
eing payment paid to INDIAN BANK CC A/C 7007270527
BEING PAYMENT [AID TO VAISHNODEVI REFOILS & SOLVEX PRIVATE LIMITED
```

The template is `BEING PAYMENT PAID TO <party> <role/imprest code>`. The dropped
letters, the stray bracket and the lowercase run are keystroke errors. A machine
writing this field would be strictly more consistent than the status quo.

## 5. Rhythm and speed

`CreateTS` is HHMMSS (verified: min 103947, max 204259).

| | MEASURED |
|---|---|
| Active days | 123 |
| Documents per active day | 16.4 (largest burst 50, on 2026-05-22) |
| Working window | 10:39 to 20:42 |
| Peak hour | 16:00 (599 docs) |
| After 19:00 | 56 documents |
| Median gap, all consecutive docs | 308.5 s |
| **Median gap in-burst (≤30 min)** | **226 s = 3 min 46 s per payment** |
| Total in-burst keying time | **169.6 hours** |
| First-to-last span across 123 days | 649.3 h (avg 5 h 17 m/day at the desk) |
| Posting lag (`DocDate`→`CreateDate`) | median **0 days**; 1,751/2,013 (87%) same-day |

**INFERRED:** 169.6 h over ~5 months on *Oil outgoing payments alone* extrapolates to
**~408 hours/year**. Adding Beverages payments and both receipt streams puts the whole
desk near **~500 hours/year ≈ three months of full-time work**.

He is not back-dating batches — 87% same-day means he keys payments as they happen.

## 6. `Ref1` — CORRECTED: it is SAP's own DocNum, not an external register

> **This section previously claimed `Ref1` was a JIVO-side voucher register living
> outside SAP, and called it "the single most important finding for automation."
> That was WRONG.** Verified 2026-08-25:

```
TOT   REF1_EQ_DOCNUM
2016  2016
```

`TO_VARCHAR("DocNum") = "Ref1"` for **every one of the 2,016 documents**. `Ref1` is the
SAP document number copied into the reference field by the numbering series. It is a
**`sap-default`, not a decided field**, and it costs the operator nothing.

The 9-digit serial advancing across bank accounts and dates is simply SAP's own
per-book payment numbering — exactly as expected once you know payment series are
monthly and shared across branches (C-0018).

**Consequence: there is no missing input document, and no hidden work queue.** The
blocker this note previously named does not exist. Automation feasibility goes UP.

## 7. THE ON-ACCOUNT PROBLEM

| | Docs | Value |
|---|---:|---:|
| **On-account** (`NoDocSum` > 0, no invoice matched) | 923 (46%) | **₹175.97 Cr — 87%** |
| Applied to specific A/P invoices | 1,090 (54%) | ₹25.83 Cr — 13% |

**87% of the money Taran pays out is never matched to an invoice.** This is correction
**C-0019** at full scale, and it has two consequences:

1. Oil's vendor open-item ageing is effectively fiction. Age from `OCRD.Balance`, never
   from open documents.
2. **An automation cannot lean on invoice matching for the big money.** The dominant
   flow is "pay this party this amount", authorised by something outside SAP.

Beverages behaves differently: 92 of 272 on-account (34%).

## 8. Counterparties

547 distinct parties. Top by value:

| CardCode | Name | n | Value |
|---|---|---:|---:|
| VENDA000224 | AWL AGRI BUSINESS LIMITED | 77 | ₹47.08 Cr |
| VENDA000930 | VAISHNODEVI AGRO RESOURCES | 28 | ₹17.52 Cr |
| VENDA001695 | M/S ARORA AGRI BUSINESS VENTURES | 24 | ₹14.75 Cr |
| VENDA000614 | DHANLAXMI EDIBLES | 20 | ₹14.12 Cr |
| VENDA001603 | **ANJU MANGLA** | 5 | ₹12.79 Cr |

Top 4 vendors = ₹93.47 Cr = **46% of all outflow**. A pipeline covering just those four
counterparties would cover nearly half the money on 149 documents/year.

ANJU MANGLA (₹12.79 Cr on 5 payments) is the fixed-asset advance line flagged in the
July savings audit — noted here for continuity, not re-verified.

## 9. Error rate

90 cancelled against 2,013 live = **4.3%**. That is the human baseline any bot must beat.

## 10. Other streams

- **Beverages payments:** 271 of 272 bank transfer (99.6%), 1 cash. Same shape as Oil.
- **Oil receipts:** 190 of 205 transfer, **15 cash**. The only cash he touches.

## 11. Clone feasibility

**The mechanics are almost fully determined.** Payment means is 100% predictable
(bank transfer). Series follows from the month. `JrnlMemo` is SAP's. `Comments` is a
template. `U_Pymnt_Mode` is NEFT/RTGS, and RTGS is India-standard above ₹2 L — a rule
that can be tested against the data. `TrsfrRef` and `CounterRef` are left blank and can
stay blank.

**What the data does NOT explain — the real gaps:**

1. **Who to pay today, and how much.** The `Ref1` register decides this and it is not
   in SAP. This is the whole input.
2. **Which bank account** to pay from (`TrsfrAcct`, 7 in use). Likely a balance/liquidity
   call — no field records the reasoning.
3. **On-account vs applied** — the 46/54 split. What makes a payment on-account?
4. **`U_Type_of_Advance`** = "One Time Settlement" on 92.7%. What are the other 7.3%?
5. **`U_URGENCY`** on 21%. What triggers it?

**Verdict: ~70% clonable today, ~95% once the `Ref1` register is in hand.** The blocker
is not SAP and not the CLI — it is one input document nobody has shown us yet.

## 12. The seam is already built

**`sapb1 draft payment outgoing` already exists and is proven.** It POSTs to
`PaymentDrafts` (OPDF), and has created live drafts — DocEntry 2144–2152 in Oil on
2026-08-24, all `bopot_OutgoingPayments`, HTTP 201.

The CLI **cannot** post a payment draft: `SaveDraftToDocument` is Drafts-only and the
path is a compile-time constant, so `PaymentDrafts(N)/SaveDraftToDocument` is
unspellable, not merely refused. A human must open **SAP B1 → Banking → Payment Drafts**
and press Add.

**That press is exactly the "last judgement" seam.** It already exists, it is enforced
by the code, and it needs nothing built.

> ⚠️ **One live risk worth naming:** `sapb1 post VendorPayments --yes` would create a
> **real outgoing payment** — money out, no draft, and the CLI cannot cancel or delete it.
> Only the confirm prompt stands in the way. Any automation must be hard-wired to
> `draft payment`, never `post VendorPayments`.

## What is still needed from a human

1. **The `Ref1` register** — a photo or export. Without it there is no trigger.
2. **The bank-account rule** — how he picks among 7 `TrsfrAcct` codes.
3. **The on-account rule** — when a payment is deliberately left unapplied.
4. **30 minutes of shadowing**, specifically the steps *before* SAP.
5. **Who authorises** a payment before he keys it, and whether that authority is written down.
