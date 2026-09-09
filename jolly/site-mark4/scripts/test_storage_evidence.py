import copy
import json
import tempfile
import unittest
from pathlib import Path
from storage_evidence import normalize, public_board
from collect_storage_evidence import collect
from live_board_feed import read_board

NOW = '2026-09-09T02:00:00+05:30'


def raw(at='2026-09-09T01:27:00+05:30', litres=591451):
    return {'provenance': {'opening_fg': {'source': 'factory_production', 'note': 'stock BH-BT + BH-PF', 'mode': 'carried ' + at, 'fetched_at': NOW}},
            'opening': {'fg_litres': litres, 'standing_l': 183190}}


class StorageEvidenceTests(unittest.TestCase):
    def test_original_clock_preserved_and_same_observation_not_appended(self):
        first = normalize(raw(), None, NOW)
        second = normalize(raw(), first, '2026-09-09T02:01:00+05:30')
        self.assertEqual(second['asOf'], '2026-09-09T01:27:00+05:30')
        self.assertEqual(len(second['snapshots']), 1)
        self.assertEqual(first['revision'], second['revision'])
        self.assertIsNone(second['physicalReconciliation']['varianceLitres'])

    def test_new_observation_is_difference_not_fictional_reconciliation(self):
        first = normalize(raw(), None, NOW)
        second = normalize(raw('2026-09-09T02:27:00+05:30', 581451), first, '2026-09-09T02:28:00+05:30')
        self.assertEqual(second['recordedChangeLitres'], -10000)
        self.assertEqual(len(second['snapshots']), 2)
        self.assertFalse(second['physicalReconciliation']['complete'])
        self.assertIsNone(second['physicalReconciliation']['calculatedClosingLitres'])

    def test_gp_scope_and_missing_quantity_refused(self):
        for change in ['scope', 'missing', 'negative', 'bool']:
            value = raw()
            if change == 'scope': value['provenance']['opening_fg']['note'] += ' + GP-FG'
            if change == 'missing': value['opening'].pop('fg_litres')
            if change == 'negative': value['opening']['fg_litres'] = -1
            if change == 'bool': value['opening']['fg_litres'] = True
            with self.assertRaises(ValueError): normalize(value, None, NOW)

    def test_same_clock_conflict_and_backward_source_refused(self):
        first = normalize(raw(), None, NOW)
        with self.assertRaises(ValueError): normalize(raw(litres=1), first, NOW)
        with self.assertRaises(ValueError): normalize(raw('2026-09-09T00:27:00+05:30'), first, NOW)

    def test_failed_read_retains_quantity_date_and_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'sim').mkdir()
            source = root / 'sim/live-inputs.json'; source.write_text(json.dumps(raw()))
            output = root / 'storage.json'; first = collect(root, output)
            source.write_text('{}'); retained = collect(root, output)
            self.assertFalse(retained['ok'])
            self.assertEqual(retained['asOf'], first['asOf'])
            self.assertEqual(retained['recordedFgLitres'], 591451)
            self.assertEqual(retained['snapshots'], first['snapshots'])

    def test_publisher_strips_extra_fields_and_false_physical_claims(self):
        value = normalize(raw(), None, NOW)
        value['secret'] = 'CANARY'; value['snapshots'][0]['driverPhone'] = 'CANARY'
        value['physicalReconciliation'] = {'complete': True, 'varianceLitres': 0}
        clean = public_board(value)
        self.assertNotIn('CANARY', json.dumps(clean))
        self.assertFalse(clean['physicalReconciliation']['complete'])
        self.assertIsNone(clean['physicalReconciliation']['varianceLitres'])

    def test_exact_public_routes_strip_private_dispatch_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'storage-evidence.json').write_text(json.dumps(normalize(raw(), None, NOW)))
            self.assertEqual(json.loads(read_board(root, '/storage-evidence.json'))['scope'], ['BH-BT', 'BH-PF'])
            dispatch = {'version': 1, 'ok': True, 'complete': True, 'asOf': NOW, 'attemptedAt': NOW,
                'coverage': {'fromDate': '2026-09-01', 'toDate': '2026-09-09', 'privateToken': 'CANARY'},
                'days': [], 'trips': [], 'secret': 'CANARY',
                'gateEntries': [{'id': '1', 'driverPhone': 'CANARY', 'warehouseLitres': [],
                    'items': [{'code': 'FG0000001', 'name': 'Oil', 'contact': 'CANARY'}]}]}
            (root / 'dispatch-now.json').write_text(json.dumps(dispatch))
            self.assertNotIn(b'CANARY', read_board(root, '/dispatch-now.json'))
            for route in ['/../storage-evidence.json', '/dispatch-now.json?private=1']:
                with self.assertRaises(ValueError): read_board(root, route)


if __name__ == '__main__':
    unittest.main()
