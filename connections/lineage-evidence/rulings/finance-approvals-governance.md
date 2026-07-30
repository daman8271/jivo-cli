# FINAL RULINGS — domain: finance-approvals-governance

Adjudicator run 2026-07-30. Live access used: SAP HANA via tunnel
(`./hana-sql/hana-sql -env connections/hana-tunnel.env`, user ZIA) **and** the SAP B1
Service Layer via tunnel (`cd sap-b1/cli && SAPB1_HOST=localhost SAPB1_PORT=15000 ./sapb1 …`,
logged in as `manager`), plus `postsql` against the Postgres cluster and one live `jsap-cli`
session. Every statement issued was a SELECT or a GET. No credential is reproduced here.

---

## THE HEADLINE — and it overturns the domain's own prior

The brief handed me a STRONG PRIOR:

> "SAP holds the POSTED financial document; the apps hold the WORKFLOW that produced it
> (who approved, when, what was rejected, what is still pending). Rejected and pending
> items never reach SAP at all — test that claim rather than assuming it."

I tested it. **It is wrong as stated, and wrong in the most expensive direction** — it
would have led us to rule a whole family of approval data "N / genuinely new" when SAP
holds it natively, in a first-class, Service-Layer-readable object, current to yesterday.

### Counter-evidence 1 — SAP's own approval engine is live, rich, and retains rejections

```
./hana-sql/hana-sql -env connections/hana-tunnel.env \
  "SELECT \"Status\",\"ProcesStat\",COUNT(*) N,MIN(\"CreateDate\") A,MAX(\"CreateDate\") B
   FROM JIVO_OIL_HANADB.OWDD GROUP BY \"Status\",\"ProcesStat\" ORDER BY N DESC"
```
| Status | ProcesStat | N | first | last |
|---|---|---|---|---|
| Y (approved) | P | 52,935 | 2024-10-03 | 2026-07-29 |
| Y | C | 1,543 | 2024-10-03 | 2026-07-29 |
| W (**pending**) | C | 1,290 | 2024-10-03 | 2026-07-29 |
| **N (rejected)** | C | **535** | 2024-10-08 | 2026-07-15 |
| **N (rejected)** | N | **465** | 2024-10-05 | **2026-07-29** |
| Y | A | 319 | 2025-03-18 | 2026-07-29 |
| W (**pending**) | W | 212 | 2025-12-19 | 2026-07-29 |
| W | N | 162 | 2024-10-05 | 2026-07-17 |
| … | | | | |

**Totals: 57,741 approval requests in Oil alone — 1,000 REJECTED and 1,671 PENDING**,
current to 2026-07-29. Mart 14,214, Beverages 16,515.

Sample rejected rows — note `DocEntry` is NULL, i.e. these never became a posted document,
yet SAP kept the request:
```
WddCode ObjType DocEntry Status ProcesStat CreateDate  OwnerID
70515   13      NULL     N      N          2026-07-29  24
70295   16      NULL     N      N          2026-07-28  44
70158   18      NULL     N      N          2026-07-27  17
```

### Counter-evidence 2 — it is exposed through the ordinary Service Layer, live

```
cd sap-b1/cli && SAPB1_HOST=localhost SAPB1_PORT=15000 ./sapb1 query ApprovalRequests --top 2 --json
```
returns a full per-stage trail:
```json
{ "Code": 9439, "ApprovalTemplatesID": 41, "CurrentStage": 13,
  "DraftEntry": 6928, "DraftType": "112", "ObjectEntry": 10573, "ObjectType": "18",
  "OriginatorID": 17, "Status": "arsApproved", "Remarks": null,
  "ApprovalRequestLines": [ { "StageCode": 13, "Status": "ardApproved", "UserID": 12,
    "CreationDate": "2025-01-16", "CreationTime": "15:55:00",
    "UpdateDate": "2025-01-17", "UpdateTime": "12:57:00", "Remarks": null } ],
  "ApprovalRequestDecisions": [] }
```
The repo's own SAP catalogue already documents it and nobody in phase 1 looked:
`sap-b1/vault/services/ApprovalRequests.md` → `readable: true`, `rows_oil: 57184`;
`ApprovalStages.md`, `ApprovalTemplates.md` (93), `Drafts.md` (47,115).

### Counter-evidence 3 — pending pre-posted documents live in SAP too
`ODRF` (drafts) = 47,609 in Oil. By `DocStatus`: ~3,700 are **O = open/pending** across
ObjTypes 13/18/20/22/67, current to 2026-07-29. A draft A/P invoice sitting in an approval
queue *is* in SAP.

### So what IS true?
The prior is right about a *different* thing. Split it in two:

| Approval flavour | Who holds the trail | Rejections/pending |
|---|---|---|
| **SAP-native approval** (the doc is drafted in SAP, OWDD fires) | **SAP** — 57,741 requests, per-stage approver `UserID`, timestamps, outcome | **In SAP.** 1,000 rejected, 1,671 pending |
| **App-originated feeder** (the record is born in an app and only the approved one is pushed) | **the app** — SAP sees nothing until push succeeds | **Never in SAP.** Proven below |

And what SAP does *not* keep well, even for its own approvals, is **the human reason**:
`OWDD.Remarks` is populated on **336 of 57,741** headers and `WDD1.Remarks` on **1,955 of
57,752** lines. SAP records *who / when / which stage / what outcome*. The apps record
*why*, plus everything that happened before the document existed.

### The clean proof of the app-side half — SAP's own schema hosts it
`ZVENDOR_PORTAL` / `ZCUST_PORTAL` (non-SAP tables **inside** `JIVO_OIL_HANADB`):
```
ZVENDOR  APPROVED 44  SAP_CARD_CODE populated 44   PENDING 2 → 0   REJECTED 3 → 0
ZCUST    APPROVED 12  SAP_CARD_CODE populated 12   PENDING 2 → 0   REJECTED 3 → 0
```
Every approved onboarding became a SAP business partner. **Not one rejected or pending one
did.** That is the F/N boundary made visible in a single GROUP BY.

---

## MANDATED N-CHECK — performed once, for the whole domain

Before ruling N on anything I enumerated **every** SAP user-defined table in Oil (59
non-archive `@` tables) and swept all three schemas for the relevant object names.

```
SELECT TABLE_NAME, RECORD_COUNT FROM M_TABLES
WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND TABLE_NAME LIKE '@%' AND TABLE_NAME NOT LIKE '@A%'
```
→ `@BRAND @BUDGET @BUDGET1 @CHAIN @ITEM_SKU @ITEM_SUBGRP @ITEM_UNIT @ITEM_VARIETY
@MAIN_GROUP @OZIA @OZIAR @QC_I @QC_O @SERVER @UNE_* (7) @UTL_* (35) @ZIA_*(4)`.
**None** is a ticket, task, MoM, document hub, org chart, aging remark, claim, target,
credit lock, courier bundle or maker/checker voucher store.

```
SELECT SCHEMA_NAME,TABLE_NAME,RECORD_COUNT FROM M_TABLES WHERE SCHEMA_NAME LIKE 'JIVO%'
AND (UPPER(TABLE_NAME) LIKE '%TICKET%' OR '%TASK%' OR '%MOM%' OR '%MINUTE%'
  OR '%DOCHUB%' OR '%DOCUMENTHUB%' OR '%HIERARCH%' OR '%CLAIM%' OR '%AGING%')
```
→ **zero business hits.** (The only rows returned were `*_STAGING_DELTA_TABLE`, all 0 rows,
which matched only because "ST-AGING" contains "AGING".)

```
… WHERE UPPER(TABLE_NAME) LIKE '%REIMBURS%' OR '%IMPREST%' OR '%TRAVEL%'
      OR '%EXPENSE%' OR '%VOUCHER%' OR '%MAKER%' OR '%CHECKER%'
```
→ **zero rows in all three schemas.**

User-field sweep (`CUFD`, 5,572 definitions in Oil) for `%REMARK% %CLAIM% %TARGET%
%APPROV% %LIMIT% %LOCK%` → only stock B1 line-level `U_Remarks`, `OJDT.U_REMARKS`,
`@ZIA_DL_LIMIT.U_Limit`, `OITM.U_ITEM_LOCK`. And the two that *are* populated are not what
they look like:
- `INV1.U_Remarks` → **69 of 96,900** populated. Cannot be the control-panel aging-remark store.
- `OJDT.U_REMARKS` → 79,150 of 132,621 populated, but sampling shows it is a **verbatim copy
  of `Memo`** (bank narration / "Based On Sales Orders 1726076714."), i.e. SAP-native
  document narration, not human annotation.

Standard-object emptiness confirmed: `OCLG`=0 (activities), `OOPR`=0, `OSCL`=0, `OCTR`=0,
`OPRQ`=0, `OPRJ`=0 in all three companies; `OHEM`=17/1/15 with `startDate` 0, `jobTitle` 0,
`dept` 3, `manager` 1 populated.

---

## RULINGS

### A. The books (SAP owns these outright)

**A1. General ledger, journal entries and chart of accounts — M (98, live)**
`OJDT` 132,621 / `JDT1` 513,596 / `OACT` 1,424, latest RefDate 2026-07-29. Service Layer
`JournalEntries` rows_oil 131,295.
Surfaced by: `jsap dashboards ledgers` (3/3 account names verified in `OACT`),
`exim sap-sync get-customer-ledger|get-vendor-ledger`, `sapb1 JournalEntries`.
*Nothing is added.* Ask SAP.

**A2. Party ledger balances (customer / vendor outstanding) — M (98, live)**
`OCRD.Balance`, paisa-exact against EXIM:
```
VENDA001347 INDRANI FOODS       -50604960/1        (EXIM: -50,604,960)
VENDA000149 MIGASA ACEITES S L U -12461355487/2500 (= -4,984,542.1948; EXIM: -4,984,542.19)
```
Surfaced by `exim sap-sync get-balance-sheet` / `get-vendor-balance-sheet`,
`control-panel masterdata customer-master`. Straight copy.

**A3. Open A/R + customer aging (raw open items) — M (97, live)**
```
SELECT COUNT(*), SUM("DocTotal"-"PaidToDate") FROM JIVO_BEVERAGES_HANADB.OINV
WHERE "DocStatus"='O' AND "CANCELED"='N'   →  1168 | 177421880353/2500 = ₹70,968,752.14
```
identical to `exim sap-sync get-open-ar` (1,168 rows / ₹70,968,752.14). Note EXIM's A/R
reads the **Beverages** company, which nobody had documented.
Surfaced by `exim get-open-ar` / `get-customer-aging-balance`,
`control-panel accounts aging-oil|aging-mart|aging-beverages`.
Buckets 0-30/31-60/… are the app's arithmetic (see A7); the rows are SAP's.

**A4. Open A/P invoices — M (96, live)** `OPCH` 15,934 Oil, `exim get-open-ap` "DB Primary
Key" is literally `OPCH.DocEntry`. Filtered subset (171 returned vs 4,242 open in SAP).

**A5. Incoming payments / receipts on account — M (96, live)**
`ORCT` 13,861 Oil, latest 2026-07-29. Control-panel `accounts open-payments` row
`{doc_no 726246746, CUSTA000365, 1,132,770}` == `ORCT.DocNum 726246746 / CUSTA000365 /
RAJESHWAR KISHORE MAHENDERPAL / 2026-07-22 / 1,132,770`. The app's `open_bal` is *not*
`ORCT.OpenBal` (20,104.42) — that column is app arithmetic.

**A6. Outgoing / vendor payments — M (97, live)** `OVPM` 14,356, latest 2026-07-29.
**No app CLI in this domain exposes it.** Only `sapb1`/`hana-sql`.

**A7. Derived finance metrics — M underneath (92, live)**
Aging buckets, B2B/B2C split, DSO-style ageing, Required Limit = (ledger + OIH) × 1.02,
realise ₹/L, MATCHED/MISMATCH reconciliation status. **The value here is the maths, not the
data** — every input is a SAP row. Two consequences: (a) you cannot get these from SAP
without rebuilding the formula; (b) you must never treat them as an independent source.
The control-panel mapper could not re-derive the headline sales aggregate from SAP
(OLIVE 76.2 M in SAP vs 53.0 M in the app) — the inputs are proven SAP, the filter rules
are not reproducible from outside.

### B. Native finance overlays (SAP has no home for these)

**B1. Per-invoice A/R aging remarks + special-price overlay (control-panel) — N (93, live-negative)**
UDT check: done (§ mandated check). Column check: done — `INV1.U_Remarks` 69/96,900,
no header remark UDF on `OINV`. Postgres check: `postsql search aging_remark` → 0 rows in
all 15 DBs. The app's own doc quotes its confirm dialog: *"cannot be undone. SAP data is
untouched."*
**Uncertainty:** the Django DB was never located (not in the Postgres cluster, engine/host
unknown), so this is a negative-space ruling — proven not-in-SAP, not directly observed
in its own store.

**B2. Claims register with hold/pass approval workflow (control-panel `accounts claims`) — N (94, live-negative)**
Fields: `claim_type, claim_hold, claim_passed, hold_amount, reason_of_hold, claim_pass_date,
coop_no`, plus free text like *"APPROVAL PENDING FROM PRINCE SIR"*. UDT + column sweep for
`%CLAIM%` returns only stock B1 tax columns (`ClaimRefun`). `party_code`/`ref_inv_no` are
**references** into `OCRD`/`OINV`, not provenance. Same negative-space caveat as B1.

**B3. Required-credit-limit lock + delivery/closing remark (control-panel `credit`) — N (88, schema+doc)**
The SAP credit limit itself (`OCRD.CreditLine`, verified: CUSTA000872 = 1,250,000) is **M**.
The *lock snapshot*, `days_left`/`lock_until`, the 2 % buffer rule and the free-text remark
are the app's. `@ZIA_DL_LIMIT` (12 rows) is a per-**SAP-user** document limit, not this.
**Uncertainty:** the page was unreachable (office-network-only); I never saw a live
`#credit-data` blob, and could not confirm a lock is currently active anywhere.

**B4. Credit-limit CHANGE REQUESTS (HANA `tbl_customerLimit`; OMS `credit_limit_logs.jsap_doc_id`) — F (70, live)**
```
SELECT * FROM JIVO_OIL_HANADB."tbl_customerLimit" ORDER BY "createdOn" DESC
id 35 | CUSTA001015JW | CurrentLimit 0 | NewLimit 180000 | ValidTill 2025-05-09 | expired 0 | createdBy 17
```
35 rows, **all stale — newest 2025-05-09**, ~15 months old. `OMS.credit_limit_logs` (11 rows)
carries `jsap_doc_id`, so OMS points at JSAP's request, not at SAP.
**Uncertainty:** I could NOT confirm the approved `NewLimit` is written back to
`OCRD.CreditLine`. Worse, the CardCodes carry a `JW` suffix that does **not** exist in SAP:
`CUSTA001015JW`/`CUSTA000592JW`/`CUSTA000002JW` → **0 rows** in Oil/Mart/Beverages `OCRD`,
while the un-suffixed `CUSTA001015` (KAMALJEET CASH SALE J3) and `CUSTA000592` do exist.
Ruled F on the shape (request → SAP field), not on a proven push. **Would change my mind:**
finding an `OCRD.CreditLine` value equal to a `NewLimit` on the matching un-suffixed card,
or the JSAP write path in source.

### C. Approval workflows

**C1. SAP-native document approval requests (`OWDD`/`WDD1`; Service Layer `ApprovalRequests`,
`ApprovalStages`, `ApprovalTemplates`) — M (99, live)** — *and NOT exposed by any app CLI.*
57,741 Oil / 14,214 Mart / 16,515 Bev; 1,000 rejected, 1,671 pending; 23 distinct approvers
in `WDD1`; per-stage `UserID` + creation/update timestamps; live to 2026-07-29.
By ObjType (Oil): 67 stock transfer 17,250 · 18 A/P invoice 14,839 · 13 A/R invoice 10,008 ·
20 GRPO 5,080 · 22 PO 2,235 · … · **17 sales order only 7**.
That last number matters: sales orders are essentially never approved in SAP, which is
exactly consistent with orders arriving from OMS already approved — so the OMS approval
trail is genuinely additive (C4) while the purchase/inventory approval trail is not.

**C2. SAP drafts (`ODRF`; Service Layer `Drafts`) — M (98, live)** 47,609 Oil, ~3,700 open,
latest 2026-07-29. Pending pre-posted documents ARE in SAP.

**C3. JSAP budget approval workflow — F (92, live)**
Chain (phase-1, re-checked by me): JSAP `budgetId 15849 / objType 18 / docEntry 51648 /
VENDA000869 / approved 2026-07-08` → `OPCH DocEntry 51648` does **not** exist → `ODRF
DocEntry 51648` exists (ObjType 18, DocTotal 425,250) → `OPCH DocEntry 47577` carries
`draftKey = 51648`. Draft in SAP → approval in JSAP → posted invoice back in SAP.
Physically the trail lives in **non-SAP tables inside the SAP HANA schema**:
```
tbl_Draft_Approvals   1,440 Oil / 7,351 Bev   DocDate 2024-10-18 … 2026-07-27  (CURRENT)
   ApprovedStatus: A 1,092 · R 174 · in-flight 143 · V 31
   columns: Branch DocEntry ObjectName ObjType AcctCode AcctName CardCode CardName
            EFFECTMONTH BUDGET SUB_BUDGET AMOUNT Current_month_Budget Budget_Owner
            OwnerCode Approver_Name ApprovalCode Status LineRemarks
JS_SYNC_BUDGET_APPROVAL_WORKFLOW 29,212   SYNC_TIMESTAMP 2026-07-30 02:50  (SYNCED TODAY)
   status: A 28,037 · P 595 · R 580 ; budgetId range 63…16,157 (15849 present)
js_budget_approval_workflow 86           createdOn max 2025-04-12  (DEAD)
```
**These are invisible to `sapb1` / the Service Layer.** Only `hana-sql` reaches them.
What SAP genuinely lacks: `budgetId`, BUDGET/SUB_BUDGET attribution, stage names
("factory oil v5 1"), the verify-then-approve second step, `LineRemarks`.
**Trap:** JSAP `totalAmount` 393,750 ≠ SAP `DocTotal` 425,250 (delta = exactly 8 % of the
JSAP figure). Never mix them in one number.

**C4. OMS order approval workflow (auditor → billing → rate approver; rate approvals,
rejections, remarks, notifications) — N (94, live-negative)**
`order_rate_approvals` 88, `order_item_approval_mapping` 95, `rate_approver_rules` 187,
`orders_log` 380. UDT check: done, no match. `ORDR`/`OQUT` carry **zero back-reference** to
an OMS order. `OWDD ObjType 17` = 7 requests in 22 months, so SAP is not running this queue.
**Do not be fooled by `ORDR.U_OMS_Order_No`** — 6,253 rows but only 746 distinct values
dominated by keyboard-mash (`4563`×750, `1234`×639, `123`×225), and it stopped being
written on 2026-04-28. It is not a join key.

**C5. Vendor / customer onboarding portal approval (`ZVENDOR_PORTAL`, `ZCUST_PORTAL`) — F (96, live)**
See counter-evidence 3 above. 66 columns incl. GSTIN/PAN/TAN/TDS/MSME/FSSAI/`BANK_ACCOUNTS`/
`ATTACHMENTS`/`VERIFIED_BY`/`APPROVED_BY`/`REJECTED_BY` → `SAP_CARD_CODE`.
**No CLI in this repo exposes it** — reachable only by `hana-sql`.

**C6. WhatsApp approval notification + action log (`JIVO_WA_MESSAGE_LOG` 5,941,
`JIVO_WA_SENT` 641, view `view_whatsapp_bot`) — N (90, live)**
SENT 5,918 / FAILED 23, live 2026-05-01 → 2026-07-29. `JIVO_WA_SENT` columns include
`WddCode, ApprovedBy, Source, ActionAt, SendStatus, AttemptCount, LastError`. The approval
**outcome** lands in `OWDD` (M); the *delivery channel, retry state, and the fact the
approval was actioned from WhatsApp* exist nowhere else. Not exposed by any CLI.

**C7. JSAP budget head / sub-budget catalogue — N (90, live-negative)**
JSAP serves 15 heads (OTE, BackOff, NPD3, Factory, Interest, Del Bkhp, Del Mayp, FACT_COM…).
SAP `@BUDGET` holds **exactly 1 row** (`U_BUDGET = 'BackOff'`, created by `manager`
2026-04-11) and **does not exist at all in `JIVO_MART_HANADB`**. SAP's real budget module
`OBGT` (Oil 164 / Mart 0 / Bev 175) is unusable junk — top rows are
`FREIGHT AND CARTAGE 55,555,000,000`, `SECURITY EXPENSES 1,111,111,110`,
`SALARY EXPENSE 111,111,110`, all FY 2025-04-01. So the budget *dimension* and the budget
*amounts* are JSAP's; only the account dimension and the actuals are SAP's (C8).

**C8. Budget-vs-actual dashboard, account + actual half (`jsap dashboards ledgers|budgetdata`) — M (88, live)**
`ADVERTISEMENT`, `AGENCY CHARGES EXPORT`, `SALES CANOLA @ 5 %` → `OACT` 5640001 / 5300006 /
4110001, 3/3 exact.
**Uncertainty:** I verified the account dimension but did not reconcile a single monthly
amount back to `JDT1`, so "the actuals come from SAP postings" is inferred.

**C9. Factory GRPO / production posting into SAP — F (90, live)**
`grpo_grpoposting` 265 rows / 232 with `sap_doc_num`, latest 2026-07-28; `grpo_servicegrpoposting`
158/158 (dormant since 2026-06-15); `warehouse_bomrequest` 12/72; `production_execution_productionrun`
14/86. Partial fill rate = real feeder. The **QC two-signature decision, arrival-slip photos,
gate/weighbridge data, the rejected quantity and its reason** are the N residue.
Note `PRODUCTIONORDERSYNC` (2,499 rows, `SAPSTATUS='PENDING'` on all of them) is the
pre-SAP approval gate — app-only in effect.

**C10. Factory scan-exception / partial-dispatch / docking approvals — N (94, live-negative)**
`docking_admin_dockingpartialscanrequest` 143, `dockingscanskiprequest` 26, with
`requested_by / reviewed_by / reviewed_at / review_notes / scanned vs expected`. UDT check
done; no SAP object. `sap_doc_num` on these rows is a comma-joined **list of referenced
invoices** — a pointer, not provenance.

**C11. JSAP bill-verification maker → checker → payment → payment-checker workflow — N (78, live)**
Live now: `jsap bills maker --json` → `{accountName "G.S. Handloom", vchNumber 973,
voucherDate 2026-07-29, billAmount 26,030, checkerStatus "Pending", paymentStatus "UnPaid",
makerRemark "", isPaymentVerified false}` — sequential voucher numbers, current to yesterday.
998 vouchers / 100 accounts, all **Baru Sahib / Akal institutional supply** (bakery, dairy,
catering, garments, footwear, toys). Cross-checked against 8,503 `OCRD.CardName` rows from
all three schemas: 6/100 generic-name coincidences. Line items `Gs Pillow`, `Mattress Single`
→ 0 matches in `OITM` in any schema; warehouse `Ary Warehouse` → 0 in `OWHS`.
**Uncertainty:** certain it is not JIVO SAP data; NOT certain whether the vouchers are keyed
by a Maker in JSAP (→ N) or imported from a Marg/Busy-style package (→ X). The presence of
`hsnsacid` foreign keys and an app warehouse master leans N. **Would change my mind:** an
import/upload endpoint or a batch-load timestamp pattern on the voucher table.

**C12. TankhaPay approvals, reimbursement claims, travel expense, imprest applications — N (93, live-negative)**
Zero SAP tables match `%REIMBURS% %TRAVEL% %EXPENSE% %VOUCHER% %MAKER% %CHECKER% %IMPREST%`
in any of the three schemas. `OHEM` is a 17/1/15-row stub. Payroll's only SAP footprint is
hand-typed aggregate journals (`OJDT` TransType 30, memos "MAY SALARY AMOUNT",
"Salary Ziual Apr 2026") plus 510 `OCRD` rows carrying `U_Emp_Code` (JWPL####) imprest
accounts and 2,011 `JDT1` lines tagged `U_OcrCode5` (PROMOTER 1,062 / SO-SR 455 / ASM 262).
So the *money* reaches SAP as a lump; the *claim, the approver, the rejection* never do.

**C13. E-com shipment approval / deletion audit (`sp_audit_log`, `sp_deletion_log`) — N (85, live)**
Correctly bucketed by phase 1, but I must downgrade its weight: live counts are
`sp_audit_log` **0 rows**, `sp_deletion_log` **2 rows**. The module is essentially unused.
Schema-shape ruling only.

### D. Governance / workflow objects

**D1. Helpdesk tickets (JSAP, 11 cmds) — N (97, live)**
Live: `{ticketId 13, projectName "JSAP", title "Entry Not Visible in JSAP", description
"Draft Key 40513 Ap Credit memo oil Unit expense entry", status Open, priority High,
fromUserName "Ishwendra S", createdOn 2026-02-26}`. Note the description *references* a SAP
draft key — reference, not provenance. UDT check done; `OSCL`/`SCL1`/`OCTR` = 0 in all three.

**D2. Task register + progress updates + team scoping (JSAP) — N (97, live)**
GUID `taskId`, `percentComplete`, progress-update log, soft-delete audit
(`deletedBy/deletedOn/deletedReason`). `OCLG` = 0 in all three companies; no `%TASK%` UDT.

**D3. Meeting minutes / MoM (JSAP `dashboards mom`) — N (90, live)**
Endpoint live, returns `[]`. `%MOM%`/`%MINUTE%` sweep → zero SAP tables. Ruling is on the
absence side, which is what the question asks; content unobserved.

**D4. Document Hub (JSAP: folders, GUID-stored files, version history, activity log,
confidentiality PIN, backup snapshots) — N (95, live)**
`{fileId 48, "June-26.pdf", storedFileName d0eec9a8036448efa421ca974751c314.pdf,
versionNumber 1, uploadedBy Kamaljeet, isConfidential, pinCode}`. `%DOCHUB%` sweep → zero.
**Distinct from D5** — do not conflate.

**D5. SAP document attachments (`OATC` 76,062 / `ATC1` 128,739) — M (94, live)**
`ATC1` current to 2026-07-29 (`01674.xlsx`, `01674.pdf`, `PARAMDEEP-535.pdf`). Surfaced by
`jsap documents sapfile` and by the `link` field on `documents po|grpo`. The files themselves
sit on a Windows share; SAP holds the registry. No versioning, no PIN, no activity log —
that is what D4 adds.

**D6. Employee / HO org hierarchy, salary, DOJ, designation, custom fields (JSAP, 227 rows) — N (96, live-negative)**
```
SELECT COUNT(*), COUNT("salary"), COUNT("startDate"), COUNT("jobTitle"), COUNT("dept"),
       COUNT("manager") FROM JIVO_OIL_HANADB.OHEM   →  17 | 17 | 0 | 0 | 3 | 1
```
`HEM1`/`HEM2`/`OHTR` = 0. The 17 are the SAP licence-holders who act as budget approvers.
Over 90 % of the people in JSAP's org chart do not exist in SAP, and no salary, start date
or job title is recorded for the ones who do.

**D7. Sales hierarchy H1→H4 (JSAP `hierarchy sales`) — N (85, live-negative)**
`OSLP` = 155 sales employees with no chain; `OTER` = 1 default territory; and the
`OCRD.U_UNE_RSM/ASM/SO/SR/ZONE/AREA` columns exist and are **0 non-blank of 3,390**.
**Uncertainty:** JSAP's H1–H4 and DSR's `tbl_salesperson` (1,809 rows) may cover the same
people — if DSR is the origin, JSAP is a mirror of DSR, not the originator. Still N with
respect to SAP either way; the N-vs-duplicate question is unresolved.

**D8. Document dispatch / courier bundles between branches and HO (JSAP, 6 cmds) — N (78, code + live-negative)**
Re-tested live 2026-07-30: `jsap-cli documents docs --json` → `"Internal server error"`.
The module has been down through two independent audits. `%DISPATCH%` sweep → zero SAP
tables. **I never saw a row.** Ruled on endpoint semantics + SAP absence only.
⚠️ `documents bundleid` has a `mode=update` variant that mutates a counter — the CLI
hardcodes `mode=select`; do not hand-craft that URL.

**D9. App users, roles and per-module permissions (JSAP, OMS, control-panel, ecom, factory,
EXIM, DSR) — N (96, live-negative)**
SAP `OUSR` = 55 Oil / 52 Mart licence users, a different and much smaller population
(B1i, manager, SUMIT, MANSI, HARPREET…). No app's identity model, role grid, territory
scoping or page-permission matrix has any SAP counterpart.
🔒 Security note carried forward, not my call to fix: OMS `GET /api/auth/users/list/`
returns each user's pbkdf2 password hash to any authenticated caller, and those hashes sit
in the CLI's local SQLite cache.

**D10. Field-level UI audit trails (OMS `audit_log` 13,347; `orders_log` 380) — N (95, live)**
`username, page, action, record, field, old_value, new_value, user_id, created_at` for
records that mostly never reach SAP.

**D11. SAP-native change log (`ADOC` 43,054 / `ADO1` 188,592 / `ACRD` 18,311 / `AITM` 11,286) — M (95, live)**
`ADOC` current 2024-10-01 → 2026-07-29. SAP DOES audit its own documents, business partners
and items. **Not exposed by any app CLI** — this is a coverage gap in the toolkit, not a gap
in SAP. Do not tell anyone "SAP has no audit trail".

**D12. Integration run logs (EXIM `sync_logs` 342 rows; OMS `sap_sync_logs` 310) — N (96, live)**
Pure integration telemetry with no SAP analogue — and operationally the most useful thing in
either app, because both prove the mirrors are **manual, not scheduled**: all 342 EXIM rows
have `triggered_by='Manual'`; OMS `sap_sync_schedules` has **0 rows**.

**D13. JSAP inventory-audit physical counts and variance — N (94, live-negative)**
Included here because it is a *control* function. SAP's counting objects are empty:
`OINC` = 0, `OIQR` = 0, `ODPS` = 0 in `JIVO_OIL_HANADB`. `jsap inventory report KAMALPREET19`
returns `systemQty 0 / physicalQty 200 / diffQty 200 / diffLitre 1000` against SAP
`FG0000004`. A row carrying a SAP ItemCode that is 100 % native data.

---

## CONFLICTS BETWEEN PHASE-1 / PHASE-2 AGENTS — resolved

1. **`JS_SYNC_BUDGET_APPROVAL_WORKFLOW` staleness.** The `sap-custom` probe called it
   "STALE (createdOn max 2026-03-26)" and named `js_budget_approval_workflow` (86 rows) "the
   live twin". **Both halves are wrong.** `SYNC_TIMESTAMP` on the big table is
   **2026-07-30 02:50:52** — synced today, 30 distinct sync stamps; `createdOn` is the
   app-side workflow date, not a load date. And the "live twin" is the *deadest* of the
   three (max `createdOn` 2025-04-12). The genuinely current, human-readable table is
   **`tbl_Draft_Approvals`** (max DocDate 2026-07-27).
2. **`tbl_Draft_Approvals` status split.** `sap-custom` reported "961 in-flight NULL,
   332 Y/Y, 146 Y/P". Oil actually reads `VerifiedStatus` **100 % NULL**, `ApprovedStatus`
   A 1,092 / R 174 / NULL 143 / V 31. They most likely measured the Beverages copy (7,351
   rows). Use per-schema numbers, never a blended one.
3. **The domain prior itself ("rejections/pending never reach SAP") vs `sap-surface`'s
   own note that "SAP DOES hold an approval trail".** `sap-surface` was right and
   under-weighted; the prior is refuted. Resolved in favour of the live `OWDD`/`ODRF`/
   Service-Layer evidence. See the headline section.
4. **Aging: control-panel ruled M-with-overlay; EXIM ruled M outright.** Not a real
   disagreement — different companies (control-panel covers Oil/Mart/Bev; EXIM's A/R is
   Beverages only) and only control-panel bolts on the native `remark`/`actual_sp` columns.
   Both stand.
5. **`jsap bills` — N (74) vs an arguable X.** Held at N, 78. Live sequential `vchNumber`
   and an in-app HSN/warehouse master lean "keyed in JSAP"; the import hypothesis is not
   excluded. Flagged as an open question rather than dressed up.
6. **TankhaPay payroll: `portals+postsql` floated "the monthly salary GL total is a
   human-in-the-loop F"; `hana-census` ruled a flat N.** Resolved: **N**. There is no
   mechanical feeder — the GL total is a hand-keyed `OJDT` TransType-30 journal with no
   TankhaPay reference in either direction. Calling that F would imply a pipeline that
   does not exist.
7. **`sap-custom` flagged `OMS_SP_GST_INVOICE_SAP` as possibly the OMS app (conf 60).**
   Out of my domain's scope; left open, not inherited.

---

## OPEN QUESTIONS (what I did not settle)

- **The control-panel's own database was never located.** Not in the 15-DB Postgres
  cluster, engine/host unknown, app office-network-only. Every N in section B is proven
  *not-in-SAP* but not *observed-in-its-store*.
- **JSAP's own application database was never inspected** (almost certainly SQL Server on
  103.89.45.75, same box as `DSR_V6`). Same caveat for D1–D4, D6–D8, C11.
- **Does an approved `tbl_customerLimit.NewLimit` actually land on `OCRD.CreditLine`?**
  Unproven, and the `JW`-suffixed CardCodes do not exist in `OCRD`. This is the weakest
  ruling in the set (B4, 70).
- **What writes `JS_SYNC_BUDGET_APPROVAL_WORKFLOW`, and on what cadence?** `SYNC_TIMESTAMP`
  says it ran at 02:50 today; I did not find the job.
- **JSAP budget `totalAmount` 393,750 vs SAP `DocTotal` 425,250** — delta is exactly 8 % of
  the JSAP figure. Basis divergence (pre-tax vs gross?) unconfirmed.
- **`jsap documents docs|rejected|pending|history|bundleid`** has returned HTTP 500 across
  two audits. Never observed a row.
- **JSAP Sales H1–H4 vs DSR `tbl_salesperson`** — same people? If so JSAP mirrors DSR.
- **No app CLI reads `OWDD`/`ApprovalRequests`, `ADOC`, or `OVPM`.** That is a gap in the
  toolkit, and arguably the single cheapest thing to add.

---

## READ-ONLY COMPLIANCE
Every HANA statement was a `SELECT`; every Service Layer call was a `GET` plus the CLI's own
Login; every `postsql` call ran inside its enforced READ ONLY transaction; the two `jsap-cli`
calls were GET-family reads. No write, no sync trigger, no approve, no dispatch. No
credential printed. I did not call `EXIM GET /sap_sync/open-grpos/` or
`JSAP GetLastBundleId?mode=update` — both are documented GETs with write side-effects.
