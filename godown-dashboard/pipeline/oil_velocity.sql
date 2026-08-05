-- oil_velocity: 90-day consumption per item x warehouse from OINM (JIVO Oil)
-- TransType 67 = internal stock transfer, excluded from OUT90/IN90 (not consumption).
-- RET90 = customer returns coming back in: 14 AR credit memo, 16 return.
SELECT
  "ItemCode",
  "Warehouse",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "TransType" <> 67 THEN "OutQty" ELSE 0 END)), 2)      AS "OUT90",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "TransType" IN (14, 16) THEN "InQty" ELSE 0 END)), 2) AS "RET90",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "TransType" <> 67 THEN "InQty" ELSE 0 END)), 2)       AS "IN90"
FROM JIVO_OIL_HANADB.OINM
WHERE "DocDate" >= ADD_DAYS(CURRENT_DATE, -90)
GROUP BY "ItemCode", "Warehouse"
