import csv, sys, os
sys.path.insert(0, "/Users/damanpreetsingh/jivo-cli/jolly/engine")
from plan_units import pack_litres

rows=[]
with open("/Users/damanpreetsingh/jivo-cli/jolly/out/aug01/fg-rewind-raw.tsv") as fh:
    rd=csv.DictReader(fh, delimiter="\t")
    for r in rd:
        pcs=float(r["PCS_OPEN_0801"])
        lpc,how=pack_litres(r["ITEMNAME"])
        rows.append(dict(whs=r["WHS"],code=r["ITEMCODE"],name=r["ITEMNAME"],grp=r["GRP"],
                         onhand_now=float(r["ONHAND_NOW"]),move=float(r["MOVE_SINCE_0801"]),
                         pcs=pcs,lpc=lpc,how=how,
                         litres=(pcs*lpc if lpc is not None else None)))

def rep(label, sel):
    p=sum(r["pcs"] for r in sel)
    l=sum(r["litres"] for r in sel if r["litres"] is not None)
    unp=[r for r in sel if r["lpc"] is None and r["pcs"]!=0]
    neg=[r for r in sel if r["pcs"]<0]
    print(f"{label:34s} items={len(sel):4d} pcs={p:>14,.0f} litres={l:>14,.1f}  unparsed_items={len(unp)} neg_rows={len(neg)}")
    return p,l

print("=== OPENING OF 1 AUGUST 2026 (rewind: OnHand_now - OINM net where DocDate>='2026-08-01') ===")
nz=[r for r in rows if r["pcs"]!=0]
tot_p=tot_l=0
for whs in ("BH-BT","BH-PF"):
    for grp,gn in (("102","FINISHED"),("115","SEMI-FIN")):
        sel=[r for r in nz if r["whs"]==whs and r["grp"]==grp]
        if sel: rep(f"  {whs} grp{grp} {gn}", sel)
    sel=[r for r in nz if r["whs"]==whs]
    p,l=rep(f"{whs} TOTAL", sel); tot_p+=p; tot_l+=l
print(f"{'GRAND TOTAL BH-BT+BH-PF':34s} pcs={tot_p:>18,.0f} litres={tot_l:>14,.1f}")

print("\n--- unparsed SKU names holding pieces on 1 Aug (litres NOT counted) ---")
for r in sorted([r for r in nz if r["lpc"] is None], key=lambda x:-abs(x["pcs"])):
    print(f"  {r['whs']} {r['code']:12s} {r['pcs']:>10,.0f} pcs  {r['name'][:60]}")

print("\n--- NEGATIVE opening balances (impossible; rewind artefact) ---")
for r in sorted([r for r in nz if r["pcs"]<0], key=lambda x:x["pcs"])[:20]:
    print(f"  {r['whs']} {r['code']:12s} {r['pcs']:>10,.0f} pcs  now={r['onhand_now']:>10,.0f} move={r['move']:>10,.0f}  {r['name'][:45]}")

with open("/Users/damanpreetsingh/jivo-cli/jolly/out/aug01/fg-by-item.csv","w",newline="") as fh:
    w=csv.DictWriter(fh, fieldnames=["whs","code","name","grp","onhand_now","move","pcs","lpc","how","litres"])
    w.writeheader()
    for r in sorted(rows,key=lambda x:(x["whs"],-(x["litres"] or 0))): w.writerow(r)
