import csv, json, os, datetime, collections, html
T='taxonomy'
EXCL={'NPD1','NPD2','OTE'}
rows=list(csv.DictReader(open(f'{T}/detail_all.csv')))
tx=json.load(open(f'{T}/taxonomy.json'))
dmap={(m['co'],m['cc3'],m['cc4']):m for m in tx['mapping']}
dlab={d['key']:d for d in tx['departments']}
copy={c['key']:c for c in tx.get('copy',[])}

months=sorted({r['MTH'] for r in rows})
mi={m:i for i,m in enumerate(months)}
cos=['OIL','MART','BEV']; ci={c:i for i,c in enumerate(cos)}

# intern strings
S=[]; si={}
def s(x):
    if x not in si: si[x]=len(S); S.append(x)
    return si[x]

deptKeys=[d['key'] for d in sorted(tx['departments'],key=lambda x:x['order'])]
dki={k:i for i,k in enumerate(deptKeys)}

# ---- extend the agents' proven rule to combos their window never contained ----
# rule (derived + verified by the workflow): Dim4 decides for BackOff / Sales / Sales RE,
# Dim3 decides everywhere else.
FANOUT={'BackOff','Sales','Sales RE'}
d3=collections.Counter(); d4=collections.Counter()
ccl={}; subl={}
for (c3,c4),m in {(k[1],k[2]):v for k,v in dmap.items()}.items():
    ccl.setdefault(c3,m['cost_centre_label']); subl.setdefault(c4,m['sub_department'])
for k,m in dmap.items():
    _,c3,c4=k
    if c3 in FANOUT: d4[(c4,m['dept_key'])]+=1
    else: d3[(c3,m['dept_key'])]+=1
D3={}; D4={}
for (c3,dk),n in d3.items(): D3.setdefault(c3,dk)
for (c4,dk),n in d4.items(): D4.setdefault(c4,dk)
# cost centres that only ever appear outside the agents' window
D3.setdefault('NPD3','new_product_development'); D3.setdefault('R & D','new_product_development')
D3.setdefault('SUPPLY-C','supply_chain'); D3.setdefault('','untagged')
ccl.setdefault('NPD3','NPD 3'); ccl.setdefault('R & D','R & D'); ccl.setdefault('','Not cost-centre tagged')
subl.setdefault('SC-FCTRY','Supply Chain - Factory'); subl.setdefault('TAXATION','Taxation')
subl.setdefault('SOCIAL M','Social Media'); subl.setdefault('EXPORT','Export')
subl.setdefault('MT','Modern Trade'); subl.setdefault('GT','General Trade'); subl.setdefault('ROI','Rest of India')
subl.setdefault('CSD','Canteen Stores Dept'); subl.setdefault('HORECA','HoReCa')
subl.setdefault('DIG MKT','Digital Marketing'); subl.setdefault('','No Sub Budget')

def derive(co,c3,c4):
    if c3 in FANOUT:
        dk=D4.get(c4) or D3.get(c3) or 'untagged'
    else:
        dk=D3.get(c3) or 'untagged'
    return {'dept_key':dk,'sub_department':subl.get(c4,c4 or 'No Sub Budget'),
            'cost_centre_label':ccl.get(c3,c3 or 'Not tagged'),
            'basis':'team_rule_extended' if (c3 in D3 or c4 in D4) else 'inferred_new',
            'confidence':'medium'}

combos={}; extended=set(); guessed=set()
def comboIdx(r):
    k=(r['CO'],r['CC3'],r['CC4'])
    if k in combos: return combos[k][0]
    m=dmap.get(k)
    if not m:
        m=derive(*k)
        (extended if m['basis']=='team_rule_extended' else guessed).add(k)
    idx=len(combos)
    combos[k]=(idx,[ci[r['CO']], dki.get(m['dept_key'],0), s(m['sub_department']), s(m['cost_centre_label']),
                    1 if r['CC3'] in EXCL else 0, 0 if m['basis']=='inferred_new' else 1])
    return idx

accts={}
def acctIdx(r):
    k=r['ACCT']
    if k not in accts: accts[k]=(len(accts),[s(k),s(r['ANAME'].strip())])
    return accts[k][0]

facts=[]
for r in rows:
    facts += [comboIdx(r), acctIdx(r), mi[r['MTH']], int(r['NET']), int(r['TXNS'])]

# per-department share of money whose department was our guess, not the team's
g=collections.defaultdict(float); a=collections.defaultdict(float)
for r in rows:
    if r['CC3'] in EXCL: continue
    k=(r['CO'],r['CC3'],r['CC4'])
    m=dmap.get(k) or derive(*k)
    v=abs(int(r['NET'])); a[m['dept_key']]+=v
    if m['basis']=='inferred_new': g[m['dept_key']]+=v

depts=[]
for d in sorted(tx['departments'],key=lambda x:x['order']):
    k=d['key']; tot=a[k]; amt=g[k]; sh=amt/tot if tot else 0
    depts.append({'key':k,'label':html.unescape(d['label']),'order':d['order'],
        'one_liner':copy.get(k,{}).get('one_liner',''),'contains':copy.get(k,{}).get('contains',''),
        'flag':'unruled' if sh>=.9 else ('partly' if (amt>=5_000_000 or sh>.2) else ''),
        'flagAmt':round(amt)})

data={'months':months,'cos':cos,'S':S,
      'combos':[v[1] for k,v in sorted(combos.items(),key=lambda x:x[1][0])],
      'accts':[v[1] for k,v in sorted(accts.items(),key=lambda x:x[1][0])],
      'facts':facts,'depts':depts,'deptKeys':deptKeys,
      'recon':json.load(open('recon.json')),
      'pulled':datetime.datetime.now().strftime('%d %b %Y, %H:%M IST'),
      'lastComplete':'2026-07','partial':'2026-08','openFrom':'2025-04'}

html_out=open('tpl.html').read().replace('__DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/'))
html_out=html_out.replace('__JS__',open('tree.js').read())
open('index.html','w').write(html_out)
tot=sum(facts[i+3] for i in range(0,len(facts),5))
print(f"{len(months)} months {months[0]}..{months[-1]} | {len(facts)//5} facts | {len(combos)} combos | "
      f"{len(accts)} accounts | {len(S)} strings | all-time net {tot:,} | html {len(html_out):,}")
print(f"mapping: {len(dmap)} from the agents, {len(extended)} extended by their rule, {len(guessed)} pure guesses")
if guessed: print("  guessed:",sorted(guessed))
