import json,re
DENS=0.910  # kg per litre (oil) - house rule 910 g/L
def litres_per_piece(name):
    n=name.upper().replace('MLS','ML').replace('GMS','GM').replace('KGS','KG')
    n=re.sub(r'\(.*?\)','',n)                      # drop bracketed notes
    n=re.sub(r'\b\d+\s*(PCS|SET)\b','',n)          # drop case-config counts
    toks=[]
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(LTR|L\b|ML|GM|KG)',n):
        v=float(m.group(1)); u=m.group(2)
        if u in('LTR','L'): toks.append(v)
        elif u=='ML': toks.append(v/1000)
        elif u=='GM': toks.append(v/1000/DENS)
        elif u=='KG': toks.append(v/DENS)
    if not toks: return None,'NO SIZE TOKEN'
    if '+' in name and len(toks)>=2: return sum(toks[:2]),'combo=sum of 2'
    return toks[0],'first token'
rec=json.load(open('recon-prod-aug.json'))['results']
rows=[];bad=[];pack=0.0
for x in sorted(rec['sap_by_item'],key=lambda y:-y['sap_qty']):
    code=x['item_code'];nm=x['item_name'];q=x['sap_qty']
    if code.startswith('PM'):
        pack+=q; rows.append((code,nm,q,None,'PACKAGING - EXCLUDED',0)); continue
    L,how=litres_per_piece(nm)
    if L is None: bad.append((code,nm,q))
    rows.append((code,nm,q,L,how,(L or 0)*q))
tot=sum(r[5] for r in rows)
print(f'{"code":11} {"pieces":>11} {"L/pc":>8} {"litres":>13}  name')
for c,nm,q,L,how,lit in rows:
    print(f'{c:11} {q:>11.0f} {("%.4f"%L) if L else "     -":>8} {lit:>13.1f}  {nm[:52]}')
print()
print('TOTAL OIL LITRES (SAP OIGN into BH-PF, Aug 2026, Oil) =',f'{tot:,.0f}')
print('packaging pieces excluded =',f'{pack:,.0f}')
print('unparsed:',bad)
json.dump({r[0]:r[3] for r in rows if r[3]},open('lpp-map.json','w'))
