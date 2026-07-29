CREATE view vw_manager as 
SELECT        salesId, date, PERSONNAME, retailerName, address, beat, timeDuration, l1, l2, l3, l4, quantity, schemeQuantity, status, lastSaleDate, lastSale, contactNo, imagePath, asm
FROM            (SELECT        sr.salesId, sr.date, person.PERSONNAME, rets.retailerName, rets.address,
                                                        (SELECT        TOP (1) beat.beatName
                                                          FROM            dbo.tbl_beats AS beat INNER JOIN
                                                                                    dbo.tbl_BeatShopMap AS beatShops ON beat.beatId = beatShops.beatId
                                                          WHERE        (beatShops.shopId = rets.Id) AND (beat.deleted <> 1) AND (beat.personId = sr.personId)) AS beat, ISNULL(NULLIF (sr.timeDuration, N''), N'0:0') AS timeDuration, loc.latitude AS l1, loc.longitude AS l2, 
                                                    sr.startLatitude AS l3, sr.startLongitude AS l4, ISNULL
                                                        ((SELECT        SUM(ps.totalQuantity) AS Expr1
                                                            FROM            dbo.tbl_ProductsSold AS ps INNER JOIN
                                                                                     dbo.tbl_item AS item ON ps.productId = item.Id
                                                            WHERE        (ps.salesId = sr.salesId) AND (item.isScheme = 'false')), 0) AS quantity, ISNULL
                                                        ((SELECT        SUM(ps.pieces * item.quantity) AS Expr1
                                                            FROM            dbo.tbl_ProductsSold AS ps INNER JOIN
                                                                                     dbo.tbl_item AS item ON ps.productId = item.Id
                                                            WHERE        (ps.salesId = sr.salesId) AND (item.isScheme = 'true')), 0) AS schemeQuantity, sr.status, CASE WHEN sr.status != 'DONE' THEN
                                                        (SELECT        TOP 1 date
                                                          FROM            tbl_SalesReport
                                                          WHERE        retailerId = rets.Id AND status = 'DONE'
                                                          ORDER BY salesId DESC) ELSE NULL END AS lastSaleDate, CASE WHEN sr.status != 'DONE' THEN CAST
                                                        ((SELECT        TOP 1 totalQuantity
                                                            FROM            tbl_SalesReport
                                                            WHERE        retailerId = rets.Id AND status = 'DONE'
                                                            ORDER BY salesId DESC) AS nvarchar(20)) ELSE '' END AS lastSale, COALESCE (rets.contactNo, N'') AS contactNo, sr.imagePath, h.asm
                          FROM            dbo.tbl_SalesReport AS sr LEFT OUTER JOIN
                                                    dbo.TBL_SALESPERSON AS person ON sr.personId = person.ID LEFT OUTER JOIN
                                                    dbo.tbl_retailers AS rets ON sr.retailerId = rets.Id LEFT OUTER JOIN
                                                    dbo.tbl_geoLocation AS loc ON loc.salesId = sr.salesId INNER JOIN
                                                    dbo.tbl_hierarchy AS h ON h.personname = person.PERSONNAME
                          WHERE        (sr.date = CAST(GETDATE() AS date)) AND (sr.deleted = 0) AND (sr.allowed = 1) OR
                                                    (sr.date = CAST(GETDATE() AS date)) AND (sr.deleted = 1) AND (sr.allowed = 0) OR
                                                    (sr.date = CAST(GETDATE() AS date)) AND (sr.deleted = 0) AND (sr.allowed = 0)) AS data