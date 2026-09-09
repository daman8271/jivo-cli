import test from 'node:test';
import assert from 'node:assert/strict';
import { MaterialCalendar } from '../lib/material-calendar.ts';
test('later receipt cannot supply earlier reservation; shared future reservation stays protected', () => {
  const ledger = new MaterialCalendar({PM:10}, [{at:13, code:'PM', quantity:20, conditional:true}]);
  assert.equal(ledger.available(12).PM,10);
  assert.deepEqual(ledger.reserve(13,{PM:25}),['PM']);
  assert.equal(ledger.available(12).PM,5);
  ledger.reserve(12,{PM:5});
  assert.equal(ledger.balance(14).PM,0);
  assert.throws(()=>ledger.reserve(12,{PM:1}),/exceeded/);
});
test('overnight receipt is reserved once and preview cannot mutate real ledger',()=>{
  const ledger=new MaterialCalendar({PM:0},[{at:25,code:'PM',quantity:100,conditional:false}]);
  const preview=ledger.clone(); preview.reserve(25,{PM:100});
  assert.equal(ledger.available(26).PM,100);
  ledger.reserve(25,{PM:100});
  assert.equal(ledger.available(32).PM,0);
  assert.equal(ledger.available(24).PM,0);
});
