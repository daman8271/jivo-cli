---
entity: CustomsDeclaration
domain: system-other-1
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# CustomsDeclaration
Records import customs declarations linking foreign purchases to customs/broker data for landed-cost handling (empty — imports not tracked here). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CustomsDeclaration --top 5
./sapb1 query CustomsDeclaration --count
./sapb1 query CustomsDeclaration --select "AbsEntry,DocNum,DeclarationDate,VendorCode" --top 10
# declarations still open (no closing date)
./sapb1 query CustomsDeclaration --filter "ClosingDate eq null" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Declaration record key |
| DocNum | Declaration document number |
| DeclarationDate | Customs filing date |
| VendorCode | Foreign vendor key |
| BrokerCode | Customs broker key |
| ClosingDate | Declaration closing date |
## Connections
- Domain: [[system-other-1]]
- [[BusinessPartners]] via VendorCode / BrokerCode — foreign vendor and customs broker
- [[PurchaseInvoices]] via linked import documents — purchases covered by the declaration
- [[LandedCosts]] via declaration reference — landed-cost allocation of customs charges
