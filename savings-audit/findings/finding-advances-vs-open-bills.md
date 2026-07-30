---
title: "Advances held against vendors whose bills SAP still shows unpaid — ₹4.05 Cr claim"
created: 2026-07-28
verdict: REFUTED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding]
---

# Advances vs open bills — REFUTED as a ₹4.05 Cr working-capital release

Part of [[SAVINGS-MOC]] · Evidence: [[vendor-money-stuck]]

## Plain-language summary for the CFO

The audit flagged ₹4.05 Cr as "money we can release by matching vendor advances against
the same vendor's unpaid bills in SAP." **The arithmetic is exactly right and the accounting
conclusion is wrong.** Matching an advance against an invoice inside SAP ("Internal
Reconciliation") is a bookkeeping tick — it moves no rupee, changes no bank balance, and does
not even change the vendor's ledger balance, because SAP already counts those "unpaid" invoices
when it computes the balance. We verified this on the four largest names: the sum of every
journal line on the vendor equals the ledger balance to the rupee, and every invoice — open or
closed — is already inside it.

Worse, 99% of the ₹4.05 Cr (₹4.01 Cr) sits with vendors JIVO is actively trading with today,
and 77% of it (₹3.11 Cr) is with just four edible-oil suppliers whose accounts swing between
"they owe us" and "we owe them" every few weeks. DHANLAXMI stood at **minus ₹9,319** on
30-Jun-2026 and at **plus ₹2.13 Cr** on 28-Jul-2026. AWL was ₹45.7 L in credit on 31-May-2026
and ₹1.79 Cr in debit today. That is the ordinary payment float of a business that pays for
oil on or near delivery — not cash stuck anywhere. The lens's own H18 already concluded these
advances equal only 0.19–1.73 months of purchases, i.e. normal for the trade; H15 then counted
the same rupees a second time as releasable working capital.

The "very old unpaid bills" cited as proof (IFFCO TOKIO 30-Sep-2024) are **SAP go-live opening
balances** — 30-Sep-2024 is the first day of data in the system and carries 949 migrated
purchase invoices in Oil alone. They are old because nobody reconciled the migration, not
because anybody is owed money.

What is genuinely stuck, after stripping every live trading relationship, is **₹4.46 lakh** —
and ₹2.70 lakh of that is already claimed by [[finding-dormant-vendor-advances]]. The
incremental bankable amount from this finding is therefore **zero**. The underlying control
point — SAP's "open A/P invoice" report is unusable for payment runs — is real, but it is
already owned by [[finding-ap-subledger-not-reconciled]]; sizing it at ₹4.05 Cr is arbitrary
(the same defect covers ₹292.57 Cr of Oil invoices, not ₹4 Cr).

## Verdict

**REFUTED.** Verified bankable amount: **₹0**. Annual interest saved at 7.3%: **₹0** (no cash
is released, so there is no borrowing to retire).

Reclassified from *working-capital-release* to *control-observation*, subsumed by
[[finding-ap-subledger-not-reconciled]].

## Re-derivation and the four tests that killed it

### 0. The number replicates exactly — this is not an arithmetic error

```sql
WITH op AS (SELECT "CardCode", SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE
  FROM <SCHEMA>.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O'
    AND ("DocTotal"-IFNULL("PaidToDate",0))>0 GROUP BY "CardCode")
SELECT COUNT(*), SUM(CASE WHEN c."Balance"<op.DUE THEN c."Balance" ELSE op.DUE END)
FROM <SCHEMA>.OCRD c JOIN op ON op."CardCode"=c."CardCode"
LEFT JOIN <SCHEMA>.OCRG g ON g."GroupCode"=c."GroupCode"
WHERE c."CardType"='S' AND c."Balance">0 AND IFNULL(g."GroupName",'')<>'FIXED ASSETS';
```

Oil ₹3,68,21,595.82 (81) · Mart ₹33,13,209.22 (15) · Bev ₹3,83,332 (11) = **₹4,05,18,137** ✓.

### 1. The ledger balance already nets the "open" invoices → reconciliation releases ₹0

```sql
SELECT j."ShortName", SUM(IFNULL(j."Debit",0))-SUM(IFNULL(j."Credit",0)) AS NET
FROM JIVO_OIL_HANADB.JDT1 j
WHERE j."ShortName" IN ('VENDA000224','VENDA000614','VENDA001695','VENDA000930')
GROUP BY j."ShortName";
```

| Vendor | JDT1 net | `OCRD."Balance"` |
|---|---:|---:|
| AWL AGRI (VENDA000224) | 1,79,32,650 | 1,79,32,650 |
| DHANLAXMI (VENDA000614) | 2,12,69,122 | 2,12,69,122 |
| ARORA AGRI (VENDA001695) | 60,85,933 | 60,85,933 |
| VAISHNODEVI (VENDA000930) | 59,58,741 | 59,58,741 |

Identical to the rupee. And AWL's `TransType`=18 (A/P invoice) lines credit **₹40,04,57,150** —
the full 12-month purchase value, open invoices included. `DocStatus`='O' is a *reconciliation*
flag, not a *posting* flag. Ticking the match leaves `Balance` unchanged and the bank untouched.

### 2. The test is near-tautological — it re-states "vendor has a debit balance"

```sql
-- which side of the LEAST() actually binds (Oil, excl. FIXED ASSETS)
```

| Binding term | Vendors | Σ Balance | Σ "open" due |
|---|---:|---:|---:|
| Balance binds (bal ≤ due) | 51 | ₹1.45 Cr | **₹128.93 Cr** |
| Open due binds | 30 | ₹5.09 Cr | ₹2.23 Cr |

For 51 of 81 vendors the answer is simply the debit balance: because ~95% of invoices are never
reconciled, virtually every vendor carries phantom "open" bills (₹128.93 Cr of them against
₹1.45 Cr of balance). The open-invoice condition filters almost nothing, so H15 is a subset of
H1's ₹24.26 Cr debit pool, not an independent finding. It is also padded — BARAL LOGISTICS
(Mart) contributes ₹0 yet counts as one of the "107 vendors"; Beverages includes rows of ₹73,
₹50 and ₹40.

### 3. 77% is live commodity float that oscillates through zero

```sql
SELECT j."ShortName", d.DT, SUM(IFNULL(j."Debit",0))-SUM(IFNULL(j."Credit",0)) AS RUNNING_BAL
FROM JIVO_OIL_HANADB.JDT1 j CROSS JOIN <date list> d
WHERE j."ShortName" IN (...) AND j."RefDate"<=TO_DATE(d.DT) GROUP BY j."ShortName", d.DT;
```

| Vendor | 30-Sep-25 | 31-Dec-25 | 31-Mar-26 | 31-May-26 | 30-Jun-26 | 28-Jul-26 |
|---|---:|---:|---:|---:|---:|---:|
| AWL AGRI | 1,751 | 54.3 L | 99.9 L | **−45.7 L** | 2.0 L | 1.79 Cr |
| DHANLAXMI | 0 | −1 | −2 | 69.5 L | **−9,319** | 2.13 Cr |
| ARORA AGRI | — | — | — | 1.10 Cr | **−58.8 L** | 60.9 L |
| VAISHNODEVI | 84.3 L | **−97.8 L** | 1.25 Cr | 65.2 L | 43.3 L | 59.6 L |

These four supply ₹40.0 Cr / ₹14.8 Cr / ₹10.2 Cr / ₹36.7 Cr a year and last invoiced JIVO on
20–23 Jul 2026. The whole PURCHASE-OIL debit pool ranged ₹95 L → ₹9.21 Cr over the last twelve
months. Nothing here is stuck; it is settlement timing. By vendor group the Oil ₹3.68 Cr is
**PURCHASE OIL ₹3.14 Cr (85%)**, SERVICE ₹34.1 L, STAFF VENDOR (imprest) ₹7.5 L,
TRANSPORTER ₹7.4 L, PURCHASE ₹3.7 L, other ₹1.3 L.

### 4. Strip live relationships and only ₹4.46 lakh survives

Dormant = no purchase invoice in 6 months **and** no payment in 3 months:

| Company | Active relationship | Genuinely dormant |
|---|---:|---:|
| Oil | ₹3,66,51,006 (67) | ₹1,70,589 (14) |
| Mart | ₹30,53,623 (11) | ₹2,59,585 (4) |
| Beverages | ₹3,67,977 (9) | ₹15,355 (2) |
| **Total** | **₹4,00,72,606 (99%)** | **₹4,45,529 (1%)** |

Largest dormant item in Oil is OM LOGISTICS LTD ₹1,21,321; everything else is under ₹10,076,
including two rows of ₹1 and one of ₹0. Two Oil rows (RAKESH KUMAR CONTRACTOR **BKHR**
₹10,076, POOJA W/O GURPREET SINGH **BKHPR** ₹1,317) are Bakharpur land-assembly counterparties —
deliberate capex spend, not recoverable money.

### 5. The "22-month-old unpaid bill" is a migration artifact

```sql
SELECT MIN("DocDate"), COUNT(*), SUM(CASE WHEN "DocDate"=TO_DATE('2024-09-30') THEN 1 ELSE 0 END)
FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N';
-- 2024-09-30 | 15,707 | 949
```

30-Sep-2024 is SAP go-live. The IFFCO TOKIO (₹3,50,371) and AL GHURAIR ("₹93.70 Cr open")
items dated that day are unreconciled opening balances, not aged payables.

### 6. No evidence the double-payment ever happened

If A/P actually paid from the open-invoice report, vendor debit balances would compound. They do
not — they cross zero repeatedly (test 3). A same-vendor/same-amount repeat-payment scan on this
vendor set returns only recurring standard consignment values (AWL ₹57,90,480 paid on many
dates = identical tanker loads), with the account squaring off each cycle.

## Overlaps — state these before adding any of it to a total

- **[[finding-ap-subledger-not-reconciled]]** — same root cause (`ODPO`/`ODPI` unused, so every
  advance is an unreconciled on-account payment). This finding was presented as its "quantified
  cash consequence"; it is not cash. **Do not add the two.**
- **[[finding-dormant-vendor-advances]]** — ₹2,70,253 of the ₹4,45,529 dormant residual is the
  same rupees (GODAMWALE ₹1,92,543 · AJANTA SOYA ₹62,428 · BONUS PAYABLE ₹15,282).
- **[[finding-cross-company-vendor-netting]]** — ~₹27.3 L of the active pool is the same debit
  side already counted there (UHBVN ₹17,89,687 · ARNAV ₹3,89,688 · BHUPINDER ₹2,86,885 ·
  ARVINDER ₹1,40,576 · MEDIA MIND ₹1,26,553).
- **No overlap** with [[finding-hs-filling-advance]] or
  [[finding-alo-logistics-unrecovered-claims]] — both counterparties have **zero** open purchase
  invoices, so neither enters this pool. Those two remain independently claimable.
- **No overlap** with [[finding-stale-security-deposits]] (GL 1107xx accounts, not BP balances)
  or [[finding-mangla-related-party-advances]] (FIXED ASSETS group excluded by construction).

## Action

1. **Owner: CFO** — remove ₹4.05 Cr from the savings total. It is not releasable cash; carrying
   it overstates the programme and would be indefensible in a review.
2. **Owner: Accounts (A/P)** — keep the operating instruction, drop the number: never build a
   payment run from SAP's open-A/P-invoice report; pay only against the vendor ledger balance
   (`OCRD."Balance"`) or a signed vendor statement. This is prevention of a hypothetical error,
   with no rupee value until an error occurs.
3. **Owner: Accounts (A/P)** — run monthly Internal Reconciliation per vendor anyway. Justify it
   as data hygiene and audit readiness (it makes ageing reports usable), **not** as a cash
   release. Prioritise the 2024-09-30 go-live migration block.
4. **Owner: Purchase head** — the only live question worth asking is a commercial one and belongs
   elsewhere: can the PURCHASE-OIL advance float (12-month trough ₹95 L, today ₹5.17 Cr) be run
   nearer its trough by shifting to on-delivery payment? That is an advance-policy negotiation,
   not a reconciliation task, and must not be booked under this finding.
