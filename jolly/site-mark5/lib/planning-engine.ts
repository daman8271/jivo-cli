import { normalizeProducts, validateInput, feasible, trial } from './model.ts';
import { eximOnlyStock, reconciledInbound } from './material-supply.ts';
import { MaterialCalendar } from './material-calendar.ts';
import { evaluateInbound } from './evidence.ts';
import { validateFactory } from './shift-validation.ts';
import { MACHINES, RULES_VERSION, route, changeover, MACHINE_RULES } from './machine-policy.ts';
import type { Mark4Input, Product, Recipe } from './types.ts';
import type { FactoryNow } from './shift-types.ts';
import type { EngineRequest, EngineResult, DayProposal, MachineId, PlanningChange, PlannedRun, PlanningAssumption, TodayBoard, ValidationResult } from './planning-types.ts';

const MINUTE=60000, HOUR=60*MINUTE, EPS=1e-6;
export const MIN_TARGET=100000, DESIRABLE:[number,number]=[115000,125000], STORAGE_LIMIT=827000;
const dateAt=(stamp:string)=>new Date(Date.parse(stamp)+5.5*HOUR).toISOString().slice(0,10);
const addDay=(date:string,n=1)=>new Date(Date.parse(`${date}T12:00:00Z`)+n*24*HOUR).toISOString().slice(0,10);
const at=(date:string,hour:string)=>Date.parse(`${date}T${hour}:00+05:30`);
const stamp=(ms:number)=>new Date(ms).toISOString();
const positive=(n:unknown)=>typeof n==='number'&&Number.isFinite(n)?Math.max(0,n):0;
const sum=(ns:number[])=>ns.reduce((a,b)=>a+b,0);
const sunday=(date:string)=>new Date(`${date}T12:00:00Z`).getUTCDay()===0;
const BASE_ASSUMPTIONS:PlanningAssumption[]=[
  {id:'running-clock',label:'Conditional working clock',detail:'Day 07:30–17:30 and night 19:30–05:30 IST: 10 hours each including setup. Sunday closed, including Sunday after midnight. CP source start is 07:30 ±30 min; the full clock and crews are planning assumptions. Running rates have no extra 80% multiplier; ordinary stops/rejects are not quantified.'},
  {id:'range-policy',label:'Conservative rate selection',detail:'Use lower running-speed endpoints: Clear Pack 4/5 L 1,500/hour; 10 Head 1 L 1,800/hour; Samarpan 1,800/hour. JP setup selects six hours from 5–6 hours.'},
  {id:'setup-policy',label:'Unmeasured setup remains conditional',detail:'Unknown opening setup reserves six hours on JP and one hour on other lines. Unlisted Tin/pouch/head changes reserve one conditional hour. One-hour-plus source values have no known upper bound; scheduled finish is a provisional minimum, not a guarantee. Unknown CP parts/flush components remain separate.'},
  {id:'reuse',label:'Flushing oil reused',detail:'Flushing occupies the machine. Flushing volume is neither saleable output nor recurring fresh-oil loss; recovery fraction, timing and make-up are unmeasured.'},
  {id:'storage',label:'Warehouse capacity retained',detail:'827,000 L cap. No unverified dispatch clearance creates future room; stock remains until physical dispatch evidence. Production may remain constrained until a fresh gate/stock snapshot.'},
  {id:'day-first',label:'Day allocation before one night line',detail:'All available day machines share stock and remaining demand first. At most one physical night machine, only for unmet minimum target or due work. Targets do not create SKU demand.'},
];

function factory(value:unknown):FactoryNow|null { try {validateFactory(value);return value as FactoryNow;}catch{return null;} }
function physicalMachine(line:string):MachineId|null { return MACHINES.includes(line as MachineId)?line as MachineId:line==='Pouch Hitech'? 'Hitech':line==='Pouch Samarpan'?'Samarpan':null; }
export function verifiedPiecesPerCase(p:Product,input:Mark4Input):number|null {
  const rows=p.bom.filter(([c])=>/carton|corrugat|\bcase\b/i.test(input.items[c]?.name??''));
  if(rows.length!==1||rows[0][1]<=0)return null;
  const n=1/rows[0][1];return Number.isFinite(n)&&n>0&&Math.abs(n-Math.round(n))<1e-6?Math.round(n):null;
}
function makeToday(date:string, f:FactoryNow|null, now:string):TodayBoard {
  const usable=f?.ok&&f.date===date&&f.asOf&&Date.parse(now)-Date.parse(f.asOf)<=Math.max(60,f.expectedRefreshSeconds)*3*1000;
  const unique=new Set<string>();
  const relevant=usable?f!.lines.flatMap(line=>line.runs.filter(run=>run.date===date).filter(run=>{if(unique.has(run.id))return false;unique.add(run.id);return true;}).map(run=>({line,run}))):[];
  const aggregate=relevant.filter(x=>!physicalMachine(x.line.line)&&/pouch/i.test(x.line.line));
  return {date,recordedLitres:usable&&relevant.length&&relevant.every(x=>x.run.producedLitres!==null)?sum(relevant.map(x=>positive(x.run.producedLitres))):null,recordedBasis:'Factory MES recorded litres for this date; incomplete coverage is not whole-plant actual. Separate from planned and booked production.',aggregatePouchNote:aggregate.length?`${aggregate.every(x=>x.run.producedLitres!==null)?sum(aggregate.map(x=>positive(x.run.producedLitres))).toLocaleString('en-IN')+' L':'Quantity unknown'} recorded on a generic pouch line; physical machine unspecified, counted once.`:null,machines:MACHINES.map(machineId=>{
    const rows=relevant.filter(x=>physicalMachine(x.line.line)===machineId), last=rows.at(-1), status=last?.line.status;
    return {machineId,status:!last?'unknown':status==='RUNNING'?'running':status==='COMPLETED'?'completed':['STOPPED','PAUSED','BREAKDOWN'].includes(status??'')?'stopped':'unknown',code:last?.run.code??null,product:last?.run.product??null,recordedLitres:rows.length&&rows.every(x=>x.run.producedLitres!==null)?sum(rows.map(x=>x.run.producedLitres!)):null,targetLitres:last?.run.targetLitres??null,asOf:usable?f!.asOf:null,note:last?last.line.note:'No attributed observation. Unknown is not zero.'};
  })};
}

function checkCommand(request:EngineRequest,products:Product[],start:string,end:string):string[] {
  const command=request.command;if(!command)return [];
  const errors:string[]=[];
  if(!/^\d{4}-\d{2}-\d{2}$/.test(command.date)||!Number.isFinite(Date.parse(command.date))||new Date(`${command.date}T12:00:00Z`).toISOString().slice(0,10)!==command.date||command.date<start||command.date>end)errors.push('Command date is invalid or outside the current planning horizon.');
  if(!Array.isArray(command.changes)||command.changes.length>30)return [...errors,'Command changes must be an array of at most 30.'];
  const runs=new Set<string>();
  for(const c of command.changes){
    if(!c||typeof c!=='object'){errors.push('Invalid change.');continue;}
    if(c.type==='prioritize_sku'){if(!products.some(p=>p.code===c.code))errors.push(`Unknown SKU ${c.code}.`);}
    else if(c.type==='set_line_enabled'){if(!MACHINES.includes(c.machineId)||typeof c.enabled!=='boolean')errors.push('Invalid machine enable change.');}
    else if(c.type==='set_night_line'){if(c.machineId!==null&&c.machineId!=='auto'&&!MACHINES.includes(c.machineId))errors.push('Invalid night machine.');}
    else if(c.type==='set_run'){
      const p=products.find(p=>p.code===c.code),key=`${c.machineId}:${c.shift}`;
      if(!MACHINES.includes(c.machineId)||!['day','night'].includes(c.shift)||!Number.isSafeInteger(c.pieces)||c.pieces<=0)errors.push('Run needs a valid machine, shift and positive integer sales-unit quantity.');
      else if(!p||!route(p,c.machineId).allowed)errors.push(`SKU ${c.code} is not eligible on ${c.machineId}.`);
      if(runs.has(key))errors.push('Only one exact operator run per machine/shift is supported.');runs.add(key);
    }else errors.push('Unknown planning change type.');
  }
  return errors;
}

/** Pure planner: only the caller persists output. Input meta.as_of is never shifted. */
export function runEngine(request:EngineRequest):EngineResult {
  if(!request||typeof request.now!=='string'||!Number.isFinite(Date.parse(request.now)))throw new Error('A valid explicit planning clock is required.');
  validateInput(request.input);
  let input:Mark4Input={...request.input,bom:{...request.input.bom,...((request.input.supplements?.verifiedBom??{}) as Record<string,Recipe>)},items:{...request.input.items,...((request.input.supplements?.verifiedItems??{}) as Mark4Input['items'])}};
  if(input.materialSupply){const materialSupply=eximOnlyStock(input.materialSupply);input={...input,materialSupply,opening:{...input.opening,stock:materialSupply.stock.byItem}};}
  validateInput(input);
  const start=dateAt(request.now), tomorrow=addDay(start), monthEnd=new Date(Date.UTC(Number(start.slice(0,4)),Number(start.slice(5,7)),0)).toISOString().slice(0,10), end=addDay(start,6)<monthEnd?addDay(start,6):monthEnd;
  const {products,orders,historyComplete}=normalizeProducts(input,false),byCode=new Map(products.map(p=>[p.code,p]));
  for(const p of products)p.bottleComponentCodes=p.bom.filter(([c,q])=>q>=.5&&/bottle|\bjar\b|jerry|hdpe|\btin\b/i.test(input.items[c]?.name??'')&&!/cap|carton|label|preform|sleeve|seal|wad|plug/i.test(input.items[c]?.name??'')).map(([c])=>c);
  const sourceMonth=input.meta.as_of.slice(0,7), sameMonth=start.slice(0,7)===sourceMonth;
  const materialStale=!!input.materialSupply?.coverage.datasets.some(s=>!s.ok||!s.complete||!s.asOf||Date.parse(request.now)-Date.parse(s.asOf)>s.expectedRefreshSeconds*3*1000);
  const sourceStale=Date.parse(request.now)-Date.parse(input.meta.as_of)>15*MINUTE||materialStale||request.sourceStatus==='stale'||request.sourceStatus==='seed';
  const errors=checkCommand(request,products,start,end),warnings:string[]=[];
  if(!sameMonth)errors.push('Input belongs to another month; new-month demand and opening stock are required.');
  if(sourceStale)warnings.push('Opening input is stale or a seed; every proposal is conditional on a refreshed stock/demand position.');
  if(!historyComplete)warnings.push('Booked month-to-date history is incomplete; remaining monthly make may be overstated.');
  const f=factory(request.factoryNow),today=makeToday(start,f,request.now);
  const calendarEvents=input.materialSupply?reconciledInbound(input,end,{nightLine:'auto',efficiency:1,allowProposedSupply:false,allowProvisionalRecipes:false,supplyMode:'expected',includePackagingEstimates:true}):evaluateInbound(input,end);
  // Without reconciled EXIM provenance do not borrow factory/raw opening RM oil.
  const opening=input.materialSupply?input.opening.stock:Object.fromEntries(Object.entries(input.opening.stock).map(([c,q])=>[c,c.startsWith('RM')?0:q]));
  if(!input.materialSupply)warnings.push('EXIM-only material reconciliation missing: raw-material opening stock withheld; packaging retained.');
  const ledger=new MaterialCalendar(opening,calendarEvents.filter(e=>e.included&&e.appliedAt).map(e=>({at:e.readyAt?Date.parse(e.readyAt):at(e.appliedAt!.slice(0,10),'07:30'),code:e.code,quantity:e.quantity,conditional:e.conditional})).filter(e=>Number.isFinite(e.at)));
  const remaining=new Map(products.map(p=>[p.code,p.requiredPieces])),confirmed=new Map(products.map(p=>[p.code,p.confirmedUncoveredPieces]));
  const remainingOrders=orders.map(o=>({...o}));
  for(const p of products){let fg=p.fgPieces;for(const o of remainingOrders.filter(o=>o.code===p.code)){const take=Math.min(fg,o.remaining);o.remaining-=take;fg-=take;}}
  const previous=new Map<MachineId,Product>(),priorAssumed=new Set<MachineId>();
  if(f?.ok && f.date<=start && f.asOf && Date.parse(f.asOf)<=Date.parse(request.now)){
    const seen=new Set<string>();
    for(const line of f.lines){const machine=physicalMachine(line.line);const rows=[...line.runs].filter(r=>r.code&&r.date&&r.date<=start).sort((a,b)=>(a.firstStartedAt??a.sourceUpdatedAt??'').localeCompare(b.firstStartedAt??b.sourceUpdatedAt??''));const last=rows.at(-1);
      if(machine&&last?.code&&byCode.has(last.code)&&line.coverage!=='conflict'){previous.set(machine,byCode.get(last.code)!);if(Date.parse(request.now)-Date.parse(f.asOf)>Math.max(60,f.expectedRefreshSeconds)*3*1000)priorAssumed.add(machine);}
      for(const run of rows){if(seen.has(run.id)||run.date!==start||!run.code)continue;seen.add(run.id);const p=products.find(p=>p.originalCodes.includes(run.code!));if(!p)continue;
        // Factory reports case quantities in some versions; litres / verified sales-unit litres avoids guessing their count basis.
        const made=run.producedLitres===null?0:Math.floor(positive(run.producedLitres)/p.packLitres+EPS);
        // Today's MES reduces only the monthly make target. Open confirmed need
        // already credits live FG; subtracting MES again would credit it twice.
        p.targetRemainingPieces=Math.max(0,p.targetRemainingPieces-made);
        remaining.set(p.code,Math.max(p.targetRemainingPieces,p.confirmedUncoveredPieces));
      }
    }
  }
  for(const saved of [...(request.savedPlans??[])].filter(p=>p.date<start&&p.status==='approved').sort((a,b)=>b.date.localeCompare(a.date)||b.revision-a.revision))for(const run of [...saved.proposal.runs].reverse()){if(!previous.has(run.machineId)&&byCode.has(run.code)){previous.set(run.machineId,byCode.get(run.code)!);priorAssumed.add(run.machineId);}}
  const reclassified=sum(Object.entries(input.opening.fg).filter(([c])=>!input.plan.some(p=>p.code===c)).map(([c,q])=>{const p=products.find(p=>p.originalCodes.includes(c));return p?positive(q)*p.packLitres:0;}));
  let storage=typeof input.opening.fg_litres==='number'?positive(input.opening.fg_litres):sum(products.map(p=>p.fgPieces*p.packLitres))+Math.max(0,positive(input.opening.fg_other_l)-reclassified);
  storage+=positive(input.opening.standing_l);
  const standingBasis=typeof input.opening.standing_basis==='string'?input.opening.standing_basis:'Standing-stock estimate is not a reconciled physical count.';
  const storageAssumption:PlanningAssumption={id:'storage-opening-basis',label:'Conditional warehouse opening',detail:`Standing goods ${positive(input.opening.standing_l).toLocaleString('en-IN')} L. ${standingBasis} Projected warehouse pressure is conditional; this is not proof that the factory has stopped.`};
  // Approved runs are commitments, not a replay of user edits (an automatic
  // approval can have changes=[]). Reserve future commitments before forecasts.
  // A command for that date explicitly asks for a comparison draft instead.
  const approved=new Map<string,NonNullable<EngineRequest['savedPlans']>[number]>();
  for(const plan of request.savedPlans??[])if(plan.status==='approved'&&plan.date>=start&&plan.date<=end&&request.command?.date!==plan.date&&(!approved.has(plan.date)||approved.get(plan.date)!.revision<plan.revision))approved.set(plan.date,plan);
  const pinned=new Map<string,PlannedRun[]>(),commitmentIssues=new Map<string,string[]>(),lockedMachines=new Map<string,Set<MachineId>>(),reservedPieces=new Map<string,number>();
  let reservedStorage=0;
  const occupied=new Map<MachineId,number>(),pinnedNight=new Map<string,MachineId>();
  const pins=[...approved.values()].flatMap(plan=>plan.proposal.runs).sort((a,b)=>Date.parse(a.setupStartsAt)-Date.parse(b.setupStartsAt));
  const noteConflict=(run:PlannedRun,reason:string)=>{commitmentIssues.set(run.date,[...(commitmentIssues.get(run.date)??[]),`Agreed run needs review: ${run.machineId} / ${run.code}: ${reason}`]);};
  for(const saved of pins){
    lockedMachines.set(saved.date,new Set([...(lockedMachines.get(saved.date)??[]),saved.machineId]));
    const p=byCode.get(saved.code),begins=Date.parse(saved.startsAt),setupStarts=Date.parse(saved.setupStartsAt),ends=Date.parse(saved.endsAt),policy=p?route(p,saved.machineId):null;
    let reason:string|null=null;
    const shiftStart=at(saved.date,saved.shift==='day'?'07:30':'19:30'),shiftEnd=saved.shift==='day'?at(saved.date,'17:30'):at(addDay(saved.date),sunday(addDay(saved.date))?'00:00':'05:30');
    if(!p||!policy?.allowed)reason='SKU no longer has a valid recipe/route.';
    else if(!Number.isSafeInteger(saved.pieces)||saved.pieces<=0||![begins,setupStarts,ends].every(Number.isFinite)||setupStarts<shiftStart||ends>shiftEnd||setupStarts>begins||begins>=ends||sunday(saved.date))reason='Invalid quantity or occupied clock.';
    else if(saved.date===start&&setupStarts<Date.parse(request.now))reason='This agreed interval has already started; current source cannot prove its remaining quantity. Original approval retained for comparison.';
    else if(saved.shift==='night'&&pinnedNight.has(saved.date)&&pinnedNight.get(saved.date)!==saved.machineId)reason='More than one approved physical night line.';
    else if(setupStarts<(occupied.get(saved.machineId)??0))reason='Approved runs overlap on a physical machine.';
    else if(Math.abs(saved.litres-saved.pieces*p.packLitres)>EPS||Math.abs(saved.containers-saved.pieces*p.containersPerPiece)>EPS||(ends-begins)/HOUR+EPS<saved.pieces*p.containersPerPiece/policy.min)reason='Saved quantity/rate conversion no longer matches approved policy.';
    else if(saved.pieces>(remaining.get(p.code)??0)-(reservedPieces.get(p.code)??0)+EPS)reason='Committed quantity exceeds remaining need.';
    else if(storage+reservedStorage+saved.litres>STORAGE_LIMIT+EPS)reason='Committed output exceeds warehouse headroom.';
    else {
      // Setup depends on the campaign immediately preceding this interval.
      // Today has not been projected yet: reserve quantities/times now, but
      // validate setup during chronological replay below, not from opening state.
      const use=trial(p,saved.pieces,ledger.available(begins),input);
      if(!reason&&use.failure)reason=`Committed material ${use.failure.code} is unavailable at its start.`;
      if(!reason){ledger.reserve(begins,use.used);reservedStorage+=saved.litres;reservedPieces.set(p.code,(reservedPieces.get(p.code)??0)+saved.pieces);pinned.set(saved.date,[...(pinned.get(saved.date)??[]),{...saved,conditional:true,constraints:[...saved.constraints,'Exact approved commitment replayed; working-clock/crew assumptions remain.']}]);occupied.set(saved.machineId,ends);if(saved.shift==='night')pinnedNight.set(saved.date,saved.machineId);}
    }
    if(reason){noteConflict(saved,reason);
      // Hold the slot and the available part of its recipe instead of offering
      // already-promised resources as free. Impossible output is not projected.
      if(p&&Number.isFinite(begins)&&begins>=Date.parse(request.now)){const qty=feasible(p,Math.max(0,saved.pieces),ledger.available(begins),input);if(qty>0){const hold=trial(p,qty,ledger.available(begins),input);if(!hold.failure)ledger.reserve(begins,hold.used);}}
    }
  }
  const proposals:DayProposal[]=[];
  for(let date=start;date<=end;date=addDay(date)){
    const dayOpeningStorage=storage;
    const runs:PlannedRun[]=[],blockers:DayProposal['blockers']=(commitmentIssues.get(date)??[]).map(reason=>({machineId:null,code:null,kind:'setup',reason})),dayErrors:string[]=[];
    for(const saved of pinned.get(date)??[]){
      const p=byCode.get(saved.code)!,needed=changeover(saved.machineId,previous.get(saved.machineId),p);
      if((Date.parse(saved.startsAt)-Date.parse(saved.setupStartsAt))/MINUTE+EPS<(needed.minutes??60)){
        noteConflict(saved,'Saved setup interval is shorter than the changeover from the chronologically preceding campaign. Quantity, materials and machine slot remain held; original approval is unchanged.');
        blockers.push({machineId:saved.machineId,code:saved.code,kind:'setup',reason:commitmentIssues.get(date)!.at(-1)!});
        continue;
      }
      reservedStorage-=saved.litres;reservedPieces.set(p.code,(reservedPieces.get(p.code)??0)-saved.pieces);storage+=saved.litres;remaining.set(p.code,(remaining.get(p.code)??0)-saved.pieces);const match=Math.min(saved.pieces,confirmed.get(p.code)??0);confirmed.set(p.code,(confirmed.get(p.code)??0)-match);let left=saved.pieces;for(const o of remainingOrders.filter(o=>o.code===p.code)){const take=Math.min(left,o.remaining);o.remaining-=take;left-=take;}previous.set(saved.machineId,p);runs.push({...saved,confirmedLitres:match*p.packLitres,demandBasis:match===saved.pieces?'orders':match===0?'forecast':'mixed'});
    }
    // With an approval present, refresh replays the approved commitment only.
    // Newer drafts remain archived comparisons until approved; inherited exact
    // controls must not execute again beside their already pinned run.
    const latest=approved.get(date)??(request.savedPlans??[]).filter(p=>p.date===date&&p.status!=='superseded').sort((a,b)=>b.revision-a.revision)[0];
    const changes:PlanningChange[]=request.command?.date===date&&errors.length===0?[...(latest?.changes??[]),...request.command.changes]:(latest?.changes??[]);
    const disabled=new Set<MachineId>();let night:MachineId|'auto'|null='auto';const priority:string[]=[];const exact=new Map<string,Extract<PlanningChange,{type:'set_run'}>>();
    for(const c of changes){if(c.type==='set_line_enabled'){if(c.enabled)disabled.delete(c.machineId);else disabled.add(c.machineId);}else if(c.type==='set_night_line')night=c.machineId;else if(c.type==='prioritize_sku'){priority.unshift(c.code);}else if(c.type==='set_run'&&!approved.has(date))exact.set(`${c.machineId}:${c.shift}`,c);}
    const due=(p:Product)=>sum(remainingOrders.filter(o=>o.code===p.code&&o.due<=date&&o.date<=date).map(o=>o.remaining));
    const total=()=>sum(runs.map(r=>r.litres));
    const dayActual=date===start?positive(today.recordedLitres):0;
    const fill=(machine:MachineId,shift:'day'|'night',manual?:Extract<PlanningChange,{type:'set_run'}>,dry=false):PlannedRun|null=>{
      if(disabled.has(machine)||sunday(date)||lockedMachines.get(date)?.has(machine))return null;
      const shiftStart=at(date,shift==='day'?'07:30':'19:30');
      let shiftEnd=shift==='day'?at(date,'17:30'):at(addDay(date),'05:30');
      if(shift==='night'&&sunday(addDay(date)))shiftEnd=at(addDay(date),'00:00');
      const cursor=Math.max(shiftStart,date===start?Date.parse(request.now):shiftStart,...runs.filter(r=>r.machineId===machine&&r.shift===shift).map(r=>Date.parse(r.endsAt)));
      if(cursor>=shiftEnd)return null;
      const futurePin=pins.find(r=>r.machineId===machine&&r.date>date);
      const preservesFutureSetup=(p:Product)=>{
        if(!futurePin||p.code===futurePin.code)return true;
        const futureProduct=byCode.get(futurePin.code);if(!futureProduct)return false;
        const availableSetup=(Date.parse(futurePin.startsAt)-Date.parse(futurePin.setupStartsAt))/MINUTE;
        return (changeover(machine,p,futureProduct).minutes??60)<=availableSetup+EPS;
      };
      const candidates=products.filter(p=>(remaining.get(p.code)??0)-(reservedPieces.get(p.code)??0)>=1&&route(p,machine).allowed&&(!manual||p.code===manual.code)&&preservesFutureSetup(p)).sort((a,b)=>{
        const score=(p:Product)=> (priority.includes(p.code)?1e9-priority.indexOf(p.code):0)+(due(p)>0?1e7:0)+(previous.get(machine)?.code===p.code?1e6:0)+route(p,machine).preference*1000+route(p,machine).min*p.fillLitres;
        return score(b)-score(a)||a.code.localeCompare(b.code);
      });
      for(const p of candidates){
        const policy=route(p,machine),setup=changeover(machine,previous.get(machine),p),setupMs=(setup.minutes??60)*MINUTE;
        for(const ready of ledger.times(cursor+setupMs,shiftEnd)){
          const setupStart=Math.max(cursor,ready-setupMs), begins=setupStart+setupMs;
          // The desirable band paces forecast; it is not a physical ceiling on
          // confirmed due work or an exact feasible operator quantity.
          const targetRoom=manual?Infinity:Math.max(0,DESIRABLE[1]-dayActual-total(),due(p)*p.packLitres);
          const capacity=Math.min((shiftEnd-begins)/HOUR*policy.min/p.containersPerPiece,(remaining.get(p.code)??0)-(reservedPieces.get(p.code)??0),Math.max(0,STORAGE_LIMIT-storage-reservedStorage)/p.packLitres,targetRoom/p.packLitres,manual?.pieces??Infinity);
          const pieces=feasible(p,Math.floor(capacity+EPS),ledger.available(begins),input);
          if(pieces<1)continue;
          if(manual&&pieces!==manual.pieces)continue;
          const use=trial(p,pieces,ledger.available(begins),input);if(use.failure)continue;
          const confirmedPieces=Math.min(pieces,confirmed.get(p.code)??0),fillingMinutes=pieces*p.containersPerPiece/policy.min*60;
          const conditional=sourceStale||!historyComplete||policy.conditional||setup.requiresConfirmation||priorAssumed.has(machine)||p.conditionalRecipe||calendarEvents.some(e=>e.included&&e.conditional&&e.appliedAt&&use.used[e.code]>0);
          const constraints=[policy.reason,...(setup.requiresConfirmation?['Setup has an unresolved duration or upper bound; proposed finish is conditional.']:[]),...(priorAssumed.has(machine)?['Opening campaign taken from approved plan, not verified machine observation.']:[]),...(sourceStale?['Stale opening stock/demand']:[])];
          const perCase=verifiedPiecesPerCase(p,input);
          const run:PlannedRun={id:`${date}:${machine}:${shift}:${runs.filter(r=>r.machineId===machine).length+1}`,machineId:machine,code:p.code,product:p.name,date,shift,setupStartsAt:stamp(setupStart),startsAt:stamp(begins),endsAt:stamp(begins+fillingMinutes*MINUTE),pieces,containers:pieces*p.containersPerPiece,cases:perCase===null?null:pieces/perCase,piecesPerCase:perCase,containersPerPiece:p.containersPerPiece,packLitres:p.packLitres,litres:pieces*p.packLitres,speedPerHour:policy.min,speedRange:{min:policy.min,max:policy.max},changeover:setup,fillingMinutes,demandBasis:confirmedPieces===pieces?'orders':confirmedPieces===0?'forecast':'mixed',confirmedLitres:confirmedPieces*p.packLitres,conditional:true,constraints:[...constraints,'Clock, full crew, ordinary stops and downstream packing availability are assumed.'],reason:manual?'Exact operator request, revalidated against route, time, demand, stock and space.':due(p)>0?'Remaining due orders first.':previous.get(machine)?.code===p.code?'Continue the same campaign within remaining monthly demand.':'Remaining monthly production requirement; this is forecast, not a new purchase order.'};
          if(dry)return run;
          const conditionalMaterials=ledger.reserve(begins,use.used);if(conditionalMaterials.length){run.conditional=true;run.constraints.push(`Expected material readiness: ${conditionalMaterials.join(', ')}`);}
          void conditional; // all runs also depend on the explicitly assumed working clock/crew.
          storage+=run.litres;remaining.set(p.code,(remaining.get(p.code)??0)-pieces);confirmed.set(p.code,(confirmed.get(p.code)??0)-confirmedPieces);
          let booked=pieces;for(const o of remainingOrders.filter(o=>o.code===p.code)){const take=Math.min(booked,o.remaining);o.remaining-=take;booked-=take;}
          previous.set(machine,p);priorAssumed.delete(machine);runs.push(run);return run;
        }
      }
      return null;
    };
    // Exact day requests reserve first, then every other day line, then optional second campaigns.
    const suspended=[...exact.values()].filter(c=>disabled.has(c.machineId)||(c.shift==='night'&&(night===null||(night!=='auto'&&night!==c.machineId))));
    for(const c of exact.values())if(c.shift==='day'&&!disabled.has(c.machineId)&&!fill(c.machineId,'day',c))dayErrors.push(`Exact run ${c.code} on ${c.machineId} cannot fit its demand, stock, storage or day clock.`);
    const dayMachines=MACHINES.filter(m=>!exact.has(`${m}:day`)&&!disabled.has(m));
    for(let pass=0;pass<2;pass++){
      const available=new Set(dayMachines);
      while(available.size){
        const choices=[...available].map(machine=>fill(machine,'day',undefined,true)).filter((r):r is PlannedRun=>r!==null).sort((a,b)=>{
          const rank=(r:PlannedRun)=>{const p=byCode.get(r.code)!;return (priority.includes(r.code)?1e12-priority.indexOf(r.code):0)+(due(p)>0?1e10:0)+(previous.get(r.machineId)?.code===r.code?1e8:0)+route(p,r.machineId).preference*1e5+r.litres;};
          return rank(b)-rank(a);
        });
        if(!choices[0])break;
        const machine=choices[0].machineId;fill(machine,'day');available.delete(machine);
      }
    }
    const dueLeft=sum(products.map(p=>due(p)*p.packLitres));
    const needNight=dayActual+total()<MIN_TARGET||dueLeft>EPS;
    const exactNight=[...exact.values()].filter(c=>c.shift==='night'&&!suspended.includes(c));
    let nightReason=sunday(date)?'Sunday closed.':!needNight?'Day allocation meets the minimum and due work; no night line needed.':night===null?'Night disabled by operator.':'Remaining need exists, but no feasible staffed/material-supported night candidate was found.';
    if(exactNight.length>1)dayErrors.push('Only one physical night line is permitted.');
    else if(exactNight.length){const c=exactNight[0];if(!needNight||night===null||(night!=='auto'&&night!==c.machineId)||!fill(c.machineId,'night',c))dayErrors.push('Exact night run is unnecessary, conflicts with night policy, or cannot fit stock/demand/time/space.');else nightReason=`${c.machineId} selected by operator for remaining need after day allocation.`;}
    else if(needNight&&night!==null&&!sunday(date)&&!runs.some(r=>r.shift==='night')&&!pins.some(r=>r.date===date&&r.shift==='night')){
      const choices=(night==='auto'?MACHINES:[night]).filter(m=>!disabled.has(m)).map(m=>fill(m,'night',undefined,true)).filter((r):r is PlannedRun=>r!==null).sort((a,b)=>{
        const coveredDue=(r:PlannedRun)=>Math.min(r.pieces,due(byCode.get(r.code)!))*r.packLitres;
        return coveredDue(b)-coveredDue(a)||b.litres-a.litres;
      });
      if(choices[0]){fill(choices[0].machineId,'night');nightReason=`${choices[0].machineId}: remaining ${dueLeft>0?'due work':'daily minimum'} after all day lines were allocated.`;}
    }
    for(const p of products.filter(p=>(remaining.get(p.code)??0)>=1)){
      const routes=MACHINES.filter(m=>!disabled.has(m)&&route(p,m).allowed);
      if(!routes.length)blockers.push({machineId:null,code:p.code,kind:'route',reason:p.exclusionReason??'No enabled verified machine/rate route.'});
      else if(storage>=STORAGE_LIMIT-1)blockers.push({machineId:null,code:p.code,kind:'storage',reason:`Projected warehouse headroom exhausted under the opening estimate. ${standingBasis} Physical dispatch/stock reconciliation may change this; no actual factory stop is claimed.`});
      else {const failure=trial(p,1,ledger.available(at(date,'17:30')),input).failure;if(failure)blockers.push({machineId:null,code:p.code,kind:'material',reason:`Usable ${input.items[failure.code]?.name??failure.code} unavailable.`});}
    }
    if(sourceStale)blockers.push({machineId:null,code:null,kind:'source',reason:'Opening snapshot stale; refresh before relying on quantities.'});
    if(!runs.length&&!blockers.length)blockers.push({machineId:null,code:null,kind:'demand',reason:sunday(date)?'Sunday closed.':'No further feasible requirement within this clock.'});
    const dayLitres=sum(runs.filter(r=>r.shift==='day').map(r=>r.litres)),nightLitres=sum(runs.filter(r=>r.shift==='night').map(r=>r.litres));
    proposals.push({date,runs,blockers,dayLitres,nightLitres,totalLitres:dayLitres+nightLitres,confirmedLitres:sum(runs.map(r=>r.confirmedLitres)),targetLitres:MIN_TARGET,desirableRangeLitres:DESIRABLE,shortfallLitres:Math.max(0,MIN_TARGET-dayActual-dayLitres-nightLitres),nightReason,assumptions:[...BASE_ASSUMPTIONS,storageAssumption,...(suspended.length?[{id:'suspended-exact-runs',label:'Saved exact runs suspended',detail:`${suspended.map(c=>`${c.machineId} ${c.shift}: ${c.code}, ${c.pieces} sales units`).join('; ')}. Retained for re-enabling; no work allocated while its machine or night slot is disabled.`}]:[])],storage:{openingLitres:dayOpeningStorage,limitLitres:STORAGE_LIMIT,closingLitres:storage,standingLitres:positive(input.opening.standing_l),standingBasis,spaceNeededForMinimumLitres:Math.max(0,MIN_TARGET-dayActual-Math.max(0,STORAGE_LIMIT-dayOpeningStorage)),conditional:true},validation:{valid:dayErrors.length===0,errors:dayErrors,warnings:[...warnings,...[...commitmentIssues].filter(([d])=>d<=date).flatMap(([,rows])=>rows)]}});
  }
  const validation:ValidationResult={valid:errors.length===0&&proposals.every(p=>p.validation.valid),errors:[...errors,...proposals.flatMap(p=>p.validation.errors)],warnings};
  today.proposal=proposals[0];
  const empty=(date:string):DayProposal=>({date,runs:[],blockers:[{machineId:null,code:null,kind:'source',reason:'Next month needs a new monthly opening and demand snapshot.'}],dayLitres:0,nightLitres:0,totalLitres:0,confirmedLitres:0,targetLitres:MIN_TARGET,desirableRangeLitres:DESIRABLE,shortfallLitres:MIN_TARGET,nightReason:'Outside current month.',assumptions:BASE_ASSUMPTIONS,validation:{valid:false,errors:['Outside current month.'],warnings:[]}});
  const materialGroups=new Map<string,NonNullable<Mark4Input['materialSupply']>['coverage']['datasets']>();
  for(const s of input.materialSupply?.coverage.datasets??[]){const group=/exim|tank|oil/i.test(s.id)?'Oil and tanks':/receipt|qc|inspection|grpo/i.test(s.id)?'Receipts and QC':/stock|warehouse|godown/i.test(s.id)?'Warehouse stock':/order|purchase|\bpo\b/i.test(s.id)?'Purchase orders':'Material source records';materialGroups.set(group,[...(materialGroups.get(group)??[]),s]);}
  const materialFreshness:EngineResult['snapshot']['freshness']=[...materialGroups].map(([label,rows])=>{const failed=rows.filter(s=>!s.ok).length,incomplete=rows.filter(s=>!s.complete).length,stale=rows.filter(s=>!s.asOf||Date.parse(request.now)-Date.parse(s.asOf)>s.expectedRefreshSeconds*3*1000).length;return {id:`material:${label}`,label,asOf:rows.some(s=>!s.asOf)?null:rows.map(s=>s.asOf!).sort()[0]??null,status:failed?'missing':incomplete?'conflict':stale?'stale':'fresh',note:`${rows.length} datasets; ${failed} failed, ${incomplete} incomplete, ${stale} stale. Worst source state is retained; each source uses its recorded refresh cadence.`};});
  const freshness:EngineResult['snapshot']['freshness']=[...input.sources.map(s=>({id:s.id,label:s.label,asOf:s.asOf,status:(!s.ok?'missing':!s.asOf||Date.parse(request.now)-Date.parse(s.asOf)>(/factory|production|dispatch/i.test(s.id)?5*MINUTE:/tank|exim/i.test(s.id)?24*HOUR:6*HOUR)?'stale':'fresh') as 'missing'|'stale'|'fresh',note:s.note??''})),...materialFreshness,{id:'factory-now',label:'Factory machine observations',asOf:f?.asOf??null,status:!f?.ok?'missing':!f.asOf||Date.parse(request.now)-Date.parse(f.asOf)>Math.max(60,f.expectedRefreshSeconds)*3*1000?'stale':'fresh',note:f?.error??'Physical-machine status; generic pouch records remain unattributed.'}];
  return {validation,proposal:request.command?proposals.find(p=>p.date===request.command!.date)??null:proposals[0]??null,snapshot:{schemaVersion:1,revision:`${request.sourceRevision}:${RULES_VERSION}:${request.now}`,generatedAt:request.now,sourceRevision:request.sourceRevision,sourceAsOf:input.meta.as_of,freshness,today,tomorrow:proposals.find(p=>p.date===tomorrow)??empty(tomorrow),ahead:proposals.filter(p=>p.date>tomorrow),savedPlans:(request.savedPlans??[]).map(p=>({id:p.id,date:p.date,revision:p.revision,status:p.status,createdAt:p.createdAt,totalLitres:p.proposal.totalLitres,sourceRevision:p.sourceRevision})),activity:[],jobs:[],machineRulesVersion:RULES_VERSION,machineRules:MACHINE_RULES,products:products.map(p=>({code:p.code,name:p.name,packLitres:p.packLitres,piecesPerCase:verifiedPiecesPerCase(p,input),machines:MACHINES.filter(m=>route(p,m).allowed)}))}};
}
