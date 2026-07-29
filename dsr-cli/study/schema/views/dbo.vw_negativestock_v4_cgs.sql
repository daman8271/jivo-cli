
CREATE VIEW [dbo].[vw_negativestock_v4_cgs] AS
SELECT 
    distid,
    distname,
    itemtype.state,
    productid,
    itemtype.itemname,
    opening,
    prim,
    sales,
    total,
    personname,
    a.itemtype,
    primout          -- NEW, added at the end
FROM
(
    SELECT 
        distid,
        distname,
        state,
        productid,
        itemname,
        SUM(opening) AS opening,
        SUM(prim) AS prim,
        SUM(primout) AS primout,      -- NEW
        SUM(sales) AS sales,
        SUM(total) AS total,
        MAX(personname) AS personname
    FROM
    (
        SELECT 
            distid,
            (
                SELECT retailername
                FROM tbl_retailers r
                WHERE r.id = datum.distid
            ) AS distname,

            (
                SELECT st.state
                FROM tbl_retailers r
                INNER JOIN tbl_states st 
                    ON r.state = st.stateid
                WHERE r.id = datum.distid
            ) AS state,

            productid,

            (
                SELECT itemname
                FROM tbl_item i
                WHERE i.id = datum.productid
            ) AS itemname,

            CASE WHEN factor = 'Opening'    THEN boxes ELSE 0 END AS opening,
            CASE WHEN factor = 'Primary'    THEN boxes ELSE 0 END AS prim,
            CASE WHEN factor = 'PrimaryOut' THEN boxes ELSE 0 END AS primout,  -- NEW
            CASE WHEN factor = 'Secondary'  THEN boxes ELSE 0 END AS sales,

            CASE 
                WHEN factor IN ('Secondary', 'PrimaryOut')   -- PrimaryOut also reduces stock
                THEN -boxes 
                ELSE boxes 
            END AS total,

            personname

        FROM
        (
            -- Opening Stock
            SELECT 
                distid,
                stockdate,
                productid,
                1.0 * boxes AS boxes,
                'Opening' AS factor,
                '' AS personname
            FROM tbl_distributorStock ds
            INNER JOIN tbl_diststockproducts dsp
                ON ds.diststockid = dsp.distStockId
            WHERE ds.stockDate =
            (
                SELECT MAX(stockdate)
                FROM tbl_distributorStock ds2
                WHERE ds2.distid = ds.distid
                AND ds2.stockdate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
                AND (ds2.deleted IS NULL OR ds2.deleted = 0)
            )
            AND ds.stockDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            AND (ds.deleted IS NULL OR ds.deleted = 0)
            AND (dsp.deleted IS NULL OR dsp.deleted = 0)

            UNION ALL

            -- Primary Sales (IN to distributor)
            SELECT 
                to_retailerid,
                date,
                itemid,
                quantity,
                'Primary',
                ''
            FROM tbl_primary_sales p1
            WHERE date >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            AND date >=
            (
                SELECT MAX(CAST(stockdate AS DATE))
                FROM tbl_distributorStock ds2
                WHERE ds2.distid = to_retailerid
                AND (ds2.deleted IS NULL OR ds2.deleted = 0)
            )
            AND (p1.deleted IS NULL OR p1.deleted = 0)

            UNION ALL

            -- NEW: Primary Out (transfers OUT from distributor)
            SELECT 
                from_retailerid,          -- <<< change this if your sender column has a different name
                date,
                itemid,
                quantity,
                'PrimaryOut',
                ''
            FROM tbl_primary_sales p2
            WHERE date >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            AND date >=
            (
                SELECT MAX(CAST(stockdate AS DATE))
                FROM tbl_distributorStock ds2
                WHERE ds2.distid = from_retailerid   -- <<< same column here
                AND (ds2.deleted IS NULL OR ds2.deleted = 0)
            )
            AND (p2.deleted IS NULL OR p2.deleted = 0)

            UNION ALL

            -- Secondary Sales
            SELECT 
                s.distid,
                DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1),
                p.productid,
                SUM(1.0 * p.pieces / i.piecespercase),
                'Secondary',
                MAX(personname)
            FROM tbl_salesreport s
            INNER JOIN tbl_productssold p
                ON s.salesid = p.salesid
            INNER JOIN tbl_item i
                ON i.id = p.productid
            WHERE s.deletiondate IS NULL
            AND p.deletiondate IS NULL
            AND i.deleted = 0
            AND s.date > '20230401'
            AND s.date >=
            (
                SELECT MAX(CAST(stockdate AS DATE))
                FROM tbl_distributorStock ds2
                WHERE ds2.distid = s.distid
                AND (ds2.deleted IS NULL OR ds2.deleted = 0)
            )
            AND s.date >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
            AND (s.deleted != 1)
            GROUP BY s.distid, p.productid

        ) datum
    ) x
    GROUP BY 
        distid,
        distname,
        state,
        productid,
        itemname
) itemtype
INNER JOIN tbl_item a
    ON a.id = itemtype.productid;
