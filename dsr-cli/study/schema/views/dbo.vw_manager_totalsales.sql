CREATE view vw_manager_totalsales as
select personname, total, asm, shopscovered,team,tq,prod,boxes,isnull(sku,'') sku from (
SELECT PERSONNAME, CASE WHEN wheatgrass = 0 THEN concat('Canola: ', canola, ' L, Olive: ', olive, ' L, Other oils: ', oils, ' L') ELSE concat('WG and Beverages: ', wheatgrass, ' L') END AS total, asm, shopscovered, 
                  CASE WHEN wheatgrass = 0 THEN 'Oil' ELSE 'WG' END AS team, ISNULL(tq, 0) AS tq, ISNULL(prod, 0) AS prod, isnull(boxes,0) boxes,
    (select string_agg(productname, ', ') sku from (
    select distinct productname from tbl_salesreport s, tbl_productssold p where s.date=cast(getdate() as date) and s.personname=x.personname and s.salesid=p.salesid and p.deletiondate is null and s.deletiondate is null) sml) sku
FROM     (SELECT sp.PERSONNAME, SUM(CASE WHEN p.itemtype = 1 THEN p.totalQuantity ELSE 0 END) AS canola, SUM(CASE WHEN p.itemtype IN (2, 5, 8) THEN p.totalQuantity ELSE 0 END) AS olive, SUM(CASE WHEN p.itemtype IN (4, 6, 7, 9, 11) 
                                    THEN p.totalQuantity ELSE 0 END) AS oils, SUM(CASE WHEN p.itemtype IN (3, 13) THEN p.totalQuantity ELSE 0 END) AS wheatgrass, boss.asm, COUNT(s.retailerId) AS shopscovered, SUM(p.totalQuantity) AS tq, 
                                    COUNT(DISTINCT CASE WHEN s.status IN ('DONE', 'BACKEND', 'TELEPHONIC') THEN retailerid ELSE NULL END) AS prod,
									format(round(sum(1.0*pieces/piecespercase),1),'F') boxes
                  FROM      dbo.tbl_SalesReport AS s INNER JOIN
                                    dbo.tbl_salesperson AS sp ON s.personId = sp.ID AND s.deletionDate IS NULL INNER JOIN
                                    dbo.tbl_hierarchy AS boss ON sp.PERSONNAME = boss.personname LEFT OUTER JOIN
                                    dbo.tbl_ProductsSold AS p ON s.salesId = p.salesId AND p.deletionDate IS NULL LEFT OUTER JOIN
									dbo.tbl_item i ON p.productid = i.id
                  WHERE   (s.date = CAST(GETDATE() AS date))
                  GROUP BY sp.PERSONNAME, boss.asm) x) x1