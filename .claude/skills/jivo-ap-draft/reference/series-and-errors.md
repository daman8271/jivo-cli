# Numbering series, SAP errors, client click-paths

## How Oil numbers A/P invoices

`NNM1` (ObjectCode 18) has one series per **branch × month × document sub-type**.
The sub-type is the decider most people miss:

| DocSubType | Service Layer `DocumentSubType` | Used for |
|---|---|---|
| `GA` | `bod_GSTTaxInvoice` | normal GST vendor invoices — **this is the one** |
| `--` | `bod_None` | non-GST / plain |
| `GD` | `bod_GSTDebitMemo` | debit memos |

Aug-2026 (period indicator `AUG-26-27`), A/P invoice, `GA`:

| Branch | Series | Name | DocNum pattern |
|---|---|---|---|
| 1 DELHI | 3672 | DL_G0826 | 72608xxxx |
| **2 FACTORY** | **3684** | **HR_G0826** | 62608xxxx |
| 3 PUNJAB | 3696 | PB_G0826 | 32608xxxx |
| 4 HIMACHAL | 3708 | HP_G0826 | 22608xxxx |
| 5 HARYANA SALES | 3768 | HS_G0826 | 62608xxxx |
| 6 DELHI ISD | 3780 | DISD0826 | 72608xxxx |

The name encodes it: `HR` = Haryana/FACTORY, `G` = GST tax invoice, `0826` =
Aug-26. Every month has a fresh set. `precheck.py` derives the series from this
month's posted/drafted documents in the branch, and cross-checks `NNM1` through
`hana-sql` when it can reach it. First document of a new month: the NNM1 lookup
is the only source —

```bash
./hana-sql/hana-sql -env connections/hana.env \
 "SELECT \"Series\",\"SeriesName\",\"DocSubType\",\"BPLId\",\"Locked\" FROM JIVO_OIL_HANADB.NNM1
  WHERE \"ObjectCode\"='18' AND \"Indicator\"='SEP-26-27' ORDER BY \"Series\""
```

## SAP errors met on this path

| Error | Meaning | Fix |
|---|---|---|
| `-10 10000521 … define the numbering series` | no `Series` given and the user has no default for this doc type/period | add `Series` |
| `-4002 … define the numbering series` | `Series` given but its sub-type ≠ document's | add `DocumentSubType` matching the series (`bod_GSTTaxInvoice` for `G` series) |
| `-5002 Specify an active branch [ODRF.BPLId]` | missing `BPL_IDAssignedToInvoice` | branch = `BusinessPlaces.FederalTaxID` == buyer GSTIN |
| `-8112` | bad `CardCode` | re-check the vendor match |
| `-5002 Attachments folder not defined … [131-102]` on `POST /PurchaseInvoices` | server-side; the approval-intercept path needs the attachments folder the Linux Service Layer can't see | do not retry; Add is done in the client |
| `Fail to NONE-SSO login from SLD` | stale/wrong password for that SAP user (the account itself may be fine) | get the current password; user codes are case-sensitive (`USER06`, not `user06`) |
| CLI exit 7 | write sent, reply lost | query `Drafts` by `NumAtCard`; never re-send blind |

## What SAP does and doesn't fill in on an API-made draft

- Fills: `DocDueDate` (terms from doc date), rounding, `VatSum`, `DocNum` (shared
  "next number" until added), `CardName`, addresses, e-way-bill party block.
- Leaves empty: **TDS** (`WTAmount 0`, lines `WTLiable tNO`) even when the BP is
  `SubjectToWithholdingTax boYES` with a WT code — client-made invoices carry it
  (0.1% u/s 194Q, code 1031, at JIVO). Payload sets `WTLiable: tYES`; if read-back
  still shows 0, Accounts ticks it before Add.
- `AuthorizationStatus` stays `dasWithout` — approval starts only at Add.

## Client click-paths (tell the operator exactly this)

**See a draft:** Purchasing – A/P → Purchasing Reports → Document Drafts Report →
tick *A/P Invoice*, *Open Only*, User = the draft's owner (or *All*) → OK →
double-click the row (vendor · vendor ref · total · posting date).

**Send it for approval:** open the draft → tick *WTax Liable* on each row →
**Add** → "sent for approval" → it is now in Approval Status Report as Pending
(Oil A/P invoices route via template "USER03 AP" to Bhawani / USER03).

**Remove a duplicate draft:** in the Document Drafts Report, right-click the row
→ Remove. Only the owner or a superuser can; the CLI cannot delete anything.

## Who keys what (Oil, as of 2026-08-21)

- FactoryApp v2 (`shahrukh@jivo.in`, SAP user 2) creates the **GRPO** at gate entry,
  with `Comments` = `App: FactoryApp v2 | … | PO: … | Gate Entry: GE-2026-xxxx | GATE ENTRY NO n`.
- Accounts (NEETU/USER07, HARSH/USER08, Lovpreet/USER06, Navdeep/USER36) key the
  **A/P invoice** in the client from the GRPO, usually the day the paper lands —
  which is why the pre-check's "already exists" branch is the common case.
- Approver for A/P invoices: BHAWANI/USER03.
