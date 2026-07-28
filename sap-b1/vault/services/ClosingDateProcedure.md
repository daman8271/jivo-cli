---
entity: ClosingDateProcedure
domain: system-other-1
readable: true
methods: [GET]
rows_oil: 1
---
# ClosingDateProcedure
Read-only setup for due-date closing procedures (month-end payment-date rules) used by payment terms calculations. Live rows in JIVO_OIL_HANADB: 1.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ClosingDateProcedure --top 5
./sapb1 query ClosingDateProcedure --count
./sapb1 query ClosingDateProcedure --select "ClosingDateCode,ClosingDateNum,BaselineDate,DueMonth" --top 10
# fetch the single defined procedure by key
./sapb1 query ClosingDateProcedure --filter "ClosingDateNum eq 1" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| ClosingDateCode | Procedure key |
| ClosingDateNum | Procedure number |
| BaselineDate | Due-date baseline day |
| DueMonth | Due month offset |
| ExtraDay | Extra days added |
| ExtraMonth | Extra months added |
## Connections
- Domain: [[system-other-1]]
- [[PaymentTermsTypes]] via ClosingDateCode — payment terms using this closing rule
