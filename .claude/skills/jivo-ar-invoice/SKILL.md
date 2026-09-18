---
name: jivo-ar-invoice
description: Use when transporter BILTY / G.R. / LR sheets or signed invoice copies arrive and the A/R (sale) invoices must be COMPLETED — attach the bilty scan to each invoice, put the bilty date on the header AND on every line, copy Received Qty from Quantity on every line, and stamp the Received Date. Triggers: "ar invoice", "bilty lagao", "receiving lagao", "attach the bilty", "received qty daal do", "mark these received", "bilty ki entry", a scanned pad of pink bilty copies, a transporter's consolidated bill listing GR.NO against INVOICE NO. Also use to check which A/R invoices are still missing their receiving, or to answer why a bilty number cannot be corrected. NOT for raising the freight GRPO from the same bilty (jivo-oil-freight-grpo / jivo-mart-freight-grpo / jivo-bev-freight-grpo) and NOT for the transporter's A/P invoice.
---

# A/R invoice — completing the receiving from the bilty

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

A transporter's bilty (G.R. / LR) is the paper proof the customer received the
goods. Completing an A/R invoice means **five** things on that invoice:

| # | What | Where it lives |
|---|---|---|
| 1 | the **bilty scan attached** | `OINV.AtcEntry` → `Attachments2` |
| 2 | **Received Qty = Quantity**, every line | `INV1.U_Recvd_Qty` |
| 3 | **Received Date = today** | `OINV.U_Recv_Date` |
| 4 | **Bilty Date**, header **and every line** | `OINV.U_BiltyDate` **and** `INV1.U_BiltyDate` |
| 5 | Bilty number, **only if blank** | `OINV.U_BilltyNumber` |

On the SAP B1 A/R Invoice screen: (1) is the **Attachments** tab, (2) is the
**Received Qty** grid column, (3) is the unlabelled box under Transporter Name on
the right, (4) is the **Bilty Date** header box *and* the **BiltyDate** grid
column, (5) is the **Billty Number** header box.

## Match on the INVOICE NUMBER — never on the G.R. number

The bilty's **`B/L No.`** field carries the JIVO **sale invoice number(s)** that
rode on that truck. That is the key. A G.R. number is only a serial on the
transporter's pad and cannot tell you where it belongs. The transporter's
consolidated bill repeats the same thing as a `GR. NO. → INVOICE NO.` table.

    Date  25/07/26        G.R. No.  3803          B/L No.: 626070522, 523
           ↓                          ↓                     ↓
      U_BiltyDate              U_BilltyNumber       THE INVOICES (the key)

**Both handwritten values are often unclear** — a 2 over a 5, digits running off
the edge of the pad. Zoom before trusting either, and never write a guess:

    python3 .claude/skills/ap-rm-pm/bin/zoom.py <page.png> --box L,T,R,B

One bilty normally carries several invoices (five on one GR is common).
The bilty date is **not** the invoice DocDate — on MAHAVIR bill 677 the bilty
ran a day later (invoice 14/07 → bilty 15/07). Read it off the paper every time.

## 🔴 Order is enforced by SAP — attach FIRST

`SBO_SP_TransactionNotification` refuses out-of-order work:

| Code | Rule |
|---|---|
| `130001002` | **"Please Attach its Receiving"** — `U_Recv_Date` is refused unless the invoice ALREADY has an attachment. **ATTACH FIRST.** |
| `1300013` | **"Please update the received qty"** — with `U_Recv_Date` set, EVERY line needs a non-zero `U_Recvd_Qty`. Send the date and all lines in ONE patch; the guard tests the final state, so a partial write is refused. |
| `1300014` | `U_Recv_Date` must not be earlier than `DocDate`. |
| `1300012` | same shape for dispatch (`U_Disp_Qty` / `U_Dipatch_Date`). |
| `1120025` | Oil only: every attachment line needs `U_CHK` (size KB) + `U_CHK2='OK'`. |
| C-0090 | Not a guard — Daman's rule: every attachment line in every book gets `CopyToTargetDoc='tYES'`. `bin/attach_scan.py` uploads through `sapb1 attach`, which sets it and fails the invoice unless it reads back. |

## 🔴 A wrong bilty number does NOT matter — leave it

**Daman, 2026-09-04: "the bilty number does not matter — we have no relation with
it, let it be wrong."** Nothing downstream consumes it. Report it in one line and
carry on with the receiving, which is the actual job. Never stall over one, never
re-offer to fix it.

It is also **write-once** — six header fields are, all read from `ADOC` (doc
history, `ObjType='13'`) at `MAX(LogInstanc)`:

| Code | Field |
|---|---|
| 1395111 | `U_DriverName` |
| 1395112 | `U_TransporterName` |
| 1395113 | `U_VehicleNoM` |
| 1395114 | `U_BilltyNumber` |
| 1395117 | `U_BiltyDate` (header) |
| 1395118 | `U_Mob_No` |

**NULL → value is allowed. value → anything else is blocked forever**, from this
CLI *and* from the SAP B1 client:

    [SAP -1116] (1395114) Cannot change the Bilty No once updated

The tools fill a blank and never touch a set value. **Never blank-then-rewrite to
defeat the guard** — the comparison ignores NULLs, so it would work, and it is
not ours to do. Getting a wrong one changed is the SAP partner's job at DB level.

## Steps

**1 — Render the scan.** Pages arrive sideways; handwriting needs size.

    python3 .claude/skills/jivo-ar-invoice/bin/render.py "<scan.pdf>" --dpi 200

`--rotate 270` for a consolidated-bill page that comes out sideways. Open **every**
page with the Read tool — a scan is usually page 1 the transporter's bill, then
the individual bilties, then signed invoice copies.

**2 — Build `mapping.json`** from the bill's table, cross-checked against each
bilty's own `B/L No.`. `page` is that bilty's 1-based page in the scan.

    {"source":"<file> — <transporter> bill <no> dt <date>",
     "company":"JIVO_OIL_HANADB", "transporter":"Mahaveer Transport",
     "bilties":[{"gr":"3684","date":"2026-07-15","page":5,
                 "invoices":[626070362,626070363,626070364,626070365,626070370]}]}

**3 — Attach the scan to every invoice.**

    python3 .../bin/attach_scan.py mapping.json --pdf "<scan.pdf>"          # preview
    python3 .../bin/attach_scan.py mapping.json --pdf "<scan.pdf>" --apply

**4 — Mark received** (Received Qty on every line + Received Date, one patch each).

    python3 .../bin/receive.py --from-mapping mapping.json --apply

**5 — Copy the bilty date down onto every LINE.** The step that gets missed.

    python3 .../bin/line_biltydate.py --from-mapping mapping.json --apply

**6 — Bilty number and header bilty date, only where blank.**

    python3 .../bin/attach.py mapping.json --apply

Every tool previews by default and needs `--apply` to send. `receive.py` and
`attach.py` read back what they wrote — an HTTP 204 is not proof.

## Traps — each of these cost real time

- **🔴 `U_BiltyDate` exists TWICE.** Header (`OINV`) *and* the **BiltyDate column
  in the item grid** (`INV1`). The grid is what the operator looks at, so filling
  only the header reads as "not done" on screen. Hand-keyed invoices carry the
  same date in both. The line-level `U_BilltyNumber` and `U_ARNO` on `INV1` stay
  NULL even when hand-keyed — **do not** fill those.
- **Line numbers are not contiguous.** Invoice 626070520 has lines 0, 2, 3.
  Read the real `LineNum` from `INV1`; assuming 0..n silently skips a line and
  then trips guard 1300013.
- **Upload through `sapb1 attach`, never `curl -F`.** (curl read the commas in
  `626070362,363.pdf` as a multi-file separator, and needed `-H "Expect:"` +
  `--http1.1` or a multi-MB scan got `400 {"code": 206, "Bad Post content."}`.
  `sapb1 attach` has neither problem.)
- **One `Attachments2` row per invoice** — never point two documents at one row,
  or a file added later shows on both. Filename = the invoice numbers covered:
  `626070362,363,364,365,370.pdf`. SAP auto-renames on collision; that is fine.
- **An attachment row can never be deleted.** Attach the right file the first time.
- **SAP B1 does not refresh an open document.** After a write, the operator must
  close and reopen the invoice or it still looks empty.
- **C-0038 — never derive the bilty from the freight GRPO** (43.8% reliable; the
  A/R invoice is a later artefact, not an input).
- **C-0073 — search all three books before saying an invoice is not found.**
- Invoice series names the book: Oil `626…`, Mart `706…`/`707…`.
- `NA` is the bilty number when the transporter is **"Jivo Vehicle"** (own truck).

## Cross-book bilties — C-0081

**One bilty can carry Oil AND Beverages invoices** (the LR reads "CARTON OIL AND
WATER"): Beverages is (BEVERAGE UNIT) JIVO WELLNESS PVT LTD, the same legal
entity in a separate company DB, so one bill legitimately spans both books. If an
invoice number off a bilty is not in Oil, **look in Beverages before calling it
missing** (C-0073), and write TWO mappings — one per `company` — for that bilty.
`attach.py` reports a not-found invoice with exactly this hint.

## Which login

USER19 (GURCHARAN), the transport/GRPO desk, one env file per book — passwords
differ per company (C-0031). `bin/_paths.py` finds them, accepting either
`sap-b1/cli/user19-<oil|mart|bev>.env` or the `mahak-user19-*.env` naming.

**The tools run on Mac and on a Windows operator box.** `_paths.py` walks up from
the script to find the checkout (no hard-coded path) and picks the binary by
PLATFORM, not by which file exists — both `sapb1` and `sapb1.exe` are committed,
so an exists-first check picks the wrong one and dies with
`OSError: [Errno 8] Exec format error`. Override the checkout with `$JIVO_REPO`.

## Scale of the backlog

Oil, FY26-27, non-cancelled — 3,110 invoices (measured 2026-09-04):

| Missing | Count |
|---|---|
| bilty number | 926 |
| bilty date | 978 |
| **attachment** | **1,744** |
| **receiving (no `U_Recv_Date`)** | **1,881** |

The receiving backlog is the one that matters. Receiving cannot be stamped
without an attachment, so those 1,744 need their paper scanned first.

## Proven

2026-09-04, MAHAVIR TRANSPORT bill 677 (7 bilties, 16 Oil invoices, Jul-2026):
12 scans attached, 12 invoices received, 19 lines given the bilty date —
**0 failures, on posted and CLOSED invoices**. Attaching and receiving both work
on a closed A/R invoice; only the six "who carried it" header fields are frozen.
