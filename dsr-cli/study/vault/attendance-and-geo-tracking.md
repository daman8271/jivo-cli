# Attendance & Geo-Tracking

## 1. Overview
This subsystem is how the JIVO DSR app proves that field staff (Sales Officers / Promoters) actually showed up and walked their beats. Every field person's Android app punches **GPS-stamped attendance** (day-start / EOD), streams a continuous **breadcrumb trail** of location pings through the day, and files a **selfie "message"** to their manager. Back-office staff can override/audit the raw punches, and every override is logged. Supporting tables map each user to their phone (push notifications, device-change detection) and carry simple manager<->field two-way messages. It is the accountability and anti-fraud backbone under the sales-productivity data.

## 2. Tables

### tbl_geoLocation — 27,025,798 rows — PK `id`
The continuous GPS breadcrumb trail (by far the largest table; a ping roughly every couple of minutes per active person). One row per location fix.
- `personId` — the field person (-> tbl_salesperson.personId). `salesId` — optional link to a secondary-sales visit event (mostly null). `retailerId` — retailer being visited if the ping was tied to a shop (mostly null).
- `latitude` / `longitude` — stored as text; `location` — reverse-geocoded address string.
- `battery` — % battery, `GpsEnabled` — "true"/"false", `provider` — "gps"/"network", `accuracy` (m), `speed` (m/s), `altitude` (m).
- `timeStamp` — exact fix time (UTC in samples); `createdOn` — date (server insert day).
- Note: sibling `tbl_geoLocationOld` exists but is empty (0 rows) — an archived/rotated copy.

### tbl_salesPersonAttendance — 426,001 rows — PK `id`
The actual attendance punches (day-start / end-of-day). One row per punch event.
- `personId` — field person (-> tbl_salesperson.personId). `timeStamp` — punch time.
- `status` — punch type; observed value **"EOD"** = end-of-day check-out (day-start punches carry the opening status).
- `latitude`/`longitude` — where the punch happened; `address` — resolved address (often null).
- `imagePath` — attendance selfie filename (e.g. `873-28-5-2024-1919.jpg`); empty when no photo.
- `accuracy` — GPS accuracy (text), `retailerId` — shop if punched at a retailer (usually null), `simNo` — device SIM (usually null).

### tbl_messagesFromAndroid — 151,141 rows — PK `id`
Field-to-manager uplink messages, dominated by **"Selfie"** attendance photos pushed from the app. One row per (message x recipient) — the same selfie fans out to several managers (note identical `imagePath`/`timeStamp` across the 3 sample rows with different `toId`).
- `fromId`/`fromName` — sender field person (-> tbl_salesperson.personId). `toId`/`toName` — recipient manager.
- `subject` — "Selfie" etc.; `body` — free text; `imagePath` — photo file.
- `latitude`/`longitude`/`GpsEnabled`/`accuracy`/`provider` — capture location; `address`, `distance` (from expected point), `simno`, `salesId`.
- `readMessage` — 0=unread / 1=read; `timeStamp` — sent time.

### tbl_AttendanceAudit — 34,811 rows — PK `id`
Back-office reconciled / manual attendance register (half-day granular). One row per person per date.
- `personid` — field person (-> tbl_salesperson.personId). `date` — attendance day.
- `presentFirstHalf` / `presentSecondHalf` — per-half code: **"A"=Absent, "P"=Present** (also H/half, WO/week-off patterns typical). `status` — day roll-up (e.g. "A"=Absent).
- `comment` — reviewer note; `modifiedBy` (-> tbl_salesperson.personId of reviewer) / `modifiedDate` — who last edited (null = never touched since auto-insert).

### deviceTracker — 18,778 rows — PK `Id`
Detects when a field person swaps phones (anti-fraud: sharing/lending a login). One row per device-name change.
- `SalesPersonId` — field person (-> tbl_salesperson.personId). `OldDeviceName` -> `DeviceName` — device model before/after (e.g. `whyred` -> `xiaomi`).
- `createdDate` — when the change was seen; `Status` — bit flag (0/false = observed/unacknowledged in samples).

### tbl_userGcmMap — 4,334 rows — PK `id`
Maps each user to their phone for **push notifications** (GCM/FCM). One row per (user, device) registration.
- `userId` — the app user (-> tbl_salesperson.personId). `gcmId` — FCM push token (often blank). `androidId` — hardware Android ID. `device` — model string (e.g. "realme RMX2061"). `timeStamp` — registration time.

### tbl_androidMessage — 36 rows — PK `id`
Manager-to-device **command/notification** downlink (small control table). One row per command.
- `senderId` — manager (-> tbl_salesperson.personId). `receiverId`/`receiverName` — target field person. `message` — command text, observed **"location"** = remote "fetch current location" ping request. `received` — 0/1 delivery ack; `timeStamp`.

### tbl_attendanceLog — 1 row — PK `Id`
Audit trail of edits/deletes on attendance punches (recently added — only 1 row so far). One row per change action.
- `attendanceId` — the tbl_salesPersonAttendance row affected. `personId`/`personName` — whose attendance. `action` — e.g. "Deleted". `oldStatus`->`newStatus` — e.g. "EOD"->null. `changedBy`/`changedByName` — the back-office user who did it (-> tbl_salesperson.personId). `changedOn`, `reason`.

## 3. Linkages
- **person**: `personId` / `personid` / `salesPersonId` / `SalesPersonId` / `userId` / `fromId` / `senderId` / `changedBy` / `modifiedBy` -> `tbl_salesperson.personId`. Message recipients `toId` / `receiverId` and `senderId`/`fromId` are also salespersons (managers are salesperson rows).
- **retailer**: `retailerId` (geoLocation, salesPersonAttendance) -> `tbl_retailers.retailerId`.
- **secondary-sales visit**: `salesId` (geoLocation, messagesFromAndroid) -> a secondary-sales/visit event row (link into the sales subsystem).
- **attendance edit chain**: `tbl_attendanceLog.attendanceId` -> `tbl_salesPersonAttendance.id`.
- **daily/monthly rollup**: `tbl_AttendanceAudit` keys on `personid` + `date`; joins to monthly target/attendance rows on personId + month/year.
- No `beatId`/`itemId` columns here — this subsystem is person- and location-centric; beat/product context is inferred via the sales/visit tables through `salesId`.

## 4. Portal mapping
- **Attendance report / register** page — `tbl_salesPersonAttendance` (punches + selfie), `tbl_AttendanceAudit` (P/A half-day register), edits surfaced via `tbl_attendanceLog`.
- **Live location / person-tracking map** ("Track Employee" / "Where is my SO") — `tbl_geoLocation` breadcrumb trail; on-demand pull via `tbl_androidMessage` ("location" command).
- **Selfie / field-message inbox** for managers — `tbl_messagesFromAndroid`.
- **Device-change / fraud monitor** admin page — `deviceTracker`.
- **Push-notification plumbing** (no dedicated page) — `tbl_userGcmMap`.

## 5. Proposed dsr commands

```
dsr attendance --from <d> --to <d> [--salesperson <id>]
```
Purpose: list attendance punches for a person / date range.
```sql
SELECT id, personId, timeStamp, status, latitude, longitude, imagePath, retailerId
FROM tbl_salesPersonAttendance
WHERE timeStamp >= @from AND timeStamp < @to
  AND (@personId IS NULL OR personId = @personId)
ORDER BY timeStamp;
-- no soft-delete col; deletions are recorded in tbl_attendanceLog (action='Deleted').
```

```
dsr attendance-register --from <d> --to <d> [--salesperson <id>]
```
Purpose: half-day present/absent register (P/A) with reviewer notes.
```sql
SELECT personid, date, presentFirstHalf, presentSecondHalf, status, comment, modifiedBy, modifiedDate
FROM tbl_AttendanceAudit
WHERE date >= @from AND date < @to
  AND (@personId IS NULL OR personid = @personId)
ORDER BY personid, date;
-- decode: 'P'=Present, 'A'=Absent per half. date is DATE; watch 1899-12-30 sentinel if present.
```

```
dsr track --salesperson <id> --from <d> --to <d> [--limit N]
```
Purpose: replay a person's GPS breadcrumb trail for a day (path on a map / distance).
```sql
SELECT id, personId, timeStamp, latitude, longitude, location, accuracy, speed, battery, GpsEnabled
FROM tbl_geoLocation
WHERE personId = @personId
  AND timeStamp >= @from AND timeStamp < @to
ORDER BY timeStamp;
-- table is ~27M rows: always constrain by personId + timeStamp. Filter GpsEnabled='true' for clean fixes.
```

```
dsr selfies --from <d> --to <d> [--salesperson <id>]
```
Purpose: attendance/visit selfies pushed from the field, with capture location.
```sql
SELECT id, fromId, fromName, subject, imagePath, latitude, longitude, distance, address, timeStamp, readMessage
FROM tbl_messagesFromAndroid
WHERE timeStamp >= @from AND timeStamp < @to
  AND (@personId IS NULL OR fromId = @personId)
ORDER BY timeStamp;
-- one physical selfie fans out to multiple managers (multiple toId rows); dedupe on imagePath+fromId+timeStamp for unique photos.
```

```
dsr device-changes [--from <d> --to <d>] [--salesperson <id>]
```
Purpose: flag field staff who swapped phones (login-sharing / fraud check).
```sql
SELECT Id, SalesPersonId, OldDeviceName, DeviceName, createdDate, Status
FROM deviceTracker
WHERE (@personId IS NULL OR SalesPersonId = @personId)
  AND (@from IS NULL OR createdDate >= @from)
  AND (@to   IS NULL OR createdDate <  @to)
ORDER BY createdDate DESC;
```
