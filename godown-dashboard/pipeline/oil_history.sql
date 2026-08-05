-- oil_history: net movement AFTER each month-end cutoff, per item x warehouse (JIVO Oil).
-- Month-end stock reconstructs as OnHand_now - NET_AFTER_<i>.
-- ALL TransTypes included (transfers matter for per-warehouse levels).
-- Cutoff map: 1=2026-02-28  2=2026-03-31  3=2026-04-30  4=2026-05-31  5=2026-06-30  6=2026-07-31
SELECT
  "ItemCode",
  "Warehouse",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "DocDate" > LAST_DAY(ADD_MONTHS(CURRENT_DATE, -6)) THEN "InQty" - "OutQty" ELSE 0 END)), 2) AS "NET_AFTER_1",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "DocDate" > LAST_DAY(ADD_MONTHS(CURRENT_DATE, -5)) THEN "InQty" - "OutQty" ELSE 0 END)), 2) AS "NET_AFTER_2",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "DocDate" > LAST_DAY(ADD_MONTHS(CURRENT_DATE, -4)) THEN "InQty" - "OutQty" ELSE 0 END)), 2) AS "NET_AFTER_3",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "DocDate" > LAST_DAY(ADD_MONTHS(CURRENT_DATE, -3)) THEN "InQty" - "OutQty" ELSE 0 END)), 2) AS "NET_AFTER_4",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "DocDate" > LAST_DAY(ADD_MONTHS(CURRENT_DATE, -2)) THEN "InQty" - "OutQty" ELSE 0 END)), 2) AS "NET_AFTER_5",
  ROUND(TO_DOUBLE(SUM(CASE WHEN "DocDate" > LAST_DAY(ADD_MONTHS(CURRENT_DATE, -1)) THEN "InQty" - "OutQty" ELSE 0 END)), 2) AS "NET_AFTER_6"
FROM JIVO_OIL_HANADB.OINM
WHERE "DocDate" > LAST_DAY(ADD_MONTHS(CURRENT_DATE, -6))
GROUP BY "ItemCode", "Warehouse"
