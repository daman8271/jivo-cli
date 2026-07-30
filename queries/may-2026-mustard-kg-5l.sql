-- May 2026: MUSTARD KACHI GHANI 5 LTR (4 PCS pack) — units sold, all 3 companies
-- Invoices (+) net of Credit Notes (-). Quantity is in PIECES = 5-litre jars.
WITH src AS (
  SELECT 'OIL' AS "Company", 'INV' AS "Kind", i."ItemCode", t."ItemName",
         i."Quantity" AS "Qty", (i."LineTotal" - i."VatSum") AS "NetGST"
  FROM "JIVO_OIL_HANADB"."INV1" i
  JOIN "JIVO_OIL_HANADB"."OINV" o ON i."DocEntry" = o."DocEntry"
  JOIN "JIVO_OIL_HANADB"."OITM" t ON i."ItemCode" = t."ItemCode"
  WHERE o."DocDate" >= '2026-05-01' AND o."DocDate" < '2026-06-01' AND o."CANCELED" = 'N'
    AND t."U_Sub_Group" = 'MUSTARD' AND UPPER(t."ItemName") LIKE '%5 LTR%'
    AND (UPPER(t."ItemName") LIKE '%KACCHI GHANI%' OR UPPER(t."ItemName") LIKE '%KACHI GHANI%')
  UNION ALL
  SELECT 'OIL', 'CN', i."ItemCode", t."ItemName",
         -i."Quantity", -(i."LineTotal" - i."VatSum")
  FROM "JIVO_OIL_HANADB"."RIN1" i
  JOIN "JIVO_OIL_HANADB"."ORIN" o ON i."DocEntry" = o."DocEntry"
  JOIN "JIVO_OIL_HANADB"."OITM" t ON i."ItemCode" = t."ItemCode"
  WHERE o."DocDate" >= '2026-05-01' AND o."DocDate" < '2026-06-01' AND o."CANCELED" = 'N'
    AND t."U_Sub_Group" = 'MUSTARD' AND UPPER(t."ItemName") LIKE '%5 LTR%'
    AND (UPPER(t."ItemName") LIKE '%KACCHI GHANI%' OR UPPER(t."ItemName") LIKE '%KACHI GHANI%')
  UNION ALL
  SELECT 'MART', 'INV', i."ItemCode", t."ItemName",
         i."Quantity", (i."LineTotal" - i."VatSum")
  FROM "JIVO_MART_HANADB"."INV1" i
  JOIN "JIVO_MART_HANADB"."OINV" o ON i."DocEntry" = o."DocEntry"
  JOIN "JIVO_MART_HANADB"."OITM" t ON i."ItemCode" = t."ItemCode"
  WHERE o."DocDate" >= '2026-05-01' AND o."DocDate" < '2026-06-01' AND o."CANCELED" = 'N'
    AND t."U_Sub_Group" = 'MUSTARD' AND UPPER(t."ItemName") LIKE '%5 LTR%'
    AND (UPPER(t."ItemName") LIKE '%KACCHI GHANI%' OR UPPER(t."ItemName") LIKE '%KACHI GHANI%')
  UNION ALL
  SELECT 'MART', 'CN', i."ItemCode", t."ItemName",
         -i."Quantity", -(i."LineTotal" - i."VatSum")
  FROM "JIVO_MART_HANADB"."RIN1" i
  JOIN "JIVO_MART_HANADB"."ORIN" o ON i."DocEntry" = o."DocEntry"
  JOIN "JIVO_MART_HANADB"."OITM" t ON i."ItemCode" = t."ItemCode"
  WHERE o."DocDate" >= '2026-05-01' AND o."DocDate" < '2026-06-01' AND o."CANCELED" = 'N'
    AND t."U_Sub_Group" = 'MUSTARD' AND UPPER(t."ItemName") LIKE '%5 LTR%'
    AND (UPPER(t."ItemName") LIKE '%KACCHI GHANI%' OR UPPER(t."ItemName") LIKE '%KACHI GHANI%')
  UNION ALL
  SELECT 'BEVERAGES', 'INV', i."ItemCode", t."ItemName",
         i."Quantity", (i."LineTotal" - i."VatSum")
  FROM "JIVO_BEVERAGES_HANADB"."INV1" i
  JOIN "JIVO_BEVERAGES_HANADB"."OINV" o ON i."DocEntry" = o."DocEntry"
  JOIN "JIVO_BEVERAGES_HANADB"."OITM" t ON i."ItemCode" = t."ItemCode"
  WHERE o."DocDate" >= '2026-05-01' AND o."DocDate" < '2026-06-01' AND o."CANCELED" = 'N'
    AND t."U_Sub_Group" = 'MUSTARD' AND UPPER(t."ItemName") LIKE '%5 LTR%'
    AND (UPPER(t."ItemName") LIKE '%KACCHI GHANI%' OR UPPER(t."ItemName") LIKE '%KACHI GHANI%')
  UNION ALL
  SELECT 'BEVERAGES', 'CN', i."ItemCode", t."ItemName",
         -i."Quantity", -(i."LineTotal" - i."VatSum")
  FROM "JIVO_BEVERAGES_HANADB"."RIN1" i
  JOIN "JIVO_BEVERAGES_HANADB"."ORIN" o ON i."DocEntry" = o."DocEntry"
  JOIN "JIVO_BEVERAGES_HANADB"."OITM" t ON i."ItemCode" = t."ItemCode"
  WHERE o."DocDate" >= '2026-05-01' AND o."DocDate" < '2026-06-01' AND o."CANCELED" = 'N'
    AND t."U_Sub_Group" = 'MUSTARD' AND UPPER(t."ItemName") LIKE '%5 LTR%'
    AND (UPPER(t."ItemName") LIKE '%KACCHI GHANI%' OR UPPER(t."ItemName") LIKE '%KACHI GHANI%')
)
SELECT "Company", "ItemCode", "ItemName",
       SUM("Qty")                        AS "NetJars",
       ROUND(SUM("Qty") * 5, 0)          AS "Litres",
       ROUND(SUM("Qty") * 5 * 0.91 / 1000, 2) AS "Tonnes",
       ROUND(SUM("NetGST"), 0)           AS "SalesNetGST"
FROM src
GROUP BY "Company", "ItemCode", "ItemName"
ORDER BY "Company", "ItemCode"
