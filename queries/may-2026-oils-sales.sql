-- May 2026 Sales: Mustard 1L, Canola 1L, and other Commodity 1L (ex mustard/sunflower) across all 3 companies

-- OIL COMPANY
SELECT
  'OIL' as Company,
  i."ItemCode",
  t."ItemName",
  SUM(i."Quantity") as TotalUnits,
  ROUND(SUM(i."LineTotal" - i."VatSum"), 2) as SalesNetGST,
  ROUND(SUM(i."LineTotal"), 2) as SalesGrossGST
FROM JIVO_OIL_HANADB.INV1 i
JOIN JIVO_OIL_HANADB.OINV o ON i."DocEntry" = o."DocEntry"
JOIN JIVO_OIL_HANADB.OITM t ON i."ItemCode" = t."ItemCode"
WHERE o."DocDate" >= '2026-05-01'
  AND o."DocDate" < '2026-06-01'
  AND o."CANCELED" = 'N'
  AND (
    (UPPER(t."ItemName") LIKE '%MUSTARD%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%CANOLA%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%OLIVE%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%SOYABEAN%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%EXTRA LIGHT%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%POMACE%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
  )
GROUP BY i."ItemCode", t."ItemName"

UNION ALL

-- MART COMPANY
SELECT
  'MART' as Company,
  i."ItemCode",
  t."ItemName",
  SUM(i."Quantity") as TotalUnits,
  ROUND(SUM(i."LineTotal" - i."VatSum"), 2) as SalesNetGST,
  ROUND(SUM(i."LineTotal"), 2) as SalesGrossGST
FROM JIVO_MART_HANADB.INV1 i
JOIN JIVO_MART_HANADB.OINV o ON i."DocEntry" = o."DocEntry"
JOIN JIVO_MART_HANADB.OITM t ON i."ItemCode" = t."ItemCode"
WHERE o."DocDate" >= '2026-05-01'
  AND o."DocDate" < '2026-06-01'
  AND o."CANCELED" = 'N'
  AND (
    (UPPER(t."ItemName") LIKE '%MUSTARD%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%CANOLA%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%OLIVE%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%SOYABEAN%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%EXTRA LIGHT%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%POMACE%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
  )
GROUP BY i."ItemCode", t."ItemName"

UNION ALL

-- BEVERAGES COMPANY
SELECT
  'BEVERAGES' as Company,
  i."ItemCode",
  t."ItemName",
  SUM(i."Quantity") as TotalUnits,
  ROUND(SUM(i."LineTotal" - i."VatSum"), 2) as SalesNetGST,
  ROUND(SUM(i."LineTotal"), 2) as SalesGrossGST
FROM JIVO_BEVERAGES_HANADB.INV1 i
JOIN JIVO_BEVERAGES_HANADB.OINV o ON i."DocEntry" = o."DocEntry"
JOIN JIVO_BEVERAGES_HANADB.OITM t ON i."ItemCode" = t."ItemCode"
WHERE o."DocDate" >= '2026-05-01'
  AND o."DocDate" < '2026-06-01'
  AND o."CANCELED" = 'N'
  AND (
    (UPPER(t."ItemName") LIKE '%MUSTARD%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%CANOLA%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%OLIVE%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%SOYABEAN%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%EXTRA LIGHT%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
    OR
    (UPPER(t."ItemName") LIKE '%POMACE%' AND UPPER(t."ItemName") LIKE '%1 LTR%')
  )
GROUP BY i."ItemCode", t."ItemName"
ORDER BY Company, "ItemCode";
