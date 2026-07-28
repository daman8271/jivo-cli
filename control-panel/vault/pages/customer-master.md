---
title: Customer Master
route: /realise/customer-master/
type: page
endpoints: [customer-master]
tags: [jivo, control-panel, masterdata]
---
# Customer Master

## Purpose
The single searchable directory of **every JIVO customer** (1,167 parties as sampled). A JIVO ops / sales / accounts user comes here to look up a customer's contact details, tax identity (GSTIN / PAN), billing address, mapped sales person, payment terms, sanctioned credit limit and current ledger balance — and to slice that list by state, business group or account status, or export the whole thing to Excel. It is a **read-only master-data view** (no add/edit on this page); it is the reference table the transactional Realise / Accounts reports join against by customer `code`.

Sidebar location: **Reports → Master Data → Customer Master** (the only entry under Master Data). Route is under the `/realise/` app even though it is grouped as Master Data.

## What it shows
- **Header** — title + one-line description ("Every customer with the details that matter…").
- **4 KPI cards** (computed client-side over the whole master, not the filtered view):
  - **Customers** — total row count (`rows.length`).
  - **With GSTIN** — count of rows having a `gstin`, plus % registered (~75% in sample).
  - **Active** — count where `status === 'Active'` (i.e. not Frozen / Inactive).
  - **States** — number of distinct non-empty `state` values (geographic spread; 28 in sample).
- **Filter bar** (all client-side over the already-loaded rows):
  - **Search** — free text matched against name, code, GSTIN, PAN, mobile, city, state, contact person, email, sales person (debounced 120 ms).
  - **State** — dropdown auto-populated from distinct `state` values.
  - **Main Group** — dropdown auto-populated from distinct `main_group` values.
  - **Status** — All / Active / Frozen / Inactive (the UI offers Inactive as a filter even though the live feed only returned Active + Frozen).
  - **Export Excel** — anchor link to `/realise/customer-master/export/` (server-side XLSX; EXPORT — not probed, see Notes).
- **Table** — sticky-header, sticky first column (`code`), click-to-sort on any column (toggle asc/desc), row-count caption ("N of 1167 customers"). Money columns right-aligned; status shown as a coloured badge; main group as a chip.

## Data sources
- [[customer-master]] — `GET /realise/api/customer-master/` (XHR). The page fires exactly one fetch on load; the entire master (~448 KB) is returned in a single payload and all filtering / sorting / KPI math happens in the browser. `status:'error'` in the body surfaces as an inline "Could not load" message.

## Key fields & columns
The table renders these 17 columns (order fixed in the page JS `COLS`):

| Column | Field key | Meaning | Fill rate (sample) |
|---|---|---|---|
| Code | `code` | Customer master code (e.g. `CUSTA000936`); the join key used by every Realise/Accounts report. Sticky first column. | 100% |
| Customer Name | `name` | Legal / trading name. | 100% |
| Main Group | `main_group` | Business-group / channel bucket the customer belongs to — see below. Rendered as a chip; drives the Main Group filter. | 100% |
| Status | `status` | Account state badge: **Active** (green), **Frozen** (red — credit-locked, see [[credit-lock-unlock]]), **Inactive** (grey, filter-only). | 100% |
| GSTIN | `gstin` | 15-char GST registration number (state code + PAN + entity). | ~75% |
| PAN | `pan` | Income-tax PAN. | ~0% (rarely stored separately; embedded in GSTIN) |
| Contact | `contact_person` | Named contact at the customer. | ~99% |
| Mobile | `mobile` | Contact phone. | ~10% |
| Email | `email` | Contact email. | ~0% |
| Address | `address` | Street / shop line (truncated, full text on hover). | ~44% |
| City | `city` | City / town. | ~98% |
| State | `state` | State / UT (also foreign, e.g. ABU DHABI for exports); drives State filter + States KPI. | ~99% |
| Pincode | `pincode` | Postal code. | ~97% |
| Sales Person | `sales_person` | Mapped salesperson / beat owner (68 distinct in sample, e.g. `G PURE`, `ANIL`). | ~26% |
| Payment Terms | `payment_terms` | Credit terms label — see below. | 100% |
| Credit Limit | `credit_limit` | Sanctioned credit limit in ₹ (numeric; formatted ₹ rounded). Feeds [[required-credit-limit]] logic elsewhere. | 100% |
| Balance | `balance` | Current outstanding ledger balance in ₹ (can be negative = customer in credit / advance). | 100% |

**Main Group values (24 distinct):** `GT` (General Trade — see [[GT]]), `MT` (Modern Trade — see [[MT]]), `ROI` (Rest of India — see [[ROI]]), `E-COMMERCE` (see [[ECOM]]), `HORECA`, `CSD` (Canteen Stores Dept), `CORPORATE`, `EXPORT`, `BRANCH`, `BULK OIL`, `PURCHASE OIL`, `COMPANY UNIT`, `CASH SALE`, `CALL CENTER`, `WEBSITE`, `CONSUMABLES`, `EVENTS & EXHIBITIONS`, `FIXED ASSETS`, `JOB WORK`, `REFERENCE`, `SANGAT`, `STAFF`, `STAFF CUSTOMER`, `TRANSPORT`. This mixes true sales channels (GT/MT/ROI/ECOM/HORECA/CSD/EXPORT) with internal/bookkeeping buckets (STAFF, FIXED ASSETS, JOB WORK, COMPANY UNIT). See [[channels]] and [[Main Group]].

**Payment Terms values (14 distinct):** `ADVANCE/CASH/0 DAYS`, `COD`, `CAD`, `20% ADVANCE`, `45 % ADV`, `LC 60`, and net-credit ladders `NET-01 / NET-02 / NET-05 / NET-07 / NET-10 / NET-15 / NET-21 / NET-30` (days). See [[credit-terms]].

## Notes / gotchas
- **Whole master in one shot.** No server-side pagination or filtering — the endpoint returns all rows; the state/group/status/search filters and column sort are pure client-side over `rows`. Fast to use, but the payload is large (~448 KB / 1,167 rows).
- **KPIs ignore filters** — they always describe the full master, by design.
- **Status enum mismatch** — the filter dropdown lists Active / Frozen / Inactive, but the live feed only contained **Active** and **Frozen**. "Inactive" is a supported-but-currently-empty state. Frozen ≈ credit-locked (see [[credit-lock-unlock]]).
- **PAN / email / mobile are sparsely populated**; GSTIN already embeds the PAN, so a separate PAN is usually blank.
- **Export** (`/realise/customer-master/export/`) is a plain `<a href>` GET that streams an XLSX file — treated as EXPORT and **not probed** per read-only discipline. Its columns mirror the table.
- Access gated by the `customer_master_viewer` group / `can_customer_master` permission (see [[users]]).

## Related
- [[customer-master]] (API) · [[users]] · [[required-credit-limit]] · [[customer-aging]] · [[credit-lock-unlock]]
- Concepts: [[channels]] · [[GT]] · [[MT]] · [[ROI]] · [[ECOM]] · [[Main Group]] · [[credit-terms]]
