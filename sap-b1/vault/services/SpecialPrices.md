---
entity: SpecialPrices
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 22
---
# SpecialPrices
Customer/item-specific special price agreements that override standard price lists with discounts and validity periods. Live rows in JIVO_OIL_HANADB: 22.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SpecialPrices --top 5
./sapb1 query SpecialPrices --count
./sapb1 query SpecialPrices --select "ItemCode,CardCode,Price,DiscountPercent" --top 10
# Only agreements still marked valid
./sapb1 query SpecialPrices --filter "Valid eq 'tYES'"
```

## Key fields
| Field | Meaning |
|---|---|
| ItemCode | Item under agreement (key) |
| CardCode | Business partner (key) |
| PriceListNum | Base price list overridden |
| Price | Agreed special price |
| Currency | Price currency |
| DiscountPercent | Discount off list price |
| AutoUpdate | Follows base-list changes |
| Valid | Agreement validity flag |
| ValidFrom | Agreement start date |
| ValidTo | Agreement end date |
| SourcePrice | Price source basis |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[Items]] via ItemCode — item the special price applies to
- [[BusinessPartners]] via CardCode — customer/vendor holding the agreement
- [[PriceLists]] via PriceListNum — standard list being overridden
- [[Currencies]] via Currency — currency of the agreed price
