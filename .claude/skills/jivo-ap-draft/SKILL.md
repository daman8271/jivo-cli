---
name: jivo-ap-draft
description: Use when an operator hands over a vendor's tax invoice (PDF, photo, scan, or typed details) and wants it entered in SAP B1 as an A/P invoice / purchase invoice / purchase bill — "make a draft of this", "enter this bill", "data entry for this invoice", "AP invoice draft". Also use when asked to check whether a vendor invoice is already in SAP, or why an A/P draft was rejected ("define the numbering series", -10, -4002, -5002 branch).
---

# A/P invoice draft from a vendor invoice (JIVO, SAP B1)

Internal skill for the jivo-cli toolkit. Everything here was learned on live data
on 2026-08-21: Frystal NINV/26-27/0826 turned out to be Neetu's existing Draft 54906;
SSY 26-27/1450 became Drafts 54937 **and** 54938 — the same document twice, under two
logins — which is exactly the duplicate this skill now prevents.

**Core principle: at JIVO the invoice is never keyed in — it is drawn from the
GRPO that the factory already made, and it may already exist. Find before you
make; read back after you make.** RULE 0 in `CLAUDE.md` governs the write itself.

## The procedure

1. **Read the paper into facts.** Vendor name + GSTIN · invoice no. (exactly as
   printed → `NumAtCard`) · invoice date · **buyer name** (Jivo Wellness Pvt Ltd →
   `JIVO_OIL_HANADB`, the default; Jivo Mart → `JIVO_MART_HANADB`; Jivo Beverages →
   `JIVO_BEVERAGES_HANADB`) · buyer GSTIN (→ branch) · "Buyer's order no." (= JIVO
   PO DocNum) · item lines (qty, rate, taxable) · GST split (IGST vs CGST+SGST) ·
   round-off · grand total · **JIVO's gate stamp: G.No and date (= gate-in date)** ·
   every handwritten number (GE-2026-xxxx = gate entry; 5-digit = a Drafts
   DocEntry; 10-digit 2026xxxxxx = a GRPO DocNum).
2. **Run the pre-check** (read-only; it refuses to build if anything is off):
   ```bash
   python3 .claude/skills/jivo-ap-draft/bin/precheck.py \
     --ref "<invoice no>" --vendor "<name fragment or CardCode>" \
     --gstin <buyer GSTIN> --inv-date YYYY-MM-DD --gate-date YYYY-MM-DD \
     --qty <pieces> --total <grand total> --po <buyer's order no> [--grpo <DocNum>] \
     --item "<item description as printed>" \
     --note "GE-2026-xxxx | Veh … | e-Way … | <approvals written on the paper>" \
     [--company JIVO_MART_HANADB] [--env <operator>.env] --out /tmp/ap-draft.json
   ```
   - **Exit 2 = already in SAP.** Run the `readback.py` lines it prints, one per
     existing draft, and give the operator the paper-vs-record comparison and the
     draft number(s). Do not draft again. Two drafts on one invoice → a human
     removes the extra in the client.
   - **Exit 3** = it could not identify vendor / GRPO / branch / series — fix the
     inputs; never hand-edit facts it couldn't find.
   - **Exit 4** = SAP unreachable. Not a data answer. It prints the bridge fix.
3. **Show the operator** the dry-run, from `sap-b1/cli` with the operator's env
   sourced (`set -a; source <operator>.env; set +a`):
   `./sapb1 draft purchase-invoice --dry-run --data-file /tmp/ap-draft.json`.
   Wait for their go.
4. **Send** the same command with `--yes`. Note the DocEntry SAP returns.
5. **Read it back and compare**:
   `python3 .claude/skills/jivo-ap-draft/bin/readback.py <DocEntry> --expect-total … --expect-qty …`
   Report its flags as gaps, not as success. Give the operator the draft number
   and the click-path it prints.

## Rules the scripts encode (know them anyway)

| Field | Rule | Why |
|---|---|---|
| `DocDate` | **gate-in date** (JIVO stamp / GRPO date) | Daman's rule, harness C-0017 |
| `TaxDate` | vendor's invoice date | C-0017 |
| `DocDueDate` | omit — SAP applies the vendor's terms | it computes from doc date |
| `BPL_IDAssignedToInvoice` | branch whose `FederalTaxID` = buyer GSTIN; one GSTIN sits on several Oil branches (2 FACTORY, 5 HARYANA SALES, 8 …) — **the GRPO's branch decides** | -5002 without it |
| `Series` + `DocumentSubType` | the month's GST-tax-invoice series for that branch, e.g. Oil FACTORY Aug-26 = **3684 + `bod_GSTTaxInvoice`** | without both: `-10`/`-4002 define the numbering series` (C-0018) |
| `DocumentLines` | one per **open GRPO line**: `BaseType 20, BaseEntry, BaseLine`, qty = line's open qty | stock is not received twice; a 5,870-pc invoice can be two lines because the GRPO merged two POs — say so to the operator |
| `WTLiable` | `tYES` on every line when the BP is TDS-liable; **always check `WTAmount` on read-back** | API drafts came out with TDS 0 (C-0018) |
| `Comments` | `Based On Goods Receipt PO <n> \| PO <n> \| GATE ENTRY NO <n> \| <paper notes>` ≤ 254 chars | how Accounts searches |

## Hard stops

- **Exit 2 from precheck means stop.** Accounts (Neetu/USER07 and others) key
  drafts in the SAP client the same afternoon the paper arrives; handwritten
  numbers on the scan are usually that draft. It checks by vendor ref **and** by
  GRPO, so a typo'd ref does not hide a duplicate. A second draft on the same
  GRPO is a duplicate.
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
  precheck prints the login it will use.
- **Exit 7 from `sapb1 draft`** = sent, outcome unknown → run readback / query
  Drafts by `NumAtCard`; do not re-send.
- **SAP unreachable / timeouts** (`cannot reach SAP Service Layer`): the box only
  admits the office IP. `bash connections/sap-home-bridge.sh`, then
  `export SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 SAPB1_TIMEOUT=180 HANA_ENV=connections/hana-office-bridge.env`.
  Exported values beat `--env` files, so the operator's env still picks the login.
  `sap-office-bridge.sh` needs an office PC parked on the VPS and is often down;
  the home bridge is the durable one.

## Reference

`reference/series-and-errors.md` — how Oil numbers A/P invoices (branch × month ×
sub-type), the Aug-26 series table, SAP error codes seen and their fixes, and the
SAP-client click-paths for drafts and approvals.
