
CREATE view vw_attendance as
select s.personid, timestamp, '' s, (select top(1) CAST(DATEDIFF(minute, s.timeStamp, s1.timestamp) / 60 AS varchar(2)) + ':' + RIGHT('00' + CAST(DATEDIFF(minute, s.timeStamp, s1.timestamp) % 60 AS varchar(2)), 2)
                                     from tbl_salesreport s1
						             where s1.personid=s.personid and
									 s1.date=s.date
					                 order by timestamp desc
                                     ) workinghours
from tbl_salesreport s
where 
s.timestamp=(select min(timestamp) from tbl_salesreport s2
             where s2.personid=s.personid and s2.date=s.date)
union
select s.personid, timestamp, '' s, (select top(1) CAST(DATEDIFF(minute, s.timeStamp, s1.timestamp) / 60 AS varchar(2)) + ':' + RIGHT('00' + CAST(DATEDIFF(minute, s.timeStamp, s1.timestamp) % 60 AS varchar(2)), 2)
                                     from tbl_salespersonattendance s1
									 where s1.personid=s.personid and cast(s1.timestamp as date)=cast(s.timestamp as date) and
									       s1.status='EOD'
                                    ) workinghours
from tbl_salespersonattendance s, tbl_salesperson sp
where 
s.status='P' and s.personid=sp.id and sp.persontype like 'PROMOTER%'
