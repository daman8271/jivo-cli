---
name: cash-voucher-jv
description: The JOURNAL VOUCHER that closes the cash holder's imprest for a cash voucher booked to a VENDOR. Use after a type-2 (cash-voucher-bill) A/P draft — the bill went to the real vendor so nothing reduced the holder's float, and a JV moves it back. Debit the vendor, credit the imprest card, memo "AMOUNT TRANSFER TO ARVINDER FROM <party> <amt>/- BUNCH NO. (<bunch>)", branch Factory, place of supply Haryana, no dimensions. A Journal VOUCHER is a draft — it sits in Financials → Journal Vouchers until a human posts it; never post a journal ENTRY. Also use when asked why a vendor-booked cash voucher never came off Arvinder's float.
---

# Cash voucher · the JOURNAL VOUCHER that closes the imprest

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

Daman taught this on **2026-09-12**, having flagged it earlier the same day:
*"We gonna close Arvinder's imprest voucher later by posting a journal voucher."*

RULE 0 in `CLAUDE.md` governs the write.

---

## Why it exists

| Voucher type | A/P goes to | Does the float move? |
|---|---|---|
| **1 · GRPO** and **3 · MANUAL** | the **imprest card** | **yes** — the A/P credits the holder, the float comes down |
| **2 · BILL** (`cash-voucher-bill`) | the **real vendor** — the input credit has to land on that vendor's GSTIN | **no** — the holder paid cash and nothing on his account reflects it |

So every type-2 voucher leaves two loose ends: a payable to a vendor the holder
has already settled in cash, and a float that never came down. **The JV closes
both in one entry.**

## 🔴 THE RULE — debit the party, credit the imprest

```
Dr   <the vendor>            <amount>
  Cr   <the FACTORY IMPREST card>      <amount>
```

**Daman: "credit Arvinder's acc; remarks should be amount transfer to Arvinder
from party name."** Getting the sides the wrong way round doubles the payable
instead of clearing it.

| Field | Value |
|---|---|
| Memo **and** every `LineMemo` | `AMOUNT TRANSFER TO ARVINDER FROM <PARTY NAME> <amt>/- BUNCH NO. (<bunch>)` |
| Branch (`LocationCode`, line `BPLID`) | **2 — FACTORY** |
| Place of supply | **Haryana** |
| Dimensions | **none.** Every precedent JV has `ProfitCode` and Dim2–Dim5 blank on both lines. A JV is a transfer between two parties, not a cost |
| `Series` | the **JV** family for the month — Oil `JV0826` = **2588**, `JV0926` = **2589** (`NNM1 ObjectCode 30`). *Not* the `ATJV` family |
| `ReferenceDate` / `TaxDate` / `DueDate` | the **A/P document's posting date** |

### 🔴 ONE JV PER VOUCHER — never combined, not even for the same party

**Daman, 2026-09-12:** *"We can't generate 1 JV for multiple vouchers, whether
they are from the same party. We need to create different JVs for each voucher."*

Vouchers **438** (₹281) and **439** (₹351) are both SMARTSHIFT, both dated
01-09-2026, same bunch. They are **two JVs**, not one of ₹632. A combined one was
made and had to be deleted.

The JV mirrors the voucher one-for-one, so each carries **its own voucher's
amount** in the memo and **its own merged PDF**. Do not net, do not total, and do
not group by party or by date.

One consequence worth planning for: the merged PDF is built **per voucher** too —
`main sheet + that one voucher`, so two vouchers from one party need two uploads
and two different `U_ATTACH_LINK` paths.

**Each line needs both sides named:**

| Line field | Debit line | Credit line |
|---|---|---|
| `ShortName` | the vendor | the imprest card |
| `AccountCode` | the vendor's control account — **`2110004`** | the imprest control account — **`2110003`** |
| `ContraAccount` | the imprest card | the vendor |

Read the control account off the partner rather than trusting this table:
`SELECT "CardCode","DebPayAcct" FROM <DB>.OCRD WHERE "CardCode" = '<card>';`

## 🔴 A journal VOUCHER is a draft. A journal ENTRY is the ledger.

They are different objects and only one of them is safe:

| | Where it lands | Undo |
|---|---|---|
| **Journal Voucher** (`OBTF`/`BTF1`, batch) | *Financials → Journal Vouchers*, **unposted** | a person edits or deletes it |
| Journal Entry (`OJDT`/`JDT1`) | **the ledger, live, unapproved** | only a reversal, which posts a SECOND document |

**Always the voucher.** `sapb1 post JournalEntries` refuses by design and there is
no flag — trust that refusal.

## How to write it — the CLI has no command for this yet

`sapb1` has **no journal-voucher doctype**: `sapb1 draft` offers 14 types and none
is a JV, and `post` only takes entity sets. The Service Layer's endpoint is an
**action**, `JournalVouchersService_Add`, so it is called directly — the same way
`jivo-ap-draft/reference/attachments-upload.md` already calls `Attachments2`.

```bash
curl -sk -b "$S/ck" -H "Content-Type: application/json" \
  --data-binary @jv.json "$H/b1s/v1/JournalVouchersService_Add" -w "%{http_code}\n"
```

Body shape:

```json
{ "JournalVoucher": { "JournalEntries": [ {
  "ReferenceDate": "2026-08-17", "DueDate": "2026-08-17", "TaxDate": "2026-08-17",
  "Memo": "AMOUNT TRANSFER TO ARVINDER FROM SUNRISE INTERNET PVT LTD 1180/- BUNCH NO. (39940)",
  "Series": 2588, "LocationCode": 2,
  "JournalEntryLines": [
    {"ShortName":"VENDA001500","AccountCode":"2110004","ContraAccount":"ORGV000465",
     "BPLID":2,"Debit":1180,"LineMemo":"<same memo>",
     "ReferenceDate1":"2026-08-17","TaxDate":"2026-08-17","DueDate":"2026-08-17"},
    {"ShortName":"ORGV000465","AccountCode":"2110003","ContraAccount":"VENDA001500",
     "BPLID":2,"Credit":1180,"LineMemo":"<same memo>",
     "ReferenceDate1":"2026-08-17","TaxDate":"2026-08-17","DueDate":"2026-08-17"}
  ] } ] } }
```

**🔴 It returns HTTP 204 with an empty body — that is NOT proof.** Read it back:

```sql
SELECT h."BatchNum", h."TransId", h."RefDate", h."Series", h."LocTotal",
       l."Line_ID", l."ShortName", l."Account", l."ContraAct", l."Debit", l."Credit", l."BPLId"
FROM   <DB>.OBTF h JOIN <DB>.BTF1 l
       ON l."BatchNum" = h."BatchNum" AND l."TransId" = h."TransId"
WHERE  h."Memo" LIKE '%AMOUNT TRANSFER TO ARVINDER%';

SELECT COUNT(*) FROM <DB>.OJDT WHERE "Memo" LIKE '%AMOUNT TRANSFER TO ARVINDER%';
-- want 0: still a voucher, nothing in the ledger
```

**Log it by hand.** A direct Service Layer call writes nothing to
`queries/<operator>/sap-writes.jsonl`, so append the `{method, path, payload,
status, note}` line yourself — otherwise the write is invisible to the team.

*Worth building: a `sapb1 draft journal-voucher` command that wraps this with the
preview, the typed confirmation and the write log every other write here gets.*

## Attachment — main sheet + voucher, ONE combined PDF

**Daman: "in JV's attachment we post main sheet + voucher in 1 pdf only
combined."** Not two files, not two rows — merge them:

```bash
pdfunite "main sheet.pdf" "CASH-VCH-<no>.pdf" "JV-<no>-<PARTY>.pdf"
```

A JV carries its file as a **path string**, not an `Attachments2` row — the
`U_ATTACH_LINK` UDF, e.g.
`\\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments\3540 - arv_merged.pdf`
(the hand-keyed precedents literally name theirs `…_merged.pdf`). Keep the merged
file under 1 MB; re-render per `cash-voucher` §8 if it is over.

### 🔴 Set `U_ATTACH_LINK` WHEN YOU CREATE IT — it can never be added later

Measured against the live metadata on 2026-09-12:

- `U_ATTACH_LINK` is a plain `Edm.String` on the JournalEntry type, so it goes in
  the `JournalVouchersService_Add` body like any other field.
- **There is no journal-voucher entity set at all.** `JournalVouchers`,
  `JournalVouchers(6746)`, `JournalVoucherEntries` all return
  `400 Unrecognized resource`, and the metadata contains exactly one journal-voucher
  operation: `FunctionImport Name="JournalVouchersService_Add"`.
- So a voucher has **no GET, no PATCH and no DELETE** from the API. Once added it
  can only be edited, posted or deleted **by a person in the SAP B1 client**.

**Two steps, in this order, before the POST:**

1. **Put the merged PDF on the share.** `POST /Attachments2` with the file writes
   it to `\\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments` and the response's
   `TargetPath` + `FileName` give you the exact path. (The `Attachments2` row it
   creates is unused and harmless — JVs do not reference rows.)
2. **Put `<TargetPath>\<FileName>.<ext>` into `U_ATTACH_LINK`** on the
   JournalEntry, then POST.

Forget step 2 and the only remedy is a person deleting the voucher so it can be
re-added — which is how vouchers 6746 and 6748 ended up without their link, and
had to be thrown away and redone as 6750 / 6751.

⚠️ **`hana-sql` prints the stored path with DOUBLED backslashes.** That is the
tool escaping its output, not a corrupted value. Do not "fix" it. Prove it
against a hand-keyed voucher with the same tool instead:

```sql
SELECT "U_ATTACH_LINK", LENGTH("U_ATTACH_LINK") FROM <DB>.OBTF WHERE "BatchNum" = <n>;
-- \\10.10.101.52\...\3540 - arv_merged.pdf is 73 chars = single separators
```



---

## Worked example — 2026-09-12

Two type-2 vouchers off the 04-09-2026 sheet, bunch **39940**:

| Voucher | Party | ₹ | JV | Series | Merged PDF |
|---|---|---:|---|---|---|
| 421 | SUNRISE INTERNET PVT LTD | 1,180 | **BatchNum 6750** | 2588 `JV0826` | `JV-421-SUNRISE-INTERNET.pdf` |
| 438 | SMARTSHIFT LOGISTICS SOLUTIONS PVT LTD | 281 | **BatchNum 6753** | 2589 `JV0926` | `JV-438-SMARTSHIFT.pdf` |
| 439 | SMARTSHIFT LOGISTICS SOLUTIONS PVT LTD | 351 | **BatchNum 6755** | 2589 `JV0926` | `JV-439-SMARTSHIFT.pdf` |

Read back: two legs each, `2110004` Dr / `2110003` Cr, `BPLId` 2, no dimensions,
`U_ATTACH_LINK` set, and `OJDT` count **0** — all three still unposted vouchers.

Three earlier attempts were deleted and redone: 6746/6748 had no attachment
(set at creation or never), and 6748 also wrongly combined 438 + 439 into one.

---

## What I got wrong

| # | I said | Truth | Root cause |
|---|---|---|---|
| 1 | "the CLI cannot write this, it is a missing feature" | the **endpoint works** and the JVs were created minutes later | I tested `post JournalEntries`, hit its (correct) refusal, and stopped — without ever testing the **voucher** entity. A guard on the dangerous sibling is not evidence about the safe one |
| 2 | offered to build a Go command before trying the direct call | the direct call is already house practice for `Attachments2` | reached for the big fix before the small one |
| 3 | combined two same-party vouchers into one JV of ₹632 | **one JV per voucher** | generalised from precedent — every precedent JV happened to be one party at one amount, and I read that as "one per party" when it was simply one per voucher |

**The lesson: when a wrapper refuses, test the underlying API before reporting
that something is impossible.** "Our tool has no command" and "it cannot be done"
are different sentences, and only one of them was true.

---

## Pre-flight

- [ ] the voucher really is **type 2** — its A/P is on a vendor, not the imprest card
- [ ] **Dr the vendor, Cr the imprest card** — not the other way round
- [ ] **one JV per VOUCHER** — never one JV for two vouchers, even same party,
      same date and same bunch
- [ ] memo = `AMOUNT TRANSFER TO ARVINDER FROM <PARTY> <amt>/- BUNCH NO. (<bunch>)`,
      on the header **and** both lines
- [ ] `Series` = the `JV<MMYY>` family for the month, period open
- [ ] `BPLID`/`LocationCode` **2**, place of supply Haryana, **no dimensions**
- [ ] control accounts read off `OCRD.DebPayAcct`, not assumed
- [ ] **read back `OBTF`/`BTF1`** — 204 proves nothing
- [ ] **`OJDT` count 0** — it is a voucher, not a ledger entry
- [ ] main sheet + voucher merged into **one** PDF, under 1 MB, uploaded to the
      share FIRST and its path put in **`U_ATTACH_LINK` in the Add payload** — it
      cannot be attached after the voucher exists
- [ ] the call appended to `queries/<operator>/sap-writes.jsonl` **by hand**
