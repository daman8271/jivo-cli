---
name: jivo-loading-unloading-ap
description: Use when a labour contractor's loading / unloading bill arrives for JIVO (Oil OR Beverages) and must be entered in SAP B1 — "BHORIA bill", "loading charges", "unloading charges", "finish goods loading" of oil or of water, "casual labour bill", a bill whose invoice number equals its amount, or a fortnightly bill backed by a dispatch-register printout. Also use to check whether such a bill is already keyed, or to book the handwritten "Debit ₹X" cut against one. NOT for freight / bilty / transporter bills (jivo-oil-freight-grpo + Transport-Bill-Playbook) and not for fuel or other service bills (jivo-ap-service-draft).
---

# Loading / unloading labour bill → A/P invoice draft (JIVO Oil / Bev)

> 🔴 **ATTACHMENT RULE — every file goes up with `sapb1 attach`, never by hand (Daman, 16 Sept 2026 · C-0090).**
> Whatever this skill attaches — to a draft, GRPO, A/P, credit memo, payment, JV, A/R, anything —
> upload it with **`sapb1 attach <file> [<file>...] --company <DB>`** (`--dry-run` first, then `--yes`).
> It puts all the files on ONE `Attachments2` row, ticks **Copy to Target Document = `tYES`** on
> every line (plus the Approve stamp `U_CHK`/`U_CHK2 OK` in Oil and Bev — Mart has no such fields),
> reads the row back, and exits non-zero unless every line is `tYES` and every file downloads
> back byte-identical. An upload by any other route
> lands `tNO`, and then the scan does NOT follow the document onward (GRPO → A/P, draft → posted).
> - It prints `"AttachmentEntry": N` — point the document at row N (in the payload, or `sapb1 patch`).
> - Exit 8 = the row exists but is not finished — the message names the fix (usually
>   `sapb1 attach --row N --yes`). Exit 7 = an answer never came back: look at the row
>   (`sapb1 query Attachments2 --filter "AbsoluteEntry eq N"`) before sending any file again.
> - Never `curl -X POST …/Attachments2` or hand-PATCH the tick any more. Proven live 17 Sept 2026:
>   Oil 177963 (two files, byte-identical), Mart 59373, Bev 43331.

Internal skill. Built from the live maiden runs 2026-09-01: BHORIA oil bill
90059 → Oil draft 55786 (cloned from posted 49636/49170; later deleted on
Daman's order) and water bill 48634 → **Bev draft 15816** (cloned from Bev
posted 13670). Daman named this its own category that day. Shared rules
(dates, duplicate gate, hard stops, delete) live in `jivo-ap-draft`; RULE 0
in `CLAUDE.md` governs the write.

## ⚠️ C-0066 — the DESCRIPTION line is the switch, never the letterhead

Every BHORIA bill is addressed to JIVO WELLNESS (P) LIMITED, GSTIN
06AACCJ4223F1Z0. Ignore that. **Read the DESCRIPTION/WORK DETAILS line —
that one word routes the whole entry** (taught by Daman 2026-09-01, "very
important and crucial"):

- `Finish GOODS loading of Oil (…) KGS` → the **Oil** column below, always
- `Finish GOODS loading of water (…) ltr` → the **Bev** column below, always

The unit confirms the read: oil is billed in KGS, water in ltr. Both books
carry the vendor under the SAME CardCode and run parallel fortnightly
trails. What flips with that one word:

| | Oil (oil bill) | Bev (water bill) |
|---|---|---|
| Dim1 `CostingCode` | `CANOLA` | `WATER` |
| TDS `WTCode` (194C 1%) | `1023` | `1230` |
| Series (Aug-26) | 3324 | 2678 |
| Rate basis | ₹/kg (× 0.910 check!) | ₹/litre (no conversion) |
| Attach stamp | `U_CHK` KB + `U_CHK2 OK` + `CopyToTargetDoc tYES` | `U_CHK2 OK` + `CopyToTargetDoc tYES` |

Everything else below is identical in both books (measured on the posted
precedents of each).

## The bill, decoded

BHORIA LABOUR CONTRACTOR, Panipat — vendor **`VENDA000281`** in Oil AND Bev,
PAN CBPPN0754C (4th char **P = individual → 194C TDS 1%**).
Bills land ~fortnightly; in Oil usually as a PAIR:

| Which | Says | Account | Dim3 |
|---|---|---|---|
| Big — "Finish GOODS loading of Oil … KGS" / "of water … ltr" | ₹0.080/kg oil · ₹0.075/L water | **5670002** UNLOADING/LOADING-INDIRECT | `Del Bkhp` |
| Small (Oil) — casual labour / misc | — | **5100004** UNLOADING/LOADING-DIRECT | `Factory` |

**The invoice number IS the rupee amount** (bill 90059 = ₹90,059). Whole
history follows this (79314, 86518, 59916, 4500 …). It is the `NumAtCard`
duplicate key — check `Drafts` AND posted `PurchaseInvoices` for it first.

## The kg-vs-litres check — where the money is (OIL bills only)

(Water bills are per-litre — rate × printed litres, cross-foot the register
day totals, no conversion, usually no debit.)

The "KGS" quantity on the bill is actually the dispatch register's **LITRES**
total, but the rate is per **kg**. The store's handwritten audit on the paper
is: `litres × 0.910 = kg`, `kg × rate` = payable (90059's: 11,25,743 L →
10,24,426 kg → ₹81,954). The gap becomes a green-ink **"Debit ₹X"**.

**Book the FULL billed amount anyway.** Precedent is explicit: June's 84713
was posted in full, then A/P credit memo 626065012 (₹7,289) was drawn
**Based On the posted invoice**. The debit note cannot be based on a draft —
it is a follow-up entry after posting, via `jivo-ap-credit-memo`.

## The payload (big bill; clone of 49636)

Header: `DocType dDocument_Service` · `DocumentSubType bod_None` · `Series` =
bill-month HR_B flavour (Aug-26 = 3324) · **`DocDate` = `TaxDate` =
`DocDueDate` = the bill date** (they key late, date stays the bill's) ·
`NumAtCard` = invoice no. · `BPL_IDAssignedToInvoice 2` (FACTORY) ·
`GSTTransactionType gsttrantyp_BillOfSupply` (no GST — unregistered labour) ·
Comments: `BEING EXPENSE BOOKED AGAINST LOADING UNLOADING AMOUNT <n>/-,
INVOICE NO. <n>, DATED <bill date>, PERIOD <a> TO <b>`.

One line: `AccountCode 5670002` · `LineTotal` = full billed · `TaxCode
Exampt` · `WTLiable tYES` · `LocationCode 2` · `CostingCode CANOLA` ·
**`CostingCode2` = the SERVICE-period month `MM-YYYY`, not the bill month**
(49636 billed 03-08 carries `07-2026`) · `CostingCode3 Del Bkhp` ·
`CostingCode5 HR` · no CostingCode4. `U_Recvd_Qty` stays 0 here — precedent
keys no quantity on this class (unlike fuel bills / C-0025); the register
pages ride along in the attachment instead.

TDS must be explicit or it lands 0:

```json
"WithholdingTaxDataCollection": [
  {"WTCode": "1023", "TaxableAmount": 90059, "WTAmount": 901}
]
```

SAP kept it: draft DocTotal came back 90,059 − 901 = **89,158** ✓.

Send: `sapb1 draft purchase-invoice --data-file <payload.json> --dry-run`,
show the operator, then `--yes`.

## Attach, then stop or submit

Attach the **whole scan** — bill page plus every dispatch-register page — per
`jivo-ap-draft/reference/attachments-upload.md` (no base document: scan
alone), with `sapb1 attach <scan> --yes`: it stamps `U_CHK`/`U_CHK2 OK` and ticks
`CopyToTargetDoc tYES` (C-0090). Then PATCH the draft's `AttachmentEntry` and verify a
byte-identical read-back. (The maiden run's curl upload needed `-H "Expect:"` or it got
`206 Bad Post content`; `sapb1 attach` does not.)

Then `jivo-add-and-new` applies as everywhere — submit with
`sapb1 add-draft` — **unless the operator says hold** (Daman's maiden-run
call: "don't add it yet"; draft 55786 was left unsubmitted on his word).

## The overall GL method — this generalizes (Daman, 2026-09-01)

Daman's framing: this skill is the pattern **for GL entries overall**, not
just BHORIA. A "GL entry" here = a service A/P invoice booked straight to a
GL expense account (`dDocument_Service`, line = `AccountCode` + `LineTotal`)
— no GRPO, no items, no hand-keyed journal. For ANY such bill, the same
spine:

1. **Read the description line first** — the product/service word on the
   paper routes the entry (which company's books, which dimension set).
   The letterhead and GSTIN prove nothing; JIVO entities bill each other's
   paper all day.
2. **The vendor's posted history in THAT company is the template.** Pull the
   last posted precedent in full and clone every populated field — account,
   dims, series flavour, dates pattern, tax code. Never compose from theory.
3. **Duplicate gate** on `NumAtCard` in Drafts + posted, then book the FULL
   billed amount; handwritten cuts ("Debit ₹X") become an A/P credit memo
   based on the invoice AFTER it posts.
4. **TDS explicitly** in `WithholdingTaxDataCollection` — the code is
   company-specific (same vendor, different code per book) — or it lands 0.
5. **Attach the whole paper**, stamp, verify byte-identical; submit via
   add-draft or hold, on the operator's word.

A new GL bill class (a new vendor, a new expense head) = the same five
steps; record what its precedent shows and it becomes its own section here.

## Pre-flight — tick before `--yes`

- [ ] `NumAtCard` clean in `Drafts` + posted `PurchaseInvoices` (remember: no. = amount)
- [ ] amount = FULL billed figure; handwritten debit noted for the post-posting credit memo
- [ ] litres×0.910×rate recomputed; matches the handwritten audit on the paper
- [ ] big bill → 5670002 + `Del Bkhp` · small bill → 5100004 + `Factory`
- [ ] `CostingCode2` = service-period month, all three dates = bill date
- [ ] `WithholdingTaxDataCollection` explicit, WTCode 1023, ≈1% rounded
- [ ] read-back: DocTotal = billed − TDS; attachment on; submitted or held per operator
