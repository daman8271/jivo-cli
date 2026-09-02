---
type: document
sap_tables: [ORPC, RPC1, RPC12]
objtype: 19
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# A/P Credit Memo — the debit note back to a vendor

> We were billed for more than we got, or at the wrong rate, or we sent goods back. This
> is the document that takes it off the vendor's account. 2,624 across the three books.

## At a glance

| | |
|---|---|
| SAP tables | `ORPC` header · `RPC1` lines · `RPC12` tax/address |
| ObjType / TransType | **19** |
| Volume | Oil 1,595 · Mart 781 · Bev 248 · **2,624** total |
| Last 120 days | Oil 229 |
| Who keys it | 11 logins in Oil, four do 96%: `UserSign` 16 (461), 17 (363), 18 (345), 15 (335) — the same desks that key [[AP-Invoice]] |
| Drafted first? | Yes — 2,513 drafts against 2,624 posted |
| Needs approval? | Yes — `WddStatus` is `P` on 1,566 of 1,595 |
| Mostly service | `DocType` `S` 1,295 · `I` 300 — **81% are service/value adjustments, not goods returns** |

## What it is *not*

It is not a [[Goods-Return]]. Those exist (`ORPD`) but there are only 209 of them across
all three books against 2,624 credit memos. So the overwhelmingly normal case is a **value
adjustment with no stock movement** — short supply billed, wrong rate, a claim settled.

`DocType` confirms it: 1,295 of 1,595 Oil credit memos are `S` (service — no item lines).

## The field the whole note exists for

Correction **C-0024** says: always set `OriginalRefNo` (the original invoice number exactly
as printed on the credit note) and `OriginalRefDate`. SAP silently accepts null; Accounts
and GST require them.

### Where those fields actually live — and why you could not find them

The Service Layer property names and the HANA column names **do not match**, and the HANA
names are unguessable:

| Service Layer (what you send) | HANA column (what you query) |
|---|---|
| `OriginalRefNo` | **`RevRefNo`** |
| `OriginalRefDate` | **`RevRefDate`** |

Nothing called "Original" exists on `ORPC`. The obvious-looking candidates are all decoys:

| Column | What it actually is |
|---|---|
| `RetInvoice` | **A flag.** Single value `N` across all 1,595 rows |
| `FlwRefNum` / `FlwRefDate` | **Never used** — 0 of 1,595 |
| `CorrInv` / `NCorrInv` / `MInvNum` / `ExcRefDate` | All 0 of 1,595 |
| `Ref1` | Auto-filled with the document's own number |

*(Found by reading draft 55128 through the Service Layer — where `OriginalRefNo` came back
as `RPL/1164/2026-27` — then searching all 251 text columns of `ODRF` for that exact value.
`RevRefNo` was the only match. Same method for the date against the 33 timestamp columns.)*

**This matters beyond curiosity:** any HANA-side audit of "did we fill the reference
number?" that looked for `Original*` or `RetInvoice` would have found nothing and concluded
the field was never populated. It is populated almost always. The audit was looking in the
wrong place.

### And the answer: followed on A/P — and on A/R, SAP enforces it for you

**A/P credit memos** (`ORPC`), all history:

| Book | Total | Has ref no. | Has ref date | **Incomplete** |
|---|---:|---:|---:|---:|
| Oil | 1,595 | 1,552 | 1,551 | **44 (2.8%)** |
| Mart | 781 | 766 | 763 | **18 (2.3%)** |
| Beverages | 248 | 245 | 245 | **3 (1.2%)** |

Oil's last 120 days: 226 of 229 (98.7%). So C-0024 is being followed. The 44 Oil gaps are
worth a one-off cleanup list, not a process change.

**A/R credit memos** (`ORIN`) — the same two columns, and I first read this wrong.

My initial figures (Oil 59.5%, Mart 50.7%, Bev 81.1%) counted **every row**, including 1,266
Oil migration rows and cancelled documents, and I concluded "roughly 7,000 sales credit notes
have no reference — the same requirement, missed half the time". [[AR-Credit-Memo]] took it
apart properly, and the truth is more precise and more useful:

| Split by whether the buyer is GST-registered | Oil | Mart | Bev | **Blank reference** |
|---|---:|---:|---:|---:|
| GST credit note, **buyer registered (B2B)** | 3,116 | 1,711 | 228 | **0 · 0 · 0** |
| GST credit note, **no buyer GSTIN** | 1,225 | 2,627 | 82 | 1,158 · 2,203 · 5 |
| Non-GST credit note | 541 | 55 | 90 | 156 · 19 · 74 |

**5,055 B2B GST credit notes across three books and not one blank reference** — including
memos copied from a Return, where SAP supplies nothing, and 853 keyed from scratch by ten
different logins. *Inferred, high confidence:* SAP's India localization makes the pair
**mandatory** on a GST credit note when the partner carries a GSTIN.

So operators are not forgetting it. The real gap is narrower and specific:
**3,366 GST credit notes to *unregistered* buyers carry output-GST reversal with no original
reference, and 207 of those are in the last four months** — GSTR-1 **CDNUR** asks for the
original invoice number and date, so they are unsupported in the return as filed.

Note the contrast that makes C-0024 real *here*: on the **purchase** side, 44 Oil vendor
credit memos genuinely do have a blank reference. The enforcement is not universal, so the
instruction still matters on A/P. → [[AR-Credit-Memo]]

## Before you start — the pre-flight list

- [ ] The **original invoice number**, exactly as printed on the vendor's credit note →
      `OriginalRefNo`. Not our `DocNum`, not the vendor's credit-note number.
- [ ] The **original invoice date** → `OriginalRefDate`.
- [ ] `NumAtCard` — the vendor's credit-note number (100% filled, 1,463 distinct values).
- [ ] Which company book. The vendor's `CardCode` differs between books.
- [ ] Is it a value adjustment (`S`) or a goods return (`I`)? 81% are `S`.
- [ ] The **same tax code as the original invoice** — the reversal must mirror the original,
      including RCM.
- [ ] Branch, series → [[Numbering-Series]]. Oil uses `BPLId` `2` FACTORY 1,325 · `5`
      HARYANA SALES 200 · `1` DELHI 66 · `6` DELHI ISD 4.
- [ ] The GL account being credited back, and the dimensions to match the original.
- [ ] The scan of the credit note → [[Attachments]].

## Fields that matter (`ORPC` header)

| Field | Reads as | Oil filled | Notes |
|---|---|---:|---|
| `RevRefNo` | **Original invoice no.** | 97.3% | = Service Layer `OriginalRefNo`. **C-0024** |
| `RevRefDate` | **Original invoice date** | 97.2% | = Service Layer `OriginalRefDate` |
| `NumAtCard` | Vendor's credit-note number | 100% / 90% recent | 1,463 distinct |
| `CardCode` / `CardName` | The vendor | 100% | |
| `DocType` | `S` value / `I` goods | 100% | 1,295 / 300 |
| `DocDate` / `TaxDate` | Posting / paper date | 100% | Same rule as [[AP-Invoice]] |
| `CtlAccount` | Vendor control account | 100% | Only 6 values: `2110004` ×1,051 · `2110001` ×282 · `2110005` ×243 · `2110003` ×13 · `2110002` ×3 · `2121002` ×3 |
| `BPLId` / `BPLName` | Branch | 100% | 4 values, and here the id and name **agree** (unlike [[GRPO]]) |
| `CANCELED` | Three-valued | 100% | `N` 1,567 · `Y` 14 · `C` 14 |
| `DocStatus` | Open / closed | 100% | `C` 1,276 · `O` 319 |
| `WddStatus` | Approval | 100% | `P` 1,566 · `-` 29 |
| `DocumentSubType` | GST document subtype | — | `bod_GSTTaxInvoice` on our drafts |

## The journal it posts

TransType 19. Oil: 1,595 journals. It is the [[AP-Invoice]] fingerprint run backwards:

- **Dr** the vendor control account (reducing what we owe)
- **Cr** the expense or inventory account originally charged
- **Cr** the input GST accounts (reversing the credit taken)
- RCM codes reverse **both** legs of the pair

Full fingerprint: `_data/gl-19-OIL.md`.

The check that matters: **the reversal must mirror the original**, account for account,
tax code for tax code, dimension for dimension. A credit memo that reverses the amount but
lands on a different GL leaves both accounts wrong.

## Traps

1. **`OriginalRefNo` is `RevRefNo` in HANA, and `OriginalRefDate` is `RevRefDate`.** Nothing
   named `Original*` exists. `RetInvoice` looks right and is a flag.
2. **SAP accepts both as null without complaint.** 44 Oil credit memos prove it. Nothing in
   the UI or the API will stop you. **(C-0024)**
3. **The same gap is far worse on [[AR-Credit-Memo]]** — about half of sales credit notes
   have no reference at all.
4. **`CANCELED` is three-valued** — `N` 1,567, `Y` 14, `C` 14. **(C-0021)**
5. **Do not reach for [[Goods-Return]] by default.** 2,624 credit memos against 209 goods
   returns; the goods-return path is the exception, not the norm.
6. **319 Oil credit memos show `DocStatus = 'O'`** — 20%. Per C-0019 that does not reliably
   mean unapplied; it often means settled some other way.
7. **The tax code must match the original invoice**, RCM included. A credit memo with a
   plain code against an RCM invoice reverses one leg and leaves the other standing.

## How to create one from the CLI

Draft only. Use the **`jivo-ap-credit-memo` skill** — it exists precisely because of
C-0024, and it sets the reference pair. Do not hand-roll the payload.

The payload must carry, beyond the obvious:

```
Series             -> from NNM1 for (ObjType 19, branch, month)
DocumentSubType    -> bod_GSTTaxInvoice
OriginalRefNo      -> the original invoice number, exactly as printed
OriginalRefDate    -> the original invoice date
NumAtCard          -> the vendor's credit-note number
BPLID              -> the branch
per line: AccountCode, TaxCode (matching the original), LocationCode, CostingCode1..5
```

## Verify after saving

- [ ] `OriginalRefNo` and `OriginalRefDate` are both set. Read them back — SAP will not
      warn you. In HANA they are `RevRefNo` / `RevRefDate`.
- [ ] The tax code matches the original invoice, and an RCM original produced **two**
      reversed legs.
- [ ] The GL account and all five dimensions match the original line.
- [ ] `NumAtCard` carries the vendor's credit-note number, not ours.
- [ ] The journal is the original run backwards, not merely balanced.

## Open questions

1. ~~Should C-0024 be extended to A/R credit memos?~~ **Answered** — see above and
   [[AR-Credit-Memo]]. SAP enforces the pair on B2B GST credit notes (0 blanks in 5,055), so
   the sales-side gap is specifically **CDNUR** — credit notes to unregistered buyers, 3,366
   of them, 207 in the last four months. That is the correction candidate, not "extend
   C-0024".
2. The 44 Oil A/P credit memos with a missing reference — are they clustered by operator,
   period, or vendor? One query away, and it decides whether it is a cleanup or a habit.
3. Why does Oil have only 6 control accounts here against 14 on [[AP-Invoice]]? *Inferred:*
   credit memos concentrate on service and oil-purchase vendors. Unconfirmed.
4. `RevRefNo` on the *invoice* side (`OPCH`) — is it ever used there, and for what?

## Queries used

```sql
-- 1. Read the draft through the Service Layer to get the real property value
--    sapb1 query Drafts --filter "DocEntry eq 55128" --json
--    -> OriginalRefNo = 'RPL/1164/2026-27', OriginalRefDate = '2026-08-13'

-- 2. Find which HANA column holds it: search all 251 text columns of ODRF
--    (one UNION ALL statement per batch of 60)
SELECT 'RevRefNo' C FROM "JIVO_OIL_HANADB"."ODRF"
WHERE "DocEntry"=55128 AND "RevRefNo"='RPL/1164/2026-27';
-- only match out of 251 columns

-- 3. The real fill rate of the pair, per book
SELECT COUNT(*) TOTAL,
       SUM(CASE WHEN "RevRefNo" IS NOT NULL AND TRIM("RevRefNo")<>'' THEN 1 ELSE 0 END) REFNO,
       SUM(CASE WHEN "RevRefDate" IS NOT NULL THEN 1 ELSE 0 END) REFDATE,
       SUM(CASE WHEN ("RevRefNo" IS NULL OR TRIM("RevRefNo")='')
                  OR "RevRefDate" IS NULL THEN 1 ELSE 0 END) INCOMPLETE
FROM "JIVO_OIL_HANADB"."ORPC";
-- Oil 1595 / 1552 / 1551 / 44 · Mart 781 / 766 / 763 / 18 · Bev 248 / 245 / 245 / 3

-- 4. The same field on the sales side
SELECT COUNT(*) TOTAL,
       SUM(CASE WHEN "RevRefNo" IS NOT NULL AND TRIM("RevRefNo")<>'' THEN 1 ELSE 0 END) REFNO
FROM "JIVO_OIL_HANADB"."ORIN";
-- Oil 6434 / 3830 (59.5%) · Mart 4545 / 2305 (50.7%) · Bev 438 / 355 (81.1%)

-- 5. RetInvoice is a flag, not a reference
SELECT "RetInvoice" V, COUNT(*) N FROM "JIVO_OIL_HANADB"."ORPC"
GROUP BY "RetInvoice";
-- N x 1595, single value
```

Field profiles: `_data/profile-ORPC.md`, `_data/profile-RPC1.md`. GL fingerprint:
`_data/gl-19-OIL.md`.
