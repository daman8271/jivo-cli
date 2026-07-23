---
title: Appointments
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Appointments

The **Appointments** section (SPA route `/app/appointments`, page-title enum `Jr.PO_SCHEDULING`) is the **inbound delivery-appointment scheduling** surface. After Blinkit raises a PO ([[PO-Summary]]), JIVO (Jivo Wellness Pvt. Ltd., `x-entity-id=1117`, `x-entity-type=manufacturer`) must book a **delivery slot** at the destination facility/warehouse before dispatching goods. This section lists every appointment, shows its slot + status, and drives the schedule → reschedule → cancel lifecycle, plus courier/tracking capture, invoice attachment, PO **clubbing/merging** (multiple POs into one appointment), the appointment **QR pass / letter** (downloadable + sendable via WhatsApp/email), and a bulk-upload path. Internally the whole feature is branded **"PO Scheduling"** (every analytics event is `PO_SCHEDULING_*`); "Appointments" is the user-facing label.

Unlike [[Assortment]], this section's page code **was captured** — it lives in the code-split chunk `captures/partner/js/useFirebasePageTracking-CGSyAZ_Q.js` (the barrel that also carries the Orders/PO page). All endpoints, columns, filters, status enums and field names below are extracted from that chunk (API-constant + `doHttpGet`/`doHttpPost`/`doHttpPut` bindings), **not** from a live network trace, except where noted. All calls hit `hostUrl.VendorConsoleEndpoint` (= `https://www.partnersbiz.com/`) under the **`vendor_appointment/api/v1|v2/`** microservice prefix, with the standard header-token auth from the atlas.

## Subpages & tabs

**List page** — `/app/appointments` (component `ye` shares the list; the scheduled-detail component is `Vt`)
- The appointments grid (event `PO_SCHEDULING_APPOINTMENTS_LIST_VIEWED` / `PO_SCHEDULING_PO_LIST_VIEWED`).
- **Aggregated stat cards** from `appointment-stats/` — counters `pending_count`, `upcoming_count`, `fulfilled` (event `PO_SCHEDULING_CARD_FILTER_CLICKED`; card filter labels seen: **Pending**, **Upcoming**, **Cancel**).
- **List filter tabs** keyed `all` / `today` / `upcoming` (labels **All / Past / Upcoming / Pending**).
- **Add PO** entry to start scheduling (`PO_SCHEDULING_ADD_PO_CLICKED` → Add-PO modal).
- Per-row **Appointment ID** click (`PO_SCHEDULING_APPOINTMENT_ID_CLICKED`) → scheduled detail.

**Scheduling form** (a 2-step wizard, `SchedulingStep` enum = `1 PO_SELECT` → `2 SLOT_SELECT`), reached at:
- `/app/appointments/schedule/:id` — book a new appointment for a PO (component `ye`).
- `/app/appointments/reschedule/:id` — move an existing appointment to a new slot (`PO_SCHEDULING_RESCHEDULE_BUTTON_CLICKED`, `..._RESCHEDULE_SUCCESSFUL`).
- `/app/appointments/edit/:id` — edit appointment details (courier/invoice/tracking).
- `/app/appointments/scheduled/:id` — **read-only** view of a scheduled appointment (component `Vt`); shows slot, QR/letter, PO clubbing, invoices.

Wizard sub-flows visible in events: choose **available slot** (`PO_SCHEDULING_AVAILABLE_SLOTS_FOR_PO`, `..._DATE_CHANGE_CLICKED`), **club/merge POs** (`..._APPOINTMENT_MERGING_CONFIRMED`, `..._CLUBBING_CHARGES_ACCEPTED/NOT_ACCEPTED`, `..._CHARGES_ACCEPTED`), **courier details** (`..._COURIER_PARTNER_DROPDOWN_CLICKED/SELECTED`, `..._COURIER_TRACKING_NUMBER_ENTERED`, `..._COURIER_DETAILS_VALIDATION_SUCCESS/FAILED`, `..._ADD_MORE_TRACKING_DETAILS_CLICKED`), **add/delete invoice** (`..._ADD_INVOICE_OPEN`, `..._DELETE_INVOICE_CLICKED`), and the **appointment letter** (`..._DOWNLOAD_QR_CLICKED`, `..._DOWNLOAD_QR_APPOINTMENT_LETTER_*`, `..._SEND_APPOINTMENT_LETTER_VIA_WHATSAPP_*`, `..._SEND_APPOINTMENT_LETTER_VIA_EMAIL_*`).

## Filters & columns (what the table shows)

**List filters** (query keys observed on the `appointments/` list call): date range on `issue_date` (`issue_date__date__gte` / `issue_date__date__lte`, also `issue_date__gte/__lte`), `expiry_date__gte`, `facility_name__in`, `po_number__in`, plus tracking-number search (`tracking_number_regex`, `tracking_numbers_csv`). Tab keys `all` / `today` / `upcoming`.

**Appointment status** (`AppointmentStatus` enum): `UNSCHEDULED` (blue) · `SCHEDULED` (green) · `FULFILLED` (blue) · `NO_SHOW` (red) · `CANCELLED` (red). (Distinct from the richer PO `po_state` set in [[PO-Summary]].)

**Columns / fields seen** (list grid + PO-picker + scheduled-detail cards):
- **Appointment ID** (`appointment_id`)
- **PO Number** (`po_number` / `po_numbers` when clubbed) — the PO-picker grid inside the wizard shows: **PO No.**, **Delivery Type** (`is_courier_unloading` → "Courier Vendor" / "Self"), **Issue Date**, **Total Quantity** (`total_units_ordered`), **Total SKUs** (`item_count_ordered`), **PO Expiry Date**.
- **Facility** (`facility_name`) · **City** (`city_name`)
- **Slot Time** (`slot_time`, from `slot_date` + `slot_start_time`/`slot_end_time`) · **Date & Time**
- **Current Status** (`appointment_state`)
- **Estimated Date of Delivery** (`estimated_delivery_date` / `estimated_delivery_time`)
- **Tracking** / **LR/AWB number** (`tracking_number`), **Courier** (`courier_partner_name` / `courier_partner_id`, `courier_unloading`)
- **PO Clubbing Charges** / **Charge ID** / **Total Cost** / **Total Amount** (merge-fee preview)
- **Reason** (cancellation reason)
- Invoice sub-table: **Invoice ID / Number / Amount / Value / Status**
- GRN sub-fields (shared with PO detail): `grn_amount`, `grn_date`, `grn_qty`, `grn_items` (**GRN Amount / GRN Date / GRN Qty / GRN Value/Qty / GRN Landing Price**)
- Appointment pass artifacts: `appointment_pass`, `appointment_qr`

## API endpoints

Base = `https://www.partnersbiz.com/` + path. Service prefix = `vendor_appointment/api/`. Verb column: `doHttpGet`/`doHttpPost`/`doHttpPut` = confirmed binding in the chunk; "to confirm" = constant present but the exact method is added at a runtime call site not directly matched (these three share the `v2/appointment/` base and are dispatched by method).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `vendor_appointment/api/v1/appointment-stats/` | Aggregated stat cards (`pending_count`, `upcoming_count`, `fulfilled`) — `GET_APPOINTMENT_AGGREGATED_DATA` | READ |
| POST | `vendor_appointment/api/v1/appointments/` | **Appointments list grid** (POST carries the filter body; server-paginated) — `GET_APPOINTMENTS` | READ |
| GET | `vendor_appointment/api/v1/appointments/fetch-cancel/` | Cancellation count / cancellability info for the current selection — `APPOINTMENT_CANCELATION_COUNT` | READ |
| GET | `vendor_appointment/api/v1/courier-partner-details/` | Courier-partner options (dropdown) — `FETCH_APPOINTMENT_COURIER_OPTIONS` | READ |
| POST | `vendor_appointment/api/v1/invoice/fetch-invoice/` | Fetch invoices tied to the selected PO(s) — `FETCH_INVOICES_FOR_POS` | READ |
| GET | `vendor_appointment/api/v1/bulk-upload/sample-file` | Download the bulk-upload sample template — `DOWNLOAD_SAMPLE_BULK_UPLOAD_TEMPLATE` | READ (file) |
| POST | `vendor_appointment/api/v2/slots/available/` | **Available delivery slots** for the chosen PO(s) — `GET_SLOTS_V2` (POST body = PO ids) | READ |
| POST | `vendor_appointment/api/v2/appointment/get-existing-appointments/` | Existing appointments to club/merge a new PO into — `GET_EXISTING_APPOINTMENTS_V2` | READ |
| GET | `vendor_appointment/api/v2/appointment/clubbing-charges/` | Preview PO-clubbing / merge charges (`EXISTING_APPOINTMENT_ISSUE_DATE_DIFFERENT_V2`) | READ |
| GET (to confirm) | `vendor_appointment/api/v2/appointment/` | Download the **appointment QR letter / pass** — `DOWNLOAD_APPOINTMENT_QR` (shares base path; method dispatched at runtime) | READ (file) |

Related endpoints used by the scheduling wizard but owned by the PO service (`v1/…`, documented in [[PO-Summary]]): `v1/client-po-details/` (PO picker list), `v1/client-po-details/distinct_values/city_name/` + `…/facility_name/` (filter dropdowns), `v1/get-grn-details/`, `v1/invoice/grn-details/`.

**Out of scope (writes) — never expose in a read-only CLI, never exercised here:**
- `POST vendor_appointment/api/v2/appointments/create/` — **schedule** a new appointment (`CREATE_APPOINTMENTS_V2`). WRITE.
- `PUT vendor_appointment/api/v2/appointments/` — **reschedule / edit** an appointment (`UPDATE_APPOINTMENTS_V2`, `doHttpPut` confirmed). WRITE.
- `POST vendor_appointment/api/v2/appointments/cancel/` — **cancel** an appointment (`APPOINTMENT_CANCELATION_V2`). WRITE.
- `vendor_appointment/api/v2/appointment/` — **release excess quantity** (`RELEASE_EXCESS_QUANTITY_ENDPOINT`). WRITE.
- `vendor_appointment/api/v2/appointment/` — **send appointment pass / letter** via WhatsApp/email (`SEND_APPOINTMENT_PASS`). WRITE / side-effecting action.
- `POST vendor_appointment/api/v1/bulk-upload-request/` — **bulk-upload** appointments (`BULK_VARIANT_CREATION_UPLOAD`). WRITE.
- `POST vendor_appointment/api/v1/courier-partner/validate/` — **validate** a courier tracking number (`COURIER_PARTNER_TRACKING_NUMBER_VALIDATE_ENDPOINT`; part of the write flow). Action.
- `POST vendor_appointment/api/v1/invoice/upload-s3-resource/` — presigned-URL mint to **upload** invoice documents (`GET_PRESIGNED_URLS`; write flow). WRITE-adjacent.

## Real data seen (evidence)

- **Route + feature confirmed** live and code-complete: the four `appointments/{schedule,reschedule,edit,scheduled}/:id` routes are registered in `routes.js` / `AuthenticatedRoutes` chunk, and `/appointments` is enum-backed (`case"appointments":return Jr.PO_SCHEDULING`). Help/Support pre-files tickets on this route under category `"appointment"` / ticketFilter `"APPOINTMENT"` (a **dedicated** filter, unlike [[Assortment]]'s generic one).
- **~30 `PO_SCHEDULING_*` analytics events** enumerate every action (list-viewed, add-PO, slot-select, date-change, clubbing/merging confirm, charges accept/reject, courier select + validate, add/delete invoice, download QR, send letter via WhatsApp/email, reschedule, cancel success/fail, update fail). These are the ground truth for the read vs write split above.
- **Empty-state assets** shipped: `/assets/no_appointment-VkxtGTxJ.svg`, `/assets/schedule-error-BgHhvm_K.svg`, plus list CSS hooks `slot-appointments-container` / `slot-appointments-date-header` / `slot-appointments-list` and card class `body-card-po-state--scheduled`.
- **No live appointment rows captured.** The two files under `captures/partner/api/` (`appointment-stats.json`, `profile-user.json`) are **just the SPA HTML shell** (1 KB `<!DOCTYPE html>`), not real API responses — so counts/slots for entity 1117 are **not yet observed**. Real values require a read-only live capture of `appointment-stats/` and `appointments/`.
- **Not in blinkit-cli.** `ecomcliauto/clis/blinkit-cli` (report-requests + Sales + SOH + Bulk PO/GRN + Brand Fund + Ads) has **no** appointment command and never hit `vendor_appointment/*`; the `SESSION-LOG-2026-07-20` shows `appointment_date` only as a **column of the PO header export**, not the scheduling service.

## What a READ-ONLY CLI would expose (candidate commands)

All read-only, all against the `vendor_appointment/api/` reads confirmed above:

- `appointments stats` → `GET v1/appointment-stats/` — the Pending / Upcoming / Fulfilled counters.
- `appointments list [--tab all|today|upcoming] [--facility <name>] [--po <n>] [--from DD-MM-YYYY] [--to DD-MM-YYYY] [--json]` → `POST v1/appointments/` with a filter body — the appointment grid (id, PO(s), facility, slot, status, courier/tracking, EDD).
- `appointments show <appointment_id>` → compose from the list + `POST v1/invoice/fetch-invoice/` (invoices) + GRN reads — mirrors the `/scheduled/:id` read-only view.
- `appointments slots --po <n>[,<n>…]` → `POST v2/slots/available/` — inspect available delivery slots for PO(s) **without booking**.
- `appointments couriers` → `GET v1/courier-partner-details/` — list courier-partner options.
- `appointments cancel-info --po <n>` → `GET v1/appointments/fetch-cancel/` — read cancellability/count (does **not** cancel).
- `appointments merge-preview --po <n> --into <appointment_id>` → `GET v2/appointment/clubbing-charges/` + `POST v2/appointment/get-existing-appointments/` — preview club/merge charges only.
- `appointments qr <appointment_id>` → `GET v2/appointment/` (download the QR/letter file) — read-only artifact fetch.
- `appointments sample-template` → `GET v1/bulk-upload/sample-file` — grab the bulk template (no upload).

Explicitly **excluded** (writes): any `schedule` / `reschedule` / `cancel` / `edit` / `release-excess` / `send-letter` / `bulk-upload` / `validate-tracking` command — these are `create` / `PUT` / `cancel` / upload verbs and are OUT-OF-SCOPE for a read-only study.

## Connections

- Portal shell & nav: [[Partner-Hub]] · index: [[00-Blinkit-Atlas]]
- Directly downstream of [[PO-Summary]] — a PO is handed into this flow to book its inbound slot (the PO-picker grid and `client-po-details` reads are shared).
- Feeds / cross-references [[Invoices]] (invoices attached to an appointment) and GRN data ([[Stock-on-Hand]] context; `get-grn-details` shared).
- Async-export sibling pattern lives in [[Report-Requests]] (this section instead uses its own `vendor_appointment` bulk-upload/sample-file rather than the shared report queue).
