create view vw_negativestock_v3_cgs as
select distid, distname, state, productid, itemname, sum(opening) opening, sum(prim) prim, sum(sales) sales, sum(total) total,
       max(personname) personname from (
select distid, (select retailername from tbl_retailers r where r.id=datum.distid
               ) distname, (select st.state from tbl_retailers r, tbl_states st where r.id=datum.distid and r.state=st.stateid
			               ) state, productid, (select itemname from tbl_item i where i.id=datum.productid
						                       ) itemname, 
	   (case when factor='Opening' then boxes else 0 end) opening, 
       (case when factor='Primary' then boxes else 0 end) prim, 
	   (case when factor='Secondary' then boxes else 0 end) sales,
	   (case when factor='Secondary' then -boxes else boxes end) total,
	   (personname) personname
from (
select distid,stockdate,productid,1.0*boxes boxes,'Opening' factor, '' personname
from tbl_distributorStock ds, tbl_diststockproducts dsp
where ds.diststockid = dsp.distStockId and
      ds.stockDate = (select max(stockdate)
                      from tbl_distributorStock ds2
                      where ds2.distid = ds.distid and
					  ds2.stockdate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) and
	  ds.stockDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
union
select to_retailerid, date, itemid, quantity, 'Primary', ''
from tbl_primary_sales p1
where date >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1) and date >= (select max(stockdate)
                                                                               from tbl_distributorStock ds2
                                                                               where ds2.distid = to_retailerid)
union
select s.distid, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1), p.productid, sum(1.0*p.pieces/i.piecespercase), 'Secondary',
       max(personname)
from tbl_salesreport s, tbl_productssold p, tbl_item i
where s.salesid=p.salesid and s.deletiondate is null and p.deletiondate is null and i.deleted=0 and
      i.id=p.productid and s.date>'20230401' and s.date >= (select max(stockdate)
                                                            from tbl_distributorStock ds2
                                                            where ds2.distid = s.distid)
group by s.distid, p.productid) datum) x
group by distid, distname, state, productid, itemname