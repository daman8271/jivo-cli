import copy
import json
import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from revision_input import merge, add_exim_transit


def output():
    return {'sources':[], 'orders':[{'old':'allocation'}], 'backlog':[], 'items':{}, 'bom':{}, 'supplements':{}, 'history':{'days':[{'date':'2026-09-01','made_mes_l':10,'made_booked_l':20}]}}


def envelope():
    now=datetime.now(timezone.utc).isoformat()
    return {'asOf':now,'ok':True,'data':{'demandBook':{'asOf':now,'coverage':'complete','online':{'grossOpenLitres':100,'acceptedOpenLitres':70,'unacceptedRequestedLitres':30,'planningDueLitres':90,'acceptedPlanningDueLitres':60,'byPlatform':[]},'trade':{'grossOpenLitres':12,'planningDueLitres':12,'isNetOutstanding':False,'scopeVerified':True},'reconciliationNotes':['Requested and accepted are distinct.']},'orders':[{'docnum':'PRIVATE-PO','sourceLineId':'line1','code':None,'date':'2026-08-01','due':'2026-09-12','expiresAt':'2026-09-30','pieces':5,'remainingLitres':5,'packLitres':1,'status':'OPEN'}]}}


class RevisionContractTests(unittest.TestCase):
    def test_exim_preserves_individual_shipments_and_source_dates(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'live';p.mkdir();(p/'freeze_live.py').write_text("OIL_NAME_TO_RM={'POMACE':'RM0000013','EXTRA LIGHT':'RM0000012'}")
            now=datetime.now(timezone.utc).isoformat()
            state={'exim':{'inbound':{'fetched_at':now,'on_the_way':[{'id':1,'oil':'POMACE','litres':20,'eta':'2026-09-05','vehicle':'PRIVATE'}, {'id':2,'oil':'EXTRA LIGHT','litres':30,'eta':'2026-09-12'}, {'id':3,'oil':'POMACE','litres':10,'grpo_number':'PRIVATE'}]}}}
            out=output();out['inboundEvents']=[{'id':'factory-po'}];add_exim_transit(out,state,root)
            self.assertEqual(len(out['inboundEvents']),4)
            self.assertEqual(out['inboundEvents'][1]['expectedAt'],'2026-09-05')
            self.assertEqual(out['inboundEvents'][2]['code'],'RM0000012')
            self.assertTrue(out['inboundEvents'][3]['stockIncluded'])
            self.assertEqual(out['inboundEvents'][3]['status'],'received')
            self.assertNotIn('PRIVATE',json.dumps(out))

    def test_empty_success_is_not_live(self):
        for kind in ('factory','demand'):
            out=output(); merge(out,{'asOf':datetime.now(timezone.utc).isoformat(),'ok':True,'data':{}},kind)
            self.assertFalse(out['sources'][0]['ok']);self.assertEqual(out['orders'],[{'old':'allocation'}])

    def test_requested_accepted_and_unmapped_survive(self):
        out=output();merge(out,envelope(),'demand')
        self.assertTrue(out['sources'][0]['ok']);self.assertEqual(out['demandBook']['online']['acceptedOpenLitres'],70)
        self.assertEqual(out['demandBook']['online']['unacceptedRequestedLitres'],30)
        self.assertFalse(out['demandBook']['trade']['isNetOutstanding'])
        self.assertIsNone(out['orders'][0]['code']);self.assertEqual(out['orders'][0]['remainingLitres'],5)
        self.assertEqual(out['orders'][0]['date'],'2026-08-01');self.assertNotIn('PRIVATE-PO',json.dumps(out))

    def test_source_identity_cannot_replace_factory_recipe_identity(self):
        e=envelope();e['data']['items']={'FG0000328':{'name':'YELLOW MUSTARD 1 LTR','uom':'PCS'}}
        e['data']['orders'][0].update(code='FG0000328',sourceProductName='YELLOW MUSTARD 1 LTR',sourcePackLitres=1,code_mapping_verified=False,mappingReason='Factory identity differs')
        e['data']['identityConflicts']=[{'code':'FG0000370','reason':'Case specification differs','factoryName':'OLIVE 3 LTR 2 PCS','plannerName':'OLIVE 3 LTR 6 PCS'}]
        out=output();out['items']['FG0000328']={'name':'SANO POMACE 200 LTR','uom':'PCS'};merge(out,e,'demand')
        self.assertEqual(out['items']['FG0000328']['name'],'SANO POMACE 200 LTR')
        self.assertFalse(out['orders'][0]['code_mapping_verified'])
        self.assertEqual(out['orders'][0]['sourcePackLitres'],1)
        self.assertEqual(out['identityConflicts'][0]['code'],'FG0000370')

    def test_old_data_date_wins_over_new_attempt(self):
        e=envelope();old=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat();e['data']['demandBook']['asOf']=old
        out=output();merge(out,e,'demand');self.assertFalse(out['sources'][0]['ok']);self.assertEqual(out['sources'][0]['asOf'],old)

    def test_failed_and_partial_coverage_retain_but_do_not_become_live(self):
        for failure in ('failed','partial'):
            e=envelope()
            if failure=='failed':e['ok']=False
            else:e['data']['demandBook']['coverage']='partial'
            out=output();merge(out,e,'demand');self.assertFalse(out['sources'][0]['ok']);self.assertEqual(out['demandBook']['online']['grossOpenLitres'],100)

    def test_private_nested_canaries_do_not_escape(self):
        e=envelope();e['data']['password']='CANARY';e['data']['demandBook']['online']['dateBasis']={'secret':'CANARY'};e['data']['orders'][0]['customer']='CANARY';e['data']['demandBook']['trade']['companyScope']='/root/CANARY person@example.com'
        out=output();merge(out,e,'demand');s=json.dumps(out);self.assertNotIn('CANARY',s);self.assertNotIn('@',s);self.assertNotIn('/root',s)

    def test_factories_preserve_composition_without_replacing_totals(self):
        now=datetime.now(timezone.utc).isoformat();e={'asOf':now,'ok':True,'data':{'coverage':{'allSuppliers':True,'supplierCount':2},'inboundEvents':[],'recordedLabour':{'asOf':now,'runs':[{'id':'private','date':'2026-09-01','line':'JP Machine','code':'FG0000030','litres':10,'labourCost':150,'worker':'CANARY'}]},'historyDays':[{'date':'2026-09-01','mes_by_item_l':{'FG0000030':9},'mes_litres':9}]}}
        out=output();merge(out,e,'factory');self.assertTrue(out['sources'][0]['ok']);self.assertEqual(out['history']['days'][0]['made_mes_l'],10);self.assertEqual(out['history']['days'][0]['mes_by_item_l'],{'FG0000030':9});self.assertEqual(out['supplements']['recordedLabour']['runs'][0]['labourCost'],150);self.assertNotIn('CANARY',json.dumps(out))


if __name__=='__main__':unittest.main()
