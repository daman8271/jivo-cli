# What you can ask saphist — and the exact command

The old books, 2014-11 → 2024-10. Every dated command routes to the right book
by itself; a range that crosses August 2019 reads both and labels each row.

## "Which book has this year?"

```
saphist books                                  all three, with the period each covers
saphist books which --year 2016
saphist books which --from 2019-06-01 --to 2019-12-01
```

## Sales / turnover

| Question | Command |
|---|---|
| What was our turnover in FY 2016-17? | `saphist sales summary --fy 2016` |
| Month by month for FY 2021-22 | `saphist sales monthly --fy 2021` |
| Every financial year we have | `saphist sales yearly --book all` |
| Turnover across the 2019 changeover | `saphist sales summary --from 2019-04-01 --to 2020-04-01` |
| Top 25 customers of FY 2021-22 | `saphist sales by-party --fy 2021 -n 25` |
| Top selling items that year | `saphist sales by-item --fy 2021 -n 25` |
| Split by branch | `saphist sales by-branch --fy 2022` |
| Last 50 invoices of FY 2020-21 | `saphist sales invoices --fy 2020 -n 50` |
| One invoice in full (header + lines + journal) | `saphist sales invoice 910000134` |
| Sales returns / credit notes | `saphist sales returns --fy 2021` |
| One customer's invoices only | `saphist sales invoices --party CUSTA000606 --fy 2021` |

## Purchases

| Question | Command |
|---|---|
| What did we buy in FY 2021-22? | `saphist purchases summary --fy 2021` |
| Top vendors that year | `saphist purchases by-vendor --fy 2021 -n 25` |
| What we bought, by item | `saphist purchases by-item --fy 2021 -n 25` |
| One vendor's bills | `saphist purchases bills --party VENDA000226 --fy 2021` |
| One A/P bill in full | `saphist purchases bill 1703226060` |
| Debit notes / purchase returns | `saphist purchases returns --fy 2021` |

## A party (customer or vendor)

| Question | Command |
|---|---|
| Find them by name | `saphist party search jindal` |
| Their master card and balance | `saphist party show CUSTA000694` |
| Their ledger, with a running balance | `saphist party statement CUSTA000694 --fy 2022` |
| Who owed JIVO the most | `saphist party balances --owing them -n 25` |
| Who JIVO owed the most | `saphist party balances --owing jivo --type vendor -n 25` |
| What of theirs was still open | `saphist party open CUSTA000694` |

**Watch the `book` column.** A CardCode is not the same party in both books —
`CUSTA000694` is *Bala Ji Store* in `old` and *JIVO MART PVT. LTD.* in `new`.

## General ledger

| Question | Command |
|---|---|
| Find an account by name | `saphist ledger chart --search freight --postable` |
| One account's entries with a running balance | `saphist ledger account 5100016 --fy 2021` |
| Trial balance for a period | `saphist ledger trial-balance --fy 2021 --non-zero -n 200` |
| List journal entries | `saphist ledger entries --fy 2021 -n 50` |
| One journal entry, both sides | `saphist ledger journal 184233` |

## Stock and items

| Question | Command |
|---|---|
| Find an item | `saphist items search mustard` |
| One item's master card | `saphist items show FG0000078` |
| Closing stock, by warehouse and value | `saphist items stock --non-zero -n 100` |
| What moved in a year (bought/sold/returned) | `saphist items movement --fy 2021 -n 40` |

`items stock` is the balance **frozen when the book closed** (Aug-2019 for `old`,
Oct-2024 for `new`) — it is not an as-at-date figure.

## Money in and out

| Question | Command |
|---|---|
| Receipts and payments for a year | `saphist payments summary --fy 2021` |
| Customer receipts | `saphist payments in --fy 2021 -n 50` |
| Vendor payments | `saphist payments out --party VENDA000226 --fy 2021` |
| One payment, what it settled, its journal | `saphist payments show 1703229286` |

## Orders and movements

```
saphist orders sales --fy 2021 --open        sales orders still open
saphist orders purchase --fy 2021            purchase orders
saphist orders deliveries --fy 2021          what went out
saphist orders receipts --fy 2021            goods receipt POs — what vendors delivered
saphist orders show 1703221094 --table OPOR  one document, header and lines
```

## Master data

```
saphist branches           6 in the 'new' book, none in 'old'
saphist warehouses         with the stock value sitting in each
saphist salespeople
saphist item-groups
```

## Getting it out of the terminal

```
saphist sales monthly --fy 2021 --csv > sales-2021.csv
saphist party balances --owing them -n 100 --json
saphist sales invoices --fy 2021 --select DocNum,doc_date,CardName,net
```

## Anything else

```
saphist tables --search inv          find the table
saphist columns OINV                 see its columns
saphist query "SELECT TOP 10 …"      one SELECT, one book (--book old|new|bsu)
```
