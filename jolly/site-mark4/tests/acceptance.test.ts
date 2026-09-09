import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { eligibility, rateFor, DEFAULT_SCENARIO, LINE_IDS, PLANNING_SPEEDS } from '../lib/rules.ts';
import { buildModel } from '../lib/model.ts';
import type { Mark4Input, Product, Scenario, Mark4Model } from '../lib/types.ts';

// Independent acceptance fixtures: business inputs and conservation identities,
// rather than expected copies of the engine's allocation order.
const noNight: Scenario = { ...DEFAULT_SCENARIO, nightLine: null };
const input = (): Mark4Input => ({
  schemaVersion: 1,
  meta: { as_of: '2026-09-07T08:00:00+05:30', month: 'September 2026' },
  plan: [], bom: {}, blends: {}, items: {}, realise: {},
  opening: { stock: {}, fg: {}, fg_other_l: 0, standing_l: 0 },
  orders: [], inbound_prebooked: {}, inbound_provenance: {},
  lines: { 'JP Machine': {'1L': 100}, 'Clear Pack': {'1L': 100, '5L': 40}, '10 Head': {'1L':100, '2L':50, '5L':20}, '6 Head': {'1L':100, '2L':50, '5L':20}, 'Tin Head': {TIN:10}, 'Pouch Machine': {POUCH:100} },
  history: { status:'complete', missing_dates:[], days: Array.from({length:6}, (_,i)=>({ date:`2026-09-0${i+1}`, made_mes_l:0, made_booked_l:0, booked_by_item:{}, complete:true })) },
  sources:[{id:'factory-stock',label:'QA fixed stock',asOf:'2026-09-07T08:00:00+05:30',ok:true}],
});
function add(i:Mark4Input, code:string, {pieces=1000, litres=1, category='SUNFLOWER', container='bottle', grams=40, carton=20}:{pieces?:number;litres?:number;category?:string;container?:string;grams?:number;carton?:number}={}) {
  i.plan.push({code,sku:`${category} ${litres} LTR ${carton} PCS`,category,pack_type:'PET',litres_per_piece:litres,pieces});
  i.items[code]={name:`${category} ${litres} LTR ${carton} PCS`,uom:'PCS'};
  const pm=`PM-${code}`;
  i.items[pm]={name:container==='bottle'?`PET BOTTLE ${litres} LTR ${grams} GM`:container==='tin'?`PRINTED TIN ${litres} LTR`:container==='pouch'?'POUCH FILM':'DRUM 200 LTR',uom:'PCS'};
  i.items['RM-OIL']={name:'SUNFLOWER OIL',uom:'LTR'};
  i.items[`CARTON-${carton}`]={name:`CORRUGATED CARTON ${carton} PCS`,uom:'PCS'};
  i.bom[code]=[['RM-OIL',litres],[pm,1],[`CARTON-${carton}`,1/carton]];
  i.opening.stock[pm]=1000000; i.opening.stock['RM-OIL']=1000000; i.opening.stock[`CARTON-${carton}`]=1000000;
  i.realise[code]=100;
}
function product(m:Mark4Model, code:string) { const p=m.products.find(p=>p.code===code || p.originalCodes.includes(code)); assert.ok(p,`Product ${code} must exist`); return p; }
function runs(m:Mark4Model) { return m.days.flatMap(d=>d.runs); }
function close(a:number,b:number,msg:string) { assert.ok(Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<1e-5,`${msg}: ${a} != ${b}`); }
const p = (patch:Partial<Product>={}): Pick<Product,'packLitres'|'container'|'category'|'name'|'bottleGrams'|'exclusionReason'> => ({ packLitres:1,container:'bottle',category:'SUNFLOWER',name:'SUNFLOWER 1 LTR 20 PCS',bottleGrams:40,exclusionReason:null,...patch });

test('M1-M3: 3 L plastic supported on heads, never Clear Pack; 15 L tins only Tin Head',()=>{
  assert.equal(eligibility(p({packLitres:3}),'Clear Pack').allowed,false);
  for(const line of ['10 Head','6 Head']) assert.equal(eligibility(p({packLitres:3}),line).allowed,true);
  for(const line of LINE_IDS) assert.equal(eligibility(p({packLitres:15,container:'tin'}),line).allowed,line==='Tin Head',line);
  for(const line of LINE_IDS) assert.equal(eligibility(p({packLitres:3,container:'tin'}),line).allowed,false,'unresolved tin routing must stay held');
});
test('M4-M10: preferences retain valid alternatives; yellow/sesame constraints and pouch isolation',()=>{
  assert.ok(eligibility(p({category:'MUSTARD'}),'JP Machine').preference > eligibility(p({category:'GROUNDNUT'}),'JP Machine').preference);
  assert.equal(eligibility(p({category:'YELLOW MUSTARD'}),'JP Machine').allowed,false);
  assert.equal(eligibility(p({category:'SESAME'}),'Clear Pack').allowed,false);
  assert.equal(eligibility(p({bottleGrams:52}),'Clear Pack').allowed,true);
  assert.equal(eligibility(p({bottleGrams:52}),'10 Head').allowed,true);
  assert.ok(eligibility(p({packLitres:5,container:'tin'}),'6 Head').preference > eligibility(p({packLitres:5,container:'tin'}),'10 Head').preference);
  assert.equal(eligibility(p({packLitres:5,container:'tin'}),'10 Head').allowed,true);
  for(const line of LINE_IDS) assert.equal(eligibility(p({container:'pouch'}),line).allowed,line==='Pouch Machine');
});
test('approved final rates ignore feed overrides and legacy efficiency; unsupported packs stay unavailable',()=>{
  const i=input(); i.supplements={rates:[{line:'JP Machine',pack:'1L',piecesPerHour:99999,basis:'rated',source:'QA conflicting master',asOf:'2026-09-07'}, {line:'Tin Head',pack:'15L',piecesPerHour:600,basis:'rated',source:'factory',asOf:'2026-09-07'}, {line:'Tin Head',pack:'TIN',piecesPerHour:700,basis:'rated',source:'legacy',asOf:'2026-09-07'}, {line:'Pouch Machine',pack:'POUCH-SAMARPAN',piecesPerHour:2400,basis:'rated',source:'factory',asOf:'2026-09-07'}]};
  const expected: [string, number, number][] = [['JP Machine',1,5400],['Clear Pack',1,4800],['Clear Pack',4,800],['Clear Pack',5,3000],['10 Head',1,2100],['10 Head',2,1260],['10 Head',3,720],['10 Head',5,900],['6 Head',1,1080],['6 Head',2,720],['6 Head',3,384],['6 Head',5,600]];
  for(const [line,pack,value] of expected){
    const r=rateFor(i,p({packLitres:pack}),line,.8); assert.ok(r); assert.equal(r.piecesPerHour,value); assert.equal(r.effectivePiecesPerHour,value); assert.equal(r.basis,'declared'); assert.equal(r.asOf,'2026-09-06');
  }
  i.supplements!.rates!.find(r=>r.line==='Tin Head' && r.pack==='15L')!.piecesPerHour=99999;
  assert.equal(rateFor(i,p({packLitres:15,container:'tin'}),'Tin Head',.8)?.effectivePiecesPerHour,600);
  for(const pack of [3,5,16.5]) assert.equal(rateFor(i,p({packLitres:pack,container:'tin'}),'Tin Head',1),null);
  assert.equal(rateFor(i,p({packLitres:15,container:'bottle'}),'Tin Head',1),null);
  assert.equal(rateFor(i,p({container:'pouch'}),'Pouch Machine',.4)?.effectivePiecesPerHour,1800);
  assert.equal(rateFor(i,p({container:'pouch'}),'Pouch Samarpan',1),null);
  assert.equal(rateFor(i,p({packLitres:9}),'10 Head',1),null);
  assert.equal(PLANNING_SPEEDS.length,16);
  add(i,'A'); const m=buildModel(i,noNight); assert.equal(m.planningSpeeds.length,16); assert.equal(m.lines.find(l=>l.id==='Clear Pack')?.rates.find(r=>r.pack==='4L')?.piecesPerHour,800,'policy rows remain visible without matching current products');
});
test('BOM container overrides erroneous PET sheet; drums excluded without manual runs',()=>{
  const i=input(); add(i,'TIN',{litres:15,container:'tin',pieces:600}); add(i,'DRUM',{litres:200,container:'drum',pieces:2});
  const m=buildModel(i,noNight); assert.equal(product(m,'TIN').container,'tin'); assert.equal(product(m,'TIN').plannedPieces,600,'approved Tin Head speed enables the available tin demand');
  assert.ok(runs(m).filter(r=>r.code==='TIN').every(r=>r.line==='Tin Head')); assert.equal(product(m,'DRUM').plannedPieces,0); assert.match(product(m,'DRUM').exclusionReason??'',/defer|excluded|Mark 4/i);
});
test('15 L Tin Head uses 600 tins per hour and conserves oil, tins and warehouse space',()=>{
  const i=input(); add(i,'TIN',{litres:15,container:'tin',pieces:7000,carton:1});
  const m=buildModel(i,{...noNight,efficiency:.8});
  const first=m.days[0].runs.find(r=>r.code==='TIN'); assert.ok(first);
  assert.equal(first.line,'Tin Head'); assert.equal(first.pieces,6000); assert.equal(first.hours,10); assert.equal(first.litres,90000);
  assert.equal(first.rate.effectivePiecesPerHour,600); assert.equal(first.nightHours,0);
  assert.equal(product(m,'TIN').plannedPieces,7000);
  assert.equal(m.materials.find(r=>r.code==='RM-OIL')?.consumed,105000);
  assert.equal(m.materials.find(r=>r.code==='PM-TIN')?.consumed,7000);
  assert.equal(m.summary.plannedLitres,105000);
  for(const d of m.days) close(d.storage.openingLitres+d.productionLitres-d.dispatchLitres,d.storage.closingLitres,'tin storage conservation');
});
test('night sessions are bounded and selectable; per-line allocated time includes setup',()=>{
  const i=input(); add(i,'A',{pieces:200000,category:'MUSTARD'}); add(i,'B',{pieces:30000}); add(i,'C',{pieces:30000,litres:5});
  const m=buildModel(i,{...DEFAULT_SCENARIO,nightLine:'JP Machine'}); assert.ok(runs(m).some(r=>r.nightHours>0),'night case must be exercised');
  for(const d of m.days){
    const night=new Set(d.runs.filter(r=>r.nightHours>0).map(r=>r.line)); assert.ok(night.size<=1); for(const line of night) assert.equal(line,'JP Machine');
    for(const line of LINE_IDS){const rs=d.runs.filter(r=>r.line===line); assert.ok(rs.reduce((s,r)=>s+r.dayHours,0)<=10+1e-7); assert.ok(rs.reduce((s,r)=>s+r.nightHours,0)<=10+1e-7); assert.ok(rs.reduce((s,r)=>s+r.hours+r.setupHours,0)<=(line==='JP Machine'?20:10)+1e-7);}
  }
  assert.ok(runs(buildModel(i,noNight)).every(r=>r.nightHours===0));
});
test('Sunday closes production and target but physical gate departures still occur',()=>{
  const i=input(); i.meta.as_of='2026-09-06T08:00:00+05:30'; i.opening.standing_l=1000; add(i,'A');
  const m=buildModel(i,DEFAULT_SCENARIO); const sunday=m.days.find(d=>d.date==='2026-09-06'); assert.ok(sunday); assert.equal(sunday.runs.length,0); assert.equal(sunday.productionLitres,0); assert.equal(sunday.targetValue,0); assert.ok(sunday.dispatchLitres>0,'standing stock must be allowed to leave on Sunday');
});
test('one shared packaging/oil ledger prevents two lines consuming the same units',()=>{
  const i=input(); add(i,'A',{pieces:5000,category:'MUSTARD'}); add(i,'B',{pieces:5000});
  i.bom.B=i.bom.A.map(([c,q])=>[c,q]); i.opening.stock['PM-A']=9001; i.opening.stock['RM-OIL']=9001;
  const m=buildModel(i,DEFAULT_SCENARIO); const total=runs(m).reduce((s,r)=>s+r.pieces,0); assert.ok(total>0); assert.ok(total<=9001);
  for(const mat of m.materials){assert.ok(mat.remaining>=-1e-7,mat.code); close(mat.opening+mat.arrivals-mat.consumed,mat.remaining,mat.code);}
});
test('ready blend and component oil are conserved without double credit',()=>{
  const i=input(); add(i,'A',{pieces:10000}); i.bom.A[0]=['BLEND',1]; i.items.BLEND={name:'BLENDED OIL',uom:'LTR'}; i.items.R1={name:'CANOLA OIL',uom:'LTR'}; i.items.R2={name:'OLIVE OIL',uom:'LTR'};
  i.blends.BLEND=[['R1',.75],['R2',.25]]; i.opening.stock.BLEND=1000; i.opening.stock.R1=1500; i.opening.stock.R2=500; delete i.opening.stock['RM-OIL'];
  const m=buildModel(i,noNight); close(product(m,'A').plannedPieces,3000,'1000 ready + 2000 blended litres');
  const consumed=Object.fromEntries(m.materials.map(x=>[x.code,x.consumed])); close(consumed.BLEND,1000,'ready blend'); close(consumed.R1,1500,'75% component'); close(consumed.R2,500,'25% component');
});
test('monthly make target subtracts booked MTD once, keeps PO focus, never subtracts FG twice',()=>{
  const i=input(); add(i,'A',{pieces:1000}); i.history.days[0].booked_by_item={A:400}; i.history.days[0].made_booked_l=400; i.history.days[0].made_mes_l=9999; i.opening.fg.A=200;
  i.orders=[{docnum:'QA',date:'2026-09-01',due:'2026-09-09',code:'A',pieces:700,channel:'GT'}];
  const a=product(buildModel(i,noNight),'A'); assert.equal(a.bookedMtdPieces,400); assert.equal(a.targetRemainingPieces,600); assert.equal(a.confirmedUncoveredPieces,500); assert.equal(a.requiredPieces,600); assert.equal(a.forecastPieces,100);
});
test('partial and absent historical reads remain unknown, never a completed zero',()=>{
  const i=input(); add(i,'A'); i.history={status:'partial',missing_dates:['2026-09-02'],days:[{date:'2026-09-01',made_mes_l:800,made_booked_l:100,booked_by_item:{A:100},complete:true}]};
  const m=buildModel(i,noNight); assert.equal(m.summary.historyComplete,false); assert.equal(m.summary.bookedMtdLitres,null); assert.equal(product(m,'A').bookedMtdPieces,null); assert.ok(m.actuals.some(d=>d.date==='2026-09-02' && d.made_booked_l===null && !d.complete),'missing calendar day must be visible');
});
test('verified 16 to 20 transition preserves bottle demand and consumes replacement carton only',()=>{
  const i=input(); add(i,'OLD',{pieces:10000,carton:16}); add(i,'NEW',{pieces:0,carton:20});
  i.supplements={cartonTransitions:[{from:'OLD',to:'NEW',evidence:'QA verified identical family and approved replacement BOM'}]};
  i.opening.stock['CARTON-20']=500; i.opening.stock['CARTON-16']=10000;
  const m=buildModel(i,noNight); const family=product(m,'OLD'); assert.equal(family.requiredPieces,10000); assert.equal(family.plannedPieces,10000); assert.equal(family.code,'NEW'); assert.ok(runs(m).every(r=>r.code!=='OLD'));
  close(m.materials.find(x=>x.code==='CARTON-20')?.consumed??NaN,500,'20 bottle carton use'); assert.equal(m.materials.find(x=>x.code==='CARTON-16')?.consumed??0,0);
});
test('unverified 16-piece replacement never silently produces old cartons',()=>{
  const i=input(); add(i,'OLD',{carton:16}); const m=buildModel(i,noNight); const a=product(m,'OLD'); assert.equal(a.plannedPieces,0); assert.match(`${a.transition} ${a.exclusionReason} ${a.notes.join(' ')}`,/20|replacement|transition/i);
});
test('proposed blanket arrival excluded by default; dated transit and explicit scenario differ',()=>{
  const i=input(); add(i,'A',{pieces:10000}); i.opening.stock['RM-OIL']=0; i.inbound_prebooked={'2026-09-08':{'RM-OIL':10000}}; i.inbound_provenance={'2026-09-08':{'RM-OIL':'PO-LEAD'}};
  const firm=buildModel(i,noNight); const proposed=buildModel(i,{...noNight,allowProposedSupply:true}); assert.equal(product(firm,'A').plannedPieces,0); assert.equal(product(proposed,'A').plannedPieces,10000); assert.ok(proposed.days.flatMap(d=>d.arrivals).some(a=>a.code==='RM-OIL'&&a.assumed));
  i.inbound_provenance={'2026-09-08':{'RM-OIL':'EXIM-OTW'}}; const transit=buildModel(i,noNight); assert.equal(product(transit,'A').plannedPieces,10000); assert.ok(transit.days.filter(d=>d.date<'2026-09-08').every(d=>d.productionLitres===0));
});
test('billing moves unbilled to waiting; gate alone removes physical stock',()=>{
  const i=input(); add(i,'A',{pieces:0}); i.opening.fg.A=100; i.orders=[{docnum:'QA',date:'2026-09-01',due:'2026-09-07',code:'A',pieces:100,channel:'GT'}];
  const m=buildModel(i,noNight); const first=m.days[0]; assert.equal(first.storage.openingLitres,100); assert.equal(first.storage.closingLitres,100); assert.equal(first.storage.billedWaitingLitres,100); assert.equal(first.dispatchLitres,0); assert.ok(m.days.some(d=>d.dispatchLitres===100));
  for(const d of m.days) close(d.storage.openingLitres+d.productionLitres-d.dispatchLitres,d.storage.closingLitres,`gate equation ${d.date}`);
});
test('full current seed: nonempty schedule, real source stamps, conservation, no old accuracy or automatic target claims',()=>{
  const i=JSON.parse(readFileSync(new URL('../data/seed.json',import.meta.url),'utf8')) as Mark4Input; assert.ok(i.plan.length>20); assert.ok(i.sources.length>2);
  const m=buildModel(i,DEFAULT_SCENARIO); assert.ok(m.days.length>=20); assert.ok(runs(m).length>0,'cannot pass an empty live schedule'); assert.ok(m.products.length>20); assert.ok(m.materials.length>10);
  for(const d of m.days){close(d.runs.reduce((s,r)=>s+r.litres,0),d.productionLitres,`${d.date} production`); close(d.storage.openingLitres+d.productionLitres-d.dispatchLitres,d.storage.closingLitres,`${d.date} storage`); if(d.sunday)assert.equal(d.runs.length,0); for(const r of d.runs){assert.ok(r.pieces>0);assert.ok(r.rate.source);assert.ok(product(m,r.code).containersPerPiece>0);close(r.rate.piecesPerHour,r.rate.effectivePiecesPerHour*product(m,r.code).containersPerPiece,'declared physical containers');assert.equal(product(m,r.code).eligibility[r.line].allowed,true);}}
  for(const material of m.materials){assert.ok(material.remaining>=-1e-5,material.code);close(material.opening+material.arrivals-material.consumed,material.remaining,material.code);}
  close(m.summary.plannedLitres,m.days.reduce((s,d)=>s+d.productionLitres,0),'summary litres'); assert.ok(m.rules.length>=12); assert.ok(m.questions.length>=5); assert.doesNotMatch(JSON.stringify(m.rules),/0\.16%/);
});

test('a partial carton still consumes one whole physical carton, or stays unscheduled',()=>{
  const i=input(); add(i,'A',{pieces:4819}); i.opening.stock['PM-A']=4819; i.opening.stock['CARTON-20']=241;
  const m=buildModel(i,noNight); assert.equal(product(m,'A').plannedPieces,4819,'the carton rounding case must exercise a viable production campaign');
  assert.equal(m.materials.find(x=>x.code==='CARTON-20')?.consumed,241,'4819 bottles cannot consume 240.95 physical cartons');
  const short=input(); add(short,'A',{pieces:2}); short.opening.stock['CARTON-20']=.1;
  assert.equal(product(buildModel(short,noNight),'A').plannedPieces,0,'fractional opening carton must not create a deliverable pack');
});
test('bottle with integral handle remains a bottle; carton accessory text cannot decide it',()=>{
  const i=input(); add(i,'HANDLE',{litres:2,carton:10,pieces:10000}); i.items['PM-HANDLE'].name='PET BOTTLE 2 LTR 80 GMS YELLOW HANDLE'; i.items['CARTON-10'].name='CARTON 2 LTR 10 PCS HANDLE BOTTLE PLAIN';
  const p=product(buildModel(i,noNight),'HANDLE'); assert.equal(p.container,'bottle'); assert.equal(p.plannedPieces,10000); assert.equal(p.eligibility['10 Head'].allowed,true);
});
test('forecast stock made before a future order becomes usable when that order opens',()=>{
  const i=input(); add(i,'A',{pieces:10000}); i.orders=[{docnum:'FUTURE',date:'2026-09-08',due:'2026-09-08',code:'A',pieces:10000,channel:'GT'}];
  const m=buildModel(i,noNight); assert.equal(m.days[0].productionLitres,10000,'reserve fixture must make goods before order date'); assert.equal(product(m,'A').plannedPieces,10000,'reserve already meets order; no duplicate production');
  const due=m.days.find(d=>d.date==='2026-09-08'); assert.ok(due); assert.equal(due.storage.unbilledLitres,0); assert.equal(due.storage.billedWaitingLitres,10000); const gate=m.days.find(d=>d.date==='2026-09-10'); assert.ok(gate); assert.equal(gate.dispatchLitres,10000);
});
test('current source physical FG total reconciles despite canonical 16/20 merging',()=>{
  const i=JSON.parse(readFileSync(new URL('../data/seed.json',import.meta.url),'utf8')) as Mark4Input;
  const sourceFg=i.opening.fg_litres; assert.equal(typeof sourceFg,'number','seed must retain source physical FG total for reconciliation');
  const m=buildModel(i,noNight); close(m.summary.openingStorageLitres,Number(sourceFg)+i.opening.standing_l,'physical FG source total + billed waiting');
});


test('combination sales unit with two 1 L bottles consumes two containers and half the sales-unit throughput',()=>{
  const i=input(); add(i,'COMBO',{pieces:27000,litres:2,category:'MUSTARD',carton:10});
  i.items['PM-COMBO'].name='PET BOTTLE 1 LTR 40 GMS'; i.bom.COMBO=i.bom.COMBO.map(([c,q])=>[c,c==='PM-COMBO'?2:q]); i.lines={'JP Machine':{'1L':100}};
  const m=buildModel(i,noNight); const a=product(m,'COMBO'); assert.equal(a.fillLitres,1); assert.equal(a.containersPerPiece,2); const r=m.days[0].runs[0]; assert.ok(r); assert.equal(r.line,'JP Machine'); assert.equal(r.pieces,27000); assert.equal(r.litres,54000); assert.equal(r.hours,10); assert.equal(r.rate.piecesPerHour,5400); assert.equal(r.rate.effectivePiecesPerHour,2700); assert.equal(r.materials.find(x=>x.code==='PM-COMBO')?.quantity,54000);
});
function provisionalFixture(){
  const i=input(); add(i,'OLD',{pieces:10000,carton:16});
  i.items.PM0000121={name:'PET BOTTLE 1 LTR 52 GMS',uom:'PCS'}; i.items.PM0000085={name:'CAP SAME CLOSURE',uom:'PCS'}; i.items.PM0000003={name:'CARTON 1 LTR 16 PCS',uom:'PCS'}; i.items.PM0000914={name:'CARTON GROUNDNUT 1 LTR 20 PCS',uom:'PCS'};
  i.bom.OLD=[['RM-OIL',1],['PM0000121',1],['PM0000085',1],['PM0000003',1/16]];
  i.bom.FG0000461=[['RM-OIL',1],['PM0000121',1],['PM0000085',1],['PM0000914',1/20]];
  i.items.FG0000461={name:'GROUNDNUT 1 LTR 20 PCS',uom:'PCS'};
  for(const c of ['PM0000121','PM0000085','PM0000003','PM0000914']) i.opening.stock[c]=10000;
  return i;
}
test('provisional carton switch separates conditional output and baseline, preserves identity and stock',()=>{
  const i=provisionalFixture(); const strict=buildModel(i,noNight); assert.equal(product(strict,'OLD').plannedPieces,0);
  const m=buildModel(i,{...noNight,allowProvisionalRecipes:true}); const a=product(m,'OLD'); assert.equal(a.code,'OLD'); assert.equal(a.plannedPieces,10000); assert.equal(a.conditionalRecipe,true); assert.equal(a.cartonPieces,20); assert.ok(runs(m).every(r=>r.conditionalRecipe)); assert.equal(m.summary.conditionalLitres,10000); assert.equal(m.summary.strictBaseline?.plannedLitres,strict.summary.plannedLitres); assert.equal(m.materials.find(x=>x.code==='PM0000914')?.consumed,500); assert.equal(m.materials.find(x=>x.code==='PM0000003')?.consumed??0,0);
  i.items.DIFFERENT={name:'CAP DIFFERENT CLOSURE',uom:'PCS'}; i.opening.stock.DIFFERENT=10000; i.bom.OLD=i.bom.OLD.map(([c,q])=>[c==='PM0000085'?'DIFFERENT':c,q]); assert.equal(product(buildModel(i,{...noNight,allowProvisionalRecipes:true}),'OLD').plannedPieces,0,'different closure is not compatible evidence');
});
test('purchase proposals aggregate shared materials and count cartons, not bottles',()=>{
  const i=input(); add(i,'A',{pieces:100}); add(i,'B',{pieces:200}); i.bom.B=i.bom.A.map(([c,q])=>[c,q]); i.opening.stock['PM-A']=50; i.opening.stock['CARTON-20']=0;
  i.inbound_prebooked={'2026-09-08':{'PM-A':50}}; i.inbound_provenance={'2026-09-08':{'PM-A':'EXIM-OTW'}};
  const m=buildModel(i,noNight); assert.equal(m.materials.find(x=>x.code==='PM-A')?.proposedQty,200); assert.equal(m.materials.find(x=>x.code==='CARTON-20')?.proposedQty,15);
  const s=input(); add(s,'A',{pieces:100}); s.opening.stock['CARTON-20']=0; const cart=buildModel(s,noNight).materials.find(x=>x.code==='CARTON-20'); assert.ok(cart); assert.equal(cart.proposedQty,5); assert.equal(cart.shortage,5,'100 bottles need five cartons, not100');
});
test('hypothetical buying has honest lead dates and cannot enable production before receipt',()=>{
  const i=input(); add(i,'A',{pieces:10000}); i.opening.stock['PM-A']=0; i.opening.stock['RM-OIL']=0;
  const strict=buildModel(i,noNight); assert.equal(product(strict,'A').plannedPieces,0);
  const m=buildModel(i,{...noNight,allowProposedSupply:true}); assert.equal(product(m,'A').plannedPieces,10000);
  const pm=m.materials.find(x=>x.code==='PM-A'), oil=m.materials.find(x=>x.code==='RM-OIL'); assert.ok(pm&&oil); assert.equal(pm.proposedQty,10000); assert.equal(pm.leadDays,7); assert.equal(pm.projectedArrival,'2026-09-14'); assert.equal(oil.proposedQty,10000); assert.equal(oil.leadDays,14); assert.equal(oil.projectedArrival,'2026-09-21'); assert.ok(m.days.filter(d=>d.date<'2026-09-21').every(d=>d.productionLitres===0));
  assert.ok(m.days.flatMap(d=>d.arrivals).filter(a=>['PM-A','RM-OIL'].includes(a.code)).every(a=>a.assumed));
});
test('partial valuation keeps known subtotal and unknown remainder without false target attainment',()=>{
  const i=input(); add(i,'A',{pieces:10000}); add(i,'B',{pieces:10000}); delete i.realise.B;
  const m=buildModel(i,noNight); assert.equal(m.summary.plannedLitres,20000); assert.equal(m.summary.plannedValue,null); assert.equal(m.summary.knownPlannedValue,1000000); assert.equal(m.summary.unvaluedLitres,10000); assert.equal(m.summary.valueGap,null); assert.ok(runs(m).filter(r=>r.code==='B').every(r=>r.value===null));
});
test('other-company OMS collision is quarantined while projected and exact demand stay distinct',()=>{
  const i=input(); add(i,'A',{pieces:100}); i.orders=[{docnum:'BAD',date:'2026-09-07',due:'2026-09-07',code:'A',pieces:99999,channel:'BEVERAGES',_src:'OMS'},{docnum:'GOOD',date:'2026-09-07',due:'2026-09-07',code:'A',pieces:20,channel:'OIL',_src:'OMS'},{docnum:'ALLOC',date:'2026-09-07',due:'2026-09-07',code:'A',pieces:30,channel:'ECOM',_src:'ECOM-PO',is_exact_sku_due:false}];
  const a=product(buildModel(i,noNight),'A'); assert.equal(a.confirmedPieces,50); assert.equal(a.exactOrderPieces,20); assert.equal(a.allocatedOrderPieces,30); assert.equal(a.requiredPieces,100);
});
test('source loader marks last-good retained response stale and preserves its original dates',async(t)=>{
  const i=input(); add(i,'A'); const now=Date.parse(i.meta.as_of); t.mock.method(Date,'now',()=>now); t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify(i),{headers:{'x-mark4-retained-last-good':'true'}}));
  const {loadInput}=await import(new URL('../lib/load-input.ts?proof=retained',import.meta.url).href); const out=await loadInput(); assert.equal(out.status,'stale'); assert.equal(out.input.meta.as_of,i.meta.as_of); assert.match(out.error??'',/retained|last good/i);
});
test('source loader refuses fresh-green presentation when stock stamp is old',async(t)=>{
  const i=input(); add(i,'A'); const now=Date.parse(i.meta.as_of); i.sources[0].asOf='2026-09-01T08:00:00+05:30'; t.mock.method(Date,'now',()=>now); t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify(i)));
  const {loadInput}=await import(new URL('../lib/load-input.ts?proof=oldstock',import.meta.url).href); const out=await loadInput(); assert.equal(out.status,'stale'); assert.match(out.error??'',/stale|incomplete/i);
});
test('source loader network failure falls back to dated seed, not fabricated live data',async(t)=>{
  const cwd=process.cwd(); process.chdir(new URL('..',import.meta.url).pathname); t.mock.method(globalThis,'fetch',async()=>{throw new Error('QA network unavailable');});
  try { const {loadInput}=await import(new URL('../lib/load-input.ts?proof=offline',import.meta.url).href); const out=await loadInput(); assert.equal(out.status,'seed'); assert.ok(out.input.plan.length>20); assert.match(out.error??'',/not fresh|saved dated seed/i); } finally { process.chdir(cwd); }
});
test('cross-day product change charges setup while same-product continuation does not',()=>{
  const i=input(); add(i,'A',{pieces:18000,container:'pouch'}); add(i,'B',{pieces:36000,container:'pouch'});
  i.opening.stock['PM-B']=0; i.inbound_prebooked={'2026-09-08':{'PM-B':36000}}; i.inbound_provenance={'2026-09-08':{'PM-B':'EXIM-OTW'}};
  const m=buildModel(i,noNight); const first=m.days[0].runs; assert.equal(first.length,1); assert.equal(first[0].code,'A'); assert.equal(first[0].pieces,18000);
  const changed=m.days[1].runs; assert.equal(changed.length,1); assert.equal(changed[0].code,'B'); assert.equal(changed[0].setupHours,1,'overnight product change still requires setup'); assert.equal(changed[0].hours,9); assert.equal(changed[0].pieces,16200);
  const continued=m.days[2].runs; assert.equal(continued.length,1); assert.equal(continued[0].code,'B'); assert.equal(continued[0].setupHours,0,'same product needs no invented repeated setup'); assert.equal(continued[0].pieces,18000);
  for(const day of m.days) assert.ok(day.runs.reduce((sum,r)=>sum+r.hours+r.setupHours,0)<=10+1e-7);
});
test('verified session labour charges an occupied session once, including short campaigns',()=>{
  const i=input(); add(i,'A',{pieces:9000,container:'pouch'}); add(i,'B',{pieces:9000,container:'pouch'}); i.supplements={labourPerSession:{'Pouch Machine':1000}};
  const m=buildModel(i,noNight); assert.equal(m.days[0].runs.length,2,'fixture must share one session across campaigns'); assert.equal(m.days[0].runs.reduce((s,r)=>s+(r.labourCost??0),0),1000,'one occupied session, not a per-campaign fee or hourly fraction'); assert.ok(m.days[1].runs.length>0); assert.equal(m.days[1].runs.reduce((s,r)=>s+(r.labourCost??0),0),1000,'short following session still carries verified per-session fee');
  delete i.supplements; assert.ok(runs(buildModel(i,noNight)).every(r=>r.labourCost===null),'missing cost never becomes zero');
});
