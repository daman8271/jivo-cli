---
name: jivo-ap-credit-memo
description: Use when an operator hands over a CREDIT NOTE (or debit note) that a VENDOR issued to JIVO — "credit note from <vendor>", "CN", "vendor gave us credit", rate difference, short quantity, rejected / returned goods, price correction, invoice reversal — and wants it in SAP B1 as an A/P Credit Memo draft (draft purchase-credit-note). Also use to check whether a vendor CN is already in SAP. Not for JIVO's own sales credit notes to customers (A/R) and not for vendor invoices (jivo-ap-draft / jivo-ap-service-draft).
---

# A/P Credit Memo draft from a vendor's credit note (JIVO, SAP B1)

Internal skill. Built from Royal Prime Labels CN 56 → draft 55128 on 2026-08-24, and
Daman's correction on it ("you never put the original reference number and date").

**Core principle: a vendor CN is a correction to something already in the books.
Find what it corrects — the invoice, and the Goods Return if stock went back — and
base the credit memo on that; then carry the CN's own statutory reference fields.**
`jivo-ap-draft` holds the shared rules (duplicate gate, series discipline, dates,
hard stops, delete); read it first. Plumbing: `acc/_playbook/sap <args>`.

## The procedure

1. **Read the scan in tiles first** — `jivo-ap-draft/bin/zoom.py "<scan>" --dpi 300`
   (`--box L,T,R,B --dpi 900` for a doubtful digit), then map **every handwritten
   mark to a field** using `jivo-ap-draft/reference/handwriting.md` — "Common" →
   Budget `CostingCode3 = FACT_COM` (C-0027), and never compare a digit against a
   sample from a different hand on the same paper.
2. **Read the paper into facts.** Vendor + GSTIN · **Credit Note No.** → `NumAtCard` ·
   CN date → `TaxDate` · **"Original Invoice No. & Date"** → `OriginalRefNo` (exactly as
   printed, e.g. `RPL/1164/2026-27`) + `OriginalRefDate` (**mandatory**, C-0024) · buyer
   GSTIN → branch · lines (item, qty, rate) · CGST/SGST or IGST · round-off · total ·
   e-invoice IRN/Ack if printed · approvals.
3. **Find the original A/P invoice.** Posted `PurchaseInvoices` by `NumAtCard` (try the
   printed form and `RPL/1164/26-27`-style variants; else fetch the vendor's month and
   match "1164" in code) **and** `Drafts` — it may still be an un-added draft, even
   `dasPending` in someone's approval queue. Record DocEntry/DocNum, DocDate, lines,
   status.
4. **Find a Goods Return.** `PurchaseReturns` for the vendor with `NumAtCard` = the
   original invoice ref, or matching item + qty near the CN date; note
   `RemainingOpenQuantity` on its lines.
5. **Duplicate gate — hard stop.** `Drafts` (`DocObjectCode eq 'oPurchaseCreditNotes'`)
   and posted `PurchaseCreditNotes` for the `CardCode` with `NumAtCard '<cn no>'`; plus
   any CN for the vendor around the date with the same total. Any hit → stop, report,
   create nothing.
6. **Classify the CN** by comparing its line to the invoice line: same qty + lower rate
   = rate difference; part qty = short/return; whole invoice = reversal. Then pull the
   vendor's last 3 posted `PurchaseCreditNotes` in full — they show how Accounts books
   that kind (based-on vs standalone, series, subtype, `Rounding`, dates, TDS).
7. **Choose the base** (precedent decides; these are JIVO's observed patterns):
   - qty return **with an open Goods Return** → base on it: lines `BaseType 21`,
     `BaseEntry` = return DocEntry, `BaseLine` (precedent: RPL CN 65, Feb-26 —
     "Based On Goods Return"). Closes the return; no second stock movement.
   - invoice posted & open, no return → base on the invoice: `BaseType 18`.
   - invoice **only a draft or absent** → standalone per precedent, link it in
     `Comments`, and **flag loudly: the invoice must be Added before this CN** or the
     books briefly show a credit against nothing.
   - rate difference only → whatever precedent shows (often a price-difference line, not
     an item line — check before moving stock).
8. **Fields** (beyond the shared rules):

   | Field | Rule | Why |
   |---|---|---|
   | `OriginalRefNo` / `OriginalRefDate` | the CN's "Original Invoice No. & Date", verbatim | C-0024; all posted JIVO CNs carry them |
   | `Series` + `DocumentSubType` | **credit memos have their own series** (Oil branch 2 Aug-26 = **3541**, verify the month); subtype per precedent (`bod_GSTTaxInvoice`) | never an invoice series |
   | `BPL_IDAssignedToInvoice` | the original invoice's branch | one GSTIN, several branches |
   | `Rounding` / `RoundingDiffAmount` | `Rounding tNO` + `RoundingDiffAmount <paper round-off>` — `tYES` smears the paise into the GST lines | GST must match the paper to the paisa |
   | `DocDate` | **≥ the base document's DocDate** (SAP refuses earlier); precedent used the Goods Return's date | 55128: 17-08 (return) vs CN 13-08 |
   | `TaxDate` | the CN's date | |
   | `WTLiable` | precedent (RPL: never TDS on CNs) | |
   | `Comments` ≤254 | `A/P Credit Memo agst <orig inv> dt <date> \| Vendor CN <n> dt <date> \| <item qty> \| Based On Goods Return <DocNum> \| <approval>` | how Accounts searches |

9. **Dry-run, then `--yes` — same turn, do not stop in between:**
   `acc/_playbook/sap draft purchase-credit-note --dry-run --data-file <payload.json>`,
   then `--yes`. Exit 7 = look (Drafts by `NumAtCard` + `CardCode`), don't resend.

   **🔴 Never end your turn on the dry-run**, and never ask "shall I send it?". The
   preview catches a wrong vendor/branch/series/total *before* it reaches the books
   — it is not a gate on the operator (RULE 0). A draft posts nothing until a human
   presses Add in the SAP B1 client. Stop only for a real fault the preview shows,
   or when the precheck told you to. Daman, 2026-09-09.
10. **Attach** — `jivo-ap-draft/reference/attachments-upload.md`: the operator's scan, plus
   the Goods Return's / invoice's file if the base document has one (55128's return had
   none). Stamp `U_CHK2 OK` first or the pointer is refused.
11. **Read back by query** (readback.py is invoice-shaped): `DocObjectCode
    oPurchaseCreditNotes`, `CardCode`, `NumAtCard`, `DocTotal` = paper, `VatSum` =
    CGST+SGST to the paisa, `RoundingDiffAmount`, **`OriginalRefNo`/`OriginalRefDate`
    set**, base refs on every line, `WTAmount`, `AttachmentEntry`.

## Pre-flight — tick before `--yes`

- [ ] duplicate gate: CN no. clean for this vendor in Drafts + posted
- [ ] original invoice located (posted / draft / absent — stated); Goods Return checked
- [ ] base chosen per precedent; if the invoice isn't posted, the Add-order warning is in the report
- [ ] `OriginalRefNo` + `OriginalRefDate` filled from the paper
- [ ] `DocTotal`, `VatSum`, `RoundingDiffAmount` = paper to the paisa
- [ ] credit-memo series for **this month**, subtype, branch = invoice's
- [ ] `DocDate` ≥ base doc date; `TaxDate` = CN date; `WTLiable` = precedent
- [ ] **field diff against one posted precedent CN** — every non-null field accounted for

## Worked example — Royal Prime Labels CN 56 (2026-08-24) → draft 55128

CN 56 dt 13-Aug-26 against RPL/1164/2026-27 dt 13-Aug-26: 27,500 × "5 LTR COLD PRESS CANOLA
OIL FRONT LABEL" @ 1.05 = 28,875.00 + CGST 2,598.75 + SGST 2,598.75 + 0.50 = **34,073.00**.

- RPL/1164 was **not posted** — A/P draft 55003 (₹1,61,813, 6 lines), already `dasPending`.
- The CN = one line of it returned: posted Goods Return 2126086501 (DocEntry 743, dt 17-08,
  keyed by USER36) carried exactly 27,500 of `PM0000046 LABEL 5 LTR COLD PRESS FRONT` open.
- Draft: `BaseType 21 / BaseEntry 743 / BaseLine 0`; Series **3541** + `bod_GSTTaxInvoice`;
  branch 2; `Rounding tNO`, `RoundingDiffAmount 0.5`; DocDate 17-08, TaxDate 13-08;
  `OriginalRefNo RPL/1164/2026-27`, `OriginalRefDate 2026-08-13`; WT 0; scan attached
  (AE 172305). **Add order: invoice draft 55003 first, then this CN.**
