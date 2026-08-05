SELECT
  "ItemCode" AS "ItemCode",
  "Warehouse" AS "Warehouse",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "TransType" <> 67 THEN "OutQty" ELSE 0 END)), 2) AS "OUT90",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "TransType" IN (14, 16) THEN "InQty" ELSE 0 END)), 2) AS "RET90",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "TransType" <> 67 THEN "InQty" ELSE 0 END)), 2) AS "IN90"
FROM JIVO_MART_HANADB.OINM
WHERE "DocDate" >= ADD_DAYS(CURRENT_DATE, -90)
GROUP BY "ItemCode", "Warehouse"
ORDER BY "ItemCode", "Warehouse"
