---
entity: NatureOfAssessees
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3
---
# NatureOfAssessees
India TDS lookup classifying business partners by assessee type (company/individual/others) for withholding-tax determination. Live rows in JIVO_OIL_HANADB: 3 — COM "Company" (atCompany), IND "Individual" (atOthers), HUF "HUF" (atOthers).

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query NatureOfAssessees --top 5
./sapb1 query NatureOfAssessees --count
./sapb1 query NatureOfAssessees --select "AbsEntry,Code,AssesseeType,Description" --top 10
# Company-type assessees only (enum value verified live):
./sapb1 query NatureOfAssessees --filter "AssesseeType eq 'atCompany'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Record numeric key |
| Code | Short code (COM/IND/HUF) |
| AssesseeType | Enum: atCompany / atOthers |
| Description | Assessee class description |

## Connections
- Domain: [[system-other-1]]
- [[BusinessPartners]] via assessee-type on BP fiscal/TDS settings — drives withholding-tax rate selection
