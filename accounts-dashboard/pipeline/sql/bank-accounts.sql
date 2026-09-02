-- ============================================================================
-- bank-accounts.sql  --  JIVO Bank & Cash Register   (section: bank-accounts)
-- ----------------------------------------------------------------------------
-- ONE ROW PER G/L BANK / CASH / BANK-FACILITY ACCOUNT in one company book.
-- Every postable account that sits directly under one of the eight banking
-- drawers of the chart of accounts is returned, whether or not it was ever used
-- (NEVER_USED_FLAG tells you which).
--
-- Expected size: Oil 70 rows, Mart 44, Beverages 18 (all three counted live
-- 2026-08-21).  Hard-bounded by the chart of accounts - there is no document
-- fan-out anywhere in this query - so it can never run away.
--
-- ----------------------------------------------------------------------------
-- WHERE THE ACCOUNTS COME FROM  (this is the part everyone gets wrong)
-- ----------------------------------------------------------------------------
-- TRAP 1 - ODSC IS NOT THE HOUSE-BANK TABLE.  ODSC is SAP's generic BANK MASTER:
--   a directory of banks (AXIS, ICICI, INDIAN BANK, YES BANK...) shipped with the
--   localisation - 65 rows in Oil, 55 in Mart, 59 in Beverages (they differ; do
--   not assume 65 everywhere).  Its "DfltAcct" is empty on every row in all three
--   books (verified).  It carries NO JIVO account number and NO balance.  It is
--   used here only as a lookup to put a canonical bank NAME against an account.
-- TRAP 2 - DSC1 (the real house-bank-accounts table) IS ALMOST EMPTY *AND* PARTLY
--   WRONG.  Oil has 5 rows, Beverages 3, Mart 1 - against 13-30 live bank G/L
--   accounts per book.  Two of those 9 rows have a NULL "GLAccount" (Mart's ONLY
--   row is one of them, so Mart gets zero house-bank matches).  Worse, Beverages'
--   DSC1 rows were copied from Oil's chart and still carry OIL's G/L codes:
--     BEV DSC1 -> "GLAccount" 2201101, which is not a postable bank account in
--                 the Bev chart at all (Bev has no CC drawer children);
--     BEV DSC1 -> "GLAccount" 1104102 with "Account" 6994996254, but Bev's
--                 1104102 is 'INDIAN BANK-7106652016' - a DIFFERENT account.
--   Taking DSC1 at face value therefore prints the wrong account number against a
--   Beverages bank account.  This query cross-checks every DSC1 row against the
--   digits in the G/L account's own name and only trusts it when they agree
--   (HOUSE_BANK_AGREES = 'AGREE'); on 'MISMATCH' it falls back to the chart of
--   accounts and suppresses the DSC1 branch and bank code.  Live: Oil 5/5 AGREE,
--   Beverages' single joinable row MISMATCHes, Mart has no joinable row at all.
-- TRAP 3 - OACT."ActType" AND "CashBox" DO NOT MARK BANK ACCOUNTS.  Every one of
--   Oil's 70 banking accounts has ActType='N' and CashBox='N' - and so do 984
--   other postable accounts in the same book.  Checked live: useless as a
--   selector, in every book.
-- TRAP 4 - THE ACCOUNT-CODE PREFIX LIES.  Oil's 1104106/1104107/1104108/1104110
--   carry 1104* ("BANK ACCOUNTS") codes but their FatherNum is 2201100 "BANK CASH
--   CREDIT LOAN"; Oil's 1103114/1103115/1103116/1103117 carry 1103* (STOCKS) codes
--   but hang under 1106100 "FDR"; Oil's 2201104 and 2201402 hang under 2201200
--   "TERM LOAN".  You MUST walk FatherNum, never LIKE '1104%'.
-- TRAP 5 - CANCELLING A PAYMENT DOES NOT DELETE IT.  SAP posts the original AND a
--   mirror-image reversal, and marks BOTH ORCT/OVPM rows "Canceled"='Y'.  The
--   BALANCE is therefore right with no filter (the pair nets to zero - see below),
--   but a naive SUM("Debit")/SUM("Credit") counts the same money twice and inflates
--   GROSS MOVEMENT on both sides.  Measured live over the 12-month window, all
--   three books: Oil +14,679.76 L (+14.5% of receipts, +14.3% of payments,
--   1,268 of 14,380 lines), Mart +4,874.42 L (+20.5% / +20.5%, 642 of 9,154),
--   Beverages +298.42 L (+11.6% / +11.7%, 206 of 3,718).  This query removes both
--   halves via OJDT."StornoToTr" - which is DOC-TYPE AGNOSTIC and so also catches
--   reversed manual journal entries that the ORCT/OVPM "Canceled" flag misses
--   (4 extra lines in Oil, 8 in Mart, 0 in Beverages) - and reports what it took
--   out in CANCELLED_GROSS_12M_L rather than letting it vanish.
--   PROVEN INDEPENDENTLY: with the storno pair removed, the ledger route equals the
--   DOCUMENT route to the paisa on Oil 2201101 (the largest account) -
--     receipts 34,503.22 L = ORCT("Canceled"='N') 32,451.07 + JE30 debits 922.15
--                            + outgoing-payment debits 1,130.00
--     payments 34,077.66 L = OVPM("Canceled"='N') 24,621.87 + JE30 credits 777.80
--                            + incoming-payment credits 8,677.98
--   Without it the same account reported 35,903.92 / 27,013.01 on TransType 24/46
--   against document totals of 32,451.07 / 24,621.87.
-- TRAP 6 - MOST OF THE BANK TRAFFIC IS NOT TRADE.  Branch and inter-company money
--   is real bank movement (it genuinely leaves the account), so it is NOT dropped -
--   but it must not be read as third-party business.  12-month share, live:
--   Mart pays 16,593.56 L of its 18,942.78 L out to JIVO group/branch parties -
--   88% - and Oil takes 16,531.11 L of its 86,464.88 L in from them (19%).
--   INTERCO_IN_12M_L / INTERCO_OUT_12M_L carry it per account.  The test is
--   OCRG."GroupName" LIKE '%BRANCH%' OR OCRD."CardName" LIKE '%JIVO%' - the group
--   test alone is NOT enough (Mart's VENDA000001 'JIVO WELLNESS PVT LTD', its
--   largest payable, sits in group 106 PURCHASE), and the 23 known group CardCodes
--   are book-specific so they cannot be hardcoded into a three-schema query.
--   Attribution is at TRANSACTION level: a journal that touches a group party at
--   all has its whole bank line counted, so treat these two columns as an upper
--   bound, not an allocation.
--
-- OUT OF SCOPE, ON PURPOSE: 2202000 UNSECURED LOAN (directors', subsidiary and
--   NBFC borrowings - Oil ~2,330 L, Mart ~233 L, Beverages nil) is real debt but
--   not a bank facility, so it is not in this register and NOT in TOT_BORROWINGS_L.
--   "Total borrowings" here means bank borrowings only.
--
-- => THE UNIVERSE IS DEFINED BY THE PARENT DRAWER'S *NAME*, resolved through
--    OACT."FatherNum".  All eight drawer accounts exist, spelled identically, in
--    all three company books (verified; in Beverages three of them - CC, CREDIT
--    CARD, VEHICLE LOAN - exist but are empty).  Names are used rather than codes
--    so the query survives a renumbered chart.  Verified live: no postable account
--    sits two levels below any drawer, so a single father hop is sufficient
--    (grandchild count = 0 in all three books).
--
--    DRAWER (OACT."AcctName" of the parent)  ->  CATEGORY            KIND
--    BANK ACCOUNTS                              CURRENT_ACCOUNT      BANK
--    PAYMENT BANK ONLINE                        PAYMENT_WALLET       BANK
--    CASH IN HAND                               CASH_IN_HAND         CASH
--    BANK CASH CREDIT LOAN                      CASH_CREDIT_OD       BANK
--    FDR                                        FIXED_DEPOSIT        DEPOSIT
--    TERM LOAN                                  TERM_LOAN            BORROWING
--    VEHICLE LOAN                               VEHICLE_LOAN         BORROWING
--    CREDIT CARD                                CREDIT_CARD          BORROWING
--
--    Note 'CASH IN HAND' is BOTH a drawer (1105000, Postable='N') and one of its
--    own postable children (1105002).  The a."Postable"='Y' test keeps the drawer
--    itself out of the result while keeping the child in.
--
-- COMPLETENESS CHECK (re-run live 2026-08-21, all three books): every distinct G/L
--   account ever used as ORCT/OVPM "CashAcct"/"CheckAcct"/"TrsfrAcct" is inside
--   this universe, except two that are correctly outside it - Oil 3200003 OPENING
--   BALANCE ACCOUNT (the migration offset) and Oil 5200015 EXCHANGE FLUCTUATIONS.
--   Mart and Beverages have none outside.  So no real bank account is missed, and
--   the payment-account list on its own would have been a BAD selector (it drags
--   in those two non-bank accounts).  Every other postable account whose name
--   mentions BANK/FDR/PAYTM/RAZORPAY and which this query excludes is an expense,
--   payable or receivable account (BANK CHARGES, INTEREST ON BANK LOAN, TDS
--   RECOVERABLE FROM BANK, PAYTM SUSPENSE A/C ...) - correctly outside.
--
-- ----------------------------------------------------------------------------
-- BALANCE
-- ----------------------------------------------------------------------------
-- BALANCE_L is computed from JDT1 as SUM("Debit") - SUM("Credit") over lines with
--   "RefDate" <= {{ASOF}}.  VERIFIED live on EVERY account in all three books
--   (70 + 44 + 18): the JDT1 sum equals OACT."CurrTotal" to floating-point noise
--   (worst |diff| 5.2e-5 rupees, on a 28.8-crore account).  CURRTOTAL_TODAY_L
--   carries OACT."CurrTotal" as an independent cross-check; it is LIFETIME-to-today
--   and will legitimately differ from BALANCE_L whenever {{ASOF}} is not today.
--   (No banking account currently carries a future-dated line in any book, so the
--   two agree exactly at an as-of of today - but Beverages' JDT1 as a whole *does*
--   hold lines out to 2026-12-31, so the <= {{ASOF}} guard is not decorative.)
-- SIGN: POSITIVE = DEBIT = money sitting with JIVO (or, on a loan account, an
--   over-repayment).  NEGATIVE = CREDIT = JIVO owes (drawn on the facility, or a
--   genuinely overdrawn current account).  Same convention as OCRD."Balance".
-- Cancelled payments need NO filter *for the balance*: SAP reverses them with a
--   contra journal, so JDT1 already nets them out - verified, the storno pairs sum
--   to exactly 0 per account in all three books - which is why the JDT1 total
--   reconciles to "CurrTotal" with no Canceled test on this CTE.  Leaving them in
--   here (rather than filtering as the movement CTE does) is deliberate: it keeps
--   BALANCE_L equal to what SAP itself reports even at an as-of date that falls
--   BETWEEN an original payment and its later reversal.
-- OPENING_BAL_L / BOOK_OPENING_DATE are gated by the as-of, so a position taken
--   before the book opened returns NULL/0 rather than a future opening balance.
--
-- ----------------------------------------------------------------------------
-- MOVEMENT
-- ----------------------------------------------------------------------------
-- 12-month window = the twelve calendar months ending with the month of {{ASOF}}
--   (i.e. 2025-09-01..2026-08-21 for an as-of of 2026-08-21).  The last month is
--   partial whenever {{ASOF}} is not a month end.
-- RECEIPTS_IN_*  = SUM("Debit")  = money INTO the account.
-- PAYMENTS_OUT_* = SUM("Credit") = money OUT of the account.
--   Both EXCLUDE cancelled/reversed transactions (TRAP 5) - so do N_LINES_12M,
--   ACTIVE_MONTHS_12M, MANUAL_JE_LINE_PCT_12M, the MONTHLY_* series and
--   FIRST/LAST_MOVE_DATE.  BALANCE_L and OPENING_BAL_L deliberately do not.
--   NET_12M_L is unchanged by the exclusion (the pair nets to zero) - only the
--   gross sides move.
--   Read them physically, not by account type: on a CC/OD or loan account a Debit
--   is still money going in (a repayment) and a Credit is still money going out
--   (a drawdown or an interest charge).
-- Only three TransTypes ever touch these accounts (checked live, 12m, all three
--   books): 24 = incoming payment (ORCT), 46 = outgoing payment (OVPM), 30 =
--   manual journal entry.  No invoice posts to a bank account directly.
--   MANUAL_JE_LINE_PCT_12M = TransType-30 lines as a % of LINES (not of value) -
--   it says how much of the traffic is hand-keyed, not how much of the money.
-- AVG_MONTHLY_OUT_L divides 12m payments out by ACTIVE months, not by 12, so a
--   seasonal account is not flattered by its idle months.
-- MONTHLY_*_SERIES are 'YYYY-MM=<lakhs>' pairs joined by ';', ALWAYS 12 slots in
--   chronological order, zero-filled - a missing month means zero, never unknown.
--   Parse with split(';') then split('=').
--
-- ----------------------------------------------------------------------------
-- ACCOUNT NUMBERS ARE NEVER EMITTED IN FULL
-- ----------------------------------------------------------------------------
-- The bank account number lives INSIDE OACT."AcctName" ('INDIAN BANK-6994996254'),
-- so the raw account name is itself sensitive and is never returned.
--   GL_ACCT_LABEL_MASKED = the account name with EVERY digit replaced by 'x'.
--   ACCT_NO_MASKED       = 'xxxx' + the last 4 digits, taken from DSC1."Account"
--                          when a house-bank row exists AND agrees, otherwise from
--                          the digits embedded in the account name.  NULL when the
--                          name holds fewer than 4 digits.
--   ACCT_NO_NDIGITS      = how many digits the source string held, so a reader can
--                          see the true length without seeing the number.
-- BANK_NAME is only filled when the account is actually bank-linked: the ODSC
--   master match, else the leading words of the account name but ONLY if that name
--   contains 'BANK'.  Cash-in-hand accounts, 'FDR - ACCRUED INTEREST' and Oil's
--   mis-filed 1103115 'R & D WHEAT GRASS' therefore come back BANK_NAME = NULL with
--   BANK_NAME_SOURCE = 'UNRESOLVED', instead of pretending to be a bank.
--   Live split: Oil 61 ODSC / 3 name / 6 unresolved; Mart 33/3/8; Bev 13/2/3.
-- CAVEAT 1: where the account name writes the number in hyphenated groups
--   ('HSBC BANK A/C- 166-794941-511'), "the last 4 digits as written" is the last
--   4 of the concatenated digits - flagged by ACCT_NO_SOURCE='GL_ACCT_NAME'.
-- CAVEAT 2: the name fallback keeps whatever leading capitals the account name
--   carries, so Oil 1104105 comes back as 'PUNJAB & SIND BANK TPT' - the trailing
--   'TPT' is JIVO's unit tag, not part of the bank's name.
-- GL_ACCT_CODE is a chart-of-accounts code, not a bank account number: safe.
--
-- ----------------------------------------------------------------------------
-- OPENING
-- ----------------------------------------------------------------------------
-- BOOK_OPENING_DATE = the earliest "RefDate" posted to ANY banking account in this
--   book, and OPENING_BAL_L = what this account was given on that date.  It is
--   deliberately NOT hardcoded to the 2024-09-30 go-live: Oil's banking ledger does
--   open on 2024-09-30 (32 accounts, net -2,352.99 L) and Beverages' on 2024-09-30
--   (2 lines, net 0), but MART'S BANK LEDGER OPENS ON 2024-12-31 as six TransType-30
--   journal lines worth +83.17 L, with nothing at all before it.  A hardcoded
--   go-live date silently returns 0 for every Mart account.
--
-- ----------------------------------------------------------------------------
-- INTEREST
-- ----------------------------------------------------------------------------
-- EST_ANNUAL_INTEREST_L = AMOUNT_DRAWN_L * 0.0847, for BORROWING and CASH_CREDIT_OD
--   rows only.  0.0847 is an INPUT CONSTANT handed to this section, NOT derived
--   here - and the live cross-check comes out BELOW it.  Measured on Oil for
--   2025-09-01..2026-08-21: debits to 5610001 INTEREST ON BANK LOAN = 463.37 L
--   (credits 82.83 L) against an average month-end drawn debt of 6,148.65 L across
--   the twelve month-ends = 7.53% gross / 6.19% net.  Some borrowing cost sits on
--   other accounts (2163024 TRADEPAY interest payable, 2163026 term-loan interest
--   payable) and the mix includes cheaper term debt, so the gap is explainable but
--   NOT closed.  Treat EST_ANNUAL_INTEREST_L as an INFERRED upper-bound run-rate on
--   today's drawn balance - not an accrual, and not a measured cost.
--
-- ----------------------------------------------------------------------------
-- MONEY UNIT: every money column is INR LAKHS and carries the _L suffix.
-- ----------------------------------------------------------------------------
-- COLUMNS RETURNED (51), in order:
--   COMPANY_SCHEMA, AS_OF, CATEGORY, CATEGORY_KIND, IS_CASH_AND_BANK,
--   GL_ACCT_CODE, GL_DRAWER, GL_ACCT_LABEL_MASKED,
--   BANK_CODE, BANK_NAME, BANK_NAME_SOURCE, BRANCH, IS_HOUSE_BANK,
--   HOUSE_BANK_AGREES, ACCT_NO_MASKED, ACCT_NO_SOURCE, ACCT_NO_NDIGITS,
--   BALANCE_L, CURRTOTAL_TODAY_L, BALANCE_SIGN, FUNDS_AVAILABLE_L,
--   AMOUNT_DRAWN_L, OVERDRAWN_FLAG, EST_ANNUAL_INTEREST_L,
--   RECEIPTS_IN_12M_L, PAYMENTS_OUT_12M_L, NET_12M_L, AVG_MONTHLY_OUT_L,
--   CANCELLED_GROSS_12M_L, INTERCO_IN_12M_L, INTERCO_OUT_12M_L,
--   N_LINES_12M, ACTIVE_MONTHS_12M, MANUAL_JE_LINE_PCT_12M,
--   FIRST_MOVE_DATE, LAST_MOVE_DATE, DAYS_SINCE_LAST_MOVE,
--   DORMANT_90D_FLAG, NEVER_USED_FLAG, BOOK_OPENING_DATE, OPENING_BAL_L,
--   MONTHLY_IN_L_SERIES, MONTHLY_OUT_L_SERIES, MONTHLY_NET_L_SERIES,
--   TOT_CASH_AND_BANK_L, TOT_BANK_CURRENT_L, TOT_CASH_IN_HAND_L,
--   TOT_WALLET_L, TOT_CC_OD_NET_L, TOT_FIXED_DEPOSIT_L, TOT_BORROWINGS_L
--   (the seven TOT_* columns are company-level window totals repeated on every row,
--    so the dashboard can read the cash-and-bank position off any single row.
--    TOT_CASH_AND_BANK_L = current accounts + wallets + cash + CC/OD, i.e. the
--    net treasury position; FDR and term/vehicle/card debt are deliberately NOT
--    in it and are carried separately.
--    OVERLAP WARNING - the seven TOT_* columns are NOT disjoint and must never be
--    added together: TOT_CASH_AND_BANK_L already contains TOT_BANK_CURRENT_L +
--    TOT_CASH_IN_HAND_L + TOT_WALLET_L + TOT_CC_OD_NET_L, and TOT_BORROWINGS_L
--    (gross drawn, negatives only) overlaps TOT_CC_OD_NET_L (net).  Read ONE of
--    them per question.  The per-account columns, by contrast, ARE safe to sum:
--    one row per G/L account, no fan-out, no faceting.)
-- ============================================================================
WITH params AS (
  SELECT DATE'{{ASOF}}'                                                        AS ASOF,
         ADD_MONTHS(TO_DATE(TO_VARCHAR(DATE'{{ASOF}}','YYYY-MM')||'-01',
                            'YYYY-MM-DD'), -11)                                AS WSTART,
         0.0847                                                                AS CC_RATE
  FROM DUMMY
),

-- ---- the account universe, defined by the PARENT DRAWER NAME -----------------
univ AS (
  SELECT a."AcctCode"                                    AS GL,
         a."AcctName"                                    AS GLNAME,
         f."AcctName"                                    AS DRAWER,
         CAST(a."CurrTotal" AS DOUBLE)                   AS CURRTOTAL,
         CASE f."AcctName"
           WHEN 'BANK ACCOUNTS'         THEN 'CURRENT_ACCOUNT'
           WHEN 'PAYMENT BANK ONLINE'   THEN 'PAYMENT_WALLET'
           WHEN 'CASH IN HAND'          THEN 'CASH_IN_HAND'
           WHEN 'BANK CASH CREDIT LOAN' THEN 'CASH_CREDIT_OD'
           WHEN 'FDR'                   THEN 'FIXED_DEPOSIT'
           WHEN 'TERM LOAN'             THEN 'TERM_LOAN'
           WHEN 'VEHICLE LOAN'          THEN 'VEHICLE_LOAN'
           WHEN 'CREDIT CARD'           THEN 'CREDIT_CARD'
         END                                             AS CATEGORY,
         CASE f."AcctName"
           WHEN 'BANK ACCOUNTS'         THEN 'BANK'
           WHEN 'PAYMENT BANK ONLINE'   THEN 'BANK'
           WHEN 'CASH IN HAND'          THEN 'CASH'
           WHEN 'BANK CASH CREDIT LOAN' THEN 'BANK'
           WHEN 'FDR'                   THEN 'DEPOSIT'
           ELSE 'BORROWING'
         END                                             AS CATEGORY_KIND,
         -- what counts towards the cash-and-bank position
         CASE WHEN f."AcctName" IN ('BANK ACCOUNTS','PAYMENT BANK ONLINE',
                                    'CASH IN HAND','BANK CASH CREDIT LOAN')
              THEN 'Y' ELSE 'N' END                      AS IS_CASH_AND_BANK,
         -- digits embedded in the account name (the bank account number)
         REPLACE_REGEXPR('[^0-9]' IN a."AcctName" WITH '' OCCURRENCE ALL)
                                                         AS NAME_DIGITS
  FROM {{SCHEMA}}.OACT a
  JOIN {{SCHEMA}}.OACT f ON f."AcctCode" = a."FatherNum"
  WHERE a."Postable" = 'Y'
    AND f."AcctName" IN ('BANK ACCOUNTS','PAYMENT BANK ONLINE','CASH IN HAND',
                         'BANK CASH CREDIT LOAN','FDR','TERM LOAN',
                         'VEHICLE LOAN','CREDIT CARD')
),

-- ---- DSC1 house-bank row, where one exists (0-5 per book) --------------------
house AS (
  SELECT d."GLAccount"                              AS GL,
         MIN(d."BankCode")                          AS BANKCODE,
         MIN(d."Account")                           AS ACCTNO,
         MIN(REPLACE_REGEXPR('[^0-9]' IN d."Account" WITH '' OCCURRENCE ALL))
                                                    AS ACCTNO_DIGITS,
         MIN(NULLIF(TRIM(COALESCE(d."BranchName", d."Branch")), '')) AS BRANCH
  FROM {{SCHEMA}}.DSC1 d
  WHERE d."GLAccount" IS NOT NULL AND d."GLAccount" <> ''
  GROUP BY d."GLAccount"
),

-- ---- canonical bank name: ODSC master, matched on BankName or a >=4 char code
bankmatch AS (
  SELECT GL, BANKCODE, BANKNAME FROM (
    SELECT u.GL                                      AS GL,
           o."BankCode"                              AS BANKCODE,
           o."BankName"                              AS BANKNAME,
           ROW_NUMBER() OVER (PARTITION BY u.GL
                              ORDER BY LENGTH(o."BankName") DESC,
                                       o."BankCode")  AS RN
    FROM univ u
    JOIN {{SCHEMA}}.ODSC o
      ON  UPPER(u.GLNAME) LIKE '%'||UPPER(o."BankName")||'%'
      OR (LENGTH(o."BankCode") >= 4
          AND UPPER(u.GLNAME) LIKE '%'||UPPER(o."BankCode")||'%')
  ) WHERE RN = 1
),

-- ---- CANCELLED / REVERSED transactions (see TRAP 5 in the header) ------------
-- Both halves of every storno pair: the reversing journal AND the journal it
-- reverses.  OJDT."StornoToTr" is doc-type agnostic, so this one set covers
-- cancelled incoming payments, cancelled outgoing payments and reversed manual
-- journal entries alike.
storno AS (
  SELECT "TransId"    AS T FROM {{SCHEMA}}.OJDT
   WHERE "StornoToTr" IS NOT NULL AND "StornoToTr" <> 0
  UNION
  SELECT "StornoToTr" AS T FROM {{SCHEMA}}.OJDT
   WHERE "StornoToTr" IS NOT NULL AND "StornoToTr" <> 0
),

-- ---- JIVO group / branch counterparties (see TRAP 6) -------------------------
-- Two tests, because neither alone is enough: the branch GROUP catches the
-- BRANCH CUSTOMER / BRANCH VENDOR families, and the NAME catches the group
-- companies filed in an ordinary trade group (Mart's VENDA000001 'JIVO WELLNESS
-- PVT LTD' sits in group 106 PURCHASE).  Verified to cover all 23 known group
-- CardCodes in all three books without dragging in a real third party.
grpbp AS (
  SELECT c."CardCode" AS CC
  FROM {{SCHEMA}}.OCRD c
  LEFT JOIN {{SCHEMA}}.OCRG g
    ON g."GroupCode" = c."GroupCode" AND g."GroupType" = c."CardType"
  WHERE UPPER(COALESCE(g."GroupName",'')) LIKE '%BRANCH%'
     OR UPPER(COALESCE(c."CardName" ,'')) LIKE '%JIVO%'
),
-- DISTINCT is load-bearing: without it this left join would fan the ledger out.
grptx AS (
  SELECT DISTINCT j."TransId" AS T
  FROM {{SCHEMA}}.JDT1 j
  WHERE j."ShortName" IN (SELECT CC FROM grpbp)
),

-- ---- the twelve month slots of the window (dense, zero-filled later) ---------
mslot AS (
  SELECT 0 AS N FROM DUMMY UNION ALL SELECT 1  FROM DUMMY UNION ALL
  SELECT 2 AS N FROM DUMMY UNION ALL SELECT 3  FROM DUMMY UNION ALL
  SELECT 4 AS N FROM DUMMY UNION ALL SELECT 5  FROM DUMMY UNION ALL
  SELECT 6 AS N FROM DUMMY UNION ALL SELECT 7  FROM DUMMY UNION ALL
  SELECT 8 AS N FROM DUMMY UNION ALL SELECT 9  FROM DUMMY UNION ALL
  SELECT 10 AS N FROM DUMMY UNION ALL SELECT 11 FROM DUMMY
),
months AS (
  SELECT TO_VARCHAR(ADD_MONTHS(p.WSTART, s.N), 'YYYY-MM') AS M
  FROM params p CROSS JOIN mslot s
),

-- ---- when this book's banking ledger opens, and each account's opening -------
openday AS (
  -- Gated by the as-of: without it, a position taken BEFORE the book opened
  -- reports a future opening balance against a nil closing balance (measured on
  -- Mart at --as-of 2024-11-30: 80.03 L of "opening" on a book that opens
  -- 2024-12-31).  NULL here simply zeroes every OPENING_BAL_L.
  SELECT MIN(j."RefDate") AS OPEN_D
  FROM {{SCHEMA}}.JDT1 j
  CROSS JOIN params p
  WHERE j."Account" IN (SELECT GL FROM univ)
    AND j."RefDate" <= p.ASOF
),

-- ---- ledger position and lifetime footprint ---------------------------------
bal AS (
  SELECT j."Account"                                                        AS GL,
         SUM(CASE WHEN j."RefDate" <= p.ASOF
                  THEN CAST(j."Debit" AS DOUBLE) - CAST(j."Credit" AS DOUBLE)
                  ELSE 0 END)                                               AS BAL,
         SUM(CASE WHEN j."RefDate" = o.OPEN_D
                  THEN CAST(j."Debit" AS DOUBLE) - CAST(j."Credit" AS DOUBLE)
                  ELSE 0 END)                                               AS OPENING,
         -- ...but FIRST/LAST MOVEMENT are about REAL traffic, so a cancelled
         -- payment and its reversal must not make a dead account look alive.
         MIN(CASE WHEN j."RefDate" <= p.ASOF AND st.T IS NULL
                  THEN j."RefDate" END)                                     AS FIRSTMV,
         MAX(CASE WHEN j."RefDate" <= p.ASOF AND st.T IS NULL
                  THEN j."RefDate" END)                                     AS LASTMV
  FROM {{SCHEMA}}.JDT1 j
  CROSS JOIN params p
  CROSS JOIN openday o
  LEFT JOIN storno st ON st.T = j."TransId"
  WHERE j."Account" IN (SELECT GL FROM univ)
  GROUP BY j."Account"
),

-- ---- movement, one row per account per month inside the 12-month window -----
mon AS (
  SELECT j."Account"                              AS GL,
         TO_VARCHAR(j."RefDate",'YYYY-MM')        AS M,
         -- st.T IS NULL  =  a line that was not cancelled and is not a reversal
         SUM(CASE WHEN st.T IS NULL THEN CAST(j."Debit"  AS DOUBLE) ELSE 0 END) AS MIN_,
         SUM(CASE WHEN st.T IS NULL THEN CAST(j."Credit" AS DOUBLE) ELSE 0 END) AS MOUT_,
         SUM(CASE WHEN st.T IS NULL THEN 1 ELSE 0 END)                          AS NL,
         SUM(CASE WHEN st.T IS NULL AND j."TransType" = '30' THEN 1 ELSE 0 END) AS NJE,
         -- the churn that was removed, kept visible instead of vanishing
         SUM(CASE WHEN st.T IS NOT NULL THEN CAST(j."Debit" AS DOUBLE) ELSE 0 END) AS MCANC,
         -- of the REAL traffic, how much sat in a transaction that also touched a
         -- JIVO group / branch party
         SUM(CASE WHEN st.T IS NULL AND gx.T IS NOT NULL
                  THEN CAST(j."Debit"  AS DOUBLE) ELSE 0 END)                  AS MGIN,
         SUM(CASE WHEN st.T IS NULL AND gx.T IS NOT NULL
                  THEN CAST(j."Credit" AS DOUBLE) ELSE 0 END)                  AS MGOUT
  FROM {{SCHEMA}}.JDT1 j
  CROSS JOIN params p
  LEFT JOIN storno st ON st.T = j."TransId"
  LEFT JOIN grptx  gx ON gx.T = j."TransId"
  WHERE j."Account" IN (SELECT GL FROM univ)
    AND j."RefDate" >= p.WSTART
    AND j."RefDate" <= p.ASOF
  GROUP BY j."Account", TO_VARCHAR(j."RefDate",'YYYY-MM')
),
mv AS (
  SELECT GL,
         SUM(MIN_)   AS IN12,
         SUM(MOUT_)  AS OUT12,
         SUM(NL)     AS NL12,
         SUM(NJE)    AS NJE12,
         SUM(MCANC)  AS CANC12,
         SUM(MGIN)   AS GIN12,
         SUM(MGOUT)  AS GOUT12,
         -- months that actually moved: NL, not COUNT(*), or a month whose only
         -- traffic was a cancelled payment would still count as active.
         SUM(CASE WHEN NL > 0 THEN 1 ELSE 0 END) AS ACTMON
  FROM mon
  GROUP BY GL
),
-- every account x every one of the 12 slots, zero where nothing moved
dense AS (
  SELECT u.GL                       AS GL,
         mo.M                       AS M,
         COALESCE(m.MIN_,  0)       AS DIN,
         COALESCE(m.MOUT_, 0)       AS DOUT
  FROM univ u
  CROSS JOIN months mo
  LEFT JOIN mon m ON m.GL = u.GL AND m.M = mo.M
),
ser AS (
  -- TRAP: CAST(<double> AS DECIMAL(n,2)) TRUNCATES in HANA - it does not round.
  -- ROUND(0.11507,2) is a double a hair under 0.12, and the cast then chops it to
  -- 0.11, so a naive series is biased DOWN by up to a paisa a month (measured:
  -- Oil 2201405 lost 0.09 L over 12 months against its own 12m total).  Rounding
  -- inside the DECIMAL domain - TO_DECIMAL first, ROUND second - is exact, and is
  -- what keeps MONTHLY_*_SERIES adding back to RECEIPTS_IN_12M_L /
  -- PAYMENTS_OUT_12M_L.  Residual measured after the storno fix: at most 0.02 L on
  -- any account in any book - twelve 2dp values cannot sum to a 2dp total exactly.
  SELECT GL,
         STRING_AGG(M||'='||TO_VARCHAR(CAST(ROUND(TO_DECIMAL(DIN /100000,28,6),2)
                                            AS DECIMAL(18,2))),
                    ';' ORDER BY M)                                    AS SER_IN,
         STRING_AGG(M||'='||TO_VARCHAR(CAST(ROUND(TO_DECIMAL(DOUT/100000,28,6),2)
                                            AS DECIMAL(18,2))),
                    ';' ORDER BY M)                                    AS SER_OUT,
         STRING_AGG(M||'='||TO_VARCHAR(CAST(ROUND(TO_DECIMAL((DIN-DOUT)/100000,28,6),2)
                                            AS DECIMAL(18,2))),
                    ';' ORDER BY M)                                    AS SER_NET
  FROM dense
  GROUP BY GL
),

-- ---- assemble ---------------------------------------------------------------
core AS (
  SELECT u.GL, u.GLNAME, u.DRAWER, u.CATEGORY, u.CATEGORY_KIND,
         u.IS_CASH_AND_BANK, u.CURRTOTAL, u.NAME_DIGITS,
         p.ASOF, p.CC_RATE, o.OPEN_D,
         COALESCE(b.BAL, 0)                                            AS BAL,
         COALESCE(b.OPENING, 0)                                        AS OPENING,
         b.FIRSTMV, b.LASTMV,
         COALESCE(m.IN12, 0)                                           AS IN12,
         COALESCE(m.OUT12, 0)                                          AS OUT12,
         COALESCE(m.NL12, 0)                                           AS NL12,
         COALESCE(m.NJE12, 0)                                          AS NJE12,
         COALESCE(m.ACTMON, 0)                                         AS ACTMON,
         COALESCE(m.CANC12, 0)                                         AS CANC12,
         COALESCE(m.GIN12, 0)                                          AS GIN12,
         COALESCE(m.GOUT12, 0)                                         AS GOUT12,
         s.SER_IN, s.SER_OUT, s.SER_NET,
         h.BANKCODE                                                    AS H_BANKCODE,
         h.ACCTNO                                                      AS H_ACCTNO,
         h.BRANCH                                                      AS H_BRANCH,
         -- does the DSC1 house-bank row actually describe THIS G/L account?
         CASE
           WHEN h.ACCTNO_DIGITS IS NULL OR h.ACCTNO_DIGITS = ''  THEN NULL
           WHEN u.NAME_DIGITS = ''                               THEN 'UNKNOWN'
           WHEN u.NAME_DIGITS LIKE '%'||h.ACCTNO_DIGITS||'%'
             OR h.ACCTNO_DIGITS LIKE '%'||u.NAME_DIGITS||'%'     THEN 'AGREE'
           ELSE 'MISMATCH'
         END                                                           AS H_AGREE,
         bm.BANKCODE                                                   AS O_BANKCODE,
         bm.BANKNAME                                                   AS O_BANKNAME
  FROM univ u
  CROSS JOIN params p
  CROSS JOIN openday o
  LEFT JOIN bal       b  ON b.GL  = u.GL
  LEFT JOIN mv        m  ON m.GL  = u.GL
  LEFT JOIN ser       s  ON s.GL  = u.GL
  LEFT JOIN house     h  ON h.GL  = u.GL
  LEFT JOIN bankmatch bm ON bm.GL = u.GL
)
SELECT
  '{{SCHEMA}}'                                                    AS COMPANY_SCHEMA,
  c.ASOF                                                          AS AS_OF,
  c.CATEGORY                                                      AS CATEGORY,
  c.CATEGORY_KIND                                                 AS CATEGORY_KIND,
  c.IS_CASH_AND_BANK                                              AS IS_CASH_AND_BANK,
  c.GL                                                            AS GL_ACCT_CODE,
  c.DRAWER                                                        AS GL_DRAWER,
  REPLACE_REGEXPR('[0-9]' IN c.GLNAME WITH 'x' OCCURRENCE ALL)    AS GL_ACCT_LABEL_MASKED,
  COALESCE(CASE WHEN c.H_AGREE = 'AGREE' THEN c.H_BANKCODE END,
           c.O_BANKCODE)                                          AS BANK_CODE,
  COALESCE(c.O_BANKNAME,
           CASE WHEN UPPER(c.GLNAME) LIKE '%BANK%'
                THEN NULLIF(TRIM(SUBSTR_REGEXPR('^[A-Z& ]+' IN
                       REPLACE_REGEXPR('^(FDR|LOAN TERM|LOAN|TERM)[ .:-]*' IN
                                       UPPER(c.GLNAME) WITH ''))), '')
           END)                                                   AS BANK_NAME,
  CASE WHEN c.O_BANKNAME IS NOT NULL             THEN 'ODSC_MASTER'
       WHEN UPPER(c.GLNAME) LIKE '%BANK%'
        AND TRIM(SUBSTR_REGEXPR('^[A-Z& ]+' IN
              REPLACE_REGEXPR('^(FDR|LOAN TERM|LOAN|TERM)[ .:-]*' IN
                              UPPER(c.GLNAME) WITH ''))) <> ''    THEN 'GL_ACCT_NAME'
       ELSE 'UNRESOLVED' END                                      AS BANK_NAME_SOURCE,
  CASE WHEN c.H_AGREE = 'AGREE' THEN c.H_BRANCH END                AS BRANCH,
  CASE WHEN c.H_ACCTNO IS NOT NULL THEN 'Y' ELSE 'N' END          AS IS_HOUSE_BANK,
  COALESCE(c.H_AGREE, 'NO_HOUSE_BANK_ROW')                        AS HOUSE_BANK_AGREES,
  CASE
    WHEN c.H_AGREE = 'AGREE' AND LENGTH(c.H_ACCTNO) >= 4
      THEN 'xxxx'||RIGHT(c.H_ACCTNO, 4)
    WHEN LENGTH(c.NAME_DIGITS) >= 4
      THEN 'xxxx'||RIGHT(c.NAME_DIGITS, 4)
    ELSE NULL
  END                                                             AS ACCT_NO_MASKED,
  CASE
    WHEN c.H_AGREE = 'AGREE' AND LENGTH(c.H_ACCTNO) >= 4 THEN 'DSC1_HOUSE_BANK'
    WHEN LENGTH(c.NAME_DIGITS) >= 4                      THEN 'GL_ACCT_NAME'
    ELSE 'NONE'
  END                                                             AS ACCT_NO_SOURCE,
  CASE
    WHEN c.H_AGREE = 'AGREE' AND LENGTH(c.H_ACCTNO) >= 4
      THEN LENGTH(REPLACE_REGEXPR('[^0-9]' IN c.H_ACCTNO WITH '' OCCURRENCE ALL))
    ELSE LENGTH(c.NAME_DIGITS)
  END                                                             AS ACCT_NO_NDIGITS,

  ROUND(c.BAL       / 100000, 2)                                  AS BALANCE_L,
  ROUND(c.CURRTOTAL / 100000, 2)                                  AS CURRTOTAL_TODAY_L,
  CASE WHEN ROUND(c.BAL,2) > 0 THEN 'DEBIT'
       WHEN ROUND(c.BAL,2) < 0 THEN 'CREDIT'
       ELSE 'NIL' END                                             AS BALANCE_SIGN,
  ROUND(CASE WHEN c.BAL > 0 THEN c.BAL ELSE 0 END / 100000, 2)    AS FUNDS_AVAILABLE_L,
  ROUND(CASE WHEN c.BAL < 0 THEN -c.BAL ELSE 0 END / 100000, 2)   AS AMOUNT_DRAWN_L,
  -- an asset-side account in credit is a genuine overdraw / booking error;
  -- a CC/OD or loan account in credit is simply borrowing, and is NOT flagged.
  CASE WHEN c.CATEGORY IN ('CURRENT_ACCOUNT','PAYMENT_WALLET','CASH_IN_HAND',
                           'FIXED_DEPOSIT')
             AND c.BAL < -100 THEN 'Y' ELSE 'N' END               AS OVERDRAWN_FLAG,
  CASE WHEN c.CATEGORY_KIND = 'BORROWING' OR c.CATEGORY = 'CASH_CREDIT_OD'
       THEN ROUND((CASE WHEN c.BAL < 0 THEN -c.BAL ELSE 0 END) * c.CC_RATE / 100000, 2)
       ELSE 0 END                                                 AS EST_ANNUAL_INTEREST_L,

  ROUND(c.IN12  / 100000, 2)                                      AS RECEIPTS_IN_12M_L,
  ROUND(c.OUT12 / 100000, 2)                                      AS PAYMENTS_OUT_12M_L,
  ROUND((c.IN12 - c.OUT12) / 100000, 2)                           AS NET_12M_L,
  ROUND(c.OUT12 / (CASE WHEN c.ACTMON = 0 THEN 1 ELSE c.ACTMON END) / 100000, 2)
                                                                  AS AVG_MONTHLY_OUT_L,
  ROUND(c.CANC12 / 100000, 2)                                     AS CANCELLED_GROSS_12M_L,
  ROUND(c.GIN12   / 100000, 2)                                    AS INTERCO_IN_12M_L,
  ROUND(c.GOUT12  / 100000, 2)                                    AS INTERCO_OUT_12M_L,
  c.NL12                                                          AS N_LINES_12M,
  c.ACTMON                                                        AS ACTIVE_MONTHS_12M,
  CASE WHEN c.NL12 = 0 THEN NULL
       ELSE CAST(ROUND(TO_DECIMAL(100.0 * c.NJE12 / c.NL12, 28, 6), 1) AS DECIMAL(5,1))
  END                                                             AS MANUAL_JE_LINE_PCT_12M,

  TO_VARCHAR(c.FIRSTMV, 'YYYY-MM-DD')                             AS FIRST_MOVE_DATE,
  TO_VARCHAR(c.LASTMV,  'YYYY-MM-DD')                             AS LAST_MOVE_DATE,
  CASE WHEN c.LASTMV IS NULL THEN NULL
       ELSE DAYS_BETWEEN(c.LASTMV, c.ASOF) END                    AS DAYS_SINCE_LAST_MOVE,
  CASE WHEN c.LASTMV IS NULL THEN 'Y'
       WHEN DAYS_BETWEEN(c.LASTMV, c.ASOF) >= 90 THEN 'Y'
       ELSE 'N' END                                               AS DORMANT_90D_FLAG,
  CASE WHEN c.FIRSTMV IS NULL THEN 'Y' ELSE 'N' END               AS NEVER_USED_FLAG,
  TO_VARCHAR(c.OPEN_D, 'YYYY-MM-DD')                              AS BOOK_OPENING_DATE,
  ROUND(c.OPENING / 100000, 2)                                    AS OPENING_BAL_L,

  c.SER_IN                                                        AS MONTHLY_IN_L_SERIES,
  c.SER_OUT                                                       AS MONTHLY_OUT_L_SERIES,
  c.SER_NET                                                       AS MONTHLY_NET_L_SERIES,

  ROUND(SUM(CASE WHEN c.IS_CASH_AND_BANK = 'Y' THEN c.BAL ELSE 0 END)
        OVER () / 100000, 2)                                      AS TOT_CASH_AND_BANK_L,
  ROUND(SUM(CASE WHEN c.CATEGORY = 'CURRENT_ACCOUNT' THEN c.BAL ELSE 0 END)
        OVER () / 100000, 2)                                      AS TOT_BANK_CURRENT_L,
  ROUND(SUM(CASE WHEN c.CATEGORY = 'CASH_IN_HAND' THEN c.BAL ELSE 0 END)
        OVER () / 100000, 2)                                      AS TOT_CASH_IN_HAND_L,
  ROUND(SUM(CASE WHEN c.CATEGORY = 'PAYMENT_WALLET' THEN c.BAL ELSE 0 END)
        OVER () / 100000, 2)                                      AS TOT_WALLET_L,
  ROUND(SUM(CASE WHEN c.CATEGORY = 'CASH_CREDIT_OD' THEN c.BAL ELSE 0 END)
        OVER () / 100000, 2)                                      AS TOT_CC_OD_NET_L,
  ROUND(SUM(CASE WHEN c.CATEGORY = 'FIXED_DEPOSIT' THEN c.BAL ELSE 0 END)
        OVER () / 100000, 2)                                      AS TOT_FIXED_DEPOSIT_L,
  ROUND(SUM(CASE WHEN (c.CATEGORY_KIND = 'BORROWING' OR c.CATEGORY = 'CASH_CREDIT_OD')
                      AND c.BAL < 0 THEN -c.BAL ELSE 0 END)
        OVER () / 100000, 2)                                      AS TOT_BORROWINGS_L
FROM core c
ORDER BY
  CASE c.CATEGORY
    WHEN 'CURRENT_ACCOUNT' THEN 1 WHEN 'CASH_CREDIT_OD' THEN 2
    WHEN 'PAYMENT_WALLET'  THEN 3 WHEN 'CASH_IN_HAND'   THEN 4
    WHEN 'FIXED_DEPOSIT'   THEN 5 WHEN 'TERM_LOAN'      THEN 6
    WHEN 'VEHICLE_LOAN'    THEN 7 ELSE 8 END,
  ABS(c.BAL) DESC,
  c.GL
