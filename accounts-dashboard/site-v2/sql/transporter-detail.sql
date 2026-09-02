-- transporter-detail.sql  --  DISPATCH vs FREIGHT, PER TRANSPORTER PER MONTH
--
-- The companion grid to transporter.sql.  Same base, same normalisation, same
-- traps -- read that file's header first; everything it says applies here.
-- This one exists only because "value and count per transporter per month" is a
-- second grain that would blow the summary's row budget.
--
-- ONE ROW PER (TRANSPORTER FAMILY, MONTH), for the top 20 families by dispatch
-- value, plus an 'ZZ_OTHER' family that carries every remaining third-party
-- transporter so the months still foot to the company total.
-- Expected size: 20-21 families x <=24 months, minus empty cells.
--   Oil 282, Mart 44, Bev 172 rows at 2026-08-21.  Hard-capped at 800.
--
-- EXACT COLUMN LIST (13):
--   FAM_KEY, TN_SAMPLE, YM,
--   DISP_DOCS, DISP_VAL_L, EXT_DISP_VAL_L,
--   LR_PCT, VEH_PCT, VARIANTS,
--   VENDOR_NAME, FRT_DOCS, FRT_SPEND_L, FRT_PCT_OF_DISP
-- MONEY UNIT: DISP_VAL_L / EXT_DISP_VAL_L / FRT_SPEND_L are INR LAKHS.
--   *_PCT are percentages (0-100).
--
-- READING IT: FRT_PCT_OF_DISP is freight billed by that transporter's vendor
-- card(s) in that month, over the goods value they carried in that month.  It is
-- the ship-versus-pay ratio, and it is only meaningful where VENDOR_NAME is not
-- null -- a family with no matched vendor card shows dispatches and no cost.
-- The two sides are dated independently (a freight bill lands in the month it is
-- booked, not the month the truck ran), so read the ratio as a trend, not as a
-- per-consignment rate.  ZZ_OTHER's freight column is deliberately NULL: the
-- residue is not attributable to any one carrier.
--
-- DO NOT TOTAL THE FREIGHT COLUMN OF THIS GRID.  Measured 2026-08-21: it is short
-- of the same families' freight in transporter.sql by Oil 404.62 L (28.6%), Mart
-- 39.78 L, Bev 13.46 L.  Two structural reasons, both inherent to the (family,
-- month) grain and neither a bug: a family outside the top 20 is folded into
-- ZZ_OTHER, whose freight is NULL by design; and a freight bill booked in a month
-- that family happened not to dispatch in has no cell to land in, because the grid
-- is driven off dispatch rows.  transporter.sql's TOTAL / FREIGHT_VENDOR rows are
-- the authority on freight spend -- this grid is for the per-carrier trend only.
WITH
UDFX AS (
  SELECT "DocEntry" AS DOC_ENTRY,
         CASE WHEN IFNULL(TRIM("U_BilltyNumber"),'') <> '' THEN 1 ELSE 0 END AS HAS_LR,
         CASE WHEN IFNULL(TRIM("U_VehicleNoM"),'')   <> '' THEN 1 ELSE 0 END AS HAS_VEH
  FROM JIVO_OIL_HANADB.OINV        WHERE '{{SCHEMA}}' = 'JIVO_OIL_HANADB'
  UNION ALL
  SELECT "DocEntry",
         CASE WHEN IFNULL(TRIM("U_BilltyNumber"),'') <> '' THEN 1 ELSE 0 END,
         CASE WHEN IFNULL(TRIM("U_VehicleNoM"),'')   <> '' THEN 1 ELSE 0 END
  FROM JIVO_MART_HANADB.OINV       WHERE '{{SCHEMA}}' = 'JIVO_MART_HANADB'
  UNION ALL
  SELECT "DocEntry",
         CASE WHEN IFNULL(TRIM("U_BiltyNumber"),'')  <> '' THEN 1 ELSE 0 END,
         CASE WHEN IFNULL(TRIM("U_VechileNom"),'')   <> '' THEN 1 ELSE 0 END
  FROM JIVO_BEVERAGES_HANADB.OINV  WHERE '{{SCHEMA}}' = 'JIVO_BEVERAGES_HANADB'
),
DISP AS (
  SELECT h."DocEntry" AS DOC_ENTRY,
         TO_VARCHAR(h."DocDate",'YYYY-MM') AS YM,
         TRIM(IFNULL(h."U_TransporterName",'')) AS TN_RAW,
         REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
           UPPER(TRIM(IFNULL(h."U_TransporterName",''))),
           ' ',''),'.',''),',',''),'-',''),'&',''),'(',''),')',''),'/',''),'''',''),'_',''),'%','') AS TN_KEY,
         CAST(h."DocTotal" AS DOUBLE) - CAST(h."VatSum" AS DOUBLE) AS NET_VAL,
         CASE WHEN UPPER(IFNULL(g."GroupName",'')) LIKE '%BRANCH%'        THEN 0
              WHEN UPPER(IFNULL(c."CardName",h."CardName")) LIKE '%JIVO%' THEN 0
              ELSE 1 END AS IS_EXT
  FROM {{SCHEMA}}.OINV h
  LEFT JOIN {{SCHEMA}}.OCRD c ON c."CardCode"  = h."CardCode"
  LEFT JOIN {{SCHEMA}}.OCRG g ON g."GroupCode" = c."GroupCode" AND g."GroupType" = c."CardType"
  WHERE h."CANCELED" = 'N'
    AND h."DocDate" <= DATE'{{ASOF}}'
    AND h."DocDate" <> DATE'2024-09-30'
),
D AS (
  SELECT d.*, IFNULL(x.HAS_LR,0) AS HAS_LR, IFNULL(x.HAS_VEH,0) AS HAS_VEH
  FROM DISP d LEFT JOIN UDFX x ON x.DOC_ENTRY = d.DOC_ENTRY
  WHERE d.TN_KEY <> ''
    AND d.TN_KEY NOT IN ('NA','N','NIL','NILL','NONE','XX','X','0','00','ZZ','TEST')
    AND d.TN_KEY NOT LIKE 'SELF%'     AND d.TN_KEY NOT LIKE 'JIVO%'
    AND d.TN_KEY NOT LIKE 'BYHAND%'   AND d.TN_KEY NOT LIKE 'CUSTOMERPICK%'
    AND d.TN_KEY NOT LIKE '%SELFPICK%' AND d.TN_KEY NOT LIKE '%OWNVEHIC%'
    AND d.TN_KEY NOT LIKE '%VEHICLE'  AND d.TN_KEY NOT LIKE '%VEHICAL'
),
TNAGG AS (SELECT TN_KEY, SUM(NET_VAL) AS VAL FROM D GROUP BY TN_KEY),
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
DF AS (SELECT d.*, m.FAM_KEY FROM D d JOIN FAM m ON m.TN_KEY = d.TN_KEY),
TOP20 AS (
  SELECT FAM_KEY, MIN(TN_RAW) AS TN_SAMPLE, SUM(NET_VAL) AS VAL
  FROM DF GROUP BY FAM_KEY ORDER BY SUM(NET_VAL) DESC, FAM_KEY LIMIT 20
),
DG AS (
  SELECT CASE WHEN t.FAM_KEY IS NULL THEN 'ZZ_OTHER' ELSE d.FAM_KEY END AS FAM_KEY,
         CASE WHEN t.FAM_KEY IS NULL THEN '(all other transporters)' ELSE t.TN_SAMPLE END AS TN_SAMPLE,
         d.YM, d.TN_RAW, d.NET_VAL, d.IS_EXT, d.HAS_LR, d.HAS_VEH
  FROM DF d LEFT JOIN TOP20 t ON t.FAM_KEY = d.FAM_KEY
),
VEND AS (
  -- MUST stay identical to transporter.sql's VEND, or the grid disagrees with the
  -- summary.  A supplier-group test alone loses R K TANKER SERVICE (Oil
  -- VENDA000671, 945 L of road freight filed under group 110 PURCHASE OIL), so a
  -- card qualifies on EITHER the supplier group OR a road-carrier token in its own
  -- name.  Ocean/CHA tokens are deliberately excluded -- see transporter.sql trap 8.
  SELECT CARD_CODE, CARD_NAME, V_KEY
  FROM (
    SELECT c."CardCode" AS CARD_CODE, c."CardName" AS CARD_NAME,
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
VMAP AS (
  SELECT CARD_CODE, CARD_NAME, FAM_KEY FROM (
    SELECT v.CARD_CODE, v.CARD_NAME, t.FAM_KEY,
           ROW_NUMBER() OVER (PARTITION BY v.CARD_CODE
                              ORDER BY LENGTH(t.FAM_KEY) DESC, t.VAL DESC, t.FAM_KEY) AS RN
    FROM VEND v
    JOIN TOP20 t ON LENGTH(t.FAM_KEY) >= 6 AND LENGTH(v.V_KEY) >= 6
                AND (v.V_KEY LIKE t.FAM_KEY || '%' OR t.FAM_KEY LIKE v.V_KEY || '%')
  ) WHERE RN = 1
),
FRTDOC AS (
  SELECT p."CardCode" AS CARD_CODE, TO_VARCHAR(p."DocDate",'YYYY-MM') AS YM,
         1 AS DOCS, CAST(p."DocTotal" AS DOUBLE) - CAST(p."VatSum" AS DOUBLE) AS AMT
  FROM {{SCHEMA}}.OPCH p
  WHERE p."CANCELED" = 'N' AND p."DocDate" <= DATE'{{ASOF}}' AND p."DocDate" <> DATE'2024-09-30'
    AND p."CardCode" IN (SELECT CARD_CODE FROM VMAP)
  UNION ALL
  SELECT r."CardCode", TO_VARCHAR(r."DocDate",'YYYY-MM'),
         0, -(CAST(r."DocTotal" AS DOUBLE) - CAST(r."VatSum" AS DOUBLE))
  FROM {{SCHEMA}}.ORPC r
  WHERE r."CANCELED" = 'N' AND r."DocDate" <= DATE'{{ASOF}}' AND r."DocDate" <> DATE'2024-09-30'
    AND r."CardCode" IN (SELECT CARD_CODE FROM VMAP)
),
FRTFM AS (
  SELECT m.FAM_KEY, f.YM, SUM(f.DOCS) AS FDOCS, SUM(f.AMT) AS FAMT
  FROM FRTDOC f JOIN VMAP m ON m.CARD_CODE = f.CARD_CODE
  GROUP BY m.FAM_KEY, f.YM
),
FAMVEND AS (
  SELECT FAM_KEY, SUBSTRING(STRING_AGG(CARD_NAME, ' + ' ORDER BY CARD_NAME), 1, 120) AS VENDOR_NAME
  FROM VMAP GROUP BY FAM_KEY
),
FAMTOT AS (SELECT FAM_KEY, SUM(NET_VAL) AS TOTVAL FROM DG GROUP BY FAM_KEY)
SELECT g.FAM_KEY,
       MIN(g.TN_SAMPLE) AS TN_SAMPLE,
       g.YM,
       COUNT(*)                          AS DISP_DOCS,
       ROUND(SUM(g.NET_VAL)/100000,2)     AS DISP_VAL_L,
       ROUND(SUM(g.IS_EXT*g.NET_VAL)/100000,2) AS EXT_DISP_VAL_L,
       ROUND(CAST(100.0*SUM(g.HAS_LR)  AS DOUBLE)/NULLIF(COUNT(*),0),1) AS LR_PCT,
       ROUND(CAST(100.0*SUM(g.HAS_VEH) AS DOUBLE)/NULLIF(COUNT(*),0),1) AS VEH_PCT,
       COUNT(DISTINCT g.TN_RAW)          AS VARIANTS,
       MAX(fv.VENDOR_NAME)               AS VENDOR_NAME,
       MAX(fr.FDOCS)                     AS FRT_DOCS,
       ROUND(MAX(fr.FAMT)/100000,2)      AS FRT_SPEND_L,
       ROUND(CAST(100.0*MAX(fr.FAMT) AS DOUBLE)/NULLIF(SUM(g.NET_VAL),0),1) AS FRT_PCT_OF_DISP
FROM DG g
LEFT JOIN FRTFM   fr ON fr.FAM_KEY = g.FAM_KEY AND fr.YM = g.YM
LEFT JOIN FAMVEND fv ON fv.FAM_KEY = g.FAM_KEY
LEFT JOIN FAMTOT  ft ON ft.FAM_KEY = g.FAM_KEY
GROUP BY g.FAM_KEY, g.YM
ORDER BY CASE WHEN g.FAM_KEY = 'ZZ_OTHER' THEN 1 ELSE 0 END,
         MAX(ft.TOTVAL) DESC, g.FAM_KEY, g.YM
LIMIT 800
