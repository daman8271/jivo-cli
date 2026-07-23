---
title: "Notifications — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, notifications]
---

# Notifications — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Section documented 2026-06-30. Jivo Mart (JIVO_MART) only.

## 1. Purpose — what this section is for in the factory

The Notifications section is the factory's real-time alert and communication backbone. It serves two functions:

1. **In-app inbox** — a per-user notification centre (accessible from the bell icon in the nav bar) that records every significant event across all factory modules. Each entry carries a deep-link URL so the user can jump straight to the affected record (gate entry, QC inspection, GRPO, dispatch plan, etc.).
2. **Push delivery infrastructure** — Firebase Cloud Messaging (FCM) device tokens are registered per user session so notifications are also delivered as mobile/desktop push alerts. The app registers the token on login and deregisters on logout.

The section covers 39 distinct notification event types spanning the full factory lifecycle: gate entry (vehicle, person, daily needs, maintenance, construction), QC inspection stages, GRPO postings, production run SAP sync, warehouse BOM and FG receipts, dispatch plan lifecycle, intercompany barcode transfers, docking scan-skip approvals, stock level alerts, and general announcements.

All 39 preference types are currently enabled for Jivo Mart. As of 2026-06-30, the authenticated user's inbox (135 records over 2026-06-17 to 2026-06-29) contains only PERSON_ENTRY_* notifications — visitor gate entry/exit events generated at the Front Gate. This means the current user's account is wired primarily to gate operations. The other 37 event types exist in the preferences catalogue but have not produced notifications visible in this account's inbox during the sampled period.

---

## 2. Page tree (page -> subpage -> sub-subpage / wizard steps)

```
/notifications                       Notification Inbox (main page)
/notifications/preferences/          Per-user notification preference toggles

/notifications/send                  Admin: manually compose and send a notification
/notifications/send/                   (same route, trailing-slash variant)

--- API-only endpoints (no dedicated UI page; consumed by the app shell) ---
/notifications/unread-count/         GET: unread badge count for the nav bar
/notifications/mark-read/            POST: mark specific or all notifications as read
/notifications/devices/register/     POST: register FCM token on login
/notifications/devices/unregister/   POST: deregister FCM token on logout
/notifications/test/                 POST: send a test push to one FCM token (dev/admin)
```

### 2.1 Inbox (`/notifications`)

The main notification centre. Displays a reverse-chronological list of all events for the authenticated user. Supports filtering by read/unread status and by notification type. Clicking a notification triggers mark-read and navigates to the `click_action_url` deep-link.

### 2.2 Preferences (`/notifications/preferences/`)

A settings page where each user can toggle which of the 39 event types they want to receive (both in-app and push). Renders as a list of toggles grouped by domain. Supports GET (load current state) and POST (save changes).

### 2.3 Send Notification (`/notifications/send`)

Admin-only page for composing and broadcasting a manual notification. Requires the `notifications.can_send_notification` permission. Used mainly for GENERAL_ANNOUNCEMENT type messages.

### 2.4 Test Push (`/notifications/test/`)

Developer/admin utility to verify FCM push delivery to a specific device token. POST-only; no list view.

---

## 3. Per-page detail

### 3.1 Notification Inbox — `/notifications`

**Purpose:** Shows all in-app notifications generated for the logged-in user across all factory modules.

**API endpoint:** `GET /api/v1/notifications/`

**Query parameters (from OPTIONS inspection):**
- `?is_read=true|false` — filter by read state
- `?type=<NOTIFICATION_CODE>` — filter by event type (e.g. `?type=GRPO_POSTED`)
- `?page=N&page_size=N` — pagination (also accepts `?limit=N&offset=N`)

**Response envelope:**
```json
{
  "results": [...],
  "count": 135,
  "total_count": 135,
  "unread_count": 12,
  "page": 1,
  "page_size": 100,
  "limit": 100,
  "offset": 0
}
```

**Key fields per notification record:**

| Field | Type | Description |
|---|---|---|
| `id` | integer | Notification PK |
| `title` | string | Short display title (e.g. "Person Gate Entry") |
| `body` | string | Full human-readable message |
| `notification_type` | string enum | One of 39 event-type codes (see preferences list) |
| `click_action_url` | string | App-internal deep-link for navigation on click (e.g. `/gate/visitor-labour`) |
| `reference_type` | string | Entity class the notification is about (e.g. `person_entry`, `gate_entry`, `dispatch_plan`) |
| `reference_id` | integer | PK of the referenced entity |
| `is_read` | boolean | Whether the user has read this notification |
| `read_at` | datetime | When it was marked read (null if unread) |
| `extra_data` | object | Domain-specific context dictionary (keys vary per type — see below) |
| `created_at` | datetime | When the event was generated |

**`extra_data` shape for PERSON_ENTRY_CREATED / PERSON_ENTRY_EXITED (observed):**

```json
{
  "name": "Pinu 9953012307",
  "status": "IN",
  "gate_in": "Front gate",
  "vehicle_no": "",
  "person_type": "visitor",
  "reference_id": "212",
  "reference_type": "person_entry"
}
```
For EXITED, also includes `"gate_out": "Front gate"` and `"status": "OUT"`.

**Live Jivo Mart samples (pulled 2026-06-30):**

Record 1 — `PERSON_ENTRY_CREATED` (id 25837):
```json
{
  "id": 25837,
  "title": "Person Gate Entry",
  "body": "visitor Pinu 9953012307 entered via Front gate.",
  "notification_type": "PERSON_ENTRY_CREATED",
  "click_action_url": "/gate/visitor-labour",
  "reference_type": "person_entry",
  "reference_id": 212,
  "is_read": true,
  "read_at": "2026-06-29T14:31:13.853442+05:30",
  "extra_data": {
    "name": "Pinu 9953012307",
    "status": "IN",
    "gate_in": "Front gate",
    "vehicle_no": "",
    "person_type": "visitor",
    "reference_id": "212",
    "reference_type": "person_entry"
  },
  "created_at": "2026-06-29T14:29:47.325380+05:30"
}
```

Record 2 — `PERSON_ENTRY_EXITED` (id 25856):
```json
{
  "id": 25856,
  "title": "Person Gate Exit",
  "body": "visitor Dayalraj 8169505652 exited via Front gate.",
  "notification_type": "PERSON_ENTRY_EXITED",
  "click_action_url": "/gate/visitor-labour",
  "reference_type": "person_entry",
  "reference_id": 210,
  "is_read": true,
  "read_at": "2026-06-29T17:05:38.830635+05:30",
  "extra_data": {
    "name": "Dayalraj 8169505652",
    "status": "OUT",
    "gate_in": "Front gate",
    "gate_out": "Front gate",
    "vehicle_no": "",
    "person_type": "visitor",
    "reference_id": "210",
    "reference_type": "person_entry"
  },
  "created_at": "2026-06-29T14:34:14.386439+05:30"
}
```

**Observation:** All 135 records in the Jivo Mart inbox are visitor person-entry/exit events from the Front Gate. Notification IDs are non-sequential (9234 → 25856), indicating the system is actively generating notifications across many users; this account's inbox reflects only events routed to this user's role/preferences. The ID gap suggests ~16,000+ notifications exist across all users in the system in this period.

---

### 3.2 Notification Preferences — `/notifications/preferences/`

**Purpose:** Per-user settings for which of the 39 event types to receive (in-app and push). All 39 are enabled for the current Jivo Mart account.

**API endpoint:** `GET /api/v1/notifications/preferences/` (list) and `POST /api/v1/notifications/preferences/` (update)

**Key fields:**

| Field | Type | Description |
|---|---|---|
| `id` | integer | Preference entry PK (1–39) |
| `code` | string | Event type code (matches `notification_type` in inbox) |
| `name` | string | Human-readable label |
| `description` | string | Description text (currently mirrors name) |
| `is_enabled` | boolean | Whether this type is toggled on for the user |

**Live Jivo Mart samples (pulled 2026-06-30):**

```json
{"id": 1, "code": "GATE_ENTRY_CREATED", "name": "Gate Entry Created", "description": "Gate Entry Created", "is_enabled": true}
{"id": 7, "code": "QC_INSPECTION_SUBMITTED", "name": "QC Inspection Submitted", "description": "QC Inspection Submitted", "is_enabled": true}
{"id": 22, "code": "GRPO_POSTED", "name": "GRPO Posted to SAP", "description": "GRPO Posted to SAP", "is_enabled": true}
{"id": 32, "code": "DISPATCH_PLAN_BOOKED", "name": "Dispatch Plan Booked", "description": "Dispatch Plan Booked", "is_enabled": true}
{"id": 39, "code": "GENERAL_ANNOUNCEMENT", "name": "General Announcement", "description": "General Announcement", "is_enabled": true}
```

**Complete list of all 39 preference codes:**

| ID | Code | Name |
|---|---|---|
| 1 | GATE_ENTRY_CREATED | Gate Entry Created |
| 2 | GATE_ENTRY_STATUS_CHANGED | Gate Entry Status Changed |
| 3 | SECURITY_CHECK_DONE | Security Check Completed |
| 4 | WEIGHMENT_RECORDED | Weighment Recorded |
| 5 | ARRIVAL_SLIP_SUBMITTED | Arrival Slip Submitted |
| 6 | ARRIVAL_SLIP_SENT_BACK | Arrival Slip Sent Back to Gate |
| 7 | QC_INSPECTION_SUBMITTED | QC Inspection Submitted |
| 8 | QC_CHEMIST_APPROVED | QC Chemist Approved |
| 9 | QC_QAM_APPROVED | QC QAM Approved |
| 10 | QC_REJECTED | QC Rejected |
| 11 | QC_HOLD | QC On Hold |
| 12 | QC_COMPLETED | QC Completed |
| 13 | FACTORY_HEAD_DECISION_REQUIRED | Factory Head Decision Required |
| 14 | FACTORY_HEAD_DECISION_RECORDED | Factory Head Decision Recorded |
| 15 | PO_RECEIVED | PO Items Received |
| 16 | GATE_ENTRY_COMPLETED | Gate Entry Completed |
| 17 | DAILY_NEED_ENTRY_CREATED | Daily Need Gate Entry Created |
| 18 | MAINTENANCE_ENTRY_CREATED | Maintenance Gate Entry Created |
| 19 | CONSTRUCTION_ENTRY_CREATED | Construction Gate Entry Created |
| 20 | PERSON_ENTRY_CREATED | Person Gate Entry Created |
| 21 | PERSON_ENTRY_EXITED | Person Gate Exit Recorded |
| 22 | GRPO_POSTED | GRPO Posted to SAP |
| 23 | GRPO_FAILED | GRPO Posting Failed |
| 24 | SERVICE_GRPO_POSTED | Service GRPO Posted to SAP |
| 25 | SERVICE_GRPO_FAILED | Service GRPO Posting Failed |
| 26 | BOM_REQUEST_CREATED | BOM Request Submitted to Warehouse |
| 27 | BOM_REQUEST_REVIEWED | BOM Request Reviewed |
| 28 | FG_RECEIPT_POSTED | Finished Goods Receipt Posted |
| 29 | FG_RECEIPT_FAILED | Finished Goods Receipt Failed |
| 30 | PRODUCTION_RUN_SAP_POSTED | Production Run Posted to SAP |
| 31 | PRODUCTION_RUN_SAP_FAILED | Production Run SAP Posting Failed |
| 32 | DISPATCH_PLAN_BOOKED | Dispatch Plan Booked |
| 33 | DISPATCH_PLAN_DISPATCHED | Dispatch Plan Dispatched |
| 34 | INTERCOMPANY_TRANSFER_COMPLETED | Intercompany Transfer Completed |
| 35 | INTERCOMPANY_TRANSFER_FAILED | Intercompany Transfer SAP Failed |
| 36 | STOCK_ALERT | Stock Level Alert |
| 37 | DOCKING_SCAN_SKIP_REQUESTED | Docking Scan Skip Requested |
| 38 | DOCKING_SCAN_SKIP_REVIEWED | Docking Scan Skip Reviewed |
| 39 | GENERAL_ANNOUNCEMENT | General Announcement |

---

### 3.3 Mark Read — `/notifications/mark-read/` (action endpoint, no UI page)

**Purpose:** Marks one or more notifications as read for the authenticated user. Updates `is_read` and `read_at` on the selected records. Called by the frontend when a notification is clicked or when "mark all as read" is triggered.

**API:** `POST /api/v1/notifications/mark-read/`
**Body:**
- `{"notification_ids": [25837, 25856]}` — mark specific IDs
- `{}` — mark all as read

No dedicated UI page; this is an action triggered from the inbox page.

---

### 3.4 Device Registration — `/notifications/devices/register/` and `/notifications/devices/unregister/`

**Purpose:** Registers or removes the FCM (Firebase Cloud Messaging) push token for the current user's device/browser session. Called transparently by the app, not user-accessible pages.

**APIs (both POST-only):**
- `POST /api/v1/notifications/devices/register/` — called on successful login; body carries the FCM token
- `POST /api/v1/notifications/devices/unregister/` — called on logout; removes the token so push stops

---

### 3.5 Send Notification — `/notifications/send`

**Purpose:** Admin page for composing and manually dispatching a notification to one or more users (likely for GENERAL_ANNOUNCEMENT type, or emergency alerts).

**API:** `POST /api/v1/notifications/send/`
**Permission required:** `notifications.can_send_notification`

This page is restricted; regular factory users do not see it. Likely used by administrators to push system-wide messages (e.g. shift schedules, emergency gates closure notices).

---

### 3.6 Unread Count — `/notifications/unread-count/` (API widget, no UI page)

**Purpose:** Provides the numeric badge shown on the notification bell icon in the app nav bar.

**API:** `GET /api/v1/notifications/unread-count/`
**Response:** `{"unread_count": N}`

**Live Jivo Mart value (2026-06-30):** `{"unread_count": 12}`

---

### 3.7 Test Push — `/notifications/test/` (admin/dev endpoint)

**Purpose:** Sends a test push notification to a single specified FCM device token. Used by developers or admins to verify push delivery is working for a specific device.

**API:** `POST /api/v1/notifications/test/`
No user-facing UI page; this is a debug/admin utility.

---

## 4. Workflows (multi-step flows + statuses)

The Notifications section is an **event-driven output layer** — it does not initiate its own workflows. Instead, it is the downstream observer of every major factory workflow. The table below maps factory flows to the notification types they emit:

### 4.1 Gate Entry Flow
```
Vehicle/person arrives at factory gate
  → GATE_ENTRY_CREATED (vehicle arrives)
  → PERSON_ENTRY_CREATED (visitor/labour enters)
  → SECURITY_CHECK_DONE (security officer completes check)
  → WEIGHMENT_RECORDED (vehicle weighed)
  → GATE_ENTRY_STATUS_CHANGED (status updates during processing)
  → GATE_ENTRY_COMPLETED (vehicle/person fully processed)
  → PERSON_ENTRY_EXITED (visitor exits)
  → DAILY_NEED_ENTRY_CREATED (daily consumables arrive)
  → MAINTENANCE_ENTRY_CREATED (maintenance vendor arrives)
  → CONSTRUCTION_ENTRY_CREATED (construction crew arrives)
```

### 4.2 QC Inspection Flow
```
Material arrives → arrival slip created
  → ARRIVAL_SLIP_SUBMITTED (gate submits slip to QC)
  → ARRIVAL_SLIP_SENT_BACK (QC returns slip to gate for correction)
  → QC_INSPECTION_SUBMITTED (chemist starts inspection)
  → QC_CHEMIST_APPROVED (chemist approves material)
  → QC_QAM_APPROVED (QAM approves material)
  → FACTORY_HEAD_DECISION_REQUIRED (escalation needed)
  → FACTORY_HEAD_DECISION_RECORDED (factory head decides)
  → QC_COMPLETED | QC_REJECTED | QC_HOLD (final outcome)
  → PO_RECEIVED (PO items formally received post-QC)
```

### 4.3 GRPO Posting Flow
```
QC approved → GRPO created and posted to SAP
  → GRPO_POSTED (material GRPO success)
  → GRPO_FAILED (SAP posting error)
  → SERVICE_GRPO_POSTED (freight/service GRPO for dispatch)
  → SERVICE_GRPO_FAILED (SAP error on service GRPO)
```

### 4.4 Production & Warehouse Flow
```
Production order runs → SAP sync
  → PRODUCTION_RUN_SAP_POSTED | PRODUCTION_RUN_SAP_FAILED
  → BOM_REQUEST_CREATED (warehouse raw material request)
  → BOM_REQUEST_REVIEWED (warehouse confirms/rejects)
  → FG_RECEIPT_POSTED | FG_RECEIPT_FAILED (FG back into warehouse)
  → STOCK_ALERT (stock falls below threshold)
```

### 4.5 Dispatch Flow
```
Dispatch plan created → vehicle docked → scanned → dispatched
  → DISPATCH_PLAN_BOOKED (plan confirmed)
  → DOCKING_SCAN_SKIP_REQUESTED (operator requests skip approval)
  → DOCKING_SCAN_SKIP_REVIEWED (admin approves/rejects skip)
  → DISPATCH_PLAN_DISPATCHED (vehicle departed)
```

### 4.6 Intercompany Transfer Flow
```
Barcode transfer between companies (JIVO_MART ↔ JIVO_OIL ↔ JIVO_BEVERAGES)
  → INTERCOMPANY_TRANSFER_COMPLETED (SAP transfer success)
  → INTERCOMPANY_TRANSFER_FAILED (SAP error)
```

### 4.7 Read State Lifecycle
```
Notification created (is_read=false)
  → User views notification OR clicks "mark all read"
  → POST /notifications/mark-read/
  → is_read=true, read_at=<timestamp>
```

---

## 5. Cross-section connections (what this links to)

The Notifications section is a **read-only mirror** of every other section's state changes. Connections are one-directional: other sections emit events; notifications consume them and route users back via `click_action_url`.

| Notification group | Connected factory section | Click-action destination |
|---|---|---|
| GATE_ENTRY_*, SECURITY_CHECK_DONE, WEIGHMENT_RECORDED | Gate Core (vehicle arrivals, gate-ins/outs) | `/gate/...` |
| PERSON_ENTRY_CREATED, PERSON_ENTRY_EXITED | Gate — Visitor/Labour register | `/gate/visitor-labour` |
| DAILY_NEED_ENTRY_CREATED | Daily Needs Gate Entry | `/gate/daily-needs` |
| MAINTENANCE_ENTRY_CREATED, CONSTRUCTION_ENTRY_CREATED | Gate — Maintenance/Construction entries | `/gate/...` |
| ARRIVAL_SLIP_*, QC_*, FACTORY_HEAD_DECISION_* | Quality Control (ArrivalSlip, Inspection) | `/quality-control/...` |
| PO_RECEIVED | Procurement (Purchase Orders) | `/po/...` |
| GRPO_POSTED, GRPO_FAILED | GRPO module | `/grpo/...` |
| SERVICE_GRPO_POSTED, SERVICE_GRPO_FAILED | GRPO service entries | `/grpo/service/...` |
| BOM_REQUEST_CREATED, BOM_REQUEST_REVIEWED | Warehouse (BOM requests) | `/warehouse/...` |
| FG_RECEIPT_POSTED, FG_RECEIPT_FAILED | Warehouse (FG receipts) | `/warehouse/...` |
| PRODUCTION_RUN_SAP_POSTED, PRODUCTION_RUN_SAP_FAILED | Production Execution | `/production/...` |
| DISPATCH_PLAN_BOOKED, DISPATCH_PLAN_DISPATCHED | Dispatch Plans / Gate Out | `/dispatch-plans/...` |
| DOCKING_SCAN_SKIP_REQUESTED, DOCKING_SCAN_SKIP_REVIEWED | Docking Admin (scan-skip requests) | `/docking-admin/...` |
| INTERCOMPANY_TRANSFER_COMPLETED, INTERCOMPANY_TRANSFER_FAILED | Barcode (Intercompany transfers) | `/barcode/intercompany/...` |
| STOCK_ALERT | Dashboards (stock monitoring) | `/dashboards/stock/...` |
| GENERAL_ANNOUNCEMENT | System-wide (admin broadcast) | (varies) |

**Push infrastructure link:** The `/notifications/devices/register/` and `/notifications/devices/unregister/` endpoints connect to Firebase Cloud Messaging (FCM) outside the factory API. The app frontend handles the FCM SDK token lifecycle; the factory API only stores and deregisters these tokens.

**Nav bar link:** The unread badge in the top navigation shell polls `/notifications/unread-count/` to display the live unread count bubble.

---

## 6. Data presence for Jivo Mart (which pages have live data vs empty, with counts)

| Endpoint | Status | Count | Notes |
|---|---|---|---|
| `GET /notifications/` | LIVE | 135 records (2 pages) | All PERSON_ENTRY_CREATED (67) and PERSON_ENTRY_EXITED (68); all marked read; date range 2026-06-17 to 2026-06-29 |
| `GET /notifications/preferences/` | LIVE | 39 records | All 39 notification types present; all `is_enabled: true`; no per-type customisation |
| `GET /notifications/unread-count/` | LIVE | 1 object | Returns `{"unread_count": 12}` at time of sampling |
| `POST /notifications/mark-read/` | Functional (POST-only) | N/A | No GET; write endpoint, not sampled |
| `POST /notifications/devices/register/` | Functional (POST-only) | N/A | Called on login; no GET |
| `POST /notifications/devices/unregister/` | Functional (POST-only) | N/A | Called on logout; no GET |
| `POST /notifications/send/` | Functional (POST-only, admin) | N/A | Requires `notifications.can_send_notification`; not sampled |
| `POST /notifications/test/` | Functional (POST-only, admin) | N/A | Dev/admin FCM test; not sampled |

**Notification type coverage for this account:**
- **Active in inbox:** PERSON_ENTRY_CREATED, PERSON_ENTRY_EXITED (2 of 39 types, 100% of inbox records)
- **Zero records in inbox:** The remaining 37 types (GATE_ENTRY_*, QC_*, GRPO_*, DISPATCH_*, PRODUCTION_*, BOM_*, FG_*, INTERCOMPANY_*, STOCK_ALERT, DOCKING_SCAN_SKIP_*, GENERAL_ANNOUNCEMENT) — these event types are enabled in preferences but have not fired for this user during the sampled period. The most likely explanation is that this API access account/user is a gate-operations role that only receives person-entry notifications.

**Unread count discrepancy note:** The paginated list metadata reports `unread_count: 12` even though `?is_read=false` returns 0 records. This suggests the 12 unread notifications are either on a different page than the 135 records returned, or belong to a slightly different scope. The live `/notifications/unread-count/` endpoint confirms `12`.

---

## Reference — UI routes (from bundle)
- `/notifications`
- `/notifications/`
- `/notifications/devices/register/`
- `/notifications/devices/unregister/`
- `/notifications/mark-read/`
- `/notifications/preferences/`
- `/notifications/send`
- `/notifications/send/`
- `/notifications/test/`
- `/notifications/unread-count/`

## Reference — captured API endpoints + record counts (this section)
- `/notifications/` -> 135 (paginated_list)
- `/notifications/preferences/` -> 39 (list)
- `/notifications/unread-count/` -> 1 (object)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
