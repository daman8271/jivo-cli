# Independent dispatch source, version 1

`collect_dispatch_now.py --config PATH --cache-dir PRIVATE --output dispatch-now.json [--once]`.
Runs only GET on the Factory dispatch list/detail endpoints. No company/business writes.
All pages are read **without date filters**: the source date query is docking/creation-based, not actual departure. Current month (plus yesterday at month boundary) is selected only after complete pagination, using DISPATCHED + gate_out_date crosschecked with timezone-aware dispatched_at.

Public envelope: version, ok, complete, asOf, attemptedAt, expectedRefreshSeconds (60), sourceUrl, coverage, unitNote, scopeNote, days, gateEntries, trips, issues. Failure keeps the previous arrays and asOf, sets ok/complete false with a new attemptedAt and generic error. Empty failed reads never become zero dispatch.

Coverage: fromDate/toDate (inclusive IST dates), dateBasis, allCompanies=true, listRows, pages, listComplete=true, queryDateFilter=null.

All totals below are litres, numeric or null (unknown): combinedLitres = source JIVO_OIL + JIVO_MART; wellnessLitres = source JIVO_OIL; martLitres = source JIVO_MART; beveragesLitres is separately reported. **Raw source company fields must not be silently relabelled.** operationalWellnessLitres / operationalMartLitres / operationalUnclassifiedLitres are item-derived ownership totals. Owner rules classify GP-FG and GP-FGM as Mart; BH-BT/BH-PF as Wellness only when source book is Oil. Other warehouses default to their recorded company and carry an explicit basis. Missing or conflicting item quantities make operational totals null. wellnessStorageLitres counts only verified JIVO_OIL BH-BT/BH-PF lines.

`days[]`: date, all totals above, gateEntryCount (Wellness+Mart company gate entries), tripCount (distinct source arrival identities for those entries, fallback gate identity), complete.

`gateEntries[]`: id, reference, tripId, identityBasis, company (unmodified source company), date, departedAt, litres, planningTonnes (= litres/1000, not physical tonnes), documentCount, warehouseLitres[{warehouse,litres}], wellnessStorageLitres, operationalWellnessLitres, operationalMartLitres, operationalUnclassifiedLitres, classificationConflict, items, detailComplete, issues[]. WarehouseLitres are the known source lines; **do not treat them as exhaustive when detailComplete=false**.

`items[]`: code, name, warehouse, quantity, uom, litres, operationalCompany (WELLNESS/MART/BEVERAGES/UNKNOWN), classificationBasis. Litres come directly from item.total_litres, including zero source litres for nonliquid goods; no pack/density guess. No customer, contact, driver, plate, address, attachment or source free-text remarks are published.

`trips[]`: id, date, departedAt, gateEntryIds[], identityBasis, all totals. Shared source `arrival` identity plus actual departure day joins company loads; licence plate never joins trips. Missing arrival identity falls back to a single gate entry explicitly labelled physical-trip-unverified. No claim that company gate rows equal unique trucks.

Source header litres remain reportable where detailed item coverage is incomplete, but warehouse/operational splits are null. Duplicate IDs, incomplete/changing pagination, list/detail conflicts, invalid actual-date timestamps or unrecognised source companies fail the cycle and retain last good evidence.

Private detail cache refreshes recent departures every 60 seconds and older departures every 12 hours, immediately on changed list fingerprint. Header list always refreshes completely. No service or deployment is performed by this collector.
