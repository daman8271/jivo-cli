 create view tbl_retailerstock_vw as
 select min(id) id, salesid, itemid, sum(stock) stock, min(stocktype) stocktype
 from tbl_retailerstock
 group by salesid, itemid