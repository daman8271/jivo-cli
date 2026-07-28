---
entity: BusinessPlaces
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 8
---
# BusinessPlaces
Master data for the company's branches/business places (8 for JIVO — likely GST-registered branches), each with its tax ID, address and default warehouse. Live rows in JIVO_OIL_HANADB: 8.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BusinessPlaces --top 5
./sapb1 query BusinessPlaces --count
./sapb1 query BusinessPlaces --select "BPLID,BPLName,FederalTaxID,DefaultWarehouseID" --top 10
# active branches only (skip disabled ones)
./sapb1 query BusinessPlaces --filter "Disabled eq 'tNO'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| BPLID | Branch key |
| BPLName | Branch name |
| Address | Branch street address |
| City | Branch city |
| County | Branch county/district |
| Country | Branch country code |
| FederalTaxID | Branch GSTIN/tax ID |
| DefaultWarehouseID | Default warehouse key |
| DefaultCustomerID | Default customer partner |
| DefaultVendorID | Default vendor partner |
| DefaultTaxCode | Default tax code |
| MainBPL | Main branch flag |
| Disabled | Branch inactive flag |
| GlobalLocationNumber | GLN identifier |
## Connections
- Domain: [[system-other-1]]
- [[Warehouses]] via DefaultWarehouseID — branch's default stocking warehouse
- [[BusinessPartners]] via DefaultCustomerID / DefaultVendorID — branch default partners
- [[Countries]] via Country — branch address country
- [[Counties]] via County — branch address county/district
- [[SalesTaxCodes]] via DefaultTaxCode — branch default tax code
