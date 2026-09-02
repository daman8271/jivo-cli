import csv,json,sys,collections
sys.path.insert(0,"/Users/damanpreetsingh/jivo-cli/jolly/engine")
from plan_units import pack_litres
BASE="/Users/damanpreetsingh/jivo-cli/jolly/out/aug01/"
exitmap=json.load(open('/tmp/claude-501/-Users-damanpreetsingh-jivo-cli-jolly/fa970459-e8af-4540-91f8-0d51d51cf2e9/scratchpad/exitmap.json'))
docs=collections.defaultdict(lambda: dict(litres=0.0,pcs=0.0,date=None,src=None,whs=set(),card=''))
for fn,has_card in (("inv-jun-jul.tsv",True),("wtr-jun-jul.tsv",False)):
    for r in csv.DictReader(open(BASE+fn),delimiter="\t"):
        dn=str(r["DOCNUM"]).strip(); l,_=pack_litres(r["ITEMNAME"]); q=float(r["QTY"])
        d=docs[(dn,r["SRC"])]
        d["date"]=r["DOCDATE"]; d["src"]=r["SRC"]; d["whs"].add(r["WHS"])
        if has_card: d["card"]=r.get("CARDNAME","")
        d["pcs"]+=q
        if l is not None: d["litres"]+=q*l

CUT="2026-08-01"
rows=[]
for (dn,src),d in docs.items():
    da=exitmap.get(dn,"__NOREC__")
    if da=="__NOREC__": cls="NO_GATE_RECORD"
    elif da is None: cls="STANDING_never_dispatched"
    elif da[:10] < CUT: cls="GONE_before_1Aug"
    else: cls="STANDING_dispatched_later"
    rows.append(dict(docnum=dn,src=src,docdate=d["date"],card=d["card"],whs="+".join(sorted(d["whs"])),
                     pcs=round(d["pcs"],1),litres=round(d["litres"],1),dispatched_at=(da or ""),cls=cls))

def month(x): return x["docdate"][:7]
print("=== DOCUMENTS OUT OF BH-BT/BH-PF, DocDate <= 2026-07-31 ===")
print(f"{'cohort':10s} {'class':28s} {'docs':>5s} {'litres':>12s}")
for m in sorted(set(month(r) for r in rows)):
    sub=[r for r in rows if month(r)==m]
    for c in ("GONE_before_1Aug","STANDING_dispatched_later","STANDING_never_dispatched","NO_GATE_RECORD"):
        s=[r for r in sub if r["cls"]==c]
        if s: print(f"{m:10s} {c:28s} {len(s):>5d} {sum(x['litres'] for x in s):>12,.0f}")
    print(f"{m:10s} {'-- cohort total':28s} {len(sub):>5d} {sum(x['litres'] for x in sub):>12,.0f}")

meas=[r for r in rows if r["cls"].startswith("STANDING")]
unk=[r for r in rows if r["cls"]=="NO_GATE_RECORD"]
gone=[r for r in rows if r["cls"]=="GONE_before_1Aug"]
print()
print(f"MEASURED STANDING on 1 Aug morning : {sum(r['litres'] for r in meas):>12,.0f} L  ({len(meas)} docs)")
print(f"  of which July docs               : {sum(r['litres'] for r in meas if month(r)=='2026-07'):>12,.0f} L")
print(f"  of which 31-Jul docs             : {sum(r['litres'] for r in meas if r['docdate']=='2026-07-31'):>12,.0f} L")
print(f"UNKNOWN (no gate record)           : {sum(r['litres'] for r in unk):>12,.0f} L  ({len(unk)} docs)")
print(f"GONE before 1 Aug (measured)       : {sum(r['litres'] for r in gone):>12,.0f} L  ({len(gone)} docs)")
tot=sum(r['litres'] for r in rows)
print(f"litre gate-match rate (Jun-Jul)    : {(tot-sum(r['litres'] for r in unk))/tot*100:.1f}%")

# intercompany split
IC={'CUSTA000001','CUSTA000002','CUSTA000003','CUSTA000004','CUSTA000606','CUSTA000827','CUSTA000906','CUSTA001099','CUSTA001113'}
print()
print("STANDING by source door / type:")
for src in ("INVOICE","TRANSFER"):
    s=[r for r in meas if r["src"]==src]
    print(f"  {src:10s} {len(s):>4d} docs  {sum(x['litres'] for x in s):>12,.0f} L")
print()
print("STANDING by warehouse:")
for w in sorted(set(r["whs"] for r in meas)):
    s=[r for r in meas if r["whs"]==w]
    print(f"  {w:14s} {len(s):>4d} docs  {sum(x['litres'] for x in s):>12,.0f} L")

with open(BASE+"standing-detail.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader()
    for r in sorted(rows,key=lambda x:(x["docdate"],x["docnum"])): w.writerow(r)
