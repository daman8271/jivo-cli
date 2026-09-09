# Independent QA — live material reconciliation

Status: independent source, ledger, model and compiled HTTP/API checks PASS, including the fresh corrected live candidate. The previous bookkeeping blocker is resolved. Deployment, visible UI verification and unattended live-cycle checks remain parent-owned gates. QA owns evidence only, never application implementation. Checks ran on the isolated VPS workspace; no production business data was written.

## Verified results

- **7 collector checks passed:** new vendor discovered on next scan; another failed supplier retains its own original observation time and orders; coverage becomes partial; successful empty response removes closed orders; stock failure retains quantity and clock; stock second page is read; repeated page fails rather than duplicating stock.
- **11 raw-source reconciliation cases passed:** no PO; new September16PO; quantity25 instead of100; cancellation; different supplier without history; release delay; two PO lines sharing one supplier cadence; partial receipt exact-line netting; accepted-unposted; posted after stock snapshot; overdue history does not roll forward.
- **11 Python→TypeScript cases passed:** new PO yields100L on September18/22/26 and none earlier; lower quantity yields25L; cancellation and unsupported new vendor yield0; release delay moves runs to September21/25/29; two order lines pool cadence once; both unresolved receipt stages stay out of usable stock. All historical-supply production is conditional and recorded-dates comparison stays0.
- **4 adversarial contract guard defects fixed and independently re-tested:** cross-unit overcredit, unknown lifecycle stage, availability before PO creation, child lots exceeding parent outstanding. Valid100lot still schedules100only on its usable day.

Two additional integration defects were found and fixed: conditional supply initially produced100L while reporting0conditional; a legitimately posted receipt awaiting a newer stock snapshot initially triggered an overstrict outstanding-quantity guard. Independent replays now pass both.

## Concrete replay evidence

All commands/evidence under `/root/mark4-live-phase3/qa`:

- `replay_collector.py` → `collector-replay-results.json`.
- `replay_raw.py` → `source-replay-results.json`, `cases/*.json`.
- `replay_model.mjs` → `source-model-results.json`, `cases/*.input.json`.
- `contract-probe.mjs` → initial/retest JSON (the initial evidence intentionally retains the discovered failures).

Fixtures use private source-shaped supplier/PO/receipt rows and real factory field names; they are not live business writes. Old completed receipts establish same-supplier delivery cadence and independent QA timing. Inherited opening9999packaging units is deliberately inconsistent: owned stock0 wins, proving legacy quantities do not leak into the new calculation.

## Real Python feed/API replay

Prepared actual `serve_inputs.Feed` + `Handler` on isolated127.0.0.1:8796. It reads a private source-root fixture and production sanitize/merge functions, retaining the normal15second cache. Source horizon/meta stay fixed as the material envelope changes. `preload.cjs` redirects only the exact Astha input feed URL in the isolated Next process; it changes no production application source and mocks no clock. Next API3406 ran after the parent production build. All9 lifecycle HTTP variants passed:100L newPO,25L quantity change, delayed100L, cancellation0, undated newvendor0withaction, pooled160L, partial70L, accepted-unposted70L and posted-after-snapshot70L. No deploy/restart/manual date change occurred between variants. Material revisions reached API in approximately16.05seconds with fixed unrelated input metadata. Invalid replacement material JSON also retained70L and the original observation timestamp, marked coverage incomplete and feed stale. Files: `http-replay-results.json`, `http-failure-result.json`, `cases/*.api.json`. FutureSeptember16 fixture dates intentionally cause stale status; no clock was mocked, and this test does not claim live-business freshness.

## Source limitations and remaining gates

No reliable promise-date field is present in current supplier PO responses. Historical estimates remain estimates and never borrow another supplier's history. Accepted QC is not proof of posting/stock inclusion. Live collector cadence, real EXIM777/789 stage reconciliation, full-suite/typecheck/build, public UI including dark mode, and multiple live update cycles are separate parent-owned release gates. This document does not claim those are complete.

## Earlier real-candidate blocker — resolved and independently rechecked

At 21:38 IST an earlier candidate failed the TS quantity guard because historical Factory receipt rows remained unposted while PO received totals already included receipts. PM0000469 had 2,504 outstanding against 16,020 in historical gate rows. RM0000025 had 21,769 L outstanding against 329,670 L of unresolved history. An intermediate FIFO fix also incorrectly promoted physical QC stages. Both approaches were rejected.

The final source uses complete lifetime receipt history to calculate the additional quantity at gate, while preserving individual physical stages and quantities. Accounting overlap remains unresolved for stock inclusion. Independent `replay_book_accounting.py` passes four assertions: 80 + 20 physically pending units remain pending and total 100; a PO already recording 80 received has only 20 additionally at gate; no new stock or expected receipt is invented. The final 11 raw-source and 11 Python-to-model replays were rerun and passed. The current partial-at-gate case schedules 95 L conditionally: 25 pending QC plus 70 undelivered, excluding 5 rejected. The earlier HTTP fixture run above preceded this QC-history addition and correctly recorded 70 L for that earlier source version.

## Final fresh candidate and compiled API

Independently fetched the actual Python feed at `127.0.0.1:8795/inputs.json`: material observation `2026-09-06T16:16:32.718672+00:00`, revision `cce8ef2616507958484d0bd1`. It contains 216 orders, 1,206 lots and 110 expected receipts. All 998 coverage datasets report success/completeness. Public feed payload was 4,445,833 bytes, below the 5 MB loader limit. Independent quantity summation found zero excluded incoming lots exceeding their PO outstanding quantity. No FIFO-promoted lot IDs remain.

The actual final compiled Next API was started separately on port 3406, redirecting only its exact feed fetch to the real isolated Python feed. `/api/model` returned HTTP 200, the same material revision and a 4,291,209-byte response. Its expected plan is 727,468 L; recorded-dates comparison is 544,267 L; 183,984 L is explicitly conditional on estimated supply. Direct `buildModel` and the compiled HTTP API agree. These are candidate snapshot outputs, not a production performance guarantee.

PM0000085's August 4 PO correctly retains 89,000 outstanding: 51,000 additionally at gate and 38,000 undelivered. Historical accepted-unposted loads preserve their stages and unresolved stock inclusion. EXIM 777 and 789 each resolve to one physical QC-pending receipt, with no extra road copy. EXIM 789's estimated release is supported by QC history and remains conditional; EXIM 777's accounting overlap blocks additional usable credit.

Confidence: high for the tested quantity, lifecycle, conditional-label and API contracts. Historical delivery predictions still require operational confirmation; a passing model contract does not prove those future dates will occur.
