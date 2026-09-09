# Factory delivery-date audit — 9 September 2026 around 01:00 IST

Read-only live Oil API + current frontend source. High confidence for observed endpoints; no claim every private backend field has been exhausted.

- Current site main JS: https://ji.jivo.in/assets/index-D1n9TSOZ.js. Read current PurchaseFromPlanPage-B2wMioFw.js, PurchaseOrderDetailPage-Bs5s2zWK.js, PurchaseOrderListPage-DUQyvDa2.js, MaterialTypesPage-C87sp4my.js.
- GET /api/v1/po/open-pos/?supplier_code=<observed vendor>: collector current all-vendor cache 326 PO headers; union header keys branch_id, doc_date, doc_entry, items, over_receipt_enforced, po_number, sourceAsOf, supplier_code, supplier_name, vendor_ref. Item keys item_name,line_num,ordered_qty,po_item_code,rate,received_qty,remaining_qty,uom. No ETA/due date.
- GET /api/v1/po/open-pos/220926007/items/, /220926005/items/, /220826016/items/: same shape, no due-date drilldown.
- GET /api/v1/planning-purchase/plans/44/requirement/: 210 component rows,197 packaging,13 raw. 75 packaging and5 raw have open_po_earliest_due. All 80 earliest dates before9 Sep; none future/today. This is aggregate earliest date only; can hide later due dates. open_po_lines is COUNT, not nested line details. All210 lead_time_days=null, lead_time_source=NONE. No complete promised shipment calendar.
- UI https://ji.jivo.in/planning-purchase/plans/44/purchase shows earliest due in hover title on On order quantity. Current source: title `${n.open_po_lines} open PO line(s), earliest due ${E(n.open_po_earliest_due)}`.
- Example PM0000408 caps: source on_order_qty50000,open_po_lines1,open_po_earliest_due2026-09-02. Matches PO220926007 line1 remaining50000. Exact PO exposes doc_date2026-09-02 but no due field. PM0000019/20 labels source earliest2026-09-01; PO220926005 lines2/3 doc_date2026-09-01. Do not label those supplier-confirmed promises.
- GET /api/v1/planning-purchase/purchase-orders/: UI https://ji.jivo.in/planning-purchase/purchase-orders supports Delivery field doc_due_date and detail required_date. Exactly2 current records both CANCELLED,mustard raw oil,zero active packaging promises. Fields therefore supported but not populated as usable book.
- GET /api/v1/planning-purchase/commitments/?item_code=PM0000005&warehouse=BH-PM: due_date is OUTBOUND transfer reservation due date, not incoming PO date.
- Older /supply-chain/reference/lead-times/,/reference/imports/,/parameters/ and /order-processing/procurement/ actual API now HTTP404; do not reuse August empty-data claim as current.
- QC material-types current160 types. No duration policy fields in master. Tested carton76(14 tests),peanut203(11 tests),mustard184(11 tests), parameter sets and parameter details. Identity,test limits,standard_value,min/max,uom etc; no promised QC duration/SLA. Peanut and mustard have actual named tests (peroxide,free fatty acid,refractive index etc). Future release duration must be empirical estimate or QA-entered policy; not present as normative schedule in inspected records.
- requirement44 meta live warehouse_scope PACKAGING=[BH-PS,BH-PC,BH-PM],RAW=[BH-LO,BH-OT]. Source note explicitly excludes FG,nonmoving,jobwork,wastage from drawable material stock. Keep this distinct from Daman written-authority audit.

Full private snapshots on VPS:/root/mark4-astha/private/delivery-source-audit-20260909.json; bundle files alongside. No business writes.
