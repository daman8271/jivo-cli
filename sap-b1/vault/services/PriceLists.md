---
entity: PriceLists
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 10
---
# PriceLists
Defines the company's price lists (base list, factor, currency, validity) used to price items across sales and purchasing documents. Live rows in JIVO_OIL_HANADB: 10.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PriceLists --top 5
./sapb1 query PriceLists --count
./sapb1 query PriceLists --select "PriceListNo,PriceListName,BasePriceList,Factor" --top 10
# Only currently active price lists
./sapb1 query PriceLists --filter "Active eq 'tYES'"
```

## Key fields
| Field | Meaning |
|---|---|
| PriceListNo | Price list number (key) |
| PriceListName | Display name |
| BasePriceList | Base list it derives from |
| Factor | Multiplier applied to base |
| Active | List active flag |
| IsGrossPrice | Prices are tax-inclusive |
| RoundingMethod | Price rounding rule |
| GroupNum | Linked payment-terms group |
| DefaultPrimeCurrency | Primary pricing currency |
| ValidFrom | Validity start date |
| ValidTo | Validity end date |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[Currencies]] via DefaultPrimeCurrency — currency the list prices in
- [[SpecialPrices]] via PriceListNum — customer/item overrides layered on this list
- [[Items]] via ItemPrices (PriceList) — per-item price rows for each list
