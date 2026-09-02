import csv,sys,collections,datetime
sys.path.insert(0,"/Users/damanpreetsingh/jivo-cli/jolly/engine")
from plan_units import pack_litres
B="/Users/damanpreetsingh/jivo-cli/jolly/out/aug01/"
lpc={}; onh=collections.defaultdict(float)
for r in csv.DictReader(open(B+"onhand-now.tsv"),delimiter="\t"):
    k=(r["WHS"],r["ITEMCODE"]); l,_=pack_litres(r["ITEMNAME"]); lpc[k]=l
    onh[k]=float(r["ONHAND"])
mv=collections.defaultdict(float)
for r in csv.DictReader(open(B+"daily-moves.tsv"),delimiter="\t"):
    k=(r["WHS"],r["ITEMCODE"]); mv[(k,r["D"])]+=float(r["MV"])
    if k not in lpc: lpc[k]=None
dates=sorted(set(d for (_,d) in mv.keys()))
# walk backwards from today's onhand
cur=dict(onh)
bal={}
today="2026-08-31"
allD=[(datetime.date(2026,6,1)+datetime.timedelta(days=i)).isoformat() for i in range(0,92)]
for d in reversed(allD):
    # opening of d = current - movements on/after d ; iterate day by day
    for k in set(list(cur.keys())+[kk for (kk,dd) in mv.keys() if dd==d]):
        cur[k]=cur.get(k,0.0)-mv.get((k,d),0.0)
    bal[d]=dict(cur)
def lit(state,whs=None):
    t=0
    for k,v in state.items():
        if whs and k[0]!=whs: continue
        l=lpc.get(k)
        if l: t+=v*l
    return t
print("OPENING BOOK BALANCE (litres) at BH-BT + BH-PF, FG+semiFG")
print(f"{'date':12s} {'BH-BT':>10s} {'BH-PF':>10s} {'TOTAL':>10s} {'%827k':>7s}")
for d in allD:
    if d<'2026-07-20' or d>'2026-08-10': continue
    s=bal[d]; a=lit(s,'BH-BT'); b=lit(s,'BH-PF'); t=a+b
    print(f"{d:12s} {a:>10,.0f} {b:>10,.0f} {t:>10,.0f} {t/827000*100:>6.1f}%")
mx=max(allD,key=lambda d: lit(bal[d]))
print()
print(f"MAX book over Jun1-Aug31: {lit(bal[mx]):,.0f} L on {mx}  = {lit(bal[mx])/827000*100:.1f}% of 827k")
import json
json.dump({d:{'BH-BT':lit(bal[d],'BH-BT'),'BH-PF':lit(bal[d],'BH-PF')} for d in allD},open(B+"book-series.json","w"))
