-- Rejected drafts still sitting open, for one company schema.
-- {{SCHEMA}} is substituted by build.py (JIVO_OIL_HANADB / JIVO_MART_HANADB /
-- JIVO_BEVERAGES_HANADB). Read-only: hana-sql refuses anything but SELECT.
--
-- Three traps, all measured live on 2026-09-18 — do not "simplify" them away:
--   * WDD1."AuthUpdDat" is NULL on 100% of rows. The decision time is
--     "UpdateDate" + "UpdateTime" (SMALLINT HHMM).
--   * One draft can carry MORE THAN ONE approval request (the double-request
--     bug closed in 5584f319), so the OWDD join multiplies rows. GROUP BY the
--     draft and take MAX() of the decision, or every count inflates.
--   * WddStatus 'C' is CANCELLED, not rejected, and is ~5x bigger. Only 'N' is
--     a rejection. Filtering on DocStatus='O' alone overstates the backlog.
SELECT
    D."ObjType"                                   AS OBJTYPE,
    D."DocEntry"                                  AS DOCENTRY,
    D."DocNum"                                    AS DOCNUM,
    D."CardCode"                                  AS CARDCODE,
    D."CardName"                                  AS VENDOR,
    D."NumAtCard"                                 AS BILLNO,
    TO_DECIMAL(D."DocTotal",18,2)                 AS AMOUNT,
    TO_VARCHAR(D."DocDate",'YYYY-MM-DD')          AS DOCDATE,
    U."USER_CODE"                                 AS CREATOR,
    TO_VARCHAR(
      MAX(ADD_SECONDS(L."UpdateDate",
          (L."UpdateTime"/100)*3600 + MOD(L."UpdateTime",100)*60)),
      'YYYY-MM-DD"T"HH24:MI:SS')                  AS REJECTED_AT,
    MAX(L."Remarks")                              AS REASON
FROM        {{SCHEMA}}.ODRF D
JOIN        {{SCHEMA}}.OWDD W ON W."DraftEntry" = D."DocEntry"
                             AND W."ObjType"    = D."ObjType"
JOIN        {{SCHEMA}}.WDD1 L ON L."WddCode"    = W."WddCode"
                             AND L."Status"     = 'N'
JOIN        {{SCHEMA}}.OUSR U ON U."USERID"     = D."UserSign"
WHERE   D."DocStatus"  = 'O'
    AND D."WddStatus"  = 'N'
    AND D."ObjType"   IN ({{OBJTYPES}})
    AND U."USER_CODE" IN ({{LOGINS}})
GROUP BY D."ObjType", D."DocEntry", D."DocNum", D."CardCode", D."CardName",
         D."NumAtCard", D."DocTotal", D."DocDate", U."USER_CODE"
