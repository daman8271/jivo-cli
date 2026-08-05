-- bev_expiry: batch rows still holding stock + their expiry dates (JIVO Beverages)
SELECT
  q."ItemCode"                          AS "ItemCode",
  i."ItemName"                          AS "ItemName",
  i."InvntryUom"                        AS "InvntryUom",
  ROUND(TO_DOUBLE(q."Quantity"), 2)     AS "Quantity",
  TO_VARCHAR(b."ExpDate", 'YYYY-MM-DD') AS "ExpDate"
FROM JIVO_BEVERAGES_HANADB.OBTQ q
JOIN JIVO_BEVERAGES_HANADB.OBTN b ON b."AbsEntry" = q."MdAbsEntry"
JOIN JIVO_BEVERAGES_HANADB.OITM i ON i."ItemCode" = q."ItemCode"
WHERE q."Quantity" > 0
