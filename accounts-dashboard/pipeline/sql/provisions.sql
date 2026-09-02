-- ============================================================================
-- provisions.sql  --  JIVO Provisions & Accruals Register  (section: provisions)
-- ----------------------------------------------------------------------------
-- ONE ROW PER PROVISION / ACCRUAL LIABILITY ACCOUNT that has either a balance
-- or at least one posting on or before {{ASOF}}.
--
-- Expected size: ~35-70 rows per company schema (Oil ~60, Mart ~55, Bev ~45).
--
-- How an account gets into the register (column FAMILY):
--   A_PROVISIONS        - sits under the non-postable title account named
--                         'PROVISIONS'  (2180000 in all 3 books; Bev also has an
--                         empty title 2162000). Found by walking OACT.FatherNum,
--                         NOT by account-code prefix.
--   B_EXPENSES_PAYABLE  - sits under the title account named 'EXPENSES PAYABLE'
--                         (2160000). This is where Oil and Beverages actually
--                         book their monthly freight / salary provisions, so it
--                         MUST be in a provisions register even though the
--                         accounts are named "...PAYABLE".
--   C_OTHER_BY_MEMO     - any other POSTABLE LIABILITY account (GroupMask=2)
--                         that received a journal line whose header Memo or
--                         line memo contains 'PROVISION'. Catches the clearing
--                         accounts JIVO uses off-piste (e.g. Oil 2110008
--                         SUNDRY CREDITORS CLEARING, 2163008 EXPENSE CLEARING).
--
-- SIGNS (SAP-native, matches OCRD.Balance convention used elsewhere at JIVO):
--   NET_DR_MINUS_CR_L  = SUM(Debit) - SUM(Credit).  NEGATIVE = CREDIT = still
--                        provided for.  POSITIVE = DEBIT = over-reversed.
--   OUTSTANDING_CR_L   = the credit balance as a positive number (0 if debit).
--   DEBIT_BAL_L        = the debit balance as a positive number (0 if credit).
--   Verified: OACT."CurrTotal" == SUM(JDT1.Debit) - SUM(JDT1.Credit), exactly,
--   on every account tested.  OACT_CURRTOTAL_L is the lifetime cross-check and
--   will differ from NET_DR_MINUS_CR_L whenever {{ASOF}} is before today.
--
-- AGEING (AGE_0_30_L .. AGE_365P_L):
--   SAP's own G/L internal reconciliation is NOT USED on these accounts -
--   JDT1."IntrnMatch" = 0 and "Closed" = 'N' on 100% of lines in all three
--   books - so SAP cannot say which provision is still open. We therefore
--   apply FIFO: debits (reversals / utilisation) consume the OLDEST credits
--   first, and whatever credit is left un-consumed is aged by its own RefDate.
--   This is deliberately conservative: it ages the residual as old as possible.
--   SUM of the four buckets equals OUTSTANDING_CR_L exactly. The FIFO runs on
--   the SIGNED movement (Credit - Debit), not on the raw "Credit" column, so a
--   line booked as a negative Credit still consumes. Before that fix
--   (2026-08-21) Oil 2110008 aged 34.53 L against a 33.93 L balance.
--   CROSSED_YEAREND_L and MIGRATED_OPENING_L are re-cuts of that SAME residual,
--   NOT extra buckets - never add them to the four AGE_* columns.
--
-- DATES: JDT1."RefDate" is used throughout (verified identical to
--   OJDT."RefDate" on 12,576/12,576 provision lines).  JIVO dates journal
--   entries by reference date, not posting date.
--
-- COLUMNS RETURNED (30):
--   COMPANY_SCHEMA, AS_OF, FAMILY, ACCT_CODE, ACCT_NAME, PARENT_NAME,
--   N_LINES, FIRST_POST, LAST_POST, DAYS_SINCE_LAST_POST,
--   CREATED_CR_L, REVERSED_DR_L, NET_DR_MINUS_CR_L, OUTSTANDING_CR_L,
--   DEBIT_BAL_L, OACT_CURRTOTAL_L, CREATED_FYTD_L, REVERSED_FYTD_L,
--   AGE_0_30_L, AGE_31_90_L, AGE_91_365_L, AGE_365P_L,
--   OLDEST_OPEN_DATE, OLDEST_OPEN_DAYS, CROSSED_YEAREND_L,
--   MIGRATED_OPENING_L, NEVER_REVERSED, DEBIT_BALANCE_FLAG,
--   MANUAL_JE_PCT, PROV_MEMO_CR_L
--   (all *_L amounts are INR LAKHS, rounded to 2dp)
-- ============================================================================
WITH
params AS (
  SELECT DATE'{{ASOF}}' AS ASOF,
         DATE'2024-09-30' AS GOLIVE,
         CASE WHEN MONTH(DATE'{{ASOF}}') >= 4
              THEN TO_DATE(TO_VARCHAR(YEAR(DATE'{{ASOF}}'))   || '-04-01','YYYY-MM-DD')
              ELSE TO_DATE(TO_VARCHAR(YEAR(DATE'{{ASOF}}')-1) || '-04-01','YYYY-MM-DD')
         END AS FY_START
  FROM DUMMY
),
-- non-postable title accounts that head a provision / accrual family
roots AS (
  SELECT "AcctCode" AS RC,
         CASE UPPER(TRIM("AcctName"))
              WHEN 'PROVISIONS'       THEN 'A_PROVISIONS'
              WHEN 'EXPENSES PAYABLE' THEN 'B_EXPENSES_PAYABLE'
         END AS FAM
  FROM {{SCHEMA}}.OACT
  WHERE "Postable" = 'N'
    AND UPPER(TRIM("AcctName")) IN ('PROVISIONS','EXPENSES PAYABLE')
),
-- walk OACT.FatherNum up to 4 hops to find each postable account's family root
fam AS (
  SELECT a."AcctCode" AS ACCT,
         COALESCE(r0.FAM, r1.FAM, r2.FAM, r3.FAM, r4.FAM) AS FAMILY
  FROM {{SCHEMA}}.OACT a
  LEFT JOIN roots r0            ON r0.RC          = a."AcctCode"
  LEFT JOIN {{SCHEMA}}.OACT p1  ON p1."AcctCode"  = a."FatherNum"
  LEFT JOIN roots r1            ON r1.RC          = p1."AcctCode"
  LEFT JOIN {{SCHEMA}}.OACT p2  ON p2."AcctCode"  = p1."FatherNum"
  LEFT JOIN roots r2            ON r2.RC          = p2."AcctCode"
  LEFT JOIN {{SCHEMA}}.OACT p3  ON p3."AcctCode"  = p2."FatherNum"
  LEFT JOIN roots r3            ON r3.RC          = p3."AcctCode"
  LEFT JOIN {{SCHEMA}}.OACT p4  ON p4."AcctCode"  = p3."FatherNum"
  LEFT JOIN roots r4            ON r4.RC          = p4."AcctCode"
  WHERE a."Postable" = 'Y'
),
-- liability accounts that received a journal line memo-tagged 'PROVISION'
memo_acct AS (
  SELECT DISTINCT j."Account" AS ACCT
  FROM {{SCHEMA}}.JDT1 j
  JOIN {{SCHEMA}}.OJDT h ON h."TransId" = j."TransId"
  JOIN {{SCHEMA}}.OACT a ON a."AcctCode" = j."Account"
  CROSS JOIN params pr
  WHERE a."GroupMask" = 2
    AND a."Postable"  = 'Y'
    AND TO_DATE(j."RefDate") <= pr.ASOF
    AND (   UPPER(IFNULL(h."Memo",''))     LIKE '%PROVISION%'
         OR UPPER(IFNULL(j."LineMemo",'')) LIKE '%PROVISION%' )
),
reg AS (
  SELECT ACCT, MIN(FAMILY) AS FAMILY FROM (
    SELECT ACCT, FAMILY        FROM fam       WHERE FAMILY IS NOT NULL
    UNION ALL
    SELECT ACCT, 'C_OTHER_BY_MEMO' FROM memo_acct
  ) GROUP BY ACCT
),
-- every posting on a register account, up to the as-of date
lines AS (
  SELECT r.ACCT, r.FAMILY,
         TO_DATE(j."RefDate") AS RD, j."TransId" AS TID, j."Line_ID" AS LID,
         CAST(j."Debit"  AS DOUBLE) AS DR,
         CAST(j."Credit" AS DOUBLE) AS CR,
         -- SIGNED movement, credit-positive. JIVO's books carry a handful of
         -- lines posted with a NEGATIVE Credit (or negative Debit) instead of
         -- the opposite column - live example: Oil 2110008 SUNDRY CREDITORS
         -- CLEARING has one Credit of -60,030. SUM("Credit") nets those away
         -- correctly, but a FIFO built on "Credit > 0" silently skips them, so
         -- the age buckets came out 60,030 HIGHER than OUTSTANDING_CR_L.
         -- Verified 2026-08-21 that no JDT1 line in any of the three books has
         -- BOTH Debit and Credit non-zero, so NET_CR is exactly one signed
         -- amount and equals CR (or -DR) on every ordinary line.
         CAST(j."Credit" AS DOUBLE) - CAST(j."Debit" AS DOUBLE) AS NET_CR,
         CASE WHEN j."TransType" = '30' THEN 1 ELSE 0 END AS MANUAL_JE,
         CASE WHEN UPPER(IFNULL(h."Memo",''))     LIKE '%PROVISION%'
                OR UPPER(IFNULL(j."LineMemo",'')) LIKE '%PROVISION%'
              THEN 1 ELSE 0 END AS PMEMO
  FROM reg r
  JOIN {{SCHEMA}}.JDT1 j ON j."Account"  = r.ACCT
  JOIN {{SCHEMA}}.OJDT h ON h."TransId"  = j."TransId"
  CROSS JOIN params pr
  WHERE TO_DATE(j."RefDate") <= pr.ASOF
),
agg AS (
  SELECT ACCT,
         COUNT(*)      AS N_LINES,
         MIN(RD)       AS FIRST_POST,
         MAX(RD)       AS LAST_POST,
         SUM(DR)       AS TOT_DR,
         SUM(CR)       AS TOT_CR,
         SUM(CASE WHEN RD >= (SELECT FY_START FROM params) THEN CR ELSE 0 END) AS CR_FYTD,
         SUM(CASE WHEN RD >= (SELECT FY_START FROM params) THEN DR ELSE 0 END) AS DR_FYTD,
         SUM(CASE WHEN PMEMO = 1 THEN CR ELSE 0 END) AS CR_PMEMO,
         SUM(CASE WHEN MANUAL_JE = 1 THEN DR + CR ELSE 0 END) AS MOVE_MANUAL,
         SUM(DR + CR) AS MOVE_ALL,
         -- everything that CONSUMES a provision: real debits plus any line
         -- booked as a negative credit. Guarantees SUM(RESID) == TOT_CR-TOT_DR.
         SUM(CASE WHEN NET_CR < 0 THEN -NET_CR ELSE 0 END) AS TOT_CONSUME
  FROM lines GROUP BY ACCT
),
-- FIFO: oldest credit first; total debits consume them in order
credits AS (
  SELECT l.ACCT, l.RD, l.NET_CR AS CR,
         SUM(l.NET_CR) OVER (PARTITION BY l.ACCT
                         ORDER BY l.RD, l.TID, l.LID
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS CUM_CR
  FROM lines l WHERE l.NET_CR > 0
),
resid AS (
  -- >= 0.01 tolerance: the running totals are DOUBLE (DECIMAL would overflow on
  -- the 5,800-line COGS PAYABLE account), and a credit line that FIFO consumes
  -- EXACTLY leaves a ~1e-7 float residue. Without the tolerance that residue is
  -- rounded away in the money columns but still counts as "open" for
  -- OLDEST_OPEN_DATE, which then reports a fully-reversed provision as 386 days
  -- old. Seen live on Mart 2180014 PROVISION FOR JULY.
  SELECT * FROM (
    SELECT c.ACCT, c.RD,
           GREATEST(0, LEAST(c.CR, c.CUM_CR - g.TOT_CONSUME)) AS RESID
    FROM credits c JOIN agg g ON g.ACCT = c.ACCT
  ) WHERE RESID >= 0.01
),
aged AS (
  SELECT r.ACCT,
         SUM(CASE WHEN DAYS_BETWEEN(r.RD, pr.ASOF) <= 30                       THEN r.RESID ELSE 0 END) AS A0,
         SUM(CASE WHEN DAYS_BETWEEN(r.RD, pr.ASOF) BETWEEN  31 AND  90         THEN r.RESID ELSE 0 END) AS A1,
         SUM(CASE WHEN DAYS_BETWEEN(r.RD, pr.ASOF) BETWEEN  91 AND 365         THEN r.RESID ELSE 0 END) AS A2,
         SUM(CASE WHEN DAYS_BETWEEN(r.RD, pr.ASOF) > 365                       THEN r.RESID ELSE 0 END) AS A3,
         SUM(CASE WHEN r.RD <  pr.FY_START                                     THEN r.RESID ELSE 0 END) AS A_YE,
         SUM(CASE WHEN r.RD =  pr.GOLIVE                                       THEN r.RESID ELSE 0 END) AS A_MIG,
         MIN(r.RD) AS OLDEST_OPEN
  FROM resid r CROSS JOIN params pr
  GROUP BY r.ACCT
)
SELECT
  '{{SCHEMA}}'                                             AS COMPANY_SCHEMA,
  pr.ASOF                                                  AS AS_OF,
  reg.FAMILY                                               AS FAMILY,
  reg.ACCT                                                 AS ACCT_CODE,
  a."AcctName"                                             AS ACCT_NAME,
  IFNULL(pa."AcctName",'')                                 AS PARENT_NAME,
  IFNULL(g.N_LINES,0)                                      AS N_LINES,
  g.FIRST_POST                                             AS FIRST_POST,
  g.LAST_POST                                              AS LAST_POST,
  DAYS_BETWEEN(g.LAST_POST, pr.ASOF)                       AS DAYS_SINCE_LAST_POST,
  ROUND(IFNULL(g.TOT_CR,0)/100000, 2)                      AS CREATED_CR_L,
  ROUND(IFNULL(g.TOT_DR,0)/100000, 2)                      AS REVERSED_DR_L,
  ROUND((IFNULL(g.TOT_DR,0)-IFNULL(g.TOT_CR,0))/100000, 2) AS NET_DR_MINUS_CR_L,
  ROUND(GREATEST(0, IFNULL(g.TOT_CR,0)-IFNULL(g.TOT_DR,0))/100000, 2) AS OUTSTANDING_CR_L,
  ROUND(GREATEST(0, IFNULL(g.TOT_DR,0)-IFNULL(g.TOT_CR,0))/100000, 2) AS DEBIT_BAL_L,
  ROUND(CAST(a."CurrTotal" AS DOUBLE)/100000, 2)           AS OACT_CURRTOTAL_L,
  ROUND(IFNULL(g.CR_FYTD,0)/100000, 2)                     AS CREATED_FYTD_L,
  ROUND(IFNULL(g.DR_FYTD,0)/100000, 2)                     AS REVERSED_FYTD_L,
  ROUND(IFNULL(ag.A0,0)/100000, 2)                         AS AGE_0_30_L,
  ROUND(IFNULL(ag.A1,0)/100000, 2)                         AS AGE_31_90_L,
  ROUND(IFNULL(ag.A2,0)/100000, 2)                         AS AGE_91_365_L,
  ROUND(IFNULL(ag.A3,0)/100000, 2)                         AS AGE_365P_L,
  ag.OLDEST_OPEN                                           AS OLDEST_OPEN_DATE,
  DAYS_BETWEEN(ag.OLDEST_OPEN, pr.ASOF)                    AS OLDEST_OPEN_DAYS,
  ROUND(IFNULL(ag.A_YE,0)/100000, 2)                       AS CROSSED_YEAREND_L,
  ROUND(IFNULL(ag.A_MIG,0)/100000, 2)                      AS MIGRATED_OPENING_L,
  CASE WHEN IFNULL(g.TOT_CR,0) > 0 AND IFNULL(g.TOT_DR,0) = 0 THEN 'Y' ELSE 'N' END AS NEVER_REVERSED,
  CASE WHEN IFNULL(g.TOT_DR,0) - IFNULL(g.TOT_CR,0) > 1      THEN 'Y' ELSE 'N' END AS DEBIT_BALANCE_FLAG,
  CASE WHEN IFNULL(g.MOVE_ALL,0) = 0 THEN NULL
       ELSE ROUND(100.0 * g.MOVE_MANUAL / g.MOVE_ALL, 1) END AS MANUAL_JE_PCT,
  ROUND(IFNULL(g.CR_PMEMO,0)/100000, 2)                    AS PROV_MEMO_CR_L
FROM reg
JOIN {{SCHEMA}}.OACT a       ON a."AcctCode"  = reg.ACCT
LEFT JOIN {{SCHEMA}}.OACT pa ON pa."AcctCode" = a."FatherNum"
LEFT JOIN agg   g            ON g.ACCT        = reg.ACCT
LEFT JOIN aged  ag           ON ag.ACCT       = reg.ACCT
CROSS JOIN params pr
WHERE (
        -- every dedicated PROVISION account is listed, even if never used
        reg.FAMILY = 'A_PROVISIONS'
        -- accrual accounts: only if they actually moved or hold a balance
     OR (reg.FAMILY = 'B_EXPENSES_PAYABLE'
         AND (IFNULL(g.N_LINES,0) > 0 OR ABS(CAST(a."CurrTotal" AS DOUBLE)) > 1))
        -- off-piste accounts: only if provisioning is a MATERIAL part of what
        -- the account does. Without this gate the memo rule drags in the bank
        -- CC account, the vendor control account and every TDS-withholding
        -- account, because a provision JE happened to touch them once.
     OR (reg.FAMILY = 'C_OTHER_BY_MEMO'
         AND IFNULL(g.CR_PMEMO,0) >= 500000
         AND IFNULL(g.CR_PMEMO,0) >= 0.25 * IFNULL(g.TOT_CR,0))
      )
ORDER BY reg.FAMILY,
         GREATEST(0, IFNULL(g.TOT_CR,0)-IFNULL(g.TOT_DR,0)) DESC,
         reg.ACCT
