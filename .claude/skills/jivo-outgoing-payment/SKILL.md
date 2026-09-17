---
name: jivo-outgoing-payment
description: Use when an operator wants a payment to a vendor entered in SAP B1 — "punch this payment", "make a payment draft", "pay this vendor", "advance payment", "payment to X", an approved payment-request mail, or a bank/ledger screenshot of what is owed. Covers both shapes: an ADVANCE against a contract/PO (on-account) and a SETTLEMENT of open bills (applied to invoices). Also use to check whether a payment is already in SAP, or why a payment draft cannot be deleted.
---

# Outgoing payment draft (JIVO, SAP B1)

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

Internal skill for the jivo-cli toolkit. Built 2026-08-25 from live entries:
AWL AGRI BUSINESS ₹1,25,04,080 (advance, on-account), DHANLAXMI EDIBLES
₹74,45,802 (advance), ASHOK KITAB GHAR ₹6,868 (bill settlement), and
**CHANCHAL CHEMICALS TRADING ₹24,780 — the first Beverages payment ever made
from this CLI** (draft 296, both papers attached), and **PYRUM ENGINEERS
₹3,00,000 — the entry that broke three of the rules below and rewrote them**
(2026-08-31, live payment 5872 / draft 298). Every rule below was measured
against Oil's 14,851 posted payments, not assumed.

**Core principle: a payment is not keyed from the paper — it is CLONED from the
same vendor's most recent posted payment, and deduplicated against the MONEY,
not against a document number.** RULE 0 in `CLAUDE.md` governs the write.

**Sibling skills.** This one moves money out. For the *bill* that money pays,
see `jivo-ap-draft` (goods through the gate), `jivo-ap-service-draft`
(fuel/freight/expenses), `jivo-ap-credit-memo` (vendor credit note).

---

## 0. Which shape is this? Decide first — it changes the payload

| | **ADVANCE** | **SETTLEMENT** |
|---|---|---|
| Trigger | a contract / PO, "advance payment", goods not yet received | an open bill, a ledger row showing what we owe |
| Applied to | **nothing** — on-account | the specific open A/P invoice(s) |
| `PaymentInvoices` | **absent** | **present**, one row per invoice |
| `U_Adv_Settl_Dt` | set (usually month-end) | **absent** |
| Typical bank | `2201101` / `2201106` | `1104107` / `1104104` |
| Typical mode | RTGS | NEFT |

**On-account is normal, but it is not the majority any more.** Measured Oil,
August 2026, `DocType eq 'rSupplier'`: **148 of 364 settle nothing (41%)**. The
often-quoted 58% came from a 365-day window across *all* `DocType`s — do not
repeat it for a vendor payment. Re-measure the current month before leaning on
either number.

> ### ⚠️ A lone on-account precedent does NOT mean "this vendor gets on-account"
> An unapplied payment is very often an **advance still waiting to be netted off**
> by a later settlement — not a house style. PYRUM's two June Oil payments both
> read `PaymentInvoices: []`, which looked like a settled habit; the real August
> entry was a settlement that *consumed* two such advances. Before copying a
> precedent's shape, ask what happened to it afterwards.

### SETTLEMENT — the Contents page (operator correction, 2026-08-25)

When settling bills, the payment must pick up the business partner's open items:

> **Contents page → `Display` = "Transactions for Business Partner" → select all.**

Do not hand-pick one row you happened to find. Pull the BP's open transactions and
tick them, so nothing open is silently left behind. Via the API that means:
fetch **every** open item for the `CardCode` and put **each** in `PaymentInvoices` —
never just the one that matches the amount you were quoted.

```bash
# every open item for the vendor — this is the "select all" list
hana-sql 'SELECT "DocEntry","DocNum","DocDate","DocTotal","PaidToDate"
          FROM "JIVO_OIL_HANADB"."OPCH"
          WHERE "CardCode"=<code> AND "DocStatus"=''O'' AND "CANCELED"=''N'''
```

Mind **C-0019**: `DocStatus='O'` is unreliable at JIVO — documents settled by
journal entry stay open. Cross-check the total against `OCRD."Balance"`. If the
open items do not add up to the balance, say so before writing.

### "Select all" includes the vendor's ADVANCES — as NEGATIVE rows

> **Proven live 2026-08-31 on Beverages payment 5872 (PYRUM ENGINEERS).** This is
> the single most-missed thing about a settlement, and it is invisible until you
> read a real posted payment's `PaymentInvoices`.

A settlement does not only tick open bills. It also picks up the vendor's
**unapplied on-account payments** and nets them off in the same document, as rows
with `InvoiceType: "it_PaymentAdvice"` and a **negative** `SumApplied`:

| `InvoiceType` | `DocEntry` | `SumApplied` |
|---|---:|---:|
| `it_PurchaseInvoice` | 12545 | **+7,46,055** |
| `it_PurchaseInvoice` | 12972 | **+2,03,945** |
| `it_PaymentAdvice` | 35326 | **−3,00,000** |
| `it_PaymentAdvice` | 35976 | **−3,50,000** |
| | **net** | **₹3,00,000** = `TransferSum` |

**`TransferSum` is the NET, not the sum of the bills.** Bills 9,50,000 minus
advances 6,50,000 = the 3,00,000 that actually leaves the bank. Get this wrong and
you pay the advances a second time.

The two negatives are that vendor's earlier May payments (₹3,00,000 on 05-May,
₹3,50,000 on 18-May) being consumed. `DocLine` is **1** on an advice row and `0`
on an invoice row. `U_Adv_Settl_Dt` is **absent** — it belongs to the advance, not
to the settlement that eats it.

So the real "select all" list is **open bills (positive) + unapplied advances
(negative)**, and the arithmetic must close before you send:

```bash
python3 -c "import json;d=json.load(open('pay.json'));\
t=sum(r['SumApplied'] for r in d['PaymentInvoices']);\
print('net',t,'vs TransferSum',d['TransferSum'],'->',t==d['TransferSum'])"
```

**SAP refuses a re-application**: pointing at a bill another payment already closed
returns `[SAP -10] Invoice is already closed or blocked [Message 3524-20]`. That
error means the settlement has already been made — go find it before doing anything
else.

---

## 0.5 Which COMPANY, and which LOGIN — settle both before the payload

Two separate questions. Getting either wrong is invisible until after the write.

### The paper names the company (C-0030) — but WHICH paper

**The company comes from what the mail SAYS THE MONEY IS FOR, in words.** JIVO's
POs print it in the header (`ONLY FOR BEVERAGES`); the approval mail says it in a
sentence ("for beverage plant use", "work completion on beverage line for which
this payment will be released"). **If nothing names a company, the entry is Oil.**

> ### ⚠️ A ledger screenshot names the VENDOR, not the COMPANY
> **Learned the hard way, 2026-08-31 (PYRUM ENGINEERS).** The request said *"As per
> sap ledger please pay Rs.250000"* with a screenshot showing `VENDA001678 …
> −250,000.0000`. That code is **Oil's** PYRUM, and Oil's balance really was
> −2,50,000 — so the screenshot corroborated itself perfectly. **The payment was
> released from BEVERAGES** (`VENDA001364`, ₹3,00,000, payment 5872).
>
> The requester attached the wrong book's ledger as "reference". A CardCode is
> exact, machine-readable and *therefore very convincing* — which is precisely why
> it misleads. **Rank the sentence above the screenshot.** When they disagree, stop
> and ask; do not let the precise-looking artefact win.

> **The same vendor is a DIFFERENT CardCode in each company book.** CHANCHAL
> CHEMICALS TRADING is `VENDA001306` in Oil and `VENDA001062` in Beverages —
> same GSTIN, same name, unrelated codes and unrelated balances. Never carry a
> CardCode across companies, and never answer a balance question without saying
> which company it came from.

`sapb1` defaults to Oil. Every command for another company needs `--company
JIVO_BEVERAGES_HANADB` / `JIVO_MART_HANADB` — reads, the draft, the patch, the
delete, all of them.

### SAP passwords are PER COMPANY DB (C-0031)

The same user code has a different password in each company book.

```
USER05 + Oil password  →  JIVO_OIL_HANADB         connected
USER05 + Oil password  →  JIVO_BEVERAGES_HANADB   Fail to NONE-SSO login from SLD
USER05 + "1234"        →  JIVO_BEVERAGES_HANADB   connected
```

> **`Fail to NONE-SSO login from SLD` means WRONG PASSWORD for that company.**
> It does NOT mean the user lacks a licence or is unassigned. This message cost a
> whole session: it was read as a licence block, and the operator was told an SAP
> admin had to assign the user — when all that was needed was that company's
> password. **Ask for the company's password before declaring anyone blocked.**

The `*.env` files next to `sapb1` are per-operator and Oil-shaped. For another
company override the two fields that change, and never echo the password:

```bash
export SAPB1_COMPANYDB=JIVO_BEVERAGES_HANADB SAPB1_USER=USER05 SAPB1_PASSWORD='…'
./sapb1 doctor          # ALWAYS run this first — one line, and it settles the login
```

`doctor` before the payload, every time you change company or user. It is the
cheapest possible check and it turns a confusing write failure into a one-line
login answer.

---

## 1. Read the request — and read the numbers at full resolution

The request arrives as mail in the accounts mailbox. Use `mail-cli/jmail`
(read-only: never sends, flags, moves or deletes).

```bash
cd mail-cli
./jmail doctor                                   # creds + connectivity
./jmail search --subject "<vendor>" --limit 10
./jmail show <uid>                               # read the WHOLE thread
./jmail pull <uid> --out bills/<name> --types pdf,png,jpeg,jpg
./jmail print <uid> --out bills/approval-mails/    # the PDF that goes ON the draft (§6)
```

Establish, from the thread: **vendor · amount · what it is for · who approved it
and when.** An unapproved request is not an entry — find the "Ok, approved" and
name the person.

**Payment approval threads live in `accounts007@jivo.in`**, not the logistics
mailbox. Use the wrapper `mail-cli/jmail-acc7` (same read-only jmail, mapped onto
`ZOHO_MAIL_ACCOUNTS007_*`). `mail-cli/jmail` itself points at logistics.

> ### The APPROVER's figure beats the requester's ask
> **Proven 2026-08-31.** Vishal requested **₹2,50,000**; Arvinder Singh replied
> *"Ok, approved.3lac"*; the entry that was made is **₹3,00,000**. The request is a
> proposal — the approval is the authorisation, and the money follows the approval.
> When the two differ, say so out loud and enter the **approved** figure. A casual
> "3lac" in a one-line reply is still the number that governs.

> ### ⚠️ Never read a figure off a small screenshot
> A ledger row pasted into mail is typically ~825×22 px. SAP prints four decimal
> places, and at that size **`−6,868.0000` reads as `−6,868,000`** — out by a
> factor of 1,000.
>
> **Always upscale before believing a number**, then confirm it against SAP:
> ```bash
> sips -Z 4000 --out zoomed.png row.png     # then read zoomed.png
> ```
> Corroborate every figure against **two** independent sources — the vendor's
> ledger balance and the vendor's own payment history. A vendor whose every
> payment for 18 months sits between ₹4,910 and ₹27,470 is not being paid ₹68 lakh.
> Scans and handwriting: use `jivo-ap-draft/bin/zoom.py` and its
> `reference/handwriting.md`.

---

## 2. Pre-check — the duplicate hunt is on the AMOUNT

An advance has **no invoice number to deduplicate on**. The only defence is the money.

```bash
S=sap-b1/cli
# a) does a draft already exist for this vendor?
$S/sapb1 query PaymentDrafts --filter "CardCode eq '<code>'" --json
# b) EVERY payment to this vendor this period — look for the same figure
$S/sapb1 query VendorPayments \
  --filter "CardCode eq '<code>' and DocDate ge '<month start>'" \
  --select "DocEntry,DocNum,DocDate,TransferSum,TransferAccount,Remarks,Cancelled" --json
# c) the contract/PO behind it
$S/sapb1 query PurchaseOrders --filter "DocNum eq <po>" --json
```

**If the same amount has already gone out this month, stop and say so by name and
date before writing anything.** Recurring advances arrive as forwarded copies of
the same mail with the same figures; the only thing distinguishing a genuine new
request is a fresh approval timestamp. That is not proof — make the operator confirm.

Also report the exposure, so the operator sees whether the advance is covered:

```
paid this month  vs  billed this month  vs  OCRD.Balance  vs  open PO value
```

---

## 3. Clone the precedent — never hand-write the payload

Pull the vendor's most recent **non-cancelled** payment and copy every populated field.

```bash
$S/sapb1 query VendorPayments --filter "DocEntry eq <precedent>" --json \
 | python3 -c "import json,sys; d=json.load(sys.stdin)[0]; [print(f'{k}: {v!r}') for k,v in sorted(d.items()) if v not in (None,'',0,[],'tNO','N',-1,{})]"
```

Six fields no paper will ever tell you, and all are **per-vendor**:

| Field | Why it must be cloned |
|---|---|
| `ControlAccount` | `2110001` for oil vendors, `2110005` for others — a wrong one posts to the wrong control |
| `PayToCode` | the vendor's pay-to address name |
| `ContactPersonCode` | numeric, per vendor |
| `PaymentPriority` | `bopp_Priority_6` throughout |
| `VATRegNum` | JIVO's own GSTIN for that branch |
| `U_Pymnt_Mode` / `U_Type_of_Advance` / `U_Adv_Settl_Dt` | JIVO UDFs; blank ones look fine and are wrong |

**Never carry a precedent's `TransferAccount` blindly** — it alternates. Take the
account the last two or three payments used, and say out loud that treasury owns
that choice.

### Payment field names differ from document field names

A wrong name **sets nothing and SAP does not complain**:

| Concept | On a document | On a **payment** |
|---|---|---|
| Free text | `Comments` | **`Remarks`** |
| Journal memo | `JournalMemo` | **`JournalRemarks`** |
| Branch | `BPL_IDAssignedToInvoice` | **`BPLID`** |
| Currency | `DocCur` | **`DocCurrency`** |

Full list: `sap-b1/entry-vault/02-documents/Outgoing-Payment.md`.

### Series and branch

Payment series at JIVO are **monthly and shared across branches** — unlike A/P
invoice series, which are per-branch (**C-0018**). Aug-2026 Oil = **`2600`**
(`OP0826`). Never guess: read it off the precedent. `BPLID` follows the precedent
too — payments skew **DELHI (1)** overall even though purchasing is FACTORY-first,
but a factory vendor's payments are usually `2`.

---

## 4. Write it

```bash
cd sap-b1/cli
set -a; source <operator>.env; set +a          # the login that owns the entry
./sapb1 draft payment outgoing --dry-run --data-file pay.json     # show the operator
./sapb1 draft payment outgoing --yes     --data-file pay.json
```

`draft payment` is a **separate command** because SAP keeps payment drafts in
`PaymentDrafts` (`OPDF`), not `Drafts`. It moves no money and posts nothing until
a human opens **Banking → Payment Drafts** and presses **Add** — which this CLI
cannot do (that is an OData action, refused by design). A posted payment cannot be
cancelled from here either — `sapb1 cancel` covers the 14 marketing documents only.

**Log in as the person whose entry it is.** SAP user codes are zero-padded:
`user5` does not exist, `USER05` does (= TARAN, who keys most of Oil's outgoing
payments). A wrong login misattributes the entry in `OVPM.UserSign` forever, and
**SAP stamps `UserSign` at creation — it cannot be patched afterwards.** If the
entry was made under the wrong login the only fix is delete and re-create, so
settle the login in §0.5 *before* writing, not after.

Register the checkout once so the write log carries the name and provenance works:

```bash
python3 harness/bin/setup.py --name <OPERATOR> --department accounts
```

---

## 5. Read back — the diff must be dates only

```bash
./sapb1 query PaymentDrafts --filter "DocEntry eq <new>" --json
```

Diff every field against the precedent. **Anything other than the dates and
SAP-assigned keys is a defect.** For a settlement, also confirm the applied rows
landed:

```bash
hana-sql 'SELECT "DocNum","DocEntry","InvType","SumApplied","InstId"
          FROM "JIVO_OIL_HANADB"."PDF2" WHERE "DocNum"=<draft DocEntry>'
```

⚠️ **`PDF2`/`VPM2` column names are backwards** — `"DocNum"` holds the *payment's
DocEntry*, `"DocEntry"` holds the *settled document's DocEntry*, and `InvoiceId`
is not the invoice. Joining on the obvious reading returns **zero rows**.

**`DocNum` on a draft is provisional.** It is not consumed from the series until
Add, so another posting shifts it. Identify a draft by **DocEntry**, or by
vendor + amount + date — never by DocNum.

---

## 6. The attachment — it is the FULL APPROVAL MAIL

> **Operator correction, 2026-08-25 (Daman).** The paper that belongs on an
> outgoing payment is **the complete approval email thread, printed to PDF** —
> not the vendor's bill, and not a screenshot cropped out of the mail.

The mail *is* the authorisation: it carries the request, the figures, the
approver's name and the timestamp. The bill proves what was bought; the mail
proves the payment was allowed. Precedents confirm it — the 03-Aug ASHOK KITAB
GHAR payment carries `Jivo Wellness Mail - Payment to ASHOK KITAB GHAR
(BFYPK7430L) 3.8.pdf`. **Every payment in that vendor's history carries a mail
print, never the bill.** For a contract advance, the PO goes on **as well** — the
mail is not optional, the PO is the second line.

**What the mail print looks like and how to read it:
`reference/approval-mail.md`** — Gmail thread PDF, newest first, so the approval
is on page 1 and **the request (amount, purpose, company) is on the LAST page**.
Dual sequential approval is the norm; one of two named approvals means not yet
approved.

**Attaching is part of making the entry — do it in the same run (Daman,
2026-08-25).** Do not finish a payment draft and leave the paper for the
operator. You read the approval mail out of the mailbox to build the entry; print
that same thread and put it on the draft before you report back.

```bash
cd mail-cli
./jmail print <uid> --out bills/approval-mails/     # thread -> Gmail-style PDF
```

`jmail print` renders the mail's own HTML part through headless Chrome, so the
output matches the prints already on JIVO's posted payments (`Jivo Wellness Mail
- <subject>.pdf`). It is read-only on the mailbox. Then upload and point the
draft at it — recipe in `jivo-ap-draft/reference/attachments-upload.md`:
`sapb1 attach <mail.pdf> [<po.pdf>] --yes` (stamps `U_CHK`/`U_CHK2`, ticks `CopyToTargetDoc tYES`,
C-0090), set `AttachmentEntry`, read `$value` back.

Line order: **mail is line 1**; for a contract advance the **PO is line 2**.
Proven live on Beverages draft 296 (`Attachments2` 41046,
`\\10.10.101.52\Attachments_Bev\JIVO_BEVERAGES\Attachments`, `$value`
read-back byte-identical).

- One document = **one** `Attachments2` row. Never point two documents at one row.
- The `U_CHK2` guard (**C-0026**) does **not** cover `OPDF` — payment drafts are
  not in the procedure's table list. Stamp anyway; it cannot fail and can only help.
- Rename before upload so the file cannot collide on the share.

**The two things that stay true.** Never attach the vendor's bill in place of the
mail (**C-0028**) — if you cannot find the approval thread, say so and ask, rather
than attaching the bill instead. And "attach automatically" means *as part of a
payment the operator asked for*; it is never a licence to go attaching paper to
documents nobody asked you to touch.

---

## 7. Deleting a payment draft — read this before promising it

`sapb1 delete payment-draft <DocEntry>` is the only DELETE, and five guards sit
in front of it:

| Guard | Status |
|---|---|
| has an attachment | real — clear `AttachmentEntry` to `null` first (cleaner than `--with-attachment`) |
| "in an approval workflow" | **FIXED 2026-08-25.** It compared `AuthorizationStatus` against `"dasWithout"` only, but payments return the `pas` prefix — so `pasWithout` (nobody is approving it) refused **every** payment draft ever made. `delete.go` now accepts both spellings via `approvalUntouched`. `pasPending`/`pasApproved`/`pasGenerated`/`pasRejected` still refuse, correctly |
| **"created by another operator"** | real, and the one you will actually hit — see below |
| "not created here" | fires whenever the checkout was unregistered when the draft was made — the write log went outside `queries/` |
| already Added | does not apply — `OPDF` has no `DocumentStatus` |

### Delete it as the login that CREATED it

The draft belongs to the SAP login that made it. Deleting as anyone else trips
`other-operator` and demands `--other-operator`, which asserts *"I have spoken to
that person"*.

**If you made the draft minutes ago under a different login, that assertion is
false — switch login instead of overriding.** Live example: draft 292 was created
as `manager`, then had to be re-cut as `USER05`; deleting it as `manager` needed
no flag at all. An override you reach for to make a refusal go away is exactly
what the guard exists to stop.

**Re-cutting an entry under a different login: DELETE FIRST, then create.** Two
live drafts for one PO is the duplicate risk this whole skill is built around —
never let both exist, not even briefly.

**`--not-created-here` requires a real TTY** (`delete.go`: `!stdinIsTTY` → refuse).
An agent shell cannot complete it. **Do not allocate a pseudo-TTY to get around
it, and never hand-write a provenance line into `queries/<op>/sap-writes.jsonl`** —
the gate exists so a person makes the assertion, and the log is the evidence
chain for every future delete. Hand the operator the command, or tell them to use
Banking → Payment Drafts → right-click → Remove.

**A draft that has been Added shows `OPDF."Canceled" = 'Y'`** and a matching row
appears in `OVPM`. That is a human pressing Add — check for it before assuming a
draft is still inert.

---

## Checklist

- [ ] **Company read off what the mail SAYS the money is for** — never off a
      ledger screenshot's CardCode; none named = Oil
- [ ] **`--company` passed on every command**, and the CardCode is that company's
- [ ] **`doctor` green** for that company + login before any payload
- [ ] Shape decided: advance (on-account) or settlement (applied)? — and the
      precedent's shape questioned, not copied
- [ ] Settlement only: **advances netted in as negative `it_PaymentAdvice` rows**,
      and the applied rows sum to `TransferSum` before sending
- [ ] Mail read end to end (`jmail-acc7`); approver and timestamp named, and the
      **approved** figure used where it differs from the request
- [ ] Every figure re-read at full resolution and corroborated twice
- [ ] Amount deduplicated against **all** payments to this vendor this period
- [ ] Existing payment draft for this vendor checked
- [ ] Precedent pulled; all six per-vendor fields cloned
- [ ] `TransferAccount` chosen from the last 2–3, flagged as treasury's call
- [ ] Series and `BPLID` read off the precedent, not guessed
- [ ] Settlement only: **Display = Transactions for Business Partner, select all**
- [ ] Logged in as the right SAP user (zero-padded), checkout registered
- [ ] `--dry-run` shown to the operator before `--yes`
- [ ] Read back; diff vs precedent is dates only; `PDF2` rows verified
- [ ] Mail read to the LAST page; BOTH named approvers have replied
- [ ] Attachment done IN THIS RUN: `jmail print <uid>` -> mail line 1 (+ PO line 2),
      `U_CHK`/`U_CHK2` stamped, `AttachmentEntry` set, `$value` read back
- [ ] Exposure reported: paid vs billed vs balance vs open PO
