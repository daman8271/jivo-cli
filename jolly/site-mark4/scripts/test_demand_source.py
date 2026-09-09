import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from demand_source import normalize_sources, normalize_directory, verify_factory_mapping, factory_pack

NOW = '2026-09-06T01:00:00+00:00'
def amazon(**kw):
    row=dict(po_number='fixture',sku_code='sku',sap_sku_code='FG1',per_liter=1,total_order_liters=100,total_delivered_liters=10,total_accepted_liters=80,requested_qty=100,received_qty=10,accepted_qty=80,order_date='2026-08-01',expiry_date='2026-09-20',po_status='PENDING')
    row.update(kw);return row

def normal(rows=[],oms=[]):return normalize_sources(rows,[],[],oms,as_of=NOW)

class DemandTests(unittest.TestCase):
    def test_requested_accepted_and_original_prior_month(self):
        d=normal([amazon()]);b=d['demandBook']['online']
        self.assertEqual((b['grossOpenLitres'],b['acceptedOpenLitres'],b['unacceptedRequestedLitres']),(90,70,20))
        self.assertEqual(d['orders'][0]['pieces'],70)
        self.assertEqual(b['priorMonthOpenLitres'],90)
    def test_expired_excluded(self):
        d=normal([amazon(expiry_date='2026-09-05')]);self.assertEqual(d['orders'],[]);self.assertEqual(d['demandBook']['online']['expiredExcludedLitres'],90)
    def test_future_gross_not_current(self):
        d=normal([amazon(expiry_date='2026-10-01')]);b=d['demandBook']['online'];self.assertEqual((b['grossOpenLitres'],b['planningDueLitres'],b['laterDueLitres']),(90,0,90))
    def test_created_does_not_manufacture_deadline(self):
        d=normal([amazon(expiry_date=None)]);self.assertEqual(d['orders'][0]['due'],'');self.assertEqual(d['demandBook']['online']['undatedLitres'],90)
    def test_outside_oil_accepted_due(self):
        d=normal([amazon(category_head='BEVERAGE')]);self.assertEqual(d['orders'],[]);b=d['demandBook']['online'];self.assertEqual((b['outsideOilScopePlanningDueLitres'],b['outsideOilScopeAcceptedPlanningDueLitres']),(90,70))
    def test_null_item_ids_distinct(self):
        rows=[dict(id=None,item_code='FG1',category='OIL',qty=5,ltrs=5),dict(id=None,item_code='FG2',category='OIL',qty=6,ltrs=6)]
        d=normal(oms=[dict(id=1,status='BILLING',company=1,items=rows)])
        self.assertEqual(len({r['sourceLineId'] for r in d['orders']}),2)
    def test_wrong_company_rejected(self):
        d=normal(oms=[dict(id=1,status='BILLING',company=3,items=[dict(category='OIL',qty=5,ltrs=5)])]);self.assertEqual(d['orders'],[]);self.assertEqual(d['demandBook']['trade']['otherCompanyOpenLitres'],5)
    def test_partial_active_details_preserve_source_clock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixtures={'oms-discovery-status.json':{'started':'2026-09-05T00:00:00+00:00','checkedAt':'2026-09-05T00:10:00+00:00','through':12,'complete':False,'counts':{'error':1},'ids':{str(i):'missing' for i in range(1,13)}},'read-status.json':{'asOf':NOW},'oms-header-snapshot.json':{'asOf':NOW,'complete':True,'orders':{'17':{'status':'ORDER_CREATED','created_at':'2026-07-01'}},'activeDetailErrors':['17']},'amazon-rows.json':[],'qcomm-rows.json':[],'products-rows.json':[]}
            for n,v in fixtures.items():(root/n).write_text(json.dumps(v))
            d=normalize_directory(root);self.assertEqual(d['asOf'],NOW);self.assertEqual(d['demandBook']['coverage'],'partial');self.assertEqual(d['demandBook']['trade']['unknownActiveOrderCount'],1);self.assertIsNone(d['demandBook']['trade']['unknownActiveOrders'][0]['litres'])
    def test_same_code_wrong_oil_rejected(self):
        ok,reason=verify_factory_mapping('FG1','EXTRA LIGHT OLIVE 1 LTR 16 PCS',1,{'FG1':{'name':'SANO POMACE OLIVE 1 LTR 16 PCS'}})
        self.assertFalse(ok)
    def test_same_code_wrong_pack_rejected(self):
        ok,reason=verify_factory_mapping('FG1','YELLOW MUSTARD OIL 1 LTR 20 PCS',1,{'FG1':{'name':'SANO POMACE OLIVE 200 LTR 1 PCS'}})
        self.assertFalse(ok)
    def test_sales_bundle_not_silently_rescaled(self):
        ok,reason=verify_factory_mapping('FG1','COLD PRESS SUNFLOWER 1 LTR 20 PCS',2,{'FG1':{'name':'COLD PRESS SUNFLOWER 1 LTR 20 PCS'}})
        self.assertFalse(ok)
    def test_factory_verified_carton_count_difference(self):
        ok,reason=verify_factory_mapping('FG1','MUSTARD KACHI GHANI 1 LTR 16 PCS',1,{'FG1':{'name':'MUSTARD KACHI GHANI 1 LTR 20 PCS'}})
        self.assertTrue(ok)
    def test_unapproved_carton_difference_not_erased(self):
        ok,_=verify_factory_mapping('FG1','OLIVE 3 LTR TIN 2 PCS',3,{'FG1':{'name':'OLIVE 3 LTR TIN 6 PCS'}})
        self.assertFalse(ok)
    def test_combo_first_number_not_factory_piece_size(self):
        self.assertIsNone(factory_pack({'name':'COLD PRESS 1 LTR + 1 LTR COMBO 10 SET'}))
    def test_factory_agreement_cannot_override_wrong_planner_identity(self):
        source=amazon(sap_sku_name='EXTRA LIGHT OLIVE 1 LTR 16 PCS')
        data=normalize_sources([source],[],[],[],as_of=NOW,factory_identity={'FG1':{'name':'EXTRA LIGHT OLIVE 1 LTR 16 PCS'}},planner_identity={'FG1':{'name':'POMACE OLIVE 1 LTR 16 PCS','packLitres':1}})
        self.assertFalse(data['orders'][0]['code_mapping_verified'])
        self.assertIn('Planner/BOM',data['orders'][0]['mappingReason'])
    def test_missing_header_id_refuses(self):
        with self.assertRaises(ValueError):normal(oms=[{'id':None}])
if __name__=='__main__':unittest.main()
