# ADVERSARIAL VERIFICATION — finance-approvals-governance

Refuter pass. Date 2026-07-30. 36 rulings attacked.
All queries below were actually executed. Tools:

```
HQ='/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql -env /Users/damanpreetsingh/jivo-cli/connections/hana-tunnel.env'
   (plain connections/hana.env HANGS — it points at the untunnelled host. Use hana-tunnel.env.)
SAPB1_HOST=localhost SAPB1_PORT=15000 /Users/damanpreetsingh/jivo-cli/sap-b1/cli/sapb1 …
   (plain `sapb1 doctor` FAILS — 103.89.45.192:50000 unreachable. There is an SSH tunnel on 15000.)
mcp__postsql__postgres_query  (factory_flow, order_management)
/Users/damanpreetsingh/jivo-cli/control-panel/cli/jivo/jivo …   ← REACHABLE, contra the ruling
/Users/damanpreetsingh/jivo-cli/jsap-cli/jsap-cli …
```

**Reachability corrections to the ruling set (both matter):**
- **The control panel IS reachable from this machine right now.** Every N ruling that
  called itself "negative-space, the Django DB was never located" could have been
  tested live. I tested them. Two of the three collapse on contact (below).
- **The SAP Service Layer IS reachable** via the 127.0.0.1:15000 tunnel;
  `sapb1 query ApprovalRequests` returns rows. Only the direct host is blocked.

---

## HEADLINE — 3 refutations, 1 downgrade, and a resolved open question

### 1. REFUTED: "JSAP budget head / sub-budget catalogue is N" → it is **M**, 16/16 exact

The single most expensive error in the set. SAP's cost-centre dimension 3 is
**literally named "Budget"** and dimension 4 **"Sub Budget"**:

```sql
SELECT * FROM "JIVO_OIL_HANADB"."ODIM";
 1 Variety · 2 Effective Month · 3 Budget · 4 Sub Budget · 5 State

SELECT "PrcCode","PrcName","Active" FROM "JIVO_OIL_HANADB"."OPRC" WHERE "DimCode"=3;
 BackOff · Centr_z3(N) · Del Bkhp · Del Mayp · FACT_COM · Factory · Interest ·
 Med MKT · NPD1 · NPD2 · NPD3 · OTE · R & D · Sal CF · Sales · Sales RE · Transprt
```

`jsap-cli dashboards budgetheads --json` returns **16** heads. SAP dim-3 holds 17,
of which `Centr_z3` is `Active='N'`. Set-differenced in python: **16 in SAP, 0 not in SAP.**
Sub-budgets likewise — `jsap-cli users subbudgets` returns `Centr_z4, CAL CNTR, CSD,
E-COM, GT…`, all present in `OPRC WHERE DimCode=4` (29 members).

The prior agent checked `@BUDGET` (a 1-row stub UDT) and `OBGT` (junk test amounts)
and concluded SAP was not the source. It never looked at `OPRC`/`ODIM` — even though
its own cited evidence (`sapmap/sap-custom.md` §6) says `JS_SYNC_BUDGET` maps
`OcrCode3→Budget, OcrCode4→Sub Budget`. The clue was in the file.

### 2. REFUTED (knock-on): "Budget-vs-actual — only the budget-head tagging is JSAP's"

Wrong. The tagging is a **SAP journal column**, populated and queryable:

```sql
SELECT "OcrCode3" BUDGET, COUNT(*) LINES, SUM("Debit"-"Credit") NET
FROM "JIVO_OIL_HANADB"."JDT1" WHERE "OcrCode3"<>'' AND "RefDate">='2026-04-01'
GROUP BY "OcrCode3" ORDER BY LINES DESC;
 Factory 1135 / 19,29,66,110.89   Sales 996 / 69,86,691.18
 Del Bkhp 785 / 1,50,96,074.37    BackOff 627 / 51,32,089.85
 Interest 569 / 1,24,05,772.75    FACT_COM 330 / 28,00,543.28
 Sales RE 173 / 12,42,913.41      Med MKT 90 / 2,31,287.53  …
```

So budget-vs-actual is **100% M — account, actual and budget head all SAP's.**
Confidence goes UP (88 → 97), not down. Nothing app-side remains in that entity.

### 3. RESOLVED: the "unexplained 8% divergence" — there is none

The ruling flagged JSAP `totalAmount 393,750` vs SAP `DocTotal 425,250` as an
unexplained 8% and warned "the two numbers must never be mixed". Decomposed:

```sql
SELECT j."Line_ID", j."Account", a."AcctName", j."Debit", j."Credit"
FROM JDT1 j JOIN OPCH p ON p."TransId"=j."TransId" WHERE p."DocEntry"=47577;
 2110004 SUNDRY CREDITOR SERVICE            Cr 4,25,250
 2133014 TDS ON RENT @10%                   Cr   39,375
 2131012 INPUT CGST @9%                     Dr   35,437.50
 2131011 INPUT SGST @9%                     Dr   35,437.50
 5660002 RENT                               Dr 3,93,750   ← JSAP's totalAmount, exactly
```

**JSAP reports the pre-tax expense base; SAP's DocTotal is net payable after TDS.**
393,750 + 70,875 GST − 39,375 TDS = 425,250. The "8%" was a coincidence of netting.
The same journal line carries `OcrCode3='Factory'`, matching
`tbl_Draft_Approvals.BUDGET='Factory'` for `DocEntry=51648`.

### 4. DOWNGRADED F→U: credit-limit change requests. No push exists.

```sql
SELECT l."CardCode", MAX(l."NewLimit"), c."CreditLine", c."DebtLine"
FROM "tbl_customerLimit" l JOIN OCRD c ON c."CardCode"=SUBSTR(l."CardCode",1,LENGTH(l."CardCode")-2)
GROUP BY …
 CUSTA000012  3,000,000  vs CreditLine 600,000    DebtLine 10
 CUSTA000119  1,600,000  vs            45,000     DebtLine 10
 CUSTA000751     41,000  vs         5,505,000     DebtLine 10
 …  0 of 17 match either field.
```

And nothing inside SAP consumes it:

```sql
SELECT DEPENDENT_OBJECT_NAME FROM SYS.OBJECT_DEPENDENCIES
WHERE BASE_OBJECT_NAME='tbl_customerLimit' AND DEPENDENT_OBJECT_TYPE IN ('PROCEDURE','VIEW');
 → (empty)
```

Dead since 2025-05-09; `CurrentLimit` is 0 or 10 on every row (it never even read SAP's
real limit). Per the house rule "if you cannot find the push path, downgrade to U" → **U**.

*Also: the ruling conflated two unrelated datasets.* `order_management.credit_limit_logs`
is **live** (11 rows, `jsap_doc_id` 182–192, 2026-07-21→23, parties G PURE INDIA /
PURE AGROCHEM / AGGARWAL AGENCIES / SAKSHI SALES). That is an OMS→JSAP escalation
running today; `tbl_customerLimit` is a corpse from May 2025. Different things.

---

## NEW EVIDENCE THE RULING SET DID NOT HAVE

### A. SAP's posting engine ENFORCES JSAP's budget approval (strengthens F)

`tbl_Draft_Approvals` is a dependency of **`SBO_SP_TRANSACTIONNOTIFICATION`** — SAP B1's
own add/update hook — in **Oil and Beverages**. Two gates read verbatim from the definition:

```
-- ObjType 122 (approval request):
IF EXISTS (SELECT * FROM OWDD OW
           INNER JOIN "tbl_Draft_Approvals" TB ON OW."DraftEntry"=TB."DocEntry"
             AND OW."ObjType"=TB."ObjType"
           WHERE "WddCode"=:list_of_cols_val_tab_del
             AND TB."ApprovedStatus" IN ('A','V') AND OW."Status" IN ('W','N')
             AND TB."DocDate">='20250401') THEN SELECT 1220011, …

-- credit memo / expense posting:
…  AND O."draftKey" NOT IN (SELECT "DocEntry" FROM "tbl_Draft_Approvals"))
THEN SELECT '141112','Budget Not Approved for this  Entry'
```

This is not passive app working-state parked next to SAP. **SAP refuses to post an
expense whose draft has no JSAP budget approval.** `PRODUCTIONORDERSYNC` also appears
in the same hook (offset 15141) — the factory feeder is enforced the same way.
No `ZVENDOR_PORTAL`, `ZCUST_PORTAL`, `tbl_customerLimit`, `JIVO_WA*` or `ZBOM_REQUESTS`
reference exists in the hook.

### B. SAP has a populated party FREEZE mechanism nobody checked

The credit-lock ruling asserted "nothing holds the lock". SAP B1 ships one and JIVO uses it:

```sql
SELECT COUNT(*), SUM(CASE WHEN "frozenFor"='Y' THEN 1 ELSE 0 END),
       COUNT("frozenFrom"), COUNT("frozenTo"),
       SUM(CASE WHEN TRIM(COALESCE("FrozenComm",''))<>'' THEN 1 ELSE 0 END)
FROM OCRD;
 OIL  3390 | frozen 24   | from 0 | to 0 | comment 1
 MART 2183 | frozen 1796 | from 0 | to 0 | comment 8
 BEV  2930 | frozen 88   | from 0 | to 0 | comment 1
```

`validFor='N'` matches `frozenFor='Y'` row-for-row (24/24, 1796/1796, 88/88).
Sampled Oil rows are dead/duplicate master records ("to be created in mart",
cash-sale accounts, defunct vendors) — a **master-data deactivation, not a credit lock**.
`frozenFrom`/`frozenTo` are 0% populated, so SAP has no time-boxed lock.
Net: the N bucket survives, but "SAP has no freeze concept" is false and
*"is this party frozen?" is a SAP question.*

### C. The control-panel's "native business memory" is largely EMPTY

Reached live, 2026-07-30:

| What the ruling claimed | What the live app returns |
|---|---|
| per-invoice ageing `remark` — "real, unrecoverable business memory" | **0 of 4,617 rows** populated (`accounts aging-oil`) |
| `actual_sp` special-price overlay | **0 of 4,617 rows** populated |
| per-party delivery/closing remark | **0 of 162 rows** populated (`credit required-limit`) |
| credit lock `{active, days_left, lock_until}` | `"lock": null` — **no lock active today** |
| claims register — "system of record" | **6 rows**, ₹2,66,899.58, 2 parties, ₹0 passed |

The 2% rule *is* real and verified live: 18,510 × 1.02 = 18,880.2;
total 40,84,05,501.65 × 1.02 = 41,65,73,611.7.

The claims register is genuinely native and genuinely useful —
`reason_of_hold` = "APPROVAL PENDING FROM PRINCE SIR", "DEBIT DOUBLE CLAIM TO JIVO(MAY CLAIM)" —
and I strengthened it: its `ref_inv_no` values (`1030003568 / 2026`, `…3562`, `…3566`)
**exist as OINV DocNum in none of the three SAP schemas** — they are the customer's
document numbers. SAP structurally cannot see them. But it is 6 rows, not a register.

### D. The onboarding portal's push is not clean (F survives, precision does not)

```sql
SELECT "COMPANY","STATUS",COUNT(*),COUNT(DISTINCT "SAP_CARD_CODE") FROM ZVENDOR_PORTAL GROUP BY …
 OIL APPROVED 28 rows → 20 distinct codes      BEV APPROVED 16 → 16
 OIL PENDING 2 → 0 pushed   OIL REJECTED 3 → 0 pushed
ZCUST_PORTAL: APPROVED 12 rows → 7 distinct codes | PENDING 2 → 0 | REJECTED 3 → 0
```

44 approved vendor **rows**, only **36 distinct card codes**. The 8 extras all carry
`VENDA001660`, which exists in **no** company's OCRD — while `VENDA001661…001669` all do.
So the portal recorded a SAP card code for a business partner that was never created.
"Every approved onboarding became a SAP business partner" is false.
The rejected/pending→0-pushed half is exactly right, and that is the load-bearing half.

Dormancy nuance: last approval 2026-05-08, **but** `ZCUST_USERS.LAST_LOGIN` = 2026-07-29.
People still use the portal; approvals stopped.

### E. `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` — the job is alive, the data is dead

The ruling "resolved" a conflict by declaring the table ALIVE off 30 distinct SYNC_TIMESTAMPs.

```sql
SELECT "SYNC_TIMESTAMP", COUNT(*), MAX("createdOn") FROM JS_SYNC_BUDGET_APPROVAL_WORKFLOW GROUP BY 1 ORDER BY 1 DESC;
 2026-07-30 03:15:53.743  212 rows  max createdOn 2026-01-08
 2026-07-30 03:15:53.728 1000 rows  max createdOn 2026-03-26
 … all 30 stamps are 2026-07-30 03:15:53.xxx
```

All 30 stamps are **1,000-row insert batches of a single truncate-and-reload** that ran at
03:15 today. Not 30 syncs. And `MAX(createdOn)` is still **2026-03-26** — the loader
faithfully reloads a dataset whose newest workflow event is four months old.
Both prior probes were half right. Use `tbl_Draft_Approvals` (max DocDate 2026-07-27).

### F. Factory GRPO F upgraded from schema → live

4 of 4 `factory_flow.grpo_grpoposting.sap_doc_num` values resolve to real SAP GRPO headers:
`2026076623`, `2026076622`, `2026076611` → `JIVO_OIL_HANADB.OPDN` (1 row each);
`2026078015` → `JIVO_BEVERAGES_HANADB.OPDN`. Cross-company, and the app knew which.

### G. Smaller corrections

- **SAP audits approvals only as current state.** `OWDD_LOG`=0, `WDD1_LOG`=0, and the
  view `V_WDD_COMPLETE_LOG` returns **0 rows**. SAP holds who/stage/outcome now, not history.
- **`JIVO_WA_SENT` has 38 orphans.** 641 rows / 641 distinct WddCode, but only **603**
  join to `OWDD`. Only 3 distinct `ApprovedBy`.
- **OHEM salary is 0.00, not "17 populated".** The ruling quoted `COUNT(salary)=17` then
  said no salary is recorded — contradictory. `SUM(salary)` = **0 in all three companies**
  (Oil 17, Mart 1, Bev 15). Non-null zeros. The conclusion was right for the wrong reason.
- **Imprest money IS in SAP.** 510 OCRD rows carry `U_Emp_Code` (JWPL####); **96 non-zero**,
  totalling ₹14,47,236.70. The imprest *application* is N; the imprest *account* is M.
- **`ZCUST_USERS` is a live app identity store inside the SAP database** — 13 rows,
  `ROLE` = manager 8 / admin 1 / sap_adder 3 / sr_manager 1, `LAST_LOGIN` 2026-07-29,
  with a `PASSWORD` column. Plus `tbl_SAPRight` (2 rows, time-boxed grants). The RBAC
  ruling's "no @UDT holds an application identity model" is true but misleading.
- **The toolkit-gap claim is overstated.** `sapb1 query ApprovalRequests` and
  `sapb1 query VendorPayments` both work through the tunnel, and both are documented in
  `sap-b1/vault/services/`. The gap that is **real** is `ADOC` — a repo-wide grep for
  `\bADOC\b` in `*.go`/`*.py`/`*.md` returns **zero** hits. Nothing here reads the
  document change log.
- **`OINV."Comments"` is populated on 27,995 of 30,477 Oil invoices** with operator text
  ("JIOMART LUHARI OUTSIDE FEB Based On Deliveries…"). SAP has a per-invoice free-text
  field and people type in it — it is base-document narration, not a collection remark,
  but "SAP has nowhere to put a remark" is wrong.
- **`jsap documents docs` still returns `"Internal server error"`** (re-tested 2026-07-30).
  Third independent audit, still never a single row.
- **`jsap dashboards mom` still returns `[]`.**
- **`jsap inventory active`** returns one session, `sessionName "abc"`, created 2025-11-19;
  `inventory inactive` → "No inactive sessions found". The module is barely used.
- **`jsap bills`**: 998 rows, `vchNumber` 1→973, 968 gaps of exactly 1, **120 distinct
  voucherDates across a 120-day window** (2026-04-01→2026-07-29). Consistent with a
  continuously keyed register — but `voucherDate` is a business date, so it does not
  exclude a nightly import. N vs X remains genuinely open. I did not close it.

---

## M-ruling spot checks — all reproduced exactly

| Ruling | My query | Result |
|---|---|---|
| Party balances | `OCRD` VENDA001347 / VENDA000149 | −50,604,960 · −12461355487/2500 = −4,984,542.1948 ✓ |
| Open A/R (Bev) | `OINV DocStatus='O' AND CANCELED='N'` | 1,168 rows · 177421880353/2500 = ₹7,09,68,752.14 ✓ |
| Open A/P | `OPCH DocEntry=4400` | DocNum 220520405 · VENDA001048 · 10,556 · 'O' ✓ |
| Incoming payments | `ORCT DocNum=726246746` | CUSTA000365 · RAJESHWAR KISHORE MAHENDERPAL · 2026-07-22 · 1,132,770 · OpenBal 20,104.42 ✓ |
| COA | `OACT` 5640001/5300006/4110001 | ADVERTISEMENT · AGENCY CHARGES EXPORT · SALES CANOLA @ 5 % ✓ |
| Credit limit | `OCRD CUSTA000872` | CreditLine 1,250,000 ✓ |
| Drafts | `ODRF GROUP BY DocStatus` | C 43,806 · **O 3,803** ✓ |
| OWDD | full status split | 57,741 · N=1,000 · W=1,671 · Remarks 336 ✓ |
| WDD1 | remarks/approvers | 57,752 · Remarks 1,955 · 23 approvers ✓ |
| ObjType 17 | `OWDD GROUP BY ObjType` | **7** sales-order approvals in 22 months ✓ |
| ADOC/ATC1 | counts + range | 43,054 / 128,739 · 2024-10-01→2026-07-29 ✓ |
| OVPM/VPM2 | counts | 14,356 / 11,469 ✓ |
| Empty modules | `M_TABLES` | OCLG 0 · OSCL 0 · OINC 0 · OIQR 0 · ODPS 0 · OTER 1 · OHEM 17 ✓ |
| Sales hierarchy | `OCRD U_UNE_*` | RSM/ASM/SO/ZONE **0 of 3,390** ✓ · `ZCUST_PORTAL` MGR_* 0 of 17 |
| Service Layer | `sapb1 query ApprovalRequests --top 2` | live rows: StageCode 13, `ardApproved`, UserID 12, DraftEntry 6928 ✓ |

Independent keyword sweep — all tables in all three JIVO schemas matching
`%CLAIM% %TICKET% %TASK% %MOM% %MINUTE% %DOCHUB% %HIERARCH% %REIMBURS% %IMPREST%
%TRAVEL% %EXPENSE% %VOUCHER% %MAKER% %CHECKER% %DISPATCH% %BUNDLE% %COURIER%
%PERMISS% %ROLE% %AUDIT% %PHYSICAL% %AGING% %NOTIF%` → **zero business tables**
(only the budget/approval tables already ruled, plus empty `*_STAGING_DELTA_TABLE`
and `TMP_PREPAREAUDITREPORT*` scratch). The N bucket for tickets, tasks, MoM,
Document Hub, dispatch, claims, RBAC, UI audit trails and integration logs is sound.

---

## What I could NOT settle

1. **`jsap bills` N vs X.** Voucher numbering is dense and daily, which leans N, but a
   nightly import would look identical on business dates. I found no import endpoint,
   but I did not read the JSAP server. Held at N/75.
2. **Whether the control-panel `lock` ever writes to `OCRD.frozenFor`.** Live lock is
   null so there was nothing to compare. The app has `credit-lock|unlock` write endpoints
   (its own DB), which is why I kept N — but this is inference, not proof.
3. **Whether physical stock counts get hand-keyed into SAP as an adjustment.** `OINC`/
   `OIQR`/`ODPS` are 0, but a human feeder leaves no trace there. Unchanged from the ruling.
4. **The control-panel OLIVE 76.2 Cr (SAP) vs 53.0 Cr (app) gap.** I did not test it.
5. **`ZCUST_PORTAL` Beverages codes** do resolve (`CUSTA001140/1141/1154/1159/1160` →
   VD ENTERPRISES, S.K. AGENCY, ZING BEVERAGES AGENCY, SHIVANSH BEVERAGES, YADAV COLD
   DRINK, all created Apr-2026 in `JIVO_BEVERAGES_HANADB.OCRD`). Only the vendor-side
   `VENDA001660` orphan is unexplained.
