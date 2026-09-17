---
name: jivo-ap-service-draft
description: Use when an operator hands over a vendor bill that has NO goods receipt (GRPO) behind it and wants it entered in SAP B1 as an A/P invoice draft — fuel / petrol pump / diesel bills, courier, electricity, water, rent, AMC, repair, professional or any service / expense bill — "book this bill", "enter this expense", "fuel bill entry". Also use when jivo-ap-draft's precheck exits 3 with "no GRPO". NOT for transporter / freight / bilty / lorry bills — those are 98% GRPO-copy jobs, see sap-b1/entry-vault/04-playbooks/Transport-Bill-Playbook.md. Not for item purchases with a GRPO (jivo-ap-draft) or vendor credit notes (jivo-ap-credit-memo).
---

# A/P draft for a service / expense bill — no GRPO (JIVO, SAP B1)

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

Internal skill. Built from the Om Sai fuel bill 2495 → draft 55130 on 2026-08-24, and
from Daman's corrections on it the same evening ("no place of supply, no location, no
quantity" — all three were fields the paper carried and the payload dropped).

**Core principle: with no GRPO there is nothing to draw from, so the vendor's own
posted history is the template. Clone every populated field of a posted precedent,
not just the ones that make the total right.** RULE 0 in `CLAUDE.md` governs the write;
`jivo-ap-draft` holds the shared rules (dates, series discipline, duplicate gate,
hard stops, delete) — read it first, then this.

Plumbing: `acc/_playbook/sap <args>` (bridge + operator login + write log). All queries
below are through it.

## The procedure

1. **Read the scan in tiles first** — `jivo-ap-draft/bin/zoom.py "<scan>" --dpi 300`
   (`--box L,T,R,B --dpi 900` for a doubtful digit), then map **every handwritten
   mark to a field** using `jivo-ap-draft/reference/handwriting.md` — "Common" →
   Budget `CostingCode3 = FACT_COM` (C-0027), and never compare a digit against a
   sample from a different hand on the same paper.
2. **Read the paper into facts.** Vendor + GSTIN (verify against the BP master — scans
   misread digits: Om Sai's "600?31" was `6065G1`) · bill no. exactly as printed →
   `NumAtCard` · bill date · billing period · **JIVO gate stamp G.No + date** · **every
   row: date, vehicle / bilty / meter, item, qty, rate, value** · discount and its
   basis · round-off · NET TOTAL · GST or none · every handwritten approval.
3. **Duplicate gate — hard stop.** `Drafts` where `NumAtCard eq '<ref>'` (any doctype);
   sweep the vendor's drafts with `--all` (Om Sai had 94) and its posted
   `PurchaseInvoices` by `NumAtCard` **and** by `DocDate` in the bill's month. Any hit →
   stop, report paper-vs-record, create nothing. Run `jivo-ap-draft`'s precheck anyway:
   its ref scan is a second opinion and exit 3 confirms "no GRPO" — a GRPO comment
   mentioning the same number can be a *bilty* number on another vendor (it was).
4. **Pull the precedent** — the vendor's last 3 posted `PurchaseInvoices` in full
   (`--all --json`, then the one with `DocumentLines`). Write down every non-null
   field; that list is the payload's spec. What it decides:

   | Field | What precedent tells you | Om Sai (fuel) |
   |---|---|---|
   | `DocType` | `dDocument_Service` for expense bills | service |
   | `Series` + `DocumentSubType` | the **flavour** (non-GST `HR_B` + `bod_None` vs GST `HR_G` + `bod_GSTTaxInvoice`); then find **this month's** number for that flavour and branch (`reference/series-and-errors.md` in jivo-ap-draft; confirm with what Aug-26 posted docs of that flavour carry) | 3324 HR_B0826 + bod_None |
   | `BPL_IDAssignedToInvoice` | the branch precedent uses. **A `[SAP -3000] … does not have permission to use this object` on `BusinessPlaces` does NOT block this bill** — some logins (USER08/Divjot) cannot open the branch *list*, and none of them need to: take the branch from the vendor's last posted invoices above, or from the operator, and pass it. Nothing has to be granted in SAP first (verified live 2026-09-04) | 2 FACTORY |
   | `GSTTransactionType` | copy | `gsttrantyp_BillOfSupply` (petrol/diesel are outside GST) |
   | `WTLiable` / TDS | **precedent beats the master flag**; transport vendors are often 194C — check the last 3, report both, follow precedent | master `boNO`, all 3 posted TDS 0 → none |
   | line `AccountCode` | per head: fuel-vehicles / generator / conveyance / freight … | 5650015 / 5680001 / 5690002 |
   | line `CostingCode`…`CostingCode5` | copy per vehicle/unit; **`CostingCode3` (Budget) is mandatory** — guard 1120009 "Please select Budget" rejects the POST without it | FACT_COM / Del Bkhp; `CostingCode5` HR |
   | line `LocationCode` | copy — **2 = Bhakharpur factory = the Haryana place-of-supply the client shows**; empty = empty on screen (C-0025) | 2 |
   | line `U_Recvd_Qty` | **the paper's per-row qty lives here** — service rows have no Quantity column in the client, so litres/kg/km would otherwise vanish (C-0025) | litres per vehicle |
   | line split | one line per vehicle / bilty / meter, as precedent does | 6 lines |

5. **Build the lines so nothing on the paper is lost.** Every paper column lands in some
   field: qty → `U_Recvd_Qty`; vehicle/bilty → the dimension precedent uses; period,
   gate no., approvals → `Comments`. Decode discounts from the arithmetic, never from the
   label: Om Sai's "Discount @ 0.50" is **₹0.50 per litre on diesel only** (549.689 L ×
   0.50 = the printed 274.84) — net it onto the diesel lines, nothing on petrol. Absorb
   the paper's round-off into the largest line so **Σ lines = NET TOTAL exactly**.
6. **Dates:** `DocDate` = gate-stamp date (C-0017), `TaxDate` = bill date, omit
   `DocDueDate`. Precedent normally agrees (Om Sai July: 07-18 / 07-15); if it doesn't,
   follow C-0017 and say so.
7. **Comments** (≤254): `Bill <ref> dt <date> period <a-b> | GATE ENTRY NO <n> dt <date> |
   <qty summary: Petrol 110.150 Ltr Diesel 549.689 Ltr> | <approval as written>`.
8. **Dry-run, then `--yes` — same turn, do not stop in between:**
   `acc/_playbook/sap draft purchase-invoice --dry-run --data-file <payload.json>` then
   `--yes`. Exit 7 = look, don't resend. A 400 with `1120009` = add `CostingCode3`; with
   `-10`/`-4002` = wrong series/subtype flavour.

   **🔴 Never end your turn on the dry-run** and never ask "shall I send it?". The
   preview catches a wrong branch/series/total *before* it reaches the books; it is
   not a gate on the operator (RULE 0). A draft posts nothing — no stock, no ledger
   entry — until a human presses Add in the SAP B1 client, so there is nothing to
   protect them from by stopping. Only stop if the preview shows a real fault
   (wrong vendor, branch, series, or a total that does not match the paper) or the
   precheck told you to. Daman, 2026-09-09: *"it is not directly making the drafts
   but confirming for their confirmation — should not happen like this."*
9. **Attach the scan** — `sapb1 attach <scan> --yes`, per `jivo-ap-draft/reference/attachments-upload.md`
   (steps 1, 3, 4; there is no base document to copy). It stamps `U_CHK2 OK` (without it the
   pointer is refused) and ticks `CopyToTargetDoc tYES` on every line in every book (C-0090).
10. **Read back:** `readback.py <DocEntry> --expect-total <net>` — its "not drawn from a
   GRPO" flags are a **false positive for this document class**; say so. Then verify by
   query: `DocTotal` exact, every line has `LocationCode`, `CostingCode3`, `U_Recvd_Qty`,
   Σ `U_Recvd_Qty` = the paper's qty total, `GSTTransactionType`, `AttachmentEntry`.
11. **Name the lane — always, unprompted.** Most bills entered with THIS skill go
   on to wait for the above-office budget approval in JSAP, but not all of them:
   ```bash
   python3 .claude/skills/jivo-ap-draft/bin/jsap_route.py <DocEntry> --company oil -v
   ```
   A `56xxxxx` expense line with a Budget dimension **WAITS IN JSAP** (freight
   outward, loading, rent, repairs, conveyance, legal…). But **job work
   `5100009`/`5500003`, inward and import freight `5100002`/`5500001`, lab &
   testing `5100018` and fixed assets post directly** — being a service bill is
   *not* the test, the account is. Nothing auto-approves in JSAP at the moment
   (no FY26-27 allocation is loaded), so a JSAP document genuinely waits for a
   person. Full rule and accuracy: **`jivo-ap-draft/reference/jsap-routing.md`**.

## Pre-flight — tick before `--yes`

- [ ] duplicate gate: ref clean in Drafts + posted; vendor's month clean
- [ ] Σ lines = NET TOTAL to the paisa; discount on the rows that earned it only
- [ ] Σ `U_Recvd_Qty` = paper's qty total; every line has `LocationCode` + `CostingCode3`
- [ ] series = **this month's** number of the precedent flavour; `DocumentSubType` matches
- [ ] `DocDate` = gate date, `TaxDate` = bill date; `WTLiable` = precedent
- [ ] **field diff against one posted precedent**: every non-null header/line field is
      in the payload or consciously omitted
- [ ] Comments carry gate no., period, qty summary, approval

## Worked example — Om Sai Filling Station, bill 2495 (2026-08-24) → draft 55130

| Line | Account / head | Vehicle | Amount ₹ | `U_Recvd_Qty` (L) | `LocationCode` |
|---|---|---|---|---|---|
| 0 | 5680001 GENERATOR (diesel) | CAN | 4,739.00 (4,764 − 25.00 disc) | 50.000 | 2 |
| 1 | 5690002 CONVEYANCE (petrol) | DL7SCH5064 | 1,333.89 | 13.000 | 2 |
| 2 | 5650015 FUEL-VEHICLES | HR42H4618 | 4,655.20 | 45.359 | 2 |
| 3 | 5650015 FUEL-VEHICLES | 0901 | 1,745.00 | 17.003 | 2 |
| 4 | 5650015 FUEL-VEHICLES | HR42J6791 | 3,570.00 | 34.788 | 2 |
| 5 | 5650015 FUEL-VEHICLES | HR69F7125 | 47,359.91 (47,610 − 249.84 disc − 0.25 rnd) | 499.689 | 2 |

Total 63,403.00 = paper; Σ litres 659.839 = paper (petrol 110.150 + diesel 549.689).
Series 3324 HR_B0826 + bod_None, branch 2, BillOfSupply, TDS none, DocDate 18-08 (gate
G.No 181), TaxDate 15-08. Judgment call to surface: DL7SCH5064's petrol → CONVEYANCE, the
companion-line pattern in every precedent doc (~85%; a two-field edit if Accounts differs).

## Transport / freight bills — NOT this skill

**Measured 2026-08-27 and the earlier note here was wrong.** Transport bills at JIVO are
**not** no-GRPO bills: the factory raises one **service GRPO per bilty** and the bill is a
copy of N of them — 1,073 of 1,093 Oil transport A/P lines (98.2 %) carry `BaseType 20`.
There were 433 such bills across the three books in the first five months of FY26-27.

**Use the GRPO-copy path with `"DocType": "dDocument_Service"`, and follow
`sap-b1/entry-vault/04-playbooks/Transport-Bill-Playbook.md`.** In one line: find the
GRPOs by matching the bill's bilty numbers to `OPDN.NumAtCard`, copy them, then set the
only two things the copy cannot give you — **TDS** (`WithholdingTaxDataCollection`,
`1024` 2 % company/firm or `1023` 1 % individual/HUF, per the vendor card) and the
**attachment** — and `add-draft` it.

Three ways this class differs from the fuel bill above: the posting date is the **bill**
date not the gate date; **all five dimensions** come across from a service GRPO (C-0035 is
the item-GRPO rule); and `U_Recvd_Qty` stays **empty** — it is 0 on all 1,093 lines.
Omitting `DocType` returns `[SAP -5002] Base document type and target document type do
not match`.
