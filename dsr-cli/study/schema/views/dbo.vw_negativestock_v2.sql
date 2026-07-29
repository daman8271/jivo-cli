create view vw_negativestock_v2 as
select m1.distid, r.retailername, st.state, stockdate, i.itemname, boxes, 
cast(round(boxes*piecespercase,0) as int) stock, sum(sales.pieces) sales,
cast(round(boxes*piecespercase,0) as int) - isnull(sum(sales.pieces),0) balance,
min(sales.personname) personname
from tbl_monthlystock m1 join tbl_item i on m1.itemid=i.id join tbl_retailers r on r.id=m1.distid join tbl_states st on r.state=st.stateid
    left join
    (select s1.date, p1.productid, p1.pieces, s1.distid, sp.personname from tbl_salesreport s1, tbl_productssold p1, tbl_salesperson sp
    where s1.salesid=p1.salesid and s1.deletiondate is null and p1.deletiondate is null and
	date>='20230501' and sp.id=s1.personid) sales on sales.date>=stockdate and sales.productid=m1.itemid and sales.distid=m1.distid
where concat(year(stockdate),month(stockdate))=concat(year(getdate()),month(getdate())) and
stockdate=(select max(stockdate) from tbl_monthlystock m2 where m1.distid=m2.distid and m1.itemid=m2.itemid)
group by m1.distid, r.retailername, st.state, stockdate, i.itemname, boxes, cast(round(boxes*piecespercase,0) as int)