# ADVERSARIAL VERIFICATION — domain `purchase-imports-vendors`

Refuter pass, 2026-07-30. Every claim below was re-tested from scratch against live systems.
I did not read the phase-2 agent's queries and re-run them; where I re-derived the same number
I say so, and where I used a *different method* and got a different answer I say that too.

**Access note that cost me 10 minutes:** `connections/hana.env` points at the office-whitelisted
direct host and hangs silently from home. The working file is `connections/hana-tunnel.env`.
All HANA queries below were run as:

```bash
cd /Users/damanpreetsingh/jivo-cli
./hana-sql/hana-sql -env connections/hana-tunnel.env "<SQL>"
```

`factory-cli` is **dead** (`doctor` → `FAIL Credentials: invalid (HTTP 401)`), so every
factory-cli-fronted ruling stayed at code/schema evidence. I compensated by attacking the
factory rulings through Postgres (`factory_flow`) and HANA instead.

---

## HEADLINE: ONE RULING IS FLATLY WRONG, AND IT IS THE EXPENSIVE KIND

### Transit-shortage / debit register: ruled `N`, actually `F`

Phase 2 concluded SAP holds nothing for transit shortage, and backed it with:
"SAP ORPC for the same ten vendors over the same window has memos for only TWO of them".
That is a true sentence about the **wrong population**. The shortage is not charged back to the
oil supplier. It is charged back to the **transporter**.

```sql
SELECT T1."Dscription", COUNT(*) FROM "JIVO_OIL_HANADB"."RPC1" T1 GROUP BY ... ;
-- "SHORTAGE CHARGES" = 75 lines, and 85 ORPC headers carry SHORT/SHORTAGE in Comments
```

Full population:

```sql
SELECT COUNT(*) LINES, COUNT(DISTINCT T0."DocEntry") DOCS, SUM(T1."LineTotal") TOTAL,
       MIN(T0."DocDate"), MAX(T0."DocDate")
FROM "JIVO_OIL_HANADB"."ORPC" T0
JOIN "JIVO_OIL_HANADB"."RPC1" T1 ON T1."DocEntry"=T0."DocEntry"
WHERE UPPER(T1."Dscription") LIKE '%SHORTAGE%';
-- 544 lines · 164 documents · Rs 38,56,015.29 · 2024-10-22 → 2026-07-16
```

By counterparty — every one a transporter, none an oil supplier:
R K TANKER SERVICE 425 · SS LOGISTICS 36 · ARSH TRANSPORT 27 · PALAK TANKER 22 ·
BALMUKUND ROADWAYS 14 · SHREENATH LOGISTICS 7 · SHREE BHOLENATH 5 · TEJAJI 4 · +4 more.

Restricted to EXIM's exact window (2026-04-25 → 2026-07-29): **54 lines, Rs 5,82,143.72**.
EXIM live (`exim stock-status get-debit-entries`): **150 rows, 95 with a deduction,
Rs 8,49,906.91**.

Then the kill shot. SAP puts the **truck number and the rate inside the line description**
("SHORTAGE CHARGES FROM RADHANPUR TO SONIPAT @3500 RJ47GA6771"). I regex-extracted the
vehicle numbers from the 54 SAP lines and joined them to EXIM's register:

| Vehicle | SAP credit-memo line | EXIM `deduction_amount` |
|---|---|---|
| RJ47GA7522 | 44,638.69 | **44,638.688** |
| RJ47GA8215 | 43,874.00 | **43,874.00** |
| RJ47GA8216 | 38,151.00 / 10,067.00 | 38,151.07 / 10,066.62 |
| RJ47GA8217 | 37,862.00 | 37,866.76 |
| RJ47GB2009 | 9,956.68 / 5,092.50 | **9,956.68 / 5,092.50** |
| RJ47GA7520 | 8,623.56 | **8,623.56** |
| RJ47GA7523 | 8,134.50 | **8,134.50** |
| RJ47GA7522 | 8,097.00 | 8,097.38 |
| RJ47GA1956 | 6,508.00 | 6,507.57 |
| RJ47GA7911 | 6,209.00 | **6,209.00** |
| RJ14GQ1756 | 3,726.95 | **3,726.95** |
| RJ47GA6770 | 2,236.50 | **2,236.50** |
| RJ47GB1956 | 2,322.00 | 2,321.78 |
| RJ47GB3056 | 7,275.00 | 7,275.38 |

18 of EXIM's 63 vehicles appear in the SAP descriptions; 19 vehicles appear in SAP, only one
of which (RJ47GA0492) is absent from EXIM. And the clincher: **the minimum and maximum of the
two datasets are the same two numbers** — SAP min 60.562 / max 44,638.69, EXIM min 60.563 /
max 44,638.688.

**Ruling: REFUTED. `N` → `F`.** EXIM computes the shortage; the rupee outcome is posted into
SAP as an A/P credit-memo line against the transporter, roughly 2–4 weeks later (SAP's latest
shortage memo is 2026-07-16, EXIM's register runs to 07-29 — which explains SAP 5.82 L vs
EXIM 8.50 L). What SAP genuinely never gets: `load_qty`, `unload_qty`, `shortage_qty`,
`allowed_shortage_qty` (the contractual tolerance), `deducted_shortage_qty` in MT, the item, and
the ~55 within-tolerance trips that produce no document at all.

**Knock-on:** the same correction applies to the shortage/deduction half of the domestic-contract
overlay (`deduction_amount`, `deduction_qty`, `shortage`, `allow_shortage` on `dc`).

---

## SECOND FINDING: SAP KNOWS THE TRUCK. THREE RULINGS SAY IT DOESN'T.

`CUFD` defines `U_VehicleNoM`, `U_DriverName`, `U_TransporterName`,
`U_TransporterInvoice` ("Gate Pass No."), `U_BilltyNumber` / `U_BiltyDate` / `U_BiltAmt` and
`U_Total_Gross_Wt` on **all 32 marketing-document headers**, including `OPDN` and `OPCH`.
Population (Oil):

```sql
SELECT COUNT(*) TOT, COUNT("U_VehicleNoM") VEH, COUNT("U_TransporterName") TRN,
       COUNT("U_BilltyNumber") BILTY, COUNT("U_TransporterInvoice") GATEPASS,
       SUM(CASE WHEN "U_Total_Gross_Wt">0 THEN 1 ELSE 0 END) GWT_NONZERO
FROM "JIVO_OIL_HANADB"."OPDN";
-- OPDN 11,248 | VEH 663 | TRN 839 | BILTY 881 | GATEPASS 8 | GWT_NONZERO 0
-- OPCH 15,934 | VEH 1,031 | BILTY 1,024
```

Overall coverage is only ~6%, **but it is 100% on exactly the vendors that matter**:

```sql
SELECT "CardCode", COUNT(*) TOT, COUNT("U_VehicleNoM") VEH FROM "JIVO_OIL_HANADB"."OPDN"
WHERE "DocDate">='2026-04-01' GROUP BY "CardCode";
-- VENDA000224 (AWL) 69/69 · VENDA000930 (VAISHNODEVI) 30/30
```

Live sample, 2026-07-29: OPDN 2026076812, VAISHNODEVI, `U_VehicleNoM` RJ47GA7523,
`U_TransporterName` R.K. TANKER SERVICE, `U_BilltyNumber` 8568.

So "SAP will show you the goods receipt, never the truck" is false for the raw-material tanker
fleet. What SAP genuinely lacks is the **weighbridge**: `U_Total_Gross_Wt` is a defined DECIMAL
field and is **zero on all 11,248 rows** — and `U_BiltAmt` likewise. `GRPO_GATEPASS` (a HANA
stored procedure in Oil and Beverages) computes "Gross Weight" as
`Quantity × OITM.U_Gross_Weight` — a theoretical weight, not a weighment.

Affected: the material-GRPO `F` ruling, the service-GRPO `F` ruling, and the arrival-slip/gate
`N` ruling. Buckets survive; the "fields SAP lacks" lists do not.

---

## THIRD FINDING: THE PURCHASE-CONFIG MIRROR NAMES TWO EMPTY TABLES

Ruling: factory `grpo service-options` returns 992 GL accounts / 24 tax codes / 8 branches /
573 SAC / 18 projects / 7 locations from `OACT, OVTG, OBPL, OPRJ, OLCT`.

```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM M_TABLES
WHERE SCHEMA_NAME LIKE 'JIVO%' AND TABLE_NAME IN ('OACT','OVTG','OBPL','OLCT','OPRJ','OSTC','OSAC');
```

| Table | Oil | Mart | Bev | Ruling claim |
|---|---|---|---|---|
| `OACT` | 1,424 | 1,104 | 764 | 992 gl_accounts |
| `OVTG` | **0** | **0** | **0** | 24 tax_codes ← **impossible** |
| `OSTC` | 23 | **24** | 24 | ← the real source |
| `OSAC` | 614 | **573** | 576 | 573 SAC ← exact on Mart |
| `OBPL` | 8 | 8 | 6 | 8 branches |
| `OLCT` | 5 | **7** | 5 | 7 locations ← exact on Mart |
| `OPRJ` | **0** | **0** | **0** | 18 projects ← **no SAP home at all** |

Two of the five named objects are empty in every company. The real homes are `OSTC` (tax codes)
and `OSAC` (SAC codes), and **the 18 "projects" cannot come from SAP** — `OPRJ` is empty
everywhere. Note also that tax_codes=24, SAC=573 and locations=7 all match **Mart**, not Oil, so
the config endpoint is reading the Mart company.

I did confirm the M *direction* independently: `factory_flow` has no cached master —
`postsql -d factory_flow search gl_account` returns only three transactional line tables
(`grpo_servicegrpolineposting`, `dispatch_plans_transporterapinvoiceline`,
`raw_material_gatein_poitemreceipt`), and no project/tax/branch/SAC table exists.

**Ruling: bucket `M` upheld, `sap_object` mapping REFUTED, and the 18 projects are not SAP data.**

---

## FOURTH FINDING: THE DGFT LICENCE PAPERWORK *IS* IN SAP — AS PDFs

The licence ruling checked tables, columns and `OINV.Comments`. It never checked the attachment
registry. `ATC1` (Oil) = 128,739 rows:

```sql
SELECT DISTINCT "FileName" FROM "JIVO_OIL_HANADB"."ATC1"
WHERE UPPER("FileName") LIKE '%DGFT%' OR UPPER("FileName") LIKE '%DFIA%'
   OR UPPER("FileName") LIKE '%AUTHORIS%' OR "FileName" LIKE '%5276495%'
   OR "FileName" LIKE '%511015224%';
```

Hits include:
- `Jivo Wellness Mail - Re_ CLOSURE DOCS - 0511015224 - ADV LIC (250 MTS)` — **EXIM's own
  licence 511015224, with its 250 MT export obligation, and its closure documents**
- `Jivo Wellness Mail - Re_ NEW DFIA FILE NUMBER - 05DA07600247A`
- `BOE ASSESSED COPY 5276495 DT 24.10.25` — **EXIM's BoE 5276495, EXIM's date**
- 44 DGFT-named documents in total, plus 413 filenames containing "BOE"
  (`BOE-OOC`, `BOE OOC-7953217`, `ASSESSED BOE-5622622 DT 16.09.24`)

The **register** (obligations, CIF/FOB, balances, shipping-bill lines) is still EXIM-only, so the
bucket holds. But "SAP has no trace of the licence" is wrong, and anyone asked "where is the
advance-licence file" should be sent to SAP's attachment share first.

Counter-check on the same method, to be fair to the other N rulings:
- 324 `%TANK%` filename hits are **all** "R.K. TANKER SERVICES / PALAK TANKER TRANSPORT" payment
  approvals — no storage-tank documents. Tank ruling survives.
- 34 `%QC%/%QUALITY%/%INSPECT%` hits are "EXPORT INSPECTION BILL" and one `Quality.xlsx`;
  18 `%WEIGH%/%KANTA%` hits are vendor names (E.G Kantawalla, TRUE WEIGH DIGITAL TECHNOLOGIES).
  **No inbound CoA, no weighbridge slip.** QC and weighbridge rulings survive.

---

## FIFTH FINDING: THE `OIPF` OPEN QUESTION IS CLOSED — AND IT HELPS THE `N`

Phase 2 left "what is in SAP's landed-cost documents (OIPF 525 / IPF1 534)" open, and flagged it
as the thing that could overturn the import-lot `N`.

```sql
SELECT COUNT(*) N, COUNT(DISTINCT "CardCode") VENDORS,
       SUM(CASE WHEN "BillOfLad" IS NOT NULL AND "BillOfLad"<>'' THEN 1 ELSE 0 END) HASBOL,
       SUM(CASE WHEN "ActCustom"<>0 THEN 1 ELSE 0 END) HASCUSTOM,
       SUM(CASE WHEN "DocCur"<>'INR' THEN 1 ELSE 0 END) FCUR
FROM "JIVO_OIL_HANADB"."OIPF";
-- 525 · 49 vendors · BillOfLad 0 · ActCustom 0 · non-INR 0
```

Every row is INR, none carries a Bill of Lading, none carries a customs amount, and every
`Descr` reads `Based On Goods Receipt PO 20260766xx,` against **domestic** oil suppliers
(VAISHNODEVI, DHANLAXMI). SAP's landed-cost module is being used for **domestic inbound freight
costing**, not import costing. The import-lot `N` is stronger than phase 2 could claim.

---

## THE REST, TESTED

**Re-derived exactly (independent queries, same numbers):**
- `OPRQ` 0/0/0, `OPQT` 0/0/0, `ODPO` 0/0/0 — SAP's purchase trail really does begin at the PO.
- `OPCH` Oil 15,934 · `U_LRNUmber` 789 (98 distinct) · `U_BOEDate` 757 · `U_InvRevEntry` 182
  (60 distinct). The phase-2 BoE correction is exact.
- `OCRD` Oil: CardType S = 2,220, C = 1,170.
- `ZVENDOR_PORTAL`: APPROVED 44 (44 pushed) / REJECTED 3 (0) / PENDING 2 (0), 2026-04-02→06-05.
- `@QC_I` 19, `@QC_O` 6. `tbl_Draft_Approvals` 1,440 · `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` 29,212
  · `js_budget_approval_workflow` 86 · `jsDocEntries` 535.
- `factory_flow.grpo_grpoposting` 265 / 232 with `sap_doc_entry` / 2026-03-11→2026-07-28;
  `grpo_servicegrpoposting` 158 / 158 / 2026-05-20→2026-06-15 (dormant, confirmed).
  Resolved `sap_doc_entry` 24740/24742/24744/24748/24780/24783 → `OPDN` DocNum
  2026076605/06/07/09/22/23 exactly. (Note: all six are **packaging** vendors — TPAC, PARAMBA
  POLYMER, MULTILAYER, RAJ TECHNOPACK — this feeder is packaging material, not oil.)
- OMS `tracker_stage`: 8 rows, exactly the documented pipeline including stage 6 "Save in SAP".

**Live pass-through re-verified field-for-field:**
- `exim sap-sync get-open-pos` → PO 220426102 / VENDA000224 / RM0000003 / 250 / open 0.491 /
  148000 / BH-GJ == `OPOR` DocEntry 11008 + `POR1`. `OPEN_VALUE` 72,668 = 0.491 × 148,000. ✔
- `exim sap-sync get-open-ap` → "DB Primary Key" 48578 / invoice 626074225 / GST 291,976.25 /
  bilty 16041 dated 2026-07-18 == `OPCH` DocEntry 48578 (DocTotal 6,125,661, VatSum 291,976.25,
  DocStatus O, `U_BilltyNumber` 16041, `U_BiltyDate` 2026-07-18). ✔
- `exim sap-sync get-balance-sheet` → VENDA001347 −50,604,960 and VENDA001490 −45,000,004
  == `OCRD.Balance`. ✔
- `exim sap-sync get-vendor-ledger --card-code VENDA000224` → **upgraded from `code` to `live`.**
  223 rows; VoucherNo 726303912 / SourceDocNo 726466919 / DocType 46 / Debit 3,309,196 /
  "Outgoing Payments - VENDA000224" == `OJDT` TransId 222946, Number 726303912, TransType 46,
  BaseRef 726466919, and `JDT1` line VENDA000224 Debit 3,309,196. ✔
- `jsap documents grpo` → 10,626 rows; DocEntry 9100/10264/10266 == `OPDN` DocNum
  2025056814/2025066705/2025066706, VENDA000636 DELHI PUNJAB TRANSPORT CO, 9,909/32,000/13,000. ✔
- `jsap bpmaster chains` → 46 rows == `@CHAIN` Oil 46. ✔

**New correction on the JSAP document feed:** the command is documented as "**Open** GRPOs", but
all three sampled rows are `DocStatus = 'C'`, and SAP Oil has only **356** open GRPOs against
10,892 closed. JSAP returns 7,123 Oil rows. "Open" is a lie in the label, not just a filtered
subset — nobody should read that feed as a pending-receipts queue.

**Domestic contracts — re-reconciled by a different method, same conclusion.** Phase 2 compared
one DC row to one PO *line* and got 5/20. I compared each DC to the **PO-level aggregate**
(sum of `POR1.Quantity`, min/max `Price`), which is the friendlier test:

```
35 EXIM POs → 35/35 exist in SAP
vendor matches 32/35 · po_date 26/35 · contract_qty vs SAP PO total 12/35 ·
contract_rate equals SAP min or max price 18/35 · all four together 10/35
```

The pattern is unmistakable and systematic: EXIM holds round negotiated figures
(40.00 / 42.00 / 210.00 / 540.00 @ 158,000 / 160,000 / 148,000) and SAP holds executed values
(39.94 / 41.07 / 124.96 / 500.00 @ 159,327.24 / 161,502.25 / 148,229.22). I independently
reproduced phase 2's specific anomalies: PO 326226520 & 326226525 name VENDA000252 in EXIM and
VENDA000930 in SAP; PO 220426027 is 2000 @ 370 in EXIM and 2 @ 370,000 in SAP; and PO 326226556
is a flat disagreement (EXIM VENDA000930 168 @ 144,200 vs SAP VENDA001203 525 @ 1,220.76).
**Upheld, confidence raised 82 → 90.**

**Things I could not test, stated plainly:**
- `control-panel` intercompany reconciliation — no access from here. UNPROVEN.
- factory `warehouse wms-billing-overview` / `grpo preview` — factory-cli 401. UNPROVEN.
- `jsap documents docs/rejected/pending/history/bundleid` — all five returned
  `"Internal server error"` for me, exactly as in both prior audits. **I have never seen a row.**
  UNPROVEN; the `N` is a name inference.
- `jsap documents sapfile` — I did not stream a binary. UNPROVEN.
- `exim sap_sync/open-grpos` — deliberately not called (HARD-RULE: GET with a SAP-refresh side
  effect). I only confirmed the SAP side (`OPDN` O=356 / C=10,892).
- `exim daily-price` — the ingest route is a write under HARD-RULE; not called, sheet not opened.
- `exim items get-rm` aggregates — I did not attempt to resolve them either. Still `U`.

**Volume caveat I can now make sharper than phase 2 did:** the OMS inbound-invoice tracker holds
**13 rows** in `order_management` — which is the 54 MB *production* database, not a UAT box. The
schema argument for `N` is sound; the module is effectively unused, so nobody should build on
its "richer detail" without checking whether anyone keys it.

**Also worth knowing:** EXIM's item namespace is entirely its own. `RM0RB02`, `RM0CCNT`,
`RM00CN`, `RM00GNR`, `RM00MDEO`, `RM00C01`, `RM000MR`, `RMMKG01`, `RM00SBR` all return **zero**
rows from `OITM`, which holds only 64 `RM%` items in Oil. That is a hard structural wall between
EXIM's lot/tank world and SAP's item master.
