-- =====================================================================
-- vendor-ageing.sql   (section: vendor-ageing)   as-of {{ASOF}}
-- ---------------------------------------------------------------------
-- WHAT IT RETURNS
--   Credit-adjusted A/P ageing, ONE ROW PER VENDOR with bucket COLUMNS
--   (not one row per vendor per bucket).
--
--   Scope = every CardType='S' vendor in {{SCHEMA}} that has any of:
--   an open A/P bill, a non-zero ledger balance, an unapplied vendor
--   payment, or an open A/P credit note.  Everything else is dropped.
--   Most of those rows are nil-balance history: of Oil's 667 TRADE rows
--   only 258 carry any ADJ_OPEN and 170 are advances, so count parties
--   off ADJ_OPEN > 0, never off the row count.
--   Expected rows: 647 (Oil), 86 (Mart), 164 (Bev) at 2026-08-21.
--   Hundreds, never thousands.  Ordered worst-first by 60+ overdue.
--   (Was 676/87/164 before 2026-08-21: 30 cards carrying -0.0001 of TDS
--   rounding dust were being reported as vendors JIVO owes money to.
--   Rounding the balance to paise drops them.  No money moved - every
--   surviving row is identical to the paise, and the company totals
--   shifted by at most 0.01 rupee.)
--
-- WHY "CREDIT-ADJUSTED"
--   A naive OPCH ageing is wrong at JIVO by ~3x (Oil: 309 Cr of "open"
--   bills against a 103 Cr real payable).  Bills are settled by manual
--   journal entries (JDT1 TransType 30) and by on-account vendor
--   payments that were never internally reconciled, so OPCH."DocStatus"
--   stays 'O' long after the money moved.  The party's LEDGER BALANCE is
--   the only ground truth.  So per vendor:
--       PAYABLE = GREATEST(0, -ledger balance)        -- what we really owe
--       CREDIT  = GREATEST(0, SUM(open bills) - PAYABLE)
--   CREDIT is then consumed OLDEST-DUE-BILL-FIRST with a running window
--   sum, and only the remainder is aged.  Identity (exact, per vendor,
--   structural - it cannot drift):
--       SUM(buckets) + UNBACKED_CREDIT = PAYABLE
--
-- AS-OF CORRECTNESS  (fixed 2026-08-21; it used to be broken)
--   The ledger balance comes from JDT1 ("Debit"-"Credit" per "ShortName",
--   "RefDate" <= as-of), NOT from OCRD."Balance".  OCRD."Balance" is a
--   "right now" running total, so on a `--as-of 2026-07-31` month-end run
--   the old query reported TODAY's payable aged against JULY's clock - a
--   hybrid true on neither date, and it read as an improvement rather than
--   as an error.  JDT1 reproduces OCRD."Balance" to the rupee on all 5,174
--   vendor cards in all three books (0 mismatches), so at the default
--   as-of=today nothing changed; at a past as-of the total is now right.
--   LIMIT, stated plainly: OPCH."PaidToDate" is itself a "right now" field
--   and cannot be rewound without the reconciliation history, so on a past
--   as-of the BILL side is still today's.  The identity above still holds,
--   so the part that cannot be explained by a visible bill lands in
--   UNBACKED_CREDIT instead of being silently lost.  Read UNBACKED_CREDIT
--   before trusting the bucket split on any as-of that is not today.
--
-- MONEY UNITS: every money column is INR RUPEES (not lakh, not crore),
--   rounded to 2 dp, so the reconciliation columns tie to the rupee.
--   The dashboard divides by 1e5 / 1e7 for display.
--
-- COLUMN LIST (exact, in order):
--   CARD_CODE, CARD_NAME, VENDOR_GROUP, ACCT_KIND, IS_EXCLUDED,
--   OCRD_BALANCE, PAYABLE, VENDOR_ADVANCE,
--   N_OPEN_BILLS, RAW_OPEN, CREDIT_APPLIED, ADJ_OPEN, UNBACKED_CREDIT,
--   MIGRATED_OPEN, BACKDATED_DUE_OPEN, OLDEST_DUE, DAYS_OLDEST,
--   B0_NOTDUE, B1_1_30, B2_31_60, B3_61_90, B4_91_180, B5_181_365,
--   B6_365PLUS, ADJ_OVERDUE_60PLUS,
--   N_UNAPPLIED_PAY, UNAPPLIED_PAY, N_OPEN_CN, OPEN_CN,
--   CO_RAW_OPEN, CO_PAYABLE, CO_ADJ_OPEN, CO_UNBACKED_CREDIT,
--   CO_UNAPPLIED_PAY, CO_OPEN_CN, CO_VENDOR_ADVANCE,
--   CO_MIGRATED_OPEN, CO_BACKDATED_DUE_OPEN,
--   CO_ADJ_OPEN_TRADE, CO_ADJ_OVERDUE_60PLUS_TRADE
--   (the CO_* columns are company-level totals repeated on every row -
--    that is the reconciliation, read it off ANY SINGLE ROW.  Summing a
--    CO_* column down the table multiplies it by the row count.)
--   OCRD_BALANCE keeps its name for the column contract but is the
--   as-of LEDGER balance from JDT1; at as-of=today it is OCRD."Balance"
--   to the rupee.  Sign is SAP's: negative = JIVO owes.
--
-- ACCT_KIND / IS_EXCLUDED
--   'BRANCH'  = OCRG."GroupName" LIKE '%BRANCH%' (JIVO's own state GST
--               registrations, group 101).
--   'INTERCO' = NOT in a branch group but the name is a JIVO / Akal
--               group entity.  This case is REAL and material: Mart's
--               VENDA000001 "JIVO WELLNESS PVT LTD" (-20.93 Cr, Mart's
--               single largest payable) sits in group 106 PURCHASE, and
--               Oil's VENDA000483 "JIVO MART PVT LTD" sits in group 103
--               E-COMMERCE.  A group-only test misses both.
--   'TRADE'   = everything else = real external suppliers.
--   Branch/interco rows are FLAGGED (IS_EXCLUDED=1), never dropped.
--   This is not a rounding detail: branch+interco is 78% of Oil's aged
--   book (79.83 of 102.15 Cr, 9 accounts), 95% of Mart's (27.60 of
--   29.18 Cr, 6 accounts) and 36% of Bev's (0.79 of 2.21 Cr).  Summing
--   the section without filtering ACCT_KIND='TRADE' reports JIVO owing
--   itself.  Group 146/144 "COMPANY UNIT VENDOR" holds 0 cards today
--   and would NOT be caught by either test if it were ever populated.
--
-- NOT SUBTRACTED ON PURPOSE
--   UNAPPLIED_PAY (OVPM."OpenBal") and OPEN_CN (open ORPC) are reported
--   as diagnostics only.  They are ALREADY inside the ledger balance, so
--   subtracting them again would double-count.  In Oil they total
--   ~2017 Cr and ~0.34 Cr against a 103 Cr real payable - proof that
--   OVPM."OpenBal" cannot be used as the subtrahend.  (Oil holds 9,038
--   uncancelled supplier payments worth 3,638 Cr and 8,355 of them carry
--   a non-zero "OpenBal": SAP internal reconciliation is simply not used
--   here, so "OpenBal" means "never matched", not "money still unspent".)
--   Mart's 15.52 Cr of open A/P credit notes is 15.41 Cr on the interco
--   card VENDA000001 alone - it is flagged, not trade.
--
-- MIGRATED_OPEN is deliberately hardcoded to DocDate = 2024-09-30
--   That is Oil's go-live: 949 bills / 102.5 Cr were loaded that day, 268
--   still read open (57.0 Cr raw) carrying due dates back to 2017-11-28.
--   It returns 0 for Mart and Bev, and that is the TRUE answer, not a
--   portability bug - Mart's OPCH starts 2025-01-01 and Bev's 2024-10-01
--   and neither book carried its A/P openings in as invoices.  Do NOT
--   "generalise" this to MIN("DocDate") per schema: that would relabel
--   Bev's ordinary first trading day as a migration.
-- =====================================================================
WITH bill AS (
  SELECT p."CardCode"                                   AS CC,
         p."DocEntry"                                   AS DE,
         p."DocDueDate"                                 AS DUEDT,
         p."DocDate"                                    AS DOCDT,
         CAST(p."DocTotal" - p."PaidToDate" AS DOUBLE)  AS OPENAMT
  FROM {{SCHEMA}}.OPCH p
  WHERE p."DocStatus" = 'O'
    AND p."CANCELED"  = 'N'
    AND p."DocDate"  <= DATE'{{ASOF}}'
    AND CAST(p."DocTotal" - p."PaidToDate" AS DOUBLE) > 0
),
-- The as-of ledger position, rebuilt from the general ledger rather than read
-- off OCRD."Balance".  OCRD."Balance" is a running "right now" figure: on an
-- --as-of run it would report TODAY's payable against buckets aged on the
-- as-of clock, which is a hybrid that is true on neither date.  Summing
-- JDT1 "Debit"-"Credit" per "ShortName" (= CardCode for a BP) reproduces
-- OCRD."Balance" EXACTLY - verified to the rupee on all 5,174 vendor cards
-- across all three books, 0 mismatches - so at the default as-of=today this
-- is the same number, and at a past as-of it is the correct one.
--   ROUND(...,2) is load-bearing, not cosmetic: summing DOUBLEs leaves a
--   ~1e-9 residue on cards whose postings net to exactly zero, and the
--   scope test below is `BAL <> 0`, so without it 15 dead vendors across
--   the three books get admitted as all-zero rows.  SAP money is 2 dp,
--   so rounding to paise loses nothing.
bal AS (
  SELECT "ShortName"                                                       AS CC,
         ROUND(SUM(CAST("Debit" AS DOUBLE) - CAST("Credit" AS DOUBLE)), 2) AS BAL
  FROM {{SCHEMA}}.JDT1
  WHERE "RefDate" <= DATE'{{ASOF}}'
  GROUP BY "ShortName"
),
tot AS (
  SELECT CC,
         COUNT(*)                                                AS NBILL,
         SUM(OPENAMT)                                            AS TOTOPEN,
         MIN(DUEDT)                                              AS OLDESTDUE
  FROM bill GROUP BY CC
),
vend AS (
  SELECT c."CardCode"                        AS CC,
         c."CardName"                        AS CNAME,
         IFNULL(g."GroupName", '(no group)') AS GRPNAME,
         IFNULL(b.BAL, 0)                    AS BAL,
         CASE
           WHEN g."GroupName" LIKE '%BRANCH%' THEN 'BRANCH'
           WHEN UPPER(c."CardName") LIKE '%JIVO%'
             OR UPPER(c."CardName") LIKE '%AKAL ROZGAR%'
             OR UPPER(c."CardName") LIKE '%AKAL INFO%'
           THEN 'INTERCO'
           ELSE 'TRADE'
         END                                 AS ACCT_KIND
  FROM {{SCHEMA}}.OCRD c
  LEFT JOIN {{SCHEMA}}.OCRG g
         ON g."GroupCode" = c."GroupCode"
        AND g."GroupType" = c."CardType"
  LEFT JOIN bal b ON b.CC = c."CardCode"
  WHERE c."CardType" = 'S'
),
vpm AS (
  SELECT "CardCode" AS CC, COUNT(*) AS NPAY,
         SUM(CAST(IFNULL("OpenBal",0) AS DOUBLE)) AS UNAPP
  FROM {{SCHEMA}}.OVPM
  WHERE "Canceled" = 'N' AND "DocType" = 'S' AND IFNULL("OpenBal",0) <> 0
  GROUP BY "CardCode"
),
cn AS (
  SELECT "CardCode" AS CC, COUNT(*) AS NCN,
         SUM(CAST("DocTotal" - "PaidToDate" AS DOUBLE)) AS OPENCN
  FROM {{SCHEMA}}.ORPC
  WHERE "DocStatus" = 'O' AND "CANCELED" = 'N'
  GROUP BY "CardCode"
),
cr AS (
  SELECT v.CC,
         IFNULL(t.TOTOPEN, 0)                                        AS TOTOPEN,
         GREATEST(0, -v.BAL)                                         AS PAYABLE,
         GREATEST(0, IFNULL(t.TOTOPEN,0) - GREATEST(0, -v.BAL))      AS CREDIT
  FROM vend v LEFT JOIN tot t ON t.CC = v.CC
),
r AS (
  SELECT b.CC, b.DUEDT, b.DOCDT, b.OPENAMT, c.CREDIT,
         SUM(b.OPENAMT) OVER (PARTITION BY b.CC
                              ORDER BY b.DUEDT, b.DE
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS CUM
  FROM bill b JOIN cr c ON c.CC = b.CC
),
eff AS (
  SELECT CC, DUEDT, DOCDT,
         GREATEST(0, LEAST(OPENAMT, CUM - CREDIT)) AS EFFOPEN
  FROM r
),
agg AS (
  SELECT CC,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') <=   0 THEN EFFOPEN ELSE 0 END) AS B0,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN   1 AND  30 THEN EFFOPEN ELSE 0 END) AS B1,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN  31 AND  60 THEN EFFOPEN ELSE 0 END) AS B2,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN  61 AND  90 THEN EFFOPEN ELSE 0 END) AS B3,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN  91 AND 180 THEN EFFOPEN ELSE 0 END) AS B4,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') BETWEEN 181 AND 365 THEN EFFOPEN ELSE 0 END) AS B5,
    SUM(CASE WHEN DAYS_BETWEEN(DUEDT, DATE'{{ASOF}}') >  365 THEN EFFOPEN ELSE 0 END) AS B6,
    SUM(CASE WHEN DOCDT = DATE'2024-09-30' THEN EFFOPEN ELSE 0 END)                      AS MIGEFF,
    SUM(CASE WHEN DUEDT < DOCDT           THEN EFFOPEN ELSE 0 END)                       AS BACKEFF
  FROM eff GROUP BY CC
),
base AS (
  SELECT v.CC, v.CNAME, v.GRPNAME, v.ACCT_KIND, v.BAL,
         c.PAYABLE, c.CREDIT, c.TOTOPEN,
         IFNULL(t.NBILL,0)     AS NBILL,
         t.OLDESTDUE           AS OLDESTDUE,
         IFNULL(a.B0,0) B0, IFNULL(a.B1,0) B1, IFNULL(a.B2,0) B2,
         IFNULL(a.B3,0) B3, IFNULL(a.B4,0) B4, IFNULL(a.B5,0) B5,
         IFNULL(a.B6,0) B6,
         IFNULL(a.MIGEFF,0)    AS MIGEFF,
         IFNULL(a.BACKEFF,0)   AS BACKEFF,
         IFNULL(p.NPAY,0)      AS NPAY,
         IFNULL(p.UNAPP,0)     AS UNAPP,
         IFNULL(n.NCN,0)       AS NCN,
         IFNULL(n.OPENCN,0)    AS OPENCN,
         GREATEST(0, v.BAL)                              AS ADVANCE,
         GREATEST(0, GREATEST(0,-v.BAL) - IFNULL(t.TOTOPEN,0)) AS UNBACKED
  FROM vend v
  JOIN cr   c ON c.CC = v.CC
  LEFT JOIN tot t ON t.CC = v.CC
  LEFT JOIN agg a ON a.CC = v.CC
  LEFT JOIN vpm p ON p.CC = v.CC
  LEFT JOIN cn  n ON n.CC = v.CC
  WHERE IFNULL(t.NBILL,0) > 0
     OR v.BAL <> 0
     OR IFNULL(p.UNAPP,0) <> 0
     OR IFNULL(n.OPENCN,0) <> 0
)
SELECT
  CC                                        AS CARD_CODE,
  CNAME                                     AS CARD_NAME,
  GRPNAME                                   AS VENDOR_GROUP,
  ACCT_KIND                                 AS ACCT_KIND,
  CASE WHEN ACCT_KIND = 'TRADE' THEN 0 ELSE 1 END AS IS_EXCLUDED,
  ROUND(BAL, 2)                             AS OCRD_BALANCE,
  ROUND(PAYABLE, 2)                         AS PAYABLE,
  ROUND(ADVANCE, 2)                         AS VENDOR_ADVANCE,
  NBILL                                     AS N_OPEN_BILLS,
  ROUND(TOTOPEN, 2)                         AS RAW_OPEN,
  ROUND(CREDIT, 2)                          AS CREDIT_APPLIED,
  ROUND(B0+B1+B2+B3+B4+B5+B6, 2)            AS ADJ_OPEN,
  ROUND(UNBACKED, 2)                        AS UNBACKED_CREDIT,
  ROUND(MIGEFF, 2)                          AS MIGRATED_OPEN,
  ROUND(BACKEFF, 2)                         AS BACKDATED_DUE_OPEN,
  OLDESTDUE                                 AS OLDEST_DUE,
  CASE WHEN OLDESTDUE IS NULL THEN NULL
       ELSE DAYS_BETWEEN(OLDESTDUE, DATE'{{ASOF}}') END AS DAYS_OLDEST,
  ROUND(B0, 2) AS B0_NOTDUE,
  ROUND(B1, 2) AS B1_1_30,
  ROUND(B2, 2) AS B2_31_60,
  ROUND(B3, 2) AS B3_61_90,
  ROUND(B4, 2) AS B4_91_180,
  ROUND(B5, 2) AS B5_181_365,
  ROUND(B6, 2) AS B6_365PLUS,
  ROUND(B3+B4+B5+B6, 2)                     AS ADJ_OVERDUE_60PLUS,
  NPAY                                      AS N_UNAPPLIED_PAY,
  ROUND(UNAPP, 2)                           AS UNAPPLIED_PAY,
  NCN                                       AS N_OPEN_CN,
  ROUND(OPENCN, 2)                          AS OPEN_CN,
  ROUND(SUM(TOTOPEN)  OVER (), 2)           AS CO_RAW_OPEN,
  ROUND(SUM(PAYABLE)  OVER (), 2)           AS CO_PAYABLE,
  ROUND(SUM(B0+B1+B2+B3+B4+B5+B6) OVER (), 2) AS CO_ADJ_OPEN,
  ROUND(SUM(UNBACKED) OVER (), 2)           AS CO_UNBACKED_CREDIT,
  ROUND(SUM(UNAPP)    OVER (), 2)           AS CO_UNAPPLIED_PAY,
  ROUND(SUM(OPENCN)   OVER (), 2)           AS CO_OPEN_CN,
  ROUND(SUM(ADVANCE)  OVER (), 2)           AS CO_VENDOR_ADVANCE,
  ROUND(SUM(MIGEFF)   OVER (), 2)           AS CO_MIGRATED_OPEN,
  ROUND(SUM(BACKEFF)  OVER (), 2)           AS CO_BACKDATED_DUE_OPEN,
  ROUND(SUM(CASE WHEN ACCT_KIND='TRADE' THEN B0+B1+B2+B3+B4+B5+B6 ELSE 0 END) OVER (), 2) AS CO_ADJ_OPEN_TRADE,
  ROUND(SUM(CASE WHEN ACCT_KIND='TRADE' THEN B3+B4+B5+B6 ELSE 0 END) OVER (), 2)          AS CO_ADJ_OVERDUE_60PLUS_TRADE
FROM base
ORDER BY CASE WHEN ACCT_KIND='TRADE' THEN 0 ELSE 1 END,
         (B3+B4+B5+B6) DESC,
         (B0+B1+B2+B3+B4+B5+B6) DESC,
         CC
