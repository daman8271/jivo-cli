# SAP CUSTOM MAP — where JIVO's non-standard data hides inside SAP

Probe: `sap-custom`. Agent: SAP ground-truth. Date: 2026-07-30.
All evidence below is **live SQL** against production SAP HANA through the tunnel
(`127.0.0.1:13015`), unless a line says otherwise.

Tool used for every query in this file:

```
/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql \
  -env /Users/damanpreetsingh/jivo-cli/connections/hana-tunnel.env "<SQL>"
```

(the plain `connections/hana.env` **hangs** — it points at the non-tunnelled host.
Use `hana-tunnel.env`. `-f file.sql` for multi-line.)

Scale: `JIVO_OIL_HANADB` 3,111 tables / 411 views / 708 procedures ·
`JIVO_MART_HANADB` 3,046 / 351 · `JIVO_BEVERAGES_HANADB` 3,087 / 234.
Only schemas on the box: the three JIVO ones, `TEST_OIL_15122025`, `ZIA` (the add-on's
own schema), and `SYS`/`_SYS_*`. **There is no staging schema, no middleware schema,
no B1if schema.** Every app<->SAP bridge that exists is a table, view or stored
procedure sitting *inside the company schema itself.*

---

# 0. THE CHECKLIST — read this before you call anything `N`

If you are about to rule a domain "not in SAP", check these six places first. Each one
has burned an assumption already.

| # | Place | Query to run | Why it bites |
|---|---|---|---|
| 1 | **Custom tables inside the SAP schema** | `SELECT TABLE_NAME,RECORD_COUNT FROM M_TABLES WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND (LENGTH(TABLE_NAME)>8 OR TABLE_NAME LIKE '%\_%' ESCAPE '\') AND RECORD_COUNT>0` | `ZVENDOR_PORTAL`, `ZCUST_PORTAL`, `ZBOM_REQUESTS`, `tbl_Draft_Approvals`, `PRODUCTIONORDERSYNC`, `JS_SYNC_BUDGET_APPROVAL_WORKFLOW`, `JIVO_WA_MESSAGE_LOG` are all app working-state, **physically inside SAP**, invisible to the Service Layer. §2 |
| 2 | **`@` UDTs** | `SELECT TABLE_NAME,RECORD_COUNT FROM M_TABLES WHERE SCHEMA_NAME='…' AND TABLE_NAME LIKE '@%'` | 60 registered UDTs in Oil. `@UTL_MDEXTH` (17,695 rows) holds **every e-invoice IRN/AckNo/QR**. `@ITEM_*`/`@BRAND`/`@CHAIN`/`@MAIN_GROUP` are JIVO's product & party taxonomy. §3 |
| 3 | **`U_*` user fields** | `SELECT "AliasID","Descr","TableID" FROM "…"."CUFD"` | 5,572 field definitions on 278 tables in Oil. `U_Emp_Code` on OCRD carries **JWPL#### HR employee codes**. `U_TYPE`/`U_Sub_Group`/`U_Variety`/`U_Brand` on OITM are 100% populated. §4 |
| 4 | **Purpose-built views** | `SELECT VIEW_NAME FROM SYS.VIEWS WHERE SCHEMA_NAME='…' AND VIEW_NAME NOT LIKE 'B1\_%' ESCAPE '\' AND VIEW_NAME NOT LIKE 'DV20%' AND VIEW_NAME NOT LIKE 'ES\_%' ESCAPE '\'` | `D_FACTORY_PRODUCTION`, `D_FACTORY_DISPATCH`, `D_FACTORY_BILLED_LITRES`, `view_whatsapp_bot`, `DISPATCHES_OIL`, `GRPO_BARCODE` — named after apps, built for apps. §5 |
| 5 | **Custom stored procedures** | `SELECT PROCEDURE_NAME FROM SYS.PROCEDURES WHERE SCHEMA_NAME='…'` | 708 in Oil. `JsGet*` (17 of them) serve JSAP's dropdowns. `FACTORY`, `FACTORY2`, `GetProductionData*` serve the factory app. `OMS_SP_GST_INVOICE_SAP` exists. §6 |
| 6 | **Intercompany code mapping fields** | `U_WG_CardCode`/`U_WG_ItemCode`/`U_WG_GLNO` (Oil), `U_OIL_CardCode`/`U_OIL_ItemCode`/`U_OIL_GLNO` (Bev), `U_Mart_ItemCode`/`U_MartCustomer`/`U_MART_DOC_NO` (Oil/Mart) | Cross-company links you might mistake for an external system's keys. 2,405 of 3,390 Oil BPs carry `U_WG_CardCode`. §4.3 |

---

# 1. LEAD WITH THE NEGATIVES — what SAP genuinely does NOT hold

Verified by row count on the standard SAP object for each domain
(`SELECT TABLE_NAME,RECORD_COUNT FROM M_TABLES WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND TABLE_NAME IN (…)`).

| Domain | SAP object | Rows (Oil) | Reading |
|---|---|---|---|
| **CRM / activities / calls / visits** | `OCLG` | **0** | JIVO has **never logged a single activity in SAP**. Any visit / call / follow-up data anywhere in the fleet is `N` or `X`. `OCLS`=0, `OCLT`=1 (default), `OCLA`=2. |
| **Service / tickets / complaints** | `OSCL`, `SCL1` | **0 / 0** | The Service module is untouched. Complaint & service data is `N`. |
| **Sales opportunities / pipeline** | `OOPR`, `OPR1` | **0** | No pipeline in SAP. |
| **HR: employee master** | `OHEM` | **17** | 17 name-only rows (`dept` and `userId` null on 15 of them). `HEM1`=0, `HEM2`=0, `OHTR`=0 (transfers), `OHPS`=1. **SAP has no workforce.** TankhaPay's employee/attendance/salary/leave data is `N`. |
| **Projects** | `OPRJ` | **0** | |
| **Territories / beats** | `OTER` | **1** (the default) | No beat/territory hierarchy. DSR geography is `N`. |
| **Retailer / outlet universe** | `OCRD` total | 3,390 BPs (Oil), 2,183 (Mart), 2,930 (Bev) | of which only **33** are `U_Chain='RETAILER'` and 76 `SINGLE SHOPS`. SAP holds distributors (684) and individuals (453), not the retail long tail. |
| **QC / lab results** | `@QC_O` / `@QC_I` | **6 / 19** | A UDO exists but is abandoned test data (`U_DocNum` values `123`, three rows with NULL doctype). Factory QC is effectively `N`. |
| **Marketplace/portal operational data** | — | — | No `U_*` field anywhere in Oil matches `%BLINK%`, `%ZEPTO%`, `%AMAZON%`, `%FLIPKART%`, `%CHANNEL%`, `%MARKETPLACE%`, `%DSR%`, `%TANKHA%`, `%BEAT%`, `%VISIT%`, `%OUTLET%`, `%RETAIL%`, `%SALAR%`, `%ATTEND%`, `%PAYROLL%`, `%LEAVE%`, `%SHIPMENT%`, `%CONTAINER%`. The **only** hits in that whole keyword sweep were `U_BOEDate` and `U_Emp_Code`. |

### 1.1 Two partial negatives — read carefully, they are the subtle ones

**HR is half-present.** SAP has no employees, but it *does* have:
- `U_Emp_Code` on `OCRD`/`OACT`, **510 of 3,390 Oil BPs populated**, holding real HR codes
  (`JWPL0016`, `JWPL2418`, `JWPL1206`, `JWPL0030`, `JWPL0035`). These are the imprest /
  expense-float accounts. So the *same employee-code namespace* as TankhaPay exists in SAP —
  it is a valid join key — but only for the ~510 staff who hold a money account.
- `U_OcrCode5` "Salary Category" on `JDT1`: **2,011 of 513,596** journal lines tagged
  `PROMOTER` (1,062), `SO/SR` (455), `ASM` (262), `RSM` (6), `CALLER` (4), `MIS` (1).
  Payroll **cost** lands in SAP, classified by field-sales role. Payroll **detail**
  (per-person, attendance, leave, PF/ESI) does not.
  → Ruling guidance: HR/payroll aggregate ledger = `F`; employee/attendance/salary/leave
  records = `N`.

**Marketplaces are present as master data, absent as operations.**
`OCRD` in Oil/Mart/Bev contains AMAZON, FLIPKART (several FBF/B2C entities), JIOMART,
AVENUE SUPERMARTS (D-Mart) as **customers** with `U_Chain` set and
`U_Main_Group='E-COMMERCE'`; and BLINK COMMERCE, ZEPTO/KIRANAKART, SWIGGY INSTAMART,
AMAZON SELLER SERVICES as **vendors** (commission/marketing billing).
Only Beverages has a Blinkit *customer* (`CUSTA001135 BLINK`, chain `DISTRIBUTOR`).
There is **no Zepto customer in any company.**
→ Money moves through SAP; listings, ads spend at SKU level, portal order status,
fill rates, city-level inventory do not. Portal-side operational data is `X`.

---

# 2. CUSTOM TABLES INSIDE THE SAP SCHEMA — the F-bucket smoking guns

These are **not SAP objects**. They do not appear in the Service Layer entity list.
They are app tables that someone created inside the SAP HANA company schema.
This is the single most important section: **"it's not a SAP entity" ≠ "it's not in SAP".**

Query used:
```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM M_TABLES
WHERE SCHEMA_NAME LIKE 'JIVO%' AND TABLE_NAME NOT LIKE '@%'
  AND (LENGTH(TABLE_NAME) > 8 OR TABLE_NAME LIKE '%\_%' ESCAPE '\')
  AND TABLE_NAME NOT LIKE 'CRSP%' AND TABLE_NAME NOT LIKE 'CR\_%' ESCAPE '\'
ORDER BY RECORD_COUNT DESC;
```
(Exclude the noise: `ES_BO*`/`ES_*` = SAP Enterprise Search metadata, `M_TIME_DIMENSION`,
`PAL_*` = HANA Predictive Analysis Library, `ATP_*`, `CFF_*`, `BA_PORT_*`, `BGT*_STAGING_*`,
`B1CFL*`, `NULL_OBJ`, `DBQSTREAMS` = all SAP-standard.)

### 2.1 Vendor & customer onboarding portal — `ZVENDOR_PORTAL` / `ZCUST_PORTAL`

The clearest `F` evidence in the whole database.

```
SELECT "STATUS", COUNT(*) N, COUNT("SAP_CARD_CODE") PUSHED FROM ZVENDOR_PORTAL GROUP BY "STATUS"
  APPROVED 44  pushed 44
  REJECTED  3  pushed  0
  PENDING   2  pushed  0     (submitted 2026-04-02 … 2026-06-05)

ZCUST_PORTAL:  APPROVED 12 pushed 12 | REJECTED 3 pushed 0 | PENDING 2 pushed 0
```

66 columns on `ZVENDOR_PORTAL` including `BANK_ACCOUNTS`, `ATTACHMENTS`, `TDS_CATEGORY`,
`TDS_LDC_NO`, `MSME_*`, `FSSAI_NO`, plus a full manager-review block
(`MGR_GROUP`, `MGR_PAY_TERMS`, `MGR_CREDIT_LIMIT`, `MGR_PURCHASE_ACCOUNT`, `MGR_TERRITORY`…)
and the audit trail `VERIFIED_BY/AT`, `APPROVED_BY/AT`, `REJECTED_BY/AT`, `SAP_CARD_CODE`,
`SAP_ATTACHMENT_ENTRY`.
`ZCUST_PORTAL` (81 cols) adds the sales hierarchy: `MGR_RSM`, `MGR_ASM`, `MGR_SO`, `MGR_SR`,
`MGR_PROMOTER`, `MGR_ZONE`, `MGR_SUBAREA`, `MGR_SCHEME_TYPE`.

**The rejected and pending applications exist nowhere else.** They never became a BP.
Whatever CLI/portal fronts this is `F`, and the rejection trail is the part SAP loses.

### 2.2 Approval workflow — the biggest custom footprint

| Table | Oil | Mart | Bev | What it is |
|---|---|---|---|---|
| `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` | **29,212** | – | – | 27 cols: `budgetId, docEntry, status, currentStageId, userName, stageId, stageName, approvalId, createdBy, createdOn, company, rejectid, currentTemplateId, currentStagePriority, nextStageId, nextStageName, objType, lineNum, visOrder, docId, currentStageApprovers, nextStageUsers, BUDGET, SUB_BUDGET, SYNC_TIMESTAMP`. 9,829 distinct docEntry, 2 companies, `createdOn` 2025-03-26 → **2026-03-26** (note: stops ~4 months ago). |
| `js_budget_approval_workflow` | 86 | – | 40 | the live/current table (lowercase twin) |
| `jsDocEntries` | 535 | – | 13 | `id, docEntry, status, currentStageId, templateId, totalStage, currentSatge` |
| `jsBudgetStatusWorkflow` | – | – | 479 | |
| `jsDocEntryDetail` | – | – | 119 | |
| `jsDocumentAttachments` | 36 | – | – | `id, docId, docType, branch` |
| `tbl_Draft_Approvals` | **1,440** | – | **7,351** | 38 cols incl. `BUDGET, SUB_BUDGET, Budget_Owner, Approver_Name, Current_month_Budget, Current_month_Posted_Amount, ACOMMENT, VCOMMENT, VerifiedStatus, ApprovedStatus, LineRemarks`. `DocDate` 2024-10-18 → 2026-07-27 (**live**). Status split: 961 NULL/NULL (in-flight), 332 Y/Y, 146 Y/P. |
| `tbl_Draft_Approval` | 161 | – | 19 | older singular twin |
| `PRODUCTIONORDERSYNC` | **2,499** | 0 | 11 | `ID, DOCENTRY, STATUS, CURRENTSTAGEID, TEMPLATEID, TOTALSTAGE, CURRENTSTAGE, DATE, UPDATEDON, CREATEDON, ITEMCODE, WAREHOUSE, COMPANY, SAPSTATUS, SYNCEDAT, LASTMODIFIED`. 2,499 distinct DocEntry, 2025-10-25 → **2026-07-29** (live). Status A=2,496 R=2 P=1; `SAPSTATUS='PENDING'` on **all** 2,499. |
| `QC_SYNC_DATA` | 0 | – | – | built, never used |
| `OWDD_LOG` / `WDD1_LOG` | 0 / 0 | – | – | log tables for the SAP approval engine, empty |

Counterweight — **SAP's own approval engine is heavily used**, so do not assume approvals
are app-native: `OWDD` **57,741** rows + `WDD1` **57,752**, 2024-10-03 → 2026-07-29,
by ObjType: 67 (stock transfer) 17,250 · 18 (A/P invoice) 14,839 · 13 (A/R invoice) 10,008 ·
20 (GRPO) 5,080 · 22 (PO) 2,235 · 19 · 15 · 14 · 46 · 16 · `1250000001` (a UDO) 668.
`ODRF` (drafts pending approval) = **47,609**.
→ Approval *decisions and stages* are in SAP (`OWDD`/`WDD1`) **and** mirrored into the
`js*`/`tbl_Draft_Approval*` tables. The **budget attribution, comments, and the
verify-then-approve two-step** live only in the custom tables.

### 2.3 WhatsApp approval bot

| Object | Rows | Detail |
|---|---|---|
| `JIVO_WA_MESSAGE_LOG` | **5,941** | `WddCode, Phone, MessageType, ItemIndex, Status, MetaMessageId, AttemptCount, LastError, CreatedAt, UpdatedAt, SentAt`. 2026-05-01 → 2026-07-29. **Only 4 distinct phone numbers.** |
| `JIVO_WA_SENT` | 641 (Oil), 4 (Mart) | |
| `view_whatsapp_bot` | view (Oil **and** Mart) | see §5 |

`WddCode` is the FK to `OWDD`. So: the bot **reads** SAP (via the view), and writes its own
delivery state (Meta message id, attempt count, last error) into a table SAP will never use.

### 2.4 Other custom tables worth knowing

| Table | Rows (Oil) | Columns / meaning |
|---|---|---|
| `ZBOM_REQUESTS` | 12 | `ID, TYPE, ITEM_CODE, QTY, BOM_TYPE, WAREHOUSE, COMPONENTS, ORIGINAL_DATA, STATUS, SUBMITTED_BY, APPROVAL_LOG, REJECTED_BY, SAP_PUSHED_AT, SAP_PUSHED_BY, SAP_RESULT, COMPANY` — a BOM change-request app with an explicit push-to-SAP result. Textbook `F`. |
| `ZCUST_USERS` | 13 | `ID, USERNAME, PASSWORD, FULL_NAME, EMAIL, ROLE, ACTIVE, CREATED_AT, LAST_LOGIN, MODULES, SAP_USER_ID` — **an app's user table with a password column, inside the SAP DB.** Do not dump it. Its existence is the finding. |
| `tbl_SAPRight` | 2 | `userid, transtype, fromDate, toDate, timeLimit, rights, branch` — time-boxed permission grants |
| `tbl_customerLimit` | 35 | `CardCode, CurrentLimit, NewLimit, ValidTill, createdOn, expired, createdBy` — credit-limit override requests with expiry (CardCodes carry a `JW` suffix, e.g. `CUSTA001015JW`) |
| `ZAPR_EMAIL_CONFIG` / `ZAPR_TOKEN_CONFIG` / `ZAPR_TABLE_CONFIG` | 23 / 11 / 10 | an "APR" (approval/reporting) config layer: `AliasID, AliasName, TableName, JoinType, JoinOn, DisplayName, IsActive` — a generic query-builder config |
| `SALES_ANALYSIS` / `SALES_ANALYSIS_DATA` | 1,299 / 17 | 45-col denormalised sales fact incl. `SchemeQty, SchemeSaleAmt, SchemeAmt, COGS, Liter, Box, U_Main_Group, U_Chain, U_SALES_PERSON` — a materialised report cache |
| `GetTurnover` | 1,392 | `CardCode, CardName, FirstDate, LastDate, Turnover, DocumentCount` — cached turnover table |
| `INV1_UPDATE` | 50 | `DocNum, DocEntry, LineNum, ItemCode, PrcName, Correct, Veriety, BaseType, ObjType` — a data-fix worklist |
| `NEWDATASALETABLEAUHS` (Bev) | 1,449 | Tableau extract staging |
| `OMS_IRN_LOG` | 4 | **Not the OMS app.** Its columns are `U_UTL_IRN, U_UTL_AckNo, U_UTL_QRPT, U_UTL_CANDT…` — this is the e-invoicing add-on's IRN log. Naming collision. Confidence 85. |
| `XCLTRLOG` (Bev) | 1,005 | unidentified add-on log — **U**, I did not chase it |

---

# 3. USER-DEFINED TABLES (`@` UDTs)

60 registered in `OUTB` (Oil). Full registry:
`SELECT "TableName","Descr","ObjectType" FROM "JIVO_OIL_HANADB"."OUTB"`.
(`OUDT` does **not** exist on this system — `OUTB` is the registry.)
Every UDT is physically stored twice: `@X` (live) and `@AX` (SAP's archive twin) — ignore `@A*`.

### 3.1 The only UDT with real volume

| UDT | Oil | Mart | Bev | What |
|---|---|---|---|---|
| `@UTL_MDEXTH` "MarktingExtentionHeader" | **17,695** | 8,972 | 4,608 | **The e-invoice store.** Cols: `DocEntry, DocNum, Object, … U_UTL_IRN, U_UTL_AckNo, U_UTL_QRPT, U_UTL_QRST, U_UTL_IST, U_UTL_IRNGENDT, U_UTL_CANDT, U_UTL_CancelTime, U_UTL_DocType, U_UTL_BaseEntry, U_UTL_StatutoryType, U_UTL_ST_GSTSt`. **If an app shows you an IRN or a GST QR, that is a SAP mirror.** |
| `@UTL_ST_EWAYDT` "E-Way Details" | 1,333 | 2,560 | 279 | e-way bills |
| `@UTL_ST_INTREWBILL` / `@UTL_ST_TREWAY1` | 117 / 117 | | 2 / – | e-way bill header/lines |
| `@UNE_USERSEL` / `@UNE_USERSELTAX` | 2,449 / 884 | 1,373 / 528 | 1,666 / 43 | add-on per-user warehouse/location selection (`U_UNE_WCOD, U_UNE_UCOD, U_UNE_LOC`) — config, not business data |
| `@UTL_UP_USRLIC1` | 108 | 97 | 101 | add-on module licensing per user |

### 3.2 JIVO's own taxonomy UDTs — these back the `U_*` classification fields

| UDT | Oil | Mart | Bev | Backs |
|---|---|---|---|---|
| `@ITEM_VARIETY` | 196 | 131 | 214 | `OITM.U_Variety` (labelled "SUBGROUP") |
| `@MAIN_GROUP` | 60 | 50 | 54 | `OCRD.U_Main_Group` |
| `@ITEM_SUBGRP` | 51 | 51 | 69 | `OITM.U_Sub_Group` (labelled "VARIETY" — the two are cross-labelled, see trap §7.3) |
| `@ITEM_SKU` | 50 | 35 | 17 | `OITM.U_SKU` |
| `@CHAIN` | 46 | 47 | 46 | `OCRD.U_Chain` |
| `@ITEM_UNIT` | 4 | 4 | 5 | `OITM.U_Unit` |
| `@BRAND` | 3 | 3 | 3 | `OITM.U_Brand` |
| `@BUDGET` / `@BUDGET1` | 1 / 1 | – | – | budget master (`U_BUDGET, U_SUB_BUDGET, U_MONTH, U_FIXED_AMOUNT, U_V_AMOUNT`) — near-empty; the real budget data is in `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` |
| `@QC_O` / `@QC_I` | 6 / 19 | – | – | abandoned QC UDO (§1) |
| `@OZIA` / `@OZIAR` | 2 / 20 | – | – | ZIA add-on authorisation rules |
| `@ZIA_DL_LIMIT` / `@ZIA_DL_OLIMIT` | 12 / 3 | – | 11 / 3 | delivery-note credit limits |
| `@SERVER` | **1** | 1 | 1 | `U_SAPServerName, U_SAPDBName, U_HanaUserId, U_Password, U_Driver` — **an integration connection-config row stored in the SAP DB.** I did not read the values and you should not either. Its existence proves something outside SAP was configured to connect back in. |

`@UTL_*`, `@UNE_*` = Uneecops add-on (e-invoice / e-way bill / licensing).
`@ZIA_*`, `@OZIA*` = the ZIA add-on (there is a whole `ZIA` HANA schema, owner `ZIA`).
Neither is JIVO app data. **No UDT is named after any JIVO app** — no `@OMS*`, `@ECOM*`,
`@FACTORY*`, `@DSR*`, `@EXIM*`, `@JSAP*`. The apps did not extend SAP this way; they used
plain custom tables (§2) instead.

---

# 4. USER-FIELD (`U_*`) INVENTORY

`SELECT "AliasID","Descr","TableID" FROM "JIVO_OIL_HANADB"."CUFD"`
→ **5,572 definitions across 278 tables** (Mart 5,194, Bev 5,106).

Split by naming family:

| Family | Definitions | Distinct names | Owner |
|---|---|---|---|
| `U_UTL_*` | 2,165 | 257 | Uneecops e-invoice/e-way add-on |
| `U_UNE_*` | 1,082 | 82 | Uneecops core add-on |
| `U_QC*` | 2 | 1 | QC UDO |
| **everything else** | **2,323** | **222** | **JIVO-authored** |

### 4.1 The 222 JIVO fields — the ones that carry lineage

**On all 32 marketing-document headers** (`OINV ORDR ODLN OPCH OPOR OPDN OQUT OPQT OPRQ OPRR
ORIN ORPC ORPD ORDN ORRR OCIN OCPI OCPV OCSI OCSV ODPI ODPO ODRF OIEI OIGE OIGN OOEI OSFC
OSFI OWTQ OWTR` + `ADOC` archive):

`U_OMS_Order_No` "OMS Order Number" · `U_OMS_REF` "Unique OMS Ref" · `U_Production_Order` ·
`U_PRODUCTION_DATE` · `U_SFGPRODEntry` "SFG Production Entry" · `U_JRId` · `U_AR_NO` ·
`U_GRPO`/`U_GRNdocentry`/`U_GRNCardCode`/`U_GRNWhsCode` · `U_DisDE`/`U_DisDN` (dispatch
DocEntry/DocNum) · `U_Dipatch_Date` · `U_Recv_Date` · `U_MartCustomer` · `U_MartCN`
"DN Mart Needed" · `U_PONo` "PO Number Mart" · `U_SALES_PERSON` · `U_TransporterName` ·
`U_TransporterInvoice` "Gate Pass No." · `U_VehicleNoM` · `U_DriverName` · `U_Mob_No` ·
`U_BilltyNumber`/`U_BiltyDate`/`U_BiltAmt` · `U_LRNUmber` "Bill Of Entry No." ·
`U_InvRevEntry` "Bill Of Lading No" · `U_BOEDate` · `U_delbranch`/`U_delbranchnam`/
`U_deldocnum`/`U_deldocdate` · `U_Ship_From` · `U_Order_Date` · `U_TotalAmt` ·
`U_Total_Gross_Wt` · `U_CreditCreated` · `U_GenType` · `U_Basement`/`U_First_Floor` (godown)

**On all 32 line tables** (`INV1 RDR1 DLN1 PCH1 POR1 …`): `U_ARNO` · `U_BilltyNumber` ·
`U_BiltyDate` · `U_CardCode` · `U_Disp_Qty` · `U_Recvd_Qty` · `U_carton`/`U_cartonpc` ·
`U_F_Year` · `U_LNDCSTNO` · `U_PRCHSE_VAL` · `U_Purpose` · `U_SchemeAgst` "Scheme Against" ·
`U_Sub_Account` · `U_Remarks`

**On `OITM`** (30 fields, all also on `AITM/UITM/SITM`):
`U_TYPE` · `U_Sub_Group` · `U_Variety` · `U_SKU` · `U_Brand` · `U_Unit` · `U_MRP` ·
`U_Net_Weight` · `U_Gross_Weight` · `U_Qty_In_PCS` · `U_IsLitre` · `U_PACK_TYPE` ·
`U_Packing_Type` · `U_Is_Plastic` · `U_P_WEIGHT` · `U_Tax_Rate` · `U_Rev_tax_Rate` ·
`U_GL_ACCT` · `U_FA_Type` · `U_Is_CSD` · `U_Index_No` · `U_Shelflife` · `U_ITEM_LOCK` ·
`U_CONSUMPTION_PER_DAY` · `U_JRID` · `U_Mart_ItemCode` · `U_WG_ItemCode`

**On `OCRD`** (40 fields): `U_Emp_Code` · `U_Chain` · `U_Main_Group` · `U_CATGCODE` ·
`U_CMDTCODE` · `U_Fssai` · `U_MSME`/`U_MSME_Type`/`U_MSME_BType` · `U_ST_GRP1..11`
(stage groups) · `U_AddressIdPrint` · `U_BranchHomeBpl` · `U_WG_CardCode`

**On `OWOR`/`AWOR`/`UWOR`** (production orders): `U_BATCH_NO` · `U_MFG` · `U_EXP_DATE` ·
`U_ProductionDate` · `U_WASTAGE` · `U_SFGPRODEntry`; on `WOR1`: `U_WASTAGE_QUANTITY`.

**On payments** (`ORCT ARCT OVPM OPDF`): `U_Pymnt_Mode` · `U_Type_of_Advance` ·
`U_Adv_Settl_Dt` · `U_URGENCY` · `U_Pay_Report_Gen` · `U_Pay_Rep_Gen_Inf`

**On `OJDT`/`OBTF`**: `U_ATTACHEMENT`, `U_ATTACH_LINK`, `U_REMARKS`;
on `JDT1`/`BTF1`: `U_OcrCode5` "Salary Category", `U_Not4BS`

**On `OACT`** (G/L): `U_Emp_Code`, `U_Account_Number`, `U_Bank_Name`, `U_IFSC`,
`U_FA_CODE`, `U_WG_GLNO`
**On `OUSR`**: `U_NAME`, `U_Role`, `U_DEPT`
**On `OITT`** (BOM): `U_Bomuser`, `U_autoproc` "Auto Production User", `U_AppDt`, `U_CrtDt`
**On `OLCT`**: `U_CID`, `U_SECRET`, `U_Contact_No`, `U_Contact_Persion` — API credentials again

### 4.2 Which of these are actually POPULATED (Oil, live counts)

| Field | Table | Populated / total |
|---|---|---|
| `U_TYPE` | OITM | 2,234 / 2,269 |
| `U_Sub_Group`, `U_Variety`, `U_Brand`, `U_Unit`, `U_ITEM_LOCK` | OITM | **2,269 / 2,269 (100%)** |
| `U_SKU` | OITM | 1,599 / 2,269 |
| `U_MRP` | OITM | 542 · `U_Mart_ItemCode` 378 · `U_WG_ItemCode` 59 · `U_Net_Weight` 211 · `U_Qty_In_PCS` 151 · `U_Is_CSD` 15 |
| `U_Main_Group` | OCRD | 3,348 / 3,390 · `U_WG_CardCode` **2,405** · `U_Chain` 1,477 · `U_Emp_Code` **510** · `U_MSME` 297 · `U_Fssai` 94 · `U_CATGCODE` 12 · `U_ST_GRP1` **0** · `U_CMDTCODE` **0** |
| `U_WASTAGE` | OWOR | **7,858 / 7,858 (100%)** · `U_BATCH_NO` **0** · `U_MFG` **0** · `U_EXP_DATE` **0** · `U_ProductionDate` **0** |
| `U_Dipatch_Date` | OINV | 10,034 / 30,477 · `U_BilltyNumber` 9,018 · `U_TransporterName` 8,745 · `U_VehicleNoM` 8,424 · `U_SALES_PERSON` 7,847 · `U_PONo` 805 · `U_delbranch` 774 · `U_GRPO` 551 · `U_MartCustomer` 424 |
| `U_SALES_PERSON` | ORDR | 6,023 / 14,736 · `U_PONo` 514 · `U_MartCustomer` 261 · everything transport-related ≈100 |
| `U_BOEDate` / `U_LRNUmber` (BoE no.) / `U_InvRevEntry` (B/L no.) | OPCH | 757 / 789 / 182 of 15,934 |
| same | OPOR | 7 / 8 / 4 of 4,191 |
| `U_Production_Order`, `U_SFGPRODEntry`, `U_JRId` | OINV/ORDR/ODLN/OPOR | **0 everywhere** — defined, never used |
| `U_OcrCode5` (salary category) | JDT1 | 2,011 / 513,596 |

### 4.3 Fields that exist in one company only (`CUFD` set difference)

- **Oil only**: `U_WG_CardCode`, `U_WG_ItemCode`, `U_WG_GLNO`, `U_Mart_ItemCode`,
  `U_MartCustomer`, `U_MartCN`, `U_OMS_REF`, `U_SALES_PERSON`, `U_GRPO`, `U_BUDGET`,
  `U_SUB_BUDGET`, `U_ITEM_LOCK`, `U_CONSUMPTION_PER_DAY`, `U_QC_Date`, `U_Rating`,
  `U_Parameters`, `U_CreditCreated`, `U_Is_Plastic`
- **Mart only**: `U_MART_DOC_NO`, `U_JWPL_BASE`, `U_Oil_ItemCode`, `U_BPCODE`, `U_POMade`,
  `U_PO_Ship_To`, `U_ShelfLife`, `U_FA_TYPE`, `U_Adv_settl_Dt`
- **Beverages only**: `U_OIL_CardCode`, `U_OIL_ItemCode`, `U_OIL_GLNO`, `U_RECIPE_NO`,
  `U_VechileNom`, `U_BiltyNumber`

The `WG_*` / `OIL_*` / `Mart_*` / `MART_DOC_NO` / `JWPL_BASE` families are **intercompany
mapping**, not external-system keys. Treat cross-company flows (Oil→Mart) as internal SAP.

---

# 5. PURPOSE-BUILT VIEWS — apps reading SAP through a window

411 views in Oil, but ~210 are auto-generated `DV20…` (B1 query-manager artefacts),
~78 are `B1_*` (SAP standard), ~48 are `ES_*` (Enterprise Search, most sitting over the
empty CRM/service tables — `ES_ACTIVITY`, `ES_OPPORTUNITY`, `ES_SERVICECALL`,
`ES_EMPLOYEE_M_D` all return nothing).

**The custom, app-shaped ones:**

| View | Where | What it serves |
|---|---|---|
| `D_FACTORY_PRODUCTION` | Oil | `OWOR ⋈ OITM WHERE Type IN ('S','D')`, returns `CmpltQty` **and a derived `Litres` = CmpltQty × SalPackUn when `U_IsLitre='Y'`**, plus `U_Brand/U_Unit/U_Variety/U_Sub_Group`. The factory app's production feed. |
| `D_FACTORY_DISPATCH` | Oil | ODLN/DLN1 aggregated to `Total_Quantity`, `Total_LineTotal`, `Litres`, `Days_Difference` |
| `D_FACTORY_BILLED_LITRES` | Oil | `OINV ⋈ INV1 ⋈ OITM`, billed litres by SKU/variety/brand |
| `DISPATCHES_OIL` / `DISPATCHES_BEVERAGE` | Oil / Bev | 9.7 KB view: item, docnum, box/loose qty, ship-to, warehouse, card |
| `PRODUCTION_RELEASE_OIL` | Oil | OWOR planned qty → Box / Liter conversions |
| `PROD_VIEW` | Oil | |
| `view_whatsapp_bot` | **Oil and Mart** | `OWDD ⋈ WDD1 ⋈ OUSR ⋈ ODRF ⋈ DRF1 ⋈ OITM` + on-hand stock from `OITW` for warehouses `BH-PM, GP-PM, BH-BS, BH-NM, GP-NM`, filtered `ProcesStat='W' AND w1.Status='W' AND ObjType='22'`. i.e. **pending purchase-order approvals with current stock and MRP** — exactly the payload the WhatsApp bot sends. |
| `GRPO_BARCODE`, `STOCK_TRANSFER_BARCODE` | Oil | barcode/scanner app: item, box/pcs conversion, batch, MFG/Exp date |
| `V_FUND_FLOW_MIS`, `V_CLOSING_BALANCE_BY_MONTH`, `V_OPEN_GRPO_BY_MONTH` | Oil | finance MIS |
| `V_WDD_COMPLETE_LOG` | Oil | full approval log (`LogID, LogDate, LogUser, LogAction, WddCode, DocEntry, ObjType, CurrStep, Status, Status_OLD, Remarks, IsDraft, DraftEntry`) |
| `SALES_INSTALLMENTS`, `OPENPQT`, `LAST12MONTHENDVIEW`, `NEXT12WEEKBEGINVIEW`, `NEXT6MONTHENDVIEW`, `AvgPrice`, `LatestPrices`, `LastPurchasePrices` (Bev) | all 3 | reporting helpers |
| `OCRDV`, `OJDTV`, `OWORV`, `DOC1_View`, `FIFO`, `VBIN`, `VTSP`, `SINM`, `OINM` | all 3 | add-on / SAP-internal helper views |

**Reading**: a view named after an app means that app's screen is a *rendering of SAP*.
Anything a `D_FACTORY_*` view returns is `M`. The same app's *own* state
(`PRODUCTIONORDERSYNC` stages, WhatsApp delivery status) is not.

---

# 6. STORED PROCEDURES — the app read-APIs

708 procedures in Oil. Most are SAP/Crystal/add-on standard (`TMSP_*` ~200, `CRSP_*` ~60,
`CRYSTAL_*`, `ATP_*`, `CFF_*`, `DA_*`, `DP_*`, `PAL*`, `GSTR*`, `PRETEST_*`).
The app-facing custom ones:

**JSAP** — `JS_SYNC_BUDGET`, `JS_SYNC_BUDGET_IT`, `JS_SYNC_BUDGET_JASHAN`,
`PRC_INS_jsDocumentAttachments`, `JSGETDISTINCTITEMNAMES`, and **17 `JsGet*` master-data
procs**: `JsGetBrand, JsGetSKU, JsGetVariety, JsGetUnit, JsGetSubGroup, JsGetHSN,
JsGetTaxRate, JsGetUOMGroup, JsGetPackType, JsGetPackingType, JsGetFaType,
JsGetGroupNameWithCode, JsGetBuyUnitMsr, JsGetBuyUnitUom, JsGetInvUnitMsr, JsGetInvntryUom,
JsGetPurPackMsr, JsGetSalPackMsr, JsGetSalUnitMsr`.
→ **JSAP's item-master dropdowns are literally SAP stored procedures.** Those screens are `M`.
`JS_SYNC_BUDGET` itself joins `ODRF ⋈ DRF1`/`js*`/`tbl_Draft_Approvals` and maps
`OcrCode3→Budget, OcrCode4→Sub Budget, OcrCode2→Eff Month` with ObjType 18/14/28/19.
→ the budget dimension is SAP cost-centre data (`OcrCode2..5`), the approval state is not.

**Factory** — `FACTORY`, `FACTORY2`, `FACTORY2COMMOND`, `FACTORYGILL`, `GetProductionData`,
`GetProductionDataUsingLine`, `GetProductionDocNum`, `Get_Planned_Production_Orders`,
`PRODUCTION_REPORT`, `PRODUCTION_WASTAGE`, `Production_Release`, `HI_PRODUCTIONCOST`,
`GetFgScRmPmItems`, `GetLocationsByUnit`, `GetWarehouseByLocation`,
`Get_Item_Location_Stock`, `GetItemStockDetails`, `SALEBOM_BATCH`, `GETDISTINCTBOM`,
`sp_FetchUpdate_BOM_Details`.
`FACTORY(DocKey)` reads `OILM ⋈ ILM1 ⋈ OBTN ⋈ OITM` and returns Quantity / Box / LooseQty /
MnfDate / ExpDate / GROSS_WEIGHT. → the factory app's quantities are SAP inventory-log
quantities.

**Approvals / gate / warehouse** — `DRAFT_APPROVAL`, `DRAFT_APPROVAL_ATC1`,
`DRAFT_APPROVAL_Budget`, `SP_LOG_OWDD_CHANGE`, `SP_LOG_WDD1_CHANGE`, `TMSP_GETWDD`,
`GET_AVAILABLE_PO`, `GET_AVAILABLE_GRPO`, `GET_AVAILABLE_GR`, `GET_AVAILABLE_APDRAFT`,
`GET_BUDGET_LIST`, `GET_PARTY_DATA`, `GetCustomerCards`, `CustomerLimit`,
`Gate_Pass`, `GATEPASS_DELIVERY`, `GATEPASS_PARWINDER`, `GRPO_GATEPASS`, `Dispatch_Note`,
`GRPO_FOR_BARCODE`, `STOCK_TRANSFER_BARCODE`, `PENDING_RECEVING`, `OPEN_DELIVERY_NOTES`,
`BRANCHSTOCKTRANSFER`, `BTACHTRACKING`.

**Auth/session for apps** — `GETCREDENTIALS`, `GETUSERDETAILS`, `GETMOBJDETAILS`,
`USER_ENTRIES`, `KEYEXISTS`, `TMSP_GETUSERS`, `TMSP_ADDSQLUSER`.

**OMS-named** — `OMS_SP_GST_INVOICE` and `OMS_SP_GST_INVOICE_SAP(DOCKEY INT)`.
The latter builds a complete GST invoice (`OINV ⋈ OCRD ⋈ OCRG ⋈ OCRY ⋈ CRD1`,
Export/Tax-invoice/Debit-note/Bill-of-supply classification, `U_Dipatch_Date`,
`U_AddressIdPrint` ship-to logic). **Whether "OMS" here means the OMS app or is an
unrelated print-template prefix, I could not determine — confidence 60.** But if the OMS
app's invoice tracker renders GST invoices, this is the most likely source, and that would
make it `M`.

**Statutory** — `GSTR1_B2B/B2CL/B2CS/CDNR/CDNUR`, `GSTR2_*`, `GST_HSN_SUMMERY*`,
`TDS_REPORT`, `TCS_BY_INCOMING_PAYMENT`, `UGST_SPT_INVOICE`. GST returns are generated
from SAP. Any GST-filing tool showing these numbers is `M`.

**Named after people** (report one-offs, ignore for lineage): `Dolly_Mam_Bst`, `REPORT_DOLLY`,
`JASHAN_STOCK_REPORT`, `TEST_MANAV1`, `REPORT_INVENTORY_MOVEMENT_MANAV`, `FACTORYGILL`,
`GATEPASS_PARWINDER`, `REPORT_BS_MJ`, `REPORT_BS_ZH`.

Saved queries (`OUQR`) are also full of operator names (`ALL BUNTY VEER JII`, `ALL PRESHIT`,
`ALL MANAGER`, `BH-JW KULBEER SIR`) — this is how the business actually queries SAP.

---

# 7. TRAPS — things that will make you rule wrong

### 7.1 `U_OMS_Order_No` is GARBAGE. Do not use it as OMS lineage.

It looks like the perfect join key. It is not.

```
SELECT COUNT(*), COUNT("U_OMS_Order_No") FROM ORDR  →  14,736 total, 6,253 populated
SELECT COUNT(DISTINCT "U_OMS_Order_No") FROM ORDR   →  746
top values: 4563 (750 rows) · 1234 (639) · 4653 (623) · 4526 (307) · 123 (225) ·
            1365 (181) · 1212 (163) · 1111 (161) · 7485 (155) · 1236 (133)
date range of populated rows: 2024-11-07 → 2026-04-28 (nothing since April)
```

746 distinct values for 6,253 rows, all 3-4 digit keyboard-mash. This is a **mandatory
field that operators typed junk into**, not an OMS reference. `U_OMS_REF` is populated on
exactly **1** row out of 30,477 invoices and **0** sales orders. `OQUT` (sales quotations —
the doc type OMS reportedly pushes into) has **0** populated on either field.

→ **You cannot join OMS orders to SAP documents on any field in SAP.** If someone claims
6,253 SAP orders "came from OMS", that is wrong.

### 7.2 "Not a SAP entity" ≠ "not in SAP"

`ZVENDOR_PORTAL`, `ZCUST_PORTAL`, `ZBOM_REQUESTS`, `tbl_Draft_Approvals`,
`PRODUCTIONORDERSYNC`, `JS_SYNC_BUDGET_APPROVAL_WORKFLOW`, `JIVO_WA_MESSAGE_LOG`,
`ZCUST_USERS`, `tbl_customerLimit` are all **inside `JIVO_OIL_HANADB`** and all invisible
to `sapb1` / the Service Layer. A "the Service Layer has no entity for this" check will
give you a false `N`. Always cross-check with `M_TABLES`.

Conversely, the data being physically in the SAP database does **not** make it `M`. It is
still app-originated pre-SAP working state → `F`, or app-only state → `N`. The physical
location is a storage decision, not a lineage fact. Say where it lives *and* where it came from.

### 7.3 `U_Sub_Group` and `U_Variety` are cross-labelled

`CUFD` says `U_Sub_Group` → Descr **"VARIETY"** and `U_Variety` → Descr **"SUBGROUP"**.
The backing UDTs are `@ITEM_SUBGRP` (51 rows, "Items Sub Group") and `@ITEM_VARIETY`
(196 rows, "Items Variety"). Do not trust the description; check the value set.

### 7.4 Approvals are in BOTH places

`OWDD`/`WDD1` (57.7k rows) is SAP's own approval engine and it is fully live through
2026-07-29. Do not call approval workflow `N` just because JSAP has a nice UI for it.
What is app-only: budget/sub-budget attribution, the verify-then-approve second step,
approver comments (`ACOMMENT`/`VCOMMENT`), and stage templates.

### 7.5 `OMS_IRN_LOG` has nothing to do with the OMS app

Its columns are `U_UTL_IRN`, `U_UTL_AckNo`, `U_UTL_QRPT` — Uneecops e-invoicing. 4 rows.
Confidence 85.

### 7.6 `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` stopped 2026-03-26

29,212 rows but `MAX(createdOn) = 2026-03-26`. The live table is the lowercase
`js_budget_approval_workflow` (86 rows in Oil, 40 in Bev). If you sample the big one you
will conclude the integration is dead; it was renamed/rebuilt.

### 7.7 Every UDT is duplicated as `@A*`

`@UTL_MDEXTH` = 17,695 and `@AUTL_MDEXTH` = 17,695. The `@A` twin is SAP's archive table.
Do not double-count.

### 7.8 Credentials live in the SAP DB

`@SERVER.U_Password`/`U_HanaUserId`, `ZCUST_USERS.PASSWORD`, `OLCT.U_SECRET`/`U_CID`.
Note their existence; never select their values into a report.

---

# 8. Confidence and gaps

| Claim | Confidence | What's stopping certainty |
|---|---|---|
| OCLG=0, OSCL=0, OOPR=0, OPRJ=0, OHEM=17 (SAP has no CRM/service/pipeline/projects/workforce) | 98 | `M_TABLES.RECORD_COUNT` is HANA's own row count; I did not `SELECT COUNT(*)` each one individually. Zeroes are unambiguous either way. |
| `U_OMS_Order_No` is junk, not an OMS key | 97 | Value distribution is decisive. Small chance a legacy OMS used 4-digit ids, but 750 rows sharing "4563" rules that out. |
| `ZVENDOR_PORTAL`/`ZCUST_PORTAL` hold pre-SAP drafts incl. rejections | 96 | Status/pushed counts are exact. I did not identify *which* CLI or portal writes them. |
| Full `U_*` inventory (5,572 defs, 222 JIVO-authored names) | 96 | `CUFD` is the definitive registry; population counts are per-field `COUNT()`. |
| UDT inventory + row counts | 96 | via `OUTB` + `M_TABLES`. `ZIA_ASSET_ISSUE_I/O` are registered in `OUTB` but have no `@` table — registry drift. |
| `D_FACTORY_*` / `view_whatsapp_bot` are app-facing windows | 92 | Definitions read in full; the *consumer* is inferred from the name and shape, not observed. |
| `OMS_SP_GST_INVOICE_SAP` belongs to the OMS app | **60** | Name only. Body is a generic GST-invoice print query. Could be an unrelated report prefix. Treat as `U`. |
| `XCLTRLOG` (1,005 rows, Bev) purpose | **U** | Not investigated. |
| `@UNE_USERSEL` (2,449 rows) is config not business data | 85 | Columns are warehouse/user/location codes; I did not read rows. |
| Whether Blinkit/Zepto **sales invoices** are booked in SAP | **not checked** | I only checked BP master presence. The e-com agent must count `OINV` rows for those CardCodes. |

**Not attempted**: the SAP Service Layer (`sapb1 doctor`) — I worked entirely through HANA
direct SQL, which is the stronger evidence anyway. Formatted searches (`OFRM`/`OSCN`) and
alerts (`OALR`/`OALT`) exist but I did not enumerate them; they are a plausible extra
integration surface if someone needs one more place to look.
