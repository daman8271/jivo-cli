# FINAL RULINGS — domain: purchase / imports / vendors

Adjudicator run 2026-07-30. All SAP evidence is my own live SQL through the tunnel:
`./hana-sql/hana-sql -env connections/hana-tunnel.env "<SELECT>"`.
EXIM API was **live** for me (`./exim doctor` → reachable); JSAP was **live**; Postgres was live via `./postsql/postsql`.
Factory app API token is expired, so factory rulings use live Postgres + live HANA instead of the app API.
Read-only throughout: SELECTs and GETs only. I did **not** call `/sap_sync/open-grpos/` (the repo's HARD-RULE flags it
as a GET with a refresh side-effect) — I verified its captured payload against HANA instead.

---

## HEADLINE

**SAP owns the purchase ledger from the PO onward and nothing before it.** `OPRQ` (purchase requisitions) and
`OPQT` (purchase quotations) are **0 rows in all three companies** — I checked. Everything upstream of the PO
(indent, negotiation, contract terms, vendor onboarding) and everything physical around the goods receipt
(gate, weighbridge, QC lab, arrival slips, CoA scans, transit-shortage arithmetic) lives outside SAP.

The three big corrections I am making to phase 1:

1. **SAP *does* hold Bill of Entry and Bill of Lading references.** 789 of 15,934 Oil `OPCH` rows carry
   `U_LRNUmber` ("Bill Of Entry No.", 98 distinct values), `U_BOEDate`, and `U_InvRevEntry` ("Bill Of Lading No",
   60 distinct, e.g. `HDMUBCNA96975100`), current to 2026-07-19. Phase 1 tested three EXIM licence BoEs and got
   zero hits — but two of them are dated **2021/2022**, before SAP went live (~Oct 2024), and the third
   (`8500238`) is a *shipping bill*, not a BoE. The one EXIM licence BoE that falls inside SAP's window,
   **`5276495` (2025-10-24), sits on 22 Oil A/P invoices**. Date-window trap, exactly as `sap-surface` warned.
2. **EXIM's domestic-contract header is NOT a clean SAP mirror.** I reconciled all 47 FY2026 DC rows against
   `OPOR`/`POR1`. All 47 PO numbers exist in SAP, but in the 20 clean 1-DC-row-to-1-PO-line cases **only 5 match
   on all of vendor+item+date+qty+rate**. EXIM holds round negotiated terms (42.00 MT @ ₹158,000); current SAP
   holds executed line values (41.07 @ ₹159,327.25).
3. **Factory's GRPO feeder is live-verified, not inferred.** `grpo_grpoposting.sap_doc_entry` 24780/24783/24744/
   24754/24740 resolve exactly to `JIVO_OIL_HANADB.OPDN` DocNum 2026076622/2026076623/2026076607/2026076611/
   2026076605; the service-GRPO entries 8654/8657/8659 resolve in `JIVO_BEVERAGES_HANADB.OPDN`.

---

## SAP GROUND TRUTH FOR THIS DOMAIN (my queries)

```
JIVO_OIL_HANADB:  OPOR 4191 · OPDN 11248 · OPCH 15934 · ORPC 1530 · ORPD 110 · OIPF 525 / IPF1 534
                  OCRD CardType='S' (vendors) 2220
MART:             OPOR 2131 · OPDN 3023 · OPCH 4569        BEV: OPOR 1113 · OPDN 4533 · OPCH 3068
ALL THREE:        OPRQ = 0   OPQT = 0   ODPO = 0
ORTT (FX):        326 rows, USD+EUR only, DataSource 'I', 2024-09-30 → 2026-07-24
OPCH import tags: U_LRNUmber 789/15934 (98 distinct) · U_BOEDate 757 · U_InvRevEntry 182 (60 distinct)
                  — Beverages OPCH has NO U_LRNUmber column at all; Mart has only U_BOEDate.
```

**Rule-3 absence checks I ran myself** (M_TABLES across all three JIVO schemas):
`%TANK%` → 0 · `%LICEN%` → only `@UTL_LICENSE` (2 rows/schema; columns `U_UTL_DBUID, U_UTL_DBPWD,
U_UTL_DataBaseName, U_UTL_SERVER, U_UTL_CMPNM, U_UTL_DBTYPE, U_UTL_EXPDT, U_UTL_PORT` = **add-on software
licence config**, not an import licence) · `%DFIA% %SHIPP% %CUSTOM% %FREIGHT% %VESSEL% %CONTAINER% %IMPORT%
%SHORTAGE%` → 0 · `%ARRIVAL% %WEIGH% %GATE% %INSPECT% %CHEMIST%` → 0 · `%TRACKER% %MAKER% %CHECKER% %VOUCHER%
%PREAUDIT% %VERIF%` → 0.
**CUFD user-field checks**: `%BOE% %LICEN% %TANK% %SHORT% %IMPORT% %CONTRACT%` → only the add-on's
`LRNUmber / BOEDate / InvRevEntry` block, present on all 32 marketing-document tables. `%TRACK% %STAGE% %MAKER%
%CHECK% %AUDIT%` → nothing but a false positive on `WASTAGE` (contains "STAGE").
**@QC_O / @QC_I**: 6 and 19 rows, all created Oct-2025 by `manager`/`USER31`, `U_DocType` = Delivery / Stock
Transfer / A/R Invoice (**outbound**), one `U_DocNum` literally `123`. An abandoned outbound stub — it has
nothing to do with factory's 1,136 inbound raw-material inspections.

---

## EXIM — the "18 SAP sync endpoints", direction by direction

**Every one of them is SAP → EXIM. There is no EXIM → SAP write path.** All 100 routes in `endpoints.json` either
read SAP or write EXIM's own Postgres; the four `sap_sync` triggers all pull. Confidence 88 — I could not read
the Django backend, so a background push cannot be strictly excluded, but `sync_logs` (only PRT/PRD/DMC, all
inbound-shaped) argues hard against it.

| Endpoint family | Bucket | How I settled it |
|---|---|---|
| `open-pos` | **M** | My query: EXIM PO 220426102 PENDING_QTY 0.491 / UNIT_PRICE 148000 / BH-GJ == `OPOR` DocEntry 11008 + `POR1` OpenQty 491/1000, Price 148000, WhsCode BH-GJ. Exact. |
| `open-grpos` (not wired) | **M** | Captured payload `{GRPO Number 2026076640, Vendor Ref No "190826018899", User Name "KULBIR SINGH", AWL AGRI, BH-GJ}` == `OPDN` DocNum 2026076640 / NumAtCard 190826018899 / OUSR.U_NAME KULBIR SINGH. Second row matched too. Verified **without** calling the endpoint. |
| `open-ap` | **M** | phase-1 live match DocEntry 4400 → OPCH 220520405 / VENDA001048 / ₹10,556 / status O. |
| `balance-sheet`, `vendor-balance-sheet` | **M** | 8/8 exact vs `OCRD.Balance` incl. MIGASA −4,984,542.1948. |
| `vendor-ledger`, `customer-ledger` | **M** (85) | Field names are `OJDT`/`JDT1` columns; never pulled live. |
| `open-ar`, `customer-aging-balance`, `custa-balance-sheet` | **M** | 1168 rows / ₹70,968,752.14 == `JIVO_BEVERAGES_HANADB.OINV` to the paisa. **EXIM is a two-company SAP window** — nobody had documented that. |
| `inventory`, `finished-inventory` | **M** | `SUM(OITW.OnHand)` by warehouse × `OITM.U_Sub_Group`. |
| `planned-months`, `monthly-planning` | **M** | Response keys are the complete `OFCT` column list, 24 rows = 24 rows. |
| `rm/items`, `fg/items`, `party/{code}` (POST triggers) | **M, stale** | `sync_logs` live: **342 runs, all `triggered_by = "Manual"`**. Last PRD 2026-07-18, last PRT **2026-06-12**, last DMC 2026-03-26. |

---

## THE RULINGS

### M — fetching it here is fetching it from SAP

- **Open POs / open GRPOs / open A/P / vendor balances / vendor ledger** (EXIM `sap-sync`) — verified above.
- **SAP purchase documents in JSAP** (`documents po|grpo|apdraft|gr`). My verification: JSAP GRPO rows
  DocEntry 9100/10264/10266/10352/8808 == `OPDN` DocNum 2025056814/2025066705/2025066706/2025066749/2025056687,
  CardCode, DocDate and DocTotal all exact, 5/5. **Filtered subset**: JSAP returns 7,123 Oil GRPOs vs SAP 11,248
  (63%) and 3,503 Bev vs 4,533 (77%); POs 3,441 vs 5,304. Never count with it.
- **Vendor / BP master** in EXIM (`parties`, 137 rows, 7 weeks stale), JSAP (`bpmaster`, 14 cmds) and factory
  (`po vendors`, 215 rows). SAP has 2,220 vendors in Oil alone. Every one of these is a lossy, stale subset.
- **Bill of Entry / Bill of Lading reference on the A/P invoice** — the one import fact SAP genuinely holds.
  Hand-typed and dirty: values include `5976233)` with a stray paren and `6720426,6815125` comma-joined.
- **Posting configuration** (GL accounts, tax codes, branches, SAC codes, projects, locations) served by
  factory `grpo service-options` — 992 GL accounts, 24 tax codes, 8 branches, 573 SAC codes = `OACT/OVTG/OBPL/
  OPRJ/OLCT`. Pure SAP config.
- **Received-vs-billed reconciliation** (factory `warehouse wms-billing-overview`) and **Wellness↔Mart
  intercompany PO/SO/GRPO/AP chains** (control-panel `inventory reconciliation`) — category (c): **new
  calculation over SAP data**. The maths is the product; the facts are all SAP's.
- **EXIM domestic-contract PO identity** (`dc` po_number/po_date/vendor_code/product_code). All 47 FY2026 PO
  numbers resolve in `OPOR`; vendor agrees 40/47, item 36/47, date 36/47. SAP is authoritative; EXIM's copy is
  dirty.

### F — originates here, then posted into SAP (SAP keeps the skeleton, the app keeps the trail)

- **Material GRPO posting** (factory `grpo`): 265 postings, 232 with a SAP doc number, 2026-03-11 → **2026-07-28**,
  live-verified into `OPDN` in both Oil and Beverages. What SAP never sees: the QC inspection that authorised it
  (1,136 inspections, 10,740 lab parameter readings), the arrival-slip CoA/CoQ photos, the gate entry, the truck
  and driver, the weighbridge tare, the **rejected** quantity and its reason, and 232 attachments.
- **Service / freight GRPO posting** (factory `grpo service-*`, `dispatch bilty-grpo-*`): 158/158 pushed, verified
  into Beverages `OPDN`. **Dormant since 2026-06-15** — six weeks with no posting.
- **A/P invoice budget approval** (JSAP `reports`): SAP draft `ODRF` 51648 → JSAP approval by Jasbir Singh at
  stage "factory oil v5 1" → posted `OPCH` DocEntry 47577 carrying `draftKey = 51648`. The trail lives in custom
  HANA tables (`js_budget_approval_workflow`, `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` 29,212 rows, `tbl_Draft_Approvals`
  1,440) that **the Service Layer and `sapb1` cannot see**. Also: JSAP `totalAmount` 393,750 ≠ SAP `DocTotal`
  425,250 (delta is exactly 8%). Never mix them.
- **Vendor onboarding** (`ZVENDOR_PORTAL`, 49 rows, in the SAP schema but not a SAP object, and **no CLI in this
  repo reads it** — I grepped). 44 APPROVED all carry `SAP_CARD_CODE`; 3 REJECTED and 2 PENDING carry none. 66
  columns: GSTIN, PAN, TAN, TDS category/rate/LDC certificate, MSME type, FSSAI, BANK_ACCOUNTS, ATTACHMENTS, a
  full `MGR_*` review block, and `VERIFIED_BY/AT` + `APPROVED_BY/AT` + `REJECTED_BY/AT`. This is the cleanest
  M/F/N boundary in the whole business, visible in one table.

### N — genuinely new; SAP has no object for it (each one Rule-3 checked above)

- **Import stock lots + 9-stage lifecycle** (IN_CONTRACT → ON_THE_SEA → MUNDRA_PORT → ON_THE_WAY → UNDER_LOADING
  → AT_REFINERY → IN_TANK → OUT_SIDE_FACTORY → COMPLETED). SAP has no in-transit object; EXIM's lot item codes
  are absent from `OITM`.
- **Tanks, tank item master, tank in/out logs.** Zero `%TANK%` tables in any schema. 32 tanks, 13,51,500 L
  capacity, 8,55,700 L held, 63.31% utilisation — a number SAP structurally cannot produce.
- **DGFT Advance Authorisation / DFIA licence register.** SAP holds the BoE *number* (see M above) but nothing
  else: no licence number, no issue date, no import/export validity, no CIF/FOB in INR+USD with their exchange
  rates, no export-obligation `total_import / total_export / to_be_exported / balance`, and no shipping-bill
  export lines (I checked `OINV.Comments`/`NumAtCard` for shipping bills 6611229 and 8361972 → 0 hits).
  Live sample: licence 511015224, CIF ₹3.75 cr @ 80.40, FOB ₹4.5 cr @ 78.20, obligation 250.002 MT, balance 7.482 MT.
- **Transit-shortage / debit register** (EXIM `stock-status get-debit-entries`). Live: 150 rows, 95 with a
  deduction, **₹8,49,907 total**, 2026-04-25 → 2026-07-29, each with load vs unload MT, tolerance, deducted MT
  and rupees, vehicle and transporter. I tested the obvious counter-hypothesis: SAP `ORPC` for the same ten
  vendors in the same window has memos for **only two** of them (VENDA000224: 46, VENDA001695: 17) and **none at
  all** for VENDA000930/000614/001203/000279/000599/001035/000149/000252, where EXIM holds 19/14/13/9/1/1/2/1
  deductions. For VENDA000224 the amounts do not overlap either (SAP repeats round values 15,698 / 18,837 /
  21,977; EXIM computes 180.69 … 8,833.50).
- **Domestic-contract negotiated terms** (`contract_qty`, `contract_rate`) and the whole logistics overlay
  (load/unload, shortage, allow_shortage, deduction, transporter, bilty, freight, brokerage).
- **Inbound QC inspection** — two-signature chemist + QA-manager workflow, 1,136 inspections / 10,740 parameter
  readings / 46 rejected / 46 returned-to-vendor in Oil alone. SAP's QC stub is 6 abandoned outbound rows.
- **Material arrival slips + CoA/CoQ scans** (1,202 slips, 1,175 attachments), **gate vehicle arrivals** (666)
  and **weighbridge weighments** (1,720).
- **Inbound vendor-invoice tracker** (OMS `tracker_*`): 8 stages Head Office In → Bilty/GRPO → Pre-Audit
  (OK/HOLD/DEBIT/RETURN) → Data Entry → SAP Approval → JSAP Approval → **Save in SAP** → Payment. The module
  exists to record what happens *before* SAP. Carries `debit_amount`, `hold_amount`, `rejection_pending`.
- **Bill-verification vouchers + maker/checker/payment trail** (JSAP `bills`). Live now: 971 bills, 41 pending
  maker, 851 approved checker, 435 paid; latest voucher 973 dated 2026-07-29 (G.S. Handloom ₹26,030, Akal
  Catering Mess ₹200/₹250/₹1,000). **These are not JIVO's books at all** — Baru Sahib / Akal institutional
  supply. 6 of 100 account names generic-match `OCRD` across all three schemas; line items ("Mattress Single",
  "Gs Pillow") match 0 rows in `OITM`; warehouse "Ary Warehouse" matches 0 rows in `OWHS`.
- **Physical-bill courier dispatch bundles** (JSAP `documents docs/rejected/pending/history`) — HTTP 500 in both
  audits, so schema/code evidence only.
- **Our-Rates pricing engine** (commodity margin, packing margin, pack sizes) and **EXIM sync-run log**.
- **Purchase requisition / indent stage generally** — nothing in SAP to mirror: `OPRQ` = `OPQT` = 0 everywhere.

### X — external feeds

- **CBIC customs exchange rates** (`exim-rates`). Live: notification **22/2026** dated 2026-07-17, Euro
  **import 112.35 / export 108.60**, 23 currencies each with two legs. SAP `ORTT` for the same week: EUR
  2026-07-14 and 07-21 = 110.65, 07-23 = 109.228, 07-24 = 109.10 — one rate, no legs, no notification number.
  Different numbers for a different purpose (duty assessment vs booking).
- **Daily commodity market prices** (`daily-price`, 13 oils) — pulled from a published Google Sheet
  (`GET /daily-price/fetch/`), `created_by` = `System`/`backup`. Commodity names ("Soya DO", "Palmoline",
  "Ricebran DO") match no SAP item.

### U — I could not determine

- **EXIM `items/rm` stock aggregates** (`total_qty`, `total_in_qty`, `total_out_qty`, `total_trans_value`).
  SAP-shaped, SAP item codes, but they reconcile to neither `OITW.OnHand` nor the `OINM` net (RM0000003: EXIM
  132,814 vs SAP 177,809; RM0000025: 85,247 vs 200,593). I could not reproduce the filter. **Never quote these
  as SAP stock.**

---

## CONFLICTS I RESOLVED

1. **`dc` header — phase 1 said M/88 from one lucky row; I say the terms are N.** My 47-row reconciliation:
   qty agrees 20/47, rate 22/47; in the 20 clean 1:1 cases only 5 match on all five fields. I then checked SAP's
   own change log — `ADO1` LogInstanc 1 for PO 220526038 shows Price **158,000**, exactly EXIM's `contract_rate`,
   while current `POR1` shows 159,327.25. So the *rate* is recoverable from SAP history; the *round contracted
   tonnage* (42.00) never existed in SAP at all (SAP rev-1 = 41.415). Ruling: PO identity **M**, negotiated terms
   and logistics overlay **N**.
2. **Licence BoEs — phase 1 said "SAP has 0 matching"; that was a date-window artefact.** SAP holds 98 distinct
   BoEs and EXIM's licence BoE 5276495 is on 22 SAP A/P invoices. Ruling: licence register **N**, BoE reference **M**.
3. **`grpo_number` reliability on EXIM rows — phase 1 saw only junk ('123','124','125') and one off-by-3.**
   I checked three recent ones: 2026056539 → VENDA000614 ✓, 2026056558 → VENDA000930 ✓, 2026056559 → VENDA001571 ✗.
   So recent references are roughly 2-in-3 correct, not pure noise — but still unsafe as a join key.
4. **Repo docs vs reality on factory GRPO.** `factory-cli/DATA-MODEL.md` says "0 GRPOs have ever been posted".
   Live Postgres says 232 posted, latest 2026-07-28, and I resolved five of them in SAP. Doc loses.
5. **"F bucket is empty" (EXIM) vs "F everywhere" (factory/JSAP/portal).** Not a contradiction — EXIM genuinely
   has no write path, while factory, JSAP and the vendor portal all post into SAP. The domain has feeders; EXIM
   is not one of them.
6. **`portals+postsql` gave DB-level shorthand ("factory_flow = F") over factory-cli's entity rulings.** No
   conflict of substance; factory-cli's per-entity calls stand, and I live-verified the two that matter.

## OPEN QUESTIONS

- What EXIM's `DMC` sync actually imports (390 records, last run 2026-03-26). If it is the SAP-PO → domestic-contract
  importer, the DC header's provenance is settled; DC rows created after March 2026 still resolve to real POs,
  which suggests hand-keying plus a one-off historical load.
- Whether EXIM's shortage deductions are **netted inside** the A/P invoice amount in SAP rather than raised as
  separate credit memos. I proved they are not separate `ORPC` documents; I could not prove they are not netted.
- What SAP's recurring round `ORPC` amounts for VENDA000224 (15,698 / 18,837 / 21,977, one per gate entry) actually
  represent. They are *not* EXIM's shortage figures.
- Whether JSAP `bills` vouchers are keyed by the maker (N) or imported from a Marg/Busy-style package (X). The
  field shapes (`serialNumber "17115.0015"`, `hsnsacid`, `margin`, `taxName "Input Gst 5%(Exclu)"`) look like an
  export. Either way they are not JIVO SAP data.
- The OMS invoice tracker's production volume — the only reachable Postgres instance is dev/UAT (13 invoices).
- Factory's SAP posting transport (Service Layer vs DI API) — the doc numbers land, the pipe is unidentified.
- `ZVENDOR_PORTAL` / `ZCUST_PORTAL` are reachable only by direct HANA SQL. Nothing in this toolkit exposes them.
