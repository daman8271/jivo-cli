-- ============================================================================
-- customer-ageing.sql  --  A/R ageing SUMMARY, credit-adjusted   (section: customer-ageing)
--
-- WHAT IT RETURNS
--   One row per KIND of customer account, plus one 'ZZ_TOTAL' roll-up row.
--   KIND = BRANCH  : JIVO's own state GST registrations (OCRG group '%BRANCH%')
--          INTERCO : the other JIVO legal entities / units (Oil<->Mart<->Bev)
--          STAFF   : employee imprest "customer" cards (not trade)
--          TRADE   : real external customers  <-- the only collectable book
--   Expected rows: 4 to 5 (one per KIND present + the total). Never more than 5.
--
-- WHY IT IS NOT A NAIVE AGEING
--   Raw open-invoice ageing at JIVO is wrong by ~3x: customer money is banked but
--   never internally reconciled, so the invoice still reads DocStatus='O'.
--   Per customer this query derives
--       UNAPPLIED = max(0, SUM(open invoices) - max(0, OCRD."Balance"))
--   and applies it to the OLDEST invoices first (HANA window function), then ages
--   only what is left. OCRD."Balance" is the ground truth net position, so this
--   absorbs unapplied receipts (ORCT."OpenBal"), unapplied credit notes (ORIN
--   open) and direct journal entries in one step.
--   RAW_OPEN_INR is kept alongside EFF_OPEN_INR so the dashboard can show the
--   naive number next to the real one.
--
-- AS-OF SEMANTICS  (read this before quoting a back-dated figure)
--   {{ASOF}} sets the ageing reference date and excludes documents dated after it.
--   Payments/balances are the CURRENT snapshot -- SAP keeps no per-date history of
--   PaidToDate / Balance. So {{ASOF}} = today is exact; a past {{ASOF}} ages
--   today's open items against an older date and is NOT a true point-in-time A/R.
--
-- COUNT THE CORRECTED BOOK, NOT SAP'S
--   N_CUSTOMERS / N_OPEN_INV are SAP's raw counts: every card with a balance,
--   every invoice still flagged 'O'. After the credit netting most of those
--   invoices carry NOTHING. Quoting them beside EFF_OPEN_INR is the very error
--   this section exists to correct, so the effective counts are returned too:
--     N_EFF_CUSTOMERS = customers who actually carry some of EFF_OPEN_INR
--     N_EFF_INV       = invoices that actually carry some of EFF_OPEN_INR
--   Measured live 2026-08-21, TRADE: Oil 89/355 customers and 1,360/11,489
--   invoices; Mart 23/54 and 674/3,975; Bev 192/361 and 454/796. Pair the
--   money with N_EFF_*; use N_OPEN_INV only to show how wrong SAP's count is.
--
-- COLUMNS (exact order)
--   KIND, N_CUSTOMERS, N_EFF_CUSTOMERS, N_OPEN_INV, N_EFF_INV,
--   RAW_OPEN_INR, UNAPPLIED_CREDIT_INR, EFF_OPEN_INR,
--   NOTDUE_INR, D1_30_INR, D31_60_INR, D61_90_INR, D91_180_INR, D181_365_INR, D365P_INR,
--   OVERDUE_INR, OD60P_INR, MIGRATED_OPEN_INR, BAL_NOT_IN_INV_INR,
--   OCRD_DEBIT_INR, OCRD_CREDIT_INR, UNAPPLIED_RECEIPTS_INR, OPEN_CREDIT_NOTES_INR,
--   OLDEST_OPEN_DUE
--   All money is raw INR (DOUBLE). /10000000 = crore, /100000 = lakh.
--
-- THE TOTAL IS SOLID, THE BUCKET SPLIT IS AN ASSUMPTION -- READ THIS
--   EFF_OPEN_INR does not depend on how the unapplied credit is allocated:
--   whatever order you consume it in, the remainder is the same, = min(open
--   invoices, OCRD debit). Verified live 2026-08-21 -- oldest-first and
--   newest-first give the identical EFF_OPEN_INR to the paisa in all 3 books.
--   The BUCKETS do depend on it, and on Mart severely. Same day, TRADE, 60+
--   days overdue: oldest-first 30.14 L, newest-first 8.46 Cr -- 28x. Oil moves
--   2.90 -> 3.42 Cr (+18%), Bev 3.20 -> 3.24 Cr (+1%). Oldest-first (FIFO) is
--   the accounting convention and is kept, but on Mart the overdue buckets are
--   a LOWER BOUND produced by an assumption, not a measurement. SAP's internal
--   reconciliation is unused here, so there is no fact to replace it with.
--
-- MIGRATED_OPEN_INR IS OIL-ONLY BY FACT, NOT BY BUG
--   The 2024-09-30 date below is SAP go-live. Verified live 2026-08-21: Oil has
--   11,078 invoices dated exactly that day (due dates back to 2017) = the
--   migrated opening A/R. Mart's first invoice is 2024-10-03 and Beverages'
--   2024-10-04, and NEITHER book has an opening batch -- so 0.00 in those two
--   columns is a true zero, not a missed date. If a fourth book is ever added,
--   check its go-live before trusting this column.
--
-- BUILT-IN RECONCILIATION (holds to the rupee, assert it in the pipeline):
--   EFF_OPEN_INR + BAL_NOT_IN_INV_INR = OCRD_DEBIT_INR   for every row.
-- ============================================================================
WITH bp AS (
  SELECT c."CardCode"                       AS CARDCODE,
         c."CardName"                       AS CARDNAME,
         CAST(c."Balance" AS DOUBLE)        AS BAL,
         IFNULL(g."GroupName",'(no group)') AS BPGROUP,
         CASE
           -- (a) JIVO's own state GST registrations: ~116 Cr of fake "debtors"
           WHEN IFNULL(g."GroupName",'') LIKE '%BRANCH%' THEN 'BRANCH'
           -- (b) the other JIVO entities/units. The C-0005 CardCode list is
           --     company-specific and the SAME code is a real shop in another
           --     book (CUSTA000874 = "JIVO MART PVT LTD - DL" in Mart but
           --     "RAKESH BROTHER" in Oil), so the code list is AND-ed with a
           --     name test. Verified live: 'JIVO%' matches every intra-group
           --     card in all 3 books and no external customer.
           WHEN UPPER(c."CardName") LIKE 'JIVO%'
             OR UPPER(c."CardName") LIKE '%A U O JWPL%'
             OR IFNULL(g."GroupName",'') IN ('PARENT COMPANY','COMPANY UNIT CUSTOMER')
             OR ( c."CardCode" IN ('CUSTA000001','CUSTA000002','CUSTA000003','CUSTA000004',
                                   'CUSTA000606','CUSTA000827','CUSTA000874','CUSTA000875',
                                   'CUSTA000876','CUSTA000877','CUSTA000878','CUSTA000906',
                                   'CUSTA000926','CUSTA001099','CUSTA001113')
                  AND UPPER(c."CardName") LIKE 'JIVO%' )
             THEN 'INTERCO'
           WHEN IFNULL(g."GroupName",'') = 'STAFF CUSTOMER' THEN 'STAFF'
           ELSE 'TRADE'
         END AS KIND
  FROM {{SCHEMA}}.OCRD c
  LEFT JOIN {{SCHEMA}}.OCRG g
         ON g."GroupCode" = c."GroupCode" AND g."GroupType" = c."CardType"
  WHERE c."CardType" = 'C'
),
-- Open A/R invoices. "CANCELED" (ONE l) has 3 values here: N, Y (was cancelled)
-- and C (IS the cancelling document); only 'N' is live.
inv AS (
  SELECT "CardCode"                                 AS CARDCODE,
         "DocEntry"                                 AS DOCENTRY,
         CAST("DocDate"    AS DATE)                 AS DOCDATE,
         CAST("DocDueDate" AS DATE)                 AS DUEDATE,
         CAST("DocTotal" - "PaidToDate" AS DOUBLE)  AS OPENAMT
  FROM {{SCHEMA}}.OINV
  WHERE "DocStatus" = 'O'
    AND "CANCELED"  = 'N'
    AND ("DocTotal" - "PaidToDate") > 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
),
tot AS (SELECT CARDCODE, SUM(OPENAMT) AS TOTOPEN, COUNT(*) AS NINV FROM inv GROUP BY CARDCODE),
cr AS (
  SELECT t.CARDCODE, t.TOTOPEN, t.NINV,
         GREATEST(0, t.TOTOPEN - GREATEST(0, IFNULL(b.BAL, t.TOTOPEN))) AS UNAPPLIED
  FROM tot t LEFT JOIN bp b ON b.CARDCODE = t.CARDCODE
),
-- oldest-first running total, so unapplied credit clears the oldest invoice first
run AS (
  SELECT i.CARDCODE, i.DOCDATE, i.DUEDATE, i.OPENAMT, c.UNAPPLIED,
         SUM(i.OPENAMT) OVER (PARTITION BY i.CARDCODE
                              ORDER BY i.DUEDATE, i.DOCENTRY
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS CUM
  FROM inv i JOIN cr c ON c.CARDCODE = i.CARDCODE
),
eff AS (
  SELECT CARDCODE, DOCDATE, DUEDATE,
         DAYS_BETWEEN(DUEDATE, DATE'{{ASOF}}')       AS DAYS_OD,
         GREATEST(0, LEAST(OPENAMT, CUM - UNAPPLIED)) AS EFFOPEN
  FROM run
),
ag AS (
  SELECT CARDCODE,
    SUM(EFFOPEN)                                                        AS EFF_OPEN,
    SUM(CASE WHEN DAYS_OD <=   0                    THEN EFFOPEN ELSE 0 END) AS NOTDUE,
    SUM(CASE WHEN DAYS_OD BETWEEN   1 AND  30       THEN EFFOPEN ELSE 0 END) AS D1_30,
    SUM(CASE WHEN DAYS_OD BETWEEN  31 AND  60       THEN EFFOPEN ELSE 0 END) AS D31_60,
    SUM(CASE WHEN DAYS_OD BETWEEN  61 AND  90       THEN EFFOPEN ELSE 0 END) AS D61_90,
    SUM(CASE WHEN DAYS_OD BETWEEN  91 AND 180       THEN EFFOPEN ELSE 0 END) AS D91_180,
    SUM(CASE WHEN DAYS_OD BETWEEN 181 AND 365       THEN EFFOPEN ELSE 0 END) AS D181_365,
    SUM(CASE WHEN DAYS_OD > 365                     THEN EFFOPEN ELSE 0 END) AS D365P,
    SUM(CASE WHEN DAYS_OD >   0                     THEN EFFOPEN ELSE 0 END) AS OVERDUE,
    SUM(CASE WHEN DAYS_OD >  60                     THEN EFFOPEN ELSE 0 END) AS OD60P,
    -- migrated openings: DocDate = SAP go-live. Their DocDueDate is the TRUE
    -- original date (back to 2017), so the bucket is right, but a 3,000-day
    -- overdue is inherited history, not rot since go-live. Oil only.
    SUM(CASE WHEN DOCDATE = DATE'2024-09-30'        THEN EFFOPEN ELSE 0 END) AS MIGRATED,
    -- invoices left carrying something after the credit netting (see header)
    SUM(CASE WHEN EFFOPEN > 0                       THEN 1 ELSE 0 END)  AS NEFFINV,
    MIN(CASE WHEN EFFOPEN > 0 THEN DUEDATE END)                         AS OLDEST_OPEN_DUE
  FROM eff GROUP BY CARDCODE
),
rc AS (  -- unapplied customer receipts: cash banked, never knocked off an invoice
  SELECT "CardCode" AS CARDCODE,
         SUM(CAST(IFNULL("OpenBal",0) AS DOUBLE)) AS UNAPPLIED_RCPT
  FROM {{SCHEMA}}.ORCT
  WHERE "DocType" = 'C' AND "Canceled" = 'N'        -- ORCT spells it "Canceled"
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  GROUP BY "CardCode"
),
cn AS (  -- unapplied sales credit notes
  SELECT "CardCode" AS CARDCODE,
         SUM(CAST("DocTotal" - "PaidToDate" AS DOUBLE)) AS OPEN_CN
  FROM {{SCHEMA}}.ORIN
  WHERE "DocStatus" = 'O' AND "CANCELED" = 'N'
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  GROUP BY "CardCode"
),
cust AS (  -- one row per customer card, nothing dropped
  SELECT b.CARDCODE, b.KIND, b.BAL,
         IFNULL(c.TOTOPEN,0)    AS RAW_OPEN,
         IFNULL(c.NINV,0)       AS NINV,
         IFNULL(c.UNAPPLIED,0)  AS UNAPPLIED,
         IFNULL(a.EFF_OPEN,0)   AS EFF_OPEN,
         IFNULL(a.NOTDUE,0)     AS NOTDUE,
         IFNULL(a.D1_30,0)      AS D1_30,
         IFNULL(a.D31_60,0)     AS D31_60,
         IFNULL(a.D61_90,0)     AS D61_90,
         IFNULL(a.D91_180,0)    AS D91_180,
         IFNULL(a.D181_365,0)   AS D181_365,
         IFNULL(a.D365P,0)      AS D365P,
         IFNULL(a.OVERDUE,0)    AS OVERDUE,
         IFNULL(a.OD60P,0)      AS OD60P,
         IFNULL(a.MIGRATED,0)   AS MIGRATED,
         IFNULL(a.NEFFINV,0)    AS NEFFINV,
         a.OLDEST_OPEN_DUE      AS OLDEST_OPEN_DUE,
         -- debit sitting in the ledger but carried by no open invoice
         GREATEST(0, b.BAL) - IFNULL(a.EFF_OPEN,0) AS BAL_NOT_IN_INV,
         GREATEST(0, b.BAL)     AS BAL_DR,
         LEAST(0, b.BAL)        AS BAL_CR,
         IFNULL(r.UNAPPLIED_RCPT,0) AS UNAPPLIED_RCPT,
         IFNULL(n.OPEN_CN,0)        AS OPEN_CN
  FROM bp b
  LEFT JOIN cr  c ON c.CARDCODE = b.CARDCODE
  LEFT JOIN ag  a ON a.CARDCODE = b.CARDCODE
  LEFT JOIN rc  r ON r.CARDCODE = b.CARDCODE
  LEFT JOIN cn  n ON n.CARDCODE = b.CARDCODE
)
SELECT
  CASE WHEN GROUPING(KIND) = 1 THEN 'ZZ_TOTAL' ELSE KIND END AS KIND,
  COUNT(CASE WHEN EFF_OPEN > 0 OR BAL <> 0 THEN 1 END)        AS N_CUSTOMERS,
  COUNT(CASE WHEN EFF_OPEN > 0 THEN 1 END)                    AS N_EFF_CUSTOMERS,
  SUM(NINV)                                                   AS N_OPEN_INV,
  SUM(NEFFINV)                                                AS N_EFF_INV,
  ROUND(SUM(RAW_OPEN),2)                                      AS RAW_OPEN_INR,
  ROUND(SUM(UNAPPLIED),2)                                     AS UNAPPLIED_CREDIT_INR,
  ROUND(SUM(EFF_OPEN),2)                                      AS EFF_OPEN_INR,
  ROUND(SUM(NOTDUE),2)                                        AS NOTDUE_INR,
  ROUND(SUM(D1_30),2)                                         AS D1_30_INR,
  ROUND(SUM(D31_60),2)                                        AS D31_60_INR,
  ROUND(SUM(D61_90),2)                                        AS D61_90_INR,
  ROUND(SUM(D91_180),2)                                       AS D91_180_INR,
  ROUND(SUM(D181_365),2)                                      AS D181_365_INR,
  ROUND(SUM(D365P),2)                                         AS D365P_INR,
  ROUND(SUM(OVERDUE),2)                                       AS OVERDUE_INR,
  ROUND(SUM(OD60P),2)                                         AS OD60P_INR,
  ROUND(SUM(MIGRATED),2)                                      AS MIGRATED_OPEN_INR,
  ROUND(SUM(BAL_NOT_IN_INV),2)                                AS BAL_NOT_IN_INV_INR,
  ROUND(SUM(BAL_DR),2)                                        AS OCRD_DEBIT_INR,
  ROUND(SUM(BAL_CR),2)                                        AS OCRD_CREDIT_INR,
  ROUND(SUM(UNAPPLIED_RCPT),2)                                AS UNAPPLIED_RECEIPTS_INR,
  ROUND(SUM(OPEN_CN),2)                                       AS OPEN_CREDIT_NOTES_INR,
  MIN(OLDEST_OPEN_DUE)                                        AS OLDEST_OPEN_DUE
FROM cust
GROUP BY GROUPING SETS ((KIND), ())
ORDER BY KIND
