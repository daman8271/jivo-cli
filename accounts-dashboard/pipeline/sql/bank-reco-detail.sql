-- ============================================================================
-- bank-reco-detail.sql   ::   section_id "bank-reco"  (companion to bank-reco.sql)
-- ----------------------------------------------------------------------------
-- WHY A SECOND QUERY
--   bank-reco.sql answers "what is the reconciliation position of each bank
--   account". It cannot also show the individual reconciliation events without
--   fanning the account grain out. This query is that event log: it is what
--   lets an operator see the CADENCE (is the team reconciling monthly or in
--   catch-up bursts?) and the LAG (how long after the statement date was the
--   reconciliation actually keyed?). Both are the real operational findings,
--   and neither is visible from the per-account summary.
--
--   ONE ROW PER EXTERNAL RECONCILIATION EVENT (one OBNK row = one event;
--   VERIFIED COUNT(*) = COUNT(DISTINCT "BankMatch") on every account in all
--   three books), most recent first.
--
--   EXPECTED ROW COUNT: Oil 201, Mart 7, Beverages 51 (live 2026-08-21).
--   Hard-bounded at 500 by the LIMIT; the whole of OBNK is 201 rows in the
--   largest book, so the limit never actually bites.
--
-- ----------------------------------------------------------------------------
-- THE JOIN, AND THE TRAP IN IT
--   OBNK."BankMatch" -- NOT "Sequence" -- is the external reconciliation number
--   that JDT1."ExtrMatch" carries. "Sequence" is only a per-account row
--   counter. They are equal on most accounts, which is what makes this a trap:
--   Oil 2201104 has "Sequence" 1..9 against "BankMatch" 5..13, so joining on
--   "Sequence" silently attaches every one of its ledger batches to the wrong
--   statement date. Join key here is ("AcctCode", "BankMatch").
--
--   TIEOUT_DIFF_L is 0.00 on every row BY CONSTRUCTION -- SAP refuses to close
--   an external reconciliation whose two sides do not balance. It is a check
--   that this query joined correctly, NOT evidence that the bank agreed. Do
--   not present it as assurance.
--
--   AS-OF: `ev` is bounded by "DueDate" <= {{ASOF}}, so only reconciliations
--   that had happened by the as-of date appear. `led` is deliberately NOT
--   bounded by {{ASOF}}: it sums the whole of each event that survived that
--   filter, which is what "what did this reconciliation clear" means. That is
--   safe because a reconciliation never reaches FORWARD -- VERIFIED 2026-08-21
--   that ZERO of the 24,118 / 6,084 / 4,262 reconciled JDT1 lines in Oil /
--   Mart / Beverages is dated after its own statement date (they reach
--   backwards by up to 547 / 360 / 166 days). So RefDate <= DueDate <= {{ASOF}}
--   holds automatically and no line can leak in from after the as-of date.
--   Re-tested end to end at {{ASOF}} = 2025-12-31: TIEOUT_DIFF_L still 0.00 on
--   every one of the 131 / 5 / 42 rows. If that invariant ever breaks, this
--   CTE needs "RefDate" <= {{ASOF}} and TIEOUT_DIFF_L will go non-zero first.
--
--   LAG_DAYS_N = "CreateDate" - "DueDate": calendar days between the statement
--   cut-off and the day the reconciliation was keyed into SAP.
--
--   OLDEST_ITEM_DATE / MAX_ITEM_AGE_AT_STMT_N show how far back the batch
--   reached. A large value means the batch was a catch-up that swept up months
--   of old items, not a clean month-on-month reconciliation.
--
-- MONEY UNIT: _L columns are INR LAKHS (INR / 100000, 2dp). Counts end _N.
--   RECEIPTS = ledger debits (money in), PAYMENTS = ledger credits (money out),
--   both positive magnitudes. CLEARED_NET_L keeps the ledger sign
--   (positive = net debit).
--
-- EXACT COLUMN LIST (16, in order)
--   ACCT_CODE, ACCT_NAME, RECON_NO, STMT_DATE, PERFORMED_DATE, LAG_DAYS_N,
--   LINES_CLEARED_N, CLEARED_RECEIPTS_N, CLEARED_RECEIPTS_L,
--   CLEARED_PAYMENTS_N, CLEARED_PAYMENTS_L, CLEARED_NET_L, BANK_SIDE_L,
--   TIEOUT_DIFF_L, OLDEST_ITEM_DATE, MAX_ITEM_AGE_AT_STMT_N
--
-- Placeholders: {{SCHEMA}}, {{ASOF}}
-- ============================================================================
WITH
ev AS (
    SELECT b."AcctCode"  AS ACCT_CODE,
           b."BankMatch" AS RECON_NO,
           MIN(b."DueDate")    AS STMT_D,
           MIN(b."CreateDate") AS MADE_D,
           SUM(CAST(b."DebAmount" AS DOUBLE) - CAST(b."CredAmnt" AS DOUBLE)) AS OBNK_NET
    FROM {{SCHEMA}}.OBNK b
    WHERE b."DueDate" IS NOT NULL
      AND b."DueDate" <= DATE'{{ASOF}}'
    GROUP BY b."AcctCode", b."BankMatch"
),
led AS (
    SELECT j."Account" AS ACCT_CODE,
           j."ExtrMatch" AS RECON_NO,
           COUNT(*) AS LINES_N,
           SUM(CASE WHEN CAST(j."Debit"  AS DOUBLE) <> 0 THEN 1 ELSE 0 END) AS RCPT_N,
           SUM(CAST(j."Debit"  AS DOUBLE)) AS RCPT_V,
           SUM(CASE WHEN CAST(j."Credit" AS DOUBLE) <> 0 THEN 1 ELSE 0 END) AS PAY_N,
           SUM(CAST(j."Credit" AS DOUBLE)) AS PAY_V,
           SUM(CAST(j."Debit" AS DOUBLE) - CAST(j."Credit" AS DOUBLE)) AS NET_V,
           MIN(j."RefDate") AS OLDEST_D
    FROM {{SCHEMA}}.JDT1 j
    WHERE j."ExtrMatch" > 0
    GROUP BY j."Account", j."ExtrMatch"
)
SELECT e.ACCT_CODE,
       a."AcctName" AS ACCT_NAME,
       e.RECON_NO,
       TO_VARCHAR(e.STMT_D, 'YYYY-MM-DD') AS STMT_DATE,
       TO_VARCHAR(e.MADE_D, 'YYYY-MM-DD') AS PERFORMED_DATE,
       DAYS_BETWEEN(e.STMT_D, e.MADE_D)   AS LAG_DAYS_N,
       IFNULL(l.LINES_N, 0)               AS LINES_CLEARED_N,
       IFNULL(l.RCPT_N, 0)                AS CLEARED_RECEIPTS_N,
       ROUND(IFNULL(l.RCPT_V, 0) / 100000, 2) AS CLEARED_RECEIPTS_L,
       IFNULL(l.PAY_N, 0)                 AS CLEARED_PAYMENTS_N,
       ROUND(IFNULL(l.PAY_V, 0) / 100000, 2)  AS CLEARED_PAYMENTS_L,
       ROUND(IFNULL(l.NET_V, 0) / 100000, 2)  AS CLEARED_NET_L,
       ROUND(-e.OBNK_NET / 100000, 2)         AS BANK_SIDE_L,
       ROUND((IFNULL(l.NET_V, 0) + e.OBNK_NET) / 100000, 2) AS TIEOUT_DIFF_L,
       TO_VARCHAR(l.OLDEST_D, 'YYYY-MM-DD')   AS OLDEST_ITEM_DATE,
       DAYS_BETWEEN(l.OLDEST_D, e.STMT_D)     AS MAX_ITEM_AGE_AT_STMT_N
FROM ev e
LEFT JOIN led l ON l.ACCT_CODE = e.ACCT_CODE AND l.RECON_NO = e.RECON_NO
LEFT JOIN {{SCHEMA}}.OACT a ON a."AcctCode" = e.ACCT_CODE
ORDER BY e.STMT_D DESC, e.ACCT_CODE ASC, e.RECON_NO DESC
LIMIT 500
