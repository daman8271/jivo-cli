SELECT
  w."ItemCode" AS "ItemCode",
  i."ItemName" AS "ItemName",
  g."ItmsGrpNam" AS "ItmsGrpNam",
  i."InvntryUom" AS "InvntryUom",
  i."U_TYPE" AS "U_TYPE",
  i."U_Sub_Group" AS "U_Sub_Group",
  i."frozenFor" AS "frozenFor",
  w."WhsCode" AS "WhsCode",
  h."WhsName" AS "WhsName",
  ROUND(TO_DOUBLE(w."OnHand"), 2) AS "OnHand",
  ROUND(TO_DOUBLE(w."IsCommited"), 2) AS "IsCommited",
  ROUND(TO_DOUBLE(w."OnOrder"), 2) AS "OnOrder",
  ROUND(TO_DOUBLE(w."StockValue"), 2) AS "StockValue"
FROM JIVO_MART_HANADB.OITW w
JOIN JIVO_MART_HANADB.OITM i ON i."ItemCode" = w."ItemCode"
LEFT JOIN JIVO_MART_HANADB.OITB g ON g."ItmsGrpCod" = i."ItmsGrpCod"
LEFT JOIN JIVO_MART_HANADB.OWHS h ON h."WhsCode" = w."WhsCode"
WHERE w."OnHand" <> 0 OR w."IsCommited" <> 0 OR w."OnOrder" <> 0 OR w."StockValue" <> 0
ORDER BY w."ItemCode", w."WhsCode"
