# The approval mail print — what it is, and how to read it

Recorded 2026-08-25 from Daman, on the CHANCHAL CHEMICALS TRADING advance
(Beverages draft 296, ₹24,780). **This is the file that goes on an outgoing
payment** (C-0028). Not the vendor's bill.

## What the operator hands you

A PDF printed straight out of the accounts mailbox — Gmail's own
"download / print to PDF" of the whole thread. It is recognisable on sight:

- filename is the subject line: `Re_ <subject>.pdf` (Gmail turns `:` into `_`)
- a running header on every page: `<date>, <time>` · subject · page `n/m`
- top-right shows the mailbox it was printed from — `accounts007 <accounts007@jivo.in>`
- footer reads `about:blank` (a browser print, not a mail-server export)
- the thread runs **newest first**, with the older messages quoted beneath, so
  the APPROVAL is at the top and the REQUEST is at the bottom
- it is usually 2+ pages — **the request is often on the last page**

**Read it end to end, bottom page included.** The top of page 1 may be nothing
but the word "Ok"; the amount, the purpose and the company live at the bottom.

## What to pull out of it

Worked example — `Re_ Advance payment to CHANCHAL CHEMICALS TRADING.pdf`:

| Field | Where it came from |
|---|---|
| amount ₹24,780 | request, last page: "Please pay advance Rs.24780/-" |
| shape = ADVANCE | the word "advance" in the request |
| **company = Beverages** | "for purchase chemical for **beverage plant use**" |
| purpose | "as per requirement by Jasmeet ji" |
| requester | Vishal Tyagi (Bakharpur) `bakharpuraccounts@jivo.in`, Sat 22-Aug 12:59 |
| approver 1 | **Arvinder Singh**, Sat 22-Aug 2026 13:49:26 — "Ok, approved." |
| approver 2 | **Bhupinder Singh**, Tue 25-Aug 2026 12:24:22 — "Ok" |

**Dual approval is the norm, and it is sequential** — the request names both
people ("Arvinder Singh Please give your approval / Bhupinder Singh Please give
your approval") and each replies in turn, often days apart. A thread with only
one of the two named approvals is **not yet approved** — say so and stop.

"Ok" on its own IS the approval. Do not hold out for the word "approved".

## Why it corroborates

The mail is a second independent source for the figures (skill §1: corroborate
every number twice). On this entry it agreed with the PO on all three of amount,
shape and company without being derived from it. When the mail and the PO
disagree, **stop and ask** — do not average them or prefer one silently.

## Attaching it

Mail is **line 1**, the PO rides as **line 2**, both on the draft's own
`Attachments2` row. Rename before upload so the file cannot collide on the
share:

    CHANCHAL-ADV-24780-MAIL-25.08.2026.pdf     <- <vendor>-<what>-<amount>-MAIL-<date>
    CHANCHAL-PO-826228022-20.08.2026.pdf       <- <vendor>-PO-<docnum>-<date>

Recipe: `jivo-ap-draft/reference/attachments-upload.md`. Beverages lands on
`\\10.10.101.52\Attachments_Bev\JIVO_BEVERAGES\Attachments`. Stamp `U_CHK`
(size KB), `U_CHK2` = `OK` and `CopyToTargetDoc` = `tYES` (C-0090) on **every** line (C-0026) — JIVO's 1120025
"Select OK in Approve Column" guard refuses the Add otherwise.
