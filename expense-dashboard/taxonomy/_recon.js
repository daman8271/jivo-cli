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

