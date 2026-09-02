
const D = JSON.parse(document.getElementById('payload').textContent);
const CO = {OIL:{name:'Oil (JIVO Wellness)',short:'Oil',c:'#4ade80',cls:'oil'},
            MART:{name:'JIVO Mart',short:'Mart',c:'#38bdf8',cls:'mart'},
            BEV:{name:'JIVO Beverages',short:'Beverages',c:'#c084fc',cls:'bev'}};
const COS=['OIL','MART','BEV'], M=D.months, ML=D.monthLabels;

function inr(n){
  const neg=n<0; n=Math.round(Math.abs(n));
  let s=String(n), r='';
  if(s.length>3){const last3=s.slice(-3); let rest=s.slice(0,-3);
    rest=rest.replace(/\B(?=(\d{2})+(?!\d))/g,','); r=rest+','+last3;} else r=s;
  return (neg?'−':'')+r;
}
function cr(n){
  const a=Math.abs(n), sg=n<0?'−':'';
  if(a>=1e7) return sg+'₹'+(a/1e7).toFixed(2)+' Cr';
  if(a>=1e5) return sg+'₹'+(a/1e5).toFixed(2)+' L';
  return sg+'₹'+inr(a);
}
const td=n=>`<td class="num ${n<0?'neg':''}">${inr(n)}</td>`;
const el=id=>document.getElementById(id);

// ---------- aggregation helpers ----------
function agg(rows,keyFn,{core=true}={}){
  const out=new Map();
  for(const r of rows){
    if(core && r.excluded) continue;
    const k=keyFn(r); if(k==null) continue;
    let o=out.get(k); if(!o){o={key:k,row:r,m:Object.fromEntries(M.map(x=>[x,0])),tot:0,txns:0};out.set(k,o);}
    o.m[r.mth]+=r.net; o.tot+=r.net; o.txns+=r.txns;
  }
  return [...out.values()];
}
const P=D.posting, E=D.effective;
const coTot={}, coMon={};
for(const c of COS){
  const rs=P.filter(r=>r.co===c && !r.excluded);
  coMon[c]=Object.fromEntries(M.map(m=>[m,rs.filter(r=>r.mth===m).reduce((a,b)=>a+b.net,0)]));
  coTot[c]=rs.reduce((a,b)=>a+b.net,0);
}
const grpTot=COS.reduce((a,c)=>a+coTot[c],0);
const grpMon=Object.fromEntries(M.map(m=>[m,COS.reduce((a,c)=>a+coMon[c][m],0)]));
const exTot={}, exMon={};
for(const c of COS){
  const rs=P.filter(r=>r.co===c && r.excluded);
  exMon[c]=Object.fromEntries(M.map(m=>[m,rs.filter(r=>r.mth===m).reduce((a,b)=>a+b.net,0)]));
  exTot[c]=rs.reduce((a,b)=>a+b.net,0);
}
const exGrand=COS.reduce((a,c)=>a+exTot[c],0);

// ---------- 01 KPIs ----------
el('kpis').innerHTML=[
 `<div class="kpi grp"><div class="lab">Group · 4 months</div><div class="val">${cr(grpTot)}</div>
   <div class="sub2">${inr(grpTot)} · averages <b>${cr(grpTot/4)}</b> a month</div></div>`,
 ...COS.map(c=>`<div class="kpi ${CO[c].cls}"><div class="lab">${CO[c].name}</div>
   <div class="val">${cr(coTot[c]/4)}<span style="font-size:14px;color:var(--ink3)"> /mo</span></div>
   <div class="sub2">${cr(coTot[c])} over the four months · ${(coTot[c]/grpTot*100).toFixed(1)}% of group</div></div>`),
 `<div class="kpi"><div class="lab">Stripped out</div><div class="val">${cr(exGrand)}</div>
   <div class="sub2">NPD 1 + NPD 2 + One Time Expense · ${cr(exGrand/4)} a month</div></div>`
].join('');

el('swingNote').innerHTML =
 `The group's four months run ${M.map((m,i)=>`<b>${ML[i].slice(0,3)} ${cr(grpMon[m])}</b>`).join(' · ')}. `+
 `Most of that movement is provision timing, not real cost: Oil's <b>Sales Realise</b> cost centre booked ₹1.79 Cr in June and reversed ₹1.24 Cr in July, and Mart's <b>ECOM</b> and <b>Sales</b> centres each carry a negative month. `+
 `The honest figure for planning is the four-month average — <b>${cr(grpTot/4)} a month for the group</b> — not any single month.`;

// ---------- 02 company table ----------
(function(){
  const head=`<tr><th>Company</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>4-month total</th><th>Average / month</th></tr>`;
  const body=COS.map(c=>`<tr><td><span class="chip ${CO[c].cls}">${CO[c].short}</span> ${CO[c].name}</td>
      ${M.map(m=>td(coMon[c][m])).join('')}${td(coTot[c])}${td(coTot[c]/4)}</tr>`).join('');
  const tot=`<tr class="tot"><td>GROUP — all three companies</td>${M.map(m=>td(grpMon[m])).join('')}${td(grpTot)}${td(grpTot/4)}</tr>`;
  el('coTable').innerHTML=`<table><thead>${head}</thead><tbody>${body}${tot}</tbody></table>`;
  const mx=Math.max(...M.map(m=>grpMon[m]));
  el('coBars').innerHTML=`<div style="font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3);margin-bottom:10px">Group monthly total, stacked by company</div>`+
   M.map((m,i)=>{
     let x=0; const segs=COS.map(c=>{const w=coMon[c][m]/mx*100; const s=`<div class="bar-fill" style="position:absolute;left:${x}%;width:${Math.max(w,0)}%;background:${CO[c].c};opacity:.85"></div>`; x+=Math.max(w,0); return s;}).join('');
     return `<div class="bar-row"><div>${ML[i]}</div><div class="bar-track">${segs}</div><div class="bar-val">${cr(grpMon[m])}</div></div>`;
   }).join('');
})();

// ---------- 03 trend ----------
(function(){
  const months=[...new Set(D.trend.map(r=>r.mth))].sort();
  const val=(c,m)=>D.trend.filter(r=>r.co===c&&r.mth===m&&r.bucket==='CORE').reduce((a,b)=>a+b.net,0);
  const series=COS.map(c=>({c,vals:months.map(m=>val(c,m))}));
  const all=series.flatMap(s=>s.vals);
  const hi=Math.max(...all,0), lo=Math.min(...all,0);
  const W=Math.max(940,months.length*58), H=300, PADL=64, PADB=44, PADT=16;
  const ch=H-PADB-PADT, sc=v=>PADT+ch*(hi-v)/((hi-lo)||1), zero=sc(0);
  const gw=(W-PADL-14)/months.length, bw=Math.min(13,(gw-10)/3);
  let s=`<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="16 month indirect expense trend">`;
  for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4, y=sc(v);
    s+=`<line x1="${PADL}" x2="${W-8}" y1="${y}" y2="${y}" stroke="#1e2a38"/>`;
    s+=`<text x="${PADL-8}" y="${y+4}" text-anchor="end" fill="#6b7f96" font-size="10" font-family="monospace">${(v/1e7).toFixed(1)}Cr</text>`;}
  s+=`<line x1="${PADL}" x2="${W-8}" y1="${zero}" y2="${zero}" stroke="#2a3a4d" stroke-width="1.5"/>`;
  months.forEach((m,i)=>{
    const gx=PADL+i*gw+6;
    series.forEach((se,j)=>{const v=se.vals[i], y=Math.min(sc(v),zero), h=Math.abs(sc(v)-zero);
      s+=`<rect x="${gx+j*(bw+2)}" y="${y}" width="${bw}" height="${Math.max(h,0.8)}" fill="${CO[se.c].c}" opacity=".85"><title>${CO[se.c].short} ${m}: ₹${inr(v)}</title></rect>`;});
    const lab=m.slice(5)+'/'+m.slice(2,4);
    s+=`<text x="${gx+(3*(bw+2))/2}" y="${H-PADB+18}" text-anchor="middle" fill="${m>='2026-04'?'#e8eef6':'#6b7f96'}" font-size="9.5" font-family="monospace">${lab}</text>`;
  });
  s+=`<rect x="${PADL+months.indexOf('2026-04')*gw+2}" y="${PADT}" width="${gw*4}" height="${ch}" fill="#4ade80" opacity=".05"/>`;
  s+=`<text x="${PADL+months.indexOf('2026-04')*gw+8}" y="${PADT+13}" fill="#4ade80" font-size="10" font-family="monospace">the four months on this page</text>`;
  s+='</svg>';
  el('trendChart').innerHTML=s;
})();

// ---------- 04 expense heads ----------
let coFilter='ALL';
function renderHeads(){
  const rows=coFilter==='ALL'?P:P.filter(r=>r.co===coFilter);
  const g=agg(rows,r=>r.grp).sort((a,b)=>a.key.localeCompare(b.key));
  const tot=Object.fromEntries(M.map(m=>[m,g.reduce((a,b)=>a+b.m[m],0)]));
  const gt=g.reduce((a,b)=>a+b.tot,0);
  const body=g.map(o=>`<tr><td><span class="muted" style="font-family:var(--mono);font-size:11px">${o.key}</span> ${D.groups[o.key]||o.key}</td>
     ${M.map(m=>td(o.m[m])).join('')}${td(o.tot)}<td class="num muted">${gt?(o.tot/gt*100).toFixed(1)+'%':'—'}</td></tr>`).join('');
  el('headTable').innerHTML=`<table><thead><tr><th>Expense head</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>4-month total</th><th>Share</th></tr></thead>
    <tbody>${body}<tr class="tot"><td>Total indirect expense${coFilter==='ALL'?' — group':' — '+CO[coFilter].short}</td>${M.map(m=>td(tot[m])).join('')}${td(gt)}<td class="num">100%</td></tr></tbody></table>`;
}
document.querySelectorAll('[data-cofilter]').forEach(b=>b.onclick=()=>{
  coFilter=b.dataset.cofilter;
  document.querySelectorAll('[data-cofilter]').forEach(x=>x.setAttribute('aria-pressed',x===b));
  renderHeads();
});
renderHeads();

// ---------- 05 cost centres ----------
(function(){
  let html=`<table><thead><tr><th>Cost centre (Dimension 3)</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>4-month total</th><th>Avg / month</th></tr></thead><tbody>`;
  for(const c of COS){
    const rows=P.filter(r=>r.co===c);
    const g=agg(rows,r=>r.cc,{core:false}).sort((a,b)=>b.tot-a.tot);
    html+=`<tr class="sec"><td colspan="${M.length+3}">${CO[c].name}</td></tr>`;
    for(const o of g){
      const ex=o.row.excluded;
      html+=`<tr${ex?' style="opacity:.55"':''}><td>${o.row.ccName}${ex?' <span class="chip x">excluded</span>':''}
        <span class="muted" style="font-family:var(--mono);font-size:10.5px"> ${o.key}</span></td>
        ${M.map(m=>td(o.m[m])).join('')}${td(o.tot)}${td(o.tot/4)}</tr>`;
    }
    html+=`<tr class="tot"><td>${CO[c].short} — total after exclusions</td>${M.map(m=>td(coMon[c][m])).join('')}${td(coTot[c])}${td(coTot[c]/4)}</tr>`;
  }
  html+='</tbody></table>';
  el('ccTable').innerHTML=html;
})();

// ---------- 06 cost centre x ledger ----------
let co2='OIL', q='', openAll=false;
function renderLedger(){
  const rows=P.filter(r=>r.co===co2);
  const ccs=agg(rows,r=>r.cc,{core:false}).sort((a,b)=>b.tot-a.tot);
  const needle=q.trim().toLowerCase();
  let html='';
  for(const o of ccs){
    const lines=agg(rows.filter(r=>r.cc===o.key),r=>r.acct,{core:false}).sort((a,b)=>b.tot-a.tot);
    const hit=l=>!needle||l.row.acct.includes(needle)||l.row.acctName.toLowerCase().includes(needle)||o.row.ccName.toLowerCase().includes(needle)||o.key.toLowerCase().includes(needle);
    const vis=lines.filter(hit);
    if(!vis.length) continue;
    const ccMatch=needle&&(o.row.ccName.toLowerCase().includes(needle)||o.key.toLowerCase().includes(needle));
    const open=openAll||(needle&&!ccMatch);
    html+=`<details class="drill"${open?' open':''}><summary>
      <span class="cc">${o.row.ccName}${o.row.excluded?' <span class="chip x">excluded</span>':''}
        <span class="muted" style="font-family:var(--mono);font-size:10.5px;font-weight:400"> ${o.key} · ${vis.length} ledger${vis.length>1?'s':''} · ${o.txns} entries</span></span>
      <span class="amt">${cr(o.tot)} <span class="muted">/ 4 mo</span></span></summary>
      <div class="tblwrap" style="border:0;border-radius:0"><table><thead><tr><th>Ledger account</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>Total</th><th>Entries</th></tr></thead><tbody>
      ${vis.map(l=>`<tr><td><span class="muted" style="font-family:var(--mono);font-size:11px">${l.row.acct}</span> ${l.row.acctName}
          <span class="chip" style="margin-left:6px">${D.groups[l.row.grp]||l.row.grp}</span></td>
        ${M.map(m=>td(l.m[m])).join('')}${td(l.tot)}<td class="num muted">${l.txns}</td></tr>`).join('')}
      <tr class="tot"><td>${o.row.ccName} total</td>${M.map(m=>td(o.m[m])).join('')}${td(o.tot)}<td class="num">${o.txns}</td></tr>
      </tbody></table></div></details>`;
  }
  el('ledgerBox').innerHTML=html||`<div style="padding:24px;color:var(--ink3);font-family:var(--mono);font-size:13px">nothing matches “${q}” in ${CO[co2].name}</div>`;
}
document.querySelectorAll('[data-cofilter2]').forEach(b=>b.onclick=()=>{
  co2=b.dataset.cofilter2;
  document.querySelectorAll('[data-cofilter2]').forEach(x=>x.setAttribute('aria-pressed',x===b));
  renderLedger();
});
el('ledgerSearch').oninput=e=>{q=e.target.value;renderLedger();};
el('expandAll').onclick=e=>{openAll=!openAll;e.target.setAttribute('aria-pressed',openAll);e.target.textContent=openAll?'collapse all':'expand all';renderLedger();};
renderLedger();

// ---------- 07 posting vs effective ----------
(function(){
  const eMon={},eTot={};
  for(const c of COS){const rs=E.filter(r=>r.co===c&&!r.excluded);
    eMon[c]=Object.fromEntries(M.map(m=>[m,rs.filter(r=>r.mth===m).reduce((a,b)=>a+b.net,0)]));
    eTot[c]=rs.reduce((a,b)=>a+b.net,0);}
  let html=`<table><thead><tr><th>Company · basis</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>4-month total</th></tr></thead><tbody>`;
  for(const c of COS){
    html+=`<tr><td><span class="chip ${CO[c].cls}">${CO[c].short}</span> posting month <span class="muted">RefDate</span></td>${M.map(m=>td(coMon[c][m])).join('')}${td(coTot[c])}</tr>`;
    html+=`<tr><td style="padding-left:26px" class="muted">effective month <span style="font-family:var(--mono);font-size:11px">TaxDate</span></td>${M.map(m=>td(eMon[c][m])).join('')}${td(eTot[c])}</tr>`;
    html+=`<tr style="opacity:.75"><td style="padding-left:26px" class="muted">difference</td>${M.map(m=>td(eMon[c][m]-coMon[c][m])).join('')}${td(eTot[c]-coTot[c])}</tr>`;
  }
  const gp=Object.fromEntries(M.map(m=>[m,COS.reduce((a,c)=>a+coMon[c][m],0)]));
  const ge=Object.fromEntries(M.map(m=>[m,COS.reduce((a,c)=>a+eMon[c][m],0)]));
  const gpT=COS.reduce((a,c)=>a+coTot[c],0), geT=COS.reduce((a,c)=>a+eTot[c],0);
  html+=`<tr class="tot"><td>GROUP — posting month</td>${M.map(m=>td(gp[m])).join('')}${td(gpT)}</tr>`;
  html+=`<tr class="tot"><td>GROUP — effective month</td>${M.map(m=>td(ge[m])).join('')}${td(geT)}</tr>`;
  html+='</tbody></table>';
  el('effTable').innerHTML=html;
  const worst=M.map((m,i)=>({m,l:ML[i],d:ge[m]-gp[m]})).sort((a,b)=>Math.abs(b.d)-Math.abs(a.d))[0];
  el('effNote').querySelector('p').innerHTML =
    `Over the four months the two bases differ by <b>${cr(geT-gpT)}</b> at group level — ${Math.abs((geT-gpT)/gpT*100).toFixed(1)}% of the total. `+
    `The widest single month is <b>${worst.l}</b>, where the effective basis is ${cr(Math.abs(worst.d))} ${worst.d>0?'higher':'lower'} than the posting basis. `+
    `A positive difference means bills whose own invoice date falls in that month were keyed into the books later; a negative one means the month absorbed bills that really belong to an earlier month. `+
    `The four-month totals do not match either, because bills dated before April or after July fall in or out of the window depending which date you use.`;
})();

// ---------- 08 excluded ----------
(function(){
  let html=`<table><thead><tr><th>Excluded cost centre</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>4-month total</th></tr></thead><tbody>`;
  for(const c of COS){
    const rows=P.filter(r=>r.co===c&&r.excluded);
    if(!rows.length){html+=`<tr class="sec"><td colspan="${M.length+2}">${CO[c].name} — nothing booked to NPD 1, NPD 2 or One Time Expense</td></tr>`;continue;}
    html+=`<tr class="sec"><td colspan="${M.length+2}">${CO[c].name}</td></tr>`;
    for(const o of agg(rows,r=>r.cc,{core:false}).sort((a,b)=>b.tot-a.tot))
      html+=`<tr><td>${o.row.ccName}</td>${M.map(m=>td(o.m[m])).join('')}${td(o.tot)}</tr>`;
    html+=`<tr class="tot"><td>${CO[c].short} excluded total</td>${M.map(m=>td(exMon[c][m])).join('')}${td(exTot[c])}</tr>`;
  }
  html+=`<tr class="tot"><td>GROUP — excluded from every figure on this page</td>${M.map(m=>td(COS.reduce((a,c)=>a+exMon[c][m],0))).join('')}${td(exGrand)}</tr></tbody></table>`;
  el('exclTable').innerHTML=html;
  const lines=agg(P.filter(r=>r.excluded),r=>r.co+'|'+r.cc+'|'+r.acct,{core:false}).sort((a,b)=>b.tot-a.tot).slice(0,12);
  el('exclDetail').innerHTML=`<div style="font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3);margin-bottom:10px">Where the excluded money went — largest ledger lines</div>
   <div class="tblwrap" style="border:0"><table><thead><tr><th>Company · cost centre · ledger</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>Total</th></tr></thead><tbody>
   ${lines.map(o=>`<tr><td><span class="chip ${CO[o.row.co].cls}">${CO[o.row.co].short}</span> ${o.row.ccName} · <span class="muted" style="font-family:var(--mono);font-size:11px">${o.row.acct}</span> ${o.row.acctName}</td>
     ${M.map(m=>td(o.m[m])).join('')}${td(o.tot)}</tr>`).join('')}</tbody></table></div>`;
})();

// ---------- stamps ----------
const stamp=D.pulled||'';
el('stamp').textContent=stamp; el('footStamp').textContent='pulled '+stamp;



// ---------- 02 departments ----------
const DEPTS=['Finance','Sales','Media','HR & Admin','Legal','Plant & Production','Transport & Freight','Ecommerce Sales'];
const DCOL={'Finance':'#fbbf24','Sales':'#4ade80','Media':'#f472b6','HR & Admin':'#22d3ee','Legal':'#a78bfa',
            'Plant & Production':'#fb923c','Transport & Freight':'#38bdf8','Ecommerce Sales':'#c084fc','Unallocated':'#6b7f96'};
const CCDEPT={'Factory':'Plant & Production','FACT_COM':'Plant & Production','SERVICES':'Plant & Production',
 'ECOM':'Ecommerce Sales','HR/ADMIN':'HR & Admin','BackOff':'HR & Admin',
 'Sales':'Sales','Sales RE':'Sales','Sal CF':'Sales','SUPPLY-C':'Sales','Med MKT':'Media',
 'Del Bkhp':'Transport & Freight','Del Mayp':'Transport & Freight','Transprt':'Transport & Freight','Interest':'Finance'};
function natureOf(r){
  const a=r.acct, n=(r.acctName||'').toUpperCase();
  if(a.startsWith('561')) return 'Finance';
  if(a.startsWith('564')) return 'Media';
  if(a.startsWith('567')||n.includes('TOLL')||n.includes('FUEL - VEH')||n.includes('MAINTENANCE VEHICLE')) return 'Transport & Freight';
  if(n.includes('LEGAL')) return 'Legal';
  if(a.startsWith('563')) return 'HR & Admin';
  return null;
}
function deptOf(r,mode){
  const cc=CCDEPT[(r.cc||'').trim()]||null, nt=natureOf(r);
  // Legal has no cost centre of its own anywhere in the three books — the ledger
  // account is the only thing that identifies it, on either basis.
  if(nt==='Legal') return 'Legal';
  if(mode==='NATURE') return nt||cc||'Unallocated';
  return cc||nt||'Unallocated';
}
// Did SAP itself carry the field this basis relies on, or did a fallback rule place the row?
function hasTag(r,mode){
  const cc=CCDEPT[(r.cc||'').trim()]||null, nt=natureOf(r);
  if(mode==='NATURE') return !!nt;
  return !!cc && nt!=='Legal';
}
let deptMode='OWNER', deptCo='ALL';
function deptRows(){ return deptCo==='ALL'?P.filter(r=>!r.excluded):P.filter(r=>!r.excluded&&r.co===deptCo); }

function renderDept(){
  const rows=deptRows();
  const keys=[...DEPTS]; 
  const blank=()=>({tot:0,m:Object.fromEntries(M.map(x=>[x,0])),co:{OIL:0,MART:0,BEV:0},txns:0,tagged:0,fallback:0});
  const acc={}; keys.concat(['Unallocated']).forEach(k=>acc[k]=blank());
  for(const r of rows){ const k=deptOf(r,deptMode); if(!acc[k])acc[k]=blank();
    acc[k].tot+=r.net; acc[k].m[r.mth]+=r.net; acc[k].co[r.co]+=r.net; acc[k].txns+=r.txns;
    if(hasTag(r,deptMode)) acc[k].tagged+=r.net; else acc[k].fallback+=r.net; }
  const shown=keys.concat(Math.abs(acc['Unallocated'].tot)>1?['Unallocated']:[]);
  const gt=shown.reduce((a,k)=>a+acc[k].tot,0);
  const ord=[...shown].sort((a,b)=>acc[b].tot-acc[a].tot);

  // cards
  el('deptCards').innerHTML=ord.map(k=>{
    const o=acc[k], sh=gt?(o.tot/gt*100):0;
    const fbNote=Math.abs(o.fallback)>1e5
      ? `<div class="sub2" style="color:var(--warn);margin-top:4px">${cr(o.fallback)} of this was placed by rule, not by SAP</div>` : '';
    return `<div class="kpi" style="border-left:3px solid ${DCOL[k]}">
      <div class="lab" style="color:${DCOL[k]}">${k}</div>
      <div class="val">${cr(o.tot)}</div>
      <div class="sub2">${sh.toFixed(1)}% of ${deptCo==='ALL'?'group':CO[deptCo].short} &middot; ${cr(o.tot/4)}/mo</div>${fbNote}</div>`;
  }).join('');

  // table
  const body=ord.map(k=>{const o=acc[k];
    return `<tr><td style="text-align:left"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${DCOL[k]};margin-right:8px"></span>${k}</td>
      ${M.map(m=>td(o.m[m])).join('')}${td(o.tot)}${td(o.tot/4)}<td class="num muted">${gt?(o.tot/gt*100).toFixed(1)+'%':'—'}</td>
      <td class="num ${Math.abs(o.fallback)>1e5?'':'muted'}" ${Math.abs(o.fallback)>1e5?'style="color:var(--warn)"':''}>${o.fallback?inr(o.fallback):'—'}</td></tr>`;}).join('');
  const tm=Object.fromEntries(M.map(m=>[m,ord.reduce((a,k)=>a+acc[k].m[m],0)]));
  el('deptTable').innerHTML=`<table><thead><tr><th style="text-align:left">Department</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>4-month total</th><th>Avg / month</th><th>Share</th><th title="Rupees this basis could not read off SAP, placed by a fallback rule">Placed by rule</th></tr></thead>
    <tbody>${body}<tr class="tot"><td style="text-align:left">Total indirect expense — ${deptCo==='ALL'?'group':CO[deptCo].name}</td>${M.map(m=>td(tm[m])).join('')}${td(gt)}${td(gt/4)}<td class="num">100%</td>${td(ord.reduce((a,k)=>a+acc[k].fallback,0))}</tr></tbody></table>`;

  // bars — department total split by company
  const mx=Math.max(...ord.map(k=>Math.abs(acc[k].tot)),1);
  el('deptBars').innerHTML=`<div style="font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3);margin-bottom:10px">Four-month total by department, stacked by company</div>`+
    ord.map(k=>{const o=acc[k]; let x=0;
      const segs=COS.map(c=>{const w=Math.max(o.co[c],0)/mx*100; const s=`<div class="bar-fill" style="position:absolute;left:${x}%;width:${w}%;background:${CO[c].c};opacity:.85"></div>`; x+=w; return s;}).join('');
      return `<div class="bar-row"><div title="${k}" style="overflow:hidden;text-overflow:ellipsis">${k}</div><div class="bar-track">${segs}</div><div class="bar-val">${cr(o.tot)}</div></div>`;}).join('')
    +`<div class="legend" style="margin-top:10px">${COS.map(c=>`<span><i style="background:${CO[c].c}"></i>${CO[c].short}</span>`).join('')}</div>`;

  // note
  const top=ord[0], neg=ord.filter(k=>acc[k].tot<0);
  el('deptNote').innerHTML=`<h4>${deptMode==='OWNER'?'Reading the cost-centre basis':'Reading the ledger basis'}</h4>
   <p>${deptMode==='OWNER'
     ? `Biggest department is <b>${top}</b> at ${cr(acc[top].tot)} (${(acc[top].tot/gt*100).toFixed(1)}%). On this basis a department carries everything booked against it — so Sales carries the brand advertising its own cost centres paid for, and E-Commerce carries its own media spend. Switch to the ledger basis to see advertising as one number.`
     : `Biggest department is <b>${top}</b> at ${cr(acc[top].tot)} (${(acc[top].tot/gt*100).toFixed(1)}%). On this basis the ledger account decides — all advertising, business promotion, brokerage and sampling roll into Media wherever they were booked, all freight and vehicle running into Transport &amp; Freight, all interest and bank charges into Finance. E-Commerce shrinks to ${cr(acc['Ecommerce Sales'].tot)} because most of what that cost centre spends <i>is</i> media.`}</p>`;

  // Media's negative has one specific cause and it is worth naming.
  el('deptWhy').innerHTML = deptMode==='OWNER'
   ? `<h4>Why Media is negative — and it is not a saving</h4>
      <p>The Media Marketing cost centre itself is <b>positive</b>, ₹44.80&nbsp;L across the four months. The department only turns negative because of <b>five A/R invoices Mart raised on JIVO Wellness (Oil) on 24&nbsp;June&nbsp;2026, totalling −₹1.20&nbsp;Cr, credited straight to ADVERTISEMENT</b>. That is an intercompany advertising recharge — Mart recovering ad spend from Oil — and Oil carries the matching debit (₹51.96&nbsp;L of it lands in Oil's <i>Sales&nbsp;Realise</i> cost centre in the same month). At group level it largely nets off; it is not money saved and not money spent.<br><br>
      Those five lines carry <b>no cost centre at all</b>, so on this basis nothing in SAP says where they belong — the page places them in Media by reading the ledger account. Every rupee placed that way is shown in the <b>Placed by rule</b> column above, so you can see exactly how much of each department is SAP's answer and how much is this page's.</p>`
   : `<h4>What this basis cannot tell you</h4>
      <p>The ledger account is present on every line, so almost nothing here is guesswork. What it does hide is <i>ownership</i>: ₹5.88&nbsp;Cr of the Media figure was spent out of the Sales cost centres and ₹1.74&nbsp;Cr out of E-Commerce's. If the question is "which budget paid for this", switch back to the cost-centre basis. Note also that Media on this basis still absorbs the −₹1.20&nbsp;Cr intercompany advertising recharge Mart billed to Oil in June 2026.</p>`;

  // crosstab: owner-basis department x nature
  const NAT=['Media','HR & Admin','Transport & Freight','Finance','Legal','Other running cost'];
  const X={}; const rowTot={}; const colTot=Object.fromEntries(NAT.map(n=>[n,0]));
  for(const r of rows){ const d=deptOf(r,'OWNER'); const n=natureOf(r)||'Other running cost';
    X[d]=X[d]||Object.fromEntries(NAT.map(k=>[k,0])); X[d][n]+=r.net; rowTot[d]=(rowTot[d]||0)+r.net; colTot[n]+=r.net; }
  const xord=Object.keys(X).sort((a,b)=>rowTot[b]-rowTot[a]);
  el('deptCross').innerHTML=`<table><thead><tr><th style="text-align:left">Department (cost centre) ↓ &nbsp;/&nbsp; spent on →</th>${NAT.map(n=>`<th>${n}</th>`).join('')}<th>Total</th></tr></thead><tbody>`
   +xord.map(d=>`<tr><td style="text-align:left"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${DCOL[d]||'#6b7f96'};margin-right:8px"></span>${d}</td>`
      +NAT.map(n=>{const v=X[d][n]; const hot=Math.abs(v)>=5e6&&n!=='Other running cost'&&n!==d;
        return `<td class="num ${v<0?'neg':''}"${hot?' style="background:#1a2433;color:#fbbf24;font-weight:600"':''}>${v?inr(v):'—'}</td>`;}).join('')
      +td(rowTot[d])+`</tr>`).join('')
   +`<tr class="tot"><td style="text-align:left">Total</td>${NAT.map(n=>td(colTot[n])).join('')}${td(gt)}</tr></tbody></table>`;

  // drill: department -> ledger account
  let dh=`<table><thead><tr><th style="text-align:left">Department · ledger account</th>${ML.map(l=>`<th>${l}</th>`).join('')}<th>4-month total</th><th>Txns</th></tr></thead><tbody>`;
  for(const k of ord){
    const sub=rows.filter(r=>deptOf(r,deptMode)===k);
    const g=agg(sub,r=>r.acct+'|'+r.acctName).sort((a,b)=>b.tot-a.tot);
    if(!g.length) continue;
    dh+=`<tr class="sec"><td colspan="${M.length+3}" style="text-align:left;color:${DCOL[k]}">${k} — ${cr(acc[k].tot)}</td></tr>`;
    for(const o of g){ const [a,nm]=o.key.split('|');
      dh+=`<tr><td style="text-align:left"><span class="muted" style="font-family:var(--mono);font-size:11px">${a}</span> ${nm}</td>${M.map(m=>td(o.m[m])).join('')}${td(o.tot)}<td class="num muted">${inr(o.txns)}</td></tr>`; }
  }
  el('deptDrill').innerHTML=dh+'</tbody></table>';
}
document.querySelectorAll('[data-deptmode]').forEach(b=>b.onclick=()=>{
  deptMode=b.dataset.deptmode;
  document.querySelectorAll('[data-deptmode]').forEach(x=>x.setAttribute('aria-pressed',x===b));
  renderDept();});
document.querySelectorAll('[data-deptco]').forEach(b=>b.onclick=()=>{
  deptCo=b.dataset.deptco;
  document.querySelectorAll('[data-deptco]').forEach(x=>x.setAttribute('aria-pressed',x===b));
  renderDept();});
renderDept();


// ---------- 10 reconciliation ----------
(function(){
  const R=D.recon; if(!R||!R.length) return;
  const RM=D.reconMeta.months, RL=D.reconMeta.monthLabels;
  const fileT=R.reduce((a,b)=>a+b.tTot,0), sapT=R.reduce((a,b)=>a+b.sTot,0);
  const byCls=c=>R.filter(r=>r.cls===c);
  const agreeCells=byCls('match').length+byCls('timing').length;
  const nearCells=R.filter(r=>r.cls!=='disputed').length;
  const nearDiff=R.filter(r=>r.cls!=='disputed').reduce((a,b)=>a+b.diff,0);
  const disputed=byCls('disputed');
  el('reconKpis').innerHTML=[
   `<div class="kpi"><div class="lab">Their workbook · 3 months</div><div class="val">${cr(fileT)}</div><div class="sub2">${inr(fileT)} · May–Jul 2026, Oil only</div></div>`,
   `<div class="kpi oil"><div class="lab">SAP live · same 3 months</div><div class="val">${cr(sapT)}</div><div class="sub2">${inr(sapT)} · same definition, same grain</div></div>`,
   `<div class="kpi" style="border-left:3px solid var(--bad)"><div class="lab">Gap</div><div class="val neg">${cr(sapT-fileT)}</div><div class="sub2">the workbook is ${Math.abs((sapT-fileT)/sapT*100).toFixed(0)}% higher than the ledger</div></div>`,
   `<div class="kpi grp"><div class="lab">Cells in agreement</div><div class="val">${nearCells}<span style="font-size:16px;color:var(--ink3)"> of ${R.length}</span></div><div class="sub2">agree to within ${cr(Math.abs(nearDiff))} in total · ${agreeCells} tie exactly</div></div>`,
   `<div class="kpi" style="border-left:3px solid var(--bad)"><div class="lab">Cells in dispute</div><div class="val">${disputed.length}</div><div class="sub2">carrying ${cr(Math.abs(disputed.reduce((a,b)=>a+b.diff,0)))} — the whole gap</div></div>`
  ].join('');
  const top2=disputed.slice().sort((a,b)=>Math.abs(b.diff)-Math.abs(a.diff)).slice(0,2);
  el('reconLead').innerHTML=
   `<b>${agreeCells} of ${R.length}</b> Budget × Sub-Budget cells tie to the rupee, ${byCls('match').length} of them month for month — so the two sides are measuring the same thing on the same dimension with the same net-of-credits rule. `+
   `Widen that to cells agreeing within ₹50,000 and it is <b>${nearCells} of ${R.length}</b>, together <b>${cr(Math.abs(nearDiff))}</b> apart. `+
   `The entire <b>${cr(Math.abs(sapT-fileT))}</b> gap sits in <b>${disputed.length}</b> cells, and <b>${cr(Math.abs(top2.reduce((a,b)=>a+b.diff,0)))}</b> of it in just two — ${top2.map(r=>`<b>${CCN(r.cc3)}</b>`).join(' and ')}.`;

  // bridge
  const F=(c)=>R.filter(r=>r.cls===c).reduce((a,b)=>a+b.diff,0);
  const named={}; disputed.forEach(r=>{named[r.cc3+'|'+r.cc4]=r.diff;});
  const bigs=[['Factory','(blank)','Factory — unexplained'],['Del Bkhp','(blank)','Delivery Bhakharpur — unexplained'],['(blank)','(blank)','“(blank)” / Short & Excess']];
  const bigSum=bigs.reduce((a,[a1,b1])=>a+(named[a1+'|'+b1]||0),0);
  const steps=[
   {l:'Their workbook, three months',v:fileT,t:'start'},
   ...bigs.map(([a1,b1,lab])=>({l:lab,v:named[a1+'|'+b1]||0,t:'step'})),
   {l:'Eight other disputed cells, netted',v:F('disputed')-bigSum,t:'step'},
   {l:'Fourteen minor cells — rounding and one-offs',v:F('minor'),t:'step'},
   {l:'NPD 2 ↔ One Time Expense reclassification',v:F('reclass'),t:'step'},
   {l:'Sales Realise provision',v:F('provision'),t:'step'},
   {l:'SAP live, three months',v:sapT,t:'end'}
  ];
  const mx=Math.max(...steps.filter(s=>s.t==='step').map(s=>Math.abs(s.v)),1);
  el('bridge').innerHTML=steps.map(s=>{
    if(s.t!=='step') return `<div class="bar-row" style="border-top:1px solid var(--line2);margin-top:6px;padding-top:10px"><div style="font-weight:650">${s.l}</div><div></div><div class="bar-val" style="font-weight:700">${cr(s.v)}</div></div>`;
    const w=Math.abs(s.v)/mx*50, pos=s.v>=0;
    return `<div class="bar-row"><div class="muted" style="font-size:12.5px">${s.l}</div>
      <div class="bar-track" style="height:16px"><div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--line2)"></div>
      <div class="bar-fill" style="position:absolute;${pos?`left:50%;width:${w}%;background:var(--accent)`:`right:50%;width:${w}%;background:var(--bad)`};opacity:.8"></div></div>
      <div class="bar-val ${pos?'':'neg'}">${s.v>=0?'+':''}${cr(s.v)}</div></div>`;
  }).join('');

  // table
  const CLS={match:['match','#4ade80','#1c4b32'],timing:['timing','#22d3ee','#14415c'],minor:['minor','#9fb0c4','#2a3a4d'],
             reclass:['reclass','#fbbf24','#4a3a12'],provision:['provision','#fbbf24','#4a3a12'],disputed:['disputed','#f87171','#5c1f1f']};
  let filt='all';
  function draw(){
    const rows=R.filter(r=>filt==='all'||r.cls===filt).sort((a,b)=>Math.abs(b.diff)-Math.abs(a.diff)||b.sTot-a.sTot);
    const th=`<tr><th>Budget · Sub Budget</th>${RL.map(l=>`<th>${l}</th>`).join('')}<th>3-month total</th><th>Status</th></tr>`;
    const body=rows.map(r=>{
      const [n,c,b]=CLS[r.cls];
      return `<tr><td>${CCN(r.cc3)} <span class="muted" style="font-family:var(--mono);font-size:10.5px">· ${r.cc4}</span></td>
        ${RM.map(m=>`<td class="num"><span class="muted" style="font-size:11px">${inr(r.their[m]||0)}</span><br><span class="${(r.sap[m]||0)<0?'neg':''}">${inr(r.sap[m]||0)}</span></td>`).join('')}
        <td class="num"><span class="muted" style="font-size:11px">${inr(r.tTot)}</span><br><span class="${r.sTot<0?'neg':''}">${inr(r.sTot)}</span></td>
        <td style="text-align:right"><span class="chip" style="color:${c};border-color:${b}">${n}</span><br><span class="num muted" style="font-size:11px">${r.diff===0?'—':(r.diff>0?'+':'')+inr(r.diff)}</span></td></tr>`;}).join('');
    el('reconTable').innerHTML=`<table><thead>${th}</thead><tbody>
      <tr class="sec"><td colspan="${RM.length+3}">grey line = their workbook · white line = SAP live · right column = SAP minus workbook</td></tr>
      ${body}</tbody></table>`;
  }
  document.querySelectorAll('[data-rcls]').forEach(b=>b.onclick=()=>{
    filt=b.dataset.rcls;
    document.querySelectorAll('[data-rcls]').forEach(x=>x.setAttribute('aria-pressed',x===b));
    draw();});
  draw();
})();
function CCN(c){const m={'BackOff':'Back Office','Del Bkhp':'Delivery Bhakharpur','Del Mayp':'Delivery Mayapuri',
 'FACT_COM':'Factory Common','Factory':'Factory','Interest':'Interest','Med MKT':'Media Marketing','NPD1':'NPD 1',
 'NPD2':'NPD 2','OTE':'One Time Expense','Sal CF':'Salary Confidential','Sales':'Sales','Sales RE':'Sales Realise',
 'Transprt':'Transport','(blank)':'(no cost centre)'};return m[c]||c;}

