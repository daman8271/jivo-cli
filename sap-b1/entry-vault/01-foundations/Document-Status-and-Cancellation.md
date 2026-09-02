---
type: foundation
sap_tables: [OPCH, OINV, OPDN, ODLN, ORDR, OPOR, ORIN, ORPC, ORDN, ORPD, OWTR, OWTQ, OIGN, OIGE, OQUT, ORRR, ODRF, OIPF, ORCT, OVPM, OPDF, OWOR, OWDD, OITR, ITR1, VPM2, OJDT]
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Document status and cancellation — what "open", "closed" and "cancelled" actually mean

> Five one-letter columns claim to tell you the state of a document. Three of them lie in
> different ways, one is dead, and the one an operator most wants — *is this bill already
> paid?* — is not any of them. This note is the decoder, measured in all three books.

## The short version

1. **`DocStatus`** has exactly two values, `O` and `C`, in every table and every book. On an
   invoice `C` means **`PaidToDate` reached `DocTotal`** — nothing more. It is an exact
   arithmetic fact, not an opinion, and it is **not** "settled": a bill paid by a manual
   journal entry or by an unapplied on-account payment stays `O` for ever. **(C-0019)**
2. **`CANCELED`** is three-valued on the documents that post a ledger entry: `N` live,
   `Y` the cancelled original, `C` the system's mirror. **Both** the `Y` and the `C` row
   carry the full positive amount, so a `<> 'Y'` filter double-counts. Always `= 'N'`.
   **(C-0021)**
3. On **payments** it is two-valued (`N`/`Y`) — no mirror row. The reversal lives in the
   **ledger** instead, as a journal entry pointing back with `StornoToTr`.
4. **`WddStatus`** is not a hint — it is literally the approval request's `OWDD.ProcesStat`,
   proven 1:1 in all three books. Only `W` and `Y` are alive; `C` and `N` are dead work.
5. **`Transfered`** is `N` on every row of every table in all three books. Dead column.
   **`InvntSttus`** disagrees with `DocStatus` on half of live A/P invoices and tracks
   nothing we could identify — do not read it.

**And the operator's real question:** to know whether a bill is already in SAP, search
`NumAtCard` across [[AP-Invoice]] **and** [[Document-Drafts]], including cancelled rows.
To know whether it is paid, read `PaidToDate` and the vendor's `Balance` — never
`DocStatus`. Both queries are in [§ 9](#9-the-two-questions-an-operator-actually-has).

---

## 1. The five letters, and what each one really tracks

| Column | HANA type | Values seen at JIVO | What it actually tracks | Trust it? |
|---|---|---|---|---|
| `DocStatus` | `NVARCHAR(1)` | `O`, `C` — **never anything else** | Invoices: `PaidToDate = DocTotal`. Receipts/orders: lines fully drawn into the next document. Drafts: `C` = it became a document. Transfers/goods receipts: **never closes**, `C` only ever means cancelled | Only if you know which family you are in |
| `CANCELED` / `Canceled` | `NVARCHAR(1)` | `N`, `Y`, `C` | `N` live · `Y` cancelled original · `C` the system's reversing mirror **document** | Yes — but only with `= 'N'` |
| `WddStatus` | `NVARCHAR(1)` | `-`, `P`, `A`, `C`, `N`, `W`, `Y` | The approval request's process state, copied from `OWDD.ProcesStat` | Yes, and it is the **only** reliable state of a draft |
| `InvntSttus` | `NVARCHAR(1)` | `O`, `C` | Unknown. Disagrees with `DocStatus` on 49% of live Oil A/P invoices and does not follow the item lines' own `LineStatus` | **No** |
| `Transfered` | `NVARCHAR(1)` | `N` only, everywhere | Nothing. SAP offers it, JIVO never uses it | Ignore |

Payments have **no `DocStatus` column at all**. They carry `Status`, and it is `N` on
14,149 / 11,391 / 4,166 incoming and 14,851 / 2,294 / 1,925 outgoing rows — 100% of every
row in all three books. A second dead column.

Service-Layer names differ from all of these — `DocumentStatus` with `bost_Open` /
`bost_Close`, `Cancelled` with two `l`s. See [[Field-Name-Rosetta]].

---

## 2. The full distribution — every status letter, every major table, all three books

Measured 2026-08-24, all history, live from HANA. `–` = the column does not exist on that
table; blank = the table is empty in that book.

### Purchase side

| Table | Field | OIL | MART | BEV |
|---|---|---|---|---|
| `OPCH` [[AP-Invoice]] | `DocStatus` | `C`×12,025 · `O`×4,309 | `O`×2,912 · `C`×1,952 | `C`×2,619 · `O`×551 |
| | `CANCELED` | `N`×16,108 · `Y`×113 · `C`×113 | `N`×4,782 · `Y`×41 · `C`×41 | `N`×3,154 · `Y`×8 · `C`×8 |
| | `WddStatus` | `P`×14,250 · `-`×2,084 | `P`×3,353 · `-`×1,510 · `Y`×1 | `P`×3,061 · `-`×109 |
| | `InvntSttus` | `C`×9,677 · `O`×6,657 | `O`×2,983 · `C`×1,881 | `C`×1,919 · `O`×1,251 |
| `OPDN` [[GRPO]] | `DocStatus` | `C`×11,279 · `O`×370 | `C`×3,189 · `O`×33 | `C`×4,648 · `O`×178 |
| | `CANCELED` | `N`×10,703 · `Y`×473 · `C`×473 | `N`×3,036 · `Y`×93 · `C`×93 | `N`×4,568 · `Y`×129 · `C`×129 |
| | `WddStatus` | `-`×7,368 · `P`×4,148 · `A`×133 | `-`×2,318 · `P`×902 · `A`×2 | `-`×4,182 · `P`×644 |
| | `InvntSttus` | `C`×11,354 · `O`×295 | `C`×3,214 · `O`×8 | `C`×4,749 · `O`×77 |
| `ORPC` [[AP-Credit-Memo]] | `DocStatus` | `C`×1,276 · `O`×319 | `C`×413 · `O`×368 | `C`×245 · `O`×3 |
| | `CANCELED` | `N`×1,567 · `Y`×14 · `C`×14 | `N`×725 · `Y`×28 · `C`×28 | `N`×244 · `Y`×2 · `C`×2 |
| | `WddStatus` | `P`×1,566 · `-`×29 | `P`×490 · `-`×291 | `P`×246 · `-`×2 |
| | `InvntSttus` | `C`×1,496 · `O`×99 | `C`×511 · `O`×270 | `C`×232 · `O`×16 |
| `OPOR` [[Purchase-Order]] | `DocStatus` | `C`×3,975 · `O`×350 | `C`×2,115 · `O`×143 | `C`×918 · `O`×223 |
| | `CANCELED` | `N`×4,292 · `Y`×33 — **no mirror** | `N`×2,167 · `Y`×91 | `N`×1,140 · `Y`×1 |
| | `WddStatus` | `-`×2,166 · `P`×2,159 | `-`×2,056 · `P`×202 | `P`×962 · `-`×179 |
| | `InvntSttus` | `C`×3,182 · `O`×1,143 | `O`×1,187 · `C`×1,071 | `C`×860 · `O`×281 |
| `ORPD` [[Goods-Return]] | `DocStatus` | `C`×109 · `O`×8 | `C`×43 · `O`×16 | `C`×30 · `O`×3 |
| | `CANCELED` | `N`×103 · `Y`×7 · `C`×7 | `N`×49 · `Y`×5 · `C`×5 | `N`×19 · `Y`×7 · `C`×7 |
| | `WddStatus` | `P`×98 · `-`×19 | `-`×37 · `P`×22 | `P`×20 · `-`×13 |
| | `InvntSttus` | `C`×100 · `O`×17 | `C`×43 · `O`×16 | `C`×26 · `O`×7 |

### Sales side

| Table | Field | OIL | MART | BEV |
|---|---|---|---|---|
| `OINV` [[AR-Invoice]] | `DocStatus` | `C`×18,028 · `O`×13,056 | `C`×21,379 · `O`×4,373 | `C`×4,423 · `O`×1,167 |
| | `CANCELED` | `N`×30,444 · `Y`×320 · `C`×320 | `N`×25,232 · `Y`×260 · `C`×260 | `N`×5,346 · `Y`×122 · `C`×122 |
| | `WddStatus` | `-`×22,712 · `P`×8,370 · `A`×2 | `-`×22,134 · `P`×3,618 | `P`×4,936 · `-`×654 |
| | `InvntSttus` | `O`×18,637 · `C`×12,447 | `O`×24,854 · `C`×898 | `O`×5,255 · `C`×335 |
| `ORIN` [[AR-Credit-Memo]] | `DocStatus` | `C`×4,751 · `O`×1,683 | `C`×4,077 · `O`×468 | `C`×392 · `O`×46 |
| | `CANCELED` | `N`×6,148 · `Y`×143 · `C`×143 | `N`×4,393 · `Y`×76 · `C`×76 | `N`×400 · `Y`×19 · `C`×19 |
| | `WddStatus` | `-`×5,171 · `P`×1,262 · `A`×1 | `-`×3,588 · `P`×957 | `P`×254 · `-`×184 |
| | `InvntSttus` | `O`×3,451 · `C`×2,983 | `O`×3,574 · `C`×971 | `C`×266 · `O`×172 |
| `ODLN` [[Delivery]] | `DocStatus` | `C`×2,829 · `O`×13 | `C`×6,124 · `O`×2 | `C`×297 · `O`×6 |
| | `CANCELED` | `N`×2,792 · `Y`×25 · `C`×25 | `N`×6,024 · `Y`×51 · `C`×51 | `N`×287 · `Y`×8 · `C`×8 |
| | `WddStatus` | `-`×1,688 · `P`×1,153 · `A`×1 | `-`×4,604 · `P`×1,522 | `P`×265 · `-`×38 |
| | `InvntSttus` | `C`×2,487 · `O`×355 | `C`×6,115 · `O`×11 | `C`×290 · `O`×13 |
| `ORDN` [[AR-Return]] | `DocStatus` | `C`×1,991 · `O`×40 | `C`×1,822 · `O`×25 | `C`×153 · `O`×34 |
| | `CANCELED` | `N`×1,817 · `Y`×107 · `C`×107 | `N`×1,795 · `Y`×26 · `C`×26 | `N`×161 · `Y`×13 · `C`×13 |
| | `WddStatus` | `P`×1,024 · `-`×994 · `A`×13 | `-`×1,400 · `P`×447 | `P`×144 · `-`×43 |
| | `InvntSttus` | `C`×1,968 · `O`×63 | `C`×1,806 · `O`×41 | `C`×151 · `O`×36 |
| `ORDR` [[Sales-Order]] | `DocStatus` | `C`×15,053 · `O`×80 | `C`×6,879 · `O`×796 | `C`×5,462 · `O`×116 |
| | `CANCELED` | `N`×15,062 · `Y`×71 — **no mirror** | `N`×7,193 · `Y`×482 | `N`×5,546 · `Y`×32 |
| | `WddStatus` | `-`×15,131 · `P`×2 | `-`×7,675 | `-`×5,578 |
| | `InvntSttus` | `C`×7,622 · `O`×7,511 | `C`×5,177 · `O`×2,498 | `C`×3,851 · `O`×1,727 |
| `OQUT` [[Sales-Quotation]] | `DocStatus` | `C`×1,632 · `O`×60 | *(none)* | `C`×696 · `O`×37 |
| | `CANCELED` | `N`×1,658 · `Y`×34 | | `N`×733 |
| | `WddStatus` | `-`×1,692 | | `-`×733 |
| | `InvntSttus` | `C`×1,045 · `O`×647 | | `C`×619 · `O`×114 |
| `ORRR` [[Return-Request]] | `DocStatus` | `C`×17 · `O`×15 | `C`×1 | *(none)* |
| | `CANCELED` | `N`×32 | `N`×1 | |
| | `WddStatus` | `-`×32 | `-`×1 | |

### Stock and production

| Table | Field | OIL | MART | BEV |
|---|---|---|---|---|
| `OWTR` [[Stock-Transfer]] | `DocStatus` | **`O`×12,170 · `C`×34** | `O`×1,710 · `C`×18 | `O`×2,189 · `C`×11 |
| | `CANCELED` | `N`×12,170 · `Y`×34 — **no `C` mirror** | `N`×1,709 · `Y`×19 | `N`×2,189 · `Y`×11 |
| | `WddStatus` | `P`×10,848 · `-`×1,172 · `A`×184 | `P`×1,298 · `-`×423 · `A`×5 · `Y`×2 | `P`×1,857 · `-`×329 · `A`×14 |
| | `InvntSttus` | `O`×12,051 · `C`×153 | `O`×1,653 · `C`×75 | `O`×2,166 · `C`×34 |
| `OWTQ` [[Inventory-Transfer-Request]] | `DocStatus` | `C`×1,227 · `O`×98 | `C`×699 · `O`×421 | `O`×48 · `C`×10 |
| | `CANCELED` | `N`×1,325 — never cancelled | `N`×1,120 | `N`×58 |
| | `WddStatus` | `P`×692 · `-`×633 | `-`×1,100 · `P`×19 · `A`×1 | `-`×58 |
| `OIGN` [[Goods-Receipt]] | `DocStatus` | **`O`×8,548 — 100%** | `O`×75 | `O`×1,477 |
| | `CANCELED` | `N`×8,548 | `N`×75 | `N`×1,477 |
| | `WddStatus` | `-`×8,541 · `P`×7 | `-`×75 | `-`×1,476 · `P`×1 |
| `OIGE` [[Goods-Issue]] | `DocStatus` | `O`×8,421 · `C`×1 | `O`×73 | `O`×1,405 |
| | `CANCELED` | `N`×8,422 | `N`×73 | `N`×1,405 |
| | `WddStatus` | `-`×8,421 · `P`×1 | `-`×73 | `-`×1,404 · `P`×1 |
| `OMRV` [[Inventory-Revaluation]] | — | *no status column at all* | | |
| `OWOR` [[Production-Order]] | `Status` | `L`×8,116 · `R`×163 · `C`×31 · `P`×23 | `L`×16 · `R`×10 · `C`×1 | `L`×1,194 · `R`×191 · `P`×57 · `C`×30 |
| `OIPF` [[Landed-Costs]] | `DocStatus` | `O`×532 · `C`×2 | *(none)* | `O`×6 |
| | `Canceled` | `N`×534 | | `N`×6 |

A production order uses a **completely different alphabet** — `P` planned, `R` released,
`L` closed ("cLosed"), `C` cancelled. `L` is the normal end state and `C` is the abnormal
one, which is the exact opposite reading from `DocStatus` elsewhere. *Letter meanings here
are inferred from the standard SAP vocabulary and the volumes; not independently confirmed.*

### Payments, drafts and reconciliations

| Table | Field | OIL | MART | BEV |
|---|---|---|---|---|
| `ORCT` [[Incoming-Payment]] | `Status` | `N`×14,149 — **dead** | `N`×11,391 | `N`×4,166 |
| | `Canceled` | `N`×13,653 · `Y`×496 — **no mirror** | `N`×11,143 · `Y`×248 | `N`×4,069 · `Y`×97 |
| | `WddStatus` | `-`×14,149 — never approved | `-`×11,391 | `-`×4,166 |
| `OVPM` [[Outgoing-Payment]] | `Status` | `N`×14,851 — **dead** | `N`×2,294 | `N`×1,925 |
| | `Canceled` | `N`×13,912 · `Y`×939 — **no mirror** | `N`×2,066 · `Y`×228 | `N`×1,786 · `Y`×139 |
| | `WddStatus` | `-`×13,540 · `P`×1,311 | `-`×2,294 — no approval in Mart | `-`×1,759 · `P`×166 |
| `OPDF` [[Payment-Draft]] | `Canceled` | **`Y`×1,376 · `N`×192** | `N`×18 · `Y`×2 | `Y`×169 · `N`×31 |
| | `WddStatus` | `-`×1,385 · `C`×150 · `Y`×21 · `N`×12 | `-`×19 · `Y`×1 | `-`×170 · `C`×23 · `Y`×4 · `N`×3 |
| | `Status` | `N`×1,568 — dead | `N`×20 | `N`×200 |
| `ODRF` [[Document-Drafts]] | `DocStatus` | `C`×45,457 · `O`×4,006 | `C`×13,271 · `O`×1,412 | `C`×12,664 · `O`×1,682 |
| | `CANCELED` | **`N`×49,463 — carries nothing** | `N`×14,683 | `N`×14,346 |
| | `WddStatus` | `-`×45,646 · `C`×2,967 · `N`×481 · `Y`×184 · `W`×184 · `P`×1 | `-`×13,519 · `C`×982 · `Y`×95 · `W`×44 · `N`×42 · `P`×1 | `-`×12,698 · `C`×1,469 · `N`×63 · `Y`×60 · `W`×56 |
| | `InvntSttus` | `O`×49,461 · `C`×2 | `O`×14,683 | `O`×14,346 |
| `OITR` [[Internal-Reconciliation]] | `Canceled` | `N`×29,151 · `Y`×467 · `C`×467 | `N`×12,969 · `Y`×217 · `C`×217 | `N`×6,153 · `Y`×100 · `C`×100 |

Two things in that block are the sharpest traps in this whole note:

- **`OPDF.Canceled` is `Y` on 1,376 of 1,568 Oil payment drafts — 88%**, and 169 of 200 in
  Beverages. A payment draft *does* use the cancelled flag, and almost all of them are
  cancelled. This is the exact opposite of `ODRF`, where `CANCELED` is `N` on all 78,492
  rows in all three books. Two draft tables, two completely different conventions.
- **`OITR.Canceled` is three-valued too** (`N`/`Y`/`C`, `Y` = `C` exactly in each book). The
  mirror pattern is not only a marketing-document thing — a cancelled internal
  reconciliation also leaves a twin row.

### The dead columns, stated once

| Column | Finding |
|---|---|
| `Transfered` | `N` on **every row of every table listed above, in all three books**. Never anything else |
| `ORCT`/`OVPM`/`OPDF`.`Status` | `N` on 100% of rows, all three books |
| `ODRF.CANCELED` | `N` on all 49,463 / 14,683 / 14,346 rows |
| `ORCT.WddStatus` | `-` on all 29,706 rows — incoming payments never enter approval anywhere |

---

## 3. A real cancellation pair — the two rows, and how they differ

Oil A/P invoices `DocEntry` **44118** and **44125**. Both live in `OPCH`, both belong to the
same vendor, both carry the same amount. One is the bill; one is SAP undoing it.

| | 44118 — the original | 44125 — the mirror |
|---|---|---|
| `CANCELED` | **`Y`** | **`C`** |
| `DocStatus` | `C` | `C` |
| `DocNum` | 726044115 | **726045101** — *its own number* |
| `Series` | 3668 | **3716** — often a different series |
| `DocDate` / `TaxDate` | 2026-04-30 | 2026-04-30 |
| `DocTotal` | 751.00 | **751.00 — same sign, not negative** |
| `CardCode` / `NumAtCard` | same vendor / same bill number | same vendor / same bill number |
| `JrnlMemo` | `A/P Invoices - VENDA000003` | **`A/P Invoice - Cancellation - VENDA000003`** |
| `draftKey` | may point at a draft | always empty |
| `UserSign` | the operator who keyed it (22) | usually `1` = `manager` |
| `CancelDate` | **`NULL`** | **`NULL`** |
| `TransId` → journal | 203804 | 203819 |

And the two journals, which is where the double-counting comes from:

| `TransId` | `TransType` | Account | Debit | Credit | `LineMemo` |
|---:|---:|---|---:|---:|---|
| 203804 | 18 | 2120002 (vendor control) | | 751.00 | A/P Invoices |
| 203804 | 18 | 2131002 (input GST) | 751.78 | | A/P Invoices |
| 203804 | 18 | 5680014 (expense) | | 0.78 | A/P Invoices |
| 203819 | 18 | 2120002 | **751.00** | | A/P Invoice - **Cancellation** |
| 203819 | 18 | 2131002 | | **751.78** | A/P Invoice - **Cancellation** |
| 203819 | 18 | 5680014 | **0.78** | | A/P Invoice - **Cancellation** |

An exact side-flip: same accounts, same amounts, opposite sides. Both journals carry
`TransType` 18, so the 24,368 A/P journal entries in the [[Entry-Types-Census]] include
113 + 41 + 8 = **162 cancellation mirrors**. `OJDT.StornoToTr` is **NULL** on both — the
marketing-document cancellation does *not* use SAP's journal-reversal link.

### Three ways to spot a mirror, all measured

| Test | Result |
|---|---|
| `CANCELED = 'C'` | The canonical test |
| `JrnlMemo LIKE '%Cancellation%'` | **Matches `CANCELED='C'` exactly** — 1:1 in `OPCH`, `OINV`, `OPDN`, `ORIN`, `ORPC`, `ORDN`, `ODLN`, `ORPD`, in all three books. Useful when a downstream report dropped the flag |
| `Y` count = `C` count | Holds in every table and book that has mirrors at all |

### Do the pair land in the same accounting period?

Usually. Pairing Oil `OPCH` on (`CardCode`, `DocTotal`, `NumAtCard`): **112 of 113 pairs
matched, 110 in the same month, 2 in a different month.** So a cancellation *can* push the
reversal into a later period — one April invoice was reversed with a 5 May document date.
Rare, but a month-end reconciliation that assumes the reversal is in the same month will be
out by those two.

`CancelDate` is `NULL` on all 16,334 / 4,864 / 3,170 `OPCH` rows. **You cannot tell when a
cancellation happened from that column** — use the mirror's `CreateDate`.

---

## 4. Which document types actually make a mirror

Measured from the value distributions in [§ 2](#2-the-full-distribution--every-status-letter-every-major-table-all-three-books). The dividing line is
whether the document posts to the ledger.

| Family | Mirror row? | How cancellation is recorded |
|---|---|---|
| A/P + A/R invoices, credit memos, returns, GRPO, delivery, goods return | **Yes** — `Y` original + `C` mirror | A second document in the same table, with a reversing journal |
| Sales order, purchase order, quotation, transfer request | **No** — `Y` only | Nothing posts, so nothing needs reversing. The row is just flagged |
| Stock transfer (`OWTR`) | **No `C`** — but see below | `Y` on the original; `DocStatus` flips to `C` |
| Goods receipt / goods issue (`OIGN`/`OIGE`) | **Never cancelled at all** — `CANCELED` is `N` on all 10,100 / 9,900 rows | JIVO has never cancelled one |
| Payments (`ORCT`/`OVPM`) | **No** — `Y` only | A **reversing journal entry** in `OJDT` (see [§ 5](#5-payments-cancel-in-the-ledger-not-in-the-payment-table)) |
| Internal reconciliation (`OITR`) | **Yes** — `Y` + `C` | A twin reconciliation row |
| Drafts (`ODRF`) | n/a | `CANCELED` unused; the state is `WddStatus = 'C'` |
| Payment drafts (`OPDF`) | n/a | `Canceled = 'Y'` — and 88% of Oil ones are |

### The stock-transfer oddity, chased down

Mart has 19 `OWTR` rows with `CANCELED='Y'` but only 18 with `DocStatus='C'`. The odd one
out is `DocEntry` 2877, `DocNum` 626674526, whose own `Comments` read
*"Inventory transfer no. 626674525 has been canceled"* — it **is** the cancellation
document, sitting one `DocEntry` after the original (2876, `DocNum` 626674525, `DocStatus`
`C`). So on a stock transfer the cancellation document exists but is flagged `Y`, not `C`,
and stays `DocStatus = 'O'`.

Consequence: `CANCELED = 'N'` still excludes both rows correctly, but **counting cancelled
transfers from `Y` counts the cancellation document as a cancellation.** Only 1 of 19 Mart
rows is identifiable this way (via the comment); whether the other 17 have silent partners
is unresolved — see [Open questions](#open-questions).

### Cancellation rates — the trap does most damage where volume is

Rate = `Y` ÷ (`N` + `Y`), so mirrors are excluded from the denominator.

| Document | OIL | MART | BEV |
|---|---:|---:|---:|
| [[GRPO]] | **4.23%** (473) | **2.97%** (93) | **2.75%** (129) |
| [[AP-Invoice]] | 0.70% (113) | 0.85% (41) | 0.25% (8) |
| [[AR-Invoice]] | 1.04% (320) | 1.02% (260) | 2.23% (122) |
| [[AR-Return]] | 5.56% (107) | 1.43% (26) | 7.47% (13) |
| [[Goods-Return]] | 6.36% (7) | 9.26% (5) | 26.9% (7) |
| [[Sales-Order]] | 0.47% (71) | **6.28%** (482) | 0.57% (32) |
| [[Purchase-Order]] | 0.76% (33) | 4.03% (91) | 0.09% (1) |
| [[Stock-Transfer]] | 0.28% (34) | 1.10% (19) | 0.50% (11) |
| [[Incoming-Payment]] | 3.51% (496) | 2.18% (248) | 2.33% (97) |
| [[Outgoing-Payment]] | **6.32%** (939) | **9.94%** (228) | **7.22%** (139) |
| [[Payment-Draft]] | **87.8%** (1,376) | 10.0% (2) | **84.5%** (169) |

**Confirmed:** GRPOs are cancelled far more than A/P invoices — 6× in Oil, 3.5× in Mart,
11× in Beverages. The direction holds in all three books. **New:** payments are cancelled
more than anything else that posts (6–10%), and Mart cancels sales orders at 6.28% against
Oil's 0.47% — a 13× difference in the same group, on the same document type.

---

## 5. Payments cancel in the ledger, not in the payment table

Cancelling a payment leaves no second row in `ORCT`/`OVPM`. It writes a **reversing journal
entry** whose `OJDT.StornoToTr` points at the original payment's journal. That produces an
exact counting identity, which holds in all three books:

| Book | `OVPM` rows | of which cancelled | `OJDT` `TransType` 46 | rows + cancelled |
|---|---:|---:|---:|---:|
| OIL | 14,851 | 939 | **15,790** | 15,790 ✓ |
| MART | 2,294 | 228 | **2,522** | 2,522 ✓ |
| BEV | 1,925 | 139 | **2,064** | 2,064 ✓ |

| Book | `ORCT` rows | of which cancelled | `OJDT` `TransType` 24 | rows + cancelled |
|---|---:|---:|---:|---:|
| OIL | 14,149 | 496 | **14,645** | 14,645 ✓ |
| MART | 11,391 | 248 | **11,639** | 11,639 ✓ |
| BEV | 4,166 | 97 | **4,263** | 4,263 ✓ |

**So a payment count taken from the ledger is higher than one taken from the payment table,
and the difference is exactly the cancellations.** Count payments from `ORCT`/`OVPM` with
`Canceled = 'N'`; count *journals* from `OJDT` and know that you are including reversals.

Reversals in Oil, by origin: `TransType` 46 × 939, `TransType` 24 × 496, `TransType` 30
(manual journal) × 43. Nothing else. `AutoStorno` and `StornoDate` are never used in any
book.

**A journal entry itself has no cancelled flag.** The only way one is undone is a second
journal carrying `StornoToTr` — 1,478 in Oil, 530 in Mart, 248 in Beverages. Anything
built on [[Journal-Entry]] must net those out itself. → [[Internal-Reconciliation]]

---

## 6. `WddStatus` — no longer inferred

[[Document-Drafts]] recorded the six letters as *inferred from standard SAP vocabulary plus
the counts*. They are now **proven from the approval tables**, and the mechanism is more
useful than the letters.

`OWDD` (the approval request) carries two different status columns:

| Column | Meaning | OIL values |
|---|---|---|
| `Status` | The **approvers' decision** | `Y`×57,032 · `W`×1,712 · `N`×1,043 |
| `ProcesStat` | The **request's process state** | `P`×54,713 · `C`×3,489 · `N`×784 · `A`×377 · `Y`×220 · `W`×204 |

Joining `OWDD.DraftEntry` → `ODRF.DocEntry` for A/P drafts gives an exact 1:1 match in all
three books, with no exceptions:

| `OWDD.ProcesStat` | `OWDD.Status` | draft's `WddStatus` | draft's `DocStatus` | OIL | MART | BEV |
|---|---|---|---|---:|---:|---:|
| `P` | `Y` | **`-`** | `C` | 14,250 | 3,355 | 3,061 |
| `C` | `N` | `C` | `O` | 410 | 106 | 89 |
| `C` | `W` | `C` | `O` | 323 | 148 | 63 |
| `C` | `Y` | `C` | `O` | 84 | 169 | 20 |
| `W` | `W` | `W` | `O` | 95 | 10 | 35 |
| `Y` | `Y` | `Y` | `O` | 78 | — | 4 |
| `N` | `N` | `N` | `O` | 62 | 12 | 12 |

Read that table twice, because it settles four things:

1. **`WddStatus` on a draft *is* `OWDD.ProcesStat`.** Same letter, every row, every book.
2. **`ProcesStat` ∈ {`P`, `A`} ⟺ `OWDD.IsDraft = 'N'`** — the draft became a document.
   When that happens the draft's own `WddStatus` **resets to `-`** and its `DocStatus`
   becomes `C`, while the resulting **document** inherits `P`. That is why Oil `OPCH` has
   `WddStatus = 'P'` on exactly **14,250** rows — the same 14,250.
3. **`W` and `Y` are the only genuinely live states**, and they are pure: all 194 Oil `W`
   requests have `Status = 'W'`, all 220 `Y` requests have `Status = 'Y'`. **Confirmed.**
4. **`C` is not a decision.** Oil `ProcesStat = 'C'` splits `Status` `Y`×1,597 / `W`×1,347 /
   `N`×545 — approved, pending and rejected work all end up cancelled. **`WddStatus = 'C'`
   does not mean "rejected"; it means "this request was closed without producing a
   document".** `N` mixes the same way (`N`×498 / `W`×163 / `Y`×123), so both are simply
   dead ends.

`P` is confirmed as "generated" by the 14,250 identity. **`A` is not explained.** It is a
terminal, generated state like `P` (`IsDraft='N'`, `Status='Y'` on all 377 Oil rows), it
never appears on the same document as `P` (156 documents with `A` only, 27 with `A`/`A`,
never `A`/`P` in 11,000 Oil stock transfers), it never occurs on a payment draft
(`DraftType` 140), and it is not explained by template, workflow step, approving user, the
adding user, whether the document was later updated, or whether the draft row still exists
— all checked, all negative. → [Open questions](#open-questions)

### The live draft queue, per book, today

| Book | dead: `C` | dead: `N` | live: `W` waiting | live: `Y` approved | live: `-` no workflow | posted (`DocStatus` `C`) |
|---|---:|---:|---:|---:|---:|---:|
| OIL | **817** | 62 | 95 | 78 | 36 | 14,264 |
| MART | **414** | 12 | 10 | — | 23 | 3,375 |
| BEV | **172** | 12 | 35 | 4 | 4 | 3,065 |

Oil's genuinely live A/P queue is **209** of 1,088 "open" drafts — the previously recorded
817/1,088 split reproduces exactly. Mart's is **33** of 459 (93% dead); Beverages' is **43**
of 227 (81% dead). **Counting a backlog from `DocStatus='O'` overstates it 5× in Oil, 14× in
Mart and 5× in Beverages.**

### Why 817 drafts were cancelled — mostly, the bill was keyed again

New measurement. Matching each open draft to a live posted invoice on (`CardCode`,
`NumAtCard`):

| Book | cancelled drafts (`C`) | of which the same bill is **already posted** |
|---|---:|---:|
| OIL | 817 | **503** (62%) |
| MART | 414 | **290** (70%) |
| BEV | 172 | **98** (57%) |

So most cancellations are not lost work — the draft was scrapped and the invoice entered
properly. **But the same test on the live queue is a warning:** 19 of Oil's 36 unmanaged
open drafts (`WddStatus = '-'`) and 6 of the 95 waiting ones duplicate a bill that is
already posted. Anyone about to press **Add** on those would be entering the bill twice.

---

## 7. How a document actually gets closed

There is no single answer — each family closes for a different reason, and two of them never
close at all.

| Family | `DocStatus` goes `C` when… | Measured |
|---|---|---|
| A/P + A/R invoice, credit memo | **`PaidToDate` equals `DocTotal`.** Exactly | Oil: all 11,799 closed live A/P invoices have `PaidToDate = DocTotal`; all 4,309 open ones are short. Same in Mart (1,870/2,912) and Bev (2,602 + one ₹0 invoice / 551). **No exceptions in any book** |
| [[GRPO]], [[Purchase-Order]], [[Sales-Order]] | Its lines are fully **drawn into the next document** | Oil: 10,213 of 10,333 closed live GRPOs are referenced by a `PCH1` line (98.8%). 120 closed without ever being invoiced; 25 of the 370 open ones are *partly* invoiced |
| [[Stock-Transfer]], [[Goods-Receipt]], [[Goods-Issue]] | **Never.** `O` is the permanent state | Oil: `OIGN` is `O` on 100% of 8,548 rows; `OWTR` is `O` on 12,170 of 12,204 and the 34 `C` rows are exactly the 34 cancelled ones |
| [[Document-Drafts]] | The draft **became a document** | Oil 45,457 of 49,463 |
| Payments | n/a — no `DocStatus` column exists | |

**So on a stock transfer or a goods receipt, `DocStatus = 'C'` means cancelled, not
finished.** That is the reverse of an invoice, in the same one-letter column, in the same
database.

### What settles an A/P invoice — the reconciliation record

`PaidToDate` is not typed by anyone; it is moved by whatever settled the document, and
`ITR1`/`OITR` names that thing. Oil A/P invoices, by the object that initiated the
reconciliation:

| `OITR.InitObjTyp` | What it is | Invoices touched |
|---:|---|---:|
| 46 | [[Outgoing-Payment]] | 7,333 |
| *NULL* | system reconciliation with no named initiator | 4,875 |
| 18 | the A/P invoice itself — the GRNI clearing at posting time | 4,776 |
| 19 | [[AP-Credit-Memo]] | 873 |
| 24 | [[Incoming-Payment]] (vendor refund) | 111 |
| **30** | **manual [[Journal-Entry]]** | **0** |

That last row is the whole of **C-0019** in one number. **A manual journal entry never
reconciles against an invoice in Oil** — not once — even though 5,885 manual-JE lines touch
928 different vendor accounts (₹105.14 Cr debit, ₹2,857.47 Cr credit; the credit side
includes intercompany and accrual postings, so do not read it as unreconciled spend —
see C-0005 / C-0020). The vendor's balance moves; the invoice is never told; it stays open
for ever.

### C-0019, measured in all three books

| Book | open A/P documents | still-open value | vendors' real balance (`OCRD`) | overstatement |
|---|---:|---:|---:|---:|
| OIL | 4,309 | ₹303.07 Cr | ₹90.17 Cr | **3.4×** |
| MART | 2,912 | ₹223.50 Cr | ₹32.68 Cr | **6.8×** |
| BEV | 551 | ₹3.54 Cr | ₹0.49 Cr | **7.2×** |

| Book | open A/R documents | still-open value | customers' real balance | overstatement |
|---|---:|---:|---:|---:|
| OIL | 13,056 | ₹185.42 Cr | ₹107.79 Cr | **1.7×** |
| MART | 4,373 | ₹134.10 Cr | ₹21.38 Cr | **6.3×** |
| BEV | 1,167 | ₹6.35 Cr | ₹4.49 Cr | **1.4×** |

That is C-0019's "1.3× to 7.5×" reproduced from scratch, and it holds on both sides of the
ledger. The sharpest single version of it:

> **In Oil, 238 A/P invoices worth ₹45.55 Cr are still marked "open" against 126 vendors
> whose ledger balance is exactly zero.** They owe nothing. Mart: 70 documents / ₹0.16 Cr /
> 14 vendors. Beverages: 46 documents / ₹0.20 Cr / 38 vendors. On the sales side, Oil has
> 4,046 open A/R invoices worth ₹21.43 Cr against 231 customers whose balance is zero.

### And the mechanism behind it: 40% of vendor payments are never applied

| Book | live vendor payments | not applied to **any** invoice | value |
|---|---:|---:|---:|
| OIL | 9,063 | **3,665 (40%)** | ₹3,452.13 Cr |
| MART | 1,451 | **571 (39%)** | ₹191.05 Cr |
| BEV | 1,482 | **493 (33%)** | ₹7.85 Cr |

A payment with no `VPM2` rows moved the money and moved the vendor's balance, and touched no
invoice's `PaidToDate`. (Value includes intercompany settlements and advances — C-0005,
C-0020 — so quote the *count*, not the crore figure, without checking the parties first.)

**Rule: age from `OCRD.Balance` and the [[Business-Partner-Master]], never from open
documents. (C-0019)**

---

## 8. Cross-book differences that will bite

| | OIL | MART | BEV |
|---|---|---|---|
| A/P invoices open by count | 26% | **60%** | 17% |
| A/R invoices open by count | 42% | 17% | 21% |
| Vendor-payment approval (`OVPM.WddStatus='P'`) | 1,311 | **0 — no approval workflow at all** | 166 |
| Payment drafts cancelled | 88% | 10% | 85% |
| Sales orders cancelled | 0.47% | **6.28%** | 0.57% |
| Live A/P draft queue | 209 | 33 | 43 |
| A/P drafts pending approval (`W`) | 95 | 10 | 35 |
| Approved but not yet added (`Y`) | 78 | **0** | 4 |
| `OQUT` [[Sales-Quotation]] | 1,692 rows | **table empty** | 733 rows |
| `OIPF` [[Landed-Costs]] | 534 rows | **table empty** | 6 rows |

Mart is not a smaller Oil. It has no outgoing-payment approval, no approved-and-waiting
drafts, 60% of its A/P invoices sitting open, and it cancels sales orders 13× more often.
A figure measured in Oil and quoted for Mart will be wrong on every line above.

---

## 9. The two questions an operator actually has

### "Is this bill already in SAP?"

Three places to look, and you need all three. **Search on the vendor's own bill number
(`NumAtCard`), never on ours.**

```sql
-- 1. posted A/P invoices, INCLUDING cancelled ones
SELECT "DocEntry","DocNum","DocDate","TaxDate","DocTotal","PaidToDate",
       "DocStatus","CANCELED","BPLName","JrnlMemo"
FROM "JIVO_OIL_HANADB"."OPCH"
WHERE "CardCode" = 'VENDA000515'
  AND "NumAtCard" LIKE '%458/26-27%';

-- 2. drafts that are still alive (W = waiting, Y = approved, '-' = no workflow)
SELECT "DocEntry","DocNum","DocDate","DocTotal","WddStatus","NumAtCard"
FROM "JIVO_OIL_HANADB"."ODRF"
WHERE "ObjType" = 18 AND "DocStatus" = 'O'
  AND "WddStatus" IN ('W','Y','-')
  AND "CardCode" = 'VENDA000515'
  AND "NumAtCard" LIKE '%458/26-27%';

-- 3. the GRPO it should be built on
SELECT "DocEntry","DocNum","DocDate","DocTotal","DocStatus","CANCELED","NumAtCard"
FROM "JIVO_OIL_HANADB"."OPDN"
WHERE "CardCode" = 'VENDA000515' AND "CANCELED" = 'N'
  AND "NumAtCard" LIKE '%458/26-27%';
```

How to read what comes back:

| You find | It means |
|---|---|
| `CANCELED='N'`, any `DocStatus` | **It is in. Stop.** Do not key it again |
| `CANCELED='Y'` and a `C` twin | It was entered and cancelled. Keying it again may be right — ask why it was cancelled first |
| A draft with `WddStatus` `W`/`Y`/`-` | It is waiting in [[Document-Drafts]]. Add that one, do not make a second |
| A draft with `WddStatus` `C` or `N` | Dead. Safe to key afresh — and 62% of Oil's dead drafts already were |
| Nothing at all | Genuinely new. Now check the right **company** — vendor `CardCode`s differ between books for the same GSTIN — and see [[AP-Invoice]] |

Two things that make this search fail:

- **`NumAtCard` is empty on 62 Oil, 11 Mart and 15 Bev A/P invoices.** Those bills cannot be
  found this way at all; fall back to `CardCode` + `DocTotal` + month.
- **A repeat bill number is not blocked.** Oil has **59 (`CardCode`, `NumAtCard`) pairs on
  more than one live A/P invoice — 118 documents**, of which 16 pairs carry the identical
  `DocTotal` and are almost certainly the same bill entered twice. Mart has 1 pair,
  Beverages 6. So a hit is proof it is in; it is not proof it is in *once*.

### "Is it already paid?"

Not `DocStatus`. In order:

```sql
-- a. the document's own money columns — this IS what DocStatus reports
SELECT "DocEntry","DocNum","DocTotal","PaidToDate",
       "DocTotal"-"PaidToDate" AS STILL_OWED, "DocStatus","CANCELED"
FROM "JIVO_OIL_HANADB"."OPCH" WHERE "DocEntry" = 49775;

-- b. which payment paid it.  TRAP: VPM2's keys read backwards —
--    VPM2."DocNum" is the PAYMENT's DocEntry, VPM2."DocEntry" is the INVOICE's
SELECT v."SumApplied", p."DocEntry" AS PAY_ENTRY, p."DocNum", p."DocDate",
       p."DocTotal", p."Canceled"
FROM "JIVO_OIL_HANADB"."VPM2" v
JOIN "JIVO_OIL_HANADB"."OVPM" p ON p."DocEntry" = v."DocNum"
WHERE v."DocEntry" = 49775 AND v."InvType" = '18';

-- c. everything that settled it, and what initiated each settlement
SELECT r."ReconNum", r."ReconDate", r."ReconType", r."IsSystem", r."Canceled",
       r."InitObjTyp", r."InitObjAbs", l."ReconSum", l."IsCredit", l."Account"
FROM "JIVO_OIL_HANADB"."ITR1" l
JOIN "JIVO_OIL_HANADB"."OITR" r ON r."ReconNum" = l."ReconNum"
WHERE l."SrcObjTyp" = '18' AND l."SrcObjAbs" = 49775 AND r."Canceled" = 'N';

-- d. the answer that is always true: does the vendor owe anything?  (C-0019)
SELECT "CardCode","CardName","Balance"    -- negative = JIVO owes them
FROM "JIVO_OIL_HANADB"."OCRD" WHERE "CardCode" = 'VENDA000515';
```

Worked example, Oil A/P invoice `DocEntry` 49775 (₹2,27,062):

| Step | What came back |
|---|---|
| a | `DocTotal` 227,062 = `PaidToDate` 227,062 → `DocStatus` `C` |
| b | Payment `DocEntry` 27657 (`DocNum` 826466849, 22 Aug 2026, ₹7,81,481 total), applied ₹2,27,062 to this invoice — one payment covering several bills |
| c | Two reconciliations: `ReconNum` 48391 (`ReconType` 13, initiated by the invoice itself) clearing ₹1,92,588.90 out of GRNI account 2140001; `ReconNum` 48491 (`ReconType` 3, initiated by outgoing payment 27657) crediting ₹2,27,062 on vendor control 2110005 |
| d | Vendor's `Balance` — the only figure that survives a manual JE |

**If (a) says short but (d) says zero, the bill was settled outside the document.** That is
the 238-invoice / ₹45.55 Cr population in Oil, and it is normal here, not a data fault.

### Checking your own entry afterwards

After a draft is added, read it back — SAP does not fill in what you sent (`WTAmount` is the
known one, C-0018). Then:

```sql
-- did my draft become a document?
SELECT d."DocEntry", d."DocStatus", d."WddStatus", p."DocEntry" AS POSTED, p."DocNum"
FROM "JIVO_OIL_HANADB"."ODRF" d
LEFT JOIN "JIVO_OIL_HANADB"."OPCH" p ON p."draftKey" = d."DocEntry"
WHERE d."DocEntry" = <your draft>;
```

`DocStatus='O'` + `WddStatus='W'` = waiting for an approver. `DocStatus='C'` + a row in
`POSTED` = it is in the books. `WddStatus='C'` = somebody killed it. `draftKey` is set on
94.5% of posted Oil A/P invoices, so a `NULL` there is not proof of anything.

---

## 10. Traps

1. **`DocStatus='C'` on an invoice means "paid in full", not "settled".** Half of what is
   really settled still says `O`. **(C-0019)**
2. **`DocStatus='C'` also means cancelled.** In Oil `OPCH`, 226 of the 12,025 `C` rows are a
   cancelled original or its mirror. Always pair `DocStatus` with `CANCELED='N'`.
3. **`DocStatus='C'` on a stock transfer or goods receipt means cancelled and nothing else.**
   A finished transfer stays `O` for ever.
4. **`CANCELED <> 'Y'` keeps the mirrors and double-counts.** Use `= 'N'`. **(C-0021)**
5. **The mirror is positive, not negative.** Same amount, same sign, opposite journal — so a
   naive `SUM(DocTotal)` inflates rather than nets.
6. **The mirror has its own `DocNum` and often its own `Series`.** It does not share the
   original's number, so you cannot pair them on `DocNum`.
7. **`CancelDate` is `NULL` on every row.** Use the mirror's `CreateDate` for when.
8. **Payments have no mirror row — the reversal is a journal entry.** `OJDT` counts exceed
   `ORCT`/`OVPM` counts by exactly the number of cancellations.
9. **A journal entry cannot be cancelled at all.** Only reversed, by a second JE with
   `StornoToTr`.
10. **`ODRF.CANCELED` is always `N`; `OPDF.Canceled` is `Y` 88% of the time.** Two draft
    tables, opposite conventions.
11. **`WddStatus='C'` does not mean rejected.** Approved, pending and rejected requests all
    end up there. It means "closed without producing a document".
12. **A posted document's `WddStatus='P'`; the draft it came from resets to `'-'`.** Do not
    look for the approval history on the draft after it posts — it is in `OWDD`.
13. **`InvntSttus` disagrees with `DocStatus` on 7,892 of 16,108 live Oil A/P invoices
    (49%).** Do not use it for anything.
14. **`Transfered` and `ORCT`/`OVPM`/`OPDF`.`Status` are dead columns.**
15. **`VPM2`'s keys read backwards** — `DocNum` holds the payment's `DocEntry` and `DocEntry`
    holds the invoice's. Verified live on invoice 49775 / payment 27657.
16. **A repeat vendor bill number is not blocked.** 118 live Oil A/P invoices sit on 59
    duplicated (`CardCode`, `NumAtCard`) pairs.
17. **A production order's letters are a different alphabet** — `L` is the good ending, `C`
    is the bad one.
18. **Mart has no outgoing-payment approval workflow.** `OVPM.WddStatus` is `-` on all 2,294
    rows, so "waiting for approval" cannot be a reason a Mart payment has not gone out.
19. **`OJDT.TransType` 321 is the internal-reconciliation journal**, not an unknown type —
    all 24 Oil rows match an `OITR.ReconJEId`. Correction to the open item in
    [[Entry-Types-Census]] → [[Unidentified-Posting-Types]].

---

## Which documents this touches

Every one. Specifically: [[AP-Invoice]] · [[AP-Credit-Memo]] · [[GRPO]] ·
[[Document-Drafts]] · [[Payment-Draft]] · [[AR-Invoice]] · [[AR-Credit-Memo]] ·
[[AR-Return]] · [[Delivery]] · [[Sales-Order]] · [[Purchase-Order]] · [[Stock-Transfer]] ·
[[Goods-Receipt]] · [[Goods-Issue]] · [[Goods-Return]] · [[Incoming-Payment]] ·
[[Outgoing-Payment]] · [[Journal-Entry]] · [[Internal-Reconciliation]] ·
[[Production-Order]] · [[Approval-Workflow]].

Foundations it depends on: [[Business-Partner-Master]] (`Balance` is the real ageing
source) · [[Numbering-Series]] (the mirror takes its own number) ·
[[Chart-of-Accounts]] (2140001 GRNI, the 2110xxx/2120xxx vendor control accounts) ·
[[Field-Name-Rosetta]] (the API spells all of this differently).

---

## Open questions

1. **What is `WddStatus`/`ProcesStat` = `A`?** 377 Oil requests, 9 Mart, 28 Bev. Terminal and
   generated like `P`, never mixed with `P` on one document, never on a payment draft. Ruled
   out: approval template, workflow step, approving user, the user who added the document,
   whether the document was updated after creation, and whether the draft row still exists.
   Someone with the SAP B1 client open on one of those stock transfers (Oil `OWTR` where
   `WddStatus='A'`) could probably see it in one look.
2. **What does `InvntSttus` mean on an invoice?** It is independent of `DocStatus` and does
   not follow `PCH1."LineStatus"` or `TargetType`. Until somebody explains it, treat it as
   noise — but it is not random, so there is an answer.
3. **Do the other 17 cancelled Mart stock transfers have silent cancellation partners?**
   Only `DocEntry` 2877 identifies itself, via its `Comments`. If the others do too, every
   "cancelled transfers" count in the group is roughly double.
4. **The 4,875 Oil A/P reconciliations with a `NULL` `InitObjTyp`** — 16% of A/P
   reconciliations have no named initiator. What creates them?
5. **The 120 Oil GRPOs closed without ever being invoiced.** Manually closed, or drawn into
   a [[Goods-Return]]? A closed GRPO with no A/P invoice is a receipt whose cost may never
   have been billed.
6. **`ORCT.WddStatus` is `-` on all 29,706 incoming payments in all three books** — is
   incoming-payment approval switched off deliberately, or never configured?
7. **Are the 16 identical-amount duplicate (`CardCode`, `NumAtCard`) pairs in Oil real
   double payments?** ₹-value not checked. This is a one-query audit that could find real
   money.
8. **The `-3` opening-balance postings** carry no cancellation concept at all. Whether a
   cutover figure was ever corrected, and how, is unmapped →
   [[Opening-Balance-and-Cutover]].

---

## Queries used

Every figure above comes from one of these, run 2026-08-24 against live HANA through
`./hana-sql/hana-sql -env connections/hana-office-bridge.env`. Swap
`JIVO_OIL_HANADB` for `JIVO_MART_HANADB` / `JIVO_BEVERAGES_HANADB`.

```sql
-- §2  the full value distribution (one column, three books; repeat per column/table)
SELECT 'OIL' CO, COALESCE("DocStatus",'~NULL~') V, COUNT(*) N
  FROM "JIVO_OIL_HANADB"."OPCH" GROUP BY "DocStatus"
UNION ALL SELECT 'MART', COALESCE("DocStatus",'~NULL~'), COUNT(*)
  FROM "JIVO_MART_HANADB"."OPCH" GROUP BY "DocStatus"
UNION ALL SELECT 'BEV', COALESCE("DocStatus",'~NULL~'), COUNT(*)
  FROM "JIVO_BEVERAGES_HANADB"."OPCH" GROUP BY "DocStatus";

-- §2  which status columns each table even has
SELECT TABLE_NAME, COLUMN_NAME FROM SYS.TABLE_COLUMNS
WHERE SCHEMA_NAME='JIVO_OIL_HANADB'
  AND COLUMN_NAME IN ('DocStatus','CANCELED','Canceled','InvntSttus','Transfered','WddStatus','Status');

-- §3  the cancellation pair, side by side
SELECT "DocEntry","DocNum","CANCELED","DocStatus","DocDate","CancelDate","DocTotal",
       "CardCode","NumAtCard","TransId","UserSign","Series","draftKey","JrnlMemo"
FROM "JIVO_OIL_HANADB"."OPCH"
WHERE "CANCELED" IN ('Y','C') AND "DocEntry" > 44000 ORDER BY "DocEntry";
-- 44118 (Y, series 3668) and 44125 (C, series 3716): same vendor, same 751.00

-- §3  the two journals — an exact side-flip
SELECT j."TransId", j."TransType", j."StornoToTr", d."Account", d."Debit", d."Credit", d."LineMemo"
FROM "JIVO_OIL_HANADB"."OJDT" j
JOIN "JIVO_OIL_HANADB"."JDT1" d ON d."TransId"=j."TransId"
WHERE j."TransId" IN (203804,203819) ORDER BY j."TransId", d."Line_ID";

-- §3  JrnlMemo detects a mirror exactly (113/113 Oil, 41/41 Mart, 8/8 Bev)
SELECT COUNT(*) TOT,
       SUM(CASE WHEN "CancelDate" IS NOT NULL THEN 1 ELSE 0 END) CANCELDATE_SET,
       SUM(CASE WHEN "JrnlMemo" LIKE '%Cancellation%' THEN 1 ELSE 0 END) MEMO_CANC,
       SUM(CASE WHEN "CANCELED"='C' THEN 1 ELSE 0 END) MIRRORS
FROM "JIVO_OIL_HANADB"."OPCH";

-- §3  does the mirror land in the original's month?  110 same / 2 different of 112 pairs
SELECT COUNT(*) PAIRS,
  SUM(CASE WHEN TO_VARCHAR(o."DocDate",'YYYY-MM')=TO_VARCHAR(c."DocDate",'YYYY-MM') THEN 1 ELSE 0 END) SAME_MONTH
FROM "JIVO_OIL_HANADB"."OPCH" o
JOIN "JIVO_OIL_HANADB"."OPCH" c
  ON c."CardCode"=o."CardCode" AND c."DocTotal"=o."DocTotal"
 AND COALESCE(c."NumAtCard",'~')=COALESCE(o."NumAtCard",'~') AND c."CANCELED"='C'
WHERE o."CANCELED"='Y';

-- §4  cancelled x closed, jointly (run per table, per book)
SELECT "CANCELED","DocStatus",COUNT(*) N FROM "JIVO_OIL_HANADB"."OPCH"
GROUP BY "CANCELED","DocStatus" ORDER BY N DESC;

-- §4  the Mart stock transfer that flags itself
SELECT "DocEntry","DocNum","DocDate","DocStatus","InvntSttus","WddStatus","Comments"
FROM "JIVO_MART_HANADB"."OWTR" WHERE "CANCELED"='Y' ORDER BY "DocNum";
-- 2877: "Inventory transfer no. 626674525 has been canceled", DocStatus 'O'

-- §5  payments: JE count = payment rows + cancellations, exactly, in all three books
SELECT (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OVPM") VPM_ROWS,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OVPM" WHERE "Canceled"='Y') VPM_CANCELLED,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OJDT" WHERE "TransType"=46) JE_46,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."ORCT") RCT_ROWS,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."ORCT" WHERE "Canceled"='Y') RCT_CANCELLED,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OJDT" WHERE "TransType"=24) JE_24
FROM DUMMY;

-- §5  journal reversals: which posting types get reversed, and how often
SELECT "TransType", COUNT(*) N, MIN("RefDate"), MAX("RefDate")
FROM "JIVO_OIL_HANADB"."OJDT" WHERE "StornoToTr" IS NOT NULL AND "StornoToTr"<>0
GROUP BY "TransType" ORDER BY N DESC;   -- 46x939, 24x496, 30x43; AutoStorno never used

-- §6  WddStatus IS OWDD.ProcesStat — 1:1, no exceptions, all three books
SELECT w."ProcesStat", w."Status", d."WddStatus", d."DocStatus", COUNT(*) N
FROM "JIVO_OIL_HANADB"."OWDD" w
JOIN "JIVO_OIL_HANADB"."ODRF" d ON d."DocEntry"=w."DraftEntry"
WHERE w."ObjType"='18' AND d."ObjType"=18
GROUP BY w."ProcesStat", w."Status", d."WddStatus", d."DocStatus" ORDER BY N DESC;

-- §6  the two OWDD status columns, and IsDraft flipping on P/A
SELECT "Status","ProcesStat","IsDraft",COUNT(*) N FROM "JIVO_OIL_HANADB"."OWDD"
GROUP BY "Status","ProcesStat","IsDraft" ORDER BY N DESC;

-- §6  'A' never shares a document with 'P'
SELECT n.REQS, n.STATS, COUNT(*) DOCS FROM (
  SELECT w."DocEntry", COUNT(*) REQS,
         STRING_AGG(w."ProcesStat",'/' ORDER BY w."WddCode") STATS
  FROM "JIVO_OIL_HANADB"."OWDD" w
  WHERE w."ObjType"='67' AND w."IsDraft"='N' GROUP BY w."DocEntry") n
GROUP BY n.REQS, n.STATS ORDER BY DOCS DESC;

-- §6  the live draft queue, per book
SELECT "DocStatus","WddStatus",COUNT(*) N FROM "JIVO_OIL_HANADB"."ODRF"
WHERE "ObjType"=18 GROUP BY "DocStatus","WddStatus" ORDER BY N DESC;

-- §6  cancelled drafts whose bill is already posted (COUNT DISTINCT — the join multiplies)
SELECT d."WddStatus", COUNT(DISTINCT d."DocEntry") DRAFTS,
       COUNT(DISTINCT CASE WHEN p."DocEntry" IS NOT NULL THEN d."DocEntry" END) ALSO_POSTED
FROM "JIVO_OIL_HANADB"."ODRF" d
LEFT JOIN "JIVO_OIL_HANADB"."OPCH" p
  ON p."CardCode"=d."CardCode" AND p."NumAtCard"=d."NumAtCard" AND p."CANCELED"='N'
WHERE d."ObjType"=18 AND d."DocStatus"='O' GROUP BY d."WddStatus";

-- §7  DocStatus 'C' is exactly 'PaidToDate = DocTotal' — no exceptions in any book
SELECT "DocStatus",
  CASE WHEN "PaidToDate"=0 THEN 'paid 0'
       WHEN ABS("PaidToDate"-"DocTotal")<0.01 THEN 'paid = total'
       WHEN "PaidToDate">0 AND "PaidToDate"<"DocTotal" THEN 'part paid'
       ELSE 'paid > total' END BUCKET,
  COUNT(*) N, TO_DECIMAL(SUM("DocTotal")/10000000,12,2) CR
FROM "JIVO_OIL_HANADB"."OPCH" WHERE "CANCELED"='N'
GROUP BY "DocStatus", CASE WHEN "PaidToDate"=0 THEN 'paid 0'
       WHEN ABS("PaidToDate"-"DocTotal")<0.01 THEN 'paid = total'
       WHEN "PaidToDate">0 AND "PaidToDate"<"DocTotal" THEN 'part paid'
       ELSE 'paid > total' END;

-- §7  a GRPO closes when it is invoiced (10,213 of 10,333)
SELECT g."DocStatus", COUNT(DISTINCT g."DocEntry") GRPOS,
       COUNT(DISTINCT CASE WHEN l."BaseEntry" IS NOT NULL THEN g."DocEntry" END) DRAWN_INTO_AP
FROM "JIVO_OIL_HANADB"."OPDN" g
LEFT JOIN "JIVO_OIL_HANADB"."PCH1" l ON l."BaseType"=20 AND l."BaseEntry"=g."DocEntry"
WHERE g."CANCELED"='N' GROUP BY g."DocStatus";

-- §7  what settles an A/P invoice — and that a manual JE never does (InitObjTyp 30 = 0)
SELECT r."InitObjTyp", COUNT(DISTINCT l."SrcObjAbs") INVOICES
FROM "JIVO_OIL_HANADB"."ITR1" l
JOIN "JIVO_OIL_HANADB"."OITR" r ON r."ReconNum"=l."ReconNum"
JOIN "JIVO_OIL_HANADB"."OPCH" p ON p."DocEntry"=l."SrcObjAbs"
WHERE l."SrcObjTyp"='18' AND r."Canceled"='N'
GROUP BY r."InitObjTyp" ORDER BY INVOICES DESC;

-- §7  C-0019: open documents vs the party balances that are actually true
SELECT 'AP open docs' K, COUNT(*) N,
       TO_DECIMAL(SUM("DocTotal"-"PaidToDate")/10000000,14,2) CR
  FROM "JIVO_OIL_HANADB"."OPCH" WHERE "CANCELED"='N' AND "DocStatus"='O'
UNION ALL SELECT 'AR open docs', COUNT(*),
       TO_DECIMAL(SUM("DocTotal"-"PaidToDate")/10000000,14,2)
  FROM "JIVO_OIL_HANADB"."OINV" WHERE "CANCELED"='N' AND "DocStatus"='O'
UNION ALL SELECT 'vendor balances', COUNT(*), TO_DECIMAL(SUM("Balance")/10000000,14,2)
  FROM "JIVO_OIL_HANADB"."OCRD" WHERE "CardType"='S' AND "Balance"<>0
UNION ALL SELECT 'customer balances', COUNT(*), TO_DECIMAL(SUM("Balance")/10000000,14,2)
  FROM "JIVO_OIL_HANADB"."OCRD" WHERE "CardType"='C' AND "Balance"<>0;

-- §7  "open" invoices against parties who owe nothing:  Oil 238 docs / Rs 45.55 Cr / 126 vendors
SELECT COUNT(DISTINCT p."CardCode") VENDORS, COUNT(*) OPEN_DOCS,
       TO_DECIMAL(SUM(p."DocTotal"-p."PaidToDate")/10000000,14,2) CR_STILL_SHOWN_OPEN
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."CardCode"=p."CardCode"
WHERE p."CANCELED"='N' AND p."DocStatus"='O' AND c."Balance"=0;

-- §7  40% of vendor payments are applied to no invoice at all
SELECT COUNT(*) VENDOR_PAYMENTS,
       SUM(CASE WHEN v."PAYENT" IS NULL THEN 1 ELSE 0 END) NOT_APPLIED,
       TO_DECIMAL(SUM(CASE WHEN v."PAYENT" IS NULL THEN p."DocTotal" ELSE 0 END)/10000000,14,2) CR
FROM "JIVO_OIL_HANADB"."OVPM" p
LEFT JOIN (SELECT DISTINCT "DocNum" AS "PAYENT" FROM "JIVO_OIL_HANADB"."VPM2") v
       ON v."PAYENT"=p."DocEntry"
WHERE p."Canceled"='N' AND p."DocType"='S';

-- §9  duplicate vendor bill numbers on live A/P invoices: 59 pairs, 16 same amount
SELECT COUNT(*) GRPS, SUM(SAME_AMT) SAME_TOTAL FROM (
  SELECT "CardCode","NumAtCard", COUNT(*) N,
         CASE WHEN COUNT(DISTINCT "DocTotal")=1 THEN 1 ELSE 0 END SAME_AMT
  FROM "JIVO_OIL_HANADB"."OPCH"
  WHERE "CANCELED"='N' AND "NumAtCard" IS NOT NULL AND "NumAtCard"<>''
  GROUP BY "CardCode","NumAtCard" HAVING COUNT(*)>1);

-- §10 TransType 321 is the internal-reconciliation journal, not an unknown
SELECT COUNT(*) JE321, SUM(CASE WHEN r."ReconNum" IS NOT NULL THEN 1 ELSE 0 END) MATCHED
FROM "JIVO_OIL_HANADB"."OJDT" j
LEFT JOIN "JIVO_OIL_HANADB"."OITR" r ON r."ReconJEId"=j."TransId"
WHERE j."TransType"=321;   -- 24 / 24
```

Field profiles behind the fill-rate claims: `_data/profile-OPCH.md`, `profile-OINV.md`,
`profile-OPDN.md`, `profile-ODRF.md`, `profile-OWDD.md`, `profile-OITR.md`,
`profile-ITR1.md`, `profile-VPM2.md`, `profile-OVPM.md`, `profile-ORCT.md`,
`profile-OPDF.md`, `profile-OWOR.md`.
