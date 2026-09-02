-- =====================================================================
-- customer-ageing-detail.sql   (section: customer-ageing-detail)   as-of {{ASOF}}
-- ---------------------------------------------------------------------
-- WHAT IT RETURNS
--   Credit-adjusted A/R ageing, ONE ROW PER CUSTOMER with bucket COLUMNS
--   (not one row per customer per bucket).  This is the per-customer
--   drill-down behind customer-ageing.sql; it is the A/R twin of
--   vendor-ageing.sql and deliberately mirrors that file's column shape
--   so one dashboard renderer serves both sections.
--
--   Scope = every CardType='C' card in {{SCHEMA}} that has any of:
--   an open A/R invoice, a non-zero OCRD."Balance", an unapplied
--   incoming payment, or an open A/R credit note.  Cards that are flat
--   zero on all four are dropped (they contribute nothing anywhere).
--   Expected rows (measured live 2026-08-21): 641 Oil / 100 Mart / 454 Bev.
--   Hundreds, never thousands.  Ordered worst-first by 60+ overdue,
--   TRADE before the flagged BRANCH / INTERCO / STAFF rows.
--
-- WHY "CREDIT-ADJUSTED"
--   A naive OINV ageing is wrong at JIVO by 1.3x to 12x depending on the
--   book -- measured live 2026-08-21, raw open vs credit-adjusted:
--       Oil  180.69 Cr -> 108.86 Cr (1.7x); TRADE alone 75.71 -> 7.43 (10.2x)
--       Mart 128.12 Cr ->  15.90 Cr (8.1x); TRADE alone 112.04 -> 9.34 (12.0x)
--       Bev    6.34 Cr ->   4.81 Cr (1.3x); TRADE alone  5.00 -> 3.85 (1.3x)
--   The error is worst exactly where it matters, on the TRADE book.  Customer
--   money is banked and invoices are knocked off by manual journal
--   entries (JDT1 TransType 30) and by on-account receipts that were
--   never internally reconciled, so OINV."DocStatus" stays 'O' long
--   after the cash arrived.  OCRD."Balance" is the only ground truth.
--   So per customer:
--       RECEIVABLE = GREATEST(0,  OCRD."Balance")   -- what is really due
--       CREDIT     = GREATEST(0, SUM(open invoices) - RECEIVABLE)
--   CREDIT is consumed OLDEST-DUE-INVOICE-FIRST with a running window
--   sum, and only the remainder is aged.  Identity (exact, per customer):
--       SUM(B0..B6) + UNBACKED_CREDIT = RECEIVABLE
--   and ADJ_OPEN = SUM(B0..B6) = RAW_OPEN - CREDIT_APPLIED.
--
-- RECONCILES TO THE SUMMARY (customer-ageing.sql), EXACTLY
--   Same OCRG/name classification, same OINV / ORCT / ORIN filters, same
--   {{ASOF}} cut-off, same buckets.  Summing these rows by ACCT_KIND
--   reproduces customer-ageing.sql row for row, to the rupee:
--       SUM(RAW_OPEN)        -> RAW_OPEN_INR
--       SUM(CREDIT_APPLIED)  -> UNAPPLIED_CREDIT_INR
--       SUM(ADJ_OPEN)        -> EFF_OPEN_INR
--       SUM(B0..B6)          -> NOTDUE_INR .. D365P_INR
--       SUM(UNBACKED_CREDIT) -> BAL_NOT_IN_INV_INR
--       SUM(MIGRATED_OPEN)   -> MIGRATED_OPEN_INR
--       SUM(RECEIVABLE)      -> OCRD_DEBIT_INR
--       -SUM(CUSTOMER_ADVANCE)-> OCRD_CREDIT_INR   (advance is stored +ve here)
--       SUM(UNAPPLIED_RCPT)  -> UNAPPLIED_RECEIPTS_INR
--       SUM(OPEN_CN)         -> OPEN_CREDIT_NOTES_INR
--       MIN(OLDEST_DUE)      -> OLDEST_OPEN_DUE
--   Verified live 2026-08-21: 105 checks per book, 315 across the three
--   books.  All 307 money and date checks tie.  The only 8 failures are
--   the N_CUSTOMERS headcount (see below), never an amount.  Largest
--   drift anywhere is 0.10 rupee on Oil's UNAPPLIED_RECEIPTS across 641
--   rows -- that is per-row ROUND(x,2) here vs the summary's
--   sum-then-round, not a difference in the numbers.
--
--   ROW COUNT is the one thing that does NOT match, for two known and
--   harmless reasons -- read this before writing a count assertion:
--     (i)  this file keeps cards that exist only as an unapplied receipt
--          or an open credit note (zero balance, no open invoice); the
--          summary's N_CUSTOMERS ignores them.  641 rows vs 378 counted.
--     (ii) applying the summary's own rule to THIS file's output still
--          gives 353, not 378, because 25 Oil cards (3 Mart, 9 Bev) carry
--          sub-paise dust balances -- smallest 0.0001, all 25 together
--          worth -0.0377 rupee -- which are "Balance <> 0" in SQL but
--          round to 0.00 in the 2-dp output column.
--   So assert the MONEY, not the headcount.
--
-- MONEY UNITS: every money column is INR RUPEES (no _L / _CR suffix
--   anywhere), rounded to 2 dp, so the reconciliation ties to the rupee.
--   The dashboard divides by 1e5 (lakh) / 1e7 (crore) for display.
--
-- COLUMN LIST (exact, in order -- 40 columns, positionally identical to
-- vendor-ageing.sql; PAY/BILL/VENDOR names become RCPT/INV/CUSTOMER):
--   CARD_CODE, CARD_NAME, CUSTOMER_GROUP, ACCT_KIND, IS_EXCLUDED,
--   OCRD_BALANCE, RECEIVABLE, CUSTOMER_ADVANCE,
--   N_OPEN_INV, RAW_OPEN, CREDIT_APPLIED, ADJ_OPEN, UNBACKED_CREDIT,
--   MIGRATED_OPEN, BACKDATED_DUE_OPEN, OLDEST_DUE, DAYS_OLDEST,
--   B0_NOTDUE, B1_1_30, B2_31_60, B3_61_90, B4_91_180, B5_181_365,
--   B6_365PLUS, ADJ_OVERDUE_60PLUS,
--   N_UNAPPLIED_RCPT, UNAPPLIED_RCPT, N_OPEN_CN, OPEN_CN,
--   CO_RAW_OPEN, CO_RECEIVABLE, CO_ADJ_OPEN, CO_UNBACKED_CREDIT,
--   CO_UNAPPLIED_RCPT, CO_OPEN_CN, CO_CUSTOMER_ADVANCE,
--   CO_MIGRATED_OPEN, CO_BACKDATED_DUE_OPEN,
--   CO_ADJ_OPEN_TRADE, CO_ADJ_OVERDUE_60PLUS_TRADE
--   (the CO_* columns are company-level totals repeated on every row -
--    that is the reconciliation, read it off any single row.)
--
-- COLUMN MEANINGS THAT ARE NOT OBVIOUS
--   OCRD_BALANCE     signed, JIVO convention: +ve = DEBIT (customer owes
--                    JIVO), -ve = CREDIT (JIVO owes the customer).
--   RECEIVABLE       = GREATEST(0, OCRD_BALANCE).  Ground truth.
--   CUSTOMER_ADVANCE = GREATEST(0, -OCRD_BALANCE), reported POSITIVE.
--                      Money held against a customer: advance received,
--                      or over-collection.  (vendor-ageing's slot 8 is
--                      VENDOR_ADVANCE = GREATEST(0, +Balance); same idea,
--                      opposite sign, because A/R and A/P sit on
--                      opposite sides of OCRD."Balance".)
--   UNBACKED_CREDIT  keeps vendor-ageing's slot-13 NAME so the renderer
--                    is shared, but on the A/R side it is an unbacked
--                    DEBIT: = GREATEST(0, RECEIVABLE - RAW_OPEN), i.e.
--                    ledger debit carried by NO open invoice (settled by
--                    journal, or a debit note / on-account charge).
--                    It is the summary's BAL_NOT_IN_INV_INR.
--   ADJ_OVERDUE_60PLUS = B3+B4+B5+B6 = strictly more than 60 days past
--                    due, after credit.  This is the collection list.
--
-- TRAPS AND HOW THEY ARE HANDLED
--   1. DocStatus='O' is NOT solvency at JIVO -> see "credit-adjusted".
--   2. Do NOT subtract ORCT."OpenBal" from the balance.  Unapplied
--      receipts are ALREADY inside OCRD."Balance"; subtracting them
--      double-counts.  UNAPPLIED_RCPT and OPEN_CN are DIAGNOSTICS ONLY
--      and are never netted off.  (Oil: 65.9 Cr of receipts banked but
--      never knocked off, against a 108.9 Cr book.)
--   3. "CANCELED" on OINV/ORIN is ONE l and has THREE values: 'N' live,
--      'Y' was cancelled, 'C' IS the cancelling document.  Only 'N'.
--      ORCT spells it "Canceled" -- different table, different spelling.
--   4. Branch + intercompany are NOT trade.  Oil's BRANCH block alone is
--      77.6 Cr of "debtors" that are JIVO's own state GST registrations.
--      They are FLAGGED (IS_EXCLUDED=1, ACCT_KIND), never dropped.
--      A group-only test is not enough: the same CardCode is a real shop
--      in another book (CUSTA000874 = "JIVO MART PVT LTD - DL" in Mart
--      but "RAKESH BROTHER" in Oil), so the C-0005 code list is AND-ed
--      with a name test, and a 'JIVO%' name test stands on its own.
--   5. STAFF ('STAFF CUSTOMER' group) = employee imprest cards, not
--      trade either.  Also flagged, also not dropped.
--   6. Migrated openings: SAP go-live 2024-09-30.  Those documents carry
--      their TRUE original DocDueDate (back to 2017), so the bucket is
--      right, but a 3,000-day overdue is inherited history, not rot
--      since go-live.  Split out as MIGRATED_OPEN.
--   7. Rows whose due date precedes their document date (data entry)
--      are split out as BACKDATED_DUE_OPEN, not silently aged.
--   8. Invoices belonging to no CardType='C' card would be dropped by
--      the join -- checked live 2026-08-21: ZERO such rows in all three
--      books, and ZERO open invoices dated after {{ASOF}}.
--   9. TWO KNOWN CLASSIFICATION DIVERGENCES, left in on purpose so this
--      file stays rupee-identical to customer-ageing.sql.  Both were
--      measured live 2026-08-21 and are immaterial:
--        - "AKAL INFORMATION SYSTEMS LTD" (Oil CUSTA000242, group
--          DEBTORS, 10,000) reads TRADE here.  vendor-ageing.sql calls
--          the same group '%AKAL INFO%' INTERCO on the A/P side, so the
--          two sections disagree about one card worth 0.013% of Oil's
--          TRADE book.
--        - 8 employee imprest cards (ORGC*, "... IMPREST JWPLnnnn") sit
--          in a STATE group instead of 'STAFF CUSTOMER', so the group-
--          only STAFF test misses them and they read TRADE: 3 in Oil
--          (3,555), 2 in Mart (1,957), 3 in Bev (1,590) -- under 0.005%
--          of TRADE in every book.
--      Fixing either one HERE without fixing customer-ageing.sql would
--      break the reconciliation.  Fix both files together or neither.
--
-- AS-OF SEMANTICS  (read before quoting a back-dated figure)
--   {{ASOF}} sets the ageing reference date and excludes documents dated
--   after it.  Balances and PaidToDate are the CURRENT snapshot -- SAP
--   keeps no per-date history -- so {{ASOF}} = today is exact, and a past
--   {{ASOF}} ages today's open items against an older date.  It is NOT a
--   true point-in-time A/R.
-- =====================================================================
WITH cust AS (
  SELECT c."CardCode"                        AS CC,
         c."CardName"                        AS CNAME,
         IFNULL(g."GroupName", '(no group)') AS GRPNAME,
         CAST(c."Balance" AS DOUBLE)         AS BAL,
         CASE
           -- (a) JIVO's own state GST registrations
           WHEN IFNULL(g."GroupName",'') LIKE '%BRANCH%' THEN 'BRANCH'
           -- (b) the other JIVO entities / units (Oil <-> Mart <-> Bev)
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
         END                                 AS ACCT_KIND
  FROM {{SCHEMA}}.OCRD c
  LEFT JOIN {{SCHEMA}}.OCRG g
         ON g."GroupCode" = c."GroupCode"
        AND g."GroupType" = c."CardType"
  WHERE c."CardType" = 'C'
),
inv AS (
  SELECT i."CardCode"                                  AS CC,
         i."DocEntry"                                  AS DE,
         CAST(i."DocDueDate" AS DATE)                  AS DUEDT,
         CAST(i."DocDate"    AS DATE)                  AS DOCDT,
         CAST(i."DocTotal" - i."PaidToDate" AS DOUBLE) AS OPENAMT
  FROM {{SCHEMA}}.OINV i
  WHERE i."DocStatus" = 'O'
    AND i."CANCELED"  = 'N'
    AND CAST(i."DocTotal" - i."PaidToDate" AS DOUBLE) > 0
    AND CAST(i."DocDate" AS DATE) <= DATE'{{ASOF}}'
),
tot AS (
  SELECT CC, COUNT(*) AS NINV, SUM(OPENAMT) AS TOTOPEN
  FROM inv GROUP BY CC
),
rcpt AS (   -- unapplied incoming payments: cash banked, never knocked off
  SELECT "CardCode" AS CC, COUNT(*) AS NRCPT,
         SUM(CAST(IFNULL("OpenBal",0) AS DOUBLE)) AS UNAPP
  FROM {{SCHEMA}}.ORCT
  WHERE "DocType" = 'C' AND "Canceled" = 'N' AND IFNULL("OpenBal",0) <> 0
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  GROUP BY "CardCode"
),
cn AS (     -- unapplied sales credit notes
  SELECT "CardCode" AS CC, COUNT(*) AS NCN,
         SUM(CAST("DocTotal" - "PaidToDate" AS DOUBLE)) AS OPENCN
  FROM {{SCHEMA}}.ORIN
  WHERE "DocStatus" = 'O' AND "CANCELED" = 'N'
    AND CAST("DocDate" AS DATE) <= DATE'{{ASOF}}'
  GROUP BY "CardCode"
),
cr AS (
  SELECT v.CC,
         IFNULL(t.TOTOPEN, 0)                                    AS TOTOPEN,
         GREATEST(0, v.BAL)                                      AS RECEIVABLE,
         GREATEST(0, IFNULL(t.TOTOPEN,0) - GREATEST(0, v.BAL))   AS CREDIT
  FROM cust v LEFT JOIN tot t ON t.CC = v.CC
),
r AS (      -- oldest-due-first running total, so credit clears the oldest first
  SELECT i.CC, i.DUEDT, i.DOCDT, i.OPENAMT, c.CREDIT,
         SUM(i.OPENAMT) OVER (PARTITION BY i.CC
                              ORDER BY i.DUEDT, i.DE
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS CUM
  FROM inv i JOIN cr c ON c.CC = i.CC
),
eff AS (
  SELECT CC, DUEDT, DOCDT,
         GREATEST(0, LEAST(OPENAMT, CUM - CREDIT)) AS EFFOPEN
  FROM r
),
agg AS (
  SELECT CC,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') <=   0              THEN EFFOPEN ELSE 0 END) AS B0,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN   1 AND  30 THEN EFFOPEN ELSE 0 END) AS B1,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN  31 AND  60 THEN EFFOPEN ELSE 0 END) AS B2,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN  61 AND  90 THEN EFFOPEN ELSE 0 END) AS B3,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN  91 AND 180 THEN EFFOPEN ELSE 0 END) AS B4,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN 181 AND 365 THEN EFFOPEN ELSE 0 END) AS B5,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') >  365              THEN EFFOPEN ELSE 0 END) AS B6,
    SUM(CASE WHEN DOCDT = DATE'2024-09-30' THEN EFFOPEN ELSE 0 END)                                AS MIGEFF,
    SUM(CASE WHEN DUEDT < DOCDT            THEN EFFOPEN ELSE 0 END)                                AS BACKEFF,
    MIN(CASE WHEN EFFOPEN > 0 THEN DUEDT END)                                                      AS OLDESTDUE
  FROM eff GROUP BY CC
),
base AS (
  SELECT v.CC, v.CNAME, v.GRPNAME, v.ACCT_KIND, v.BAL,
         c.RECEIVABLE, c.CREDIT, c.TOTOPEN,
         IFNULL(t.NINV,0)      AS NINV,
         a.OLDESTDUE           AS OLDESTDUE,
         IFNULL(a.B0,0) B0, IFNULL(a.B1,0) B1, IFNULL(a.B2,0) B2,
         IFNULL(a.B3,0) B3, IFNULL(a.B4,0) B4, IFNULL(a.B5,0) B5,
         IFNULL(a.B6,0) B6,
         IFNULL(a.MIGEFF,0)    AS MIGEFF,
         IFNULL(a.BACKEFF,0)   AS BACKEFF,
         IFNULL(p.NRCPT,0)     AS NRCPT,
         IFNULL(p.UNAPP,0)     AS UNAPP,
         IFNULL(n.NCN,0)       AS NCN,
         IFNULL(n.OPENCN,0)    AS OPENCN,
         GREATEST(0, -v.BAL)                                       AS ADVANCE,
         GREATEST(0, GREATEST(0, v.BAL) - IFNULL(t.TOTOPEN,0))     AS UNBACKED
  FROM cust v
  JOIN      cr   c ON c.CC = v.CC
  LEFT JOIN tot  t ON t.CC = v.CC
  LEFT JOIN agg  a ON a.CC = v.CC
  LEFT JOIN rcpt p ON p.CC = v.CC
  LEFT JOIN cn   n ON n.CC = v.CC
  WHERE IFNULL(t.NINV,0) > 0
     OR v.BAL <> 0
     OR IFNULL(p.UNAPP,0) <> 0
     OR IFNULL(n.OPENCN,0) <> 0
)
SELECT
  CC                                              AS CARD_CODE,
  CNAME                                           AS CARD_NAME,
  GRPNAME                                         AS CUSTOMER_GROUP,
  ACCT_KIND                                       AS ACCT_KIND,
  CASE WHEN ACCT_KIND = 'TRADE' THEN 0 ELSE 1 END AS IS_EXCLUDED,
  ROUND(BAL, 2)                                   AS OCRD_BALANCE,
  ROUND(RECEIVABLE, 2)                            AS RECEIVABLE,
  ROUND(ADVANCE, 2)                               AS CUSTOMER_ADVANCE,
  NINV                                            AS N_OPEN_INV,
  ROUND(TOTOPEN, 2)                               AS RAW_OPEN,
  ROUND(CREDIT, 2)                                AS CREDIT_APPLIED,
  ROUND(B0+B1+B2+B3+B4+B5+B6, 2)                  AS ADJ_OPEN,
  ROUND(UNBACKED, 2)                              AS UNBACKED_CREDIT,
  ROUND(MIGEFF, 2)                                AS MIGRATED_OPEN,
  ROUND(BACKEFF, 2)                               AS BACKDATED_DUE_OPEN,
  OLDESTDUE                                       AS OLDEST_DUE,
  CASE WHEN OLDESTDUE IS NULL THEN NULL
       ELSE DAYS_BETWEEN(OLDESTDUE, DATE'{{ASOF}}') END AS DAYS_OLDEST,
  ROUND(B0, 2) AS B0_NOTDUE,
  ROUND(B1, 2) AS B1_1_30,
  ROUND(B2, 2) AS B2_31_60,
  ROUND(B3, 2) AS B3_61_90,
  ROUND(B4, 2) AS B4_91_180,
  ROUND(B5, 2) AS B5_181_365,
  ROUND(B6, 2) AS B6_365PLUS,
  ROUND(B3+B4+B5+B6, 2)                           AS ADJ_OVERDUE_60PLUS,
  NRCPT                                           AS N_UNAPPLIED_RCPT,
  ROUND(UNAPP, 2)                                 AS UNAPPLIED_RCPT,
  NCN                                             AS N_OPEN_CN,
  ROUND(OPENCN, 2)                                AS OPEN_CN,
  ROUND(SUM(TOTOPEN)    OVER (), 2)               AS CO_RAW_OPEN,
  ROUND(SUM(RECEIVABLE) OVER (), 2)               AS CO_RECEIVABLE,
  ROUND(SUM(B0+B1+B2+B3+B4+B5+B6) OVER (), 2)     AS CO_ADJ_OPEN,
  ROUND(SUM(UNBACKED)   OVER (), 2)               AS CO_UNBACKED_CREDIT,
  ROUND(SUM(UNAPP)      OVER (), 2)               AS CO_UNAPPLIED_RCPT,
  ROUND(SUM(OPENCN)     OVER (), 2)               AS CO_OPEN_CN,
  ROUND(SUM(ADVANCE)    OVER (), 2)               AS CO_CUSTOMER_ADVANCE,
  ROUND(SUM(MIGEFF)     OVER (), 2)               AS CO_MIGRATED_OPEN,
  ROUND(SUM(BACKEFF)    OVER (), 2)               AS CO_BACKDATED_DUE_OPEN,
  ROUND(SUM(CASE WHEN ACCT_KIND='TRADE' THEN B0+B1+B2+B3+B4+B5+B6 ELSE 0 END) OVER (), 2) AS CO_ADJ_OPEN_TRADE,
  ROUND(SUM(CASE WHEN ACCT_KIND='TRADE' THEN B3+B4+B5+B6 ELSE 0 END)          OVER (), 2) AS CO_ADJ_OVERDUE_60PLUS_TRADE
FROM base
ORDER BY CASE WHEN ACCT_KIND='TRADE' THEN 0 ELSE 1 END,
         (B3+B4+B5+B6) DESC,
         (B0+B1+B2+B3+B4+B5+B6) DESC,
         CC
