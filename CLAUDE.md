# JIVO CLI — read this first

You are running inside **JIVO's read-only data toolkit**. Someone (often the Accounts team) has opened a terminal here and wants answers about the business — SAP balances, turnover, ledgers, orders, stock. Your job: **answer their questions in plain language, with real numbers, pulled live.**

## ⛔ RULE 0 — READ-ONLY, ALWAYS

Every tool here only **reads** JIVO's live production systems. You must **NEVER** create, update, delete, upload, post, approve, or change anything — in SAP or any other system. The only write any tool performs is Login. There is no valid reason to run a write. If a user asks you to change data, say it's read-only and stop.

## What's here

A folder of command-line tools ("CLIs"), each a window into one JIVO system. All read-only.

| Folder | System | What you can answer |
|---|---|---|
| `sap-b1/` | **SAP B1** (the books, 3 companies) | ledger balances, turnover/sales, invoices, orders, stock, party statements |
| `ecom-cli/` `exim/` `factory-cli/` `oms-cli/` `jsap-cli/` | ecom / imports / factory / orders / ops | channel sales, POs, production, approvals (Go/Python CLIs) |
| `postsql/` | raw Postgres (16 DBs) | direct SQL reads under the apps |
| `portals/` | Blinkit/Zepto seller portals + **TankhaPay** HR/payroll | studied; read-only CLIs built (tankhapay: 297 cmds — employees/attendance/salary/payouts/leave/reports) |

**SAP is the main one for Accounts.** Start there unless asked otherwise.

## How to answer SAP questions

The SAP tool is **`sapb1`**. On **Windows** use `sap-b1\accounts-kit\sapb1.exe` (creds are in a `.env` next to it). On Mac/Linux use `sap-b1/cli/sapb1`. Always run `doctor` first if unsure it's connected.

**Three companies** (pass `--company`, default is Oil):
`JIVO_OIL_HANADB` (Oil) · `JIVO_MART_HANADB` (Mart) · `JIVO_BEVERAGES_HANADB` (Beverages)

**Core commands:**
```
sapb1 doctor                         # is SAP connected?
sapb1 query <Entity> --filter "…" --select "…" --top N [--company DB] [--json]
sapb1 query <Entity> --count --filter "…"        # just the number
sapb1 query <Entity> --all --json                # every matching row (paginated)
```

**Key entities:** `BusinessPartners` (customers/vendors + balances), `Invoices` (A/R sales), `CreditNotes` (sales returns), `Orders` (sales orders), `PurchaseInvoices`/`PurchaseOrders`, `IncomingPayments`/`VendorPayments`, `Items` (stock).

### Definitions that matter (use these, they're correct)
- **Ledger balance** = `BusinessPartners.CurrentAccountBalance`. **Positive = DEBIT** (the party owes JIVO / advance held). **Negative = CREDIT** (JIVO owes them).
- **Turnover / sales** = `Invoices` **net of GST** (`DocTotal − VatSum`) **minus** `CreditNotes` (returns), by `DocDate`, excluding cancelled (`Cancelled eq 'tNO'`). GST-inclusive = `DocTotal`.
- A party can have several accounts (e.g. an employee "IMPREST" vendor account + a customer account) — check all and say which is which.

### Gotchas
- Date filters: `DocDate ge '2026-04-01' and DocDate lt '2026-07-25'` (quoted).
- `toupper()`/`tolower()` are **not supported** — to name-search a partner, fetch `BusinessPartners` with `--all --json` and match in code (case-insensitive) rather than filtering by name.
- For sums/turnover there's no server-side SUM — fetch the rows (`--all --json`, add `--page-size 200` for speed) and total them yourself.
- Money is INR. Present with Indian grouping and crores for big numbers.

## How to behave
- Answer the actual question with the number, then a one-line "how I got it." Offer the drill-down.
- Name the company if it's not Oil. Give date ranges for sales questions.
- Don't wander, don't run writes, don't expose the SAP password in output.
- More example questions: `sap-b1/accounts-kit/ASK-EXAMPLES.md`. Setup: `sap-b1/accounts-kit/SETUP.md`. Full map: `README.md`. Our work log: `chats/`.
