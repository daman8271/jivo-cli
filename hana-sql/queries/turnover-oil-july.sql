-- Oil turnover, 1–28 Jul 2026, net of GST (DocTotal - VatSum), excluding cancelled.
-- Turnover = A/R invoices (OINV) minus A/R credit notes / returns (ORIN).
-- Change the schema (JIVO_MART_HANADB / JIVO_BEVERAGES_HANADB) for other companies.
SELECT
  inv_rows,
  cn_rows,
  TO_DOUBLE(inv_net)                               AS inv_net,
  TO_DOUBLE(cn_net)                                AS cn_net,
  TO_DOUBLE(inv_net - cn_net)                      AS turnover_net,
  TO_DOUBLE(ROUND((inv_net - cn_net)/10000000, 2)) AS turnover_crore
FROM (
  SELECT
    (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OINV"
       WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N') AS inv_rows,
    (SELECT COALESCE(SUM("DocTotal" - "VatSum"), 0) FROM "JIVO_OIL_HANADB"."OINV"
       WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N') AS inv_net,
    (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."ORIN"
       WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N') AS cn_rows,
    (SELECT COALESCE(SUM("DocTotal" - "VatSum"), 0) FROM "JIVO_OIL_HANADB"."ORIN"
       WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N') AS cn_net
  FROM DUMMY
)
