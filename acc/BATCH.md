# `acc batch` — many A/P invoice drafts from open goods receipts

For the pile, not for one bill. It reads JIVO's open GRPOs, works out which ones
can become A/P invoice drafts, and gives you **an Excel file to review**. You
tick the rows you want. It then creates those drafts in SAP.

**Nothing it makes is posted.** Every row becomes a *draft*. A person opens SAP
B1 → Document Drafts, looks at it, and presses **Add**. Until somebody does
that, no stock moves and no ledger entry exists.

One bill in your hand right now? Use the `jivo-ap-draft` skill instead — ask
Claude to "make a draft of this invoice" and hand it the PDF.

---

## The three commands

```
scan     read SAP, write a review workbook          (never writes to SAP)
send     read the workbook back, create the drafts  (previews unless you add --yes)
status   what happened to a batch                    (reads disk, not SAP)
```

### Windows (operator boxes)

```bat
cd C:\Users\<you>\Documents\jivo-cli
acc\acc.cmd batch scan --company Oil --limit 50
acc\acc.cmd batch send "acc\_batches\B260824-OIL-7F3A\review-B260824-OIL-7F3A.xlsx"
acc\acc.cmd batch send "acc\_batches\B260824-OIL-7F3A\review-B260824-OIL-7F3A.xlsx" --yes
```

### Mac / Linux

```bash
cd ~/jivo-cli
python3 acc/acc.py batch scan --company Oil --limit 50
python3 acc/acc.py batch send "acc/_batches/B260824-OIL-7F3A/review-B260824-OIL-7F3A.xlsx"
python3 acc/acc.py batch send "acc/_batches/B260824-OIL-7F3A/review-B260824-OIL-7F3A.xlsx" --yes
```

Off the office network first: `bash connections/sap-home-bridge.sh`, then
`export SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000`.

---

## 1. Scan

```
acc batch scan --company Oil|Mart|Beverages [--since YYYY-MM-DD] [--vendor X]
               [--group TRANSPORTER] [--limit 50] [--order oldest|newest]
               [--include-intercompany] [--allow-service] [--env <you>.env] [--out DIR]
```

* `--since` defaults to 90 days back. `--limit 0` means every matching row.
* `--env navdeep-user36.env` decides **whose login the drafts land under**. The
  scan prints it; so does the About sheet. If it is not your name, stop.
* Everything lands in `acc/_batches/<batch id>/`:
  `review-<id>.xlsx` (yours), `sidecar-<id>.json` (the payloads — do not edit),
  `journal-<id>.jsonl` (what happened, appended to for ever).

A scan is read-only by construction. If SAP goes away halfway through, it writes
**nothing** — a half-finished workbook looks complete, and its missing rows look
like rows that were checked and found to need nothing.

---

## 2. Review — the only part that is yours

Open `review-<id>.xlsx`. Three sheets: **Review** (one row per goods receipt),
**Lines** (the detail behind each row), **About** (who, what, when, and this
legend).

**Type only in the yellow cells. Everything grey is checked against SAP again
before anything is sent, and a changed grey cell makes the row refuse to send.**

| Yellow cell | What to put in it |
|---|---|
| **V Approve?** | `yes` on every row you want drafted. Blank = skip. |
| **W TDS (yes/no)** | usually prefilled. **Blank means the evidence contradicts itself — read column Q and answer it yourself.** The row will not send while it is blank. |
| **X Vendor bill date** | the date printed on the vendor's invoice (`TaxDate`). Prefilled from the GRPO; column S says whether that is trustworthy. |
| **Y Vendor ref** | the invoice number exactly as printed (`NumAtCard`). |
| **Z Note** | anything extra for Remarks (gate entry, vehicle, e-way bill). |

Yellow cells only appear on **READY** rows. On any other row V–Z are grey and
locked, because those rows cannot be sent whatever you type in them.

### Status column (T)

| Status | What it means |
|---|---|
| `READY` | a draft can be built. Approve it and it will be sent. |
| `DUPLICATE` | already in SAP — a posted invoice, or an open draft on this GRPO or this reference. The reason names the DocEntry, the user and whether it is waiting for approval. **Never send.** |
| `REF-COLLISION` | two rows of **this batch** carry the same vendor reference: one bill received twice. Both are held. Find out which goods receipt it belongs to. |
| `NEEDS-REF` | the GRPO has no vendor reference. Fix the GRPO, or do that one bill with the `jivo-ap-draft` skill. |
| `SERVICE-HOLD` | a service GRPO (transporters). That draft shape has not been proved on live SAP yet, so the batch will not build one. |
| `CANNOT-BUILD` | see the Reason column. Frozen vendor, closed period, unknown numbering series, no open lines. |

Intercompany GRPOs (JIVO billing JIVO, correction C-0020) are left out of the
sheet entirely unless you pass `--include-intercompany`.

### Two things about the money columns

* **Taxable / Tax / Gross are the OPEN part**, not the whole goods receipt. If
  half a line was invoiced last month, the batch bills the half that is left and
  the sheet shows that half. Column J marks such lines `open 100/500` and column
  U says "partially billed earlier".
* They are real numbers with Indian grouping, so they still add up in Excel.

Save as **.xlsx** (not .csv — it would lose the sheets and the leading zeros).

---

## 3. Send

```
acc batch send <workbook.xlsx> [--yes] [--dry-run] [--resume] [--max-age-days 3] [--env <you>.env]
```

**Without `--yes` it previews**: every approved row is re-checked against live
SAP and dry-run through `sapb1`, and nothing is sent. Read the preview. Then run
it again with `--yes`.

Before it sends anything at all it refuses the whole run if: the workbook and
the sidecar are from different batches, rows were added or deleted, the sidecar
is older than `--max-age-days` (3), or the CLI resolves to a different company
than the scan used.

Per row, immediately before that row's draft:

* the goods receipt is read again — still open, still that vendor, still that
  open quantity (exactly), and its bill attachment as it is *now*;
* SAP is asked whether anybody has keyed this bill since the scan (by reference,
  posted and drafted, and by GRPO);
* the vendor card is checked for frozen/invalid.

Anything that has moved makes the row `STALE` or `STALE-DUPLICATE`, and it is
not sent.

The duplicate questions are asked two ways, because one is not enough: SAP is
asked for the reference by name (it matches `NumAtCard` exactly, so `2633100542`
does **not** find `.2633100542`), and everything the vendor has open or recently
posted is compared here, normalized — which is what catches the same bill typed
with a dot, a space or a leading zero. Every one of those sweeps reads **all**
the rows, not the first page.

### What each outcome means

| Outcome | Meaning |
|---|---|
| `SKIPPED` | not approved. |
| `REFUSED-STATUS` | you approved a row the scan had held. |
| `TAMPERED` | a grey cell no longer matches the sidecar. The message names the cell and both values. |
| `INVALID-INPUT` | a yellow cell is empty or unusable (blank TDS, empty reference, a bill date in the future or a year off). |
| `PREVIEWED` | dry run only. Nothing was sent. |
| `CREATED` | draft made and read back clean. |
| `CREATED-WITH-GAPS` | draft made, and something needs you in the client — usually **TDS came out 0** (C-0018: tick WTax Liable on every row before Add) or the attachment pointer could not be set. |
| `REJECTED` | SAP said no. **Nothing was committed.** Fix it and run again. |
| `STALE` | SAP moved on since the scan — the goods receipt was closed, cancelled, re-vendored, or its open quantity changed. |
| `STALE-DUPLICATE` | somebody keyed this bill between the scan and now: a posted invoice or an open draft carries this reference (however it is spelled) or is already drawn from this goods receipt. |
| `UNKNOWN` | the request went out and no answer came back — or came back without saying which draft it made. **Go look. Do not re-run it.** See below. |
| `UNKNOWN-UNRESOLVED` | `--resume` looked and could not settle it. Never re-sent from this batch; a person decides. |
| `FOREIGN-DRAFT-FOUND` | `--resume` found a draft for this bill that **this batch did not make** (somebody keyed it in the client). It is not adopted, not patched and not re-sent — the message names the DocEntry, the owner and the approval status. |
| `CREATED-RECOVERED` | `--resume` found the draft an unknown outcome had left behind, with evidence that this batch made it, and adopted it. |
| `NOT-ATTEMPTED` | the run halted before this row. |
| `ALREADY-CREATED` | this batch already made that draft. |

Exit codes: `0` everything fine · `1` finished, some rows need attention ·
`2` the workbook/sidecar was refused · `3` login/config · `4` SAP unreachable ·
`7` halted on an unknown outcome. **A halt at `4` or `7` always names the drafts
the run had already created** — it never tells you nothing was sent when
something was.

### When a row comes back UNKNOWN

The batch **stops**. Nothing after that row is attempted, and that row is never
re-sent from this batch — a re-send is how one bill becomes two invoices. Until
it is settled, no later run of this batch will send anything either (it halts at
exit 7 and tells you to look).

1. Look in SAP B1 → Document Drafts for that vendor and reference.
2. Then: `acc batch send <workbook> --resume --yes`

**`--resume` never sends a draft. It looks.**

* On its own it looks and reports, and writes nothing at all.
* With `--yes` it settles the unknown rows **first**, before any other row of
  the batch is sent. Only if every one of them is settled does the rest of the
  run go ahead; if any is still unaccounted for, nothing else is sent (exit 7,
  or exit 1 for a foreign draft).

A draft is only adopted with **evidence that this batch made it**: the batch id
in its Remarks, or the draft belonging to this login *and* drawn from this goods
receipt. Matching on the vendor reference alone is not evidence — Accounts keys
bills in the client all day, and the halt is exactly when they do. So: exactly
one draft with evidence → adopted (`CREATED-RECOVERED`); a matching draft
without evidence → `FOREIGN-DRAFT-FOUND`, untouched; none → `UNKNOWN-UNRESOLVED`,
and you decide; more than one → it names them and refuses to choose.

---

## 4. Status, and the audit trail

```
acc batch status <workbook.xlsx>
```

Reads the journal and the sidecar — no SAP — and prints what the scan found,
every send run, what each row produced, and any row that was sent and never
answered.

Every write also lands in the shared write log, keyed by the batch id, which
travels in the draft's Remarks:

```bash
grep B260824-OIL-7F3A queries/*/sap-writes.jsonl
```

The same token is searchable in SAP's own Remarks field.

---

## 5. If a batch was wrong: removing its drafts

A draft costs nothing to leave alone — it is not in the books. But a batch sent
against the wrong branch, or the wrong month, leaves a pile nobody wants, and
they can be removed:

```
sapb1 delete draft <DocEntry> [<DocEntry> …]      # up to 50 at a time
```

It reads each draft first and shows you what you are about to destroy, refuses
any draft this CLI did not create, needs a typed `yes`, logs a snapshot of what
was there, and reads back to confirm it is gone. `--dry-run` there does talk to
SAP: it *reads* the drafts so the preview shows the real documents, and sends no
DELETE.

Get the DocEntry list from the results workbook (`Draft DocEntry` column) or
from `acc batch status`.

Two exit codes are specific to it: **8** = deleted but the read-back could not
confirm it (probably gone — check Document Drafts; re-running is safe), **9** = a
guard refused (provenance, age, an attachment, someone else's draft). A `9` is a
"go ask the operator to say it out loud" signal, not something to flag away.

**A posted document can never be deleted from here.** Once somebody presses Add
in the client, only SAP can undo it.

---

## What this cannot do

* **Service GRPOs** (the transporters, 229 of the 609 open ones) — held as
  `SERVICE-HOLD` until one has been proved by hand.
* **Post anything.** Drafts only, always.
* **Fix a GRPO.** No vendor reference on the goods receipt means somebody has to
  put one there, in the client.
* **Decide TDS for you** when the vendor's own history contradicts the vendor
  master. That is the blank W cell, and it is deliberate.

## Files a batch leaves behind

```
acc/_batches/<batch id>/
  review-<id>.xlsx           the workbook you review
  sidecar-<id>.json          the payloads + the locked values (do not edit)
  journal-<id>.jsonl         append-only: every event, before and after each write
  payloads/<docentry>.json   the exact bytes sent for each row
  dryrun-<run>.txt           what the preview showed
  results-<id>-<run>.xlsx    outcome per row, with draft numbers and flags
```

`acc/_batches/` is gitignored: it carries vendor names, bill references and
amounts, and this repository is public.
