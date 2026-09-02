import csv,json,sys,collections,datetime
sys.path.insert(0,"/Users/damanpreetsingh/jivo-cli/jolly/engine")
from plan_units import pack_litres
B="/Users/damanpreetsingh/jivo-cli/jolly/out/aug01/"
exitmap=json.load(open('/tmp/claude-501/-Users-damanpreetsingh-jivo-cli-jolly/fa970459-e8af-4540-91f8-0d51d51cf2e9/scratchpad/exitmap.json'))
docs=collections.defaultdict(lambda: dict(litres=0.0,date=None,whs=set()))
def load(fn,cols):
    for r in csv.DictReader(open(B+fn),delimiter="\t"):
        dn=str(r[cols[0]]).strip(); l,_=pack_litres(r[cols[3]]); q=float(r[cols[4]])
        d=docs[(dn,r[cols[5]])]; d["date"]=r[cols[1]]; d["whs"].add(r[cols[2]])
        if l is not None: d["litres"]+=q*l
load("inv-jun-jul.tsv",["DOCNUM","DOCDATE","WHS","ITEMNAME","QTY","SRC"])
load("wtr-jun-jul.tsv",["DOCNUM","DOCDATE","WHS","ITEMNAME","QTY","SRC"])
load("docs-aug.tsv",["DOCNUM","DOCDATE","WHS","ITEMNAME","QTY","SRC"])
book=json.load(open(B+"book-series.json"))
allD=[(datetime.date(2026,7,1)+datetime.timedelta(days=i)).isoformat() for i in range(0,62)]
print("ADVERSARIAL TEST OF THE ADDITIVE MODEL  (book + standing vs the 923,000 L ABSOLUTE pallet peak)")
print(f"{'date':12s} {'book':>9s} {'standing':>9s} {'book+std':>9s} {'%peak923':>9s} {'VERDICT':>10s}")
over=0; rows=[]
for d in allD:
    if d not in book: continue
    bk=book[d]['BH-BT']+book[d]['BH-PF']
    st=0.0
    for (dn,src),v in docs.items():
        if v["date"] and v["date"] < d:              # booked out before this morning
            da=exitmap.get(dn,"__NOREC__")
            if da=="__NOREC__": continue             # unknown, excluded from the measured pile
            if da is None or da[:10] >= d: st+=v["litres"]   # truck had not gone by this morning
    tot=bk+st; pct=tot/923000*100
    v="IMPOSSIBLE" if tot>923000 else ""
    if tot>923000: over+=1
    rows.append((d,bk,st,tot,pct,v))
    if d>='2026-07-25' and d<='2026-08-25' or v:
        print(f"{d:12s} {bk:>9,.0f} {st:>9,.0f} {tot:>9,.0f} {pct:>8.1f}% {v:>10s}")
print()
print(f"Days where book+standing EXCEEDS the 923,000 L absolute pallet peak: {over} of {len(rows)}")
print(f"Max book+standing: {max(r[3] for r in rows):,.0f} L = {max(r[4] for r in rows):.1f}% of peak")
print(f"Max book ALONE   : {max(r[1] for r in rows):,.0f} L = {max(r[1] for r in rows)/923000*100:.1f}% of peak")
json.dump({r[0]:{'book':r[1],'standing':r[2]} for r in rows},open(B+"phys-series.json","w"))
