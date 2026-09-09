# Live material reconciliation — implementation plan

Authorized goal: make Factory/EXIM material evidence live in Astha so newly issued purchase orders, receipts, QC decisions and revised deliveries automatically change future production. An undated PO must become a visible commitment/action, not a fictional delivery or zero supply.

Architecture: Atlas recommends an owned additive material ledger. Keep the existing scheduling engine; do not import Mark 3's simulated purchases, six/seven/eleven/fourteen-day lead assumptions or scheduling algorithm. Parent owns runtime and release, Forge builders own Python and TypeScript, Cassius and Proof independently review and verify.

## Phase 1: Authoritative collection

Read Factory Oil warehouse stock, supplier catalog and every open supplier PO line, fully paginated gate entries and detailed receipt/QC records. Read EXIM tanks and individual shipment records, including parent contracts and revised ETAs. Preserve original observation times, success, completeness and refresh target per dataset.

Refresh supplier catalog every full PO scan so new suppliers are discoverable. Existing 2,231-supplier scans measured 109–111 seconds with four workers. Target 180 seconds without overlapping scans. Keep slow PO discovery separate from stock/QC refresh. Failures retain each supplier/warehouse's last good data and original time; they do not remove orders or set stock to zero. Preserve unresolved receipts across month boundaries and periodically reconcile historical windows.

## Phase 2: One lifecycle and one stock credit

Use company + PO + SAP line number, not just PO/item. Receipt detail route `/raw-material-gatein/gate-entries/{id}/po-receipts/view/` provides line and receipt-item identities. Reconcile outstanding PO quantities with unposted loads already at the gate. Match EXIM and Factory using material, quantity/unit, PO/contract, vehicle and dates, never vehicle alone. Contracts are not additional trucks.

Ledger stages: ordered, loading, in_transit, arrived, qc_pending, accepted_unposted, usable, rejected, cancelled, conflict. Every lot states stock inclusion: included, excluded or unresolved. QC acceptance does not prove posting or inclusion. Accepted quantity zero under ACCEPTED means received minus rejected according to the verified source rule. Posting after a stock snapshot cannot prove inclusion in that snapshot.

Own PM/RM stock replaces inherited opening material stock. EXIM tanks supersede corresponding oil drums once. Preserve explicit material units/conversion evidence; preforms are not finished bottles. When the new ledger exists, disable legacy EXIM event append. Every quantity occupies one lifecycle stage and can enter production stock only once.

## Phase 3: Evidence-based expected replenishment

Prefer recorded availability dates; next use shipment ETA plus separately supported QC/release timing; next same-supplier/same-material receipt history. Otherwise publish a missing-date action. Arrival is not usable availability.

Separate first-load lead time from part-load cadence on blanket orders. Require at least three distinct relevant receipt dates for recurring historical forecasts. Use observed load sizes capped by real outstanding balances. Calculate cadence once per supplier/material pool and allocate across its POs; do not multiply cadence by PO count. Different suppliers do not inherit one another's histories. Preserve earliest/expected/latest windows, sample counts, period, assumptions and evidence. Do not roll overdue windows forward each refresh just to remove zero-production days.

## Phase 4: Planning and user view

`materialSupply.version=1` contains revision, coverage.datasets, stock, orders, lots, expectedReceipts and actions. Public identifiers are consistently hashed; raw records and mappings stay private.

Default scenario uses expected existing supply with evidence. Recorded-only scenario excludes historical estimates. Proposed new purchases remain separate and off. Credit materials no earlier than usable date. Link conditional production to incoming evidence and missing confirmations. Show usable now, ordered, travelling, arrived/QC, expected usable date, affected production and next action. Explain closures, shortages, undated existing supply, unresolved recipes/identity, machine limits, storage limits and completed demand separately. Preserve dark mode.

Refresh the model on material content/revision changes even if unrelated metadata is unchanged. Source ages must remain visible; reduce avoidable input-cache delay. A complete HTTP response is not proof every source is current.

## Phase 5: Independent verification

Proof and Cassius must verify PO-line separation, partial receipt conservation, previous-month unresolved receipts, EXIM 777/789 already-at-gate regression, accepted-unposted visibility, posting-after-snapshot treatment, repeated vehicles, contract/child overlap, different-supplier history, cadence pooling, failed/truncated source retention, and public sanitization. Existing machine/storage invariants must pass.

Required isolated end-to-end replay, without creating business records: begin with a blocked 16 September run; add a source-shaped PO with supported usable-date evidence; collect and publish again; prove `/api/model` changes without deployment/manual date edits and production starts only from usable date. Repeat quantity change, delay, cancellation, new supplier and undated PO. An undated unsupported PO must change the action list, not become a promised delivery.

## Phase 6: Rollout and observation

Build and test in an isolated VPS staging directory; preserve unrelated Mark 3/Claude services. Compare a fresh candidate with raw quantities and lifecycle stages. Install owned Astha collectors/feed only after review. Deploy `jivo-mark4-astha`, make it public and verify HTTP 200 plus browser views. Observe multiple real collection cycles and material revisions reaching the model. Record actual cadence, unresolved source fields, decisions, evidence and rollback.

## Completion gates (verified 6 September 2026)

- [x] Owned fresh stock and complete automatic supplier/PO discovery.
- [x] Conserved lifecycle reconciliation across PO, EXIM, Factory gate, QC and stock; 43 source-unresolved lines remain explicitly qualified rather than forced into false matches.
- [x] Qualified historical estimates and actionable missing-date/stock-inclusion records.
- [x] Independent source-to-model replay and review passed.
- [x] Tests, typecheck and production build passed (76 TypeScript, 50 Python).
- [x] Correct public Astha release and visible desktop/mobile/dark-mode UI verified.
- [x] Two live PO and material cycles observed; changed revisions reached the public model without redeployment. Latency and limitations recorded in ROLLOUT.md.

Baseline backup: `/root/mark4-live-phase3/baseline-app.tgz` and baseline Factory/input service units. Material runtime rollback must restore only owned Astha files/services, never main checkout or Mark 3 runtime.
