---
name: jivo-rent-invoice
description: Use when a landlord's rent invoice arrives for JIVO and must be entered in SAP B1 — "Rent - month of <Month>'26" line items, a system-generated invoice with no GST columns filled, monthly or several-months-in-arrears rent, shop/office/godown/space rent, or a landlord named "<NAME> - RENT" in the vendor master. Also use to check whether a rent month is already booked. NOT for employee expense claims (jivo-service-vehicle-expense), labour bills (jivo-loading-unloading-ap) or freight (Transport-Bill-Playbook).
---

# Landlord rent invoice → A/P draft (JIVO)

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

Internal skill. Built from the live run 2026-09-01 (USER07): three Rajouri
Garden landlords → Mart drafts **40119 / 40120 / 40121**, cloned from posted
precedent 8709. Shared rules live in `ap-rm-pm`; RULE 0 in `CLAUDE.md`
governs the write.

**The class:** a `dDocument_Service` A/P invoice on account **5660002 RENT**.
No GRPO, no items, **no TDS** at JIVO's rent levels, and — the part everyone
gets wrong — **not tax-exempt**: it carries a reverse-charge tax code.

## 1 · Company comes from the invoice's customer block

The landlord addresses it to a JIVO entity by name — "Jivo Mart Pvt Ltd" →
`JIVO_MART_HANADB`. Read that block, not the property address (the landlord
and the JIVO office are often the same building, so the addresses match and
prove nothing). Same discipline as C-0066.

## 2 · The vendor — a dedicated RENT card, spelled their way

Landlords get their own card named **`<NAME> - RENT`**. Fetch
`BusinessPartners --all` and match in code on `RENT` and on the surname —
**never assume the invoice's spelling.** Measured: the invoice says
**BHUPINDER KAUR**, SAP holds **`VENDA000950 BHUPENDER  KAUR - RENT`**
(different vowel, double space). Others: `VENDA000949 HARSIMRAN KAUR - RENT`,
`VENDA000958 GURPREET SINGH RENT` — note the third has no dash. Search on the
distinctive part of the name, then confirm by the rent history on the card.

A person may also hold an `ORGV… IMPREST` card; that is their employee float,
never rent.

## 3 · Header

`DocType dDocument_Service` · `DocumentSubType bod_None` · `BPL_IDAssignedToInvoice`
**1 DELHI** · line `LocationCode` **1** · `GSTTransactionType gsttrantyp_BillOfSupply`
· **no `WithholdingTaxDataCollection`**.

- **`Series` — take the `bod_None` family, not the GST one.** Each month has
  two live BPL-1 series and they are not interchangeable: Mart Aug-26 had
  **2874** (`bod_None`, imprest/RCM/non-GST) and 2754 (`bod_GSTTaxInvoice`).
  Identify by pulling live documents of that month and reading their
  `DocumentSubType`. The FY-boundary renumbers everything (Mar-26 was 1107,
  Apr-26 restarted at 2750), so never extrapolate a series forward.
- `NumAtCard` = **the landlord's invoice number exactly as printed** — a bare
  `01`, `07`, `09`. It restarts at 01 each financial year, so `01` recurring
  is normal; the duplicate gate is per vendor per year.
- `DocDate` = `TaxDate` = the **invoice date**; `DocDueDate` = the next day.

## 4 · Lines — one per rent MONTH

An invoice covering April→August is **five lines**, not one, because
`CostingCode2` carries the month the rent belongs to. That is how a
five-month arrears invoice still lands in the right periods.

| Field | Value |
|---|---|
| `AccountCode` | **5660002** RENT |
| `LineTotal` | that month's rent |
| **`TaxCode`** | **`RCGSG@18`** — reverse charge, unregistered landlord. **Not `Exampt`.** |
| `CostingCode` | `CANOLA` |
| `CostingCode2` | the **rent** month, `MM-YYYY`, one per line |
| `CostingCode3` | `SERVICES` |
| `CostingCode4` / `CostingCode5` | **empty** — unlike expense claims, rent carries neither |
| `WTLiable` | `tNO` |

**RCM does not inflate the document.** With `RCGSG@18` the draft still reads
`DocTotal` = the printed total and `VatSum` = 0 (verified on precedent 8709
and on all three 2026-09-01 drafts). JIVO pays that GST to the government
separately; the landlord is paid the face amount.

**TDS:** none at these levels. 194I bites at ₹2.4 L a year and these rents run
₹2,000–₹4,000 a month. Re-check the moment a rent crosses ₹20,000/month.

## 5 · Attach

Upload with `sapb1 attach <scan> --company <DB> --yes` (recipe:
`ap-rm-pm/reference/attachments-upload.md`). It ticks `CopyToTargetDoc tYES` on
every line in every book (C-0090) and stamps `U_CHK`/`U_CHK2` only where `ATC1` has
them — **Mart has no such UDF**, confirmed again on 2026-09-01 against the rent
precedent's own attachment row, so there it sends the tick alone.

## Watch for: stale drafts pile up on rent vendors

These three landlords carried **19 unadded drafts** between them (refs 04–09),
several duplicating invoices that were later posted anyway. Before keying,
list the vendor's drafts — and when a ref you are about to use already sits
there unadded, say so rather than adding a second one.

## Pre-flight — tick before `--yes`

- [ ] company read off the invoice's **customer** block
- [ ] vendor = the `- RENT` card, found by search not by assumed spelling
- [ ] `NumAtCard` clean for that vendor **this financial year** (drafts + posted)
- [ ] one line per rent month; Σ = the printed total
- [ ] `TaxCode RCGSG@18`, Dim3 `SERVICES`, Dim4/Dim5 empty
- [ ] `Series` = the month's **`bod_None`** family, confirmed against live docs
- [ ] read back: `DocTotal` = printed total, `VatSum` = 0, attachment on
