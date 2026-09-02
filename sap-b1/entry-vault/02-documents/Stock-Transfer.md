---
type: document
sap_tables: [OWTR, WTR1]
objtype: 67
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Stock Transfer — moving goods between warehouses

> 16,132 documents and **15,289 drafts** — the third-most-drafted document in the books,
> behind only [[AP-Invoice]] and [[AR-Invoice]]. Almost all of it is Oil, and almost all of
> it is inside one site.

Accounts does not key these; the factory does. They matter here because they move ₹1,006 Cr
a year through inventory accounts, and because 2,891 approval requests in 90 days land on
someone's desk.

## At a glance

| | |
|---|---|
| SAP tables | `OWTR` header · `WTR1` lines |
| ObjType / TransType | **67** |
| Volume | Oil 12,204 · Mart 1,728 · Bev 2,200 · **16,132** |
| Last 120 days | Oil 2,396 · Mart 592 · Bev 497 |
| Drafts | **15,289** — 3rd most drafted document type |
| Who keys it | 22 logins in Oil; three do 80% (`UserSign` 33 ×5,385, 36 ×2,785, 35 ×1,634) |
| Needs approval? | **Usually** — `WddStatus` `P` on 10,848 of 12,204 |
| `DocType` | `I` only — single-valued. Always an item document |
| Value moved | **₹1,006 Cr** in 365 days (Oil), 7,320 journals |

## `DocStatus` here means something different — read this before any report

| `DocStatus` | `CANCELED` | Count | Oldest | Newest |
|---|---|---:|---|---|
| `O` | `N` | **12,170** | 2024-09-30 | 2026-08-24 |
| `C` | `Y` | 34 | 2025-03-29 | 2026-08-05 |

**`DocStatus` = `O` on every live stock transfer, forever.** It never closes — a completed
transfer stays "open". And `C` correlates perfectly with `CANCELED` = `Y`: on this document
**"closed" means cancelled**, not completed.

So the C-0019 warning ("`DocStatus = 'O'` is unreliable") is *understated* here. On an
[[AP-Invoice]] the field is unreliable; on a stock transfer it carries **no completion
information at all**. Never build an "open transfers" report from it.

Also note `CANCELED` is **two-valued** here — `N` 12,170, `Y` 34, **no `C` mirror**. So
C-0021's three-valued rule is table-specific: check per table rather than assuming.
→ [[Document-Status-and-Cancellation]]

## Where it comes from

| Base | Lines (Oil, 365d) | Share |
|---|---:|---:|
| **keyed from scratch** (`-1` and `0`) | 29,410 | **84.6%** |
| `1250000001` — [[Inventory-Transfer-Request]] | 4,530 | 13.0% |
| `67` — another stock transfer | 841 | 2.4% |

By document: **80.2% fully keyed**, 19.7% copied from a request. So the transfer request
exists but is the exception — most movement is entered directly.

Two representations of "no base" appear: `BaseType` `-1` (29,273 lines) **and** `0` (137).
Any query testing only `= -1` misses 137 lines. Treat both as keyed.

Downstream: **98% of lines are never copied onward.** A stock transfer is a terminal document.

## The routes — it is mostly internal to one site

Top warehouse pairs, Oil, 365 days:

| From | To | Lines |
|---|---|---:|
| `BH-BS` | `BH-PC` | 6,854 |
| `BH-PC` | `BH-WST` | 4,146 |
| `BH-PM` | `BH-PC` | 3,515 |
| `BH-PM` | `BH-BS` | 3,452 |
| `BH-PF` | `GP-FG` | 2,185 |
| `BH-LO` | `BH-PC` | 1,304 |
| `BH-PF` | `BH-EC` | 747 |

Every high-volume route is `BH-*` → `BH-*` — *inferred:* the `BH` prefix is the factory site
and these are stage-to-stage movements inside it (bulk store → process → warehouse), not
branch-to-branch logistics. `BH-PF` → `GP-FG` is the only cross-prefix route in the top
seven. **Unverified** — the warehouse code convention is an open question for
[[Warehouses-and-Locations]].

Consistent with that: `BPLId` is `2` FACTORY on 11,497 of 12,204 (94%), and `OcrCode5` (the
state dimension) is filled on only **102 of 34,781** lines. If these were inter-state
movements the state dimension would be populated. **So the GST and e-way-bill exposure is
much smaller than the volume suggests** — most of this stock never leaves the site.

## The journal it posts

TransType 67. Oil, 365 days: 7,320 journals, 16,190 lines, **₹1,006 Cr each way**.

| Account | Name | Lines | Value each way |
|---|---|---:|---:|
| `1103005` | Packaging materials oil | 6,407 | ₹47.80 Cr |
| `1103001` | **Finished goods oil** | 5,426 | **₹328.76 Cr** |
| `1103006` | **Raw material oil** | 2,378 | **₹609.99 Cr** |
| `5100013` | Cost of goods sold | 780 | ₹9.58 Cr |
| `1103010` | Packaging material foods | 540 | ₹0.75 Cr |
| `1103002` | Finished goods food | 468 | ₹6.85 Cr |
| `1103011` | Raw material foods | 130 | ₹2.58 Cr |
| `1103004` | Finished goods tradable | 48 | ₹0.20 Cr |
| `1205006` | Office equipments | 8 | ₹0.02 Cr |
| `5300015` | **Inventory variance** | **1** | ₹9,621 Dr only |

Every account is **both Dr and Cr in equal amounts** — the signature of a transfer: value
leaves one warehouse's account and enters another's, same account code, net zero. That is
the check: **if a stock-transfer journal is not net-zero per account, something is wrong.**

Two exceptions worth noting:

- `1103005` is Dr ₹477,995,928 and Cr ₹478,005,549 — **off by ₹9,621**, which is exactly the
  single `5300015` INVENTORY VARIANCE line. So a valuation difference on a transfer lands in
  a variance account. Once in a year.
- `5100013` COST OF GOODS SOLD appears on 780 lines. *Inferred:* transfers into a
  consumption or sales warehouse. **Unverified** — worth one query, because a transfer
  touching COGS is not obviously a transfer.

## Fields that matter

| Field | Reads as | Notes |
|---|---|---|
| `DocType` | Always `I` | Single-valued — no service transfers |
| `FromWhsCod` / `WhsCode` (line) | From / to warehouse | The whole point of the document |
| `Quantity` (line) | **In pieces, not cartons** | **(C-0001)** |
| `BPLId` | Branch | 3 values: `2` FACTORY 11,497 · `1` DELHI 434 · `3` PUNJAB 273 |
| `BPLName` | Branch name | **5 values for 3 branches** — `FACTORY`/`Factory`, `DELHI`/`Delhi`. Group by the **id** |
| `WddStatus` | Approval | `P` 10,848 · `-` 1,172 · `A` 184 |
| `Series` | 24 values | Book-local → [[Numbering-Series]] |
| `DocStatus` | **Not completion** | See above |

## Traps

1. **`DocStatus` never becomes `C` for a completed transfer.** `O` is permanent; `C` means
   cancelled. Do not report "open transfers".
2. **`CANCELED` is two-valued here** — no `C` mirror, unlike [[GRPO]] and [[AP-Invoice]].
   C-0021 is a per-table fact.
3. **`BPLName` has duplicate capitalisations** (5 strings for 3 branches). Same defect as on
   [[GRPO]]. Group by `BPLId`.
4. **Two "no base" values** — `BaseType` `-1` and `0`. Test both.
5. **Quantity is in pieces.** **(C-0001)**
6. **A transfer journal must net to zero per account.** Anything else is a valuation
   difference and lands in `5300015`.
7. **Most transfers are intra-site**, so do not assume an e-way bill or GST exposure from the
   volume. `OcrCode5` is filled on 0.3% of lines.

## Open questions

1. **What does the `BH-` prefix mean, and what are `BS`, `PC`, `PM`, `PF`, `WST`, `LO`, `EC`?**
   Decoding the warehouse convention would make this note far more useful, and it belongs in
   [[Warehouses-and-Locations]].
2. Why do 780 lines touch `5100013` COST OF GOODS SOLD? A transfer should not hit a P&L
   account.
3. The single `5300015` INVENTORY VARIANCE line of ₹9,621 — one event in a year. What
   happened, and is the mechanism reliable enough that a bigger difference would also be
   caught?
4. What distinguishes the 184 documents with `WddStatus` = `A` from the 10,848 with `P`?
   → [[Approval-Workflow]]
5. Mart runs only 1,728 transfers against Oil's 12,204 but has 20 branches. Does Mart move
   stock some other way, or does it not hold stock?
6. 15,289 drafts against 16,132 posted — nearly one each, like [[AP-Invoice]]. Yet the
   drafted-first ratio computed over a 365-day window came out low. Worth reconciling.

## Queries used

```sql
-- DocStatus carries no completion information here
SELECT "DocStatus", "CANCELED", COUNT(*) N, MIN("DocDate") OLDEST, MAX("DocDate") NEWEST
FROM "JIVO_OIL_HANADB"."OWTR" GROUP BY "DocStatus","CANCELED";
-- O/N 12,170 (all live) | C/Y 34 (all cancelled)

-- the routes
SELECT L."FromWhsCod" FROM_W, L."WhsCode" TO_W, COUNT(*) LINES
FROM "JIVO_OIL_HANADB"."WTR1" L
JOIN "JIVO_OIL_HANADB"."OWTR" H ON H."DocEntry"=L."DocEntry"
WHERE H."DocDate" >= ADD_DAYS(CURRENT_DATE,-365)
GROUP BY L."FromWhsCod", L."WhsCode" ORDER BY LINES DESC;

-- is any of this inter-state?
SELECT COUNT(*) N,
       SUM(CASE WHEN L."OcrCode5" IS NOT NULL AND TRIM(L."OcrCode5")<>'' THEN 1 ELSE 0 END) HAS_STATE
FROM "JIVO_OIL_HANADB"."WTR1" L
WHERE L."DocDate" >= ADD_DAYS(CURRENT_DATE,-365);
-- 34,781 lines, 102 with a state dimension
```

Profile: `_data/profile-OWTR.md`, `profile-WTR1.md`. GL: `_data/gl-67-OIL.md` (also MART,
BEV). Flow: `_data/flow-OWTR-OIL.md`.
