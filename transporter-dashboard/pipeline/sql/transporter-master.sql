-- transporter-master.sql
-- ONE ROW PER TRANSPORTER VENDOR (OCRD GroupCode=102, CardType='S') that had ANY
-- activity - an A/P invoice or a vendor payment - on/after 2025-04-01 (FY25 start).
--
-- {{SCHEMA}} is substituted by the runner with exactly one of:
--   JIVO_OIL_HANADB | JIVO_MART_HANADB | JIVO_BEVERAGES_HANADB
-- The three books are SEPARATE. Never union or sum them together (FACTS S.8.7).
--
-- READ-ONLY. SELECT/WITH only. No DML in this file, ever.
--
-- HOW TO RUN:  hana-sql -env <env> -f <substituted-file>    (or pipe on stdin)
--   Do NOT pass this text as a bare argv string: the first line starts with "--"
--   and the binary's flag parser swallows it as an unknown flag. If it must be
--   an argument, put a "--" separator first:  hana-sql -env <env> -- "<sql>".
--   Verified 2026-08-22: -f and stdin give byte-identical output; comments and
--   a trailing ';' are both accepted.
--
-- Binding facts this query implements (transporter-dashboard/FACTS.md):
--   S.2  VPM2's key columns are named BACKWARDS:
--          VPM2."DocNum"   = the PAYMENT's OVPM."DocEntry"
--          VPM2."DocEntry" = the TARGET DOCUMENT's DocEntry
--        DocEntry is per-table, so the InvType='18' filter is MANDATORY before
--        joining VPM2."DocEntry" to OPCH."DocEntry" - without it an InvType=30
--        (journal) or 19 (credit note) line can collide onto an unrelated invoice.
--   S.2  Cancelled flags are spelled differently per table and are THREE-valued
--        (C-0021): OPCH."CANCELED" (upper), OVPM."Canceled" (mixed).
--        Always "= 'N'", never "<> 'Y'" - '<>' keeps the 'C' system mirrors.
--   S.4  TDS lives on the INVOICE (OPCH."WTSum"), not on the payment
--        (VPM2."WtAppld" is 0.00 across the board). OPCH."DiscSum" is 0 today;
--        the column is kept because the reconciliation line needs it.
--   S.5  An on-account payment is one with NO VPM2 line AT ALL.
--   S.6  Window starts 2025-04-01 so every FY26 payment can resolve its invoice.
--   C-0019 OPCH."DocStatus" is unreliable at JIVO (invoices settled by a manual
--        journal stay 'O'). OPEN_INV_CNT is emitted because it was asked for and
--        must be labelled "SAP's own flag, unreliable" wherever it is rendered.
--
-- Verified 2026-08-22 against live HANA: with the window moved to 2026-04-01
-- this query reproduces FACTS S.1 exactly in all three books
--   Oil  194 inv / 97.01L gross / 96 pay / 120.81L paid / 16 on-account / TDS 1,40,077
--   Mart 145 inv / 81.55L gross / 76 pay /  99.03L paid
--   Bev   86 inv / 34.72L gross / 31 pay /  18.98L paid
--
-- OUTPUT CONTRACT:
--   Amounts are plain rupees, 2dp, no grouping, no symbol. NOT lakhs.
--   Dates are 'YYYY-MM-DD'. A SQL NULL prints as the literal token NULL and the
--   loader must render it as "not computed" - never as 0 and never as blank.

WITH tp AS (
    -- The transporter master. GroupCode 102 = 'TRANSPORTER' in all three books.
    SELECT
        c."CardCode" AS CARD_CODE,
        c."CardName" AS CARD_NAME,
        c."Balance"  AS LEDGER_BALANCE
    FROM {{SCHEMA}}.OCRD c
    WHERE c."CardType"  = 'S'
      AND c."GroupCode" = 102
),

inv AS (
    -- Non-cancelled A/P invoices for those vendors, in the fetch window.
    SELECT
        i."DocEntry"  AS DOC_ENTRY,
        i."CardCode"  AS CARD_CODE,
        i."DocDate"   AS DOC_DATE,
        i."DocTotal"  AS GROSS,
        i."WTSum"     AS TDS,
        i."DiscSum"   AS DISC,
        i."DocStatus" AS DOC_STATUS
    FROM {{SCHEMA}}.OPCH i
    INNER JOIN tp ON tp.CARD_CODE = i."CardCode"
    WHERE i."CANCELED" = 'N'
      AND i."DocDate" >= '2025-04-01'
),

pay AS (
    -- Non-cancelled outgoing payments for those vendors, in the fetch window.
    SELECT
        p."DocEntry" AS DOC_ENTRY,
        p."CardCode" AS CARD_CODE,
        p."DocDate"  AS DOC_DATE,
        p."DocTotal" AS PAY_AMT
    FROM {{SCHEMA}}.OVPM p
    INNER JOIN tp ON tp.CARD_CODE = p."CardCode"
    WHERE p."Canceled" = 'N'
      AND p."DocDate" >= '2025-04-01'
),

inv_applied AS (
    -- How much has actually been applied AGAINST each invoice, from any
    -- non-cancelled payment. Deliberately NOT date-windowed on the payment: an
    -- invoice inside the window can be settled by a payment dated outside it
    -- (an older on-account payment reconciled later). Windowing here would
    -- invent false residuals. InvType='18' is mandatory - see the header note
    -- on DocEntry collisions. Same population as transporter-invoices.sql.
    SELECT
        l."DocEntry"          AS DOC_ENTRY,
        SUM(l."SumApplied")   AS APPLIED
    FROM {{SCHEMA}}.VPM2 l
    INNER JOIN {{SCHEMA}}.OVPM p ON p."DocEntry" = l."DocNum"
    WHERE l."InvType"  = '18'
      AND p."Canceled" = 'N'
    GROUP BY l."DocEntry"
),

pay_lines AS (
    -- Per payment: does it have ANY VPM2 line, and what does it apply in total
    -- across ALL InvTypes (18 A/P inv, 19 A/P CN, 30 JE, 46 on-account applied
    -- - which is negative - 24/13/14 contra). Nothing is dropped; dropping a
    -- line type is how the totals stop tying (FACTS S.3).
    -- Cancellation is handled by the join to `pay`, which is already filtered.
    SELECT
        l."DocNum"          AS PAY_DOC_ENTRY,
        SUM(l."SumApplied") AS APPLIED
    FROM {{SCHEMA}}.VPM2 l
    GROUP BY l."DocNum"
),

inv_agg AS (
    SELECT
        v.CARD_CODE,
        COUNT(*)      AS INV_CNT,
        SUM(v.GROSS)  AS INV_GROSS,
        SUM(v.TDS)    AS INV_TDS,
        SUM(v.DISC)   AS INV_DISC,
        -- C-0019: SAP's own open flag. Unreliable at JIVO; emitted as asked.
        SUM(CASE WHEN v.DOC_STATUS = 'O' THEN 1 ELSE 0 END) AS OPEN_INV_CNT,
        -- FLAG_CNT: invoices with an UNEXPLAINED residual, i.e. money WAS applied
        -- to the invoice (at least one InvType-18 allocation from a non-cancelled
        -- payment) and GROSS - TDS - DISCOUNT - APPLIED is not within Rs 1 of 0.
        -- Both directions count: short-paid (TDS plus something else withheld)
        -- and over-paid (full gross paid, TDS not deducted - FACTS S.4 row
        -- 626074367). An invoice with NO allocation at all is 'UNPAID', not
        -- flagged: its residual is not computed (a balancing figure against
        -- nothing is meaningless), which is exactly how transporter-invoices.sql
        -- sets RESIDUAL_FLAG, so this count equals its SHORT+OVER rows per vendor.
        -- (The purely literal reading - treat no allocation as applied = 0 -
        -- would also flag every unpaid bill and make FLAG_CNT ~= INV_CNT. If that
        -- reading is wanted, drop the "a.DOC_ENTRY IS NOT NULL AND" line.)
        SUM(CASE
                WHEN a.DOC_ENTRY IS NOT NULL
                 AND ABS(v.GROSS - v.TDS - v.DISC - COALESCE(a.APPLIED, 0)) > 1
                THEN 1 ELSE 0
            END) AS FLAG_CNT
    FROM inv v
    LEFT JOIN inv_applied a ON a.DOC_ENTRY = v.DOC_ENTRY
    GROUP BY v.CARD_CODE
),

pay_agg AS (
    -- MATCHED_APPLIED is summed over the SAME payment population as PAY_CNT /
    -- PAY_TOTAL (this vendor, non-cancelled, DocDate >= window), all InvTypes,
    -- so that per vendor:
    --   PAY_TOTAL = MATCHED_APPLIED + ONACCT_PAY_AMT + (unallocated part of
    --               partially-allocated payments, which can be negative when a
    --               payment's lines exceed its DocTotal)
    -- Sign caveat (see transporter-payments.sql header): SAP stores an InvType
    -- '19' credit-note line with a POSITIVE SumApplied even though the CN reduces
    -- what the payment covers, so the 4 payments that carry a CN line (3 Oil,
    -- 1 Mart) are over-counted here by 2 x the CN amount. This column is the
    -- plain SUM the spec asked for and equals the payments dataset's ALLOC_TOTAL
    -- per vendor exactly; the netted view is recoverable from that dataset.
    SELECT
        q.CARD_CODE,
        COUNT(*)         AS PAY_CNT,
        SUM(q.PAY_AMT)   AS PAY_TOTAL,
        SUM(COALESCE(pl.APPLIED, 0)) AS MATCHED_APPLIED,
        -- On-account = NO VPM2 line at all (FACTS S.5). Money paid against no
        -- bill. It gets its own bucket; hiding it makes the board useless.
        SUM(CASE WHEN pl.PAY_DOC_ENTRY IS NULL THEN 1 ELSE 0 END)        AS ONACCT_PAY_CNT,
        SUM(CASE WHEN pl.PAY_DOC_ENTRY IS NULL THEN q.PAY_AMT ELSE 0 END) AS ONACCT_PAY_AMT
    FROM pay q
    LEFT JOIN pay_lines pl ON pl.PAY_DOC_ENTRY = q.DOC_ENTRY
    GROUP BY q.CARD_CODE
),

act AS (
    -- "Had ANY activity": first/last touch across invoices AND payments.
    -- A UNION ALL rather than LEAST/GREATEST so a vendor with only one of the
    -- two still gets a real date instead of a NULL.
    SELECT
        CARD_CODE,
        MIN(D) AS FIRST_ACTIVITY,
        MAX(D) AS LAST_ACTIVITY
    FROM (
        SELECT CARD_CODE, DOC_DATE AS D FROM inv
        UNION ALL
        SELECT CARD_CODE, DOC_DATE AS D FROM pay
    ) u
    GROUP BY CARD_CODE
)

SELECT
    t.CARD_CODE                                          AS CARD_CODE,
    t.CARD_NAME                                          AS CARD_NAME,
    TO_VARCHAR(a.FIRST_ACTIVITY, 'YYYY-MM-DD')           AS FIRST_ACTIVITY,
    TO_VARCHAR(a.LAST_ACTIVITY,  'YYYY-MM-DD')           AS LAST_ACTIVITY,

    -- A vendor that appears here via payments only has genuinely 0 invoices in
    -- the window: that zero is a fact, not an uncomputed value.
    COALESCE(iv.INV_CNT,   0)                            AS INV_CNT,
    CAST(ROUND(COALESCE(iv.INV_GROSS, 0), 2) AS DECIMAL(18,2))       AS INV_GROSS,
    CAST(ROUND(COALESCE(iv.INV_TDS,   0), 2) AS DECIMAL(18,2))       AS INV_TDS,
    CAST(ROUND(COALESCE(iv.INV_DISC,  0), 2) AS DECIMAL(18,2))       AS INV_DISC,

    COALESCE(pa.PAY_CNT,   0)                            AS PAY_CNT,
    CAST(ROUND(COALESCE(pa.PAY_TOTAL, 0), 2) AS DECIMAL(18,2))       AS PAY_TOTAL,

    CAST(ROUND(COALESCE(pa.MATCHED_APPLIED, 0), 2) AS DECIMAL(18,2)) AS MATCHED_APPLIED,
    COALESCE(pa.ONACCT_PAY_CNT, 0)                       AS ONACCT_PAY_CNT,
    CAST(ROUND(COALESCE(pa.ONACCT_PAY_AMT, 0), 2) AS DECIMAL(18,2))  AS ONACCT_PAY_AMT,

    -- OCRD."Balance" verbatim, sign untouched, all-time (not windowed).
    -- It equals SUM(JDT1.Debit - JDT1.Credit) on the vendor's control rows, so:
    --   NEGATIVE = net CREDIT = JIVO OWES THE TRANSPORTER (payable).
    --   POSITIVE = net DEBIT  = advance held / the transporter owes JIVO.
    -- Left NULL if SAP holds NULL - the renderer prints "not computed", never 0.
    CAST(ROUND(t.LEDGER_BALANCE, 2) AS DECIMAL(18,2))                AS BALANCE,

    COALESCE(iv.OPEN_INV_CNT, 0)                         AS OPEN_INV_CNT,
    COALESCE(iv.FLAG_CNT,     0)                         AS FLAG_CNT

FROM tp t
INNER JOIN act a  ON a.CARD_CODE  = t.CARD_CODE   -- the "had ANY activity" gate
LEFT  JOIN inv_agg iv ON iv.CARD_CODE = t.CARD_CODE
LEFT  JOIN pay_agg pa ON pa.CARD_CODE = t.CARD_CODE
ORDER BY COALESCE(iv.INV_GROSS, 0) DESC, t.CARD_CODE ASC
