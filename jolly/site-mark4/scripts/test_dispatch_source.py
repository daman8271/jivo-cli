import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dispatch_source import read_all, normalize, normalize_entry
from collect_dispatch_now import run_once

NOW = '2026-09-09T01:00:00+05:30'
def fixture(identity=1, company='JIVO_OIL', warehouse='BH-BT', litres='1000', arrival=9):
    row = {'id': identity, 'entry_no': 'DOCK-20260907-0001', 'company_code': company,
           'status': 'DISPATCHED', 'dispatch_date': '2026-09-07', 'gate_out_date': '2026-09-08',
           'dispatched_at': '2026-09-08T22:00:00+05:30', 'updated_at': '2026-09-08T22:01:00+05:30',
           'total_litres': litres, 'arrival': arrival, 'vehicle_no': 'SAME-PLATE', 'driver_mobile_no': '9999999999'}
    detail = {**row, 'document_count': 1, 'documents': [{'id': 90, 'items': [
        {'id': identity, 'item_code': 'FG0000001', 'item_name': 'OIL 1 L', 'quantity': 1000, 'uom': 'PCS', 'total_litres': litres, 'warehouse_code': warehouse}]}]}
    return row, detail
class Client:
    def __init__(self, pages): self.pages = pages
    def get(self,path,params): return self.pages[params['page']-1]
class DispatchTest(unittest.TestCase):
    def model(self, pairs):
        return normalize([x[0] for x in pairs], {str(x[0]['id']):x[1] for x in pairs}, NOW, '2026-09-08', '2026-09-09', 1)
    def test_cross_day_docking_uses_departure(self):
        m=self.model([fixture()]);self.assertEqual(m['days'][0]['combinedLitres'],1000);self.assertEqual(m['days'][1]['combinedLitres'],0)
    def test_scope_and_operational_classification(self):
        m=self.model([fixture(),fixture(2,'JIVO_OIL','GP-FG','400'),fixture(3,'JIVO_MART','GP-FGM','700'),fixture(4,'JIVO_BEVERAGES','BH-FG','800')])
        d=m['days'][0];self.assertEqual(d['combinedLitres'],2100);self.assertEqual(d['wellnessLitres'],1400);self.assertEqual(d['martLitres'],700)
        self.assertEqual(d['operationalWellnessLitres'],1000);self.assertEqual(d['operationalMartLitres'],1100);self.assertEqual(d['beveragesLitres'],800);self.assertEqual(d['wellnessStorageLitres'],1000)
    def test_identity_joins_companies_not_plate(self):
        m=self.model([fixture(),fixture(2,'JIVO_MART','GP-FGM','500',9),fixture(3,arrival=10)])
        self.assertEqual(len(m['trips']),2);self.assertEqual(m['days'][0]['tripCount'],2)
    def test_missing_physical_identity_uses_gate(self):
        m=self.model([fixture(arrival=None),fixture(2,arrival=None)]);self.assertEqual(len(m['trips']),2)
    def test_partial_litres_not_invented(self):
        r,d=fixture();d['documents'][0]['items'][0]['total_litres']=None
        m=self.model([(r,d)]);self.assertFalse(m['complete']);self.assertIsNone(m['days'][0]['wellnessStorageLitres']);self.assertIsNone(m['days'][0]['operationalWellnessLitres']);self.assertEqual(m['days'][0]['combinedLitres'],1000)
    def test_recorded_litres_do_not_need_guessed_pack_conversion(self):
        r,d=fixture();d['documents'][0]['items'][0]['uom']='UNRECOGNISED'
        self.assertEqual(self.model([(r,d)])['days'][0]['combinedLitres'],1000)
    def test_header_line_mismatch_held(self):
        r,d=fixture();d['documents'][0]['items'][0]['total_litres']='900'
        self.assertFalse(self.model([(r,d)])['complete'])
    def test_detail_duplicate_rejected(self):
        r,d=fixture();d['documents'][0]['items']*=2
        with self.assertRaises(ValueError):self.model([(r,d)])
    def test_invalid_date_rejected(self):
        r,d=fixture();r['gate_out_date']=d['gate_out_date']='2026-09-07'
        with self.assertRaises(ValueError):self.model([(r,d)])
    def test_unknown_company_rejected(self):
        with self.assertRaises(ValueError): self.model([fixture(company='OTHER')])
    def test_pagination_incomplete(self):
        with self.assertRaises(ValueError):read_all(Client([{'count':2,'num_pages':1,'page':1,'results':[fixture()[0]]}]))
    def test_duplicate_list_rejected(self):
        with self.assertRaises(ValueError):read_all(Client([{'count':2,'num_pages':1,'page':1,'results':[fixture()[0],fixture()[0]]}]))
    def test_changed_pagination_rejected(self):
        with self.assertRaises(ValueError):read_all(Client([{'count':2,'num_pages':2,'page':1,'results':[fixture()[0]]},{'count':3,'num_pages':2,'page':2,'results':[fixture(2)[0]]}]))
    def test_failed_cycle_preserves_evidence_and_clock(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'out.json';old=self.model([fixture()]);file.write_text(json.dumps(old))
            with patch('collect_dispatch_now.collect',side_effect=TimeoutError):new=run_once(None,folder,file)
            self.assertFalse(new['ok']);self.assertFalse(new['complete']);self.assertEqual(new['asOf'],old['asOf']);self.assertEqual(new['days'],old['days'])
    def test_public_payload_does_not_expose_contacts(self):
        text=json.dumps(self.model([fixture()]));self.assertNotIn('9999999999',text);self.assertNotIn('driver',text);self.assertNotIn('SAME-PLATE',text)
    def test_mixed_warehouse_item_split(self):
        r,d=fixture(litres='1500');item=copy.deepcopy(d['documents'][0]['items'][0]);item.update(id=2,total_litres='500',warehouse_code='GP-FG');d['documents'][0]['items'][0]['total_litres']='1000';d['documents'][0]['items'].append(item)
        e=self.model([(r,d)])['gateEntries'][0];self.assertEqual(e['operationalWellnessLitres'],1000);self.assertEqual(e['operationalMartLitres'],500)
if __name__=='__main__':unittest.main()
