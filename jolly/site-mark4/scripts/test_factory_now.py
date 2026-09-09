import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

from collect_factory_now import normalize
from live_board_feed import read_board

NOW = '2026-09-08T14:00:00+00:00'

def run(code='FG0000030', state='IN_PROGRESS', active=True):
    return {'id': 1, 'line_name': 'JP Machine', 'date': '2026-09-08', 'item_code': code,
            'product': 'MUSTARD 1 LTR 20 PCS', 'status': state, 'pieces_per_case': 20,
            'litres_per_piece': '1', 'total_production': '0', 'updated_at': '2026-09-08T10:00:00+05:30',
            'segments': [{'is_active': active, 'start_time': '2026-09-08T09:00:00+05:30',
                          'end_time': None if active else '2026-09-08T10:00:00+05:30',
                          'produced_cases': '12', 'updated_at': '2026-09-08T10:00:00+05:30'}]}

class FactoryNowTests(unittest.TestCase):
    def test_running_uses_live_status_and_segment_not_header(self):
        r = run()
        board = normalize([r], [{**r, 'live_status': 'RUNNING'}], [], NOW)
        a = board['lines'][0]
        self.assertEqual(a['status'], 'RUNNING')
        self.assertEqual(a['runs'][0]['producedPieces'], 240)
        self.assertEqual(a['runs'][0]['producedLitres'], 240)
        self.assertEqual(a['runs'][0]['sourceUpdatedAt'], r['updated_at'])
        self.assertEqual(board['asOf'], NOW)

    def test_stopped_header_remains_in_progress(self):
        r = run(active=False)
        a = normalize([r], [{**r, 'live_status':'STOPPED'}], [], NOW)['lines'][0]
        self.assertEqual(a['status'], 'STOPPED')

    def test_targets_convert_cases_and_closed_segment_time_excludes_active(self):
        r = run()
        r['required_qty'] = '1000'
        r['total_running_minutes'] = 9999  # header roll-up is not our basis
        r['segments'][0]['duration_minutes'] = 900  # active is not a closed record
        r['segments'].insert(0, {**r['segments'][0], 'is_active': False,
            'start_time': '2026-09-08T08:00:00+05:30',
            'end_time': '2026-09-08T08:30:00+05:30', 'duration_minutes': 30})
        result = normalize([r], [{**r, 'live_status':'RUNNING'}], [], NOW)['lines'][0]['runs'][0]
        self.assertEqual(result['targetPieces'], 20000)
        self.assertEqual(result['targetLitres'], 20000)
        self.assertEqual(result['recordedRunningMinutes'], 30)
        self.assertNotIn('expectedEndAt', result)

    def test_unknown_targets_and_closed_duration_are_not_zero(self):
        for target in (None, 'NaN', -1, True):
            r = run(active=False)
            r['required_qty'] = target
            result = normalize([r], [{**r, 'live_status':'STOPPED'}], [], NOW)['lines'][0]['runs'][0]
            self.assertIsNone(result['targetPieces'])
            self.assertIsNone(result['targetLitres'])
            self.assertIsNone(result['recordedRunningMinutes'])
        r['required_qty'] = '1000'
        r['pieces_per_case'] = 0
        result = normalize([r], [{**r, 'live_status':'STOPPED'}], [], NOW)['lines'][0]['runs'][0]
        self.assertIsNone(result['targetPieces'])

    def test_new_metrics_survive_public_whitelist_without_private_fields(self):
        r = run(active=False)
        r['required_qty'] = '1000'
        r['rated_speed'] = '5400.00'
        r['segments'][0]['duration_minutes'] = 60
        board = normalize([r], [{**r, 'live_status':'STOPPED'}], [], NOW)
        board['lines'][0]['runs'][0]['privateToken'] = 'CANARY'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'factory-now.json').write_text(json.dumps(board))
            published = read_board(root, '/factory-now.json', dt.datetime.fromisoformat(NOW))
            result = json.loads(published)['lines'][0]['runs'][0]
            self.assertEqual(result['targetPieces'], 20000)
            self.assertEqual(result['recordedRunningMinutes'], 60)
            self.assertEqual(result['ratedSpeedPiecesPerHour'], 5400)
            self.assertNotIn(b'CANARY', published)

    def test_source_speed_is_pieces_per_hour_and_invalid_speed_stays_unknown(self):
        for speed, expected in [('5400.00', 5400), (0, 0), (None, None), ('NaN', None), (-1, None), (True, None), ('Infinity', None)]:
            r = run()
            r['rated_speed'] = speed
            result = normalize([r], [{**r, 'live_status':'RUNNING'}], [], NOW)['lines'][0]['runs'][0]
            self.assertEqual(result['ratedSpeedPiecesPerHour'], expected)

    def test_malformed_segment_timing_never_reports_zero_minutes(self):
        for malformed in (None, 'invalid', [{**run()['segments'][0], 'end_time':'2026-09-08T10:00:00+05:30'}]):
            r = run(); r['segments'] = malformed
            result = normalize([r], [{**r, 'live_status':'RUNNING'}], [], NOW)['lines'][0]
            self.assertEqual(result['coverage'], 'conflict')
            self.assertIsNone(result['runs'][0]['recordedRunningMinutes'])

    def test_conflicting_sources_unknown(self):
        r = run()
        a = normalize([r], [{**r, 'live_status':'STOPPED'}], [], NOW)['lines'][0]
        self.assertEqual(a['coverage'], 'conflict')
        self.assertEqual(a['status'], 'UNKNOWN')

    def test_multiple_active_runs_not_silently_selected(self):
        a,b = run(), {**run(), 'id':2}
        row = normalize([a,b], [{**r, 'live_status':'RUNNING'} for r in [a,b]], [], NOW)['lines'][0]
        self.assertEqual(row['coverage'], 'conflict')

    def test_closed_detail_cannot_be_running(self):
        for status in ('COMPLETED','DRAFT'):
            r=run(state=status)
            self.assertEqual(normalize([r],[{**r,'live_status':'RUNNING'}],[],NOW)['lines'][0]['status'],'UNKNOWN')

    def test_header_identity_and_old_active_time_conflict(self):
        r=run()
        self.assertEqual(normalize([r],[{**r,'item_code':'FG0000081','live_status':'RUNNING'}],[],NOW)['lines'][0]['status'],'UNKNOWN')
        r['segments'][0]['start_time']='2026-09-07T09:00:00+05:30'
        self.assertEqual(normalize([r],[{**r,'live_status':'RUNNING'}],[],NOW)['lines'][0]['status'],'UNKNOWN')

    def test_timestamps_compare_instants_across_offsets(self):
        r=run();r['updated_at']='2026-09-08T14:00:00+05:30';r['segments'][0]['updated_at']='2026-09-08T10:00:00+00:00'
        a=normalize([r],[{**r,'live_status':'RUNNING'}],[],NOW)['lines'][0]
        self.assertEqual(a['runs'][0]['sourceUpdatedAt'],'2026-09-08T10:00:00+00:00')

    def test_missing_machine_and_draft_are_not_idle(self):
        r = {**run(state='DRAFT'), 'segments':[]}
        a = normalize([r], [], [], NOW)['lines'][0]
        self.assertEqual(a['coverage'], 'unreported')
        self.assertEqual(a['status'], 'UNKNOWN')

    def test_previous_open_does_not_become_today(self):
        r = {**run(), 'date':'2026-07-24','live_status':'RUNNING'}
        a = normalize([], [r], [], NOW)['lines'][0]
        self.assertEqual(a['status'], 'UNKNOWN')
        self.assertEqual(a['runs'], [])
        self.assertIn('prior-day', a['note'])

    def test_bad_quantities_unknown_not_zero(self):
        r = run();r['segments'][0]['produced_cases'] = 'NaN'
        a = normalize([r], [{**r,'live_status':'RUNNING'}], [], NOW)['lines'][0]
        self.assertIsNone(a['runs'][0]['producedPieces'])

    def test_ancient_open_header_does_not_override_current_activity(self):
        r = run()
        old = {**run(),'id':2,'date':'2026-07-24','live_status':'RUNNING'}
        a = normalize([r],[{**r,'live_status':'RUNNING'},old],[],NOW)['lines'][0]
        self.assertEqual(a['status'],'RUNNING')

    def test_requested_date_must_match(self):
        r = {**run(),'date':'2026-09-07'}
        with self.assertRaises(ValueError): normalize([r],[],[],NOW)

    def test_raw_personal_fields_not_published(self):
        r = {**run(),'operators':[{'phone':'9876543210'}],'created_by':'secret@example.com'}
        text = json.dumps(normalize([r],[{**r,'live_status':'RUNNING'}],[],NOW))
        self.assertNotIn('9876543210',text);self.assertNotIn('secret@example.com',text)
        self.assertNotIn('created_by',text)

    def test_routes_dated_baseline_and_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'baselines').mkdir()
            (root/'baselines'/'2026-09-07.json').write_text(json.dumps({'version':1,'date':'2026-09-07','day':{'date':'2026-09-07','runs':[]}}))
            d=dt.datetime.fromisoformat(NOW)
            self.assertEqual(json.loads(read_board(root,'/shift-baseline.json',d))['status'],'unavailable')
            with self.assertRaises(ValueError): read_board(root,'/factory-now.json',d)
            b=normalize([],[],[],NOW);b['privateToken']='CANARY'
            (root/'factory-now.json').write_text(json.dumps(b))
            self.assertNotIn(b'CANARY',read_board(root,'/factory-now.json',d))

if __name__ == '__main__': unittest.main()

class ReviewEvidenceTests(unittest.TestCase):
    def test_first_start_is_earliest_instant_and_notes_have_no_free_text(self):
        from collect_factory_now import public_note
        r = run(active=False)
        r['segments'][0]['remarks'] = 'TEA TIME'
        r['segments'].append({**r['segments'][0], 'start_time': '2026-09-08T03:00:00Z', 'end_time': '2026-09-08T04:00:00Z', 'remarks': 'Stopped by TEST PERSON at 12 Example Street; +91 9876543210'})
        a = normalize([r], [{**r, 'live_status': 'STOPPED'}], [], NOW)['lines'][0]['runs'][0]
        self.assertEqual(a['firstStartedAt'], '2026-09-08T03:00:00Z')
        self.assertEqual(a['timingSegments'][0]['note'], 'tea time')
        self.assertEqual(a['timingSegments'][1]['note'], 'Other remark withheld')
        self.assertNotIn('TEST PERSON', json.dumps(a))
        self.assertEqual(public_note('Other remark withheld'), 'Other remark withheld')

    def test_dated_archives_are_exact_and_path_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); archived = root / 'reviews' / '2026-09-08'; archived.mkdir(parents=True)
            value = normalize([], [], [], NOW)
            (archived / 'factory-now.json').write_text(json.dumps(value))
            (archived / 'shift-baseline.json').write_text(json.dumps({'version': 1, 'date': '2026-09-08', 'day': {'date': '2026-09-08', 'runs': []}}))
            later = dt.datetime.fromisoformat('2026-09-09T01:00:00+00:00')
            self.assertEqual(json.loads(read_board(root, '/review/2026-09-08/factory-now.json', later))['date'], '2026-09-08')
            self.assertEqual(json.loads(read_board(root, '/review/2026-09-08/shift-baseline.json', later))['date'], '2026-09-08')
            for route in ['/review/../../factory-now.json', '/review/2026-09-31/factory-now.json', '/review/2026-09-10/factory-now.json']:
                with self.assertRaises(ValueError): read_board(root, route, later)

    def test_rollover_freezes_previous_snapshot_without_replacing_existing_archive(self):
        from collect_factory_now import archive_previous
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'factory-now.json'; previous = normalize([], [], [], NOW); output.write_text(json.dumps(previous))
            archive_previous(output, {**previous, 'date': '2026-09-09'})
            target = Path(tmp) / 'reviews' / '2026-09-08' / 'factory-now.json'
            original = target.read_bytes()
            output.write_text(json.dumps({**previous, 'revision': 'changed'}))
            archive_previous(output, {**previous, 'date': '2026-09-09'})
            self.assertEqual(target.read_bytes(), original)

    def test_archive_publisher_rechecks_remark_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); value = normalize([run()], [{**run(), 'live_status': 'RUNNING'}], [], NOW)
            value['lines'][0]['runs'][0]['timingSegments'][0]['note'] = 'TEST PERSON 12 Example Street'
            value['lines'][0]['runs'][0]['timingSegments'][0]['operator'] = 'CANARY'
            (root / 'factory-now.json').write_text(json.dumps(value))
            published = read_board(root, '/factory-now.json', dt.datetime.fromisoformat(NOW))
            self.assertNotIn(b'TEST PERSON', published); self.assertNotIn(b'CANARY', published)

    def test_archive_publish_failure_never_leaves_partial_final_bytes(self):
        from collect_factory_now import archive_previous
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'factory-now.json'
            previous = normalize([], [], [], NOW)
            output.write_text(json.dumps(previous)); original = output.read_bytes()
            with patch('collect_factory_now.os.link', side_effect=OSError('disk failed')):
                with self.assertRaises(OSError): archive_previous(output, {**previous, 'date': '2026-09-09'})
            self.assertEqual(output.read_bytes(), original)
            self.assertFalse((Path(tmp) / 'reviews' / '2026-09-08' / 'factory-now.json').exists())
