---
type: document
sap_tables: [OITR, ITR1]
objtype: -1
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Internal Reconciliation — how a bill actually gets marked paid

> 49,840 rows across the books, and the step that answers the one question `DocStatus`
> cannot: *has this actually been settled?*

This note exists because [[Purchase-to-Pay]] leaves a hole: 58% of vendor payments settle
nothing specific at the time, so matching happens **here**, afterwards. Understanding this
table is how you stop guessing.

## At a glance

| | |
|---|---|
| SAP tables | `OITR` header (one reconciliation) · `ITR1` lines (the things reconciled) |
| Volume | Oil 30,084 · Mart 13,403 · Bev 6,353 · **49,840** |
| Key | `ReconNum` — **not** `DocEntry`. This is not a document |
| Cancellable | Yes — `Canceled` + `CancelAbs` point at the reversing reconciliation |

## Correction: reconciliations DO have an owner

> [!warning] A claim to stop repeating
> `acc/INVENTORY.md` (2026-08-23) records that the 6,409 reconciliations in its 90-day window
> "carry no `UserSign`", and I repeated that in [[Purchase-to-Pay]] and [[Outgoing-Payment]]
> before checking it. **It is wrong.** `OITR` has a `UserSign` column, it is never null, and
> most rows carry a real user.

Measured, Oil, all history:

| `IsSystem` | Rows | `UserSign` null | `UserSign` = 0 | **Named user** |
|---|---:|---:|---:|---:|
| `Y` — SAP did it | 25,775 | 0 | 8,930 | 16,845 |
| `N` — a person did it | 4,310 | 0 | 1,462 | **2,848** |

And the manual ones have names on them:

| User | Name | Manual reconciliations |
|---:|---|---:|
| 20 | Preshit Thakur | 989 |
| 12 | Bhawani | 575 |
| 14 | Taran | 300 |
| 15 | Lovpreet Singh | 241 |
| 16 | Neetu | 153 |
| 17 | Harsh | 125 |
| 13 | Dolly Gupta | 124 |
| 0 | *(system / unattributed)* | 1,462 |

So the real picture: **86% of reconciliations are automatic** (`IsSystem` = `Y` — SAP creates
them the moment a payment is applied to a document) and **14% are a person working the
reconciliation screen**, with a name attached in two thirds of those cases.

That is a materially different conclusion from "nobody owns it". The step has owners; it just
does not produce a document, so it is invisible to anyone looking at document tables.

## What gets reconciled

`ITR1."SrcObjTyp"`, Oil:

| ObjType | Document | Lines |
|---:|---|---:|
| 13 | [[AR-Invoice]] | 25,801 |
| **60** | **[[Goods-Issue]]** | **21,173** |
| 18 | [[AP-Invoice]] | 20,922 |
| 24 | [[Incoming-Payment]] | 11,725 |
| 46 | [[Outgoing-Payment]] | 11,309 |
| 59 | [[Goods-Receipt]] | 8,291 |
| 20 | [[GRPO]] | 7,077 |
| 30 | [[Journal-Entry]] | 6,433 |
| 14 | [[AR-Credit-Memo]] | 5,217 |
| 202 | [[Production-Order]] | 2,363 |

Two surprises:

1. **Goods issues and receipts are reconciled** — 21,173 + 8,291 lines. *Inferred:* these are
   the automatic inventory-clearing reconciliations SAP makes when stock movements offset,
   not accounts-receivable work. **Unverified** but consistent with `IsSystem` = `Y`
   dominating and `IsCard` = `A` (account, not card) on those `ReconType`s.
2. **6,433 lines reconcile a manual [[Journal-Entry]]** — this is the mechanism behind
   **C-0019**. An invoice cleared by journal is reconciled against the journal, so the
   invoice's own `DocStatus` never learns about it.

## The reconciliation types

`ReconType` with `IsCard`, Oil:

| `IsSystem` | `ReconType` | `IsCard` | Rows | *Inferred* meaning |
|---|---:|---|---:|---|
| `Y` | 3 | `C` | 8,759 | automatic, business-partner |
| `Y` | 14 | `A` | 8,076 | automatic, GL account |
| `Y` | 13 | `A` | 4,970 | automatic, GL account |
| **`N`** | **0** | **`C`** | **4,157** | **manual, business-partner** — the reconciliation screen |
| `Y` | 4 | `C` | 2,388 | automatic, business-partner |
| `Y` | 5 | `C` | 990 | automatic |
| `Y` | 7 | `C` | 328 | automatic |
| `Y` | 11 | `A` | 218 | automatic (single user, `0`) |
| `N` | 7 | `C` | 82 | manual |

`IsCard` = `C` means the reconciliation is against a **business partner** subledger; `A`
means a **GL account**. The type numbers themselves are **not decoded** — SAP's meanings are
not in the data. Open question below.

## How to answer "has this bill been paid?"

This is the operator-facing point of the note. `DocStatus` cannot tell you **(C-0019)**, and
`PaidToDate` only sees payments applied *to that document*. The reliable path:

```sql
-- 1. Everything ever reconciled against one document
SELECT r."ReconNum", r."ReconDate", r."IsSystem", r."Canceled",
       l."ReconSum", l."IsCredit", l."ShortName"
FROM "JIVO_OIL_HANADB"."ITR1" l
JOIN "JIVO_OIL_HANADB"."OITR" r ON r."ReconNum" = l."ReconNum"
WHERE l."SrcObjTyp" = '18'        -- A/P invoice
  AND l."SrcObjAbs" = <DocEntry>
  AND r."Canceled" = 'N';
```

Then, for the party as a whole, the authoritative figure is `OCRD."Balance"` — which is what
C-0019 tells you to age from, and which already nets everything: documents, payments,
journals and reconciliations. **Do not rebuild it from documents.**

Order of trust, highest first:

1. `OCRD."Balance"` — the party's real position
2. `ITR1` / `OITR` — what was actually matched against this document
3. `PaidToDate` on the document — only payments applied directly to it
4. `DocStatus` — **carries no reliable settlement information**

## Traps

1. **`OITR` is keyed on `ReconNum`, not `DocEntry`.** It is not a document and has no
   `DocNum`, no series, no branch, no approval.
2. **`UserSign` exists and is populated** — the "no UserSign" claim is wrong. But `UserSign`
   = 0 on 10,392 rows, so attribution is incomplete rather than absent.
3. **A reconciliation can be cancelled** — check `Canceled` = `N` and note `CancelAbs` points
   at the reversal. A query that ignores it double-counts.
4. **Most reconciliations are inventory, not receivables.** Goods issue (21,173) and receipt
   (8,291) lines outnumber A/P invoice lines. Filter on `SrcObjTyp` for the question you are
   actually asking.
5. **`ReconType` numbers are undecoded.** Do not infer meaning from the number.
6. **A journal-cleared invoice is reconciled against the journal**, never against itself.
   That is why it looks open forever. **(C-0019)**

## Open questions

1. **What does each `ReconType` mean?** Nine combinations in use, none documented in the
   data. SAP's own list would settle it; worth asking someone with access to the client's
   reconciliation screen.
2. Why is `UserSign` = 0 on 1,462 *manual* reconciliations, when 2,848 carry a name? An older
   period, or an integration login?
3. Are the goods-issue and goods-receipt reconciliations genuinely automatic inventory
   clearing? *Inferred* from `IsSystem` and `IsCard`, not proven.
4. `ReconRule1` / `ReconRule2` on `OITR` — not examined. They may explain the type numbers.
5. Mart runs 13,403 reconciliations against Oil's 30,084 on a much smaller ledger — is
   Mart's payment matching more manual, or just more numerous?

## Queries used

```sql
-- who creates reconciliations, and is UserSign really absent?
SELECT "IsSystem", COUNT(*) N,
       SUM(CASE WHEN "UserSign" IS NULL THEN 1 ELSE 0 END) NULL_US,
       SUM(CASE WHEN "UserSign"=0    THEN 1 ELSE 0 END) ZERO_US,
       SUM(CASE WHEN "UserSign">0    THEN 1 ELSE 0 END) REAL_US
FROM "JIVO_OIL_HANADB"."OITR" GROUP BY "IsSystem";
-- N: 4,310 rows, 0 null, 1,462 zero, 2,848 named
-- Y: 25,775 rows, 0 null, 8,930 zero, 16,845 named

-- the people doing it by hand
SELECT O."UserSign", U."U_NAME", COUNT(*) N
FROM "JIVO_OIL_HANADB"."OITR" O
LEFT JOIN "JIVO_OIL_HANADB"."OUSR" U ON U."USERID"=O."UserSign"
WHERE O."IsSystem"='N'
GROUP BY O."UserSign", U."U_NAME" ORDER BY N DESC;

-- what gets reconciled
SELECT "SrcObjTyp", COUNT(*) N FROM "JIVO_OIL_HANADB"."ITR1"
GROUP BY "SrcObjTyp" ORDER BY N DESC;

-- the type matrix
SELECT "IsSystem", "ReconType", "IsCard", COUNT(*) N
FROM "JIVO_OIL_HANADB"."OITR"
GROUP BY "IsSystem","ReconType","IsCard" ORDER BY N DESC;
```
