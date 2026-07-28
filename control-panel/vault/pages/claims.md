---
title: Claims
route: /realise/claims/
type: page
endpoints: [claims, export-xlsx]
tags: [jivo, control-panel, accounts]
---
# Claims

## Purpose
A **manually-maintained claim register** for customer claims (discounts, NSO/scheme claims, FOC, co-op, damage etc.). The accounts / sales-ops team logs each claim with its party, type, amount and a **pass / hold** workflow, then filters and drills the book by month, type, customer or main group. Unlike the aging pages, claims are entered by hand — they are not pulled from SAP.

## What it shows
- **KPI cards**: **Claims** (count in selection), **Claim Amount** (Σ ₹), **Passed** (Σ passed ₹), **On Hold** (Σ hold ₹).
- **Table** with columns (`COLS`): Claim Date, Claim Pass Date, Claim Month & Year, Party, Main Group, Claim Type (tag), Ref. INV No., Claim Hold (Yes/No badge), Claim Amount, Claim Passed (Manual), Hold, Reason of Hold (Manual), plus per-row Edit/Delete.
- **Filters**: month, date, Claim Type; search (party / type / product / item / reason); **Drill** by Customer or Main Group.
- **Add / Edit Claim** dialog — fields: Receiving/Claim Date, Claim Pass Date, Claim Month, Party (autocomplete from masters), Main Group (auto-filled from party), Claim Type (autocomplete), Ref. INV No., COOP No., Claim Amount, Claim Hold (Yes/No), Claim Passed (Manual), Hold ₹ (auto = Amount − Passed), Reason of Hold.
- **Export Excel** and Excel **upload** (bulk import claims).

## Data sources
- [[claims]] — GET(XHR); returns `rows[]` (the register) + `masters` (customer picklist for the Add dialog).
- Writes (documented only): `claims/save/`, `claims/delete/`, `claims/upload/` — create/update, delete, and bulk-import claims.
- [[export-xlsx]] — POST (EXPORT): current view → .xlsx.

## Key fields & columns
- **claim_date / claim_pass_date** — date received vs date the claim was passed for payment.
- **claim_month / month_year / ym** — the month the claim is filed under (defaults to the receiving month; can be overridden).
- **party_code / party_name** — SAP CardCode + name; **main_group** auto-derived from the party.
- **claim_type** — free-text/typeahead category (e.g. `NSO CLAIM`, discount, FOC).
- **ref_inv_no / coop_no** — reference invoice and co-op scheme numbers.
- **claim_amount** — total claimed; **claim_passed** — amount approved for payment; **hold_amount** = claim_amount − claim_passed.
- **claim_hold** (`Yes`/`No`) + **reason_of_hold** — whether/why the claim is withheld.
- **masters.customers** — `[{code, name, main_group}]` picklist backing the party autocomplete.

## Notes / gotchas
- This is a **local register**, not a SAP feed — all rows come from data entered through this page's Add/Upload/Edit actions.
- `save/`, `delete/`, `upload/` are WRITE (page uses `API + 'save/'` etc. where `API = /realise/api/claims/`) — documented from JS only, never executed.
- Hold ₹ is auto-computed (Amount − Passed) in the dialog but stored as `hold_amount` on the row.

## Related
[[customer-aging]], [[open-payments]], [[required-credit-limit]], [[customer-master]], [[REALISE]], [[GT]], [[MT]]
