CREATE view vw_stock_primary_skus as
SELECT        distid, productid
FROM            tbl_distributorstock ds, tbl_diststockproducts dsp
WHERE        ds.diststockid = dsp.diststockid AND stockdate =
                             (SELECT        min(stockdate)
                               FROM            tbl_distributorstock ds2
                               WHERE        ds.distid = ds2.distid AND stockdate >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)) AND boxes > 0
UNION
SELECT DISTINCT to_retailerid, itemid
FROM            tbl_primary_sales p, tbl_retailers r
WHERE        date >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0) AND r.id = p.to_retailerid AND r.type = 'Distributor' AND quantity > 0 and (p.deleted is null or p.deleted=0)