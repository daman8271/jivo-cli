---
name: jivo-ap-draft
description: Use when an operator hands over a vendor's tax invoice (PDF, photo, scan, or typed details) and wants it entered in SAP B1 as an A/P invoice / purchase invoice / purchase bill — "make a draft of this", "enter this bill", "data entry for this invoice", "AP invoice draft". Also use when asked to check whether a vendor invoice is already in SAP, or why an A/P draft was rejected ("define the numbering series", -10, -4002, -5002 branch).
---

# A/P invoice draft from a vendor invoice (JIVO, SAP B1)

Internal skill for the jivo-cli toolkit. Everything here was learned on live data
on 2026-08-21 (Frystal NINV/26-27/0826, SSY 26-27/1450 → Drafts 54937/54938).

**Core principle: at JIVO the invoice is never keyed in — it is drawn from the
GRPO that the factory already made, and it may already exist. Find before you
make; read back after you make.** RULE 0 in `CLAUDE.md` governs the write itself.

## The procedure

1. **Read the paper into facts.** Vendor name + GSTIN · invoice no. (exactly as
   printed → `NumAtCard`) · invoice date · buyer GSTIN (→ branch) · item lines
   (qty, rate, taxable) · GST split (IGST vs CGST+SGST) · round-off · grand total ·
   "Buyer's order no." (= JIVO PO DocNum) · **JIVO's gate stamp: G.No and date
   (= gate-in date)** · every handwritten number (GE-2026-xxxx = gate entry;
   5-digit = a Drafts DocEntry; 10-digit 2026xxxxxx = a GRPO DocNum).
2. **Run the pre-check** (read-only; it refuses to build if anything is off):
   ```bash
   python3 .claude/skills/jivo-ap-draft/bin/precheck.py \
     --ref "<invoice no>" --vendor "<name fragment or CardCode>" \
     --gstin <buyer GSTIN> --inv-date YYYY-MM-DD --gate-date YYYY-MM-DD \
     --qty <pieces> --total <grand total> [--grpo <DocNum>] \
     --note "GE-2026-xxxx | Veh … | e-Way … | <approvals written on the paper>" \
     [--env <operator>.env] --out /tmp/ap-<ref>.json
   ```
   Exit 2 = **already in SAP** → the deliverable is a paper-vs-record comparison,
   not a new draft. Exit 3 = it could not identify vendor/GRPO/series — fix the
   inputs, never hand-edit the facts it couldn't find.
3. **Show the operator** `sapb1 draft purchase-invoice --dry-run --data-file …`
   (from `sap-b1/cli`, with the operator's env sourced). Wait for their go.
4. **Send** the same command with `--yes`. Note the DocEntry SAP returns.
5. **Read it back and compare**:
   `python3 .claude/skills/jivo-ap-draft/bin/readback.py <DocEntry> --expect-total … --expect-qty …`
   Report its flags as gaps, not as success. Tell the operator the draft number
   and the click-path it prints.

## Rules the scripts encode (know them anyway)

| Field | Rule | Why |
|---|---|---|
| `DocDate` | **gate-in date** (JIVO stamp / GRPO date) | Daman's rule, harness C-0017 |
| `TaxDate` | vendor's invoice date | C-0017 |
| `DocDueDate` | omit — SAP applies the vendor's terms | it computes from doc date |
| `BPL_IDAssignedToInvoice` | branch whose `FederalTaxID` = buyer GSTIN on the paper | -5002 without it |
| `Series` + `DocumentSubType` | the month's GST-tax-invoice series for that branch, e.g. Oil FACTORY Aug-26 = **3684 + `bod_GSTTaxInvoice`** | without both: `-10`/`-4002 define the numbering series` (C-0018) |
| `DocumentLines` | one per **open GRPO line**: `BaseType 20, BaseEntry, BaseLine`, qty = line's open qty | stock is not received twice; a 5,870-pc invoice can be two lines because the GRPO drew from two POs |
| `WTLiable` | `tYES` on every line when the BP is TDS-liable; **always check `WTAmount` on read-back** | API drafts came out with TDS 0 (C-0018) |
| `Comments` | `Based On Goods Receipt PO <n> \| PO <n> \| GATE ENTRY NO <n> \| <paper notes>` ≤ 254 chars | how Accounts searches |

## Hard stops

- **Exit 2 from precheck means stop.** Neetu/USER07 keys drafts in the SAP client
  the same afternoon the paper arrives; handwritten numbers on the scan are
  usually that draft. A second draft on the same GRPO is a duplicate.
- **"Put it in approval / make it pending" is a client action, not a CLI one.**
  The approval request is created when a person presses **Add** on the draft.
  `POST /PurchaseInvoices` to let the approval template intercept is refused by
  the server (`-5002 Attachments folder not defined [131-102]`) and, if it ever
  weren't, would post a live invoice. Never try it; say "open the draft → WTax
  Liable → Add".
- **A draft is owned by the login that made it.** The operator's Document Drafts
  Report defaults to their own user; a draft made as `manager` is invisible to
  them until they set User = manager/All. Use their per-operator env file
  (`sap-b1/cli/<name>.env`, 0600, gitignored) so it lands in their own list.
- **Exit 7 from `sapb1 draft`** = sent, outcome unknown → run readback / query
  Drafts by `NumAtCard`; do not re-send.

## Reference

`reference/series-and-errors.md` — how Oil numbers A/P invoices (branch × month ×
sub-type), the Aug-26 series table, SAP error codes seen and their fixes, and the
SAP-client click-paths for drafts and approvals.
