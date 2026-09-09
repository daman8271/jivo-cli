---
name: jivo-cancel-document
description: USE AUTOMATICALLY when an operator wants a POSTED SAP document undone — "cancel this invoice", "delete this bill", "delete this post", "cancel the GRPO", "reverse this", "void it", "this entry is wrong, remove it", "cancel kar do", "galat entry hata do", "yeh bill hata do" — including when they only hand over a document number and say it is wrong. Covers the 14 marketing documents (invoice, credit note, delivery, return, A/P invoice, A/P credit note, GRPO, goods return, order, quotation, PO, purchase quotation, and both down payment invoices) the way right-click → Cancel does in SAP B1: SAP posts a reversal, nothing is deleted. Also use to explain what already cancelled a document. NOT for drafts (that is `delete draft`), and payments and journal entries cannot be cancelled from here at all.
---

# Cancel a posted document

**Cancelling is not deleting.** SAP has no delete for a posted document — not in the
client, not from here. What it has is Cancel: for an invoice, credit note, delivery,
return, A/P invoice, GRPO or down payment, SAP posts a **second document, the
reversal**, that undoes the stock, the ledger and the GST, and marks the original
Cancelled. An order, quotation or PO posts nothing, so it only flips to Cancelled.
Either way **two documents end up in SAP, nothing disappears**, and nothing here can
undo it afterwards.

Say that to the operator in those words. "Delete" is what they asked for; it is not
what happens.

## 🔴 The reversal carries the ORIGINAL's posting date

Not today's. A June invoice cancelled in September posts its reversal **in June** —
June's books and **June's GST return**, which has been filed. The preview says the
period out loud:

```
reversal: SAP will date the reversal 2026-06-14 (period Jun 2026)
```

**Read that month to the operator before they confirm.** Past 45 days the command
refuses anyway (`--older-than`) — the same warning in a harder form.

## 🔴 You cannot type `yes` for them, and must not try

The prompt needs a person at a terminal and this AI's shell is not one. For a
document a person keyed in the SAP B1 client — **the normal case here** — `cancel`
refuses without `--not-created-here`, and that flag cannot be combined with `--yes`
by design. So the job is: **prepare the exact command, show the dry-run preview, and
hand them the line.** They paste it into their own Command Prompt (or terminal) and
type `yes` themselves.

Never add `--yes` to a `--not-created-here` command. Never look for another way
round the prompt.

## 1. Is it actually a posted document?

| What they have | Where it goes |
|---|---|
| a DocNum off a printed/Added document, or anything in the books | this skill |
| a draft (Document Drafts, a DocEntry from `sapb1 draft`) | `sapb1 delete draft <DocEntry>` — a different command |
| an incoming or outgoing payment | **not possible here.** Cancelling a payment is a person's job in Banking |
| a journal entry | **not possible here.** |

Say "that one cannot be done from the CLI" plainly, and say where it is done
instead. Do not go hunting for a workaround.

## 2. Find it in all three books before saying "not found" (C-0073)

A DocNum is unique inside one company only.

```bash
for db in JIVO_OIL_HANADB JIVO_MART_HANADB JIVO_BEVERAGES_HANADB; do
  sapb1 query PurchaseInvoices --filter "DocNum eq 626084329" \
    --select "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,Cancelled,CancelStatus" \
    --company "$db"
done
```

Swap the entity for the right one (`Invoices`, `CreditNotes`, `PurchaseDeliveryNotes`,
`Orders`, …). Already `Cancelled tYES` → it is done; name what cancelled it instead
of running anything (`cancel … --dry-run` finds and prints the reversal for you).

## 3. Dry-run it, and read the preview back to them

```bash
sapb1 cancel purchase-invoice 45140 --company JIVO_OIL_HANADB --dry-run
```

This dry-run **does** contact SAP — reads only — and runs every guard against the
real row. Read out: the party, the total, the bill number, the posting date, **the
reversal's period**, and any warning (paid, drawn into a later document, closed —
SAP refuses those itself).

## 4. Their word on THAT document, then hand over the command

Exit 9 naming `--not-created-here` is the **expected** answer for a document a person
keyed. It is not a fault and not something to route around. Ask plainly: *"a person
keyed this in SAP B1 — do you want it cancelled anyway?"* If they say yes, give them
the line to run:

```
sapb1 cancel purchase-invoice 45140 --company JIVO_OIL_HANADB --not-created-here
```

One document, one command, one `yes`. Their answer covered one document, so the
command does too.

## 5. Report both documents

Say it back: the original is now **Cancelled**, the reversal is DocEntry/DocNum
dated *that* date in *that* period, and **nothing was deleted — SAP posted a
reversal**.

- **exit 8** — probably cancelled, not verified. Go and look
  (`sapb1 query <Set> --filter "DocEntry eq <n>" --select "DocEntry,Cancelled,CancelStatus"`).
  Do not re-run.
- **exit 7** — sent, no answer came back. Run the query in the message before
  anything else.
- **exit 6** — SAP refused it: paid, drawn into a later document, a locked period.
  Nothing was posted. Repeat what SAP said.

## 6. Never

- **never loop** over a list of documents — one per run, by construction
- **never `post` or `patch` a `Cancelled` / `CancelStatus` field** to fake a cancel
- **never** switch login, `.env` or checkout to get past a guard — the drafts-only
  desk refusal has no flag on purpose, and a second login is the thing it exists to
  stop. The shared-login refusal has exactly one door, `--shared-login <login>`
  (Daman, 2026-09-05: "you will not do it yourself; if I say so, you will") — relay
  it only when he or the operator has said, about this run, to cancel as that login,
  and say that the reversal will name no person
- **never** suggest `--not-created-here`, `--other-operator`, `--older-than` or
  `--shared-login` as your own idea. Each is a sentence the operator says; you only
  relay it
- **never** promise a cancel for a payment, a journal entry or a draft
