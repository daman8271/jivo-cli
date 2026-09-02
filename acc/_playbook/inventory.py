import subprocess, sys, os, csv, io
ENV=os.environ.get("HANA_ENV", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../connections/hana-office-bridge.env"))
SINCE="2026-05-25"
OUT=os.path.dirname(os.path.abspath(__file__))
def q(sql):
    r=subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../hana-sql/hana-sql"),"-env",ENV,"-csv",sql],capture_output=True,text=True)
    if r.returncode!=0 or r.stdout.startswith("QUERY ERROR"):
        raise SystemExit(f"ERR: {r.stdout[:500]} {r.stderr[:500]}")
    return list(csv.reader(io.StringIO(r.stdout)))
rows_all=[]
for S in ["JIVO_OIL_HANADB","JIVO_MART_HANADB","JIVO_BEVERAGES_HANADB"]:
    tabs=[r[0] for r in q(f"""SELECT t.TABLE_NAME FROM SYS.M_TABLES t WHERE t.SCHEMA_NAME='{S}' AND t.TABLE_NAME LIKE 'O%' AND t.RECORD_COUNT>0
      AND t.TABLE_NAME IN (SELECT TABLE_NAME FROM SYS.TABLE_COLUMNS WHERE SCHEMA_NAME='{S}' AND COLUMN_NAME='UserSign')
      AND t.TABLE_NAME IN (SELECT TABLE_NAME FROM SYS.TABLE_COLUMNS WHERE SCHEMA_NAME='{S}' AND COLUMN_NAME='CreateDate')
      AND t.TABLE_NAME IN (SELECT TABLE_NAME FROM SYS.TABLE_COLUMNS WHERE SCHEMA_NAME='{S}' AND COLUMN_NAME='ObjType')
      AND t.TABLE_NAME NOT IN ('OBTN','OOOITM')""")[1:]]
    parts=[f"""SELECT '{T}' AS TBL, "UserSign" AS US, COUNT(*) AS N FROM {S}.{T} WHERE "CreateDate" >= '{SINCE}' GROUP BY "UserSign" """ for T in tabs]
    sql=f"""SELECT x.TBL, x.US, u."USER_CODE", u."U_NAME", x.N FROM ({' UNION ALL '.join(parts)}) x LEFT JOIN {S}.OUSR u ON u."USERID"=x.US ORDER BY x.TBL, x.N DESC"""
    res=q(sql)[1:]
    for r in res: rows_all.append([S]+r)
    print(S, len(tabs), "tables,", len(res), "rows")
with open(f"{OUT}/inventory_90d.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["schema","table","usersign","user_code","user_name","n"]); w.writerows(rows_all)
