-- Factory indirect expenses + casual labour, by posting month, FY-to-date.
-- FAMILY splits the two things the operator asked for together: the whole
-- INDIRECT EXPENSE tree (5600000, prefix '56' in all three books) and CASUAL
-- LABOUR (5100008), which sits under DIRECT EXPENSE and would otherwise be
-- invisible in an indirect-only cut.
WITH W AS (
  SELECT CASE WHEN MONTH(TO_DATE('{{ASOF}}')) >= 4
              THEN TO_DATE(TO_VARCHAR(YEAR(TO_DATE('{{ASOF}}'))) || '-04-01')
              ELSE TO_DATE(TO_VARCHAR(YEAR(TO_DATE('{{ASOF}}')) - 1) || '-04-01')
         END AS FY_START,
         TO_DATE('{{ASOF}}') AS ASOF
  FROM DUMMY
)
SELECT
  TO_VARCHAR(j."RefDate", 'YYYY-MM')                         AS MONTH_KEY,
  TO_VARCHAR(j."RefDate", 'MON-YY')                          AS MONTH_LABEL,
  CASE WHEN a."AcctCode" = '5100008' THEN 'CASUAL LABOUR'
       ELSE 'INDIRECT' END                                   AS FAMILY,
  CASE WHEN a."AcctCode" = '5100008' THEN 'CASUAL LABOUR (direct)'
       ELSE COALESCE(g."AcctName", a."AcctName") END          AS GRP_NAME,
  COUNT(*)                                                   AS LINES_CNT,
  COUNT(DISTINCT j."TransId")                                AS DOCS_CNT,
  ROUND(SUM(j."Debit" - j."Credit") / 100000, 2)              AS NET_L,
  ROUND(SUM(j."Debit") / 100000, 2)                           AS DEBIT_L,
  ROUND(SUM(j."Credit") / 100000, 2)                          AS CREDIT_L,
  CASE WHEN TO_VARCHAR(j."RefDate", 'YYYY-MM')
          = TO_VARCHAR((SELECT ASOF FROM W), 'YYYY-MM') THEN 'Y' ELSE 'N' END
                                                             AS PART_MONTH
FROM {{SCHEMA}}.JDT1 j
JOIN {{SCHEMA}}.OACT a ON a."AcctCode" = j."Account"
LEFT JOIN {{SCHEMA}}.OACT g ON g."AcctCode" = a."FatherNum"
WHERE j."RefDate" >= (SELECT FY_START FROM W)
  AND j."RefDate" <= (SELECT ASOF FROM W)
  AND (a."AcctCode" LIKE '56%' OR a."AcctCode" = '5100008')
GROUP BY
  TO_VARCHAR(j."RefDate", 'YYYY-MM'),
  TO_VARCHAR(j."RefDate", 'MON-YY'),
  CASE WHEN a."AcctCode" = '5100008' THEN 'CASUAL LABOUR' ELSE 'INDIRECT' END,
  CASE WHEN a."AcctCode" = '5100008' THEN 'CASUAL LABOUR (direct)'
       ELSE COALESCE(g."AcctName", a."AcctName") END,
  CASE WHEN TO_VARCHAR(j."RefDate", 'YYYY-MM')
          = TO_VARCHAR((SELECT ASOF FROM W), 'YYYY-MM') THEN 'Y' ELSE 'N' END
ORDER BY 1, 7 DESC
