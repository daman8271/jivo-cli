---
endpoint: /api/cogs/
method: GET
auth: session + XHR header (X-Requested-With) + OTP gate
readonly: true
used_by: [control-panel]
tags: [jivo, api, cogs, otp-gated, sensitive]
---

# `GET /api/cogs/`

## Purpose
Return **Cost of Goods Sold** for a date window so the home dashboard's COGS KPI card can show total COGS, COGS-per-litre and total litres. COGS is a **sensitive P&L figure**, so this endpoint is **OTP-gated** and additionally requires the `can_cogs` permission — for user `preshit` (`can_cogs:false`) it is fully denied. See [[COGS]].

## Request
Top-level endpoint (note: `/api/…`, **not** under `/realise/`). Query params (built by the COGS card JS on [[control-panel]]):
- `from_date` — string `YYYY-MM-DD`; window start, taken from the card's `data-from-date`.
- `to_date` — string `YYYY-MM-DD`; window end, from `data-to-date`.
- `param_type` — string; selected from the card's inline `<select name="param_type">` (COGS parameter/basis dimension). Sent empty when unset.
- `otp` — string; one-time password typed into the card's `<input name="otp">`. **This is the gate** — without a valid OTP the call is refused.

Headers: session cookie + `X-Requested-With: XMLHttpRequest`.

Live JS (home.html `bindCogsCard`):
```
var params = new URLSearchParams();
params.set('from_date', card.dataset.fromDate || '');
params.set('to_date',   card.dataset.toDate   || '');
params.set('param_type', form.param_type.value || '');
params.set('otp',        form.otp.value        || '');
fetch('/api/cogs/?' + params.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
```

## Response
Two documented states:

**Locked (no/invalid OTP or no `can_cogs`)** — observed live probe `GET /api/cogs/?param_type=&otp=` → **HTTP 403**, `application/json`:
```json
{"error": "Permission denied"}
```

**Unlocked (valid OTP + permission)** — *not executed* (production, no OTP). From the client code the success payload has a `cogs` object with display strings:
- `cogs.total_cogs_display` — total COGS (₹) for the window.
- `cogs.cogs_per_liter_display` — COGS per litre (₹/L).
- `cogs.total_liter_display` — total litres in the window.
- `cogs.opt_missing` — boolean; when `true` the card treats COGS as still locked and shows "Enter OTP to view COGS" (only litres are revealed).

## Used by
[[control-panel]] (COGS KPI card — only rendered when `can_cogs` is true; absent for `preshit`).

## Notes
- **OTP-GATED — DOCUMENT ONLY. Do NOT attempt to bypass.** Per the recon recipe this endpoint needs `param_type` + a valid `otp`; probing without OTP is a permission check (returns 403), not a bypass. Confirmed live: `403 {"error":"Permission denied"}`.
- Not a write endpoint, but sensitive: it exposes cost/margin data. `preshit`'s permission set has `can_cogs:false`, so even a valid OTP would not unlock it for this user.
- Lives at the top-level `/api/` namespace (alongside the admin-write `/api/users/save/` · `/api/users/delete/`), not under `/realise/api/`.
