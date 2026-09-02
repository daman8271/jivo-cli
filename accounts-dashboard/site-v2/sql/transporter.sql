-- transporter.sql  --  WHO MOVES OUR GOODS, AND WHAT WE PAY THEM
--
-- The standard SAP shipping table OSHP is EMPTY (0 rows) in all three books.
-- JIVO records transport in USER-DEFINED FIELDS on the A/R INVOICE ({{SCHEMA}}.OINV),
-- which is the real dispatch document here -- deliveries (ODLN) are barely used
-- (Mart 0 and Bev 0 of their delivery notes carry a transporter name).
-- The payment side is {{SCHEMA}}.OPCH / ORPC against vendors in the OCRG supplier
-- group named TRANSPORTER (code 102 in all three books, ~96 cards each).
--
-- ONE ROW PER (SCOPE, GRP_KEY).  Seven stacked scopes in one bounded result:
--   SCOPE = 'TOTAL'          1 row   -- the company headline
--   SCOPE = 'FIELD'          11      -- per UDF: where the data lives, and how full
--   SCOPE = 'NAMECLASS'      <=4     -- THIRD_PARTY / OWN_OR_SELF / UNUSABLE / UNNAMED
--   SCOPE = 'PARTY'          <=3     -- EXTERNAL / BRANCH / INTERCOMPANY (never merged)
--   SCOPE = 'MONTH'          <=36    -- dispatch + freight by month
--   SCOPE = 'TRANSPORTER'    <=40    -- top third-party transporters by dispatch value
--   SCOPE = 'FREIGHT_VENDOR' <=25    -- top freight vendors by A/P spend
-- Expected size: ~80-110 rows per company (Oil 107, Mart 81, Bev 106 at 2026-08-21).
-- Hard-capped at 250 rows.
--
-- EXACT COLUMN LIST (21):
--   SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY,
--   DISP_DOCS, DISP_VAL_L, EXT_DISP_DOCS, EXT_DISP_VAL_L,
--   NAMED_PCT, LR_PCT, VEH_PCT, DRIVER_PCT,
--   FILLED, FILL_PCT, VARIANTS,
--   VENDOR_CODE, VENDOR_NAME, FRT_DOCS, FRT_SPEND_L, FRT_PCT_OF_DISP,
--   NOTE
-- FILLED is context-dependent: on FIELD rows it is how many documents carry that
-- UDF; on TRANSPORTER rows it is how many distinct squashed keys the family merged.
-- MONEY UNIT: every amount column ends _L and is INR LAKHS (rupees / 100000).
--   DISP_VAL_L / EXT_DISP_VAL_L = dispatch value NET OF GST ("DocTotal"-"VatSum").
--   FRT_SPEND_L = freight A/P net of GST, OPCH minus ORPC credit notes.
--   *_PCT columns are percentages (0-100), not money.
--
-- TRAPS FOUND AND HOW THEY ARE HANDLED (full write-up in notes/transporter.md):
--  1. "U_LRNUmber" IS NOT THE LR NUMBER.  Its SAP caption (CUFD."Descr") is
--     "Bill Of Entry No." -- a customs/import field.  It is filled on 39 of the
--     19309 live Oil dispatches (0.2%) and 1 of Mart's 25109, and the column does
--     not exist at all in Beverages.  The real lorry receipt is the BILTY:
--     "U_BilltyNumber" (Oil 9385 = 48.6%, Mart 959 = 3.8%) and "U_BiltyNumber"
--     (Bev 4486 = 84.4%).  LR_PCT is built on the bilty, never on U_LRNUmber.
--  2. THE UDF NAMES DIFFER BETWEEN BOOKS, so a single static statement cannot name
--     them directly -- HANA fails at compile time on a column the book does not have:
--         Oil / Mart :  "U_BilltyNumber"  "U_VehicleNoM"
--         Beverages  :  "U_BiltyNumber"   "U_VechileNom"   (both re-spelled)
--     Handled by the UDFX shim below: three branches, each naming only the columns
--     that exist in ITS OWN schema, each gated on a constant predicate
--     '{{SCHEMA}}' = '<that schema>'.  All three compile; HANA prunes the two
--     constant-false branches, so exactly one book is ever read.  This is the ONLY
--     place a schema is named literally -- every other reference is {{SCHEMA}}.
--     A fourth/renamed company book would return no LR or vehicle rows (LR_PCT and
--     VEH_PCT come back 0 with NOTE 'UDF SHIM MISS'), never an error.
--  3. "U_TransporterInvoice" is captioned "Gate Pass No.", NOT a transporter invoice
--     number, and is filled on 1-2 documents per book.  It is reported in the FIELD
--     scope for completeness and used for nothing else.  Freight cost is NOT on the
--     dispatch document -- "U_BiltAmt" ("Bilty Amount") is filled on 4 of 31027 Oil
--     invoices and 0 elsewhere -- so cost has to come from A/P, which is why the
--     vendor tie below is the only route to spend-per-transporter.
--  4. Oil has 11078 live invoices dated EXACTLY 2024-09-30 -- SAP go-live migrated
--     opening balances, 36% of the book, none carrying a transporter.  Left in, they
--     dilute every coverage percentage by about a third.  That date is excluded from
--     dispatches and from freight spend in all three books.
--  5. "U_TransporterName" IS FREE TEXT.  CUFD."EditType" is blank and UFD1 holds
--     ZERO valid values for it in all three books, so nothing is validated on entry.
--     Oil holds 234 raw spellings that collapse to 168 once case and punctuation are
--     normalised.  TN_KEY strips case, spaces and punctuation (including the LIKE
--     wildcards % and _, so a stray one cannot widen the vendor match); VARIANTS
--     reports how many raw spellings fed each row, which is the number that decides
--     whether the dashboard needs a hand-written normalisation map.
--  6. Not every name is a transporter.  'JIVO VEHICLE' (848 Oil docs), 'SELF',
--     'SELF PICKUP' are own-fleet or customer-collected -- no freight is bought --
--     and 'NA'/'NIL'/'-' are keystrokes, not carriers.  Any name ENDING in VEHICLE
--     / VEHICAL ('AMAZON VEHICLE', 'BARU SAHIB VEHICLE') is the counterparty's own
--     truck, not a carrier we buy from.  NAMECLASS splits them out and
--     the TRANSPORTER scope counts THIRD_PARTY only, so freight-per-transporter is
--     never divided by dispatches nobody was paid for.
--  7. Branch and intercompany dispatches are NOT trade.  PARTY scope separates them
--     and every scope carries both DISP_VAL_L (all) and EXT_DISP_VAL_L (external
--     only) so neither is silently dropped nor silently included.  The group test
--     alone is not enough at JIVO, so the card NAME is checked for JIVO as well.
--  8. THE FREIGHT VENDOR IS OFTEN NOT IN THE TRANSPORTER GROUP.  This was the one
--     material defect found in adversarial review on 2026-08-21.  R K TANKER SERVICE
--     (Oil VENDA000671) bills 945 L of "TPT FREIGHT FROM SHEMLA TO SONIPAT" and is
--     filed under supplier group 110 PURCHASE OIL.  On a group-only test the whole
--     945 L disappeared -- more than the entire reported freight figure -- and the
--     dashboard printed 'NO FREIGHT VENDOR CARD MATCHED' next to R K TANKER, its
--     4th-biggest transporter.  VEND now takes a card on EITHER the supplier group
--     OR a road-carrier token in the card's own name, and each FREIGHT_VENDOR row
--     says which.  Effect: Oil freight 520.09 L -> 1802.07 L, Mart 289.49 -> 323.84,
--     Bev 168.47 -> 203.04.  Read the group-only figure as roughly a THIRD of the
--     truth in the Oil book.
--  9. Vendor matching is many-to-many by nature ('OM LOGISTICS', 'OM LOGISTICS LTD'
--     and 'OM LOGISTICS LTD.' are all one vendor card).  Matching is a two-sided
--     prefix test on the squashed key with a 6-character floor, reduced to one
--     family per vendor card (ROW_NUMBER PARTITION BY CARD_CODE), so no vendor's
--     spend is counted under two transporters.  Freight belonging to vendors that
--     matched no dispatch name is NOT discarded: it is reported as FREIGHT_VENDOR
--     rows and in the TOTAL row's NOTE.  A transporter whose vendor card exists but
--     carries no A/P at all reads 'NEVER BILLED', which is a different fact from
--     'no card matched' -- do not conflate them.
-- 10. Amounts are cancellation-filtered ("CANCELED" = 'N' on OINV/OPCH/ORPC/ODLN/OPDN).
--     Verified: the column takes 'N', 'Y' and 'C' -- 'Y' is the cancelled document
--     and 'C' the cancelling one -- so = 'N' correctly drops both halves of a pair.
--     "DocStatus" is deliberately NOT used -- at JIVO it is unreliable, documents are
--     settled by journal entry and stay open long after the money moved.  Nothing
--     here is ageing- or open-item-shaped, so ORCT/OVPM "OpenBal" never enters and
--     cannot be double-subtracted.
-- 11. KNOWN AND LEFT ALONE, quantified rather than fixed (see notes/transporter.md):
--     (a) service A/R invoices ("DocType" = 'S') are counted as dispatches -- Oil
--         556.04 L / 0.6%, Mart 1567.49 L / 4.9%, Bev nil.  NONE of them carries a
--         transporter name, so they only dilute; they never invent a carrier.
--     (b) DISP_VAL_L is invoices only.  Sales returns (ORIN) are NOT netted off --
--         a return does not un-dispatch a truck -- so this is NOT turnover.
--     (c) freight accrued straight to G/L by journal entry, with no A/P invoice,
--         is invisible here.  Oil account 5670001 carries ~1077 L of debits that
--         reach it that way.
WITH
UDFX AS (
  SELECT "DocEntry" AS DOC_ENTRY,
         CASE WHEN IFNULL(TRIM("U_BilltyNumber"),'') <> '' THEN 1 ELSE 0 END AS HAS_LR,
         CASE WHEN IFNULL(TRIM("U_VehicleNoM"),'')   <> '' THEN 1 ELSE 0 END AS HAS_VEH,
         CASE WHEN IFNULL(TRIM("U_LRNUmber"),'')     <> '' THEN 1 ELSE 0 END AS HAS_BOE,
         'U_BilltyNumber / U_VehicleNoM' AS UDF_SPELLING,
         'U_LRNUmber' AS BOE_COL
  FROM JIVO_OIL_HANADB.OINV        WHERE '{{SCHEMA}}' = 'JIVO_OIL_HANADB'
  UNION ALL
  SELECT "DocEntry",
         CASE WHEN IFNULL(TRIM("U_BilltyNumber"),'') <> '' THEN 1 ELSE 0 END,
         CASE WHEN IFNULL(TRIM("U_VehicleNoM"),'')   <> '' THEN 1 ELSE 0 END,
         CASE WHEN IFNULL(TRIM("U_LRNUmber"),'')     <> '' THEN 1 ELSE 0 END,
         'U_BilltyNumber / U_VehicleNoM', 'U_LRNUmber'
  FROM JIVO_MART_HANADB.OINV       WHERE '{{SCHEMA}}' = 'JIVO_MART_HANADB'
  UNION ALL
  SELECT "DocEntry",
         CASE WHEN IFNULL(TRIM("U_BiltyNumber"),'')  <> '' THEN 1 ELSE 0 END,
         CASE WHEN IFNULL(TRIM("U_VechileNom"),'')   <> '' THEN 1 ELSE 0 END,
         0,
         'U_BiltyNumber / U_VechileNom', '(no such column in this book)'
  FROM JIVO_BEVERAGES_HANADB.OINV  WHERE '{{SCHEMA}}' = 'JIVO_BEVERAGES_HANADB'
),
DISP AS (
  SELECT h."DocEntry" AS DOC_ENTRY,
         TO_VARCHAR(h."DocDate",'YYYY-MM') AS YM,
         TRIM(IFNULL(h."U_TransporterName",'')) AS TN_RAW,
         REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
           UPPER(TRIM(IFNULL(h."U_TransporterName",''))),
           ' ',''),'.',''),',',''),'-',''),'&',''),'(',''),')',''),'/',''),'''',''),'_',''),'%','') AS TN_KEY,
         CASE WHEN IFNULL(TRIM(h."U_DriverName"),'')          <> '' THEN 1 ELSE 0 END AS HAS_DRV,
         CAST(h."DocTotal" AS DOUBLE) - CAST(h."VatSum" AS DOUBLE) AS NET_VAL,
         CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%BRANCH%'            THEN 'BRANCH'
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE '%JIVO%'     THEN 'INTERCOMPANY'
              ELSE 'EXTERNAL' END AS PARTY_CLASS
  FROM {{SCHEMA}}.OINV h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode" AND g."GroupType" = c."CardType"
  WHERE h."CANCELED" = 'N'
    AND h."DocDate" <= DATE'{{ASOF}}'
    AND h."DocDate" <> DATE'2024-09-30'
),
D AS (
  SELECT d.*, IFNULL(x.HAS_LR,0) AS HAS_LR, IFNULL(x.HAS_VEH,0) AS HAS_VEH,
         IFNULL(x.HAS_BOE,0) AS HAS_BOE,
         CASE WHEN d.TN_KEY = '' AND d.TN_RAW = ''                    THEN 'UNNAMED'
              WHEN d.TN_KEY = ''                                       THEN 'UNUSABLE'
              WHEN d.TN_KEY IN ('NA','N','NIL','NILL','NONE','XX','X','0','00','ZZ','TEST')
                                                                     THEN 'UNUSABLE'
              WHEN d.TN_KEY LIKE 'SELF%'     OR d.TN_KEY LIKE 'JIVO%'
                OR d.TN_KEY LIKE 'BYHAND%'   OR d.TN_KEY LIKE 'CUSTOMERPICK%'
                OR d.TN_KEY LIKE '%SELFPICK%' OR d.TN_KEY LIKE '%OWNVEHIC%'
                OR d.TN_KEY LIKE '%VEHICLE'  OR d.TN_KEY LIKE '%VEHICAL'
                                                                     THEN 'OWN_OR_SELF'
              ELSE 'THIRD_PARTY' END AS NAME_CLASS,
         CASE WHEN d.PARTY_CLASS = 'EXTERNAL' THEN 1 ELSE 0 END AS IS_EXT
  FROM DISP d
  LEFT JOIN UDFX x ON x.DOC_ENTRY = d.DOC_ENTRY
),
VEND AS (
  -- THE FREIGHT-VENDOR UNIVERSE.  A supplier-GROUP test alone is not enough here.
  -- The single biggest carrier in the Oil book -- R K TANKER SERVICE VENDA000671,
  -- 945 L of A/P, every line reading "TPT FREIGHT FROM SHEMLA TO SONIPAT" -- is
  -- filed under supplier group 110 PURCHASE OIL, not 102 TRANSPORTER.  On the group
  -- test alone it vanished, and the dashboard then told the operator "NO FREIGHT
  -- VENDOR CARD MATCHED" for R K TANKER, its 4th-largest transporter by dispatch
  -- value.  So a supplier card also qualifies when its OWN NAME carries a
  -- road-carrier token.  Verified 2026-08-21: the token list below produced ZERO
  -- false positives across all three books.  IN_GRP records which test let the card
  -- in, and every FREIGHT_VENDOR row says so in its NOTE, so the widening is
  -- auditable rather than silent.
  -- DELIBERATELY NOT TOKENS: SHIPPING / EXPRESS / FORWARD / TEMPO / LOGIS.  Those
  -- pull in ocean lines, container agents and clearing-and-forwarding houses
  -- (COSCO, MSC, EVERGREEN, TRANSGLOBE SHIPTRANS...) -- import freight on goods
  -- BOUGHT, a different cost family from road transport of goods DISPATCHED -- plus
  -- an outright false positive on %TRANS% ("KAMAL TRANSFORMERS").  That excluded
  -- remainder is Oil 192.58 L, Mart 0, Bev 2.08 L; it is named in notes/transporter.md.
  SELECT CARD_CODE, CARD_NAME, V_KEY, GRP_NAME, IN_GRP
  FROM (
    SELECT c."CardCode" AS CARD_CODE, c."CardName" AS CARD_NAME,
           IFNULL(g."GroupName",'(no supplier group)') AS GRP_NAME,
           REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
             UPPER(TRIM(c."CardName")),
             ' ',''),'.',''),',',''),'-',''),'&',''),'(',''),')',''),'/',''),'''',''),'_',''),'%','') AS V_KEY,
           CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%TRANSPORT%'
                  OR UPPER(IFNULL(g."GroupName",'')) LIKE '%FREIGHT%'
                  OR UPPER(IFNULL(g."GroupName",'')) LIKE '%LOGIST%'
                  OR UPPER(IFNULL(g."GroupName",'')) LIKE '%COURIER%'
                  OR UPPER(IFNULL(g."GroupName",'')) LIKE '%CARRIAGE%'
                THEN 1 ELSE 0 END AS IN_GRP
    FROM {{SCHEMA}}.OCRD c
    LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode" AND g."GroupType" = 'S'
    WHERE c."CardType" = 'S'
      AND UPPER(IFNULL(c."CardName",'')) NOT LIKE '%JIVO%'
  )
  WHERE IN_GRP = 1
     OR V_KEY LIKE '%TRANSPORT%'   OR V_KEY LIKE '%LOGISTIC%' OR V_KEY LIKE '%CARRIER%'
     OR V_KEY LIKE '%CARGO%'       OR V_KEY LIKE '%ROADLINE%' OR V_KEY LIKE '%FREIGHT%'
     OR V_KEY LIKE '%COURIER%'     OR V_KEY LIKE '%TANKER%'   OR V_KEY LIKE '%CARTAGE%'
     OR V_KEY LIKE '%ROADWAY%'     OR V_KEY LIKE '%SUPPLYCHAIN%'
     OR V_KEY LIKE '%PACKERSMOVER%'
),
FRTDOC AS (
  SELECT p."CardCode" AS CARD_CODE, TO_VARCHAR(p."DocDate",'YYYY-MM') AS YM,
         1 AS DOCS, CAST(p."DocTotal" AS DOUBLE) - CAST(p."VatSum" AS DOUBLE) AS AMT
  FROM {{SCHEMA}}.OPCH p
  WHERE p."CANCELED" = 'N' AND p."DocDate" <= DATE'{{ASOF}}' AND p."DocDate" <> DATE'2024-09-30'
    AND p."CardCode" IN (SELECT CARD_CODE FROM VEND)
  UNION ALL
  SELECT r."CardCode", TO_VARCHAR(r."DocDate",'YYYY-MM'),
         0, -(CAST(r."DocTotal" AS DOUBLE) - CAST(r."VatSum" AS DOUBLE))
  FROM {{SCHEMA}}.ORPC r
  WHERE r."CANCELED" = 'N' AND r."DocDate" <= DATE'{{ASOF}}' AND r."DocDate" <> DATE'2024-09-30'
    AND r."CardCode" IN (SELECT CARD_CODE FROM VEND)
),
FRTV AS (
  SELECT CARD_CODE, SUM(DOCS) AS FDOCS, SUM(AMT) AS FAMT
  FROM FRTDOC GROUP BY CARD_CODE
),
TNAGG AS (
  SELECT TN_KEY, COUNT(*) AS DOCS, SUM(NET_VAL) AS VAL
  FROM D WHERE NAME_CLASS = 'THIRD_PARTY' GROUP BY TN_KEY
),
FAMX AS (
  SELECT t.TN_KEY, p.TN_KEY AS FAM_KEY,
         ROW_NUMBER() OVER (PARTITION BY t.TN_KEY ORDER BY LENGTH(p.TN_KEY), p.TN_KEY) AS RN
  FROM TNAGG t
  JOIN TNAGG p ON LENGTH(p.TN_KEY) >= 6 AND LENGTH(p.TN_KEY) <= LENGTH(t.TN_KEY)
              AND t.TN_KEY LIKE p.TN_KEY || '%'
),
FAM AS (
  SELECT t.TN_KEY, IFNULL(f.FAM_KEY, t.TN_KEY) AS FAM_KEY
  FROM TNAGG t LEFT JOIN FAMX f ON f.TN_KEY = t.TN_KEY AND f.RN = 1
),
FAMAGG AS (
  SELECT m.FAM_KEY,
         MIN(d.TN_RAW) AS TN_SAMPLE,
         COUNT(DISTINCT d.TN_RAW) AS VARIANTS,
         COUNT(DISTINCT d.TN_KEY) AS KEYS_IN_FAM,
         COUNT(*) AS DOCS, SUM(d.NET_VAL) AS VAL,
         SUM(d.IS_EXT) AS EXT_DOCS, SUM(d.IS_EXT * d.NET_VAL) AS EXT_VAL,
         SUM(d.HAS_LR) AS LRN, SUM(d.HAS_VEH) AS VEHN, SUM(d.HAS_DRV) AS DRVN
  FROM D d JOIN FAM m ON m.TN_KEY = d.TN_KEY
  WHERE d.NAME_CLASS = 'THIRD_PARTY' GROUP BY m.FAM_KEY
),
FAMSPELL AS (
  SELECT FAM_KEY, SUBSTRING(STRING_AGG(TN_RAW, ' | ' ORDER BY TN_RAW), 1, 160) AS SPELLINGS
  FROM (SELECT DISTINCT m.FAM_KEY, d.TN_RAW
        FROM D d JOIN FAM m ON m.TN_KEY = d.TN_KEY
        WHERE d.NAME_CLASS = 'THIRD_PARTY')
  GROUP BY FAM_KEY
),
VMAP AS (
  SELECT CARD_CODE, CARD_NAME, FAM_KEY FROM (
    SELECT v.CARD_CODE, v.CARD_NAME, f.FAM_KEY,
           ROW_NUMBER() OVER (PARTITION BY v.CARD_CODE
                              ORDER BY LENGTH(f.FAM_KEY) DESC, f.VAL DESC, f.FAM_KEY) AS RN
    FROM VEND v
    JOIN FAMAGG f ON LENGTH(f.FAM_KEY) >= 6 AND LENGTH(v.V_KEY) >= 6
                 AND (v.V_KEY LIKE f.FAM_KEY || '%' OR f.FAM_KEY LIKE v.V_KEY || '%')
  ) WHERE RN = 1
),
FAMFRT AS (
  SELECT FAM_KEY, COUNT(*) AS NVEND, SUM(FDOCS) AS FDOCS, SUM(FAMT) AS FAMT,
         MAX(CASE WHEN RN = 1 THEN CARD_CODE END) AS TOP_CODE,
         MAX(CASE WHEN RN = 1 THEN CARD_NAME END) AS TOP_NAME
  FROM (SELECT m.FAM_KEY, m.CARD_CODE, m.CARD_NAME,
               IFNULL(fv.FDOCS,0) AS FDOCS, IFNULL(fv.FAMT,0) AS FAMT,
               ROW_NUMBER() OVER (PARTITION BY m.FAM_KEY
                                  ORDER BY IFNULL(fv.FAMT,0) DESC, m.CARD_CODE) AS RN
        FROM VMAP m LEFT JOIN FRTV fv ON fv.CARD_CODE = m.CARD_CODE)
  GROUP BY FAM_KEY
),
FLD AS (
  SELECT f."TableID" AS TBL, f."AliasID" AS ALIASID, f."Descr" AS CAPTION, f."TypeID" AS FTYPE,
         (SELECT COUNT(*) FROM {{SCHEMA}}.UFD1 u
          WHERE u."TableID" = f."TableID" AND u."FieldID" = f."FieldID") AS NVALID
  FROM {{SCHEMA}}.CUFD f WHERE f."TableID" IN ('OINV','ODLN','OPDN')
),
FIELDSTAT AS (
  SELECT 'OINV.U_TransporterName' AS K, 'OINV' AS TBL, 'TransporterName' AS AL,
         COUNT(*) AS TOTN, SUM(CASE WHEN IFNULL(TRIM("U_TransporterName"),'')<>'' THEN 1 ELSE 0 END) AS FILLN
  FROM {{SCHEMA}}.OINV WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}' AND "DocDate" <> DATE'2024-09-30'
  UNION ALL
  SELECT 'OINV.U_TransporterInvoice','OINV','TransporterInvoice', COUNT(*),
         SUM(CASE WHEN IFNULL(TRIM("U_TransporterInvoice"),'')<>'' THEN 1 ELSE 0 END)
  FROM {{SCHEMA}}.OINV WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}' AND "DocDate" <> DATE'2024-09-30'
  UNION ALL
  SELECT 'OINV.U_DriverName','OINV','DriverName', COUNT(*),
         SUM(CASE WHEN IFNULL(TRIM("U_DriverName"),'')<>'' THEN 1 ELSE 0 END)
  FROM {{SCHEMA}}.OINV WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}' AND "DocDate" <> DATE'2024-09-30'
  UNION ALL
  SELECT 'OINV.U_BiltyDate','OINV','BiltyDate', COUNT(*),
         SUM(CASE WHEN "U_BiltyDate" IS NOT NULL THEN 1 ELSE 0 END)
  FROM {{SCHEMA}}.OINV WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}' AND "DocDate" <> DATE'2024-09-30'
  UNION ALL
  SELECT 'OINV.U_BiltAmt','OINV','BiltAmt', COUNT(*),
         SUM(CASE WHEN CAST(IFNULL("U_BiltAmt",0) AS DOUBLE) <> 0 THEN 1 ELSE 0 END)
  FROM {{SCHEMA}}.OINV WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}' AND "DocDate" <> DATE'2024-09-30'
  UNION ALL
  SELECT 'OINV.U_Ship_From','OINV','Ship_From', COUNT(*),
         SUM(CASE WHEN IFNULL(TRIM("U_Ship_From"),'')<>'' THEN 1 ELSE 0 END)
  FROM {{SCHEMA}}.OINV WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}' AND "DocDate" <> DATE'2024-09-30'
  UNION ALL
  SELECT 'ODLN.U_TransporterName','ODLN','TransporterName', COUNT(*),
         SUM(CASE WHEN IFNULL(TRIM("U_TransporterName"),'')<>'' THEN 1 ELSE 0 END)
  FROM {{SCHEMA}}.ODLN WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}'
  UNION ALL
  SELECT 'OPDN.U_TransporterName','OPDN','TransporterName', COUNT(*),
         SUM(CASE WHEN IFNULL(TRIM("U_TransporterName"),'')<>'' THEN 1 ELSE 0 END)
  FROM {{SCHEMA}}.OPDN WHERE "CANCELED"='N' AND "DocDate" <= DATE'{{ASOF}}' AND "DocDate" <> DATE'2024-09-30'
),
BASE AS (
  SELECT COUNT(*) AS DOCS, SUM(NET_VAL) AS VAL,
         SUM(IS_EXT) AS EXT_DOCS, SUM(IS_EXT*NET_VAL) AS EXT_VAL,
         SUM(CASE WHEN NAME_CLASS='THIRD_PARTY' THEN 1 ELSE 0 END) AS TP_DOCS,
         SUM(HAS_LR) AS LRN, SUM(HAS_VEH) AS VEHN, SUM(HAS_DRV) AS DRVN, SUM(HAS_BOE) AS BOEN,
         COUNT(DISTINCT CASE WHEN TN_RAW<>'' THEN TN_RAW END) AS RAWVAR,
         COUNT(DISTINCT CASE WHEN NAME_CLASS='THIRD_PARTY' THEN TN_RAW END) AS TPVAR
  FROM D
),
FRTTOT AS (
  -- FRTV only ever holds cards that are in VEND (FRTDOC filters on it), so this
  -- JOIN cannot drop a vendor; it is here purely to read IN_GRP back.
  SELECT SUM(f.FDOCS) AS FDOCS, SUM(f.FAMT) AS FAMT,
         SUM(CASE WHEN f.CARD_CODE IN (SELECT CARD_CODE FROM VMAP) THEN f.FAMT ELSE 0 END) AS FAMT_MATCHED,
         SUM(CASE WHEN v.IN_GRP = 0 THEN f.FAMT ELSE 0 END) AS FAMT_OUTGRP,
         COUNT(CASE WHEN v.IN_GRP = 0 AND f.FAMT <> 0 THEN 1 END) AS NV_OUTGRP
  FROM FRTV f JOIN VEND v ON v.CARD_CODE = f.CARD_CODE
),
ROWS_ALL AS (
  SELECT 'TOTAL' AS SCOPE, 'ALL' AS GRP_KEY, 'Company total' AS GRP_LABEL, 1 AS SORT_KEY,
         b.DOCS AS DISP_DOCS, b.VAL AS DISP_VAL, b.EXT_DOCS AS EXT_DISP_DOCS, b.EXT_VAL AS EXT_DISP_VAL,
         100.0*b.TP_DOCS/NULLIF(b.DOCS,0) AS NAMED_PCT,
         100.0*b.LRN/NULLIF(b.DOCS,0)  AS LR_PCT,
         100.0*b.VEHN/NULLIF(b.DOCS,0) AS VEH_PCT,
         100.0*b.DRVN/NULLIF(b.DOCS,0) AS DRIVER_PCT,
         CAST(NULL AS BIGINT) AS FILLED, CAST(NULL AS DOUBLE) AS FILL_PCT,
         b.RAWVAR AS VARIANTS,
         CAST(NULL AS NVARCHAR(50)) AS VENDOR_CODE, CAST(NULL AS NVARCHAR(200)) AS VENDOR_NAME,
         t.FDOCS AS FRT_DOCS, t.FAMT AS FRT_SPEND,
         100.0*t.FAMT/NULLIF(b.VAL,0) AS FRT_PCT_OF_DISP,
         -- Every piece is IFNULL-guarded: in HANA one NULL blanks the whole
         -- concatenation, and an empty book (no dispatches, no freight) must still
         -- render a readable TOTAL row rather than a NULL note.
         'dispatch doc = OINV, ex-cancelled, ex 2024-09-30 migration. DISP_VAL_L is ALL '
           || 'dispatches incl. branch + intercompany -- EXT_DISP_VAL_L is external-only, '
           || 'and PARTY splits them. Freight A/P '
           || IFNULL(TO_VARCHAR(ROUND(100.0*IFNULL(t.FAMT_MATCHED,0)/NULLIF(t.FAMT,0),1)),'n/a')
           || '% tied to a named transporter; '
           || IFNULL(TO_VARCHAR(t.NV_OUTGRP),'0') || ' carrier(s) worth '
           || IFNULL(TO_VARCHAR(ROUND(IFNULL(t.FAMT_OUTGRP,0)/100000,2)),'0') || ' L sit OUTSIDE the '
           || 'transporter supplier group and were pulled in by name. Name spread '
           || IFNULL(TO_VARCHAR(b.TPVAR),'0') || ' third-party spellings ('
           || IFNULL(TO_VARCHAR(b.RAWVAR),'0') || ' incl. own-fleet/placeholder) -> '
           || TO_VARCHAR((SELECT COUNT(*) FROM TNAGG))  || ' keys -> '
           || TO_VARCHAR((SELECT COUNT(*) FROM FAMAGG)) || ' families; LR field = '
           || IFNULL((SELECT MIN(UDF_SPELLING) FROM UDFX),'UDF SHIM MISS') AS NOTE
  FROM BASE b CROSS JOIN FRTTOT t
  UNION ALL
  SELECT 'FIELD', f.K, IFNULL(d.CAPTION, '(not in CUFD)'), 2,
         f.TOTN, CAST(NULL AS DOUBLE), CAST(NULL AS BIGINT), CAST(NULL AS DOUBLE),
         CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE),
         f.FILLN, 100.0*f.FILLN/NULLIF(f.TOTN,0), CAST(NULL AS BIGINT),
         NULL, NULL, CAST(NULL AS BIGINT), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE),
         CASE WHEN IFNULL(d.NVALID,0) > 0     THEN 'controlled list, ' || TO_VARCHAR(d.NVALID) || ' valid values'
              WHEN d.CAPTION IS NULL           THEN 'column present, no CUFD definition in this book'
              WHEN d.FTYPE IN ('A','M')        THEN 'FREE TEXT - no valid-value list in UFD1'
              ELSE 'typed field (' || d.FTYPE || '), not a list' END
  FROM FIELDSTAT f LEFT JOIN FLD d ON d.TBL = f.TBL AND d.ALIASID = f.AL
  UNION ALL
  SELECT 'FIELD', 'OINV.LR_NUMBER (bilty)', 'Bilty / lorry receipt number', 2,
         (SELECT DOCS FROM BASE), NULL, NULL, NULL, NULL, NULL, NULL, NULL,
         (SELECT LRN FROM BASE), 100.0*(SELECT LRN FROM BASE)/NULLIF((SELECT DOCS FROM BASE),0), NULL,
         NULL, NULL, NULL, NULL, NULL,
         'per-book column: ' || IFNULL((SELECT MIN(UDF_SPELLING) FROM UDFX),'UDF SHIM MISS')
           || ' -- NOT U_LRNUmber, which is captioned Bill Of Entry No.'
  FROM DUMMY
  UNION ALL
  SELECT 'FIELD', 'OINV.U_LRNUmber', 'Bill Of Entry No. (NOT a lorry receipt)', 2,
         (SELECT DOCS FROM BASE), NULL, NULL, NULL, NULL, NULL, NULL, NULL,
         (SELECT BOEN FROM BASE), 100.0*(SELECT BOEN FROM BASE)/NULLIF((SELECT DOCS FROM BASE),0), NULL,
         NULL, NULL, NULL, NULL, NULL,
         'this book: ' || IFNULL((SELECT MIN(BOE_COL) FROM UDFX),'UDF SHIM MISS')
           || ' -- a customs field, near-empty; the LR lives in the bilty column above'
  FROM DUMMY
  UNION ALL
  SELECT 'FIELD', 'OINV.VEHICLE_NO', 'Vehicle number (e-way bill Part B)', 2,
         (SELECT DOCS FROM BASE), NULL, NULL, NULL, NULL, NULL, NULL, NULL,
         (SELECT VEHN FROM BASE), 100.0*(SELECT VEHN FROM BASE)/NULLIF((SELECT DOCS FROM BASE),0), NULL,
         NULL, NULL, NULL, NULL, NULL,
         'per-book column: ' || IFNULL((SELECT MIN(UDF_SPELLING) FROM UDFX),'UDF SHIM MISS')
  FROM DUMMY
  UNION ALL
  SELECT 'NAMECLASS', NAME_CLASS,
         CASE NAME_CLASS WHEN 'THIRD_PARTY' THEN 'Named third-party transporter'
                         WHEN 'OWN_OR_SELF' THEN 'Own fleet / collected by customer'
                         WHEN 'UNUSABLE'    THEN 'Placeholder text (NA, NIL, X)'
                         ELSE 'No transporter recorded' END, 3,
         COUNT(*), SUM(NET_VAL), SUM(IS_EXT), SUM(IS_EXT*NET_VAL),
         NULL,
         100.0*SUM(HAS_LR)/NULLIF(COUNT(*),0), 100.0*SUM(HAS_VEH)/NULLIF(COUNT(*),0),
         100.0*SUM(HAS_DRV)/NULLIF(COUNT(*),0),
         NULL, NULL, COUNT(DISTINCT CASE WHEN TN_RAW<>'' THEN TN_RAW END),
         NULL, NULL, NULL, NULL, NULL, NULL
  FROM D GROUP BY NAME_CLASS
  UNION ALL
  SELECT 'PARTY', PARTY_CLASS,
         CASE PARTY_CLASS WHEN 'EXTERNAL' THEN 'External customers (real trade)'
                          WHEN 'BRANCH'   THEN 'Own branch GST registrations'
                          ELSE 'JIVO group company' END, 4,
         COUNT(*), SUM(NET_VAL), SUM(IS_EXT), SUM(IS_EXT*NET_VAL),
         100.0*SUM(CASE WHEN NAME_CLASS='THIRD_PARTY' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),
         100.0*SUM(HAS_LR)/NULLIF(COUNT(*),0), 100.0*SUM(HAS_VEH)/NULLIF(COUNT(*),0),
         100.0*SUM(HAS_DRV)/NULLIF(COUNT(*),0),
         NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
  FROM D GROUP BY PARTY_CLASS
  UNION ALL
  SELECT 'MONTH', d.YM, 'Dispatches in ' || d.YM, 5,
         COUNT(*), SUM(d.NET_VAL), SUM(d.IS_EXT), SUM(d.IS_EXT*d.NET_VAL),
         100.0*SUM(CASE WHEN d.NAME_CLASS='THIRD_PARTY' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),
         100.0*SUM(d.HAS_LR)/NULLIF(COUNT(*),0), 100.0*SUM(d.HAS_VEH)/NULLIF(COUNT(*),0),
         100.0*SUM(d.HAS_DRV)/NULLIF(COUNT(*),0),
         NULL, NULL, COUNT(DISTINCT CASE WHEN d.TN_RAW<>'' THEN d.TN_RAW END),
         NULL, NULL,
         (SELECT SUM(f.DOCS) FROM FRTDOC f WHERE f.YM = d.YM),
         (SELECT SUM(f.AMT) FROM FRTDOC f WHERE f.YM = d.YM),
         100.0*(SELECT SUM(f.AMT) FROM FRTDOC f WHERE f.YM = d.YM)/NULLIF(SUM(d.NET_VAL),0),
         NULL
  FROM D d GROUP BY d.YM
  UNION ALL
  SELECT 'TRANSPORTER', r.FAM_KEY, r.TN_SAMPLE, 6,
         r.DOCS, r.VAL, r.EXT_DOCS, r.EXT_VAL,
         NULL,
         100.0*r.LRN/NULLIF(r.DOCS,0), 100.0*r.VEHN/NULLIF(r.DOCS,0), 100.0*r.DRVN/NULLIF(r.DOCS,0),
         r.KEYS_IN_FAM, NULL, r.VARIANTS,
         r.TOP_CODE, r.TOP_NAME, r.FDOCS, r.FAMT,
         100.0*r.FAMT/NULLIF(r.VAL,0),
         CASE WHEN r.TOP_CODE IS NULL   THEN 'NO FREIGHT VENDOR CARD MATCHED; spellings: '
              WHEN IFNULL(r.FAMT,0) = 0  THEN 'vendor card exists but was NEVER BILLED; spellings: '
              WHEN r.NVEND > 1           THEN TO_VARCHAR(r.NVEND) || ' vendor cards merged here; spellings: '
              ELSE 'spellings: ' END || r.SPELLINGS
  FROM (SELECT f.*, sp.SPELLINGS, ff.NVEND, ff.FDOCS, ff.FAMT, ff.TOP_CODE, ff.TOP_NAME,
               ROW_NUMBER() OVER (ORDER BY f.VAL DESC, f.FAM_KEY) AS RN
        FROM FAMAGG f
        LEFT JOIN FAMSPELL sp ON sp.FAM_KEY = f.FAM_KEY
        LEFT JOIN FAMFRT  ff ON ff.FAM_KEY = f.FAM_KEY) r
  WHERE r.RN <= 40
  UNION ALL
  SELECT 'FREIGHT_VENDOR', v.CARD_CODE, v.CARD_NAME, 7,
         NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
         v.CARD_CODE, v.CARD_NAME, v.FDOCS, v.FAMT, NULL,
         CASE WHEN v.IN_GRP = 1 THEN '' ELSE
              'OUTSIDE the transporter group -- filed under "' || v.GRP_NAME
              || '", pulled in on the carrier token in its name; ' END
         || CASE WHEN v.FAM_KEY IS NULL THEN 'PAID BUT NEVER NAMED ON A DISPATCH'
                 ELSE 'ships under transporter family "' || v.FAM_KEY || '"' END
  FROM (SELECT f.CARD_CODE, ve.CARD_NAME, ve.GRP_NAME, ve.IN_GRP, f.FDOCS, f.FAMT, m.FAM_KEY,
               ROW_NUMBER() OVER (ORDER BY f.FAMT DESC, f.CARD_CODE) AS RN
        FROM FRTV f
        JOIN VEND ve ON ve.CARD_CODE = f.CARD_CODE
        LEFT JOIN VMAP m ON m.CARD_CODE = f.CARD_CODE) v
  WHERE v.RN <= 25
)
SELECT SCOPE, GRP_KEY, GRP_LABEL, SORT_KEY,
       DISP_DOCS,
       ROUND(DISP_VAL/100000,2)     AS DISP_VAL_L,
       EXT_DISP_DOCS,
       ROUND(EXT_DISP_VAL/100000,2) AS EXT_DISP_VAL_L,
       ROUND(NAMED_PCT,1)  AS NAMED_PCT,
       ROUND(LR_PCT,1)     AS LR_PCT,
       ROUND(VEH_PCT,1)    AS VEH_PCT,
       ROUND(DRIVER_PCT,1) AS DRIVER_PCT,
       FILLED,
       ROUND(FILL_PCT,1)   AS FILL_PCT,
       VARIANTS,
       VENDOR_CODE, VENDOR_NAME, FRT_DOCS,
       ROUND(FRT_SPEND/100000,2)   AS FRT_SPEND_L,
       ROUND(FRT_PCT_OF_DISP,1)    AS FRT_PCT_OF_DISP,
       NOTE
FROM ROWS_ALL
ORDER BY SORT_KEY,
         CASE WHEN SCOPE IN ('MONTH','FIELD','FREIGHT_VENDOR') THEN 0 ELSE 1 END,
         CASE WHEN SCOPE = 'MONTH' THEN GRP_KEY END,
         CASE WHEN SCOPE = 'FIELD' THEN GRP_KEY END,
         CASE WHEN SCOPE = 'FREIGHT_VENDOR' THEN -FRT_SPEND END,
         DISP_VAL DESC NULLS LAST,
         GRP_KEY
LIMIT 250
