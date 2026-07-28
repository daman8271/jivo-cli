# Query Cookbook — business questions → sapb1 commands

Real questions answered with the read-only CLI. Every command starts with `cd /Users/damanpreetsingh/sap-b1/cli` (the CLI reads `.env` from the current directory). Default company is `JIVO_OIL_HANADB`; add `--company JIVO_MART_HANADB` / `--company JIVO_BEVERAGES_HANADB` to switch (see [[00-SAP-B1-Atlas]]). All recipes target entities that actually hold data at JIVO ([[03-Live-Data-Census]]). Add `--csv` or `--json` to any read for machine-friendly output.

## Sales

**1. Biggest invoices this fiscal year** — [[Invoices]] (30.3k rows)
```bash
./sapb1 query Invoices --filter "DocDate ge '2026-04-01'" --orderby "DocTotal desc" --select "DocNum,DocDate,CardCode,CardName,DocTotal" --top 20
```

**2. Top customers by open A/R balance (receivables)** — [[BusinessPartners]] (3.4k rows)
```bash
./sapb1 query BusinessPartners --filter "CardType eq 'cCustomer' and CurrentAccountBalance gt 0" --orderby "CurrentAccountBalance desc" --select "CardCode,CardName,CurrentAccountBalance,CreditLimit" --top 20
```

**3. The live open order book (orders awaiting delivery)** — [[Orders]] (14.6k rows)
```bash
./sapb1 query Orders --filter "DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'" --orderby "DocDueDate asc" --select "DocNum,DocDate,DocDueDate,CardName,DocTotal" --top 30
# just the number:
./sapb1 query Orders --count --filter "DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'"
```

**4. Overdue open invoices (collection list)** — [[Invoices]]
```bash
./sapb1 query Invoices --filter "DocumentStatus eq 'bost_Open' and DocDueDate lt '2026-07-23'" --orderby "DocDueDate asc" --select "DocNum,DocDueDate,CardCode,CardName,DocTotal" --top 30
```

**5. Monthly sales count by branch (all three companies)** — [[Invoices]] via `--company`
```bash
for DB in JIVO_OIL_HANADB JIVO_MART_HANADB JIVO_BEVERAGES_HANADB; do
  echo -n "$DB: "; ./sapb1 query Invoices --count --filter "DocDate ge '2026-07-01' and DocDate le '2026-07-31'" --company $DB
done
```

**6. Credit-note leakage — biggest A/R credit memos this quarter** — [[CreditNotes]] (6.4k rows)
```bash
./sapb1 query CreditNotes --filter "DocDate ge '2026-04-01'" --orderby "DocTotal desc" --select "DocNum,DocDate,CardName,DocTotal" --top 20
```

**7. A customer's recent orders (account review)** — [[Orders]] + [[BusinessPartners]]
```bash
./sapb1 query BusinessPartners --filter "startswith(CardName, 'JIVO')" --select "CardCode,CardName,CurrentAccountBalance"   # find the CardCode
./sapb1 query Orders --filter "CardCode eq 'C00001'" --orderby "DocDate desc" --select "DocNum,DocDate,DocTotal,DocumentStatus" --top 10
```

**8. Sales-rep directory (who owns which document)** — [[SalesPersons]] (155 rows)
```bash
./sapb1 query SalesPersons --select "SalesEmployeeCode,SalesEmployeeName,Active" --all
```

## Inventory

**9. Out-of-stock items** — [[Items]] (2,264 SKUs)
```bash
./sapb1 query Items --filter "QuantityOnStock le 0 and Frozen eq 'tNO'" --select "ItemCode,ItemName,QuantityOnStock,DefaultWarehouse" --top 30
```

**10. Stock on hand, biggest holdings first** — [[Items]]
```bash
./sapb1 query Items --filter "QuantityOnStock gt 0" --orderby "QuantityOnStock desc" --select "ItemCode,ItemName,QuantityOnStock,AvgStdPrice" --top 30
```

**11. An item's prices on every price list** — [[Items]] + [[PriceLists]] (10 lists)
```bash
./sapb1 query PriceLists --select "PriceListNo,PriceListName,BasePriceList,Factor" --all
./sapb1 query Items --filter "ItemCode eq 'A0001'" --json          # ItemPrices collection = price per list
./sapb1 query SpecialPrices --top 22                                # customer-specific overrides ([[SpecialPrices]])
```

**12. Batches expiring in the next 90 days (oil shelf life)** — [[BatchNumberDetails]] (17.3k batches)
```bash
./sapb1 query BatchNumberDetails --filter "ExpirationDate ge '2026-07-23' and ExpirationDate le '2026-10-21'" --orderby "ExpirationDate asc" --select "ItemCode,ItemDescription,Batch,ExpirationDate,Status" --top 30
```

**13. Recent inter-depot stock transfers** — [[StockTransfers]] (11.7k) across 58 [[Warehouses]]
```bash
./sapb1 query StockTransfers --filter "DocDate ge '2026-07-01'" --orderby "DocDate desc" --select "DocNum,DocDate,FromWarehouse,ToWarehouse" --top 20
./sapb1 query Warehouses --select "WarehouseCode,WarehouseName,BusinessPlaceID" --all   # the depot map
```

## Purchasing

**14. Open purchase orders (goods still expected)** — [[PurchaseOrders]] (4.2k rows)
```bash
./sapb1 query PurchaseOrders --filter "DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'" --orderby "DocDueDate asc" --select "DocNum,DocDate,DocDueDate,CardName,DocTotal" --top 30
```

**15. Top vendors by open A/P balance (payables)** — [[BusinessPartners]]
```bash
./sapb1 query BusinessPartners --filter "CardType eq 'cSupplier' and CurrentAccountBalance gt 0" --orderby "CurrentAccountBalance desc" --select "CardCode,CardName,CurrentAccountBalance" --top 20
```

**16. This month's A/P invoices from a vendor** — [[PurchaseInvoices]] (15.9k rows)
```bash
./sapb1 query PurchaseInvoices --filter "CardCode eq 'V00001' and DocDate ge '2026-07-01'" --orderby "DocDate desc" --select "DocNum,DocDate,CardName,DocTotal" --top 20
```

**17. Landed-cost documents on recent imports** — [[LandedCosts]] (522 rows)
```bash
./sapb1 query LandedCosts --orderby "DocEntry desc" --select "DocEntry,DocNum,PostingDate,VendorCode" --top 10
```

## Money & books

**18. Cash collected this week** — [[IncomingPayments]] (13.8k rows)
```bash
./sapb1 query IncomingPayments --filter "DocDate ge '2026-07-20'" --orderby "DocDate desc" --select "DocNum,DocDate,CardCode,CardName,CashSum,TransferSum" --top 30
```

**19. Payments we made to vendors this month** — [[VendorPayments]] (14.2k rows)
```bash
./sapb1 query VendorPayments --filter "DocDate ge '2026-07-01'" --orderby "DocDate desc" --select "DocNum,DocDate,CardCode,CardName,CashSum,TransferSum" --top 30
```

**20. G/L journal activity in a date range** — [[JournalEntries]] (131k rows — always filter!)
```bash
./sapb1 query JournalEntries --filter "ReferenceDate ge '2026-07-01' and ReferenceDate le '2026-07-23'" --select "JdtNum,ReferenceDate,Memo,Reference" --top 30
./sapb1 query ChartOfAccounts --filter "startswith(Code, '4')" --select "Code,Name,Balance" --top 30   # revenue accounts ([[ChartOfAccounts]])
```

**21. Production throughput — open work orders at the plant** — [[ProductionOrders]] (7.7k rows)
```bash
./sapb1 query ProductionOrders --filter "ProductionOrderStatus eq 'boposReleased'" --select "DocumentNumber,ItemNo,PlannedQuantity,CompletedQuantity,DueDate,Warehouse" --top 30
```

### Notes
- Dates are plain `'YYYY-MM-DD'` strings in `$filter` (Service Layer accepts them directly) — shift the examples' dates as needed.
- Discover any entity's real field names first: `./sapb1 fields <Entity>`; find entities: `./sapb1 entities | grep -i <word>`; see an entity's operations: `./sapb1 ops <Entity>`.
- `--count` is server-side and cheap; `--all` paginates everything (capped at 200 pages) — prefer filters on big tables like [[JournalEntries]], [[FormPreferences]], [[StockTakings]].
