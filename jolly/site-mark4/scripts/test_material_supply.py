import copy
import tempfile
import unittest
from material_supply import reconcile, amount
from replenishment_history import day
from collect_material_supply import scan_orders, retained, read_stock
from revision_input import merge_material_supply, add_exim_transit


def raw():
    return {'asOf':'2026-09-16T10:00:00+05:30','horizonEnd':'2026-09-30','oilCodes':['RM0000025'],
        'densityKgPerLitre':.91,'aliases':{},'stock':{'BH-PM':{'asOf':'2026-09-16T10:00:00+05:30',
        'rows':[{'item_code':'PM0000001','on_hand':20,'uom':'PCS'}, {'item_code':'PM0000075','on_hand':100,'uom':'MTR'}]}},
        'tanks':[],'receipts':[],'orders':[],'shipments':[],'historyFrom':'2026-07-01','receiptHistoryComplete':True,
        'datasets':[{'id':'po','asOf':'2026-09-16T10:00:00+05:30','ok':True,'complete':True,'expectedRefreshSeconds':180}]}


def po(quantity=100):
    return {'po_number':'PRIVATE-PO','doc_date':'2026-09-16','supplier_code':'PRIVATE-VENDOR',
        'items':[{'line_num':0,'po_item_code':'PM0000001','uom':'PCS','ordered_qty':quantity,'received_qty':0,'remaining_qty':quantity}]}


def receipt(i, quantity=30, **kw):
    return {'id':i,'gateId':i,'code':'PM0000001','poNumber':'PRIVATE-PO','lineNum':0,'supplier':'PRIVATE-VENDOR',
        'quantity':quantity,'rejectedQty':0,'unit':'PCS','qcStatus':'ACCEPTED','posted':False,
        'arrivalDate':'2026-09-16','observedAt':'2026-09-16T10:00:00+05:30',**kw}


class SupplyTests(unittest.TestCase):
    def test_native_tape_unit_and_invalid_quantity(self):
        result=reconcile(raw())
        self.assertEqual(result['stock']['byItem']['PM0000075'],100)
        self.assertEqual(result['stock']['unitByItem']['PM0000075'],'MTR')
        with self.assertRaises(ValueError):amount('unread')

    def test_partial_receipt_once_and_unresolved_acceptance(self):
        data=raw();data['orders']=[po()];data['receipts']=[receipt(1),receipt(1)]
        result=reconcile(data)
        self.assertEqual(result['orders'][0]['atGateQty'],30)
        self.assertEqual(result['orders'][0]['notYetAtGateQty'],70)
        self.assertTrue(any(r['stage']=='accepted_unposted' and r['stockInclusion']=='unresolved' for r in result['lots']))

    def test_po_line_identity_conflict_and_quantity_conflict(self):
        data=raw();data['orders']=[po()];data['receipts']=[receipt(1,code='PM0000002')]
        result=reconcile(data)
        self.assertEqual(result['orders'][0]['notYetAtGateQty'],100)
        self.assertTrue(any(r['stage']=='conflict' for r in result['lots']))
        data['receipts']=[receipt(1,quantity=120)]
        self.assertTrue(any(r['stage']=='conflict' for r in reconcile(data)['lots']))

    def test_false_posted_flag_does_not_subtract_book_received_twice(self):
        data=raw();data['orders']=[po(10000)];data['orders'][0]['items'][0].update(received_qty=1800,remaining_qty=8200)
        data['receipts']=[receipt(1,quantity=900,posted=True,stockSnapshotAfterPosting=True),receipt(2,quantity=900)]
        result=reconcile(data)
        self.assertEqual(result['orders'][0]['atGateQty'],0)
        self.assertEqual(result['orders'][0]['notYetAtGateQty'],8200)
        data['orders'][0]['items'][0].update(ordered_qty=500000,received_qty=411000,remaining_qty=89000)
        data['receipts']=[receipt(1,quantity=174000,posted=True,stockSnapshotAfterPosting=True),receipt(2,quantity=288000)]
        result=reconcile(data)
        self.assertAlmostEqual(result['orders'][0]['atGateQty'],51000)
        self.assertAlmostEqual(result['orders'][0]['notYetAtGateQty'],38000)
        self.assertTrue(any(l['quantity']==288000 and l['stage']=='accepted_unposted' and l['stockInclusion']=='unresolved' for l in result['lots']))

    def test_supplier_history_splits_batches_and_missing_history_does_not_invent_date(self):
        data=raw();data['orders']=[po()]
        self.assertEqual(reconcile(data)['expectedReceipts'],[])
        for i,d in enumerate([5,9,13]):
            data['receipts'].append(receipt(i,quantity=40,poNumber='CLOSED',posted=True,stockSnapshotAfterPosting=True,
                arrivalDate=f'2026-09-{d:02}',qaAcceptedAt=f'2026-09-{d+1:02}'))
        result=reconcile(data)
        self.assertEqual(result['expectedReceipts'], [])
        self.assertTrue(any(l['quantity'] == 100 and l['stage'] == 'ordered' for l in result['lots']))
        self.assertEqual(len({r['lotId'] for r in result['expectedReceipts']}),len(result['expectedReceipts']))
        data['asOf']='2026-09-24T10:00:00+05:30'
        self.assertEqual(reconcile(data)['expectedReceipts'],[])

    def test_ist_dates_and_public_reference_links(self):
        self.assertEqual(str(day('2026-09-01T20:00:00Z')),'2026-09-02')
        data=raw();data['orders']=[po()];data['receipts']=[receipt('PRIVATE-ID')]
        result=reconcile(data)
        out={'opening':{},'items':{},'sources':[]}
        merge_material_supply(out,{'ok':True,'asOf':data['asOf'],'data':result})
        order=out['materialSupply']['orders'][0]
        self.assertTrue(any(l.get('orderId')==order['id'] for l in out['materialSupply']['lots']))
        self.assertNotIn('PRIVATE',str(out))
        add_exim_transit(out,{},'/does-not-exist')
        self.assertEqual(out['inboundEvents'],[])


class CollectorTests(unittest.TestCase):
    def test_new_supplier_and_failed_supplier_retention(self):
        class Client:
            vendors=['A'];fail=False
            def get(self,path,params=None):
                if path=='/po/vendors/':return [{'vendor_code':v} for v in self.vendors]
                if params['supplier_code']=='A' and self.fail:raise ValueError('outage')
                return [{**po(),'po_number':params['supplier_code']}]
        with tempfile.TemporaryDirectory() as cache:
            client=Client();first=scan_orders(client,cache)
            client.vendors=['A','B'];client.fail=True;second=scan_orders(client,cache)
            self.assertFalse(second['complete']);self.assertEqual(len(second['orders']),2)
            self.assertEqual(first['orders'][0]['sourceAsOf'],second['orders'][0]['sourceAsOf'])

    def test_retained_read_preserves_original_clock(self):
        with tempfile.TemporaryDirectory() as cache:
            first=retained(cache,'stock',lambda:{'quantity':9})
            def fail():raise ValueError('unread')
            second=retained(cache,'stock',fail)
            self.assertFalse(second['ok']);self.assertEqual(second['data'],first['data']);self.assertEqual(second['asOf'],first['asOf'])


if __name__=='__main__':unittest.main()
