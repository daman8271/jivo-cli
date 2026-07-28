---
entity: BusinessPartners
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3384
---
# BusinessPartners
Master data for all 3,384 customers, vendors and leads — the core CRM/AR-AP entity with addresses, bank accounts, contacts and credit terms. Live rows in JIVO_OIL_HANADB: 3384.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BusinessPartners --top 5
./sapb1 query BusinessPartners --count
./sapb1 query BusinessPartners --select "CardCode,CardName,CardType,CurrentAccountBalance" --top 10
# Customers only (cCustomer / cSupplier / cLid for leads):
./sapb1 query BusinessPartners --filter "CardType eq 'cCustomer'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| CardCode | Unique BP code (key) |
| CardName | Business partner name |
| CardType | Customer / vendor / lead |
| GroupCode | BP group assignment |
| Phone1 | Primary phone number |
| EmailAddress | Primary e-mail address |
| Currency | BP default currency |
| CurrentAccountBalance | Open AR/AP balance |
| CreditLimit | Allowed credit ceiling |
| SalesPersonCode | Assigned sales employee |
| PayTermsGrpCode | Payment terms group |
| PriceListNum | Default price list |
| FederalTaxID | Tax registration (GSTIN/PAN) |
| CreateDate | Record creation date |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartnerGroups]] via GroupCode
- [[SalesPersons]] via SalesPersonCode
- [[PriceLists]] via PriceListNum
- [[Currencies]] via Currency
- [[PaymentTermsTypes]] via PayTermsGrpCode
- [[Contacts]] via CardCode (inline ContactEmployees collection)
- [[CommissionGroups]] via CommissionGroupCode
- [[Campaigns]] via campaign target lists referencing CardCode
- [[ChartOfAccounts]] via AR/AP control accounts
