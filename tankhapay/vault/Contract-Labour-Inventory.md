---
tags: [tankhapay, section, contract-labour-inventory]
---
# Contract Labour & D-Inventory

Two operational tracks for non-payroll workforce and assets. **Contract Labour** (`contractLabor/*`,
business backend) — contractors, their daily labour entries, labour details/rates and the contractor
approval workflow. **D-Inventory** (`dinventory/*`, mobapi backend) — asset/product issuance to
employees, barcode-tracked (who holds what, by status). The reads list dashboards, labour entries
and inventory holdings; writes save/assign. AES-encrypted POST ([[Encryption-Scheme]]); one JWT
([[Auth-and-Access]]). 9 reads, 4 writes, 6 ambiguous.

## Read endpoints (in-scope for the CLI)

| Command (`contract …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `contractor-dashboard` | business | `actionType`, `customerAccountId` | contractor dashboard summary |
| `contractor-dashboard-approval-workflow` | business | `actionType`, `customerAccountId`, `contractorId`, `departmentId`, `status`, `dateFrom`, `dateTo`, `id` | approval-workflow rows |
| `contractor-daily-labour-entry` | business | `actionType`, `customerAccountId`, `contractorId`, `departmentId`, `startDate`, `endDate` | daily labour entries |
| `labour-details` | business | `actionType`, `customerAccountId`, `contractorId` | labour details for a contractor |
| `manage-contractor-status` | business | `customerAccountId`, `actionType`, `contractorId`, `changedBy` | contractor status (read via `actionType`) |
| `master-data-node` | business | `actionType`, `customerAccountId` | contract-labour master nodes |
| `d-inventory-emp-list` | mobapi | account ctx | employees with issued inventory |
| `emp-product-list` | mobapi | account ctx + `empCode` | products issued to an employee |
| `emp-product-list-by-status` | mobapi | account ctx + `status` | issued products filtered by status |

### Account context
`customerAccountId` = **2719**; `actionType` selects the read mode; `contractorId`, `departmentId`,
`startDate`/`endDate` (or `dateFrom`/`dateTo`), `status`, `empCode` via `--set`.

## Write endpoints (documented, OUT OF SCOPE)

```
d-inventory   : dinventory/{saveDInventory, assignDInventoryEmpRole, assignDInventoryReportingManager,
    getAssignedDInventoryProductList}
```
UNKNOWN (not wired — mostly `manage*` create/update handlers): `contractLabor/{manageContractor,
manageContractorApproval, manageContractorDailyLabourEntry, manageLabourRates, manageLabourType}`,
`dinventory/validateBarcodes_tpself`.

## CLI command mapping

```
tankhapay-portal contract contractor-dashboard --set actionType=…
tankhapay-portal contract contractor-daily-labour-entry --set contractorId=… --set startDate=… --set endDate=…
tankhapay-portal contract emp-product-list --set empCode=…
tankhapay-portal contract d-inventory-emp-list
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Training-Performance]]
