# saphist — JIVO's OLD SAP B1 books (2014 → Oct-2024). Read this before answering.

You are in the CLI for JIVO's **closed** SAP Business One company databases, on
the Microsoft SQL Server `138.252.101.118:1433`. This is history: ten years of
books that the live `sapb1` CLI cannot reach.

## The rule that matters most

**Anything dated after October 2024 is NOT in this tool.** That is the live SAP
HANA system — answer it with `sapb1` from `sap-b1/`, and say so plainly instead
of returning an empty result and letting the operator think there were no sales.

## Three books, and you should not make the operator pick

| `--book` | Database | Company | Documents | Journals to |
|---|---|---|---|---|
| `old` | `Live_Jivo_WellnessN_Aug_2019` | Jivo Wellness Pvt. Ltd. **(Old)** | 2014-11-01 → 2019-08-31 | 2019-10-29 |
| `new` | `Jivo_All_Branches_Live` | Jivo Wellness Pvt. Ltd. | 2019-08-31 → 2024-10-01 | 2025-03-31 |
| `bsu` | `ARY_BSU` | Akal Rozgar Yojana (BSU) | 2019-04-01 → 2023-03-14 | 2025-03-31 |

Every dated command routes itself on `--from/--to` (or `--fy` / `--year`) and
reads **both** Jivo Wellness books when the range crosses August 2019, labelling
each row with its `book`. Don't pin `--book` unless the operator asked for one
book, or you are looking at BSU (which is deliberately outside the routing —
it is a separate company and its figures must never be added to Jivo Wellness's).

## Writes are impossible here, and that is a fact about the code

There is no write command in this CLI. Every statement passes a SELECT-only
guard and runs inside a transaction that is always rolled back. Say that plainly
if asked — it is not caution, and it is not a policy you are applying.

The login is `sa`, a sysadmin on that instance. The guard is what protects the
books, not the login. Never print the password.

## Traps that produce confidently wrong numbers

1. **A CardCode is NOT the same party in both books.** `CUSTA000694` is
   *Bala Ji Store (Janak Puri)* in `old` and *JIVO MART PVT. LTD.* in `new` — the
   two databases were numbered independently. Always read the `book` column back
   to the operator, and never carry a code across books. When you name a party,
   name the book.
2. **`old` has no branches.** `OBPL` is empty there. `--branch` and
   `sales by-branch` mean nothing before Aug-2019; say so rather than reporting
   a single unnamed bucket.
3. **`items stock` is frozen, not as-at-date.** `OITW.OnHand` is the balance at
   the moment the book stopped being posted to. For a period, use
   `items movement`.
4. **Journals run past the last document.** `new` has journal entries to
   2025-03-31 (the FY24-25 close) while its last invoice is 2024-10-01. A FY2024
   trial balance is real; a 2025 *sales* figure from here is not.
5. **`zTest_Jivo` is a test copy** with near-identical counts. It is listed in
   `saphist books` so it is never quoted by accident. Never use `--db zTest_Jivo`
   for an answer.
6. **Two-book results are two answers, not one.** A `-n 20` across both books is
   the top 20 *of each*. If the operator wants a single combined figure, add the
   two `turnover` rows yourself and say you did.

## Definitions — the same ones the live system uses

- **Turnover** = `OINV(DocTotal − VatSum)` − `ORIN(DocTotal − VatSum)`, by
  `DocDate`, excluding cancelled. GST-inclusive = `DocTotal`.
- **Ledger balance** = `OCRD.Balance`. **Positive = DEBIT** (they owe JIVO),
  **negative = CREDIT** (JIVO owes them).
- **Quantities are pieces**, not cartons — a "20 PCS" in an item name is carton
  configuration (correction C-0001).
- Cancel flag: `CANCELED` on documents, `Canceled` on payments (collation is
  case-insensitive, so either resolves).
- Money is INR. Present with Indian grouping and crores for big numbers.

## How to answer

Lead with the number, then one line on how you got it, then offer the drill-down.
Always state the date range and **which book(s)** the figure came from. Never
state a financial figure without the command that produced it.

Name search is a real server-side `LIKE` here — unlike the live Service Layer,
where `toupper()`/`tolower()` are unsupported. `saphist party search jindal`
just works.

## Commands

`doctor` · `books` (+ `books which`) · `sales` · `purchases` · `party` ·
`ledger` · `items` · `payments` · `orders` · `branches` · `warehouses` ·
`salespeople` · `item-groups` · `query` · `tables` · `columns`

Details and worked questions: `README.md`, `ASK-EXAMPLES.md`. Install: `SETUP.md`.
