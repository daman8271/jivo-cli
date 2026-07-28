---
entity: BlanketAgreements
domain: sales-ar
readable: true
methods: ["GET BlanketAgreements(id)", "GET BlanketAgreements", "POST BlanketAgreements", "PATCH BlanketAgreements(id)", "POST BlanketAgreements(id)/CancelBlanketAgreement", "POST BlanketAgreements(id)/GetRelatedDocuments"]
rows_oil: 0
---
# BlanketAgreements
Long-term customer sales agreements (blanket agreements) committing quantities or amounts over a date range; empty in JIVO_OIL_HANADB so fields listed from the SAP B1 standard schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BlanketAgreements --top 5
./sapb1 query BlanketAgreements --count
./sapb1 query BlanketAgreements --select "AgreementNo,BPCode,StartDate,EndDate" --top 10
# Only agreements still in force (approved, not draft/terminated):
./sapb1 query BlanketAgreements --filter "Status eq 'asApproved'" --select "AgreementNo,BPCode,StartDate,EndDate"
```
## Key fields
| Field | Meaning |
|---|---|
| AgreementNo | Internal agreement key |
| BPCode | Customer code |
| StartDate | Agreement start date |
| EndDate | Agreement end date |
| TerminateDate | Early termination date |
| Status | Draft/approved/terminated status |
| AgreementType | General or specific type |
| AgreementMethod | Monetary or quantity commitment |
| PaymentTerms | Payment terms code |
| PriceList | Price list applied |
| Owner | Owning sales employee |
| Project | Linked project code |
| DocNum | Visible agreement number |
| Description | Free-text description |
## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via BPCode — the customer bound by the agreement
- [[PriceLists]] via PriceList — pricing applied to agreement releases
- [[Projects]] via Project — project the agreement is booked under
- [[PaymentTermsTypes]] via PaymentTerms — payment terms governing releases
- [[SalesPersons]] via Owner — sales employee who owns the agreement
