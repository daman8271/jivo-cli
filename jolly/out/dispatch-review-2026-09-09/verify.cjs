const fs=require('node:fs');const vm=require('node:vm');const assert=require('node:assert/strict');const path=require('node:path');
const d=JSON.parse(fs.readFileSync(path.join(__dirname,'evidence.json'),'utf8'));
assert.equal(d.trips.length,5);assert.equal(d.trips.reduce((s,t)=>s+t.litres,0),54076);assert.equal(Object.values(d.warehouseLitres).reduce((a,b)=>a+b,0),54076);assert(d.trips.every(t=>t.warehouses.split(', ').every(w=>d.scope.includes(w))));assert.equal(d.physicalClosingStockLitres,null);
const elements=new Map();function elem(id){if(!elements.has(id))elements.set(id,{value:id==='replay'?'1440':'',innerHTML:'',textContent:'',validity:{valid:true},events:{},setAttribute(){},classList:{toggle(){}},addEventListener(name,fn){this.events[name]=fn}});return elements.get(id);}
const context={window:{DISPATCH_DATA:d},document:{getElementById:elem},console:{info(){}}};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'app.js'),'utf8'),context);
assert.match(elem('total').innerHTML,/54\.076/);assert.match(elem('gap').innerHTML,/45\.924/);assert.match(elem('fallback').textContent,/3D is unavailable/);
elem('replay').value='0';elem('replay').events.input();assert.match(elem('replay-summary').textContent,/0 of 5.*0\.000/);
elem('replay').value='878';elem('replay').events.input();assert.match(elem('replay-summary').textContent,/2 of 5.*13\.800/);
elem('end-day').events.click();assert.match(elem('replay-summary').textContent,/5 of 5.*54\.076/);
for(const [id,v] of Object.entries({opening:'100',production:'20',other:'-5','test-dispatch':'54.076'}))elem(id).value=v;
elem('scenario').events.input();assert.match(elem('scenario-result').textContent,/60\.924/);
elem('opening').value='0';elem('scenario').events.input();assert.match(elem('scenario-result').textContent,/short by 39\.076/);
elem('opening').value='';elem('scenario').events.input();assert.match(elem('scenario-result').textContent,/Enter valid values/);
console.log('PASS: source sums, warehouse scope, 0/midday/full-day replay, WebGL fallback, positive/negative/missing-input scenarios.');
