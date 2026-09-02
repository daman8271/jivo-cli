import subprocess, csv, io, os
ENV=os.environ.get("HANA_ENV", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../connections/hana-office-bridge.env"))
def q(sql):
    r=subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../hana-sql/hana-sql"),"-env",ENV,"-csv",sql],capture_output=True,text=True)
    if r.stdout.startswith("QUERY ERROR") or r.returncode!=0: print("ERR",r.stdout[:300],r.stderr[:200]); return []
    return list(csv.reader(io.StringIO(r.stdout)))[1:]
S3=["JIVO_OIL_HANADB","JIVO_MART_HANADB","JIVO_BEVERAGES_HANADB"]
def union(tpl): return " UNION ALL ".join(tpl.format(S=S, SHORT=S[5:9].rstrip('_')) for S in S3)
def show(title, rows, hdr):
    print(f"\n### {title}"); print("\t".join(hdr))
    for r in rows: print("\t".join(r))

inner_pch = """SELECT '{SHORT}' AS B, h."DocEntry" AS DE, h."DocType" AS DT, h."UserSign" AS US, h."DocTotal" AS AMT,
  (SELECT MAX(CASE WHEN l."BaseType"=20 THEN 'GRPO' WHEN l."BaseType"=22 THEN 'PO' WHEN l."BaseType"=21 THEN 'GoodsReturn' ELSE 'standalone' END) FROM {S}.PCH1 l WHERE l."DocEntry"=h."DocEntry") AS BASED,
  g."GroupName" AS G
  FROM {S}.OPCH h JOIN {S}.OCRD c ON c."CardCode"=h."CardCode" LEFT JOIN {S}.OCRG g ON g."GroupCode"=c."GroupCode" WHERE h."CreateDate">='%s'""" % SINCE
show("OPCH A/P: book x DocType x based_on", q(f"""SELECT B, DT, BASED, COUNT(*), SUM(AMT) FROM ({union(inner_pch)}) GROUP BY B, DT, BASED ORDER BY B, COUNT(*) DESC"""), ["book","DocType(I=item,S=service)","based_on","n","amount"])
show("OPCH A/P: DocType x based_on x USER (top 40)", q(f"""SELECT DT, BASED, u."USER_CODE", u."U_NAME", COUNT(*) FROM ({union(inner_pch)}) x LEFT JOIN JIVO_OIL_HANADB.OUSR u ON u."USERID"=x.US GROUP BY DT, BASED, u."USER_CODE", u."U_NAME" ORDER BY COUNT(*) DESC LIMIT 40"""), ["DocType","based_on","user","name","n"])
show("OPCH A/P: vendor group x DocType x based_on", q(f"""SELECT G, DT, BASED, COUNT(*), SUM(AMT) FROM ({union(inner_pch)}) GROUP BY G, DT, BASED ORDER BY COUNT(*) DESC"""), ["vendor_group","DocType","based_on","n","amount"])
show("OPCH TRANSPORTER group: who keys it, per book", q(f"""SELECT B, u."USER_CODE", u."U_NAME", COUNT(*), SUM(AMT) FROM ({union(inner_pch)}) x LEFT JOIN JIVO_OIL_HANADB.OUSR u ON u."USERID"=x.US WHERE G='TRANSPORTER' GROUP BY B, u."USER_CODE", u."U_NAME" ORDER BY COUNT(*) DESC"""), ["book","user","name","n","amount"])
show("OPCH TRANSPORTER: top vendors", q(f"""SELECT CN, COUNT(*), SUM(AMT) FROM ({union('SELECT c."CardName" AS CN, h."DocTotal" AS AMT FROM {S}.OPCH h JOIN {S}.OCRD c ON c."CardCode"=h."CardCode" LEFT JOIN {S}.OCRG g ON g."GroupCode"=c."GroupCode" WHERE h."CreateDate">=\'%s\' AND g."GroupName"=\'TRANSPORTER\''%SINCE)}) GROUP BY CN ORDER BY COUNT(*) DESC LIMIT 15"""), ["transporter","n","amount"])

inner_inv = """SELECT '{SHORT}' AS B, h."DocType" AS DT, h."UserSign" AS US,
  (SELECT MAX(CASE WHEN l."BaseType"=15 THEN 'delivery' WHEN l."BaseType"=17 THEN 'order' ELSE 'standalone' END) FROM {S}.INV1 l WHERE l."DocEntry"=h."DocEntry") AS BASED
  FROM {S}.OINV h WHERE h."CreateDate">='%s'""" % SINCE
show("OINV A/R: book x DocType x based_on", q(f"""SELECT B, DT, BASED, COUNT(*) FROM ({union(inner_inv)}) GROUP BY B, DT, BASED ORDER BY B, COUNT(*) DESC"""), ["book","DocType","based_on","n"])
show("OINV A/R: user (top 15)", q(f"""SELECT u."USER_CODE", u."U_NAME", COUNT(*) FROM ({union(inner_inv)}) x LEFT JOIN JIVO_OIL_HANADB.OUSR u ON u."USERID"=x.US GROUP BY u."USER_CODE", u."U_NAME" ORDER BY COUNT(*) DESC LIMIT 15"""), ["user","name","n"])

# ODRF A/P drafts (ObjType 18): GRPO-based or not, by user
inner_drf = """SELECT '{SHORT}' AS B, d."UserSign" AS US, d."DocType" AS DT,
  (SELECT MAX(CASE WHEN l."BaseType"=20 THEN 'GRPO' WHEN l."BaseType"=22 THEN 'PO' ELSE 'standalone' END) FROM {S}.DRF1 l WHERE l."DocEntry"=d."DocEntry") AS BASED
  FROM {S}.ODRF d WHERE d."CreateDate">='%s' AND d."ObjType"='18'""" % SINCE
show("ODRF A/P-invoice DRAFTS: DocType x based_on x user", q(f"""SELECT DT, BASED, u."USER_CODE", u."U_NAME", COUNT(*) FROM ({union(inner_drf)}) x LEFT JOIN JIVO_OIL_HANADB.OUSR u ON u."USERID"=x.US GROUP BY DT, BASED, u."USER_CODE", u."U_NAME" ORDER BY COUNT(*) DESC LIMIT 25"""), ["DocType","based_on","user","name","n"])

# payments: who
show("OVPM outgoing payments by user x DocType", q(f"""SELECT u."USER_CODE", u."U_NAME", DT, SUM(N) FROM ({union('SELECT "UserSign" AS US, "DocType" AS DT, COUNT(*) AS N FROM {S}.OVPM WHERE "CreateDate">=\'%s\' GROUP BY "UserSign","DocType"'%SINCE)}) x LEFT JOIN JIVO_OIL_HANADB.OUSR u ON u."USERID"=x.US GROUP BY u."USER_CODE", u."U_NAME", DT ORDER BY SUM(N) DESC LIMIT 15"""), ["user","name","DocType","n"])
show("ORCT incoming payments by user x DocType", q(f"""SELECT u."USER_CODE", u."U_NAME", DT, SUM(N) FROM ({union('SELECT "UserSign" AS US, "DocType" AS DT, COUNT(*) AS N FROM {S}.ORCT WHERE "CreateDate">=\'%s\' GROUP BY "UserSign","DocType"'%SINCE)}) x LEFT JOIN JIVO_OIL_HANADB.OUSR u ON u."USERID"=x.US GROUP BY u."USER_CODE", u."U_NAME", DT ORDER BY SUM(N) DESC LIMIT 15"""), ["user","name","DocType","n"])
# OVPM: how many invoices per payment (batch size) 
show("OVPM: invoices settled per outgoing payment (distribution)", q(f"""SELECT K, COUNT(*) FROM (SELECT CASE WHEN N=0 THEN '0 (on-account)' WHEN N=1 THEN '1' WHEN N<=5 THEN '2-5' WHEN N<=20 THEN '6-20' ELSE '21+' END AS K FROM ({union('SELECT h."DocEntry", (SELECT COUNT(*) FROM {S}.VPM2 v WHERE v."DocNum"=h."DocEntry") AS N FROM {S}.OVPM h WHERE h."CreateDate">=\'%s\''%SINCE)})) GROUP BY K ORDER BY K"""), ["invoices_per_payment","n_payments"])
# Manual JE: what are they — top account pairs? Just memo keywords
show("Manual JEs (TransType 30): sample memos (top 25)", q(f"""SELECT M, COUNT(*) FROM ({union('SELECT UPPER(LEFT("Memo",40)) AS M FROM {S}.OJDT WHERE "CreateDate">=\'%s\' AND "TransType"=\'30\''%SINCE)}) GROUP BY M ORDER BY COUNT(*) DESC LIMIT 25"""), ["memo","n"])
