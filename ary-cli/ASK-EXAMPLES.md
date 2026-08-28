# What you can ask ARY

Copy-paste these. Run `set -a; . ../connections/ary.env; set +a` once first.

## Is it working, and is the data current?

```bash
ary doctor
```
Prints the last document date for every module. Sales stop on 2026-08-21 during
the physical stock audit; accounting is live to today.

## Sales

```bash
ary sales net --from 2026-08-01 --to 2026-09-01        # THE sales figure (bills − returns)
ary sales summary --from 2026-04-01                    # FY to date
ary sales daily --from 2026-08-15                      # day by day + when the feed last wrote
ary sales monthly --from 2025-04-01 -n 18              # the trend
ary sales by-warehouse --from 2026-08-01               # which counter earns
ary sales by-product --from 2026-08-01 -n 25           # top SKUs + gross margin vs cost
ary sales by-customer --from 2026-04-01 -n 30          # top customers (walk-ins grouped)
ary sales by-staff --from 2026-08-01                   # per salesperson, against target
ary sales payment-mix --from 2026-08-01                # cash vs card vs UPI vs credit
ary sales bills --from 2026-08-20 --min-amount 5000    # the big bills
ary sales bill 2264295.0015                            # one bill: header + lines + payments
```

## Stock — and where it is leaking

```bash
ary stock summary                                      # on-hand per counter + every movement bucket
ary stock value                                        # valuation at cost and at MRP, negatives shown separately
ary stock negative -n 40                               # sold without a recorded receipt — start here
ary stock dead --days 180 -n 40                        # capital sitting still
ary stock movement --product 0CU7                      # one SKU, every bucket, every counter
ary stock transfers --from 2026-08-01                  # inter-counter movement
ary stock journals --from 2026-08-01                   # the adjustment documents
```

## The audit (this is the timely one)

```bash
ary audit counts --from 2026-08-01                     # who counted what, when
ary audit count 3905.0015                              # one count sheet in full
ary audit variance                                     # shortage / excess / wastage per counter, in ₹
ary audit shortage -n 40                               # the SKUs that lost the most
ary audit shortage --kind wastage                      # written off
ary audit uncounted --months 6                         # holding stock, not counted lately
```

## Purchases

```bash
ary purchases summary --from 2026-04-01
ary purchases by-supplier --from 2026-04-01 -n 25
ary purchases by-product --from 2026-04-01 -n 25       # with average landed rate
ary purchases bills --from 2026-08-01                  # incl. the vendor's own bill no. + date
ary purchases bill 17339.0015
```

## Money owed

```bash
ary accounts outstanding -n 40                         # bill-wise, positive = they owe ARY
ary accounts ageing                                    # 0-30 / 31-60 / 61-90 / 91-180 / 180+
ary accounts ageing --as-of 2026-08-01
ary accounts list --search "jivo"                      # find an account id
ary accounts get 1                                     # master + balance + open references
ary customers credit -n 40                             # credit customers vs what they actually owe
```

## Ledger

```bash
ary ledger list --from 2026-08-20                      # recent vouchers
ary ledger get 2194735.0001                            # one voucher's double entry
ary ledger statement --account 1 --days 30             # Cash, last 30 days, with opening
ary ledger statement --account 2072 --from 2026-08-01  # Paytm
ary ledger trial --from 2026-04-01                     # by account group
```

## Catalogue

```bash
ary products list --search "maggi"
ary products get 03GT                                  # master + price children + stock by counter
ary products list --barcode 8901058851298
ary products expiring --days 60                        # expiring AND still on the shelf
ary products sap-gap                                   # the missing ARY↔SAP item bridge
ary masters principals                                 # J.L, Vanesa Care, Honasa, Unicorn/Apple
ary masters brands -n 30
```

## Anything else

```bash
ary schema tables --search stock
ary schema columns SaleHeader
ary peek PhysicalStockDetail -n 5
ary query "SELECT TOP 10 * FROM StockJournalHeader ORDER BY VoucherDate DESC"
ary query "SELECT ..." --csv > out.csv
```

## Other databases on the same box

```bash
ary schema databases                                   # all 72
ary --db ARY_BSU peek OADM -n 1                        # the SAP B1 SQL company
ary --db FR8Ilahi query "SELECT MAX(VoucherDate) FROM SaleHeader"
ary --db BusyComp0001_db query "SELECT Name, GSTNo FROM Company"
```
