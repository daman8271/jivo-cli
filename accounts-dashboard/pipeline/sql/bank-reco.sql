-- ============================================================================
-- bank-reco.sql   ::   section_id "bank-reco"
-- ----------------------------------------------------------------------------
-- WHAT IT RETURNS
--   Everything SAP itself knows about bank reconciliation, per bank / cash /
--   bank-facility G/L account, as of {{ASOF}}, plus one grand TOTAL row.
--   Per account: how many reconciliations SAP has recorded, their date range
--   and the latest, the book balance, how much of it the bank has agreed,
--   the unreconciled receipts and payments (count + value), those unreconciled
--   items aged 30/60/90+, the oldest one, and the gap between the book balance
--   at the last reconciliation date and the balance the bank agreed.
--
--   ONE ROW PER: postable balance-sheet G/L account in the bank / cash /
--   bank-facility universe (ROW_TYPE='ACCOUNT'), plus exactly one
--   ROW_TYPE='TOTAL' row.
--
--   EXPECTED ROW COUNT: tens, hard-bounded by the chart of accounts.
--     Oil 70+1 = 71 · Mart 44+1 = 45 · Beverages 18+1 = 19  (measured live
--     2026-08-21). No document-level fan-out, so it cannot run away.
--
-- ----------------------------------------------------------------------------
-- HEADLINE, AND THE HONEST ANSWER TO "CAN WE DO A BANK RECO FROM SAP?"
--
--   NO -- not a real one. VERIFIED live in all three books on 2026-08-21:
--     * BNK1 = 0 rows and BNK2 = 0 rows in Oil, Mart and Beverages. No bank
--       statement was ever imported into SAP. There are no statement LINES in
--       the system to match anything against.
--     * OBNK is NOT a bank statement table here. It holds exactly ONE row per
--       reconciliation event (COUNT(*) = COUNT(DISTINCT "BankMatch") on every
--       account in every book), carrying a single lump bank-side figure for
--       that month. So SAP records the CONCLUSION of a reconciliation, never
--       the statement it was reconciled against.
--     * Coverage is thin and lopsided: 19 of Oil's 70 accounts have ever been
--       reconciled, 2 of Mart's 44, 2 of Beverages' 18. Mart has 7 OBNK rows
--       in nearly two years of trading.
--     * There are NO CHEQUES anywhere in SAP: RCT1, VPM1, OCHO, OCHH, ODPS and
--       DPS1 are all 0 rows in all three books, and "CheckSum" <> 0 on ZERO
--       uncancelled receipts or payments. JIVO banks 100% by transfer (plus a
--       little cash). A literal "uncleared cheque ageing" is therefore
--       impossible -- there is nothing to age. What this query ages instead is
--       UNRECONCILED BANK LEDGER ITEMS, which is the correct equivalent.
--   What IS possible from SAP alone, and is what this query delivers: which
--   accounts are being reconciled and how current that is, how much of each
--   book balance the bank has agreed, and the size and age of everything the
--   bank has not agreed. That is a reconciliation STATUS report, not a
--   reconciliation.
--
-- ----------------------------------------------------------------------------
-- THE DATA MODEL, AS ACTUALLY VERIFIED (not assumed)
--
--   JDT1."ExtrMatch"  -- the EXTERNAL reconciliation number stamped on a G/L
--       line when it is agreed with the bank. 0 = not agreed. This is the
--       ground truth for "has this bank item cleared".
--       VERIFIED Oil: 24,118 of 526,820 JDT1 lines carry ExtrMatch > 0, and
--       every single one of them sits on one of the 19 reconciled bank
--       accounts (per-account counts sum to exactly 24,118). External
--       reconciliation is used at JIVO for bank accounts and nothing else.
--       Mart 6,084 / 344,144 lines; Beverages 4,262 / 86,414.
--
--   OBNK  -- one row per reconciliation EVENT on an account.
--       "AcctCode"  the G/L account.
--       "BankMatch" the reconciliation number == JDT1."ExtrMatch".  <-- THE JOIN
--       "Sequence"  a per-account row counter (1,2,3...). NOT the
--                   reconciliation number -- see TRAP T2.
--       "DueDate"   the statement / cut-off date. Always a month-end here.
--       "DebAmount"/"CredAmnt"  the bank-side balancing figure for that batch.
--
--   OACT."ExtrMatch"  -- INTEGER, the LAST reconciliation number used on that
--       account (NULL = never reconciled). It is NOT a count -- see TRAP T2.
--
-- ----------------------------------------------------------------------------
-- TRAPS FOUND, AND HOW THIS QUERY HANDLES THEM
--
--   T1  "Internal reconciliation is unused at JIVO" is TRUE OF THE FIELD AND
--       FALSE AS A CONCLUSION, and it is the wrong table for this section
--       anyway. JDT1."IntrnMatch" is 0 on 100% of lines in all three books
--       (VERIFIED: 526,820 / 344,144 / 86,414 lines, zero non-zero), and
--       JDT1."Closed" is 'N' on 100%. But internal reconciliation IS heavily
--       used -- SAP 9.x/10 keeps it in OITR/ITR1 and leaves the legacy JDT1
--       field at 0. Oil has 29,994 OITR headers / 122,801 ITR1 rows dated
--       2024-10-01 through today. It just does not touch bank accounts: only
--       2 of Oil's 122,801 ITR1 rows sit on an account OBNK reconciles; the
--       rest are debtor / creditor control accounts, WIP and GRNI.
--       Handled: this query keys on "ExtrMatch", never "IntrnMatch"; and it
--       carries CO_INTERNAL_RECONS_N / CO_INTRECON_ON_BANK_N so the dashboard
--       can state the distinction instead of repeating the wrong conclusion.
--
--   T2  OBNK."Sequence" IS NOT THE RECONCILIATION NUMBER, and OACT."ExtrMatch"
--       IS NOT A COUNT. They coincide on most accounts, which is what makes
--       this trap dangerous. Oil 2201104 LOAN TERM INDIAN BANK 8021303333 has
--       9 OBNK rows with "Sequence" 1..9 but "BankMatch" 5..13, and
--       OACT."ExtrMatch" = 13 -- so the naive reading reports 13 statements
--       where there are 9, and joins ledger line ExtrMatch=5 to the wrong
--       statement date. Handled: reconciliations are counted as
--       COUNT(DISTINCT "BankMatch") and joined on "BankMatch".
--
--   T3  RECON_TIEOUT_DIFF_L IS A STRUCTURAL INVARIANT, NOT EVIDENCE OF A GOOD
--       RECONCILIATION. SAP will not let you close an external reconciliation
--       unless the selected book lines and the bank-side lines balance, so
--       SUM(reconciled JDT1 net) = -SUM(OBNK "DebAmount"-"CredAmnt") is
--       guaranteed by the software. VERIFIED live at exactly 0.00 on all 23
--       reconciled accounts across the three books -- which proves this query
--       joins correctly and proves nothing whatever about whether the bank
--       actually said those numbers. Kept as a query self-check, labelled as
--       one. Do not present it to an auditor as assurance.
--
--   T4  DOCSTATUS / OPEN-ITEM LOGIC HAS NO PLACE HERE and is not used. Bank
--       clearing state lives in "ExtrMatch" only.
--
--   T5  PICKING BANK ACCOUNTS BY NAME OR CODE PREFIX IS WRONG. '%BANK%' also
--       catches BANK CHARGES and TDS RECOVERABLE FROM BANK; and the code
--       prefix lies -- Oil's 1104106/1104107 carry 1104* codes but hang under
--       2201100 BANK CASH CREDIT LOAN. OACT."ActType" and "CashBox" are
--       useless as selectors (every bank account here is ActType='N',
--       CashBox='N'). Handled: the universe is the postable balance-sheet
--       children of eight named chart-of-accounts drawers resolved through
--       OACT."FatherNum" -- BANK ACCOUNTS, PAYMENT BANK ONLINE, CASH IN HAND,
--       BANK CASH CREDIT LOAN, FDR, TERM LOAN, VEHICLE LOAN, CREDIT CARD --
--       all eight verified present with identical spelling in all three books
--       (Oil 70 postable children, Mart 44, Beverages 18). Any account that
--       has an OBNK row or an OACT."ExtrMatch" is unioned in as a safety net
--       so a reconciled account can never be dropped; live, that net catches
--       nothing, which is itself the check that the drawer list is complete.
--
--   T6  REVERSED / STORNO JOURNAL ENTRIES ARE NOT REMOVED. Both legs post to
--       the ledger and both belong in the balance; removing one would break
--       the tie-out to OACT."CurrTotal". They do inflate line COUNTS and the
--       gross ageing values. Noted, not silently dropped. MEASURED 2026-08-21
--       inside the 90-day-plus unreconciled bucket: Oil 209 lines / 2,881.31 L
--       of 19,464.41 L (14.8%), Mart 284 / 598.08 L of 7,383.00 L (8.1%),
--       Beverages 44 / 27.86 L of 811.11 L (3.4%). Each pair nets to zero, so
--       UNRECONCILED_DIFF_L is unaffected; only the gross ageing is inflated.
--
--   T7  A RECONCILIATION IS NOT DATE-SEQUENTIAL -- an old item can be picked
--       up in a much later batch, so "everything before LAST_RECON_DATE is
--       clear" is false. Handled: STALE_PRE_RECON_N / _L report exactly the
--       items that are still unreconciled although they are dated on or
--       before the last reconciled statement date. Those are the ones that
--       should already have cleared and did not -- the real finding.
--
--   T8  AGEING VALUES ARE GROSS MOVEMENT, NOT NET EXPOSURE. UNREC_0_30_L and
--       friends sum Debit + Credit of the unreconciled lines in that bucket,
--       so a busy current account shows a month of throughput, not an amount
--       at risk. Deliberate: an uncleared item has a size whichever way it
--       points, and a debit/credit pair that nets to zero is still two
--       uncleared items. Read UNRECONCILED_DIFF_L for the net position and
--       UNREC_90PLUS_PAYMENTS_L for the stale money-out figure.
--
--   T9  Every JDT1 read is bounded by "RefDate" <= {{ASOF}} and every OBNK
--       read by "DueDate" <= {{ASOF}}, so an as-of date in the past gives a
--       true as-of answer. (No future-dated bank lines exist today in Oil.)
--
--   T10 A BACK-DATED RUN MUST NOT COUNT A LINE AS RECONCILED BECAUSE OF A
--       RECONCILIATION THAT HAD NOT HAPPENED YET. Batches reach backwards
--       (T7): Oil 2201101 batch #24, statement 2026-05-31, cleared items
--       dated back to 2025-12-26. Testing j."ExtrMatch" > 0 alone would call
--       those items reconciled on an {{ASOF}} of 2025-12-31, months before the
--       reconciliation existed -- and it broke the tie-out, which printed
--       -42.09 lakh instead of 0.00 on that date. Handled: a line counts as
--       reconciled only when its ("Account", "ExtrMatch") matches an OBNK
--       reconciliation whose "DueDate" is itself <= {{ASOF}} (CTE `reckey`).
--       At {{ASOF}} = today this changes nothing (every ExtrMatch value has an
--       OBNK row); on a back-dated run it is the difference between a true
--       as-of answer and a wrong one.
--
--   T11 BRANCH AND INTERCOMPANY ARE PRESENT, ARE DELIBERATELY INCLUDED, AND
--       ARE FLAGGED HERE RATHER THAN WAVED AWAY. The earlier claim that they
--       "do not apply because these are G/L accounts" was wrong on the facts.
--       (a) BRANCH: JDT1."BPLId" IS populated on these bank lines -- Oil
--           spreads over 7 branches (DELHI 16,582 lines, FACTORY 13,459,
--           PUNJAB 579, HARYANA SALES 215, DELHI ISD 11, DELHI INFO 9, HP 8),
--           Mart 7, Beverages 5, and one physical bank account is shared by
--           several branches. This section aggregates ACROSS branches on
--           purpose: a bank account is reconciled as one account against one
--           statement, not per branch. Branch is available in JDT1 for a
--           drill-down; it is not a dimension of a reconciliation.
--       (b) INTERCOMPANY: real money moves between the JIVO books through
--           these accounts. MEASURED 2026-08-21, bank lines sitting in a
--           journal that also touches a JIVO-named related party: Oil 532
--           lines, 30,674.81 L gross / +27,110.25 L net; Mart 486 lines,
--           33,696.35 L gross / -24,731.49 L net; Beverages 3 lines, 40.45 L.
--           The two large ones mirror each other -- Oil receiving what Mart
--           pays. This is INCLUDED and must be: the bank statement shows those
--           transfers, so a reconciliation that netted them out would stop
--           tying to the bank. It is not trade and must never be read as
--           turnover; nothing in this section is a trade figure.
--       (c) The 23 group CardCodes and OCRG '%BRANCH%' tests are BP-side tests
--           and cannot be applied to a G/L account row. Nothing is dropped on
--           branch or intercompany grounds anywhere in this query.
--
--   T12 CURRTOTAL_XCHECK_L is OACT."CurrTotal", SAP's own stored balance. It
--       is LIFETIME-TO-TODAY and will legitimately differ from GL_BAL_L
--       whenever {{ASOF}} is not today. Equal at {{ASOF}} = today is the
--       cross-check; a difference on a back-dated run is not a defect.
--
--   T13 THE TOTAL ROW BLENDS TWO DIFFERENT THINGS, AND A READER WILL MISREAD
--       IT UNLESS IT IS SPLIT. "Unreconciled" here means both "an item on an
--       account we do reconcile that has not cleared" (an exception to chase)
--       and "every line on an account nobody has ever reconciled" (a coverage
--       failure, not an exception). The second dominates. MEASURED 2026-08-21
--       on the 90-day-plus bucket:
--         Oil  15 items / 1,678.18 L on reconciled accounts  vs
--              3,968 items / 17,786.23 L on never-reconciled  (91.4% of it)
--         Mart 142 / 290.77 L  vs  7,236 / 7,092.23 L         (96.1%)
--         Bev  0             vs  1,338 / 811.11 L             (100%)
--       Of Oil's never-reconciled 90-day-plus, 23 items / 863.55 L are the
--       2024-09-30 go-live opening balances -- migrated, not stale.
--       Handled: RECO_STATUS is carried on every ACCOUNT row, so the split is
--       derivable client-side (filter RECO_STATUS LIKE 'RECONCILED%'). It is
--       deliberately NOT pre-split into extra columns -- the data is already
--       there and a second set of totals would be one more thing to keep
--       consistent. Any consumer quoting UNREC_90PLUS_L off the TOTAL row
--       alone is quoting a coverage failure and calling it an exception list.
--
--   T14 THE TOTAL ROW IS EXACTLY ADDITIVE OVER THE ACCOUNT ROWS (verified on
--       all 15 summable columns in all three books). That is convenient and it
--       is also the trap: ROW_TYPE='ACCOUNT' and ROW_TYPE='TOTAL' live in ONE
--       result set, so any consumer that sums a column without filtering
--       ROW_TYPE gets exactly 2x the truth. Filter ROW_TYPE. The CO_* columns
--       are the opposite case -- book-level constants repeated on every row,
--       aggregated with MAX() not SUM() on the TOTAL row; summing those gives
--       71x the truth in Oil.
--
-- ----------------------------------------------------------------------------
-- MONEY UNIT: every money column is suffixed _L and is INR LAKHS
--             (raw INR / 100000, rounded to 2dp). Counts end _N. Dates are
--             'YYYY-MM-DD' strings. Balance sign is the ledger's:
--             POSITIVE = DEBIT (money in the bank / an asset),
--             NEGATIVE = CREDIT (overdraft drawn, loan outstanding).
--             RECEIPTS = ledger debits (money in); PAYMENTS = ledger credits
--             (money out); both reported as positive magnitudes.
--
-- ----------------------------------------------------------------------------
-- EXACT COLUMN LIST (50, in order)
--   ROW_TYPE, ACCT_CODE, ACCT_NAME, DRAWER_NAME, ACCT_KIND, IS_HOUSE_BANK,
--   RECO_STATUS, RECONS_DONE_N, FIRST_RECON_DATE, LAST_RECON_DATE,
--   DAYS_SINCE_RECON_N, LAST_RECON_NO,
--   GL_LINES_N, GL_BAL_L, THROUGHPUT_L, CURRTOTAL_XCHECK_L,
--   REC_LINES_N, RECONCILED_LINES_PCT, REC_RECEIPTS_N, REC_RECEIPTS_L, REC_PAYMENTS_N,
--   REC_PAYMENTS_L, RECONCILED_BAL_L, BANK_SIDE_BAL_L, RECON_TIEOUT_DIFF_L,
--   UNREC_LINES_N, UNREC_RECEIPTS_N, UNREC_RECEIPTS_L, UNREC_PAYMENTS_N,
--   UNREC_PAYMENTS_L, UNRECONCILED_DIFF_L,
--   GL_BAL_AT_LAST_RECON_L, GAP_AT_LAST_RECON_L, MOVEMENT_SINCE_RECON_L,
--   UNREC_0_30_N, UNREC_0_30_L, UNREC_31_60_N, UNREC_31_60_L,
--   UNREC_61_90_N, UNREC_61_90_L, UNREC_90PLUS_N, UNREC_90PLUS_L,
--   UNREC_90PLUS_PAYMENTS_L, OLDEST_UNREC_DATE,
--   STALE_PRE_RECON_N, STALE_PRE_RECON_L,
--   CO_STMT_IMPORT_ROWS_N, CO_CHEQUE_DOCS_N, CO_INTERNAL_RECONS_N,
--   CO_INTRECON_ON_BANK_N
--
-- Placeholders: {{SCHEMA}} = JIVO_OIL_HANADB | JIVO_MART_HANADB |
--               JIVO_BEVERAGES_HANADB ;  {{ASOF}} = YYYY-MM-DD
-- ============================================================================
WITH
drawers AS (
    SELECT "AcctCode" AS DCODE, "AcctName" AS DNAME
    FROM {{SCHEMA}}.OACT
    WHERE "AcctName" IN ('BANK ACCOUNTS','PAYMENT BANK ONLINE','CASH IN HAND',
                         'BANK CASH CREDIT LOAN','FDR','TERM LOAN',
                         'VEHICLE LOAN','CREDIT CARD')
),
acct AS (
    SELECT a."AcctCode" AS ACCT_CODE,
           a."AcctName" AS ACCT_NAME,
           IFNULL(d.DNAME, p."AcctName") AS DRAWER_NAME,
           CASE IFNULL(d.DNAME, '')
                WHEN 'BANK ACCOUNTS'         THEN 'BANK'
                WHEN 'PAYMENT BANK ONLINE'   THEN 'WALLET'
                WHEN 'CASH IN HAND'          THEN 'CASH'
                WHEN 'BANK CASH CREDIT LOAN' THEN 'CASH_CREDIT'
                WHEN 'FDR'                   THEN 'DEPOSIT'
                WHEN 'TERM LOAN'             THEN 'BORROWING'
                WHEN 'VEHICLE LOAN'          THEN 'BORROWING'
                WHEN 'CREDIT CARD'           THEN 'BORROWING'
                ELSE 'OTHER' END AS ACCT_KIND,
           CAST(a."CurrTotal" AS DOUBLE) AS CURRTOTAL
    FROM {{SCHEMA}}.OACT a
    LEFT JOIN drawers d ON d.DCODE = a."FatherNum"
    LEFT JOIN {{SCHEMA}}.OACT p ON p."AcctCode" = a."FatherNum"
    WHERE a."ActType" = 'N'
      AND a."Postable" = 'Y'
      AND ( d.DCODE IS NOT NULL
         OR a."ExtrMatch" IS NOT NULL
         OR a."AcctCode" IN (SELECT "AcctCode" FROM {{SCHEMA}}.OBNK) )
),
house AS (
    SELECT DISTINCT "GLAccount" AS ACCT_CODE
    FROM {{SCHEMA}}.DSC1
    WHERE "GLAccount" IS NOT NULL AND "GLAccount" <> ''
),
stmt AS (
    SELECT "AcctCode"                     AS ACCT_CODE,
           COUNT(DISTINCT "BankMatch")    AS RECONS_N,
           MIN("DueDate")                 AS FIRST_D,
           MAX("DueDate")                 AS LAST_D,
           MAX("BankMatch")               AS LAST_NO,
           SUM(CAST("DebAmount" AS DOUBLE) - CAST("CredAmnt" AS DOUBLE)) AS OBNK_NET
    FROM {{SCHEMA}}.OBNK
    WHERE "DueDate" IS NOT NULL
      AND "DueDate" <= DATE'{{ASOF}}'
    GROUP BY "AcctCode"
),
reckey AS (
    SELECT DISTINCT "AcctCode" AS ACCT_CODE, "BankMatch" AS RECON_NO
    FROM {{SCHEMA}}.OBNK
    WHERE "DueDate" IS NOT NULL
      AND "DueDate" <= DATE'{{ASOF}}'
      AND "BankMatch" IS NOT NULL
),
gl AS (
    SELECT j."Account" AS ACCT_CODE,
           COUNT(*) AS GL_LINES_N,
           SUM(CAST(j."Debit" AS DOUBLE) - CAST(j."Credit" AS DOUBLE)) AS GL_BAL,
           SUM(CAST(j."Debit" AS DOUBLE) + CAST(j."Credit" AS DOUBLE)) AS THRUPUT,

           SUM(CASE WHEN k.RECON_NO IS NOT NULL THEN 1 ELSE 0 END) AS REC_LINES_N,
           SUM(CASE WHEN k.RECON_NO IS NOT NULL AND CAST(j."Debit"  AS DOUBLE) <> 0 THEN 1 ELSE 0 END) AS REC_RCPT_N,
           SUM(CASE WHEN k.RECON_NO IS NOT NULL THEN CAST(j."Debit"  AS DOUBLE) ELSE 0 END) AS REC_RCPT,
           SUM(CASE WHEN k.RECON_NO IS NOT NULL AND CAST(j."Credit" AS DOUBLE) <> 0 THEN 1 ELSE 0 END) AS REC_PAY_N,
           SUM(CASE WHEN k.RECON_NO IS NOT NULL THEN CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS REC_PAY,
           SUM(CASE WHEN k.RECON_NO IS NOT NULL THEN CAST(j."Debit" AS DOUBLE) - CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS REC_BAL,

           SUM(CASE WHEN k.RECON_NO IS NULL THEN 1 ELSE 0 END) AS UNREC_LINES_N,
           SUM(CASE WHEN k.RECON_NO IS NULL AND CAST(j."Debit"  AS DOUBLE) <> 0 THEN 1 ELSE 0 END) AS UNREC_RCPT_N,
           SUM(CASE WHEN k.RECON_NO IS NULL THEN CAST(j."Debit"  AS DOUBLE) ELSE 0 END) AS UNREC_RCPT,
           SUM(CASE WHEN k.RECON_NO IS NULL AND CAST(j."Credit" AS DOUBLE) <> 0 THEN 1 ELSE 0 END) AS UNREC_PAY_N,
           SUM(CASE WHEN k.RECON_NO IS NULL THEN CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS UNREC_PAY,

           SUM(CASE WHEN s.LAST_D IS NOT NULL AND j."RefDate" <= s.LAST_D
                    THEN CAST(j."Debit" AS DOUBLE) - CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS BAL_AT_RECON,
           SUM(CASE WHEN k.RECON_NO IS NULL AND s.LAST_D IS NOT NULL AND j."RefDate" <= s.LAST_D
                    THEN 1 ELSE 0 END) AS STALE_N,
           SUM(CASE WHEN k.RECON_NO IS NULL AND s.LAST_D IS NOT NULL AND j."RefDate" <= s.LAST_D
                    THEN CAST(j."Debit" AS DOUBLE) + CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS STALE_V,

           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') <= 30 THEN 1 ELSE 0 END) AS A030_N,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') <= 30 THEN CAST(j."Debit" AS DOUBLE) + CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS A030_V,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') > 30 AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') <= 60 THEN 1 ELSE 0 END) AS A3160_N,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') > 30 AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') <= 60 THEN CAST(j."Debit" AS DOUBLE) + CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS A3160_V,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') > 60 AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') <= 90 THEN 1 ELSE 0 END) AS A6190_N,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') > 60 AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') <= 90 THEN CAST(j."Debit" AS DOUBLE) + CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS A6190_V,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') > 90 THEN 1 ELSE 0 END) AS A90_N,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') > 90 THEN CAST(j."Debit" AS DOUBLE) + CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS A90_V,
           SUM(CASE WHEN k.RECON_NO IS NULL AND DAYS_BETWEEN(j."RefDate", DATE'{{ASOF}}') > 90 THEN CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS A90_PAY,
           MIN(CASE WHEN k.RECON_NO IS NULL THEN j."RefDate" END) AS OLDEST_UNREC
    FROM {{SCHEMA}}.JDT1 j
    JOIN acct a ON a.ACCT_CODE = j."Account"
    LEFT JOIN stmt s ON s.ACCT_CODE = j."Account"
    LEFT JOIN reckey k ON k.ACCT_CODE = j."Account" AND k.RECON_NO = j."ExtrMatch"
    WHERE j."RefDate" <= DATE'{{ASOF}}'
    GROUP BY j."Account"
),
co AS (
    SELECT (SELECT COUNT(*) FROM {{SCHEMA}}.BNK1) + (SELECT COUNT(*) FROM {{SCHEMA}}.BNK2) AS STMT_IMPORT_N,
           (SELECT COUNT(*) FROM {{SCHEMA}}.ORCT WHERE "Canceled" = 'N' AND CAST("CheckSum" AS DOUBLE) <> 0)
         + (SELECT COUNT(*) FROM {{SCHEMA}}.OVPM WHERE "Canceled" = 'N' AND CAST("CheckSum" AS DOUBLE) <> 0)
         + (SELECT COUNT(*) FROM {{SCHEMA}}.RCT1)
         + (SELECT COUNT(*) FROM {{SCHEMA}}.VPM1)
         + (SELECT COUNT(*) FROM {{SCHEMA}}.OCHO) AS CHEQUE_N,
           (SELECT COUNT(*) FROM {{SCHEMA}}.OITR WHERE "Canceled" = 'N') AS INT_RECON_N,
           (SELECT COUNT(*) FROM {{SCHEMA}}.ITR1
             WHERE "Account" IN (SELECT ACCT_CODE FROM acct)) AS INT_RECON_BANK_N
    FROM DUMMY
),
per_acct AS (
    SELECT a.ACCT_CODE,
           a.ACCT_NAME,
           a.DRAWER_NAME,
           a.ACCT_KIND,
           CASE WHEN h.ACCT_CODE IS NOT NULL THEN 'Y' ELSE 'N' END AS IS_HOUSE_BANK,
           CASE WHEN s.RECONS_N IS NULL AND IFNULL(g.GL_LINES_N,0) = 0 THEN 'DORMANT_NEVER_RECONCILED'
                WHEN s.RECONS_N IS NULL                               THEN 'NEVER_RECONCILED'
                WHEN DAYS_BETWEEN(s.LAST_D, DATE'{{ASOF}}') <= 45     THEN 'RECONCILED_CURRENT'
                WHEN DAYS_BETWEEN(s.LAST_D, DATE'{{ASOF}}') <= 120    THEN 'RECONCILED_LAGGING'
                ELSE 'RECONCILED_STALE' END AS RECO_STATUS,
           IFNULL(s.RECONS_N, 0) AS RECONS_N,
           TO_VARCHAR(s.FIRST_D, 'YYYY-MM-DD') AS FIRST_RECON_DATE,
           TO_VARCHAR(s.LAST_D,  'YYYY-MM-DD') AS LAST_RECON_DATE,
           CASE WHEN s.LAST_D IS NULL THEN NULL ELSE DAYS_BETWEEN(s.LAST_D, DATE'{{ASOF}}') END AS DAYS_SINCE_RECON_N,
           s.LAST_NO AS LAST_RECON_NO,
           IFNULL(g.GL_LINES_N, 0)   AS GL_LINES_N,
           IFNULL(g.GL_BAL, 0)       AS GL_BAL,
           IFNULL(g.THRUPUT, 0)      AS THRUPUT,
           a.CURRTOTAL               AS CURRTOTAL,
           IFNULL(g.REC_LINES_N, 0)  AS REC_LINES_N,
           IFNULL(g.REC_RCPT_N, 0)   AS REC_RCPT_N,
           IFNULL(g.REC_RCPT, 0)     AS REC_RCPT,
           IFNULL(g.REC_PAY_N, 0)    AS REC_PAY_N,
           IFNULL(g.REC_PAY, 0)      AS REC_PAY,
           IFNULL(g.REC_BAL, 0)      AS REC_BAL,
           -IFNULL(s.OBNK_NET, 0)    AS BANK_SIDE_BAL,
           IFNULL(g.UNREC_LINES_N,0) AS UNREC_LINES_N,
           IFNULL(g.UNREC_RCPT_N, 0) AS UNREC_RCPT_N,
           IFNULL(g.UNREC_RCPT, 0)   AS UNREC_RCPT,
           IFNULL(g.UNREC_PAY_N, 0)  AS UNREC_PAY_N,
           IFNULL(g.UNREC_PAY, 0)    AS UNREC_PAY,
           CASE WHEN s.LAST_D IS NULL THEN NULL ELSE IFNULL(g.BAL_AT_RECON, 0) END AS BAL_AT_RECON,
           IFNULL(g.STALE_N, 0)      AS STALE_N,
           IFNULL(g.STALE_V, 0)      AS STALE_V,
           IFNULL(g.A030_N, 0)  AS A030_N,  IFNULL(g.A030_V, 0)  AS A030_V,
           IFNULL(g.A3160_N, 0) AS A3160_N, IFNULL(g.A3160_V, 0) AS A3160_V,
           IFNULL(g.A6190_N, 0) AS A6190_N, IFNULL(g.A6190_V, 0) AS A6190_V,
           IFNULL(g.A90_N, 0)   AS A90_N,   IFNULL(g.A90_V, 0)   AS A90_V,
           IFNULL(g.A90_PAY, 0) AS A90_PAY,
           TO_VARCHAR(g.OLDEST_UNREC, 'YYYY-MM-DD') AS OLDEST_UNREC_DATE,
           c.STMT_IMPORT_N, c.CHEQUE_N, c.INT_RECON_N, c.INT_RECON_BANK_N
    FROM acct a
    LEFT JOIN house h ON h.ACCT_CODE = a.ACCT_CODE
    LEFT JOIN stmt  s ON s.ACCT_CODE = a.ACCT_CODE
    LEFT JOIN gl    g ON g.ACCT_CODE = a.ACCT_CODE
    CROSS JOIN co c
),
out_rows AS (
    SELECT 'ACCOUNT' AS ROW_TYPE,
           ACCT_CODE, ACCT_NAME, DRAWER_NAME, ACCT_KIND, IS_HOUSE_BANK, RECO_STATUS,
           RECONS_N AS RECONS_DONE_N,
           FIRST_RECON_DATE, LAST_RECON_DATE, DAYS_SINCE_RECON_N, LAST_RECON_NO,
           GL_LINES_N,
           ROUND(GL_BAL    / 100000, 2) AS GL_BAL_L,
           ROUND(THRUPUT   / 100000, 2) AS THROUGHPUT_L,
           ROUND(CURRTOTAL / 100000, 2) AS CURRTOTAL_XCHECK_L,
           REC_LINES_N,
           CASE WHEN GL_LINES_N = 0 THEN NULL
                ELSE ROUND(CAST(100.0 * REC_LINES_N / GL_LINES_N AS DOUBLE), 1) END AS RECONCILED_LINES_PCT,
           REC_RCPT_N AS REC_RECEIPTS_N, ROUND(REC_RCPT / 100000, 2) AS REC_RECEIPTS_L,
           REC_PAY_N  AS REC_PAYMENTS_N, ROUND(REC_PAY  / 100000, 2) AS REC_PAYMENTS_L,
           ROUND(REC_BAL        / 100000, 2) AS RECONCILED_BAL_L,
           ROUND(BANK_SIDE_BAL  / 100000, 2) AS BANK_SIDE_BAL_L,
           ROUND((REC_BAL - BANK_SIDE_BAL) / 100000, 2) AS RECON_TIEOUT_DIFF_L,
           UNREC_LINES_N,
           UNREC_RCPT_N AS UNREC_RECEIPTS_N, ROUND(UNREC_RCPT / 100000, 2) AS UNREC_RECEIPTS_L,
           UNREC_PAY_N  AS UNREC_PAYMENTS_N, ROUND(UNREC_PAY  / 100000, 2) AS UNREC_PAYMENTS_L,
           ROUND((GL_BAL - REC_BAL) / 100000, 2) AS UNRECONCILED_DIFF_L,
           ROUND(BAL_AT_RECON / 100000, 2) AS GL_BAL_AT_LAST_RECON_L,
           ROUND((BAL_AT_RECON - BANK_SIDE_BAL) / 100000, 2) AS GAP_AT_LAST_RECON_L,
           ROUND((GL_BAL - BAL_AT_RECON) / 100000, 2) AS MOVEMENT_SINCE_RECON_L,
           A030_N  AS UNREC_0_30_N,   ROUND(A030_V  / 100000, 2) AS UNREC_0_30_L,
           A3160_N AS UNREC_31_60_N,  ROUND(A3160_V / 100000, 2) AS UNREC_31_60_L,
           A6190_N AS UNREC_61_90_N,  ROUND(A6190_V / 100000, 2) AS UNREC_61_90_L,
           A90_N   AS UNREC_90PLUS_N, ROUND(A90_V   / 100000, 2) AS UNREC_90PLUS_L,
           ROUND(A90_PAY / 100000, 2) AS UNREC_90PLUS_PAYMENTS_L,
           OLDEST_UNREC_DATE,
           STALE_N AS STALE_PRE_RECON_N, ROUND(STALE_V / 100000, 2) AS STALE_PRE_RECON_L,
           STMT_IMPORT_N    AS CO_STMT_IMPORT_ROWS_N,
           CHEQUE_N         AS CO_CHEQUE_DOCS_N,
           INT_RECON_N      AS CO_INTERNAL_RECONS_N,
           INT_RECON_BANK_N AS CO_INTRECON_ON_BANK_N
    FROM per_acct
    UNION ALL
    SELECT 'TOTAL',
           NULL, 'ALL BANK / CASH / BANK-FACILITY ACCOUNTS', NULL, NULL, NULL,
           CASE WHEN SUM(CASE WHEN RECONS_N > 0 THEN 1 ELSE 0 END) = 0 THEN 'NEVER_RECONCILED'
                ELSE TO_VARCHAR(SUM(CASE WHEN RECONS_N > 0 THEN 1 ELSE 0 END)) || '_OF_'
                     || TO_VARCHAR(COUNT(*)) || '_ACCOUNTS_RECONCILED' END,
           SUM(RECONS_N), MIN(FIRST_RECON_DATE), MAX(LAST_RECON_DATE),
           MIN(DAYS_SINCE_RECON_N), NULL,
           SUM(GL_LINES_N),
           ROUND(SUM(GL_BAL)    / 100000, 2),
           ROUND(SUM(THRUPUT)   / 100000, 2),
           ROUND(SUM(CURRTOTAL) / 100000, 2),
           SUM(REC_LINES_N),
           CASE WHEN SUM(GL_LINES_N) = 0 THEN NULL
                ELSE ROUND(CAST(100.0 * SUM(REC_LINES_N) / SUM(GL_LINES_N) AS DOUBLE), 1) END,
           SUM(REC_RCPT_N), ROUND(SUM(REC_RCPT) / 100000, 2),
           SUM(REC_PAY_N),  ROUND(SUM(REC_PAY)  / 100000, 2),
           ROUND(SUM(REC_BAL)       / 100000, 2),
           ROUND(SUM(BANK_SIDE_BAL) / 100000, 2),
           ROUND(SUM(REC_BAL - BANK_SIDE_BAL) / 100000, 2),
           SUM(UNREC_LINES_N),
           SUM(UNREC_RCPT_N), ROUND(SUM(UNREC_RCPT) / 100000, 2),
           SUM(UNREC_PAY_N),  ROUND(SUM(UNREC_PAY)  / 100000, 2),
           ROUND(SUM(GL_BAL - REC_BAL) / 100000, 2),
           ROUND(SUM(IFNULL(BAL_AT_RECON, 0)) / 100000, 2),
           ROUND(SUM(IFNULL(BAL_AT_RECON, 0) - BANK_SIDE_BAL) / 100000, 2),
           ROUND(SUM(GL_BAL - IFNULL(BAL_AT_RECON, 0)) / 100000, 2),
           SUM(A030_N),  ROUND(SUM(A030_V)  / 100000, 2),
           SUM(A3160_N), ROUND(SUM(A3160_V) / 100000, 2),
           SUM(A6190_N), ROUND(SUM(A6190_V) / 100000, 2),
           SUM(A90_N),   ROUND(SUM(A90_V)   / 100000, 2),
           ROUND(SUM(A90_PAY) / 100000, 2),
           MIN(OLDEST_UNREC_DATE),
           SUM(STALE_N), ROUND(SUM(STALE_V) / 100000, 2),
           MAX(STMT_IMPORT_N), MAX(CHEQUE_N), MAX(INT_RECON_N), MAX(INT_RECON_BANK_N)
    FROM per_acct
)
SELECT *
FROM out_rows
ORDER BY ROW_TYPE ASC, ABS(GL_BAL_L) DESC, ACCT_CODE ASC
