---
entity: Contacts
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Contacts
Contact persons attached to business partners; empty as a standalone set here (contacts live inline in BusinessPartners.ContactEmployees). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Contacts --top 5
./sapb1 query Contacts --count
./sapb1 query Contacts --select "ContactCode,CardCode,Name,E_Mail" --top 10
# Contact persons of one business partner (if ever populated):
./sapb1 query Contacts --filter "CardCode eq 'C00001'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ContactCode | Contact numeric code (key) |
| CardCode | Parent business partner |
| Name | Contact internal name |
| FirstName | Contact first name |
| LastName | Contact last name |
| Position | Job title/position |
| Phone1 | Primary phone number |
| MobilePhone | Mobile phone number |
| E_Mail | Contact e-mail address |
| Address | Contact address text |
| CreateDate | Record creation date |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via CardCode (mirrors inline ContactEmployees)
- [[Activities]] via ContactPersonCode
