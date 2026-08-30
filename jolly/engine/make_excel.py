#!/usr/bin/env python3
"""Build the one-sheet August buy list. Daman's format: yellow inputs, grey live formulas."""
import csv, os, openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side

HELD={"FG0000451":"SKU not ready (70 pcs)","FG0000452":"SKU not ready",
      "FG0000448":"held — Manav owns the recipe"}
def f(v):
    try: return float(v)
    except: return 0.0
comp=list(csv.DictReader(open("out/plan-aug-components.csv")))
plan=list(csv.DictReader(open("out/plan-aug-resolved.csv")))
recon=list(csv.DictReader(open("reference/reconstructed-boms.csv")))
blend=list(csv.DictReader(open("reference/blend-recipes.csv")))
live=[r for r in plan if r["code"] not in HELD]
PLAN_KL=sum(f(r["plan_kl"]) for r in live)
PIECES=sum(f(r["pieces"]) for r in live if r["pieces"])
oil=sorted([r for r in comp if r["code"].startswith("RM") and r["declared"]=="BUY"],key=lambda r:-f(r["required"]))
bl=sorted([r for r in comp if r["declared"]=="BLEND"],key=lambda r:-f(r["required"]))
mk=sorted([r for r in comp if r["declared"]=="MAKE" and r["code"].startswith("RM")],key=lambda r:-f(r["required"]))
pack=sorted([r for r in comp if r["code"].startswith("PM")],key=lambda r:-f(r["required"]))

wb=openpyxl.Workbook(); ws=wb.active; ws.title="AUG PLAN"
Y=PatternFill("solid",fgColor="FFF2CC"); G=PatternFill("solid",fgColor="F2F2F2")
B=PatternFill("solid",fgColor="E7EEF7"); A=PatternFill("solid",fgColor="FCE4D6")
HDR=Font(bold=True,size=12); BIG=Font(bold=True,size=12,color="1F6E43")
RED=Font(bold=True,size=11,color="B00000"); NOTE=Font(italic=True,size=9,color="808080")
SUB=Font(bold=True,size=9,color="404040")
t=Side(style="thin",color="BFBFBF"); BOX=Border(t,t,t,t); M0="#,##0"; M2="#,##0.00"
def put(r,a=None,b=None,c=None,fill=None,fmt=None,fa=None,fb=None):
    if a is not None:
        x=ws.cell(r,1,a)
        if fa: x.font=fa
    if b is not None:
        y=ws.cell(r,2,b); y.border=BOX
        if fill: y.fill=fill
        if fmt: y.number_format=fmt
        if fb: y.font=fb
    if c is not None: ws.cell(r,3,c).font=Font(size=9,color="595959")
def head(r,*cols):
    for i,x in enumerate(cols):
        c=ws.cell(r,i+1,x); c.font=SUB; c.fill=B
    return r+1

r=1
ws.cell(r,1,"JIVO OIL — AUGUST 2026 PLAN, EXPLODED TO WHAT WE BUY").font=Font(bold=True,size=14); r+=1
ws.cell(r,1,"FINAL (2), By Gurvinder Vj 03.08.2026 · built 2026-08-29").font=NOTE; r+=2
ws.cell(r,1,"INPUTS — edit the yellow cells").font=HDR; r+=1
put(r,"Plan (sale-tonnes)",PLAN_KL,"FINAL (2), less 2 SKUs not ready. 1 T = 1,000 L",Y,M2); P=f"B{r}"; r+=1
put(r,"Oil density",910,"g/L — yours, confirmed by SAP's own 12 KGS BOM",Y,M0); D=f"B{r}"; r+=1
put(r,"Finished pieces",PIECES,"bottles / pouches / tins / jars",Y,M0); PC=f"B{r}"; r+=1
r+=1
ws.cell(r,1,"1) THE PLAN").font=HDR; r+=1
put(r,"Litres to fill",f"={P}*1000","litres",G,M0,fb=BIG); L=f"B{r}"; r+=1
put(r,"Purchase-tonnes",f"={P}*1000*{D}/1000000","1 T = 1,000 kg",G,M2,fb=BIG); r+=1
put(r,"Order in SAP as",f"={P}*1000/(1000000/{D})","MTS — POR1.NumPerMsr = 1,098.9 L/MT",G,M2); r+=1
r+=1
ws.cell(r,1,"2) OIL TO BUY").font=HDR; r=head(r+1,"ITEM","QTY","UOM · CODE")
o1=r
for x in oil: put(r,x["name"][:44],f(x["required"]),f"{x['uom']} · {x['code']}",G,M0); r+=1
o2=r-1
put(r,"TOTAL OIL (litres only)",f'=SUMIF(C{o1}:C{o2},"LTR*",B{o1}:B{o2})',"KGS excluded — different unit",G,M0,fa=Font(bold=True),fb=BIG); OT=f"B{r}"; r+=1
put(r,"  = purchase-tonnes",f"={OT}*{D}/1000000",None,G,M2); r+=1
put(r,"  vs plan litres",f"={OT}/{L}","just over 100% = blending loss. The sanity check.",G,"0.00%",fb=BIG); r+=1
r+=1
ws.cell(r,1,"3) THE TWO OILS WE BLEND — not bought, made here").font=HDR; r+=1
ws.cell(r,1,"Neither has a recipe in SAP. These came from what was actually issued to their production orders.").font=NOTE; r+=1
for x in bl:
    put(r,x["name"][:44],f(x["required"]),f"LTR · {x['code']} · we make this",A,M0,fa=Font(bold=True,size=10)); r+=1
    for y in [z for z in blend if z["blend"]==x["code"]]:
        put(r,"     "+y["note"][:38],f(y["per_litre"]),f"per litre · {y['component']}",None,"0.0%"); r+=1
r+=1
ws.cell(r,1,f"4) PACKAGING TO BUY — {len(pack)} items").font=HDR; r=head(r+1,"ITEM","QTY","UOM · CODE")
k1=r
for x in pack: put(r,x["name"][:44],f(x["required"]),f"{x['uom']} · {x['code']}",G,M0); r+=1
k2=r-1
put(r,"TOTAL PACKAGING",f"=SUM(B{k1}:B{k2})","pieces",G,M0,fa=Font(bold=True),fb=BIG); r+=1
put(r,"  per finished piece",f"=SUM(B{k1}:B{k2})/{PC}",None,G,M2); r+=1
r+=1
ws.cell(r,1,"5) RECIPES I REBUILT — SAP has none for these").font=HDR; r+=1
for fg in sorted({x["father"] for x in recon}):
    if fg in HELD: continue
    nm=next((p["sku"] for p in plan if p["code"]==fg),fg)
    ws.cell(r,1,f"{fg}  {nm}").font=Font(bold=True,size=10); r+=1
    for x in [y for y in recon if y["father"]==fg]:
        put(r,"   "+x["child"],f(x["per_piece"]),f"from {x['source_template']} · {x['note']}",A,"#,##0.0000"); r+=1
r+=1
ws.cell(r,1,"6) HELD — nothing ordered").font=HDR; r+=1
for c_,why in HELD.items():
    nm=next((p["sku"] for p in plan if p["code"]==c_),c_)
    kl=next((f(p["plan_kl"]) for p in plan if p["code"]==c_),0)
    put(r,f"{c_}  {nm[:36]}",kl,f"sale-tonnes · {why}",G,M2,fb=RED); r+=1
r+=1
ws.cell(r,1,"NOTES").font=SUB; r+=1
for n in ["Grey = live formula off the 3 yellow inputs. Change the density or plan total and everything recalculates.",
          "Amber = built by me, not by SAP. The 2 blend recipes come from real production orders; the rebuilt BOMs from lookalike products.",
          "9 SAP recipes are written per BOX but labelled per BOTTLE — corrected here, still wrong in SAP."]:
    ws.cell(r,1,n).font=NOTE; r+=1
ws.column_dimensions['A'].width=48; ws.column_dimensions['B'].width=16
ws.column_dimensions['C'].width=54; ws.sheet_view.showGridLines=False
ws.freeze_panes="A5"
out=os.path.expanduser("~/Downloads/JIVO-Aug-Plan-Buy-List.xlsx"); wb.save(out)
litres=PLAN_KL*1000
oil_l=sum(f(x["required"]) for x in oil if x["uom"].startswith("LTR"))
pk=sum(f(x["required"]) for x in pack)
print(f"saved {out}  rows={ws.max_row}\n")
print(f"  litres to fill     {litres:>13,.0f}")
print(f"  purchase-tonnes    {litres*910/1e6:>13,.1f}")
print(f"  OIL to buy         {oil_l:>13,.0f} L = {oil_l*910/1e6:,.1f} T")
print(f"  vs plan            {oil_l/litres:>13.4f}")
print(f"  PACKAGING          {pk:>13,.0f} pcs / {len(pack)} items")
print(f"  blends exploded    {len(bl)}   rebuilt BOMs {len({x['father'] for x in recon})-len(HELD)}   held {len(HELD)}")
