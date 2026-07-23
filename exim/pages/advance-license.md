---
title: Advance License
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /license/advance-license
section: License
---

# Advance License

[[INDEX|JIVO EXIM]] › **License** › Advance License

**Route:** `/license/advance-license`  ·  **Web:** `https://exim.jivo.in/license/advance-license`

## What this page does

Tracks JIVO's Advance Authorisation (duty-free import) licenses. `GET /license/advance-license-headers/` returns each license with its nested import lines (Bill of Entry: boe_No, boe_date, boe_value_usd, import_in_mts) and export lines (shipping bill: shipping_bill_no, sb_date, sb_value_usd, export_in_mts), plus header terms: issue_date, import_validity, export_validity, CIF/FOB values in INR and USD with exchange rates, and status (e.g. CLOSE). The user can create a new license header, add BOE import lines and shipping-bill export lines (POST endpoints), and link an export line to a specific import line via the `/license/advance-license-import-lines/dropdown/?license_no=` picker.

## How it helps

Advance Authorisation licenses waive import duty only if the matching export obligation is met before export_validity. Ops and finance open this page to see, per license, total_import vs total_export against to_be_exported and the remaining balance in MTS, so they can push shipments against licenses nearing expiry and avoid duty demands on unfulfilled obligations.

## Backend endpoints

- [[endpoints/license_advance-license-headers|`GET /license/advance-license-headers/`]] — Create advance-license header.

## Key data & interactions

- License table: license_no, issue_date, import_validity, export_validity, status (OPEN/CLOSE), cif_value_inr / cif_value_usd / cif_exchange_rate, fob_value_inr / fob_value_usd / fob_exhange_rate
- Fulfilment columns per license (MTS): total_import_quantity, total_import, total_export, to_be_exported, balance
- Expandable rows: import lines (boe_No, boe_date, boe_value_usd, import_in_mts) and export lines (shipping_bill_no, sb_date, sb_value_usd, export_in_mts, linked_import_line)
- Add-license form (POST /license/advance-license-headers/), add import-line and add export-line forms
- linked_import_line dropdown filtered by license_no when adding an export line

## Related pages (same section)

- [[pages/dfia-license|DFIA License]]


Linked: [[INDEX]] · [[API-INVENTORY]]
