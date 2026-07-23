---
title: "Admin — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, admin]
---

# Admin — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Jivo Mart (JIVO_MART) only. Last verified: 2026-06-30.

## 1. Purpose — what this section is for in the factory

The Admin section is the access-control and operational-exception management layer of the Jivo Mart factory app. It serves two distinct functions:

**User & permission management.** Admins can view and manage all factory app users (62 total for JIVO_MART), assign permissions, and organize staff into departments. Every capability across Gate, QC, GRPO, Barcode, Dispatch, and Warehouse sections is permission-gated (871 distinct Django permission strings visible on a superuser profile), and the Admin section is where those permissions are managed.

**Docking scan-exception approvals.** During outbound dispatch loading, the Docking module requires barcode scanning of every box being loaded. Two kinds of exceptions arise in practice and require supervisor sign-off before the dispatch can proceed:
- **Partial dispatch:** only some boxes were scanned (e.g. a vehicle carried a mix of old pre-barcode stock and new barcoded boxes — old ones cannot be scanned)
- **Scan skip:** the entire scan step is bypassed for a dispatch (e.g. a JIVO MART own-vehicle carrying only old-sticker stock)

Both exception types land in Admin approval queues. The admin reviewer (in practice, Bhupinder Singh / EP000) either approves or rejects each request before the dispatch can be committed. This creates an auditable paper trail of every scan bypass that occurred, who requested it, why, and who signed off.

---

## 2. Page tree (page -> subpage -> sub-subpage / wizard steps)

```
/admin
├── (hub page) Admin dashboard — navigation landing, user list overview
├── /admin/docking
│   ├── /admin/docking/partial-dispatch-approvals
│   │   └── Approval queue for partial-scan requests
│   │       (raised when scanned_boxes < expected_boxes for a dispatch)
│   └── /admin/docking/scan-approvals
│       └── Approval queue for scan-skip requests
│           (raised when barcode scanning is bypassed entirely for a dispatch)
```

**What `/admin` shows:** Based on the permission structure (`accounts.can_manage_user_permissions`, `accounts.can_manage_department`) and the `/accounts/users/` and `/accounts/departments/` endpoints, the admin landing page is a user management hub — it lists all factory users with search/filter, links to each user's profile/permissions editor, and shows department management. There is no separate API endpoint that returns an "admin dashboard summary"; the page loads user list and department data directly.

---

## 3. Per-page detail

### 3.1 Admin home (`/admin`) — User Management Hub

**Purpose:** Lists all factory app users, allows admins to view/edit user profiles, assign or revoke permissions, and manage departments. This is the system-wide identity and access layer.

**Data shown:**
- Paginated user list (id, email, full_name, employee_code, is_active, is_staff, date_joined)
- Department list for filtering/grouping
- Current session user's own profile via `/accounts/me/` (shown in header/sidebar)

**API endpoints:**
| Endpoint | Method | Description |
|---|---|---|
| `GET /accounts/users/` | read | All factory users for JIVO_MART |
| `GET /accounts/me/` | read | Authenticated user's own profile + all permissions |
| `GET /accounts/departments/` | read | Department reference list |

**Key fields (User):**

| Field | Description |
|---|---|
| `id` | Internal user ID |
| `email` | Login email (domain: @jivo.in for factory staff) |
| `full_name` | Display name |
| `employee_code` | HR employee code (e.g. EP1403, JWPL0030) |
| `is_active` | Whether user can log in |
| `is_staff` | Django staff flag (14 of 62 users); gives Django admin panel access |
| `is_superuser` | Full permission bypass (only id=2 test/dev user) |
| `date_joined` | Account creation timestamp |
| `companies[]` | Multi-company membership (JIVO_OIL, JIVO_MART, JIVO_BEVERAGES) with `role` and `is_default` |
| `permissions[]` | Full permission string list (only on `/accounts/me/`; not returned in user list) |

**Key fields (Department):**

| Field | Description |
|---|---|
| `id` | Department ID |
| `name` | Department name |
| `description` | Optional description |

**Real samples from Jivo Mart API:**

*Selected users from `GET /accounts/users/`:*

```json
{"id": 19, "email": "bhupinder@jivo.in", "full_name": "Bhupinder Singh",
 "employee_code": "EP000", "is_active": true, "is_staff": true,
 "date_joined": "2026-02-20T14:33:30+05:30"}
```
(Bhupinder Singh — de facto docking approval reviewer, approves all scan exceptions)

```json
{"id": 9, "email": "qc.manager@jivo.in", "full_name": "Quality manager",
 "employee_code": "EP009", "is_active": true, "is_staff": false,
 "date_joined": "2026-02-12T11:24:17+05:30"}
```

```json
{"id": 6, "email": "gateuser@jivo.in", "full_name": "gate",
 "employee_code": "EP006", "is_active": true, "is_staff": true,
 "date_joined": "2026-02-12T11:09:56+05:30"}
```

*Departments from `GET /accounts/departments/`:*

```json
[
  {"id": 1, "name": "IT", "description": "Jivo IT"},
  {"id": 2, "name": "Ecom", "description": ""},
  {"id": 3, "name": "Account", "description": ""},
  {"id": 4, "name": "Store", "description": ""},
  {"id": 5, "name": "Others", "description": ""},
  {"id": 6, "name": "Mess", "description": ""}
]
```

*Current user profile from `GET /accounts/me/`:*

```json
{
  "id": 2, "email": "test@jivo.in", "full_name": "test",
  "employee_code": "EP0002", "is_active": true, "is_staff": true, "is_superuser": true,
  "date_joined": "2026-02-05T15:51:21+05:30",
  "companies": [
    {"company_id": 2, "company_name": "Jivo Mart", "company_code": "JIVO_MART",
     "role": "Employee", "is_default": false, "is_active": true}
  ],
  "permissions": ["accounts.add_department", "accounts.add_user", ... ]
  // 871 permission strings total for this superuser
}
```

**User population breakdown (Jivo Mart, 2026-06-30):**
- Total: 62 users (all active)
- Staff/Django admin: 14 users
- Superuser: 1 (id=2, test/dev account)
- Email domains: 59 × @jivo.in, 2 × @example.com (test accounts), 1 × @gmail.com
- Growth: 17 users in Feb 2026, 6 in Mar, 16 in May, 23 in Jun

**Permission model:** The system uses Django's per-permission model (not Django Groups from the API evidence). A superuser gets all 871 permissions. Regular users have a subset assigned by an admin. Key permission prefixes visible: `accounts`, `barcode`, `docking_admin`, `gate_core`, `grpo`, `notifications`, `production_execution`, `quality_control`, `vehicle_management`, `warehouse`, `wms`, etc. Permissions follow the pattern `<app_label>.<codename>`.

---

### 3.2 Partial Dispatch Approvals (`/admin/docking/partial-dispatch-approvals`)

**Purpose:** Queue for reviewing exception requests where a dispatch was loaded with only a partial barcode scan — i.e., the number of boxes physically scanned is less than the number expected per the SAP invoice. This arises when a vehicle carries a mix of old stock (pre-barcode system) and new barcoded stock. The docking operator raises the request; the admin approves or rejects before the dispatch is marked complete.

**API endpoint:** `GET /docking-admin/partial-scan-requests/`

**Key fields:**

| Field | Type | Description |
|---|---|---|
| `id` | int | Internal request ID |
| `sales_dispatch` | int | FK → SalesDispatch.id (the gate-core DOCK- entry) |
| `entry_no` | string | SalesDispatch entry number (DOCK-YYYYMMDD-NNNN) |
| `vehicle_no` | string | Vehicle registration number |
| `customer_name` | string | Customer for this dispatch |
| `sap_doc_num` | string | SAP invoice number(s), comma-separated if multi-invoice load |
| `document_type` | enum | Document type (always `INVOICE` for Jivo Mart) |
| `dispatch_status` | string | Status of the parent SalesDispatch at time of request |
| `scanned_boxes` | int | Number of boxes that were actually scanned |
| `expected_boxes` | int | Expected box count (0 in current data — field meaning TBD, possibly populated only on rejection) |
| `reason` | text | Free-text justification from the requester |
| `status` | enum | `PENDING` / `APPROVED` / `REJECTED` |
| `requested_by` | int | FK → User.id (docking operator who raised the request) |
| `requested_by_name` | string | Denormalized requester name |
| `requested_at` | datetime | When the request was raised |
| `reviewed_by` | int | FK → User.id (admin who reviewed) |
| `reviewed_by_name` | string | Denormalized reviewer name |
| `reviewed_at` | datetime | When the review was completed |
| `review_notes` | text | Admin's notes (often blank when approved) |
| `created_at` / `updated_at` | datetime | Record timestamps |

**Permissions:**
- `docking_admin.can_request_docking_partial_scan` — raise a request (docking operators)
- `docking_admin.can_approve_docking_partial_scan` — review/approve/reject (admin)
- `docking_admin.can_view_docking_partial_scan` — read-only view

**Real samples from Jivo Mart (pulled 2026-06-30):**

```json
{
  "id": 40, "sales_dispatch": 230,
  "entry_no": "DOCK-20260629-0022",
  "vehicle_no": "HR69E9959",
  "customer_name": "R K WORLDINFOCOM PVT LTD",
  "sap_doc_num": "706260665, 706260666",
  "document_type": "INVOICE", "dispatch_status": "DISPATCHED",
  "scanned_boxes": 4, "expected_boxes": 0,
  "reason": "half box scanned old & half new",
  "status": "APPROVED",
  "requested_by_name": "Raaj", "requested_at": "2026-06-29T20:19:29+05:30",
  "reviewed_by_name": "Bhupinder Singh", "reviewed_at": "2026-06-29T20:20:42+05:30",
  "review_notes": ""
}
```

```json
{
  "id": 6, "sales_dispatch": 78,
  "entry_no": "DOCK-20260623-0004",
  "vehicle_no": "RJ11GD2629",
  "customer_name": "KNOWTABLE ONLINE SERVICES PRIVATE LIMITED",
  "sap_doc_num": "606260142, 606260143, 606260144",
  "scanned_boxes": 1112, "expected_boxes": 0,
  "reason": "MART VEHICLE OLD STICKER HALF NEW",
  "status": "APPROVED",
  "requested_by_name": "Raaj", "reviewed_by_name": "Bhupinder Singh"
}
```

**Operational pattern observed:** The recurring reason across nearly all 21 requests is some variation of "MART VEHICLE half box scanned old & half new". This indicates a systematic inventory transition: Jivo Mart is still working through old stock that was manufactured before the barcode system was deployed. These exceptions are expected to decrease as old stock is depleted.

---

### 3.3 Scan Skip Approvals (`/admin/docking/scan-approvals`)

**Purpose:** Queue for reviewing requests to bypass barcode scanning entirely for a specific dispatch. Distinct from partial scan — here, no scanning was done at all. Typically raised for dispatches where the entire load is old-sticker stock (no barcodes exist on any box).

**API endpoint:** `GET /docking-admin/scan-skip-requests/`

**Key fields:** Same schema as PartialScanRequest, except `scanned_boxes` and `expected_boxes` are absent (scanning was not attempted at all).

| Field | Description |
|---|---|
| `id` | Internal request ID |
| `sales_dispatch` | FK → SalesDispatch.id |
| `entry_no` | DOCK-prefixed SalesDispatch entry no. |
| `vehicle_no` | Vehicle registration number |
| `customer_name` | Customer name |
| `sap_doc_num` | SAP invoice number(s) |
| `document_type` | Always `INVOICE` for Jivo Mart |
| `dispatch_status` | Status of parent dispatch |
| `reason` | Free-text justification (e.g. "old sticker", "mart vehicle") |
| `status` | `PENDING` / `APPROVED` / `REJECTED` |
| `requested_by_name` | Requester name |
| `requested_at` | Request timestamp |
| `reviewed_by_name` | Reviewer name |
| `reviewed_at` | Review timestamp |
| `review_notes` | Admin notes |

**Permissions:**
- `docking_admin.can_request_docking_scan_skip` — raise a request
- `docking_admin.can_approve_docking_scan_skip` — review/approve/reject
- `docking_admin.can_view_docking_scan_skip` — read-only view

**Real samples from Jivo Mart (pulled 2026-06-30):**

```json
{
  "id": 50, "sales_dispatch": 199,
  "entry_no": "DOCK-20260627-0014",
  "vehicle_no": "DL01LAD1397",
  "customer_name": "TOATS PRIVATE LIMITED (AAJCT2944G)",
  "sap_doc_num": "606260182",
  "document_type": "INVOICE", "dispatch_status": "DISPATCHED",
  "reason": "old sticker",
  "status": "APPROVED",
  "requested_by_name": "Shivam", "requested_at": "2026-06-27T19:11:54+05:30",
  "reviewed_by_name": "Bhupinder Singh", "reviewed_at": "2026-06-27T19:13:50+05:30",
  "review_notes": ""
}
```

```json
{
  "id": 39, "sales_dispatch": 72,
  "entry_no": "DOCK-20260620-0003",
  "vehicle_no": "DL01MA6176",
  "customer_name": "JIVO MART PVT LTD - DL",
  "sap_doc_num": "606260150",
  "reason": "mart vehicle",
  "status": "APPROVED",
  "requested_by_name": "Shivam", "reviewed_by_name": "Bhupinder Singh"
}
```

**Operational pattern:** Scan-skip is used specifically for "JIVO MART own vehicles" (the company's own trucks carrying internal transfers or old-sticker stock). The "old sticker" justification accounts for the same pre-barcode inventory transition as partial scans. Requesters are Shivam, Raaj, and Bhupinder Singh himself; reviewer is always Bhupinder Singh.

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Partial Scan Exception Approval Workflow

```
[During Dispatch Loading]
Docking operator notices old-sticker boxes that cannot be scanned
    ↓
Operator raises PartialScanRequest (via Docking module)
    ↓ (permission: can_request_docking_partial_scan)
Status: PENDING → appears in Admin > Docking > Partial Dispatch Approvals queue
    ↓
Admin reviewer opens the request: sees entry_no, vehicle, customer, SAP docs,
    scanned_boxes count, reason text
    ↓
Reviewer APPROVES (or REJECTS) with optional review_notes
    ↓ (permission: can_approve_docking_partial_scan)
Status: APPROVED → dispatch loading can proceed / be committed
Status: REJECTED → dispatch loading is blocked; operator must resolve discrepancy
```

**Observed timing:** Approvals at Jivo Mart happen very quickly — typically 1–5 minutes between `requested_at` and `reviewed_at`. No REJECTED records exist in the current dataset.

### 4.2 Scan Skip Approval Workflow

```
[During Dispatch Loading]
Operator determines the entire vehicle load has no barcodes (all old-sticker stock)
    ↓
Operator raises ScanSkipRequest (via Docking module)
    ↓ (permission: can_request_docking_scan_skip)
Status: PENDING → appears in Admin > Docking > Scan Approvals queue
    ↓
Admin reviewer reviews request: sees entry_no, vehicle, customer, reason
    ↓
Reviewer APPROVES or REJECTS
    ↓ (permission: can_approve_docking_scan_skip)
Status: APPROVED → dispatch proceeds with no barcode scan verification
Status: REJECTED → operator must attempt scanning or raise a different exception
```

### 4.3 User Provisioning Workflow (inferred from permission model)

```
New factory employee onboarded
    ↓
Admin creates user account via /accounts/users/ (can_manage_user)
    ↓
Admin assigns permissions via user detail page (can_manage_user_permissions)
    ↓
Optionally assigns department (can_manage_department)
    ↓
User can log in and access the modules/actions their permissions allow
```

User growth pattern: 17 users added in Feb 2026 (initial system rollout), then incremental additions as more factory roles were activated. 23 users added in June 2026 alone, suggesting rapid expansion.

---

## 5. Cross-section connections (what Admin links to)

| Connection | Direction | Detail |
|---|---|---|
| **Admin → Gate (gate-core)** | via FK | `PartialScanRequest.sales_dispatch` and `ScanSkipRequest.sales_dispatch` both FK to `SalesDispatch.id` (DOCK-prefixed entries in the gate-core section). Admin approval decisions directly control whether a gate-out dispatch is committed. |
| **Admin → All sections (users)** | provides identity | `User.id` (from `/accounts/users/`) is referenced as `created_by`, `submitted_by`, `requested_by`, `reviewed_by`, `dispatched_by`, `scanned_by_name` etc. throughout every section. User records are the identity backbone for audit trails across the entire app. |
| **Admin → Barcode (dispatch sessions)** | via permissions | `docking_admin.can_request_docking_partial_scan` / `can_request_docking_scan_skip` are the permissions that docking operators (in the Barcode/Dispatch section) need to raise scan exceptions. These permissions are set in Admin. |
| **Admin → Notifications** | via permissions | `notifications.can_send_bulk_notification`, `notifications.can_send_notification` etc. are set in Admin; notification preferences (39 event types) are tied to user profiles managed here. |
| **Admin → All sections (access control)** | enforces | Every feature across Gate, QC, GRPO, Barcode, Dispatch, Warehouse, Production, Maintenance is permission-gated using Django permissions assigned to users via this Admin section. |

---

## 6. Data presence for Jivo Mart (live data vs empty, with counts)

| Endpoint | Count | Status | Notes |
|---|---|---|---|
| `GET /accounts/me/` | 1 object | **LIVE** | Authenticated user profile; 871 permissions for superuser; `companies[]` includes JIVO_MART with role=Employee |
| `GET /accounts/users/` | 62 users | **LIVE** | All 62 active; 14 staff users; 59 @jivo.in domain; joined Feb–Jun 2026 |
| `GET /accounts/departments/` | 6 departments | **LIVE** | IT, Ecom, Account, Store, Others, Mess — all minimal metadata |
| `GET /docking-admin/partial-scan-requests/` | 21 records | **LIVE** | All status=APPROVED; all INVOICE type; date range 2026-06-22 to 2026-06-29; 0 PENDING at pull time |
| `GET /docking-admin/scan-skip-requests/` | 12 records | **LIVE** | All status=APPROVED; all INVOICE type; date range 2026-06-16 to 2026-06-27; 0 PENDING at pull time |

**Key observations:**
- Both docking exception queues show 0 PENDING records when filtered by `?status=PENDING`. This means either the app surfaces only resolved records to this (superuser) caller, or all in-flight exceptions are resolved within minutes of creation (consistent with the 1–5 minute approval pattern seen in timestamps).
- The exclusive reviewer for all 33 exception records is **Bhupinder Singh (id=19, bhupinder@jivo.in, EP000)**. Every single partial-scan and scan-skip request in Jivo Mart history has been approved by this one person, making him a critical single point in the exception workflow.
- Common requesters are **Raaj (id=25)** and **Shivam (id=51)** for the docking floor; in earlier records Bhupinder himself was both requester and reviewer (self-approval).
- The dominant recurring reason pattern — "MART VEHICLE half box scanned old & half new" — confirms this is a known, accepted transitional state as Jivo Mart migrates its inventory from pre-barcode to barcoded stock. These approvals are not ad-hoc exceptions but a routine daily operational step.

---
## Reference — UI routes (from bundle)
- `/admin`
- `/admin/docking/partial-dispatch-approvals`
- `/admin/docking/scan-approvals`

## Reference — captured API endpoints + record counts (this section)
- `/accounts/me/` → 1 (object) — authenticated user profile with permissions
- `/accounts/users/` → 62 (list) — all factory users
- `/accounts/departments/` → 6 (list) — department reference (discovered via exploration, not in original scaffold)
- `/docking-admin/partial-scan-requests/` → 21 (list) — all APPROVED
- `/docking-admin/scan-skip-requests/` → 12 (list) — all APPROVED

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
