---
entity: Users
domain: administration-setup-4
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 55
---
# Users
Manages SAP B1 login accounts — user codes, credentials, superuser/lock status, department/branch assignment, and discount/cash limits. Live rows in JIVO_OIL_HANADB: 55.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Users --top 5
./sapb1 query Users --count
./sapb1 query Users --select "InternalKey,UserCode,UserName,eMail" --top 10
# All superuser accounts (audit who has unrestricted access):
./sapb1 query Users --filter "Superuser eq 'tYES'" --select "UserCode,UserName,eMail,Locked"
```

## Key fields
| Field | Meaning |
|---|---|
| InternalKey | Internal numeric user ID |
| UserCode | Login user code |
| UserName | Display name |
| eMail | User email address |
| Superuser | Unrestricted superuser flag |
| Locked | Account locked flag |
| Department | Assigned department code |
| Branch | Assigned branch key |
| Group | User group membership |
| LanguageCode | UI language setting |
| LastLoginTime | Last login timestamp |
| MaxDiscountSales | Max sales discount % |
| MaxDiscountPurchase | Max purchase discount % |
| MobilePhoneNumber | Mobile phone number |

## Connections
- Domain: [[administration-setup-4]]
- [[Departments]] via Department — the department code assigned to the user
- [[Branches]] via Branch — the branch the user is assigned to
- UserGroups via Group — the user group the account belongs to (no UserGroups service exists in the Service Layer catalog)
