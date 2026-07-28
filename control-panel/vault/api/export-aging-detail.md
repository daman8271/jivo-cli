---
endpoint: /realise/api/export-aging-detail/
method: POST
auth: session + X-CSRFToken (JSON)
readonly: false
used_by: [customer-aging]
tags: [jivo, api, accounts]
---
# `POST /realise/api/export-aging-detail/` (EXPORT — document only)

## Purpose
Server-side Excel export for the [[customer-aging]] page's **Export Detail** button: builds a workbook of **every open document + its remarks** for a chosen set of parties, aged to a given date. Distinct from the generic [[export-xlsx]] (which serialises client-built rows) — this one assembles the detail server-side.

## Request
Headers: `Content-Type: application/json`, `X-CSRFToken`. Session cookie required.

JSON body (from page JS):
- `as_of` — `YYYY-MM-DD`; the aging date.
- `parties` — array of customer codes (the currently filtered parties) to include.

Built as `body: JSON.stringify({as_of: <asOf>, parties: parties})`.

## Response
Not probed (EXPORT). Returns a binary `.xlsx` blob on success (streamed to a download named `Customer Aging Detail <as_of>.xlsx`); on failure returns JSON `{error}` with a non-200 status (the page throws on `!r.ok`).

## Used by
[[customer-aging]] (Export Detail).

## Notes
- **EXPORT — never executed.** Generates a file server-side; treated as non-read-only under recon discipline. Signature captured from page JS only.
- Scope follows the on-screen filters (only the filtered `parties` are exported).
