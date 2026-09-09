import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from serve_inputs import sanitize, Feed, Handler


def fixture():
    return {'meta':{'as_of':'2026-09-06T05:15:01+05:30','horizon':['2026-09-06','2026-09-30'],'month':'September 2026'},'plan':[{'code':'FG0000142','sku':'Groundnut 1 L','category':'oil','head':'10 Head','pack_type':'PET','litres_per_piece':1,'pieces':100,'litres':100}], 'bom':{'FG0000142':[['RM0000011',1]]},'items':{'RM0000011':{'name':'GROUNDNUT OIL','uom':'LTR'},'FA0000001':{'name':'SECRET_PERSON','uom':'PCS'}}, 'opening':{'stock':{'RM0000011':200},'fg':{},'fg_other_l':0,'standing_l':0},'history':{'data':{'status':'partial','days':[{'date':'2026-09-05','complete':False,'made_booked_l':None,'booked_by_item':None}]}},'provenance':{'opening_fg':{'source':'factory_production','fetched_at':'2026-09-06T05:15:00+05:30','mode':'carried 2026-09-06T04:48:03+05:30'}},'orders':[{'docnum':'PRIVATE-INVOICE','customer':'PRIVATE_CUSTOMER','date':'2026-09-05','due':'2026-09-08','code':'FG0000142','pieces':3,'channel':'OIL','_src':'OMS'}]}

class SanitizerTests(unittest.TestCase):
    def test_recursive_private_canaries_removed(self):
        raw=fixture();raw['meta']['month']={'password':'CANARY'};raw['plan'][0]['head']={'password':'CANARY'};raw['people']=[{'name':'CANARY','whatsapp':'9999999999'}];raw['inbound_provenance']={'2026-09-07':{'RM0000011':'UPPERCASE_CANARY'}};raw['lines_basis']={'JP Machine':{'/root/CANARY':'rated'}}
        out=sanitize(raw,{}, {'unknown_secret':'CANARY','rates':[]})
        encoded=json.dumps(out)
        for token in ('CANARY','PRIVATE_CUSTOMER','PRIVATE-INVOICE','SECRET_PERSON','9999999999'):self.assertNotIn(token,encoded)
        self.assertEqual(out['orders'][0]['channel'],'OIL');self.assertEqual(out['orders'][0]['_src'],'OMS')
    def test_carried_timestamp_not_laundered(self):
        out=sanitize(fixture(),{})
        self.assertEqual(next(s for s in out['sources'] if s['id']=='opening_fg')['asOf'],'2026-09-06T04:48:03+05:30')
    def test_failed_source_retains_old_clock_and_marks_failed(self):
        out=sanitize(fixture(),{'sources':{'factory_production':{'ok':False}}})
        source=next(s for s in out['sources'] if s['id']=='opening_fg')
        self.assertFalse(source['ok']);self.assertIsNotNone(source['asOf'])
    def test_unread_history_never_zero(self):
        row=sanitize(fixture(),{})['history']['days'][0]
        self.assertIsNone(row['booked_by_item']);self.assertIsNone(row['made_booked_l'])
    def test_bad_required_data_rejected(self):
        for mutation in ('date','quantity','plan'):
            raw=fixture()
            if mutation=='date':raw['meta']['as_of']='today'
            if mutation=='quantity':raw['plan'][0]['pieces']=float('nan')
            if mutation=='plan':raw['plan']=[]
            with self.assertRaises(ValueError):sanitize(raw,{})
    def test_supply_classification_only_known_tokens(self):
        raw=fixture();raw['inbound_provenance']={'2026-09-07':{'RM0000011':'EXIM-OTW+PO-LEAD-OVERDUE','PM0000003':'SOME PRIVATE UPPERCASE TEXT'}}
        self.assertEqual(sanitize(raw,{})['inbound_provenance']['2026-09-07'],{'RM0000011':'EXIM-OTW+PO-LEAD-OVERDUE'})
    def test_hourly_rate_updates_use_original_carry_clock(self):
        carry={'line_configs':{'at':'2026-09-06T04:48:00+05:30','data':[{'line_name':'Clear Pack','config_name':'5 LTR','rated_speed':'3000','is_active':True,'operators':'PRIVATE_PERSON'}]}}
        out=sanitize(fixture(),{}, {'rates':[{'line':'Clear Pack','pack':'5L','piecesPerHour':1000,'basis':'rated'}]},carry)
        self.assertEqual(out['supplements']['rates'][0]['piecesPerHour'],3000)
        self.assertEqual(out['supplements']['rates'][0]['asOf'],carry['line_configs']['at'])
        self.assertNotIn('PRIVATE_PERSON',json.dumps(out))
    def test_order_identity_stable_across_backlog_reordering_and_clamped_date(self):
        raw=fixture();first=raw['orders'][0];second={**first,'pieces':4};identical=dict(first)
        raw['orders']=[first,second,identical]
        raw['backlog']=[{**r,'date':'2026-08-20'} for r in reversed(raw['orders'])]
        out=sanitize(raw,{})
        self.assertEqual({r['docnum'] for r in out['orders']},{r['docnum'] for r in out['backlog']})
        self.assertEqual(len({r['docnum'] for r in out['orders']}),3)
        # The engine merges both arrays by stable ID: no duplicate demand, no collapsed lines.
        merged={r['docnum']:r for r in out['orders']+out['backlog']}
        self.assertEqual(sum(r['pieces'] for r in merged.values()),10)
    def test_ecom_allocation_is_not_an_exact_confirmed_sku_due_date(self):
        raw=fixture();raw['orders'][0].update({'channel':'ECOM','_src':'ECOM-PO'})
        order=sanitize(raw,{})['orders'][0]
        self.assertEqual(order['demand_basis'],'allocated_ecom_mix')
        self.assertFalse(order['is_exact_sku_due']);self.assertEqual(order['value_basis'],'derived_realisation')
    def test_non_oil_code_collision_classified_for_quarantine(self):
        raw=fixture();raw['orders'][0]['channel']='BEVERAGES'
        self.assertEqual(sanitize(raw,{})['orders'][0]['planning_scope'],'non_oil_or_unverified')
    def test_supplement_aggregation_excludes_personnel(self):
        out=sanitize(fixture(),{}, {'recordedLabour':{'runs':[{'line':'10 Head','code':'FG0000142','date':'2026-09-01','labourCost':100,'workers':[{'name':'PRIVATE_PERSON'}]}]}})
        self.assertNotIn('PRIVATE_PERSON',json.dumps(out));self.assertEqual(out['supplements']['recordedLabour']['runs'][0]['labourCost'],100)
    def test_operational_strings_bounded_and_contact_redacted(self):
        raw=fixture();raw['plan'][0]['sku']='OIL PRIVATE@EXAMPLE.COM /root/config '+('x'*200)
        value=sanitize(raw,{})['plan'][0]['sku'];self.assertLessEqual(len(value),180);self.assertNotIn('/root',value);self.assertNotIn('@',value)

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'sim').mkdir();(self.root/'live/state').mkdir(parents=True)
        self.source=self.root/'sim/live-inputs.json';self.source.write_text(json.dumps(fixture()));(self.root/'live/state/state.json').write_text('{}')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.server.feed=Feed(self.root,{},ttl=0);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):self.server.shutdown();self.thread.join();self.server.server_close();self.tmp.cleanup()
    def test_only_exact_read_routes_and_no_writes(self):
        self.assertEqual(urlopen(self.url+'/inputs.json').status,200)
        for path in ['/','/inputs.json?raw=1','/../sim/live-inputs.json','/state.json']:
            with self.assertRaises(HTTPError) as error:urlopen(self.url+path)
            self.assertEqual(error.exception.code,404);error.exception.close()
        with self.assertRaises(HTTPError) as error:urlopen(Request(self.url+'/inputs.json',data=b'overwrite',method='POST'))
        self.assertEqual(error.exception.code,501);error.exception.close();self.assertEqual(json.loads(self.source.read_text())['meta']['month'],'September 2026')
    def test_last_good_retained_on_corruption_original_clock(self):
        first=urlopen(self.url+'/inputs.json');original=json.loads(first.read());self.assertEqual(first.headers['X-Mark4-Retained-Last-Good'],'false');self.source.write_text('{')
        response=urlopen(self.url+'/inputs.json');retained=json.loads(response.read());self.assertEqual(response.headers['X-Mark4-Retained-Last-Good'],'true');self.assertEqual(response.headers['X-Mark4-Source-Status'],'error');health=json.loads(urlopen(self.url+'/healthz').read())
        self.assertEqual(original,retained);self.assertEqual(health,{'ok':False,'retainedLastGood':True,'materialCoverageComplete':False})
    def test_first_read_failure_generic_503(self):
        self.source.unlink()
        with self.assertRaises(HTTPError) as error:urlopen(self.url+'/inputs.json')
        self.assertEqual(error.exception.code,503);self.assertNotIn(self.tmp.name,error.exception.read().decode());error.exception.close()
if __name__=='__main__':unittest.main()
