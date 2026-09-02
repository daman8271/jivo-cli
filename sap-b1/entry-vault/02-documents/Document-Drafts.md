---
type: document
sap_tables: [ODRF, DRF1, DRF12]
objtype: -1
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Document Drafts — the unit of work, and what the CLI actually creates

> A draft is a document that has not happened yet: no stock moves, no ledger entry, nothing
> posts until a person opens SAP B1 → Document Drafts and presses **Add**. 78,492 of them
> across the three books, in 14 different document types, all in one table.

This is the note to read before creating anything from the CLI, because **a draft is all
the CLI can create.** → [[AP-Invoice]], [[AP-Credit-Memo]]

## At a glance

| | |
|---|---|
| SAP tables | `ODRF` header · `DRF1` lines · `DRF12` tax/address — **one table for every document type** |
| Volume | Oil 49,463 · Mart 14,683 · Bev 14,346 · **78,492** |
| Discriminator | `ObjType` — 14 values in Oil |
| `DocType` | `I` 38,196 · `S` 11,267 |
| Drafts *are* visible | To other operators and to any approval workflow. A draft is not a private scratchpad |

## What gets drafted

| `ObjType` | Document | Oil drafts |
|---:|---|---:|
| 18 | [[AP-Invoice]] | 15,352 |
| 67 | [[Stock-Transfer]] | 11,655 |
| 13 | [[AR-Invoice]] | 9,790 |
| 20 | [[GRPO]] | 4,488 |
| 19 | [[AP-Credit-Memo]] | 1,696 |
| 22 | [[Purchase-Order]] | 1,631 |
| 14 | [[AR-Credit-Memo]] | 1,488 |
| 15 | [[Delivery]] | 1,388 |
| 16 | [[AR-Return]] | 1,116 |
| 1250000001 | [[Inventory-Transfer-Request]] | 704 |
| 21 | [[Goods-Return]] | 102 |
| 17 | [[Sales-Order]] | 34 |
| 59 | [[Goods-Receipt]] | 14 |
| 60 | [[Goods-Issue]] | 5 |

Payments are **not** here — they have their own draft table, [[Payment-Draft]] (`OPDF`).
Journal entries are never drafted; the parked equivalent is a [[Journal-Voucher]] (`OBTF`).

## Drafting is the norm for some documents and rare for others

Drafts per posted document, Oil, 365-day window:

| Document | Ratio | Reading |
|---|---:|---|
| [[AP-Invoice]] | **1.02** | Practically one draft each — drafting *is* the process |
| [[GRPO]] | 0.39 | Usually posted directly |

So: an A/P invoice you cannot find may well be sitting in Document Drafts. A GRPO you
cannot find probably does not exist yet. That difference changes where you look first.

## The status field everyone misreads

`ODRF."CANCELED"` is **single-valued** — `N` on all 49,463 rows. A draft is never marked
cancelled there. The real state lives in **`WddStatus`**, which on a draft is the
**approval status**, not merely a workflow hint.

Oil A/P drafts (`ObjType` 18), every combination:

| `DocStatus` | `WddStatus` | Count | What it means |
|---|---|---:|---|
| `C` | `-` | 14,264 | **Posted.** The draft became a document |
| `O` | `C` | **817** | **Cancelled in approval.** Dead. Not pending |
| `O` | `W` | 95 | Waiting for an approver |
| `O` | `Y` | 78 | Approved, not yet added |
| `O` | `N` | 62 | Rejected |
| `O` | `-` | 36 | Open, no approval process attached |

**Of 1,088 "open" Oil A/P drafts, 817 — 75% — are cancelled, not pending.** Anyone
counting the backlog from `DocStatus = 'O'` overstates it by four times. The genuinely live
queue is 95 waiting + 78 approved + 36 unmanaged = **209**.

*(This independently reproduces a figure recorded on 2026-08-24 — 817 of ~1,053 — and now
pins down where it lives. `WddStatus = 'C'` is the HANA representation of the Service
Layer's `dasCancelled`.)*

Value meanings across all 49,463 Oil drafts: `-` 45,646 · `C` 2,967 · `N` 481 · `Y` 184 ·
`W` 184 · `P` 1. *Inferred from the standard SAP approval vocabulary and consistent with the
counts:* `Y` approved, `N` rejected, `W` waiting, `C` cancelled, `P` pending, `-` no
approval process. **Not independently confirmed** — worth one check with an operator who can
see the Approval Status Report.

## Does the posted document remember its draft?

Yes, usually. `OPCH."draftKey"` is populated on **7,009 of 7,420** posted Oil A/P invoices
in a 365-day window (**94.5%**).

So you can trace a document back to the draft it came from — for 94.5% of them. The missing
5.5% were posted without going through a draft (or through a path that does not record it).
Do **not** build a reconciliation that assumes every document has a `draftKey`.

## Draft numbers are not unique

Three different Oil A/P drafts — `DocEntry` 54848, 54853 and 54855 — all carry `DocNum`
**726083103**, all dated 2026-08-01, all cancelled in approval.

So `DocNum` on a draft is **not** an identifier. Use `DocEntry`. A draft re-created after a
rejection appears to reuse the number, which means a `DocNum`-keyed lookup can return
several rows. *(Inferred cause: re-drafting after cancellation. The reuse itself is
measured.)*

## What a draft does and does not do

| | |
|---|---|
| **Does not** move stock | |
| **Does not** post to the ledger | No journal until Add |
| **Does not** consume the numbering series' live number | *Inferred* from the duplicate `DocNum` above — needs confirming |
| **Does** appear to every other operator in Document Drafts | |
| **Does** enter the approval workflow | Which is exactly what [[Approval-Workflow]] expects |
| **Does** carry attachments | → [[Attachments]] |
| **Can** be deleted from the CLI | The only sanctioned `DELETE` — see below |

`Printed` is `Y` on 17 of 49,463 and `Handwrtten` on 1. Nobody prints a draft.

## Creating one from the CLI

`sapb1 draft <doctype>` — this is the sanctioned write path, and drafts-first is the rule
for anything document-shaped. Never `post` a document.

The mechanics that bite:

- **`Series` is mandatory and specific** to (document type, branch, month) →
  [[Numbering-Series]]. Getting it wrong gives SAP `-10`, "define the numbering series".
- **`DocumentSubType`** — `bod_GSTTaxInvoice` for A/P documents. **(C-0018)**
- **The draft comes back with fields SAP filled differently from what you sent.** TDS is
  the known one: `WTAmount` comes out 0 even when the vendor is liable. **Always read the
  draft back.** **(C-0018)**
- **Attachments need their flags set** — `U_CHK2` = `OK` and `U_CHK` = size in KB on each
  line, plus a copy of the base document's file as an independent second line. **(C-0026)**
- **Exit code 7 means "unknown — go look".** The request reached SAP but the answer did
  not come back. **Do not re-run it.** Check Document Drafts first.

## Deleting one from the CLI

`sapb1 delete draft <DocEntry> [<DocEntry>...]` — up to 50 at a time. This is the **only**
`DELETE` this toolkit can perform: it reaches `Drafts` and `PaymentDrafts` and nothing else.
A posted document can never be deleted from here.

What it does before deleting: reads the draft and shows you what you are about to destroy,
refuses any draft this CLI did not create, requires a typed `yes`, keeps a local snapshot
(only its sha256 goes in the shared log, because the repo is public), and reads back to
confirm the draft is gone.

The guards each map to a fact an operator must assert out loud, and each is recorded under
their name — **never add one to make a refusal go away**:

| Flag | The operator is asserting |
|---|---|
| `--not-created-here` | "A person keyed this in the SAP B1 client and I am telling you to remove it anyway." One DocEntry, needs a human at the prompt, cannot combine with `--yes` |
| `--older-than` | The draft is older than 24 hours and that is fine |
| `--with-attachment` | It has an attachment and that is fine |
| `--closed` | It is closed and that is fine |
| `--other-operator` | It is someone else's draft |
| `--in-approval` | It is in somebody's Approval Status Report — **ask them first** |

Exit codes: **8** = deleted but the read-back did not confirm (probably gone, check
Document Drafts; re-running is safe). **9** = a guard refused — that is a "go ask the
operator" signal, not an invitation to add the flag.

Given that 817 of 1,088 open Oil A/P drafts are already cancelled, **a bulk delete of
"open" drafts would mostly be deleting things that are already dead** — and would still
need `--in-approval` for anything a person can see. Filter on `WddStatus`, not `DocStatus`.

## Traps

1. **`DocStatus = 'O'` does not mean pending.** 75% of open Oil A/P drafts are cancelled.
   Read `WddStatus`.
2. **`CANCELED` on a draft is always `N`.** It carries no information. This is the opposite
   of every posted document, where `CANCELED` is three-valued. **(cf. C-0021)**
3. **`DocNum` is not unique on a draft.** Key on `DocEntry`.
4. **`draftKey` is on 94.5% of posted documents, not 100%.**
5. **A draft is visible to everyone.** It is not a private working copy — it shows up in
   Document Drafts and in the approval flow the moment it exists.
6. **All 14 document types share `ODRF` and `DRF1`.** Any query over drafts must filter
   `ObjType` or it silently mixes A/P invoices with stock transfers.
7. **`InvntSttus` is `O` on 49,461 of 49,463** — effectively constant on drafts. Don't read
   anything into it.

## Open questions

1. Confirm the `WddStatus` letter meanings with someone who can see the Approval Status
   Report. `Y`/`N`/`W`/`C`/`P` are inferred from standard SAP vocabulary plus the counts,
   not verified.
2. Does a draft consume a numbering-series number? The duplicate `DocNum` on 54848/54853/
   54855 suggests not, but that is inference.
3. Why are **817** Oil A/P drafts cancelled in approval? That is a lot of rejected work.
   Clustered by operator, vendor, or period? One query, and it might point at a real process
   problem rather than a data curiosity.
4. What are the 411 posted A/P invoices with no `draftKey` — a different entry path, or an
   integration?
5. `WddStatus = 'P'` on exactly 1 draft out of 49,463. What is that one?

## Queries used

```sql
-- what gets drafted, and the status matrix that actually matters
SELECT "DocStatus", "WddStatus", COUNT(*) N
FROM "JIVO_OIL_HANADB"."ODRF" WHERE "ObjType"=18
GROUP BY "DocStatus","WddStatus" ORDER BY N DESC;
-- C/- 14264 (posted) | O/C 817 (cancelled) | O/W 95 | O/Y 78 | O/N 62 | O/- 36

-- CANCELED carries nothing on a draft
SELECT "CANCELED", COUNT(*) FROM "JIVO_OIL_HANADB"."ODRF" GROUP BY "CANCELED";
-- N x 49,463

-- does the posted document remember its draft?
SELECT COUNT(*) TOTAL,
       SUM(CASE WHEN "draftKey" IS NOT NULL AND "draftKey"<>0 THEN 1 ELSE 0 END) HAS_DRAFTKEY
FROM "JIVO_OIL_HANADB"."OPCH" WHERE "DocDate" >= ADD_DAYS(CURRENT_DATE,-365);
-- 7,420 / 7,009 = 94.5%

-- DocNum is not unique on a draft
SELECT "DocEntry","DocNum","DocStatus","WddStatus","DocDate"
FROM "JIVO_OIL_HANADB"."ODRF"
WHERE "ObjType"=18 AND "DocStatus"='O' AND "WddStatus"='C'
ORDER BY "DocEntry" DESC LIMIT 3;
-- 54848, 54853, 54855 all DocNum 726083103
```

Field profile: `_data/profile-ODRF.md` · lines: `_data/profile-DRF1.md`.
