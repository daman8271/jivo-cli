create view vw_salesreportpromoter as
select salesid, date, personid, retailerid, deleted, deletedby, deletiondate, createdby, createdon,
       timestamp, status, imagepath, remarks, stateid, zoneid, areaid, subareaid, distid, personname, retailername, 
	   state, zone, area, subarea, distributor, imagepath1, imagepath2
from tbl_salesreportpromoter a
where salesid=(select max(salesid)
               from tbl_salesreportpromoter b
			   where a.date=b.date and
					 a.personid=b.personid and
					 a.retailerid=b.retailerid and 
					 deletiondate is null)