---
entity: LandedCosts
domain: purchasing
readable: true
methods: ["GET LandedCosts(id)", "GET LandedCosts", "POST LandedCosts", "PATCH LandedCosts(id)", "DELETE LandedCosts(id)", "POST LandedCosts(id)/CloseLandedCost", "POST LandedCosts(id)/CancelLandedCost"]
rows_oil: 522
---
# LandedCosts
Allocates import costs (freight, customs, insurance) onto received goods to compute true landed item cost — actively used for JIVO's oil imports. Live rows in JIVO_OIL_HANADB: 522.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query LandedCosts --top 5
./sapb1 query LandedCosts --count
./sapb1 query LandedCosts --select "LandedCostNumber,VendorCode,PostingDate,Total" --top 10
# Import cost files posted since the start of 2026:
./sapb1 query LandedCosts --filter "PostingDate ge '2026-01-01'" --select "LandedCostNumber,VendorCode,PostingDate,Total,DocumentCurrency"
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| LandedCostNumber | Landed cost document number |
| VendorCode | Import vendor code |
| VendorName | Import vendor name |
| PostingDate | Posting date |
| DueDate | Due date |
| Reference | Free reference text |
| FileNumber | Import file number |
| BillofLadingNumber | Bill of lading reference |
| Broker | Customs broker |
| Total | Total landed cost |
| TotalFreightCharges | Total freight amount |
| DocumentCurrency | Document currency |
| TransactionNumber | Linked journal transaction |
## Connections
- Domain: [[purchasing]]
- [[BusinessPartners]] via VendorCode — the import vendor / freight party
- [[LandedCostsCodes]] via cost lines LandedCostCode — which cost types are allocated
- [[PurchaseDeliveryNotes]] via item lines BaseEntry — the goods receipts costs land on
- [[JournalEntries]] via TransactionNumber — the G/L posting the allocation creates
- [[Currencies]] via DocumentCurrency — currency of Total
