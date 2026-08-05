SELECT
  W."ItemCode" AS "ItemCode",
  I."ItemName" AS "ItemName",
  G."ItmsGrpNam" AS "ItmsGrpNam",
  I."InvntryUom" AS "InvntryUom",
  I."U_TYPE" AS "U_TYPE",
  I."U_Sub_Group" AS "U_Sub_Group",
  I."frozenFor" AS "frozenFor",
  W."WhsCode" AS "WhsCode",
  H."WhsName" AS "WhsName",
  ROUND(TO_DOUBLE(W."OnHand"), 2) AS "OnHand",
  ROUND(TO_DOUBLE(W."IsCommited"), 2) AS "IsCommited",
  ROUND(TO_DOUBLE(W."OnOrder"), 2) AS "OnOrder",
  ROUND(TO_DOUBLE(W."StockValue"), 2) AS "StockValue"
FROM JIVO_BEVERAGES_HANADB.OITW W
INNER JOIN JIVO_BEVERAGES_HANADB.OITM I ON I."ItemCode" = W."ItemCode"
LEFT JOIN JIVO_BEVERAGES_HANADB.OITB G ON G."ItmsGrpCod" = I."ItmsGrpCod"
LEFT JOIN JIVO_BEVERAGES_HANADB.OWHS H ON H."WhsCode" = W."WhsCode"
WHERE W."OnHand" <> 0 OR W."IsCommited" <> 0 OR W."OnOrder" <> 0 OR W."StockValue" <> 0
ORDER BY W."ItemCode", W."WhsCode"
