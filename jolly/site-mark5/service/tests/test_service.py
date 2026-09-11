import copy, hashlib, hmac, json, os, tempfile, threading, time, unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Service, Problem, make_server, now
os.environ['MARK5_AUTO_AI']='0'
os.environ['MARK5_AI_MIN_SECONDS']='0'
DATE='2026-09-11'
def proposal(date=DATE): return {'date':date,'runs':[],'blockers':[],'totalLitres':0,'validation':{'valid':True,'errors':[],'warnings':[]}}
def fake_engine(req):
    p=proposal(req.get('command',{}).get('date',DATE))
    return {'validation':{'valid':True,'errors':[],'warnings':[]},'proposal':p if req.get('command') else None,'snapshot':{'schemaVersion':1,'revision':'snap-'+req['sourceRevision'],'generatedAt':now(),'sourceRevision':req['sourceRevision'],'sourceAsOf':now(),'freshness':[],'today':{'date':'2026-09-10','machines':[]},'tomorrow':p,'ahead':[],'savedPlans':[],'activity':[],'jobs':[],'machineRulesVersion':'test-v1','machineRules':[],'products':[]}}
class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.path=self.temp.name+'/db.sqlite'
        self.service=Service(self.path,engine=fake_engine,ai=lambda c:{'explanation':'No justified changes','changes':[]},fetcher=lambda u:{'meta':{'as_of':'2026-09-10T00:00:00Z'},'test':1})
        self.service.refresh(); self.service.work_one()
    def tearDown(self): self.service.db.close(); self.temp.cleanup()
    def command(self,key='command-key-123',expected=None): return {'date':DATE,'expectedRevision':expected,'idempotencyKey':key,'changes':[]}
    def save(self):
        r=self.service.revise(DATE,self.command()); self.service.work_one(); return r
    def test_three_draft_edits_retain_effective_controls_after_restart(self):
        exact={'type':'set_run','machineId':'10 Head','code':'FG-TEST','pieces':2000,'shift':'day'}
        night={'type':'set_night_line','machineId':None}
        priority={'type':'prioritize_sku','code':'FG-TEST'}
        for revision,change in enumerate([exact,night,priority]):
            command=self.command('cumulative-edit-'+str(revision),revision or None);command['changes']=[change]
            job=self.service.revise(DATE,command)['job'];self.service.work_one()
            self.assertEqual('succeeded',self.service.job(job['id'])['status'])
        stored=self.service.plans(DATE)[0]['changes']
        self.assertIn(exact,stored);self.assertIn(night,stored);self.assertIn(priority,stored)
        self.service.db.close();self.service=Service(self.path,engine=fake_engine)
        latest=next(p for p in self.service.engine_request()['savedPlans'] if p['date']==DATE)
        self.assertEqual(stored,latest['changes'])
    def test_overwrites_are_canonical_and_bounded(self):
        for n in range(35):
            changes=[{'type':'set_run','machineId':'10 Head','code':'FG-TEST','pieces':2000+n,'shift':'day'},
                     {'type':'set_line_enabled','machineId':'10 Head','enabled':n%2==0},
                     {'type':'set_night_line','machineId':None if n%2 else 'auto'}]
            command=self.command('replace-edit-'+str(n),n or None);command['changes']=changes
            job=self.service.revise(DATE,command)['job'];self.service.work_one()
            self.assertEqual('succeeded',self.service.job(job['id'])['status'])
        controls=self.service.plans(DATE)[0]['changes']
        self.assertEqual(3,len(controls));self.assertEqual(2034,next(c for c in controls if c['type']=='set_run')['pieces'])
    def test_control_overflow_does_not_drop_existing_state(self):
        command=self.command();command['changes']=[{'type':'prioritize_sku','code':'SKU-'+str(n)} for n in range(30)]
        self.service.revise(DATE,command);self.service.work_one()
        command=self.command('overflow-edit-123',1);command['changes']=[{'type':'prioritize_sku','code':'SKU-31'}]
        with self.assertRaises(Problem) as error:self.service.revise(DATE,command)
        self.assertEqual(422,error.exception.status);self.assertEqual(1,len(self.service.plans(DATE)));self.assertEqual(30,len(self.service.plans(DATE)[0]['changes']))
    def test_legacy_delta_chain_is_recovered_without_mutating_history(self):
        exact={'type':'set_run','machineId':'10 Head','code':'FG-TEST','pieces':2000,'shift':'day'}
        night={'type':'set_night_line','machineId':None}
        for n,change in enumerate([exact,night]):
            command=self.command('legacy-edit-'+str(n),n or None);command['changes']=[change]
            self.service.revise(DATE,command);self.service.work_one()
        legacy=self.service.plans(DATE)[0];legacy['changes']=[night]
        self.service.db.execute('UPDATE plans SET data=? WHERE date=? AND revision=2',(json.dumps(legacy),DATE))
        self.service.db.execute('DELETE FROM kv WHERE k=?',('controls_version:'+legacy['id'],))
        before=self.service.db.execute('SELECT data FROM plans WHERE date=? AND revision=2',(DATE,)).fetchone()[0]
        loaded=next(p for p in self.service.engine_request()['savedPlans'] if p['date']==DATE)
        self.assertEqual([exact,night],loaded['changes'])
        self.assertEqual(before,self.service.db.execute('SELECT data FROM plans WHERE date=? AND revision=2',(DATE,)).fetchone()[0])
    def test_real_engine_retains_exact_run_through_three_edits_and_restart(self):
        fixed='2026-09-10T06:00:00+05:30';code='FG-TEST'
        fixture={'schemaVersion':1,'meta':{'as_of':fixed},'plan':[{'code':code,'sku':'SUNFLOWER 1 LTR 20 PCS','category':'SUNFLOWER','pack_type':'BOTTLE','litres_per_piece':1,'pieces':1000000}],
            'bom':{code:[['RM-OIL',1],['PM-BOTTLE',1],['CARTON',.05]]},'blends':{},'items':{code:{'name':'SUNFLOWER 1 LTR 20 PCS','uom':'PCS'},'RM-OIL':{'name':'OIL','uom':'LTR'},'PM-BOTTLE':{'name':'PET BOTTLE 1 LTR 40 GM','uom':'PCS'},'CARTON':{'name':'CORRUGATED CARTON 20 PCS','uom':'PCS'}},'realise':{},
            'opening':{'stock':{'RM-OIL':10000000,'PM-BOTTLE':10000000,'CARTON':10000000},'fg':{},'fg_other_l':0,'standing_l':0},'orders':[],'inbound_prebooked':{},'lines':{},
            'history':{'status':'complete','missing_dates':[],'days':[{'date':'2026-09-'+str(n).zfill(2),'made_mes_l':0,'made_booked_l':0,'booked_by_item':{},'complete':True} for n in range(1,10)]},'sources':[]}
        fixture['materialSupply']={'version':1,'revision':'synthetic-exim','asOf':fixed,'coverage':{'complete':True,'datasets':[]},'stock':{'asOf':fixed,'byItem':fixture['opening']['stock'],'oilSourcePolicy':'exim_only','byWarehouse':{},'excludedWarehouses':[],'conflicts':[]},'orders':[],'lots':[],'expectedReceipts':[],'actions':[]}
        self.service.fetcher=lambda url: fixture if url.endswith('inputs.json') else {}
        self.service.engine=lambda request:self.service.run_engine({**request,'now':fixed})
        job=self.service.refresh()['job'];self.service.work_one();self.assertEqual('succeeded',self.service.job(job['id'])['status'])
        changes=[{'type':'set_run','machineId':'10 Head','code':code,'pieces':2000,'shift':'day'},{'type':'set_night_line','machineId':None},{'type':'prioritize_sku','code':code}]
        for n,change in enumerate(changes):
            command=self.command('real-engine-edit-'+str(n),n or None);command['changes']=[change]
            job=self.service.revise(DATE,command)['job'];self.service.work_one()
            self.assertEqual('succeeded',self.service.job(job['id'])['status'],self.service.job(job['id']))
            run=next(r for r in self.service.plans(DATE)[0]['proposal']['runs'] if r['machineId']=='10 Head' and r['shift']=='day')
            self.assertEqual(2000,run['pieces']);self.assertEqual(100,run['cases'])
        self.service.db.close();self.service=Service(self.path)
        result=self.service.run_engine({**self.service.engine_request(),'now':fixed})
        run=next(r for r in result['snapshot']['tomorrow']['runs'] if r['machineId']=='10 Head' and r['shift']=='day')
        self.assertEqual(2000,run['pieces']);self.assertEqual(100,run['cases'])
        # Approval pins this exact run. A later AI no-op must not execute its
        # inherited controls again during a normal background refresh.
        self.service.approve(DATE,{'expectedRevision':3,'idempotencyKey':'real-controls-approve'})
        self.service.ai=lambda context:{'explanation':'No change is justified','changes':[]}
        self.service.engine=lambda request:self.service.run_engine({**request,'now':fixed})
        job=self.service.ai_review({'date':DATE,'idempotencyKey':'real-controls-ai-noop'})['job'];self.service.work_one()
        self.assertEqual('succeeded',self.service.job(job['id'])['status'],self.service.job(job['id']))
        result=self.service.run_engine({**self.service.engine_request(),'now':fixed})
        self.assertTrue(result['validation']['valid'],result['validation'])
        matches=[r for r in result['snapshot']['tomorrow']['runs'] if r['machineId']=='10 Head' and r['shift']=='day']
        self.assertEqual(1,len(matches));self.assertEqual(2000,matches[0]['pieces'])
    def test_restart_and_idempotency(self):
        first=self.save(); self.service.db.close()
        self.service=Service(self.path,engine=fake_engine)
        second=self.service.revise(DATE,self.command())
        self.assertEqual(first['job']['id'],second['job']['id']); self.assertEqual(1,len(self.service.plans(DATE)))
        self.assertEqual('succeeded',second['job']['status'])
    def test_idempotency_rejects_changed_content(self):
        self.save(); b=self.command(); b['changes']=[{'type':'set_night_line','machineId':None}]
        with self.assertRaises(Problem) as e:self.service.revise(DATE,b)
        self.assertEqual(409,e.exception.status)
    def test_coalesces_refresh(self):
        a=self.service.refresh(); b=self.service.refresh(); self.assertEqual(a['job']['id'],b['job']['id'])
    def test_concurrent_revisions_only_one_publishes(self):
        a=self.service.revise(DATE,self.command()); b=self.service.revise(DATE,self.command('second-key-123'))
        self.service.work_one(); self.service.work_one()
        self.assertEqual('succeeded',self.service.job(a['job']['id'])['status']);self.assertEqual('superseded',self.service.job(b['job']['id'])['status'])
        self.assertEqual(1,len(self.service.plans(DATE)))
    def test_approval_exact_revision_and_refresh_preserves(self):
        self.save(); approved=self.service.approve(DATE,{'expectedRevision':1,'idempotencyKey':'approval-123'})
        self.service.refresh();self.service.work_one()
        self.assertEqual(approved,self.service.plans(DATE)[0])
        self.assertEqual(approved,self.service.approve(DATE,{'expectedRevision':1,'idempotencyKey':'approval-123'}))
    def test_approval_rejects_new_sources(self):
        self.save();self.service.put('source_revision','newer')
        with self.assertRaises(Problem) as e:self.service.approve(DATE,{'expectedRevision':1,'idempotencyKey':'approval-123'})
        self.assertEqual(409,e.exception.status)
    def test_source_race_does_not_publish(self):
        before=self.service.get('snapshot')
        def race(req):
            result=fake_engine(req);self.service.put('source_revision','newer');return result
        self.service.engine=race; job=self.service.revise(DATE,self.command());self.service.work_one()
        self.assertEqual('superseded',self.service.job(job['job']['id'])['status']);self.assertEqual([],self.service.plans(DATE));self.assertEqual(before,self.service.get('snapshot'))
    def test_failure_retains_last_good(self):
        def fail(url):raise RuntimeError('secret-provider-data')
        self.service.fetcher=fail;self.service.refresh();self.service.work_one()
        self.assertTrue(self.service.dashboard()['tomorrow']);self.assertTrue(any(s['status']=='stale' for s in self.service.dashboard()['freshness']))
        self.assertNotIn('secret-provider-data',json.dumps(self.service.dashboard()))
    def test_ai_actual_result_saved_and_engine_validated(self):
        j=self.service.ai_review({'date':DATE,'idempotencyKey':'ai-review-123'});self.service.work_one()
        self.assertEqual('succeeded',self.service.job(j['job']['id'])['status']);p=self.service.plans(DATE)[0];self.assertEqual('ai',p['createdBy']);self.assertEqual('draft',p['status'])
        self.assertEqual('No justified changes',self.service.get('ai_result:'+j['job']['id'])['explanation'])
    def test_ai_invalid_change_does_not_save(self):
        self.service.ai=lambda c:{'explanation':'malicious','changes':[{'type':'run_shell','command':'cat secrets'}]}
        j=self.service.ai_review({'date':DATE,'idempotencyKey':'ai-review-123'});self.service.work_one()
        self.assertEqual('failed',self.service.job(j['job']['id'])['status']);self.assertEqual([],self.service.plans(DATE))
    def test_ai_engine_invalid_does_not_save(self):
        self.service.engine=lambda r:{**fake_engine(r),'validation':{'valid':False,'errors':['Unsupported route'],'warnings':[]}}
        j=self.service.ai_review({'date':DATE,'idempotencyKey':'ai-review-123'});self.service.work_one()
        self.assertEqual('failed',self.service.job(j['job']['id'])['status']);self.assertEqual([],self.service.plans(DATE))
    def test_ai_other_date_not_coalesced(self):
        self.service.ai_review({'date':DATE,'idempotencyKey':'ai-review-123'})
        with self.assertRaises(Problem) as e:self.service.ai_review({'date':'2026-09-12','idempotencyKey':'ai-review-456'})
        self.assertEqual(429,e.exception.status)
    def test_interrupted_ai_does_not_rebill_on_restart(self):
        j=self.service.ai_review({'date':DATE,'idempotencyKey':'ai-review-123'})['job']
        self.service.db.execute("UPDATE jobs SET status='running' WHERE id=?",(j['id'],));self.service.db.close();self.service=Service(self.path,engine=fake_engine)
        self.assertEqual('failed',self.service.job(j['id'])['status'])
    def test_meaningful_fingerprint_ignores_clock(self):
        a=self.service.dashboard();b=copy.deepcopy(a);b['generatedAt']='later';b['today']['asOf']='later';b['tomorrow']['assumptions']=[{'detail':'new timestamp'}]
        self.assertEqual(Service.meaningful_fingerprint(a),Service.meaningful_fingerprint(b))
        b['today']['machines']=[{'machineId':'JP Machine','status':'running','recordedLitres':1000}]
        self.assertNotEqual(Service.meaningful_fingerprint(a),Service.meaningful_fingerprint(b))
    def test_collection_clock_change_does_not_invalidate_approval(self):
        self.save(); original=self.service.get('source_revision')
        self.service.fetcher=lambda u:{'meta':{'as_of':'2026-09-10T00:03:00Z'},'test':1}
        self.service.refresh();self.service.work_one()
        self.assertEqual(original,self.service.get('source_revision'))
        self.assertEqual('approved',self.service.approve(DATE,{'expectedRevision':1,'idempotencyKey':'approval-123'})['status'])
    def test_business_change_advances_source_revision(self):
        before=self.service.get('source_revision')
        self.service.fetcher=lambda u:{'meta':{'as_of':'2026-09-10T00:03:00Z'},'test':2}
        self.service.refresh();self.service.work_one()
        self.assertNotEqual(before,self.service.get('source_revision'))
    def test_webhook_during_computation_supersedes_result(self):
        def race(req):
            result=fake_engine(req)
            self.service.event({'id':'during-compute-123','type':'material_changed'})
            return result
        self.service.engine=race;j=self.service.revise(DATE,self.command())['job'];self.service.work_one()
        self.assertEqual('superseded',self.service.job(j['id'])['status'])
        self.assertEqual([],self.service.plans(DATE))
    def test_ai_provider_tool_event_is_rejected(self):
        def provider(args,**kw):
            Path(args[args.index('--output-last-message')+1]).write_text(json.dumps({'explanation':'looks safe','changes':[]}))
            return SimpleNamespace(returncode=0,stderr='',stdout=json.dumps({'type':'item.completed','item':{'type':'command_execution','command':'cat private'}}))
        with patch('server.subprocess.run',side_effect=provider):
            with self.assertRaisesRegex(RuntimeError,'tool use rejected'): self.service.run_ai({'date':DATE})
    def test_ai_provider_plain_structured_message_is_accepted(self):
        def provider(args,**kw):
            self.assertIn('--ignore-user-config',args);self.assertIn('--ignore-rules',args);self.assertIn('shell_tool',args)
            self.assertEqual('read-only',args[args.index('--sandbox')+1])
            Path(args[args.index('--output-last-message')+1]).write_text(json.dumps({'explanation':'No supported change','changes':[]}))
            return SimpleNamespace(returncode=0,stderr='',stdout=json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'structured result'}}))
        with patch('server.subprocess.run',side_effect=provider):
            self.assertEqual([],self.service.run_ai({'date':DATE})['changes'])
    def test_http_auth_etag_events_and_limits(self):
        server=make_server(self.service,port=0,secret='s'*40,webhook_secret='w'*40)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        def call(path,body=None,headers=None):
            raw=json.dumps(body).encode() if body is not None else None
            req=Request(base+path,data=raw,headers=headers or {})
            try:
                with urlopen(req,timeout=3) as r:return r.status,dict(r.headers),r.read()
            except HTTPError as e:return e.code,dict(e.headers),e.read()
        try:
            code,headers,_=call('/v1/dashboard');self.assertEqual(200,code)
            self.assertEqual(304,call('/v1/dashboard',headers={'If-None-Match':headers['ETag']})[0])
            self.assertEqual(401,call('/v1/refresh',{})[0]);self.assertEqual(202,call('/v1/refresh',{}, {'Authorization':'Bearer '+'s'*40})[0])
            body={'id':'event-123456','type':'production_changed'};raw=json.dumps(body).encode();stamp=str(int(time.time()));sign=hmac.new(('w'*40).encode(),stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest();auth={'X-Mark5-Timestamp':stamp,'X-Mark5-Signature':sign}
            self.assertEqual(401,call('/v1/events',body)[0]);a=call('/v1/events',body,auth);b=call('/v1/events',body,auth);self.assertEqual(202,a[0]);self.assertEqual(a[2],b[2])
            self.assertEqual(404,call('/v1/plans/2026-02-30')[0]);self.assertEqual(413,call('/v1/refresh',{'x':'x'*140000},{'Authorization':'Bearer '+'s'*40})[0])
        finally:server.shutdown();server.server_close()
if __name__=='__main__': unittest.main()
