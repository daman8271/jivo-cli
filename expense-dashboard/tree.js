const D=JSON.parse(document.getElementById('payload').textContent);
const MO=D.months, S=D.S, COMBO=D.combos, ACCT=D.accts, F=D.facts;
const COS=D.cos, CO={OIL:{n:'Oil',full:'Oil — JIVO Wellness',c:'#4FE3A5',cls:'t'},
 MART:{n:'Mart',full:'JIVO Mart',c:'#F5B23C',cls:'o'},BEV:{n:'Beverages',full:'JIVO Beverages',c:'#EE8FD0',cls:'p'}};
const el=id=>document.getElementById(id);
const PAL=['#4FE3A5','#FF8A6B','#F5B23C','#EE8FD0','#9BD46B','#6FC0E8','#F0846B','#8FA8F0','#D8C566','#C58AE8','#5FD8C8'];
const MN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const nice=m=>MN[+m.slice(5)-1]+" '"+m.slice(2,4);
const niceLong=m=>MN[+m.slice(5)-1]+' 20'+m.slice(2,4);

function inr(n){const g=n<0;n=Math.round(Math.abs(n));let s=String(n),r;
 if(s.length>3){r=s.slice(0,-3).replace(/\B(?=(\d{2})+(?!\d))/g,',')+','+s.slice(-3);}else r=s;
 return (g?'−':'')+r;}
function cr(n){const a=Math.abs(n),g=n<0?'−':'';
 if(a>=1e7)return g+'₹'+(a/1e7).toFixed(2)+' Cr';
 if(a>=1e5)return g+'₹'+(a/1e5).toFixed(2)+' L';
 if(a>=1000)return g+'₹'+inr(a);
 return g+'₹'+Math.round(a);}
const LAST=MO.indexOf(D.lastComplete)<0?MO.length-1:MO.indexOf(D.lastComplete);
// Sep 2024 - Mar 2025 is a part first year: it carries the SAP cutover AND the FY24-25
// year-end close, which reverses the whole year out (Mar 2025 alone is -56.43 Cr).
// Those months are real entries but they are not operating months, so they are kept out
// of the presets and out of the chart's scale, and flagged whenever selected.
const OPEN=Math.max(0,MO.indexOf(D.openFrom));
const isClosing=i=>i<OPEN;

// ---------- state ----------
let from=Math.max(0,MO.indexOf('2026-04')), to=LAST, co='ALL', lvl='auto', cmp='off', dept='ALL';

// ---------- fact scan ----------
const C_CO=0,C_DEPT=1,C_SUB=2,C_CC=3,C_EXC=4,C_RULED=5;
function scan(f,t,keep){                       // keep(comboRow) -> bool
  const out=[];
  for(let i=0;i<F.length;i+=5){
    const mth=F[i+2]; if(mth<f||mth>t)continue;
    const c=COMBO[F[i]]; if(c[C_EXC])continue;
    if(keep&&!keep(c))continue;
    out.push(i);
  }
  return out;
}
const inCo=c=>co==='ALL'||COS[c[C_CO]]===co;

function totalOf(f,t,filt){let s=0;
  for(let i=0;i<F.length;i+=5){const m=F[i+2];if(m<f||m>t)continue;
    const c=COMBO[F[i]];if(c[C_EXC])continue;if(filt&&!filt(c))continue;s+=F[i+3];}
  return s;}
function excludedOf(f,t){let s=0;
  for(let i=0;i<F.length;i+=5){const m=F[i+2];if(m<f||m>t)continue;
    if(COMBO[F[i]][C_EXC])s+=F[i+3];}
  return s;}

// ---------- department x month matrix (one pass) ----------
let MX=null, MXkey='';
let MXabs=null,MXguess=null;
function matrix(){
  if(MX&&MXkey===co)return MX;
  const m={},ab={},gu={};
  for(let i=0;i<F.length;i+=5){
    const c=COMBO[F[i]]; if(c[C_EXC])continue; if(!inCo(c))continue;
    const dk=D.deptKeys[c[C_DEPT]], mo=F[i+2], v=F[i+3];
    (m[dk] ||(m[dk] =new Array(MO.length).fill(0)))[mo]+=v;
    (ab[dk]||(ab[dk]=new Array(MO.length).fill(0)))[mo]+=Math.abs(v);
    if(!c[C_RULED])(gu[dk]||(gu[dk]=new Array(MO.length).fill(0)))[mo]+=Math.abs(v);
  }
  MX=m; MXabs=ab; MXguess=gu; MXkey=co; return m;
}
// how much of what you are looking at right now was my judgement, not Accounts'
function guessShare(dk){
  matrix();
  const all=sum(win(MXabs[dk]||[],from,to)), gs=sum(win(MXguess[dk]||[],from,to));
  return all?{pct:gs/all*100,amt:gs}:{pct:0,amt:0};
}
function coMatrix(){
  const m={};
  for(let i=0;i<F.length;i+=5){
    const c=COMBO[F[i]]; if(c[C_EXC])continue;
    const k=COS[c[C_CO]];
    (m[k]||(m[k]=new Array(MO.length).fill(0)))[F[i+2]]+=F[i+3];
  }
  return m;
}
const win=(a,f,t)=>a.slice(f,t+1);
const sum=a=>a.reduce((x,y)=>x+y,0);
function trendOf(v){
  const n=v.length; if(n<3)return null;
  const mx=(n-1)/2, my=sum(v)/n; let num=0,den=0;
  for(let i=0;i<n;i++){num+=(i-mx)*(v[i]-my);den+=(i-mx)*(i-mx);}
  const slope=den?num/den:0;
  return {slope,pct:slope/(Math.abs(my)||1)*100,avg:my};
}
function tag(v){
  const t=trendOf(v); if(!t)return '';
  const p=t.pct;
  if(p>2.5) return `<span class="tt up" title="rising about ${p.toFixed(1)}% a month">\u25B2 rising ${p.toFixed(0)}%/mo</span>`;
  if(p<-2.5)return `<span class="tt down" title="falling about ${Math.abs(p).toFixed(1)}% a month">\u25BC falling ${Math.abs(p).toFixed(0)}%/mo</span>`;
  return `<span class="tt flat">\u2192 flat</span>`;
}
function sparkline(v,colour){
  const n=v.length; if(n<2)return '';
  const W=100,H=26,hi=Math.max(...v,0),lo=Math.min(...v,0),rng=(hi-lo)||1;
  const X=i=>i/(n-1)*W, Y=q=>H-1-((q-lo)/rng)*(H-2);
  return `<span class="spark"><svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">
    <line x1="0" x2="${W}" y1="${Y(0)}" y2="${Y(0)}" stroke="#2A313C"/>
    <polyline points="${v.map((q,i)=>X(i).toFixed(1)+','+Y(q).toFixed(1)).join(' ')}" fill="none" stroke="${colour}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${X(n-1)}" cy="${Y(v[n-1])}" r="2.2" fill="${colour}"/></svg></span>`;
}

// ---------- comparison window ----------
// comparison window; clamped to the months the books actually hold.
// when it comes out shorter than the selection we compare per-month averages instead
// of totals, and say so, rather than pretending 11 months is 12.
function cmpWindow(){
  const len=to-from+1;
  let f,t;
  if(cmp==='prev'){t=from-1;f=t-len+1;}
  else if(cmp==='yoy'){f=from-12;t=to-12;}
  else return null;
  if(t<0)return null;
  const clamped=Math.max(0,f);
  const n=t-clamped+1;
  if(n<1)return null;
  return [clamped,t,n!==len,n];
}

// ---------- tree ----------
const BLANK=k=>!k||k==='(blank)'||k==='Not tagged'||k==='No Sub Budget'||k==='Unassigned'||k==='—';
const SMALL=5000;
const deptMeta=k=>D.depts.find(d=>d.key===k)||{label:k,one_liner:'',order:99};

function orders(idx){                          // per-department: lead with team or cost centre?
  const o={};
  const agg=new Map();
  for(const i of idx){const c=COMBO[F[i]];const d=D.deptKeys[c[C_DEPT]];
    let e=agg.get(d);if(!e){e={tot:0,blank:0};agg.set(d,e);}
    const v=Math.abs(F[i+3]);e.tot+=v; if(BLANK(S[c[C_SUB]]))e.blank+=v;}
  for(const [d,e] of agg){
    o[d]= lvl==='sub'?['sub','cc'] : lvl==='cc'?['cc','sub']
        : (e.blank/(e.tot||1)>0.55?['cc','sub']:['sub','cc']);
  }
  return o;
}

function collect(idx,ord){
  const root=new Map();
  for(const i of idx){
    const c=COMBO[F[i]], a=ACCT[F[i+1]], net=F[i+3], tx=F[i+4];
    const dk=D.deptKeys[c[C_DEPT]];
    const sub=S[c[C_SUB]], ccl=S[c[C_CC]];
    const [L1,L2]=ord[dk]||['sub','cc'];
    const k1=L1==='sub'?sub:ccl, k2=L2==='sub'?sub:ccl;
    let d=root.get(dk); if(!d){d={key:dk,tot:0,txns:0,kids:new Map()};root.set(dk,d);}
    let x=d.kids.get(k1); if(!x){x={key:k1,tot:0,txns:0,kids:new Map()};d.kids.set(k1,x);}
    let y=x.kids.get(k2); if(!y){y={key:k2,tot:0,txns:0,kids:new Map()};x.kids.set(k2,y);}
    const ak=S[a[0]];
    let z=y.kids.get(ak); if(!z){z={key:ak,label:S[a[1]],tot:0,txns:0};y.kids.set(ak,z);}
    for(const n of [d,x,y,z]){n.tot+=net;n.txns+=tx;}
  }
  for(const d of root.values()){hoist(d,0);fold(d);}
  return root;
}
function hoist(n,depth){
  if(!n.kids)return;
  for(const k of n.kids.values())hoist(k,depth+1);
  if(depth<1)return;
  const kids=[...n.kids.values()];
  const b=kids.find(k=>BLANK(k.key)&&k.kids&&k.kids.size);
  if(!b||Math.abs(b.tot)/(Math.abs(n.tot)||1)<0.7)return;
  const m=new Map();
  for(const k of kids){if(k===b){for(const[kk,vv]of b.kids)m.set(kk,vv);}else m.set(k.key,k);}
  n.kids=m;
}
function fold(n){
  if(!n.kids)return;
  for(const k of n.kids.values())fold(k);
  const kids=[...n.kids.values()];
  if(kids.length<4)return;
  const tiny=kids.filter(k=>Math.abs(k.tot)<SMALL&&!k.kids);
  if(tiny.length<3)return;
  const lump={key:'__small',label:`${tiny.length} small lines`,tot:0,txns:0,small:true};
  for(const t of tiny){lump.tot+=t.tot;lump.txns+=t.txns;}
  n.kids=new Map([...kids.filter(k=>!tiny.includes(k)).map(r=>[r.key,r]),['__small',lump]]);
}
function flat(root,pre,into){                  // path -> total, for comparison lookups
  for(const [k,n] of root){const p=pre+'|'+k; into.set(p,n.tot);
    if(n.kids)flat(n.kids,p,into);}
  return into;
}

const NAMES={sub:'team',cc:'cost centre'};
function labelOf(n,depth,l1,l2){
  if(depth===0){const m=deptMeta(n.key);
    const g=guessShare(n.key); let f='';
    if(g.pct>=90)f=` <span class="flag" title="Accounts' own workbook never labelled these cost centres. I assigned them, using the rule their file implies. ${cr(g.amt)} of gross flow in this window.">Accounts hasn\'t ruled on this</span>`;
    else if(g.pct>=8)f=` <span class="flag soft" title="${g.pct.toFixed(0)}% of the entries here (${cr(g.amt)} of gross flow in this window) sit in this department because I put them there, not because Accounts' workbook said so.">${g.pct.toFixed(0)}% of this is my call</span>`;
    return [m.label+f,m.one_liner];}
  if(!n.kids||!n.kids.size)return [n.label||n.key,
    n.small?n.txns+' entries, none over '+cr(SMALL):(n.label?n.key+' · '+n.txns+' entr'+(n.txns===1?'y':'ies'):n.txns+' entries')];
  return [BLANK(n.key)?'Not tagged':n.key, depth===1?l1:l2];
}

function delta(cur,prev,scale){
  if(prev===undefined)return `<span class="dlt new">new</span>`;
  if(scale)prev=prev*scale;
  const d=cur-prev;
  if(Math.abs(d)<1)return `<span class="dlt flatd">no change</span>`;
  const pc=Math.abs(prev)>1?Math.round(d/Math.abs(prev)*100):null;
  const upBad=d>0;
  return `<span class="dlt ${upBad?'up':'down'}">${upBad?'▲':'▼'} ${cr(Math.abs(d))}${pc!==null?` · ${d>0?'+':'−'}${Math.abs(pc)}%`:''}</span>`;
}

let cmpScale=null;
function node(n,depth,grand,color,l1,l2,path,prevMap,mths){
  let cur=n,d=depth,names=[],subs=[],p=path+'|'+n.key;
  let [t0,s0]=labelOf(n,depth,l1,l2); names.push(t0); subs.push(s0);
  while(depth>=1&&d<3&&cur.kids&&cur.kids.size===1){
    const only=[...cur.kids.values()][0];
    if(Math.abs(only.tot-cur.tot)>1)break;
    d++; const [t,s]=labelOf(only,d,l1,l2);
    if(t!==names[names.length-1])names.push(t);
    subs.push(s); cur=only; p+='|'+only.key;
  }
  const kids=cur.kids?[...cur.kids.values()].sort((a,b)=>b.tot-a.tot):null;
  const has=kids&&kids.length;
  const title=names.join(' · ');
  let sub=depth===0?subs[0]:subs[subs.length-1];
  if(depth>=1&&depth<3&&has)sub=(sub?sub+' · ':'')+kids.length+' inside';
  const pct=grand?Math.max(0,n.tot)/grand*100:0;
  const dl=prevMap?delta(n.tot,prevMap.get(p),cmpScale):'';
  let sp='',tg='';
  if(depth===0){
    const row=matrix()[n.key]||[];
    const wv=win(row,from,to);
    sp=sparkline(wv.length>=3?wv:win(row,Math.max(0,to-11),to),color);
    tg=tag(wv);
  }
  const inner=has?`<div class="kids"><div><div class="inset">${kids.map(k=>node(k,d+1,grand,color,l1,l2,p,prevMap,mths)).join('')}</div></div></div>`:'';
  return `<div class="node d${depth}" data-open="0">
    <button class="bar ${depth===0?'d0grid':''}" ${has?'':'tabindex="-1" style="cursor:default"'}>
      ${has?`<span class="twist">+</span>`:`<span class="leafdot"></span>`}
      <span class="nm"><span class="t">${title}${tg}</span>${sub?`<span class="s">${sub}</span>`:''}</span>
      ${depth===0?sp:''}
      <span class="amt"><span class="big ${n.tot<0?'neg':''}">${cr(n.tot)}</span>
        <span class="per">${cr(n.tot/mths)}/mo${depth===0&&pct>=1?` · ${pct.toFixed(0)}%`:''}${dl?' · '+dl:''}</span></span>
      ${depth===0?`<span class="share"><i style="width:${pct}%;background:${color}"></i></span>`:''}
    </button>${inner}</div>`;
}

// ---------- render ----------
function draw(){
  const mths=to-from+1;
  const idx=scan(from,to,inCo);
  const ord=orders(idx);
  const root=collect(idx,ord);
  const cw=cmpWindow();
  let prevMap=null;
  cmpScale = cw&&cw[2] ? mths/cw[3] : null;      // short window -> scale to the same length
  if(cw){prevMap=flat(collect(scan(cw[0],cw[1],inCo),ord),'',new Map());}
  const all=[...root.values()].sort((a,b)=>
    (D.deptKeys.indexOf(a.key))-(D.deptKeys.indexOf(b.key))||b.tot-a.tot);
  const grand=all.reduce((a,b)=>a+Math.max(0,b.tot),0);
  const colour={}; all.forEach((d,i)=>colour[d.key]=PAL[i%PAL.length]);
  paintDeptChips(all,grand,colour);
  if(dept!=='ALL'&&!all.some(d=>d.key===dept))dept='ALL';
  const tree=dept==='ALL'?all:all.filter(d=>d.key===dept);
  el('tree').innerHTML=tree.length
    ?tree.map(d=>node(d,0,grand,colour[d.key],NAMES[(ord[d.key]||['sub','cc'])[0]],
        NAMES[(ord[d.key]||['sub','cc'])[1]],'',prevMap,mths)).join('')
    :`<div class="empty">nothing posted in this window</div>`;
  if(dept!=='ALL'){const n=el('tree').querySelector('.node.d0'); if(n)n.dataset.open='1';}
  el('tree').querySelectorAll('.bar').forEach(b=>{
    const n=b.parentElement;
    if(!n.querySelector(':scope > .kids'))return;
    b.onclick=()=>{n.dataset.open=n.dataset.open==='1'?'0':'1';};
  });
  paintSummary(mths,cw);
}

// ---------- department chips ----------
function paintDeptChips(all,grand,colour){
  const host=el('deptPills');
  host.innerHTML='<span class="lab">Department</span>';
  const mk=(k,label,amt,c)=>{
    const b=document.createElement('button');
    b.className='pill dept'; b.setAttribute('aria-pressed',dept===k);
    b.innerHTML=(c?`<i style="background:${c}"></i>`:'')+label+(amt!==null?` <b>${cr(amt)}</b>`:'');
    b.onclick=()=>{dept=k;draw();
      if(k!=='ALL')el('depts').scrollIntoView({behavior:'smooth',block:'start'});};
    host.appendChild(b);
  };
  mk('ALL','All '+all.length,grand,null);
  for(const d of all)mk(d.key,deptMeta(d.key).label,d.tot,colour[d.key]);
}

// ---------- period controls ----------
function opt(sel,i){return `<option value="${i}" ${i===sel?'selected':''}>${niceLong(MO[i])}</option>`;}
function buildControls(){
  el('fromSel').innerHTML=MO.map((m,i)=>opt(from,i)).join('');
  el('toSel').innerHTML=MO.map((m,i)=>opt(to,i)).join('');
  el('fromSel').onchange=e=>{from=+e.target.value; if(from>to)to=from; buildControls(); draw();};
  el('toSel').onchange=e=>{to=+e.target.value; if(to<from)from=to; buildControls(); draw();};
  el('presets').querySelectorAll('.pill').forEach(b=>b.setAttribute('aria-pressed',b.dataset.k===activePreset()));
}
const M0=i=>MO[i];
function activePreset(){
  const l=to-from+1;
  if(from===OPEN&&to===LAST)return 'all';
  if(M0(from)==='2026-04'&&to===LAST)return 'fy';
  if(M0(from)==='2025-04'&&M0(to)==='2026-03')return 'lfy';
  if(to===LAST&&l===3)return 'm3';
  if(to===LAST&&l===6)return 'm6';
  if(to===LAST&&l===12)return 'm12';
  return '';
}
const PRESETS=[
  ['fy','This year so far',()=>[Math.max(0,MO.indexOf('2026-04')),LAST]],
  ['lfy','Last full year',()=>[MO.indexOf('2025-04'),MO.indexOf('2026-03')]],
  ['m3','Last 3 months',()=>[LAST-2,LAST]],
  ['m6','Last 6 months',()=>[LAST-5,LAST]],
  ['m12','Last 12 months',()=>[LAST-11,LAST]],
  ['all','Everything since Apr 2025',()=>[OPEN,LAST]],
];
el('presets').innerHTML='<span class="lab">Period</span>'+PRESETS.map(([k,l])=>
  `<button class="pill" data-k="${k}">${l}</button>`).join('');
el('presets').querySelectorAll('.pill').forEach(b=>b.onclick=()=>{
  const p=PRESETS.find(x=>x[0]===b.dataset.k); let [f,t]=p[2]();
  from=Math.max(0,f); to=Math.min(MO.length-1,t); buildControls(); draw();});

function pills(host,items,get,set,lab){
  host.innerHTML=lab?`<span class="lab">${lab}</span>`:'';
  items.forEach(([v,l,title])=>{
    const b=document.createElement('button');
    b.className='pill';b.textContent=l;if(title)b.title=title;
    b.setAttribute('aria-pressed',get()===v);
    b.onclick=()=>{set(v);host.querySelectorAll('.pill').forEach(x=>x.setAttribute('aria-pressed',x===b));draw();};
    host.appendChild(b);});
}
pills(el('coPills'),[['ALL','Everything'],...COS.map(c=>[c,CO[c].n])],()=>co,v=>{co=v;MX=null;},'Company');
pills(el('lvlPills'),[['auto','Whatever reads best'],['sub','Team'],['cc','Cost centre']],()=>lvl,v=>lvl=v,'Then split by');
pills(el('cmpPills'),[['off','Don’t compare'],['prev','The period before'],['yoy','Same months last year']],
      ()=>cmp,v=>cmp=v,'Compare with');

// ---------- summary blocks ----------
function paintSummary(mths,cw){
  const tot=totalOf(from,to,inCo);
  const gTot=totalOf(from,to);
  const label=from===to?niceLong(MO[from]):`${niceLong(MO[from])} – ${niceLong(MO[to])}`;
  el('heroTotal').textContent=cr(gTot);
  el('heroPer').textContent=cr(gTot/mths)+' a month · '+mths+' month'+(mths>1?'s':'');
  el('heroLabel').textContent=label;
  el('periodEcho').innerHTML=`Showing <b>${label}</b>${co==='ALL'?', all three companies':', '+CO[co].full}`
    +(dept!=='ALL'?` · <b>${deptMeta(dept).label}</b> only`:'')
    +(cw?` · compared with <b>${niceLong(MO[cw[0]])} – ${niceLong(MO[cw[1]])}</b>`
        +(cw[2]?` <span style="color:var(--gold)">(only ${cw[3]} month${cw[3]>1?'s':''} exist that far back, so the change below is per-month, scaled up to ${mths})</span>`:'')
      :'')
    +(cmp!=='off'&&!cw?` · <span style="color:var(--coral)">the books don't go back far enough to compare this window</span>`:'');
  const cl=[];for(let i=from;i<=to;i++)if(isClosing(i))cl.push(MO[i]);
  el('closeWarn').innerHTML=cl.length
    ?`<div class="note r" style="margin-top:18px"><h4>This window includes the first year's closing entries</h4>
      <p>${cl.length} of the ${mths} months you picked (${cl.map(nice).join(', ')}) fall in <b>Sep 2024 – Mar 2025</b> — the stretch that carries the SAP cutover and the FY 24-25 year-end close.
      March 2025 alone is <b>−₹56.43 Cr</b>, because the whole year's expense was closed out in it. Those are genuine entries, but they are not a month's spending, and any average that includes them is meaningless.</p></div>`
    :'';
  el('exclNote').textContent=cr(excludedOf(from,to))+' in this window';
  el('stamp').innerHTML=`Pulled <b>${D.pulled}</b> · books start ${niceLong(MO[0])} · `
    +`${niceLong(D.partial)} left out, it is only part-posted · groups 561–569, net of credits`;
  el('foot').textContent='pulled '+D.pulled;

  const cTot={},cPrev={};
  for(const c of COS){cTot[c]=totalOf(from,to,x=>COS[x[C_CO]]===c);
    if(cw)cPrev[c]=totalOf(cw[0],cw[1],x=>COS[x[C_CO]]===c);}
  el('coCards').innerHTML=COS.map(c=>`<div class="card ${CO[c].cls}">
    <div class="k">${CO[c].full}</div><div class="v">${cr(cTot[c]/mths)}</div>
    <div class="m">a month · ${cr(cTot[c])} over ${mths} month${mths>1?'s':''} · ${gTot?(cTot[c]/gTot*100).toFixed(0):0}% of the group
    ${cw?`<br>${delta(cTot[c],cPrev[c],cmpScale)}`:''}</div></div>`).join('')
   +`<div class="card r"><div class="k">All three together</div><div class="v">${cr(gTot/mths)}</div>
     <div class="m">a month · ${cr(gTot)} over ${mths} month${mths>1?'s':''}
     ${cw?`<br>${delta(gTot,totalOf(cw[0],cw[1]),cmpScale)}`:''}</div></div>`;

  const cols=MO.slice(from,to+1);
  const wide=cols.length<=8;
  el('coTable').innerHTML=`<table><thead><tr><th>Company</th>${wide?cols.map(m=>`<th>${nice(m)}</th>`).join(''):''}<th>${label}</th><th>Per month</th>${cw?'<th>Change</th>':''}</tr></thead><tbody>
  ${COS.map(c=>{const f=x=>COS[x[C_CO]]===c;return `<tr><td>${CO[c].full}</td>
    ${wide?cols.map(m=>{const v=totalOf(MO.indexOf(m),MO.indexOf(m),f);return `<td class="n ${v<0?'neg':''}">${inr(v)}</td>`;}).join(''):''}
    <td class="n">${inr(cTot[c])}</td><td class="n">${inr(cTot[c]/mths)}</td>
    ${cw?`<td class="n">${delta(cTot[c],cPrev[c],cmpScale)}</td>`:''}</tr>`;}).join('')}
  <tr class="sum"><td>Group</td>
    ${wide?cols.map(m=>`<td class="n">${inr(totalOf(MO.indexOf(m),MO.indexOf(m)))}</td>`).join(''):''}
    <td class="n">${inr(gTot)}</td><td class="n">${inr(gTot/mths)}</td>
    ${cw?`<td class="n">${delta(gTot,totalOf(cw[0],cw[1]),cmpScale)}</td>`:''}</tr></tbody></table>`;

  chart(cw);
  const gm=MO.map((m,i)=>totalOf(i,i));
  const sel=gm.slice(from,to+1);
  const hi=sel.indexOf(Math.max(...sel)), lo=sel.indexOf(Math.min(...sel));
  el('watchSay').innerHTML=`Across ${label} the months run from <b>${cr(sel[lo])}</b> in ${nice(MO[from+lo])}
   to <b>${cr(sel[hi])}</b> in ${nice(MO[from+hi])} — a spread of ${cr(sel[hi]-sel[lo])}.
   A lot of that is provisions going on and coming off, not spending changing. Use the average, ${cr(gTot/mths)} a month, and drill in before you act on any single month.`;
}

// ---------- trend lines ----------
let cmode='dept';
function chart(cw){
  const dm=matrix(), cm=coMatrix();
  const dkeys=D.deptKeys.filter(k=>dm[k]&&dm[k].some(v=>v!==0));
  const group=MO.map((m,i)=>dkeys.reduce((a,k)=>a+dm[k][i],0));
  const opIdx=MO.map((m,i)=>i).filter(i=>!isClosing(i));
  const indexed=cmode==='idx';
  let lines;
  if(cmode==='co')      lines=COS.map(c=>({k:c,label:CO[c].full,v:cm[c]||new Array(MO.length).fill(0),c:CO[c].c,w:2.3}));
  else if(cmode==='grp')lines=[{k:'grp',label:'All three companies',v:group,c:'#2EE6A8',w:2.9}];
  else if(indexed)      lines=dkeys.map((k,i)=>{
      const n=Math.min(3,to-from+1);
      const base=sum(win(dm[k],from,from+n-1))/n, b=Math.abs(base)||1;
      return {k,label:deptMeta(k).label,v:dm[k].map(v=>v/b*100),c:PAL[i%PAL.length],w:2};});
  else                  lines=dkeys.map((k,i)=>({k,label:deptMeta(k).label,v:dm[k],c:PAL[i%PAL.length],w:2}));

  const vis=indexed?MO.map((m,i)=>i).filter(i=>i>=from&&i<=to):opIdx;
  // when one department is selected, scale to it alone; otherwise use a 3rd-97th
  // percentile band so a single outlier line doesn't flatten the other ten.
  // anything outside the band is drawn clipped at the edge, and the legend says so.
  const focus = dept!=='ALL'&&(cmode==='dept'||indexed) ? lines.filter(l=>l.k===dept) : lines;
  const flatv=focus.flatMap(l=>vis.map(i=>l.v[i]||0)).sort((a,b)=>a-b);
  let hi,lo,clipped=false;
  if(!flatv.length){hi=1;lo=-1;}
  else if(focus.length===1||flatv.length<8){hi=Math.max(flatv[flatv.length-1],0);lo=Math.min(flatv[0],0);}
  else{
    const q=p=>flatv[Math.min(flatv.length-1,Math.max(0,Math.round((flatv.length-1)*p)))];
    hi=Math.max(q(.97),0); lo=Math.min(q(.03),0);
    clipped = flatv[flatv.length-1]>hi || flatv[0]<lo;
  }
  if(hi===lo){hi+=1;lo-=1;}
  const pad=(hi-lo)*.08; hi+=pad; lo-=pad;
  const W=Math.max(860,MO.length*44), H=270, PL=62, PB=30, PT=14;
  const ch=H-PB-PT, y=v=>PT+ch*(hi-v)/((hi-lo)||1), z=y(0);
  const x=i=>PL+(MO.length>1?i/(MO.length-1)*(W-PL-14):0);
  const cy=v=>Math.min(PT+ch,Math.max(PT,y(v)));
  const fmtY=v=>indexed?String(Math.round(v)):(Math.abs(v)>=1e7?(v/1e7).toFixed(1)+'Cr':(v/1e5).toFixed(0)+'L');
  const colw=MO.length>1?(W-PL-14)/(MO.length-1):40;

  let s=`<div style="overflow-x:auto"><svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" style="max-width:none">`;
  s+=`<rect x="${PL}" y="${PT}" width="${W-PL-8}" height="${ch}" fill="#0A0C11"/>`;
  if(cw)s+=`<rect x="${x(cw[0])}" y="${PT}" width="${Math.max(6,x(cw[1])-x(cw[0]))}" height="${ch}" fill="#FFB020" opacity=".09"/>`;
  s+=`<rect x="${x(from)}" y="${PT}" width="${Math.max(6,x(to)-x(from))}" height="${ch}" fill="#2EE6A8" opacity=".07"/>`;
  for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4, yy=y(v);
    s+=`<line x1="${PL}" x2="${W-8}" y1="${yy}" y2="${yy}" stroke="#171C24"/>`
     +`<text x="${PL-8}" y="${yy+3.5}" text-anchor="end" fill="#69737F" font-size="9.5" font-family="IBM Plex Mono,monospace">${fmtY(v)}</text>`;}
  if(lo<0&&hi>0)s+=`<line x1="${PL}" x2="${W-8}" y1="${z}" y2="${z}" stroke="#39424F" stroke-width="1.4"/>`;
  if(indexed)s+=`<line x1="${PL}" x2="${W-8}" y1="${y(100)}" y2="${y(100)}" stroke="#39424F" stroke-width="1.2" stroke-dasharray="4 4"/>`;

  for(const l of lines){
    const dim=dept!=='ALL'&&(cmode==='dept'||indexed)&&l.k!==dept;
    const seg=[]; let cur=[];
    MO.forEach((m,i)=>{
      const skip=indexed?(i<from||i>to):isClosing(i);
      if(skip){if(cur.length){seg.push(cur);cur=[];}return;}
      cur.push([x(i),cy(l.v[i]||0)]);});
    if(cur.length)seg.push(cur);
    for(const g of seg){
      if(g.length===1){s+=`<circle cx="${g[0][0]}" cy="${g[0][1]}" r="2.2" fill="${l.c}" opacity="${dim?.18:.95}"/>`;continue;}
      s+=`<polyline points="${g.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')}" fill="none" stroke="${l.c}" stroke-width="${dim?1:l.w}" opacity="${dim?.18:.95}" stroke-linejoin="round" stroke-linecap="round"/>`;}
    if(!dim){const li=indexed?to:MO.length-1;
      s+=`<circle cx="${x(li)}" cy="${cy(l.v[li]||0)}" r="2.8" fill="${l.c}"/>`;}
  }
  MO.forEach((m,i)=>{
    const insel=i>=from&&i<=to;
    const tip=lines.filter(l=>!(dept!=='ALL'&&(cmode==='dept'||indexed)&&l.k!==dept))
      .map(l=>`${l.label}: ${indexed?Math.round(l.v[i]||0):cr(l.v[i]||0)}`).slice(0,12).join('\n');
    s+=`<rect x="${x(i)-colw/2}" y="${PT}" width="${colw}" height="${ch}" fill="transparent" style="cursor:pointer" data-m="${i}"><title>${niceLong(m)}${isClosing(i)?' — cutover / year-end close':''}\n${tip}</title></rect>`;
    if(i%2===0||MO.length<=14)
      s+=`<text x="${x(i)}" y="${H-PB+15}" text-anchor="middle" fill="${insel?'#F5F7FA':'#5A6472'}" font-size="8.5" font-family="IBM Plex Mono,monospace">${m.slice(5)}/${m.slice(2,4)}</text>`;});
  s+='</svg></div>';
  el('trendChart').innerHTML=s;
  el('trendChart').querySelectorAll('[data-m]').forEach(r=>r.onclick=()=>{from=to=+r.dataset.m;buildControls();draw();});

  el('chartLegend').innerHTML=lines.map(l=>{
    const dim=dept!=='ALL'&&(cmode==='dept'||indexed)&&l.k!==dept;
    return `<span style="opacity:${dim?.32:1}"><b style="color:${l.c}">—</b> ${l.label}</span>`;}).join('')
    +(indexed?`<span style="color:var(--ink3)">each line starts at 100 — shape, not size</span>`
             :`<span style="color:var(--ink3)">cutover and year-end months are cut out of the lines</span>`)
    +(clipped?`<span style="color:var(--gold)">scale trimmed to the middle 94% — a line touching the top or bottom edge runs past it. Pick one department to see its true range.</span>`:'')
    +(dept!=='ALL'&&(cmode==='dept'||indexed)?`<span style="color:var(--mint)">scaled to ${deptMeta(dept).label}</span>`:'');

  const mths=to-from+1;
  const rows=dkeys.map((k,i)=>{
    const wv=win(dm[k],from,to), t=trendOf(wv), now=sum(wv);
    let prev=null;
    if(cw){prev=sum(win(dm[k],cw[0],cw[1]))*(cw[2]?mths/cw[3]:1);}
    return {k,label:deptMeta(k).label,c:PAL[i%PAL.length],now,prev,pct:t?t.pct:null,
      chg:prev===null?null:now-prev,
      chgPct:(prev===null||!Math.abs(prev))?null:(now-prev)/Math.abs(prev)*100};
  }).sort((a,b)=>b.now-a.now);
  const gTot=rows.reduce((a,b)=>a+b.now,0);
  const col=p=>p===null?'var(--ink3)':(p>2.5?'var(--up)':p<-2.5?'var(--down)':'var(--ink3)');
  el('deptTable').innerHTML=`<table><thead><tr><th>Department</th>
    <th>${from===to?niceLong(MO[from]):niceLong(MO[from])+' – '+niceLong(MO[to])}</th><th>Per month</th><th>Share</th>
    ${cw?'<th>vs before</th>':''}<th>Trend</th></tr></thead><tbody>
    ${rows.map(r=>`<tr><td><b style="color:${r.c}">—</b> ${r.label}</td>
      <td class="n ${r.now<0?'neg':''}">${inr(r.now)}</td><td class="n">${inr(r.now/mths)}</td>
      <td class="n" style="color:var(--ink3)">${gTot?(Math.max(0,r.now)/gTot*100).toFixed(1)+'%':'—'}</td>
      ${cw?`<td class="n" style="color:${r.chg===null?'var(--ink3)':(r.chg>0?'var(--up)':'var(--down)')}">${r.chg===null?'—':(r.chg>0?'▲ ':'▼ ')+cr(Math.abs(r.chg))+(r.chgPct!==null?` (${r.chg>0?'+':'−'}${Math.abs(r.chgPct).toFixed(0)}%)`:'')}</td>`:''}
      <td class="n" style="color:${col(r.pct)}">${r.pct===null?'—':(r.pct>0?'+':'')+r.pct.toFixed(1)+'%/mo'}</td></tr>`).join('')}
    <tr class="sum"><td>All departments</td><td class="n">${inr(gTot)}</td><td class="n">${inr(gTot/mths)}</td><td class="n">100%</td>${cw?'<td></td>':''}<td></td></tr>
    </tbody></table>`;

  const ranked=rows.filter(r=>r.chg!==null).sort((a,b)=>b.chg-a.chg);
  el('movers').innerHTML=(cw&&ranked.length)?`
   <div class="mv bad"><h5>Costing more than before</h5><ol>${ranked.filter(r=>r.chg>0).slice(0,5).map(r=>
     `<li><span><b style="color:${r.c}">—</b> ${r.label}</span><span class="v up">▲ ${cr(r.chg)}${r.chgPct!==null?` · +${Math.abs(r.chgPct).toFixed(0)}%`:''}</span></li>`).join('')||'<li><span style="color:var(--ink3)">nothing went up</span></li>'}</ol></div>
   <div class="mv good"><h5>Costing less than before</h5><ol>${ranked.filter(r=>r.chg<0).sort((a,b)=>a.chg-b.chg).slice(0,5).map(r=>
     `<li><span><b style="color:${r.c}">—</b> ${r.label}</span><span class="v down">▼ ${cr(Math.abs(r.chg))}${r.chgPct!==null?` · −${Math.abs(r.chgPct).toFixed(0)}%`:''}</span></li>`).join('')||'<li><span style="color:var(--ink3)">nothing came down</span></li>'}</ol></div>`
   :`<div class="mv"><h5>Risers and fallers</h5><ol><li><span style="color:var(--ink3)">turn on a comparison above and the biggest movers land here</span></li></ol></div>`;

  const fy=MO.map((m,i)=>i).filter(i=>MO[i]>='2025-04'&&MO[i]<'2026-04');
  const avgL=fy.reduce((a,i)=>a+group[i],0)/(fy.length||1);
  const selAvg=sum(win(group,from,to))/mths;
  const rising=rows.filter(r=>r.pct!==null&&r.pct>2.5).sort((a,b)=>b.pct-a.pct);
  const falling=rows.filter(r=>r.pct!==null&&r.pct<-2.5).sort((a,b)=>a.pct-b.pct);
  el('trendSay').innerHTML=`Last full year ran <b>${cr(avgL)}</b> a month. Your window averages <b>${cr(selAvg)}</b>`
   +(avgL?` — ${selAvg>avgL?'up':'down'} <b>${Math.abs((selAvg-avgL)/avgL*100).toFixed(0)}%</b> on it`:'')+'.'
   +(mths>=3?`<br><br><b style="color:var(--up)">${rising.length} department${rising.length===1?'':'s'} rising</b>`
      +(rising.length?` — ${rising.slice(0,3).map(r=>`${r.label} <b>+${r.pct.toFixed(0)}%/mo</b>`).join(', ')}`:'')
      +` and <b style="color:var(--down)">${falling.length} falling</b>`
      +(falling.length?` — ${falling.slice(0,3).map(r=>`${r.label} <b>${r.pct.toFixed(0)}%/mo</b>`).join(', ')}`:'')+'.'
     :`<br><br>Pick three months or more and every department gets a rising / falling read.`)
   +` The seven months before Apr 2025 are the SAP cutover and the FY 24-25 close — March 2025 alone is −₹56.43 Cr — so they are cut out of the lines.`;
}

pills(el('chartPills'),[['dept','Every department'],['idx','Indexed \u2014 compare shapes'],['co','By company'],['grp','Group total only']],
      ()=>cmode,v=>cmode=v,'Chart');
buildControls();
draw();

// ---------- reconciliation: their file (Oil + Beverages) vs SAP, May-Jul 2026 ----------
(function(){
  const R=D.recon; if(!R||!R.length)return;
  const RM=['2026-05','2026-06','2026-07'], RL=['May','Jun','Jul'];
  const fT=R.reduce((a,b)=>a+b.tTot,0), sT=R.reduce((a,b)=>a+b.sTot,0);
  const dis=R.filter(r=>r.cls==='disputed'), near=R.filter(r=>r.cls!=='disputed');
  const tie=R.filter(r=>r.cls==='match'||r.cls==='timing');
  const nd=near.reduce((a,b)=>a+b.diff,0);
  el('rKpi').innerHTML=`
   <div class="card"><div class="k">Their file</div><div class="v">${cr(fT)}</div><div class="m">Oil + Beverages, May–Jul 2026</div></div>
   <div class="card t"><div class="k">SAP, same scope</div><div class="v">${cr(sT)}</div><div class="m">same two companies, pulled live</div></div>
   <div class="card t"><div class="k">Gap</div><div class="v" style="color:var(--down)">${cr(sT-fT)}</div><div class="m">${Math.abs((sT-fT)/fT*100).toFixed(2)}% of their total — they are right</div></div>
   <div class="card o"><div class="k">Cells agreeing</div><div class="v">${near.length}<span style="font-size:17px;color:var(--ink3)"> of ${R.length}</span></div><div class="m">${tie.length} tie to the rupee · ${near.length} within ₹50,000</div></div>`;
  el('rLead').innerHTML=`Their workbook says ${cr(fT)}. SAP, on the same two companies and the same three months, says <b>${cr(sT)}</b> —
   <b>${cr(Math.abs(sT-fT))} apart, ${Math.abs((sT-fT)/fT*100).toFixed(2)}%</b>. ${tie.length} of the ${R.length} cells tie to the rupee and ${near.length} are within ₹50,000 of each other.
   Nobody needs to redo that workbook. What is left is ordinary: one June journal of ₹24.10 L their extract predates, a Beverages digital-marketing row where they picked up only July,
   and a scatter of cells a few thousand apart — the signature of an extract pulled a few days before mine.`;
  const CL={match:['agrees','var(--down)'],timing:['same total, different month','var(--down)'],minor:['under ₹50,000 apart','var(--ink3)'],
            reclass:['a reclass entry','var(--gold)'],provision:['provision timing','var(--gold)'],disputed:['still differs','var(--up)']};
  el('rBody').innerHTML=`
  <div class="tw"><table><thead><tr><th>Budget · Sub Budget</th>${RL.map(l=>`<th>${l}</th>`).join('')}<th>Three months</th><th>Verdict</th></tr></thead><tbody>
  ${R.slice().sort((a,b)=>Math.abs(b.diff)-Math.abs(a.diff)).map(r=>`<tr>
    <td>${r.cc3==='(blank)'?'Not tagged':r.cc3} <span style="color:var(--ink3);font-size:12px">· ${r.cc4==='(blank)'?'—':r.cc4}</span></td>
    ${RM.map(m=>`<td class="n"><span style="color:var(--ink3);font-size:12px">${inr(r.their[m]||0)}</span><br>${inr(r.sap[m]||0)}</td>`).join('')}
    <td class="n"><span style="color:var(--ink3);font-size:12px">${inr(r.tTot)}</span><br>${inr(r.sTot)}</td>
    <td style="text-align:right;font-size:12.5px;color:${CL[r.cls][1]}">${CL[r.cls][0]}<br><span class="n" style="color:var(--ink3);font-size:11.5px">${r.diff?(r.diff>0?'+':'')+inr(r.diff):'—'}</span></td></tr>`).join('')}
  </tbody></table></div>
  <p class="say" style="font-size:13.5px">Grey figure is their workbook, white one is SAP. Right column is SAP minus workbook.</p>
  <div class="note"><h4>The four that still differ, largest first</h4>
   <p><b>Factory ₹31.80 L</b> — their figure is higher than everything SAP holds under that cost centre for both companies. Still open.<br>
   <b>Not tagged / Short &amp; Excess ₹16.13 L</b> — their file carries ₹16.76 L against a blank cost centre; SAP has ₹62,739.<br>
   <b>Media Marketing · DIG MKT ₹15.65 L</b> — a Beverages row where their extract has July only; SAP also has May ₹10.9 L and June ₹5 L.<br>
   <b>NPD 2 ↔ One Time Expense ₹24.10 L each way</b> — one June journal moved cost between the two. Nets to ₹14,339. Their extract predates it.</p></div>
  <div class="note t"><h4>What was tested, and what actually mattered</h4>
   <p>Wider account range, gross debits instead of net, the vendor's invoice date instead of the posting date, months shifted by one, and SAP spreading costs between centres — none of those explained anything. Every Dimension-3 rule is <code>Direct = Y</code> at 100% to itself, so no allocation exists.</p>
   <p><b>The one that mattered was company scope</b>, and I had dismissed it. Worth asking of any figures file in future: which companies does this cover? One line of context would have saved the whole chase.</p></div>`;
})();
