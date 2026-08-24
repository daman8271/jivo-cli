---
name: jivo-ap-service-draft
description: Use when an operator hands over a vendor bill that has NO goods receipt (GRPO) behind it and wants it entered in SAP B1 as an A/P invoice draft — fuel / petrol pump / diesel bills, transporter / freight / bilty / lorry bills, courier, electricity, water, rent, AMC, repair, professional or any service / expense bill — "book this bill", "enter this expense", "fuel bill entry", "transport bill draft". Also use when jivo-ap-draft's precheck exits 3 with "no GRPO". Not for item purchases with a GRPO (jivo-ap-draft) or vendor credit notes (jivo-ap-credit-memo).
---

# A/P draft for a service / expense bill — no GRPO (JIVO, SAP B1)

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

1. **Read the paper into facts.** Vendor + GSTIN (verify against the BP master — scans
   misread digits: Om Sai's "600?31" was `6065G1`) · bill no. exactly as printed →
   `NumAtCard` · bill date · billing period · **JIVO gate stamp G.No + date** · **every
   row: date, vehicle / bilty / meter, item, qty, rate, value** · discount and its
   basis · round-off · NET TOTAL · GST or none · every handwritten approval.
2. **Duplicate gate — hard stop.** `Drafts` where `NumAtCard eq '<ref>'` (any doctype);
   sweep the vendor's drafts with `--all` (Om Sai had 94) and its posted
   `PurchaseInvoices` by `NumAtCard` **and** by `DocDate` in the bill's month. Any hit →
   stop, report paper-vs-record, create nothing. Run `jivo-ap-draft`'s precheck anyway:
   its ref scan is a second opinion and exit 3 confirms "no GRPO" — a GRPO comment
   mentioning the same number can be a *bilty* number on another vendor (it was).
3. **Pull the precedent** — the vendor's last 3 posted `PurchaseInvoices` in full
   (`--all --json`, then the one with `DocumentLines`). Write down every non-null
   field; that list is the payload's spec. What it decides:

   | Field | What precedent tells you | Om Sai (fuel) |
   |---|---|---|
   | `DocType` | `dDocument_Service` for expense bills | service |
   | `Series` + `DocumentSubType` | the **flavour** (non-GST `HR_B` + `bod_None` vs GST `HR_G` + `bod_GSTTaxInvoice`); then find **this month's** number for that flavour and branch (`reference/series-and-errors.md` in jivo-ap-draft; confirm with what Aug-26 posted docs of that flavour carry) | 3324 HR_B0826 + bod_None |
   | `BPL_IDAssignedToInvoice` | the branch precedent uses | 2 FACTORY |
   | `GSTTransactionType` | copy | `gsttrantyp_BillOfSupply` (petrol/diesel are outside GST) |
   | `WTLiable` / TDS | **precedent beats the master flag**; transport vendors are often 194C — check the last 3, report both, follow precedent | master `boNO`, all 3 posted TDS 0 → none |
   | line `AccountCode` | per head: fuel-vehicles / generator / conveyance / freight … | 5650015 / 5680001 / 5690002 |
   | line `CostingCode`…`CostingCode5` | copy per vehicle/unit; **`CostingCode3` (Budget) is mandatory** — guard 1120009 "Please select Budget" rejects the POST without it | FACT_COM / Del Bkhp; `CostingCode5` HR |
   | line `LocationCode` | copy — **2 = Bhakharpur factory = the Haryana place-of-supply the client shows**; empty = empty on screen (C-0025) | 2 |
   | line `U_Recvd_Qty` | **the paper's per-row qty lives here** — service rows have no Quantity column in the client, so litres/kg/km would otherwise vanish (C-0025) | litres per vehicle |
   | line split | one line per vehicle / bilty / meter, as precedent does | 6 lines |

4. **Build the lines so nothing on the paper is lost.** Every paper column lands in some
   field: qty → `U_Recvd_Qty`; vehicle/bilty → the dimension precedent uses; period,
   gate no., approvals → `Comments`. Decode discounts from the arithmetic, never from the
   label: Om Sai's "Discount @ 0.50" is **₹0.50 per litre on diesel only** (549.689 L ×
   0.50 = the printed 274.84) — net it onto the diesel lines, nothing on petrol. Absorb
   the paper's round-off into the largest line so **Σ lines = NET TOTAL exactly**.
5. **Dates:** `DocDate` = gate-stamp date (C-0017), `TaxDate` = bill date, omit
   `DocDueDate`. Precedent normally agrees (Om Sai July: 07-18 / 07-15); if it doesn't,
   follow C-0017 and say so.
6. **Comments** (≤254): `Bill <ref> dt <date> period <a-b> | GATE ENTRY NO <n> dt <date> |
   <qty summary: Petrol 110.150 Ltr Diesel 549.689 Ltr> | <approval as written>`.
7. **Dry-run → operator's go → `--yes`:**
   `acc/_playbook/sap draft purchase-invoice --dry-run --data-file <payload.json>` then
   `--yes`. Exit 7 = look, don't resend. A 400 with `1120009` = add `CostingCode3`; with
   `-10`/`-4002` = wrong series/subtype flavour.
8. **Attach the scan** — `jivo-ap-draft/reference/attachments-upload.md` (steps 1, 4, 5,
   6; there is no base document to copy). Stamp `U_CHK2 OK` or the pointer is refused.
9. **Read back:** `readback.py <DocEntry> --expect-total <net>` — its "not drawn from a
   GRPO" flags are a **false positive for this document class**; say so. Then verify by
   query: `DocTotal` exact, every line has `LocationCode`, `CostingCode3`, `U_Recvd_Qty`,
   Σ `U_Recvd_Qty` = the paper's qty total, `GSTTransactionType`, `AttachmentEntry`.

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

## Transport / freight bills — first one through here extends this file

Not yet exercised. Expect: one line per bilty/LR with the bilty no. in the dimension or
`Comments`, freight accounts under 5650xxx, weight/km in `U_Recvd_Qty`, and **TDS 194C is
likely** — the precedent check in step 3 decides, never the assumption. Add the worked
example here after the first live draft.
