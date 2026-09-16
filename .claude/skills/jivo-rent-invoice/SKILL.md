---
name: jivo-rent-invoice
description: Use when a landlord's rent invoice arrives for JIVO and must be entered in SAP B1 — "Rent - month of <Month>'26" line items, a system-generated invoice with no GST columns filled, monthly or several-months-in-arrears rent, shop/office/godown/space rent, or a landlord named "<NAME> - RENT" in the vendor master. Also use to check whether a rent month is already booked. NOT for employee expense claims (jivo-service-vehicle-expense), labour bills (jivo-loading-unloading-ap) or freight (Transport-Bill-Playbook).
---

# Landlord rent invoice → A/P draft (JIVO)

> 🔴 **ATTACHMENT RULE — COPY TO TARGET DOCUMENT = YES, on every file (Daman, 16 Sept 2026 · C-0090).**
> Whatever this skill attaches — to a draft, GRPO, A/P, credit memo, payment, JV, A/R, anything —
> every `Attachments2` line gets **`CopyToTargetDoc = "tYES"`** (the "Copy to Target Document"
> tick). An API upload lands **`tNO`** by default, so the scan does NOT follow the document when
> it is copied onward (GRPO → A/P, draft → posted). Set it in the SAME PATCH as the Approve stamp,
> **in all three books**, before pointing the document at the row:
> - Oil / Bev: `{"AbsoluteEntry":N,"LineNum":1,"U_CHK":<KB>,"U_CHK2":"OK","CopyToTargetDoc":"tYES"}`
> - Mart (no `U_CHK` columns): `{"AbsoluteEntry":N,"LineNum":1,"CopyToTargetDoc":"tYES"}`
>
> One object per line (line 2, 3 … too). Read back `Attachments2(N)`: every line must show
> `"CopyToTargetDoc": "tYES"` — if any shows `tNO`, the entry is not done. Proven live 16 Sept on
> Oil 177765/177767, Mart 59273, Bev 43223 (HTTP 204, stamp kept).

Internal skill. Built from the live run 2026-09-01 (USER07): three Rajouri
Garden landlords → Mart drafts **40119 / 40120 / 40121**, cloned from posted
precedent 8709. Shared rules live in `jivo-ap-draft`; RULE 0 in `CLAUDE.md`
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

Follow `jivo-ap-draft/reference/attachments-upload.md` (`-H "Expect:"`, and
grep the `AbsoluteEntry` — the response is not valid JSON). **In Mart skip the
`U_CHK`/`U_CHK2` stamp** — `ATC1` has no such UDF there, confirmed again on
2026-09-01 against the rent precedent's own attachment row. **Do NOT skip the PATCH
itself:** Mart still gets `{"Attachments2_Lines":[{"AbsoluteEntry":N,"LineNum":1,"CopyToTargetDoc":"tYES"}]}`
(C-0090) — every book, every line.

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
