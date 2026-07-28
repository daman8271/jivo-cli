# SAP B1 Service Layer — READ Playbook (start here)

The cheat-sheet you open the moment you connect. It covers the **17 highest-value
read (GET) entities**, the **real** field names to `--select`, and copy-paste
`sapb1 query` commands for the questions people actually ask.

Everything here is **read-only** — the `sapb1` CLI only ever issues OData `GET`
(plus `POST /Login` and `/Logout`). No business data is ever written.

> **Field sourcing — nothing is invented.** Every field below is grounded in one of two
> real sources: (1) the Service Layer API Reference `$select`/payload examples in
> `raw/service-layer-api-reference.html`, and (2) the `sapb1` CLI's own built-in default
> selects in `~/sapb1-cli/internal/cli/*.go` (author-verified against a live SAP box).
> When in doubt, run `sapb1 fields <Entity>` — it does a live `GET <Entity>?$top=1` and
> prints the exact field names your company DB returns.

---

## 0. Get connected first

```bash
sapb1 doctor            # end-to-end check: config present? host reachable? login OK?
sapb1 auth login        # caches the session cookie → "Connected to <company> as <user>"
sapb1 auth status       # resolved config (password masked) + session state
```

If commands hang or fail with `cannot reach … are you on the VPN?` — get on the
company VPN or have your IP whitelisted. The Service Layer host is firewalled to the
corporate network. Also make sure `SAPB1_COMPANYDB` is set (ask your SAP admin).

---

## 1. The one command shape you'll use everywhere

```bash
sapb1 query <Entity> --select "<fields>" --filter "<odata>" --top <N>
```

| Flag         | What it does                                                          |
|--------------|----------------------------------------------------------------------|
| `--select`   | comma-separated **real** fields (also sets table column order)        |
| `--filter`   | raw OData `$filter` (see patterns in §2)                              |
| `--top`      | max rows (default **20**; ignored with `--all`)                       |
| `--orderby`  | raw OData `$orderby`, e.g. `"DocDate desc"`                           |
| `--skip`     | pagination offset                                                    |
| `--all`      | page through **everything** (`odata.nextLink`, capped at 200 pages)   |
| `--count`    | print only the server-side total row count (`$inlinecount`)          |
| `--json`     | **emit the raw OData array as JSON** — pipe to `jq` or an AI agent    |

**`--json` is the AI/automation hook.** Any command + `--json` prints the raw `value`
array so you can pipe it into `jq` or feed it to a model:

```bash
sapb1 query Orders --select "DocNum,CardName,DocTotal" --filter "DocStatus eq 'O'" --json \
  | jq '.[] | {DocNum, CardName, DocTotal}'
```

**Discovery helpers (offline-friendly):**

```bash
sapb1 entities --read-only          # list every readable entity in the catalog
sapb1 entities --search invoice     # find the entity set name you want
sapb1 fields Orders                 # live: what can I --select on this entity?
```

**Shortcuts:** `Orders`, `Invoices`, `Items`, `BusinessPartners` also have typed
subcommands — `sapb1 orders list --open`, `sapb1 partners list --customers`,
`sapb1 items list --low-stock 10`. Everything else goes through `query`.

---

## 2. Common filter patterns (OData `$filter`)

OData string literals use **single quotes**; wrap the whole expression in **double
quotes** for the shell. Dates are ISO strings in single quotes.

| Intent                | Pattern                                                        |
|-----------------------|----------------------------------------------------------------|
| **Open documents**    | `DocStatus eq 'O'`  (`'C'` = closed)                           |
| **Date range**        | `DocDate ge '2026-01-01' and DocDate le '2026-03-31'`         |
| **Since a date**      | `DocDate ge '2026-01-01'`                                     |
| **By customer/vendor**| `CardCode eq 'C1234'`                                         |
| **Value threshold**   | `DocTotal gt 10000`                                           |
| **Low stock**         | `QuantityOnStock le 10`                                       |
| **Text starts-with**  | `startswith(ItemCode, 'A')`                                   |
| **Only customers**    | `CardType eq 'cCustomer'`  (suppliers: `'cSupplier'`)         |
| **Combine (AND/OR)**  | `DocStatus eq 'O' and DocTotal gt 50000`                      |

Operators: `eq ne gt ge lt le`, joined with `and` / `or`. Sort with
`--orderby "DocDate desc"`.

---

## 3. The 17 entities

Sales/purchase documents (§3.1–3.8) all share the same **marketing-document** shape,
so the header fields — `DocEntry, DocNum, DocDate, DocDueDate, CardCode, CardName,
DocTotal, DocStatus, DocCurrency, Comments, Series` — and the nested `DocumentLines`
(`ItemCode, Quantity, UnitPrice, TaxCode, WarehouseCode`) are the same across all of them.

---

### 3.1 `Orders` — Sales Orders

**Holds:** confirmed customer sales orders (the sales-demand backbone). Header + line items.

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `DocDueDate`, `CardCode`,
`CardName`, `DocTotal`, `DocStatus`, `DocCurrency`, `DocumentLines`

**Q: What sales orders are still open right now?**
```bash
sapb1 query Orders --select "DocNum,DocDate,CardName,DocTotal,DocStatus" \
  --filter "DocStatus eq 'O'" --orderby "DocDate desc" --top 50
```

**Q: What did customer C1234 order this quarter?**
```bash
sapb1 query Orders --select "DocNum,DocDate,DocTotal,DocCurrency" \
  --filter "CardCode eq 'C1234' and DocDate ge '2026-01-01'" --top 100 --json
```

---

### 3.2 `Quotations` — Sales Quotations

**Holds:** pre-sales price quotes offered to customers (the top of the sales funnel).

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `DocDueDate`, `CardCode`,
`CardName`, `DocTotal`, `DocStatus`, `DocumentLines`

**Q: Which quotations are still open (not yet won/lost)?**
```bash
sapb1 query Quotations --select "DocNum,DocDate,CardName,DocTotal" \
  --filter "DocStatus eq 'O'" --orderby "DocTotal desc" --top 50
```

**Q: What's the total value of quotes we sent since Jan?**
```bash
sapb1 query Quotations --select "DocNum,DocDate,DocTotal" \
  --filter "DocDate ge '2026-01-01'" --all --json | jq '[.[].DocTotal] | add'
```

---

### 3.3 `Invoices` — A/R Invoices

**Holds:** what you billed customers (revenue + receivables). Open invoices = money owed to you.

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `DocDueDate`, `CardCode`,
`CardName`, `DocTotal`, `DocStatus`, `DocCurrency`

**Q: Which invoices are open (unpaid) and how much do customers owe?**
```bash
sapb1 query Invoices --select "DocNum,CardName,DocDate,DocDueDate,DocTotal" \
  --filter "DocStatus eq 'O'" --orderby "DocTotal desc" --top 50
```

**Q: What are our biggest invoices this year (over 10k)?**
```bash
sapb1 query Invoices --select "DocNum,CardName,DocTotal" \
  --filter "DocDate ge '2026-01-01' and DocTotal gt 10000" --top 100 --json
```

---

### 3.4 `CreditNotes` — A/R Credit Notes

**Holds:** customer credits/returns issued against invoices (reduces receivables/revenue).

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `CardCode`, `CardName`,
`DocTotal`, `DocStatus`, `Comments`, `DocumentLines`

**Q: How much did we credit back to customers this quarter?**
```bash
sapb1 query CreditNotes --select "DocNum,DocDate,CardName,DocTotal" \
  --filter "DocDate ge '2026-01-01'" --all --json | jq '[.[].DocTotal] | add'
```

**Q: Which credit notes did we issue to customer C1234?**
```bash
sapb1 query CreditNotes --select "DocNum,DocDate,DocTotal,Comments" \
  --filter "CardCode eq 'C1234'" --orderby "DocDate desc" --top 50
```

---

### 3.5 `DeliveryNotes` — Deliveries (A/R)

**Holds:** goods shipped to customers (fulfilment). Open deliveries = shipped-but-not-yet-invoiced.

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `CardCode`, `CardName`,
`DocTotal`, `DocStatus`, `Comments`, `DocumentLines`

**Q: What have we shipped but not yet invoiced (open deliveries)?**
```bash
sapb1 query DeliveryNotes --select "DocNum,DocDate,CardName,DocTotal,DocStatus" \
  --filter "DocStatus eq 'O'" --orderby "DocDate desc" --top 50
```

**Q: What did we deliver to customer C1234 this month?**
```bash
sapb1 query DeliveryNotes --select "DocNum,DocDate,DocTotal" \
  --filter "CardCode eq 'C1234' and DocDate ge '2026-07-01'" --top 100 --json
```

---

### 3.6 `PurchaseOrders` — Purchase Orders (A/P)

**Holds:** what you ordered from suppliers (procurement demand). Open POs = incoming goods on order.

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `DocDueDate`, `CardCode`
(supplier), `CardName`, `DocTotal`, `DocStatus`, `DocumentLines`

**Q: Which purchase orders are still open with suppliers?**
```bash
sapb1 query PurchaseOrders --select "DocNum,DocDate,CardName,DocTotal,DocStatus" \
  --filter "DocStatus eq 'O'" --orderby "DocDate desc" --top 50
```

**Q: What have we ordered from supplier V1001 this year?**
```bash
sapb1 query PurchaseOrders --select "DocNum,DocDate,DocTotal" \
  --filter "CardCode eq 'V1001' and DocDate ge '2026-01-01'" --top 100 --json
```

---

### 3.7 `PurchaseInvoices` — A/P Invoices

**Holds:** what suppliers billed you (payables). Open A/P invoices = money you owe.

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `DocDueDate`, `CardCode`
(supplier), `CardName`, `DocTotal`, `DocStatus`, `Comments`

**Q: Which supplier invoices are open (unpaid) and due soon?**
```bash
sapb1 query PurchaseInvoices --select "DocNum,CardName,DocDueDate,DocTotal" \
  --filter "DocStatus eq 'O'" --orderby "DocDueDate" --top 50
```

**Q: How much did we get billed by suppliers this quarter?**
```bash
sapb1 query PurchaseInvoices --select "DocNum,DocDate,DocTotal" \
  --filter "DocDate ge '2026-01-01'" --all --json | jq '[.[].DocTotal] | add'
```

---

### 3.8 `PurchaseDeliveryNotes` — Goods Receipt POs (A/P)

**Holds:** goods received from suppliers (the receiving side of procurement).

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `CardCode` (supplier),
`CardName`, `DocTotal`, `DocStatus`, `Comments`, `DocumentLines`

**Q: What goods have we received this month?**
```bash
sapb1 query PurchaseDeliveryNotes --select "DocNum,DocDate,CardName,DocTotal" \
  --filter "DocDate ge '2026-07-01'" --orderby "DocDate desc" --top 50
```

**Q: What did we receive from supplier V1001 that's still open?**
```bash
sapb1 query PurchaseDeliveryNotes --select "DocNum,DocDate,DocTotal,DocStatus" \
  --filter "CardCode eq 'V1001' and DocStatus eq 'O'" --top 100 --json
```

---

### 3.9 `Items` — Items / Products (master data)

**Holds:** the product/material master — codes, names, item group, on-hand stock, sell/buy flags.

**Key fields:** `ItemCode` (key), `ItemName`, `ForeignName`, `ItemsGroupCode`,
`QuantityOnStock`, `ItemType`, `BarCode`, `Valid`

**Q: Which items are low on stock (10 or fewer on hand)?**
```bash
sapb1 query Items --select "ItemCode,ItemName,ItemsGroupCode,QuantityOnStock" \
  --filter "QuantityOnStock le 10" --orderby "QuantityOnStock" --top 100
# shortcut: sapb1 items list --low-stock 10
```

**Q: What items belong to item group 100?**
```bash
sapb1 query Items --select "ItemCode,ItemName,QuantityOnStock" \
  --filter "ItemsGroupCode eq 100" --top 200 --json
```

---

### 3.10 `BusinessPartners` — Customers & Suppliers (master data)

**Holds:** the BP master — customers (`cCustomer`), suppliers (`cSupplier`), leads —
with contact info and current balance.

**Key fields:** `CardCode` (key), `CardName`, `CardType`, `GroupCode`, `Phone1`,
`EmailAddress`, `CurrentAccountBalance`

**Q: Which customers currently owe us money (positive balance)?**
```bash
sapb1 query BusinessPartners --select "CardCode,CardName,CurrentAccountBalance,Phone1" \
  --filter "CardType eq 'cCustomer' and CurrentAccountBalance gt 0" \
  --orderby "CurrentAccountBalance desc" --top 50
```

**Q: Give me the full supplier contact list.**
```bash
sapb1 query BusinessPartners --select "CardCode,CardName,Phone1,EmailAddress" \
  --filter "CardType eq 'cSupplier'" --all --json
# shortcut: sapb1 partners list --suppliers --json
```

---

### 3.11 `StockTransfers` — Inventory Transfers between warehouses

**Holds:** movements of stock from one warehouse to another (no purchase/sale). Line-level
`WarehouseCode` on `StockTransferLines` shows where stock moved.

**Key fields:** `DocEntry` (key), `DocNum`, `DocDate`, `Series`, `Printed`, `CardCode`,
`StockTransferLines` (`ItemCode`, `Quantity`, `WarehouseCode`)

**Q: What stock transfers happened this month?**
```bash
sapb1 query StockTransfers --select "DocEntry,DocNum,DocDate,CardCode" \
  --filter "DocDate ge '2026-07-01'" --orderby "DocDate desc" --top 50
```

**Q: Show the line detail (items + warehouses) of a specific transfer.**
```bash
sapb1 query StockTransfers --select "DocNum,DocDate,StockTransferLines" \
  --filter "DocNum eq 123" --json | jq '.[].StockTransferLines'
```

---

### 3.12 `Drafts` — Document Drafts (any type)

**Holds:** unposted draft documents of every kind — the type is in `DocObjectCode`
(e.g. `17` = Sales Order, `13` = A/R Invoice, `22` = Purchase Order, `23` = Quotation).

**Key fields:** `DocEntry` (key), `DocNum`, `DocType`, `DocObjectCode`, `CardCode`,
`DocDueDate`, `Comments`, `DocumentLines`

**Q: What draft sales orders are sitting unposted?**
```bash
sapb1 query Drafts --select "DocEntry,DocNum,DocObjectCode,CardCode,DocDueDate" \
  --filter "DocObjectCode eq '17'" --top 50
```

**Q: How many drafts are pending overall?**
```bash
sapb1 query Drafts --count
```

---

### 3.13 `JournalEntries` — GL Journal Entries

**Holds:** the general-ledger postings (double-entry accounting). Each entry has debit/credit
`JournalEntryLines` per account.

**Key fields:** `JdtNum` (key/entry number), `ReferenceDate`, `DueDate`, `Memo`,
`Reference`, `TransId`, `JournalEntryLines` (`AccountCode`, `Debit`, `Credit`)

**Q: What was posted to the GL since the start of the year?**
```bash
sapb1 query JournalEntries --select "JdtNum,ReferenceDate,Memo,Reference" \
  --filter "ReferenceDate ge '2026-01-01'" --orderby "JdtNum" --all
```

**Q: Show the debit/credit lines of a specific journal entry.**
```bash
sapb1 query JournalEntries --select "JdtNum,ReferenceDate,JournalEntryLines" \
  --filter "JdtNum eq 123" --json | jq '.[].JournalEntryLines'
```

---

### 3.14 `Warehouses` — Warehouse master data

**Holds:** the list of physical/logical warehouses (locations stock lives in).

**Key fields:** `WarehouseCode` (key), `WarehouseName`, `Location`, `Street`, `ZipCode`

**Q: List all warehouses and where they are.**
```bash
sapb1 query Warehouses --select "WarehouseCode,WarehouseName,Location" --top 100
```

**Q: Find a specific warehouse by code.**
```bash
sapb1 query Warehouses --select "WarehouseCode,WarehouseName,Street,ZipCode" \
  --filter "WarehouseCode eq '01'" --json
```

---

### 3.15 `ItemGroups` — Item Group master data

**Holds:** the categories items are bucketed into (`ItemsGroupCode` on `Items` joins here).

**Key fields:** `Number` (key/group code), `GroupName`, `MinimumOrderQuantity`,
`PriceDifferencesAccount`

**Q: List all item groups (to decode `ItemsGroupCode`).**
```bash
sapb1 query ItemGroups --select "Number,GroupName" --orderby "Number" --top 200
```

**Q: Look up the name of a specific item group.**
```bash
sapb1 query ItemGroups --select "Number,GroupName,MinimumOrderQuantity" \
  --filter "Number eq 100" --json
```

---

### 3.16 `PriceLists` — Price Lists

**Holds:** the pricing tiers (retail, wholesale, etc.) referenced across items and BPs.

**Key fields:** `PriceListNo` (key), `PriceListName`, `BasePriceList`, `Factor`,
`GroupNum`, `RoundingMethod`

**Q: List all price lists.**
```bash
sapb1 query PriceLists --select "PriceListNo,PriceListName,BasePriceList" \
  --orderby "PriceListNo" --top 100
```

**Q: Which price lists are derived from another (have a base list + factor)?**
```bash
sapb1 query PriceLists --select "PriceListNo,PriceListName,BasePriceList,Factor" \
  --filter "PriceListNo ge 1" --json
```

---

### 3.17 `SalesPersons` — Sales Employees

**Holds:** the sales-rep master (owner of orders/invoices via `SalesPersonCode` on documents).

**Key fields:** `SalesEmployeeCode` (key), `SalesEmployeeName`, `Remarks`, `Active`

**Q: List all active sales employees.**
```bash
sapb1 query SalesPersons --select "SalesEmployeeCode,SalesEmployeeName" \
  --filter "Active eq 'tYES'" --orderby "SalesEmployeeCode" --top 100
```

**Q: Look up a sales rep by code.**
```bash
sapb1 query SalesPersons --select "SalesEmployeeCode,SalesEmployeeName,Remarks" \
  --filter "SalesEmployeeCode eq 3" --json
```

---

## 4. Recipes that combine entities

```bash
# Open A/R exposure: sum of everything customers still owe on open invoices
sapb1 query Invoices --select "DocTotal" --filter "DocStatus eq 'O'" --all --json \
  | jq '[.[].DocTotal] | add'

# Top 10 customers by outstanding balance
sapb1 query BusinessPartners --select "CardName,CurrentAccountBalance" \
  --filter "CardType eq 'cCustomer'" --orderby "CurrentAccountBalance desc" --top 10

# Everything ordered but not yet delivered this month, as JSON for an AI to summarize
sapb1 query Orders --select "DocNum,CardName,DocTotal,DocStatus" \
  --filter "DocStatus eq 'O' and DocDate ge '2026-07-01'" --all --json
```

---

## 5. Gotchas

- **VPN / whitelist first** — every network command fails fast with a clear message
  if you're off-network. Run `sapb1 doctor` to confirm.
- **`--top` defaults to 20.** Use a bigger `--top`, or `--all` to page through everything
  (capped at 200 pages — narrow your `--filter` if you hit the cap).
- **String values need single quotes inside the double-quoted filter:** `"CardCode eq 'C1234'"`.
- **Not sure a field exists on your DB?** `sapb1 fields <Entity>` prints the live field list.
  Field availability can vary slightly by SAP B1 version and localization.
- **Read-only, always.** Nothing here can modify SAP data.
