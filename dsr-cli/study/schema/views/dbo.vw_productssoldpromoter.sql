create view vw_productssoldpromoter as
select id, salesid, productid, pieces, deleted, deletedby, deletiondate, createdby, createdon,
       productname, productquantity, totalquantity, cost, totalcost, openingstock, closingstock,
	   samplestock
from tbl_productssoldpromoter b
where id = (select min(id)
            from tbl_productssoldpromoter c where c.salesid=b.salesid and b.productid=c.productid)