-- ============================================================================
-- cash-sale.sql  ·  section_id: cash-sale  ·  as-of {{ASOF}}  ·  schema {{SCHEMA}}
-- ----------------------------------------------------------------------------
-- WHAT IT RETURNS
--   A cash-sale register for one company book, as a TALL fact table: one row per
--   (SECTION, ROW_KEY) — that pair is UNIQUE, checked.  Slice on SECTION; the
--   sections are DIFFERENT CUTS OF THE SAME MONEY, so never add them together.
--
--     1_SCOPE       one row per business partner that IS a cash-sale card   (~3-6 rows)
--     2_MONTH       cash-sale invoices/credit notes by DocDate month        (~0-25 rows)
--     3_BRANCH      by GST branch (OINV."BPLId", named from OBPL)           (~0-4 rows)
--     4_WAREHOUSE   by dominant stock warehouse of the document             (~0-12 rows)
--     5_CUSTOMER    by cash-sale card                                       (~3-6 rows)
--     6_TENDER_MONTH  ALTERNATIVE DEFINITION: physical CASH tendered on
--                     customer receipts (ORCT."CashSum"), by month          (~0-25 rows)
--     7_GL_CASH     GL movement on the cash-in-hand tills and on the
--                   "SUNDRY DEBTORS CASH SALE" control account (cross-check) (~4 rows)
--     9_TOTAL       four grand-total rows, each a DIFFERENT population       (4 rows)
--
--   EXPECTED SIZE: ~30-80 rows per company. Never unbounded.
--
-- COLUMNS (identical for every section; measures that do not apply are 0)
--   SECTION, SORT_KEY, ROW_KEY, ROW_LABEL, ROW_NOTE,
--   INV_CNT, INV_GROSS_INR, INV_NET_INR,       -- INVOICES ONLY. Never receipts, never GL lines.
--   CN_CNT,  CN_GROSS_INR,  CN_NET_INR,
--   TURNOVER_NET_INR,          -- INV_NET - CN_NET  (JIVO turnover definition)
--   OPEN_CNT, OPEN_INR,        -- still DocStatus='O'.  A DIAGNOSTIC, NOT A RECEIVABLE - see T6.
--   UNAPPLIED_RCT_INR,         -- ORCT."OpenBal" on the same cards: money in, never applied
--   LEDGER_BAL_INR,            -- OCRD."Balance": GROUND TRUTH for what the card owes (+DR/-CR)
--   TXN_CNT,                   -- receipts (6_TENDER_MONTH / 9_TOTAL C,D) or JDT1 lines (7_GL_CASH)
--   CASH_TENDER_INR,           -- ORCT."CashSum" actually received in notes/coins
--   GL_DEBIT_INR, GL_CREDIT_INR
--
--   MONEY UNITS: every money column is named _INR and is in RUPEES, unscaled.
--   Verified against the GL: 9_TOTAL A INV_GROSS_INR for Oil = 1,438,780 rupees
--   and JDT1 debits on 1101014 = 3,586,948 rupees (= 35.87 L).  No _L / _CR here.
--
-- ----------------------------------------------------------------------------
-- THE DEFINITION, AND WHY (settled 2026-08-21 against live data)
--
--   At JIVO "CASH SALE" is a SALES CHANNEL (counter / walk-in / no-credit), NOT a
--   tender type.  It is carried by dedicated customer cards that post to the
--   dedicated receivables control account 1101014 SUNDRY DEBTORS CASH SALE.
--   PROOF (re-run 2026-08-21): 1101014 exists in all three books and ONLY these
--   cards post to it -- a JDT1 sweep of the account by "ShortName" returns exactly
--   the same card list the scope CTE derives, nobody else.  Oil JDT1 debits on
--   1101014 = 3,586,948 vs 3,464,703 of invoices on the 1101014 cards; the
--   122,245 gap is non-invoice debits (a 56,750 JE on CASH SALE PB, which has no
--   invoices at all, plus 58,995 on HARPREET and 6,500 on KAMALPREET).
--   93% of the money against those cards then arrives by BANK TRANSFER, not cash,
--   so tender is NOT the marker.
--
--   DISPROVEN candidates (each tested live, see notes/cash-sale.md):
--     * OINV."DocType"          -> only 'I'/'S' (item/service). No cash value.
--     * POS fields              -> "POSCashN"/"PosCashReg"/"POSRcptNo"/"DigPayment"
--                                  are 0/blank on all 31,027 Oil invoices. SAP POS unused.
--     * OINV."GroupNum" (terms) -> term -1 "ADVANCE/CASH/0 DAYS" is the DEFAULT
--                                  bucket: 15,586 Oil invoices, 925.91 Cr. Useless.
--                                  Term 10 "COD" = 39 invoices, 0.02 Cr. Not it either.
--     * "DocDueDate" = "DocDate" -> 14,820 Oil invoices / 879.10 Cr, top names are
--                                  JIVO MART (intercompany 320 Cr) and JIVO WELLNESS
--                                  PVT LTD - PB (branch). Definitively not cash sales.
--     * ORCT."CashSum" > 0      -> REAL but a DIFFERENT thing: cash COLLECTED against
--                                  ordinary credit sales (route salesmen "DEL ...").
--                                  Kept as section 6_TENDER_MONTH, not as the register.
--
-- TRAPS HANDLED  (every one re-tested live 2026-08-21; figures are as-of that day)
--   T1 name-matching '%CASH%' catches CASHEW, METRO CASH & CARRY (a 66.4 L credit
--      customer), CASHBACK, CASH PURCHASE HR.  -> match the phrase 'CASH SALE' and
--      explicitly bar '%CASH & CARRY%'.  VERIFIED: with the bar in place the scope
--      is 6 cards (Oil) / 3 (Mart) / 5 (Bev); METRO and CASHEW are out, the two
--      CASH-named VENDOR cards are out via "CardType"='C'.
--   T2 cards renamed over time: CUSTA001015 was BALWINDER KAUR J/3 -> KAMAL J3
--      PAYMENTS -> KAMALJEET CASH SALE J3.  OINV."CardName" is the historic snapshot.
--      -> the scope is resolved from OCRD (master) and matched by "CardCode".
--   T3 some cash cards sit on OTHER control accounts (ONLINE CASH SALE WEBSITE ->
--      1101005 E-COM; KAMALJEET CASH SALE J3 in Oil -> 1101008 CALL CENTRE).
--      -> scope = control account 1101014 OR name phrase, union of both.
--   T4 migrated openings: Oil CASH SALE DL has 35 invoices all dated the 2024-09-30
--      go-live, VatSum 0, no warehouse on the lines, 2,441,924 gross.  They are an
--      opening balance, not a sale.  -> they are EXCLUDED from 9_TOTAL A and from
--      3_BRANCH / 4_WAREHOUSE / 5_CUSTOMER so every cut of the register adds up to
--      the same headline, shown separately as 9_TOTAL B, and kept visible in
--      2_MONTH under their own ROW_KEY 'YYYY-MM (opening)'.
--      (Before this fix the three breakdowns silently included them: Oil's customer
--      table added to 3,800,716 against a 1,358,792 headline, 2.8x.)
--   T5 cancelled documents: HANA "CANCELED" carries 'N', 'Y' AND 'C' (the reversing
--      document).  VERIFIED Oil OINV: 1129 'N', 18 'Y', 18 'C' (29,885 each side);
--      Bev: 284 'N', 2 'Y', 2 'C'.  -> only "CANCELED"='N' counts.  ORCT spells it
--      "Canceled" and carries only 'Y'/'N' (Oil 16 cancelled cash receipts,
--      284,090; Bev 11, 356,122) -> "Canceled"='N'.
--   T6 THE BIG ONE - "open" here does NOT mean unpaid.  Cash-sale invoices stay
--      DocStatus='O' because settlement is a lump on-account receipt that is never
--      internally applied: JDT1."IntrnMatch"=0 on 100% of the 1101014 lines
--      (Oil 1295 of 1295, Bev 336 of 336).  Bev CASH SALE DL shows 4,355,961 of
--      "open" invoices while its OCRD."Balance" is MINUS 1,097,839 - a credit -
--      because 5,786,550 of receipts sit unapplied.  -> OPEN_INR is reported as a
--      diagnostic ONLY, always beside UNAPPLIED_RCT_INR and LEDGER_BAL_INR, and
--      the OCRD balance is NEVER netted against the receipts (that double-counts:
--      the receipt is already inside the balance).
--   T7 ORCT."DocType"='A' rows are till-to-till GL transfers booked as receipts
--      (Mart 14,312,721 · Oil 4,103,144 · Bev 856,190) and would double-count
--      customer cash.  -> the tender sections take "DocType"='C' only.
--   T8 branch/intercompany is not trade.  The bar is (a) OCRG."GroupName" LIKE
--      '%BRANCH%', (b) the C-0005 group CardCodes APPLIED PER BOOK - the 23 codes
--      are per-company and the same code is a different party in another book
--      (CUSTA001099 is a group card in Oil but HK TRADERS, an ordinary customer,
--      in Beverages), and (c) the NAME test '%JIVO%'.
--      VERIFIED: none of them is a cash-sale card in any book, so the register
--      itself is 100% external.  The CASH TENDER side was NOT clean - Oil had
--      147,000 of cash receipts from CUSTA000606 JIVO MART PVT LTD sitting inside
--      the total.  -> tender is split: 9_TOTAL C = external, 9_TOTAL D = the
--      group/branch slice, flagged and quantified, never silently folded in.
--   T9 OINV."BPLName" is a per-document snapshot, so Beverages branch 2 arrives as
--      both 'FACTORY' (97 docs) and 'Factory' (7 docs) and used to emit TWO rows
--      with the same ROW_KEY '2'.  -> group on "BPLId" only, name from OBPL.
--   T10 an empty book must not produce NULLs.  Mart has ZERO cash-sale documents
--      and its 9_TOTAL row came back all-NULL, rendering as em dashes ("unknown")
--      where the truth is zero.  -> every 9_TOTAL aggregate is IFNULL-wrapped, and
--      7_GL_CASH LEFT JOINs JDT1 so an account that exists but has no lines still
--      reports (Mart 1101014: exists, 0 lines, 0 movement).
--   T11 raw HANA DOUBLEs do not survive the pipeline.  build_data.coerce()
--      refuses to float() a token with more than 15 digits (it protects doc
--      numbers and GSTINs), so 1358792.4106999983 arrives in data.json as a
--      STRING and index.html, which switches on `typeof v === 'number'`, prints
--      it raw instead of formatting it as money.  128 money cells across the
--      three books were rendering as float noise.  -> every money column is
--      ROUNDed to 2 dp once, in the outer SELECT, where no branch can miss it.
-- ============================================================================
WITH
-- ---- the C-0005 group/intercompany CardCodes, PER BOOK (T8) ----------------
grp_card AS (
  SELECT CARD_CODE FROM (
              SELECT 'JIVO_OIL_HANADB'       AS BOOK, 'CUSTA000001' AS CARD_CODE FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA000002' FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA000003' FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA000004' FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA000606' FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA000827' FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA000906' FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA001099' FROM DUMMY
    UNION ALL SELECT 'JIVO_OIL_HANADB',       'CUSTA001113' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000001' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000827' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000874' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000875' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000876' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000877' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000878' FROM DUMMY
    UNION ALL SELECT 'JIVO_MART_HANADB',      'CUSTA000926' FROM DUMMY
    UNION ALL SELECT 'JIVO_BEVERAGES_HANADB', 'CUSTA000001' FROM DUMMY
    UNION ALL SELECT 'JIVO_BEVERAGES_HANADB', 'CUSTA000002' FROM DUMMY
    UNION ALL SELECT 'JIVO_BEVERAGES_HANADB', 'CUSTA000003' FROM DUMMY
    UNION ALL SELECT 'JIVO_BEVERAGES_HANADB', 'CUSTA000004' FROM DUMMY
    UNION ALL SELECT 'JIVO_BEVERAGES_HANADB', 'CUSTA000606' FROM DUMMY
    UNION ALL SELECT 'JIVO_BEVERAGES_HANADB', 'CUSTA000827' FROM DUMMY
  ) WHERE BOOK = '{{SCHEMA}}'
),
-- ---- scope: the cash-sale customer cards, derived, never hard-coded --------
cc AS (
  SELECT c."CardCode"            AS CARD_CODE,
         c."CardName"            AS CARD_NAME,
         IFNULL(g."GroupName",'') AS GRP_NAME,
         c."DebPayAcct"          AS CTRL_ACCT,
         c."validFor"            AS ACTIVE,
         CAST(c."Balance" AS DOUBLE) AS BAL
  FROM {{SCHEMA}}.OCRD c
  LEFT JOIN {{SCHEMA}}.OCRG g
         ON g."GroupCode" = c."GroupCode" AND g."GroupType" = c."CardType"
  WHERE c."CardType" = 'C'
    AND (   c."DebPayAcct" IN (SELECT a."AcctCode" FROM {{SCHEMA}}.OACT a
                               WHERE UPPER(a."AcctName") LIKE '%DEBTORS CASH SALE%')
         OR UPPER(c."CardName") LIKE '%CASH SALE%' )
    AND UPPER(c."CardName") NOT LIKE '%CASH & CARRY%'          -- T1 METRO
    AND UPPER(IFNULL(g."GroupName",'')) NOT LIKE '%BRANCH%'    -- T8 (a)
    AND UPPER(c."CardName") NOT LIKE '%JIVO%'                  -- T8 (c) name test
    AND c."CardCode" NOT IN (SELECT CARD_CODE FROM grp_card)   -- T8 (b) per book
),
-- ---- unapplied customer receipts sitting on those cards (T6 diagnostic) ----
rct_open AS (
  SELECT r."CardCode" AS CARD_CODE,
         SUM(CAST(IFNULL(r."OpenBal",0) AS DOUBLE)) AS UNAPPLIED
  FROM {{SCHEMA}}.ORCT r
  WHERE r."Canceled" = 'N' AND r."DocDate" <= DATE'{{ASOF}}'
    AND r."CardCode" IN (SELECT CARD_CODE FROM cc)
  GROUP BY r."CardCode"
),
-- ---- the documents in scope (invoices + credit notes) ----------------------
docs AS (
  SELECT 'INV' AS KIND, i."DocEntry" AS DE, i."DocDate" AS DDATE, i."CardCode" AS CARD_CODE,
         IFNULL(TO_VARCHAR(i."BPLId"),'?') AS BR_ID, IFNULL(i."BPLName",'(no branch)') AS BR_NAME,
         CAST(i."DocTotal" AS DOUBLE) AS GROSS,
         CAST(i."DocTotal" AS DOUBLE) - CAST(i."VatSum" AS DOUBLE) AS NET,
         i."DocStatus" AS DSTAT,
         CAST(i."DocTotal" AS DOUBLE) - CAST(i."PaidToDate" AS DOUBLE) AS OPENAMT,
         CASE WHEN i."DocDate" = DATE'2024-09-30' THEN 'MIGRATED_OPENING' ELSE 'REAL' END AS TAG
  FROM {{SCHEMA}}.OINV i
  WHERE i."CANCELED" = 'N' AND i."DocDate" <= DATE'{{ASOF}}'
    AND i."CardCode" IN (SELECT CARD_CODE FROM cc)
  UNION ALL
  SELECT 'CN', n."DocEntry", n."DocDate", n."CardCode",
         IFNULL(TO_VARCHAR(n."BPLId"),'?'), IFNULL(n."BPLName",'(no branch)'),
         CAST(n."DocTotal" AS DOUBLE),
         CAST(n."DocTotal" AS DOUBLE) - CAST(n."VatSum" AS DOUBLE),
         n."DocStatus",
         CAST(n."DocTotal" AS DOUBLE) - CAST(n."PaidToDate" AS DOUBLE),
         CASE WHEN n."DocDate" = DATE'2024-09-30' THEN 'MIGRATED_OPENING' ELSE 'REAL' END
  FROM {{SCHEMA}}.ORIN n
  WHERE n."CANCELED" = 'N' AND n."DocDate" <= DATE'{{ASOF}}'
    AND n."CardCode" IN (SELECT CARD_CODE FROM cc)
),
-- ---- dominant warehouse per document (one bucket per doc, never fans) ------
dwhs AS (
  SELECT DE, KIND,
         CASE WHEN NW = 0 THEN '(no stock warehouse)'
              WHEN NW > 1 THEN '(multi-warehouse)'
              ELSE W END AS WHS
  FROM (
    SELECT d.DE, d.KIND,
           (SELECT COUNT(DISTINCT l."WhsCode") FROM {{SCHEMA}}.INV1 l WHERE l."DocEntry" = d.DE AND d.KIND='INV')
           + (SELECT COUNT(DISTINCT m."WhsCode") FROM {{SCHEMA}}.RIN1 m WHERE m."DocEntry" = d.DE AND d.KIND='CN') AS NW,
           IFNULL((SELECT MIN(l."WhsCode") FROM {{SCHEMA}}.INV1 l WHERE l."DocEntry" = d.DE AND d.KIND='INV'),
                  (SELECT MIN(m."WhsCode") FROM {{SCHEMA}}.RIN1 m WHERE m."DocEntry" = d.DE AND d.KIND='CN')) AS W
    FROM docs d
  )
),
-- ---- customer cash tendered on receipts (alternative definition) -----------
-- T7: "DocType"='C' only.  T8: classified, never silently folded in.
tender AS (
  SELECT r."DocDate" AS DDATE, r."CardCode" AS CARD_CODE,
         CAST(r."CashSum" AS DOUBLE) AS CASH,
         CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%BRANCH%'
                OR UPPER(IFNULL(c."CardName",''))  LIKE '%JIVO%'
                OR r."CardCode" IN (SELECT CARD_CODE FROM grp_card)
              THEN 'GROUP' ELSE 'EXTERNAL' END AS PARTY_CLASS
  FROM {{SCHEMA}}.ORCT r
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode" = r."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode" AND g."GroupType" = c."CardType"
  WHERE r."Canceled" = 'N'                 -- ORCT spells it "Canceled", values Y/N
    AND r."DocType"  = 'C'                 -- T7: 'A' rows are till-to-till transfers
    AND IFNULL(r."CashSum",0) > 0
    AND r."DocDate" <= DATE'{{ASOF}}'
),
-- ---- GL cross-check accounts ----------------------------------------------
gl_acct AS (
  SELECT a."AcctCode" AS AC, a."AcctName" AS AN, 'CASH TILL' AS ROLE
  FROM {{SCHEMA}}.OACT a
  WHERE a."Postable" = 'Y'
    AND a."FatherNum" IN (SELECT p."AcctCode" FROM {{SCHEMA}}.OACT p
                          WHERE UPPER(p."AcctName") = 'CASH IN HAND' AND p."Postable" = 'N')
  UNION ALL
  SELECT a."AcctCode", a."AcctName", 'AR CONTROL'
  FROM {{SCHEMA}}.OACT a
  WHERE UPPER(a."AcctName") LIKE '%DEBTORS CASH SALE%'
)
-- ===========================================================================
-- Money is ROUNDed to paise HERE, in ONE place, so no branch can escape it.
-- WHY THIS MATTERS: build_data.coerce() refuses to float() a token with more
-- than 15 digits (it protects doc numbers and GSTINs), so a raw HANA DOUBLE
-- like 1358792.4106999983 lands in data.json as a STRING and the renderer,
-- which switches on `typeof v === 'number'`, prints it verbatim instead of
-- "Rs 13.59 L".  Unrounded, 128 money cells across the three books rendered as
-- raw float noise.  Every other section in this pipeline rounds; this one did not.
SELECT
  X.SECTION, X.SORT_KEY, X.ROW_KEY, X.ROW_LABEL, X.ROW_NOTE,
  X.INV_CNT,
  ROUND(X.INV_GROSS_INR,     2) AS INV_GROSS_INR,
  ROUND(X.INV_NET_INR,       2) AS INV_NET_INR,
  X.CN_CNT,
  ROUND(X.CN_GROSS_INR,      2) AS CN_GROSS_INR,
  ROUND(X.CN_NET_INR,        2) AS CN_NET_INR,
  ROUND(X.TURNOVER_NET_INR,  2) AS TURNOVER_NET_INR,
  X.OPEN_CNT,
  ROUND(X.OPEN_INR,          2) AS OPEN_INR,
  ROUND(X.UNAPPLIED_RCT_INR, 2) AS UNAPPLIED_RCT_INR,
  ROUND(X.LEDGER_BAL_INR,    2) AS LEDGER_BAL_INR,
  X.TXN_CNT,
  ROUND(X.CASH_TENDER_INR,   2) AS CASH_TENDER_INR,
  ROUND(X.GL_DEBIT_INR,      2) AS GL_DEBIT_INR,
  ROUND(X.GL_CREDIT_INR,     2) AS GL_CREDIT_INR
FROM (
  -- 1_SCOPE ------------------------------------------------------------------
  SELECT '1_SCOPE' AS SECTION, cc.CARD_CODE AS SORT_KEY, cc.CARD_CODE AS ROW_KEY,
         cc.CARD_NAME AS ROW_LABEL,
         'ctrl ' || cc.CTRL_ACCT || ' | grp ' || cc.GRP_NAME ||
         ' | active ' || cc.ACTIVE AS ROW_NOTE,
         0 AS INV_CNT, 0.0 AS INV_GROSS_INR, 0.0 AS INV_NET_INR,
         0 AS CN_CNT, 0.0 AS CN_GROSS_INR, 0.0 AS CN_NET_INR,
         0.0 AS TURNOVER_NET_INR,
         0 AS OPEN_CNT, 0.0 AS OPEN_INR,
         IFNULL((SELECT ro.UNAPPLIED FROM rct_open ro WHERE ro.CARD_CODE = cc.CARD_CODE),0) AS UNAPPLIED_RCT_INR,
         cc.BAL AS LEDGER_BAL_INR,
         0 AS TXN_CNT, 0.0 AS CASH_TENDER_INR,
         0.0 AS GL_DEBIT_INR, 0.0 AS GL_CREDIT_INR
  FROM cc

  UNION ALL
  -- 2_MONTH ------------------------------------------------------------------
  -- migrated openings keep their own ROW_KEY so (SECTION,ROW_KEY) stays unique
  -- even if a real invoice is ever dated in the go-live month.
  SELECT '2_MONTH', TO_VARCHAR(d.DDATE,'YYYY-MM') || '|' || d.TAG,
         TO_VARCHAR(d.DDATE,'YYYY-MM') || CASE WHEN d.TAG='REAL' THEN '' ELSE ' (opening)' END,
         TO_VARCHAR(d.DDATE,'YYYY-MM') || CASE WHEN d.TAG='REAL' THEN '' ELSE ' (opening)' END,
         CASE WHEN d.TAG='REAL' THEN 'trading month'
              ELSE 'MIGRATED OPENING - go-live balance, not a sale; excluded from 9_TOTAL A' END,
         SUM(CASE WHEN d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET ELSE -d.NET END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN d.OPENAMT ELSE 0 END),
         0.0, 0.0, 0, 0.0, 0.0, 0.0
  FROM docs d GROUP BY TO_VARCHAR(d.DDATE,'YYYY-MM'), d.TAG

  UNION ALL
  -- 3_BRANCH -----------------------------------------------------------------
  -- T9: group on "BPLId" only; the label comes from OBPL, not the per-document
  -- snapshot, so 'FACTORY'/'Factory' cannot split one branch into two rows.
  SELECT '3_BRANCH', d.BR_ID, d.BR_ID,
         IFNULL(MAX(b."BPLName"), MAX(d.BR_NAME)),
         'GST branch (BPLId), name from OBPL | excl. migrated openings',
         SUM(CASE WHEN d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET ELSE -d.NET END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN d.OPENAMT ELSE 0 END),
         0.0, 0.0, 0, 0.0, 0.0, 0.0
  FROM docs d
  LEFT JOIN {{SCHEMA}}.OBPL b ON TO_VARCHAR(b."BPLId") = d.BR_ID
  WHERE d.TAG = 'REAL'
  GROUP BY d.BR_ID

  UNION ALL
  -- 4_WAREHOUSE --------------------------------------------------------------
  SELECT '4_WAREHOUSE', w.WHS, w.WHS, IFNULL(o."WhsName", w.WHS),
         'dominant stock warehouse | excl. migrated openings',
         SUM(CASE WHEN d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET ELSE -d.NET END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN d.OPENAMT ELSE 0 END),
         0.0, 0.0, 0, 0.0, 0.0, 0.0
  FROM docs d
  JOIN dwhs w ON w.DE = d.DE AND w.KIND = d.KIND
  LEFT JOIN {{SCHEMA}}.OWHS o ON o."WhsCode" = w.WHS
  WHERE d.TAG = 'REAL'
  GROUP BY w.WHS, o."WhsName"

  UNION ALL
  -- 5_CUSTOMER ---------------------------------------------------------------
  SELECT '5_CUSTOMER', d.CARD_CODE, d.CARD_CODE, MAX(cc.CARD_NAME),
         'master name (invoice snapshots may differ) | excl. migrated openings',
         SUM(CASE WHEN d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.GROSS ELSE 0 END),
         SUM(CASE WHEN d.KIND='CN'  THEN d.NET   ELSE 0 END),
         SUM(CASE WHEN d.KIND='INV' THEN d.NET ELSE -d.NET END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN 1 ELSE 0 END),
         SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN d.OPENAMT ELSE 0 END),
         IFNULL(MAX((SELECT ro.UNAPPLIED FROM rct_open ro WHERE ro.CARD_CODE = d.CARD_CODE)),0),
         MAX(cc.BAL),
         0,
         IFNULL((SELECT SUM(t.CASH) FROM tender t WHERE t.CARD_CODE = d.CARD_CODE),0),
         0.0, 0.0
  FROM docs d JOIN cc ON cc.CARD_CODE = d.CARD_CODE
  WHERE d.TAG = 'REAL'
  GROUP BY d.CARD_CODE

  UNION ALL
  -- 6_TENDER_MONTH  (ALTERNATIVE DEFINITION: physical cash received) ----------
  -- external parties only; the group/branch slice is broken out as 9_TOTAL D.
  SELECT '6_TENDER_MONTH', TO_VARCHAR(t.DDATE,'YYYY-MM'), TO_VARCHAR(t.DDATE,'YYYY-MM'),
         TO_VARCHAR(t.DDATE,'YYYY-MM'),
         'ORCT."CashSum", DocType=C, external only (cash COLLECTED, not cash SOLD)',
         0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0,
         COUNT(*), SUM(t.CASH), 0.0, 0.0
  FROM tender t WHERE t.PARTY_CLASS = 'EXTERNAL'
  GROUP BY TO_VARCHAR(t.DDATE,'YYYY-MM')

  UNION ALL
  -- 7_GL_CASH  (cross-check) --------------------------------------------------
  -- LEFT JOIN: an account that exists with no postings still reports, at zero.
  SELECT '7_GL_CASH', g.AC, g.AC, g.AN, g.ROLE,
         0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0,
         COUNT(j."Account"), 0.0,
         IFNULL(SUM(CAST(j."Debit" AS DOUBLE)),0), IFNULL(SUM(CAST(j."Credit" AS DOUBLE)),0)
  FROM gl_acct g
  LEFT JOIN {{SCHEMA}}.JDT1 j ON j."Account" = g.AC AND j."RefDate" <= DATE'{{ASOF}}'
  GROUP BY g.AC, g.AN, g.ROLE

  UNION ALL
  -- 9_TOTAL  A: the register - cash-sale invoices, migrated openings excluded --
  SELECT '9_TOTAL', 'A', 'CASH_SALE_INVOICES',
         'Cash-sale register (invoices on cash-sale cards)',
         'excl. 2024-09-30 migrated openings; excl. cancelled. OPEN_INR is NOT a '
         || 'receivable - LEDGER_BAL_INR (OCRD balance, +DR/-CR) is what is owed.',
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN 1 ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN d.GROSS ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN d.NET   ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='CN'  THEN 1 ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='CN'  THEN d.GROSS ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='CN'  THEN d.NET   ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN d.NET ELSE -d.NET END),0),
         IFNULL(SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN 1 ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN d.OPENAMT ELSE 0 END),0),
         IFNULL((SELECT SUM(ro.UNAPPLIED) FROM rct_open ro),0),
         IFNULL((SELECT SUM(cc2.BAL) FROM cc cc2),0),
         0, 0.0, 0.0, 0.0
  FROM docs d WHERE d.TAG = 'REAL'

  UNION ALL
  -- 9_TOTAL  B: the migrated openings, shown, not hidden ----------------------
  SELECT '9_TOTAL', 'B', 'MIGRATED_OPENINGS',
         'Go-live opening balances dated 2024-09-30 (NOT sales)',
         'EXCLUDED from A and from the 3_/4_/5_ breakdowns. Cards: '
         || IFNULL((SELECT STRING_AGG(x.CARD_CODE, ', ' ORDER BY x.CARD_CODE)
                    FROM (SELECT DISTINCT d2.CARD_CODE FROM docs d2 WHERE d2.TAG='MIGRATED_OPENING') x),'none'),
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN 1 ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN d.GROSS ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN d.NET   ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='CN'  THEN 1 ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='CN'  THEN d.GROSS ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='CN'  THEN d.NET   ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.KIND='INV' THEN d.NET ELSE -d.NET END),0),
         IFNULL(SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN 1 ELSE 0 END),0),
         IFNULL(SUM(CASE WHEN d.DSTAT='O' AND d.KIND='INV' THEN d.OPENAMT ELSE 0 END),0),
         0.0, 0.0, 0, 0.0, 0.0, 0.0
  FROM docs d WHERE d.TAG = 'MIGRATED_OPENING'

  UNION ALL
  -- 9_TOTAL  C: physical cash tendered by EXTERNAL customers -------------------
  SELECT '9_TOTAL', 'C', 'CASH_TENDER_RECEIPTS',
         'Cash tendered by customers (ORCT."CashSum"), external only',
         'DIFFERENT POPULATION - cash collected against ordinary credit sales. '
         || 'Do not add to A.',
         0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0,
         IFNULL(COUNT(*),0), IFNULL(SUM(t.CASH),0), 0.0, 0.0
  FROM tender t WHERE t.PARTY_CLASS = 'EXTERNAL'

  UNION ALL
  -- 9_TOTAL  D: the group/branch cash slice, flagged and quantified (T8) -------
  SELECT '9_TOTAL', 'D', 'CASH_TENDER_GROUP',
         'Cash tendered by JIVO group / branch cards',
         'NOT TRADE - excluded from C and from 6_TENDER_MONTH; shown so it is '
         || 'never silently folded into a cash figure.',
         0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0,
         IFNULL(COUNT(*),0), IFNULL(SUM(t.CASH),0), 0.0, 0.0
  FROM tender t WHERE t.PARTY_CLASS = 'GROUP'
) X
ORDER BY X.SECTION, X.SORT_KEY
