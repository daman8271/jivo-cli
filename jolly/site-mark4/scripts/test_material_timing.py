import unittest
from datetime import datetime, timedelta
from material_timing import qa_timing, readiness
from material_supply import reconcile
from test_material_supply import raw

class TimingTests(unittest.TestCase):
    def samples(self):
        return [{'id':str(i), 'supplier':'v', 'code':'RM1', 'unit':'L', 'stage':'usable', 'quantity':1,
                 'arrivalDate':f'2026-09-0{i}T20:00:00+05:30',
                 'qaAcceptedAt':f'2026-09-0{i+2}T03:30:00+05:30'} for i in [1,2,3]]
    def test_elapsed_hours_and_late_arrival_daily_credit(self):
        timing=qa_timing(self.samples(),'v','RM1','L','2026-09-08T10:00:00+05:30')
        self.assertEqual(timing['medianHours'],31.5)
        ready=readiness('2026-09-08T20:00:00+05:30',timing)
        self.assertEqual(ready['qaEstimatedAt'],'2026-09-10T03:30:00+05:30')
        self.assertEqual(ready['usableExpected'],'2026-09-10')
        self.assertIsNone(ready['storesReleaseAt'])
    def test_date_only_arrival_uses_late_edge(self):
        ready=readiness('2026-09-08',{'medianHours':31.5,'minHours':31.5,'maxHours':31.5})
        self.assertFalse(ready['arrivalTimeKnown'])
        self.assertEqual(ready['usableExpected'],'2026-09-10')
    def test_invalid_future_conflicting_rejected_and_unit_mismatch_excluded(self):
        for update in [{'unit':'PCS'},{'stage':'conflict'},{'raw':{'rejectedQty':1}}, {'qaAcceptedAt':'2026-10-01T00:00:00+05:30'}, {'qaAcceptedAt':'2026-08-01'}, {'arrivalDate':'2026-09-01'}]:
            rows=self.samples(); rows[0].update(update)
            self.assertIsNone(qa_timing(rows,'v','RM1','L','2026-09-08T10:00:00+05:30'))
    def test_source_eta_miss_blocks_even_when_qa_would_be_future(self):
        data=raw(); data['asOf']='2026-09-08T10:00:00+05:30'
        data['receipts']=[{'id':r['id'], 'gateId':r['id'], 'code':'RM0000025', 'unit':'L', 'quantity':10,
            'supplier':'v', 'arrivalDate':r['arrivalDate'], 'qaAcceptedAt':r['qaAcceptedAt'], 'posted':True,
            'qcStatus':'ACCEPTED'} for r in self.samples()]
        data['shipments']=[{'id':'load','code':'RM0000025','supplier':'v','quantity':100,'eta':'2026-09-07','stage':'in_transit'}]
        self.assertEqual(reconcile(data)['expectedReceipts'],[])
        data['shipments'][0]['eta']='2026-09-08'
        result=reconcile(data)
        self.assertEqual(result['expectedReceipts'][0]['qaMedianHours'],31.5)
        self.assertEqual(result['expectedReceipts'][0]['usableExpected'],'2026-09-10')
        from revision_input import merge_material_supply
        out={'opening':{},'items':{},'sources':[]}
        merge_material_supply(out,{'ok':True,'asOf':data['asOf'],'data':result})
        self.assertEqual(out['materialSupply']['expectedReceipts'][0]['qaMedianHours'],31.5)
        self.assertEqual(out['materialSupply']['expectedReceipts'][0]['timingVersion'],2)
    def test_cached_negative_or_unknown_factory_oil_never_creates_stock(self):
        from revision_input import merge_material_supply
        for quantity in [-100, None, float('nan')]:
            data=raw(); result=reconcile(data)
            result['stock'].pop('oilSourcePolicy')
            result['stock']['byItem']['RM0000025']=0
            result['stock']['byWarehouse']['BH-LO']=[{'code':'RM0000025','quantity':quantity,'unit':'L',
                'included':True,'normalizedQuantity':quantity,'normalizedUnit':'L','asOf':data['asOf']}]
            out={'opening':{},'items':{},'sources':[]}
            merge_material_supply(out,{'ok':True,'asOf':data['asOf'],'data':result})
            self.assertEqual(out['materialSupply']['stock']['byItem']['RM0000025'],0)
    def test_unmapped_shipment_is_published_without_stock_or_arrival_credit(self):
        from revision_input import merge_material_supply
        data=raw(); data['unmappedShipments']=[{'name':'2B Pakki Ghani', 'quantity':123, 'eta':'2026-09-19', 'stage':'in_transit'}]
        result=reconcile(data)
        self.assertEqual(result['expectedReceipts'],[])
        self.assertFalse(any(code.startswith('RM') for code in result['stock']['byItem']))
        out={'opening':{},'items':{},'sources':[]}
        merge_material_supply(out,{'ok':True,'asOf':data['asOf'],'data':result})
        row=out['materialSupply']['unmappedShipments'][0]
        self.assertEqual((row['name'], row['quantity'], row['eta'], row['stage']),('2B Pakki Ghani',123,'2026-09-19','in_transit'))
    def test_factory_oil_is_excluded_and_unmapped_tank_preserved(self):
        data=raw(); data['stock']['BH-LO']={'asOf':data['asOf'],'rows':[{'item_code':'RM0000025','on_hand':900,'uom':'L'}]}
        data['tanks']=[{'code':'','name':'2B Pakki Ghani','quantity':10}]
        out=reconcile(data)
        self.assertNotIn('RM0000025',out['stock']['byItem'])
        self.assertEqual(out['stock']['unmappedOils'][0]['quantity'],10)
        self.assertFalse(out['stock']['byWarehouse']['BH-LO'][0]['included'])
if __name__=='__main__': unittest.main()

class TemporaryPackagingTests(unittest.TestCase):
    def data(self):
        from test_material_supply import po, receipt
        data=raw(); data['asOf']='2026-09-09T10:00:00+05:30'
        order=po(100); order['doc_date']='2026-09-08'; data['orders']=[order]
        data['receipts']=[receipt(i, quantity=40, poNumber='CLOSED', posted=True, stockSnapshotAfterPosting=True,
            arrivalDate=f'2026-09-{d:02}T08:00:00+05:30',qaAcceptedAt=f'2026-09-{d:02}T10:00:00+05:30') for i,d in enumerate([1,4,7])]
        return data
    def test_temporary_history_splits_and_caps_existing_po_without_new_supply(self):
        data=self.data(); result=reconcile(data); rows=result['expectedReceipts']
        self.assertTrue(rows)
        self.assertEqual(sum(r['quantity'] for r in rows),100)
        self.assertTrue(all(r['basis']=='temporary_packaging_estimate' and r['temporaryUntil']=='2026-09-10' and r['timingVersion']==2 for r in rows))
        self.assertEqual(rows[0]['arrivalExpected'],'2026-09-10')
        self.assertEqual(rows[0]['qaMedianHours'],2)
        self.assertEqual(len({r['lotId'] for r in rows}),len(rows))
        self.assertEqual(sum(l['quantity'] for l in result['lots'] if l.get('orderId')==result['orders'][0]['id']),100)
        data['asOf']='2026-09-11T10:00:00+05:30';self.assertEqual(reconcile(data)['expectedReceipts'],[])
    def test_rejected_history_and_unknown_cohort_do_not_create_dates(self):
        data=self.data();data['receipts'][0]['rejectedQty']=1
        self.assertEqual(reconcile(data)['expectedReceipts'],[])
        data=self.data();data['receipts'][0]['supplier']='OTHER'
        self.assertEqual(reconcile(data)['expectedReceipts'],[])
