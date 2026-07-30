---
title: "Open A/P credit notes + duplicate vendor bills — ₹12.15 L claimed, ₹4.73 L bankable"
created: 2026-07-29
verdict: REVISED
amount_verified_inr: 472632
amount_claimed_inr: 1215021
kind: one-time-recovery
company: ALL
lens: duplicate-payments
ranks: [64, 66]
tags: [savings-audit, finding]
---

# Open A/P credit notes (rank 64) + duplicate vendor bills (rank 66) — REVISED

**Claimed:** ₹7,03,989 (open A/P credit notes, all companies) + ₹5,11,032 (bills booked twice, Oil) = **₹12,15,021**.
**Re-derived bankable:** **₹4,72,632** (₹4.73 lakh) — 38.9% of the claim.
**Interest overlay at the measured 8.25% CC rate:** ₹38,992 a year *(an overlay on the ₹4.73 L, never additive money).*

Part of [[SAVINGS-MOC]] · Evidence: [[duplicate-payments]]

---

## Plain-language summary for the CFO

Two small "money we already lost" findings were bundled here. Both populations are real — I reproduced
every rupee of both with my own, differently-shaped queries. What does not survive is **what those
documents actually are** once you open each one and read the goods, the dates and the payment trail.

| Component | Claimed | Bankable | What happened |
|---|---:|---:|---|
| Open A/P credit notes never set off (rank 64) | 7,03,989 | **1,31,678** | 81% is either a bookkeeping artifact or sits on vendors whose account is already at exactly zero |
| Vendor bills booked twice (rank 66) | 5,11,032 | **3,40,954** | The one "paid twice" case is two real truckloads; the two unpaid ones are genuine and still stoppable |
| **Total** | **12,15,021** | **4,72,632** | |

**The single biggest item in the bundle — Bee Hive Farms ₹4,05,317 — is not money.** JIVO has **never
paid Bee Hive Farms a single rupee**, in any of the three companies (zero outgoing-payment rows on the
account, and the Mart and Beverages cards are both at ₹0). The ₹4.05 L "debit" was created when one
vendor bill, `BHF/TI/1616`, was migrated into SAP at go-live as a ₹2,07,880 payable and then a goods
return of the *same* bill was raised at ₹6,37,326 of stock value and converted into an A/P credit memo.
The credit memo credits **GRNI (Goods Received But Not Invoiced)** — the honey had never been invoiced
to JIVO, so returning it cost JIVO nothing and creates no claim. You cannot collect a refund of money
you never paid.

**The one case flagged as an actual double payment — Raj Technopack ₹1,70,078 — is two genuine
deliveries.** Both documents carry bill number `SNP-0002/25-26` and both are ₹1,70,078 to the rupee,
which is why the sweep caught them. But open the lines and they are different goods, on different
purchase orders, received on different days at different gate entries, and paid by two different
payments five months apart:

| Doc | Date | Goods | PO / Gate entry | Paid by |
|---|---|---|---|---|
| 625034446 | 2025-03-31 | CAPS 5 LTR **GREEN** 4,480 + HDPE BOTTLE 5 LTR 4,480 | PO 1124226525 · GRPO 325207006 · Gate 309 | 525466738, 2025-05-16 |
| 625094331 | 2025-09-01 | CAPS 5 LTR **ORANGE** 4,480 + HDPE BOTTLE 5 LTR 4,480 | PO 325226636 · GRPO 2025046501 · Gate 5 | 1025466793, 2025-10-16 |

Identical value because the pack is identical (4,480 five-litre bottles plus caps); only the cap colour
differs. Raj Technopack simply re-used a bill number. **No rupee was paid twice.**

**What is genuinely there, and worth doing this week, is ₹4.73 lakh** — ₹1.32 L of small balances
sitting with suppliers who owe it back, and ₹3.41 L of duplicated bills that have **not been paid yet**
and can still be stopped.

**One correction to the framing that matters more than the number.** The rank-66 finding described
₹1.70 L as "already paid twice, go and recover it". After re-derivation, **none of the ₹3.41 L that
survives has left the bank.** Every one of the three vendors shows JIVO has *under*-disbursed, not
over-disbursed: Raj Technopack holds ₹30,92,631 of JIVO's credit, Octavos ₹8,49,126, and Reliance Retail
C&C's account is ₹1,12,896 in JIVO's favour. So this is **cost avoidance, realised by withholding the
duplicate from the next settlement** — easier and more certain than chasing a refund, but it must be
done *before* the next payment run or it converts into a real loss.

---

## Verdict: REVISED — ₹4,72,632 bankable

- **Rank 64 (open A/P credit notes): REVISED** — ₹7,03,989 → **₹1,31,678** (18.7%).
- **Rank 66 (duplicate bills): REVISED** — ₹5,11,032 → **₹3,40,954** (66.7%), and reclassified from
  *recovery* to *avoidance*.

---

## Component 1 — open A/P credit notes never set off (rank 64)

### The population reproduces exactly

```sql
SELECT COUNT(*) AS N_NOTES,
       TO_DECIMAL(SUM(r."DocTotal"-r."PaidToDate"),18,2) AS TOT_OPEN,
       TO_DECIMAL(SUM(CASE WHEN c."Balance">0
                      THEN LEAST(r."DocTotal"-r."PaidToDate", c."Balance") ELSE 0 END),18,2) AS CAPPED_AT_DEBIT,
       TO_DECIMAL(SUM(CASE WHEN c."Balance"<=0
                      THEN r."DocTotal"-r."PaidToDate" ELSE 0 END),18,2) AS ON_CREDIT_VENDORS,
       TO_DECIMAL(SUM(CASE WHEN r."DocDate"='2024-09-30'
                      THEN r."DocTotal"-r."PaidToDate" ELSE 0 END),18,2) AS GOLIVE_MIGRATION
FROM   JIVO_OIL_HANADB.ORPC r JOIN JIVO_OIL_HANADB.OCRD c ON c."CardCode"=r."CardCode"
WHERE  r."CANCELED"='N' AND r."DocStatus"='O';
```

| Company | Notes | Open ₹ | Capped at vendor debit | On credit-balance vendors | Dated 30-Sep-2024 (migration) |
|---|---:|---:|---:|---:|---:|
| Oil | 321 | 27,40,815 | 10,94,618 | 12,46,547 | **4,74,044** |
| Mart | 362 | 15,51,32,074 | 28,479 | 15,50,82,057 | 0 |
| Beverages | 2 | 1,67,560 | 19,800 | 37,760 | 0 |

Matches the sweep to the rupee. **17% of Oil's open notes are dated 30-Sep-2024** — SAP go-live opening
balances, not aged claims. Mart's ₹15.51 Cr is 99.4% the intercompany JIVO WELLNESS account
(VENDA000001, ₹15,40,77,684 open against a ₹2.31 Cr credit balance) and nets to zero at group level;
Oil's JIVO MART card (VENDA000483, ₹34,193) is the same story. Both were correctly excluded.

### Per-name verdicts

| Company | Vendor | Claimed ₹ | Verified ₹ | Verdict and why |
|---|---|---:|---:|---|
| OIL | BEE HIVE FARMS | 4,05,317 | **0** | Zero payments ever, in all 3 companies. Migration invoice, goods return and credit memo all carry the **same** vendor bill ref `BHF/TI/1616`; the memo credits GRNI, so the honey was never invoiced. Artifact. **REFUTED** |
| OIL | OM LOGISTICS LTD | 1,21,321 | **1,21,321** | Net debit on a transporter with no purchase activity since Sep-2025. The three open notes mirror credit notes OM Logistics itself issued ("Debit Note against CN-1349551100005"), so the claim is already agreed. **CONFIRMED** |
| OIL | S M PLAST & CHEMICALS | 35,025 | **0** | Vendor balance is exactly **₹0** (ledger DR ₹4,43,018 = CR ₹4,43,018). A 21-day-old quality-reject return (612 caps + 612 bottles) on a live vendor; it will net in the next run. **REFUTED** |
| OIL | M M OVERSEAS | 23,322 | **0** | Balance exactly **₹0** (DR = CR = ₹28,774). Short-quantity return, already absorbed. **REFUTED** |
| OIL | MIRACLE CONTAINER | 15,941 | **0** | **One ledger line in the entire database**, dated 2024-09-30, line description literally `OPENING BALANCE ACCOUNT`, GL 3200003. Pure go-live migration. **REFUTED** |
| OIL | ARNAV TRANSPORT SERVICE | 15,000 | **0** | A "discount received" note inside a live 238-line account carrying ₹15,11,889 debit *and* ₹3,89,688 of open bills — the exact H6 population already refuted by [[finding-advances-vs-open-bills]]. **REFUTED** |
| OIL | UNMEET SINGH IMPREST | 12,807 | **0** | An employee imprest card, not a supplier; a mobile-bill credit. Account balance is only ₹5,410. Payroll matter. **REFUTED** |
| OIL | INTL CO FOR OILS & AGRI FOOD | 9,086 | **9,086** | Container demurrage recharged to an import supplier; balance is exactly ₹9,085.81 and dormant 14 months. **CONFIRMED** |
| OIL | RELIANCE JIO INFOCOM | 1,047 | **1,047** | Balance exactly ₹1,046.98. Immaterial but real. **CONFIRMED** |
| OIL | FASHNEAR TECHNOLOGIES | 106 | **0** | 2024-09-30, GL 3200003 `OPENING BALANCE ACCOUNT`. Migration. **REFUTED** |
| MART | BARAL LOGISTICS | 21,539 | **0** | Balance **₹0.44**. Squared. **REFUTED** |
| MART | AMAZON SELLER SERVICES | 23,254 | **0** | Standalone fee-reversal notes (technology fee, fixed fee, commission) inside a 498-line marketplace settlement account carrying ₹18.45 L of live float. Not separable cash. **REFUTED** |
| MART | TRUEX LOGISTIC SERVICES | 10,000 | **0** | Balance **₹0** (DR = CR = ₹22,74,512). **REFUTED** |
| MART | VISHWAKARMA TRANSPORT | 9,000 | **0** | Balance **₹0**. **REFUTED** |
| MART | COMMERCIAL TRANSPORT CO | 1,000 | **0** | Balance **₹0**. **REFUTED** |
| MART | OM LOGISTICS LTD | 224 | **224** | Trivial residue. **CONFIRMED** |
| | **Total** | **7,03,989** | **1,31,678** | |

### The logical error that inflated this one

The sweep's rule was *"vendor balance is zero or debit ⇒ we owe them nothing ⇒ the note is real cash."*
The zero-balance half of that rule is backwards. **A vendor balance of exactly ₹0 means the credit note
has already been consumed**, not that cash is waiting. Six of the sixteen names (₹99,886) are at exactly
₹0 with debits equalling credits to the rupee — they are open only because JIVO does not run SAP's
internal reconciliation ([[finding-ap-subledger-not-reconciled]]), which is trap 3, not money.

### The Bee Hive kill in full

```sql
SELECT 'AP-INVOICE' AS KIND, TO_VARCHAR(i."DocNum"), i."DocDate", i."NumAtCard",
       TO_DECIMAL(i."DocTotal",18,2) FROM JIVO_OIL_HANADB.OPCH i WHERE i."CardCode"='VENDA000625'
UNION ALL SELECT 'GOODS-RETURN', TO_VARCHAR(r."DocNum"), r."DocDate", r."NumAtCard",
       TO_DECIMAL(r."DocTotal",18,2) FROM JIVO_OIL_HANADB.ORPD r WHERE r."CardCode"='VENDA000625'
UNION ALL SELECT 'AP-CREDITNOTE', TO_VARCHAR(c."DocNum"), c."DocDate", c."NumAtCard",
       TO_DECIMAL(c."DocTotal",18,2) FROM JIVO_OIL_HANADB.ORPC c WHERE c."CardCode"='VENDA000625'
UNION ALL SELECT 'PAYMENT', TO_VARCHAR(p."DocNum"), p."DocDate", '',
       TO_DECIMAL(p."DocTotal",18,2) FROM JIVO_OIL_HANADB.OVPM p WHERE p."CardCode"='VENDA000625'
ORDER BY 3;
```

| Kind | DocNum | Date | Vendor bill ref | ₹ |
|---|---|---|---|---:|
| AP-INVOICE | 240230066 | 2024-09-30 | **BHF/TI/1616** | 2,07,880 |
| GOODS-RETURN | 1224216504 | 2024-12-27 | **BHF/TI/1616** | 6,37,326 |
| AP-CREDITNOTE | 625015902 | 2025-01-13 | **BHF/TI/1616** | 6,37,326 |
| AP-INVOICE | 626044308 | 2026-04-01 | BHF/TI/1715 | 24,129 |
| PAYMENT | — | — | — | **none, ever** |

One bill, booked as a ₹2.08 L migrated payable and returned at ₹6.37 L of stock value. The credit memo's
four lines (SANO HONEY 500 GMS ×4,990, SANO HONEY 1 KG ×2,369) all post to GL **2140001 GOODS RECEIVED
BUT NOT INVOICED**. Net ₹4,05,317 debit is the gap between a migration opening balance and a
stock-valued return on the same document. Traps 1 and 6 both apply. A second goods return
(2125106502, 2025-10-23, ₹54,578) is still open and was never converted at all — the process is
inconsistent, which is the real control point.

---

## Component 2 — vendor bills booked twice (rank 66)

### Re-derived with a self-join rather than a GROUP BY

```sql
SELECT a."CardCode", a."NumAtCard", a."DocNum", a."DocDate", b."DocNum", b."DocDate",
       TO_DECIMAL(a."DocTotal",18,2), TO_DECIMAL(a."PaidToDate",18,2), TO_DECIMAL(b."PaidToDate",18,2),
       DAYS_BETWEEN(a."DocDate", b."DocDate") AS GAP, TO_DECIMAL(c."Balance",18,2) AS VENDOR_BAL
FROM   JIVO_OIL_HANADB.OPCH a
JOIN   JIVO_OIL_HANADB.OPCH b ON a."CardCode"=b."CardCode"
       AND TRIM(a."NumAtCard")=TRIM(b."NumAtCard") AND a."DocEntry"<b."DocEntry"
JOIN   JIVO_OIL_HANADB.OCRD c ON c."CardCode"=a."CardCode"
WHERE  a."CANCELED"='N' AND b."CANCELED"='N' AND LENGTH(TRIM(a."NumAtCard"))>2
  AND  ABS(a."DocTotal"-b."DocTotal") < 1
ORDER BY a."DocTotal" DESC;
```

Ten live same-vendor / same-ref / same-amount pairs in Oil. **Zero in Mart and Beverages** — the same
self-join over both those schemas returns no rows, confirming the sweep.

| Vendor | Bill ref | Dates | ₹ each | Paid? | Vendor balance | Verdict |
|---|---|---|---:|---|---:|---|
| RAJ TECHNOPACK | SNP-0002/25-26 | 2025-03-31 / 2025-09-01 | 1,70,078 | both | 30,92,631 **Cr** | **REFUTED** — different goods |
| OCTAVOS ENTERPRISES | DN-00652/2024-25 | 2025-03-19 / 2026-03-31 | 2,59,754 | neither | 8,49,126 **Cr** | **CONFIRMED** |
| RELIANCE RETAIL C&C (×7) | A31G1100005088 etc. | 2025-03-31 / 2026-03-31 | 81,200 total | neither | 1,12,896 **Dr** | **CONFIRMED** |
| BSES RAJDHANI POWER | 100788658441 | 2025-05-23 / 2026-05-23 | 57,080 | first only | 20,620 Cr | **not banked** — see below |

### Raj Technopack — REFUTED

`STRING_AGG` over `PCH1` for both documents shows GREEN caps on one and ORANGE caps on the other, from
different POs and different Goods Receipt POs, paid by two different payments. The control has in fact
worked on this vendor twice — bill refs `RTPL/SNP/001554` and `SNP-0005/25-26` each appear three times
in `OPCH`, and in both cases two of the three are `CANCELED` in ('Y','C'), leaving exactly one live
document. Only `SNP-0002/25-26` has two live copies, and those are two real consignments.

### Octavos ₹2,59,754 — CONFIRMED, and still stoppable

The vendor's normal pattern is that every A/P invoice is moved to the customer ledger by a
"Vendor to Customer transfer" journal within weeks. `DN-00652/2024-25` was booked on 2025-03-19 and never
transferred; then on **2026-03-31** someone booked a year-end catch-up batch of three FY2024-25 bills
(`SI/1217/2024-25` ₹5,80,000, `DN-00551/2024-25` ₹9,372 and `DN-00652/2024-25` ₹2,59,754 again). The
ledger ties out exactly: credits ₹51,34,714 minus debits ₹42,85,588 = the ₹8,49,126 credit balance in
`OCRD`, and the four open invoices total ₹11,08,880 — ₹2,59,754 more than JIVO actually owes.

### Reliance Retail C&C ₹81,200 — CONFIRMED

Seven Reliance invoice numbers (`A31G1100005088`, `A31G1100005605`, `271G1100027499`, `A91G1100013318`,
`A61G1100008800`, `271G1100034040`, `271G1100034039`) were booked on 31-Mar-2025 and identically again on
31-Mar-2026. Every one of the 2025 batch is still `DocStatus='O'` with `PaidToDate=0`, so the 2025 batch
was never cleared before being re-entered. The account is ₹1,12,896 in JIVO's favour, so correcting the
duplicates increases what JIVO nets out of the Reliance reconciliation by ₹81,200.

### BSES ₹57,080 — a pair the original sweep missed, deliberately NOT banked

`100788658441` is the only vendor reference that repeats across ~40 live BSES bills, and both copies are
₹57,080 to the rupee, exactly 365 days apart. That is a duplicate signature. But the two narrations cite
**different bill dates** ("DATE 23-05-2025" vs "DATED 23-05-26") and the 2025 narration also mis-states
the amount as ₹1,57,080 against a ₹57,080 document. It is equally consistent with two genuine monthly
electricity bills whose reference was copy-pasted. It cannot be settled from SAP alone. **₹0 banked;
raised as a check-the-portal item** — and BSES's open bills total ₹4,52,030 against a ₹20,620 credit
balance, so this bill has very likely already been paid on account (trap 3), which is why it matters.

---

## The concrete action

**Owner: Manager – Accounts Payable (Oil), with the Financial Controller signing off before the next payment run.**

1. **Before the next payment cycle — block ₹3,40,954.** Cancel or credit Octavos A/P invoice `726035503`
   (₹2,59,754) and the seven Reliance Retail C&C duplicates dated 31-Mar-2026 (₹81,200). Both vendors
   are in credit to JIVO or in JIVO's favour, so this is a withholding, not a negotiation. **This is
   time-critical: it is avoidance today and a cash loss the day either is paid.**
2. **Send three balance-confirmation letters — ₹1,31,678.** OM Logistics Ltd (₹1,21,321, Oil),
   International Company for Oils & Agri Food (₹9,086), Reliance Jio Infocom (₹1,047). OM Logistics'
   notes mirror credit notes the vendor already issued, so ask for a refund or a set-off against the
   next consignment. *Upside pointer, not claimed here:* OM Logistics also holds **₹3,65,790 debit in
   Mart** — chase both in one letter.
3. **Check two documents against source.** Pull the physical BSES bill for `100788658441` dated
   23-May-2026 (₹57,080) and the second Bee Hive goods return `2125106502` (₹54,578, open since
   Oct-2025 and never converted).
4. **Fix the posting rule that manufactured the Bee Hive number.** A goods return against a bill that
   was never invoiced should stop at the Goods Return; converting it to an A/P credit memo debits the
   vendor for money that was never paid. Add this to the SAP user note.
5. **Turn on `NumAtCard` uniqueness per business partner in SAP** (Document Settings → "Block documents
   with duplicate vendor reference"). Note it must be a *warning with override*, not a hard block —
   Raj Technopack proves suppliers do legitimately re-use bill numbers.
6. **Add to the monthly close checklist:** "open A/P credit notes older than 90 days on vendors with a
   nil or debit balance" — a four-line report, not a project.

---

## Overlaps — which rupees appear more than once

- **Inside this bundle: none.** The two components share no vendor, so ₹1,31,678 + ₹3,40,954 = ₹4,72,632
  is fully deduplicated.
- **Miracle Container ₹15,941** and the excluded **Vijay Industries ₹4,21,402** are both listed in
  [[finding-no-invoice-vendors]] under "open A/P credit notes — real, but = lens H9". That finding
  banked **neither**, so there is no double count either way; I refute Miracle here regardless.
- **Arnav Transport's ₹15,11,889 debit balance** (the parent of the ₹15,000 note) sits in the population
  refuted at ₹0 by [[finding-advances-vs-open-bills]].
- **OM Logistics ₹1,21,321** is a dormant vendor advance in substance. It is **not** among the three
  names banked by [[finding-dormant-vendor-advances]] (Godamwale, Bharat Organics, Ajanta Soya), because
  it narrowly failed that lens's 12-month dormancy test. If that sweep is ever re-run on a 6-month
  window it will pick up these same rupees — tag them there before re-claiming.
- **Reliance JioMart's ₹6,55,787** of open notes was excluded by the sweep because that account is
  ₹8,54,755 in credit; I re-tested and agree — the notes only reduce what JIVO still owes.
- **The ₹38,992 interest overlay** at 8.25% overlaps [[finding-cc-interest-conversion-rate]] and is a
  presentation multiplier, never additive bankable money.
- No overlap with the trade-spend GST claim in [[finding-trade-spend-as-credit-notes]] — that is A/R
  (`ORIN` `DocType`='S'); everything here is A/P (`ORPC` / `OPCH`).

---

Back-links: [[SAVINGS-MOC]] · [[duplicate-payments]] · [[finding-no-invoice-vendors]] ·
[[finding-advances-vs-open-bills]] · [[finding-dormant-vendor-advances]] ·
[[finding-cc-interest-conversion-rate]]
