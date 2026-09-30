"""Persistent live entry capture operator path. Network is mocked in tests."""
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from unittest.mock import patch

from tracker.entry_sources import PROFILES, PROFILE_VERSION, digest
from tracker.entry_html import inspect_html
from tracker.entry_review_store import EntryReviewStore, ReviewStoreError
from tracker.entry_review_live import run_live_capture, main

ROOT=Path(__file__).resolve().parents[1]
RECORDS=json.loads((ROOT/'data/rules.json').read_text())+json.loads((ROOT/'data/entry-notes.json').read_text())
CHECKED='2026-09-29T14:00:00.000Z'
NOW=datetime(2026,9,29,15,0,tzinfo=timezone.utc)

def fake_pair(code, *, failed=False, checked=CHECKED):
    profile=PROFILES[code]
    if failed:
        capture={'source_url':profile['url'],'final_url':None,'checked_at':checked,'status':'failed','content_type':None,'html':None}
        receipt={'park_code':code,'source_url':profile['url'],'started_at':checked,'checked_at':checked,
                 'http_status':503,'reason':'http_not_success','byte_count':0,'raw_sha256':None}
        return capture,receipt
    body='<html><body><h1>'+escape(profile['heading'])+'</h1>'
    body+=''.join('<p>'+escape(r['evidence']['excerpt'])+'</p>' for r in RECORDS if r['park_code']==code)
    body+='<p>Synthetic retained live-capture context.</p></body></html>'
    raw=body.encode()
    capture={'source_url':profile['url'],'final_url':profile['url'],'checked_at':checked,
             'status':'success','content_type':'text/html','html':body}
    receipt={'park_code':code,'source_url':profile['url'],'started_at':checked,'checked_at':checked,
             'http_status':200,'reason':'captured','byte_count':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest()}
    return capture,receipt

def capture_all(failed_code=None, checked=CHECKED):
    return lambda code, live=False: fake_pair(code,failed=code==failed_code,checked=checked)

class LiveEntryReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.base.chmod(0o700)
        self.store=EntryReviewStore(self.base/'review')
        self.packets=self.base/'packets'

    def run_live(self, expected=None, failed_code=None, checked=CHECKED, now=NOW):
        with patch('tracker.entry_review_live.capture_source',side_effect=capture_all(failed_code,checked)):
            return run_live_capture(self.store,self.packets,expected_revision=expected,live=True,now=now)

    def check_setup(self, *, expected='empty', store=None, packets=None, flags=('--check-only',)):
        out,err=io.StringIO(),io.StringIO()
        args=[*flags,'--store',str(store or self.store.root),
              '--packet-output-dir',str(packets or self.packets),'--expected-revision',expected]
        with patch('tracker.entry_review_live.capture_source',side_effect=AssertionError('unexpected network')), \
             redirect_stdout(out),redirect_stderr(err):
            code=main(args)
        return code,out.getvalue(),err.getvalue()

    def test_offline_setup_accepts_empty_destinations_without_creating_them(self):
        public=[ROOT/'data'/name for name in ('rules.json','entry-notes.json','entry-review.json')]
        before=[p.read_bytes() for p in public]
        code,out,err=self.check_setup()
        self.assertEqual(code,0,err)
        report=json.loads(out)
        self.assertEqual(report['mode'],'private_entry_capture_preflight')
        self.assertTrue(report['setup_validated'])
        self.assertIsNone(report['ledger_revision'])
        self.assertEqual(report['recorded_batches'],0)
        self.assertEqual(report['guidance_records'],6)
        self.assertEqual(report['required_sources'],5)
        for field in ('network_performed','writes_performed','ledger_committed',
                      'approval_performed','publication_performed','public_data_written'):
            self.assertFalse(report[field])
        self.assertNotIn('review_ready',report)
        self.assertNotIn(str(self.base),out+err)
        self.assertFalse(self.store.root.exists()); self.assertFalse(self.packets.exists())
        self.assertEqual(before,[p.read_bytes() for p in public])

    def test_offline_setup_replays_existing_ledger_without_changing_private_files(self):
        first=self.run_live()
        files=[p for p in self.base.rglob('*') if p.is_file()]
        before={p:p.read_bytes() for p in files}
        code,out,err=self.check_setup(expected=first['ledger_revision'])
        self.assertEqual(code,0,err)
        report=json.loads(out)
        self.assertEqual(report['ledger_revision'],first['ledger_revision'])
        self.assertEqual(report['recorded_batches'],1)
        self.assertEqual(report['pending_proposals'],6)
        self.assertFalse(report['network_performed']); self.assertFalse(report['writes_performed'])
        self.assertNotIn('Synthetic retained live-capture context',out)
        self.assertNotIn(str(self.base),out+err)
        self.assertEqual(before,{p:p.read_bytes() for p in self.base.rglob('*') if p.is_file()})

    def test_offline_setup_refuses_unsafe_destinations_without_creation(self):
        insecure=self.base/'insecure'; insecure.mkdir(mode=0o755)
        linked=self.base/'linked'; linked.symlink_to(self.base,target_is_directory=True)
        cases=[
            (insecure/'review',self.packets,'insecure_private_permissions'),
            (self.base/'missing'/'review',self.packets,'private_capture_destination_unavailable'),
            (self.store.root,insecure/'packets','insecure_private_permissions'),
            (self.store.root,self.store.root/'packets','overlapping_live_review_paths'),
            (linked/'review',self.packets,'symlink_private_path'),
            (ROOT/'unsafe-test-ledger',self.packets,'protected_repository_path'),
        ]
        for store,packets,reason in cases:
            with self.subTest(reason=reason):
                code,out,err=self.check_setup(store=store,packets=packets)
                self.assertEqual(code,2); self.assertEqual(out,'')
                self.assertEqual(err,reason+'\n')
                self.assertNotIn(str(self.base),err)
                self.assertFalse(store.exists()); self.assertFalse(packets.exists())

    def test_offline_setup_refuses_stale_or_malformed_expected_head(self):
        first=self.run_live(); before=self.store.path.read_bytes()
        for expected,reason in [('empty','stale_review_revision'),
                                ('0'*64,'stale_review_revision'),
                                ('/private/sentinel/head','invalid_expected_revision')]:
            with self.subTest(expected=expected):
                code,out,err=self.check_setup(expected=expected)
                self.assertEqual(code,2); self.assertEqual(out,'')
                self.assertEqual(err,reason+'\n')
                self.assertEqual(before,self.store.path.read_bytes())
        self.assertEqual(self.store.read()['revision'],first['ledger_revision'])

    def test_offline_setup_refuses_unreadable_initial_inventory(self):
        with patch('tracker.entry_review_live.RECORDS_FILE',self.base/'missing-private-inventory'):
            code,out,err=self.check_setup()
        self.assertEqual(code,2); self.assertEqual(out,'')
        self.assertEqual(err,'invalid_live_review_inventory\n')
        self.assertFalse(self.store.root.exists()); self.assertFalse(self.packets.exists())

    def test_offline_and_live_modes_are_mutually_exclusive(self):
        code,out,err=self.check_setup(flags=('--check-only','--live'))
        self.assertEqual(code,2); self.assertEqual(out,'')
        self.assertEqual(err,'invalid_live_review_arguments\n')
        self.assertFalse(self.store.root.exists()); self.assertFalse(self.packets.exists())

    def test_live_capture_refuses_missing_or_insecure_ledger_parent_before_requests(self):
        insecure=self.base/'insecure'; insecure.mkdir(mode=0o755)
        for parent in (self.base/'missing',insecure):
            with self.subTest(parent=parent):
                out,err=io.StringIO(),io.StringIO()
                with patch('tracker.entry_review_live.capture_source',side_effect=capture_all()) as capture, \
                     redirect_stdout(out),redirect_stderr(err):
                    code=main(['--live','--store',str(parent/'review'),
                              '--packet-output-dir',str(self.packets),'--expected-revision','empty'])
                self.assertEqual(code,2); self.assertEqual(out.getvalue(),'')
                capture.assert_not_called()
                self.assertFalse((parent/'review').exists())

    def test_live_opt_in_and_expected_revision_are_checked_before_network(self):
        with patch('tracker.entry_review_live.capture_source') as capture:
            with self.assertRaises(ReviewStoreError):
                run_live_capture(self.store,self.packets,expected_revision=None,live=False,now=NOW)
            capture.assert_not_called()
        first=self.run_live()
        with patch('tracker.entry_review_live.capture_source') as capture:
            with self.assertRaises(ReviewStoreError):
                run_live_capture(self.store,self.packets,expected_revision=None,live=True,now=NOW)
            capture.assert_not_called()
        self.assertEqual(self.store.read()['revision'],first['ledger_revision'])

    def test_new_store_persists_all_five_captures_and_builds_five_packets(self):
        result=self.run_live()
        state=self.store.read()
        self.assertTrue(result['capture_complete']); self.assertTrue(result['review_packets_ready'])
        self.assertTrue(result['review_ready']); self.assertTrue(result['network_performed'])
        self.assertFalse(result['approval_performed']); self.assertFalse(result['publication_performed'])
        self.assertFalse(result['public_data_written'])
        self.assertEqual(result['ledger_revision'],state['revision'])
        self.assertEqual(result['source_event_revision'],state['revision'])
        self.assertEqual(len(state['events']),1); self.assertEqual(len(state['events'][0]['request']['captures']),5)
        self.assertEqual(len(state['register']['proposals']),6)
        self.assertEqual(result['packet_count'],5)
        self.assertEqual({row['park_code'] for row in result['sources']},set(PROFILES))
        self.assertTrue(all(row['packet_status']=='ready' for row in result['sources']))
        self.assertEqual(len(list(self.packets.glob('*/index.html'))),5)
        encoded=json.dumps(result)
        self.assertNotIn('<html',encoded); self.assertNotIn('Synthetic retained live-capture context',encoded)
        self.assertNotIn(str(self.base),encoded)

    def test_existing_ledger_requires_current_head_and_appends_complete_batch(self):
        first=self.run_live()
        checked='2026-09-29T14:30:00.000Z'
        second=self.run_live(expected=first['ledger_revision'],checked=checked,
          now=datetime(2026,9,29,15,30,tzinfo=timezone.utc))
        state=self.store.read()
        self.assertEqual(len(state['events']),2)
        self.assertEqual(second['ledger_revision'],state['revision'])
        self.assertNotEqual(second['ledger_revision'],first['ledger_revision'])
        self.assertEqual({c['checked_at'] for c in state['events'][-1]['request']['captures']},{checked})
        self.assertEqual(state['records'],state['events'][0]['request']['records'])

    def test_existing_legacy_baseline_is_preserved_on_live_append(self):
        seed=json.loads((ROOT/'data/entry-review.json').read_text())
        initial_checked='2026-09-29T13:00:00.000Z'
        captures=[fake_pair(code,checked=initial_checked)[0] for code in PROFILES]
        yell_html=next(c['html'] for c in captures if c['source_url']==PROFILES['yell']['url'])
        context=inspect_html(yell_html,PROFILES['yell']['heading'])
        baseline={
            'schema_version':1,
            'source_url':PROFILES['yell']['url'],
            'profile_id':f'{PROFILE_VERSION}:yell',
            'guidance_hashes':{r['id']:digest(r) for r in RECORDS if r['park_code']=='yell'},
            'checked_at':'2026-09-29T12:00:00.000Z',
            'reviewed_at':'2026-09-29T12:30:00.000Z',
            'context':context,
            'context_hash':digest(context),
        }
        first=self.store.record(
            {'records':RECORDS,'captures':captures,'baselines':[baseline],'seed_register':seed},
            expected_revision=None,now=datetime(2026,9,29,13,30,tzinfo=timezone.utc))
        self.assertEqual(
            next(s for s in self.store.read()['events'][-1]['extraction']['sources']
                 if s['source_url']==PROFILES['yell']['url'])['reason'],
            'matching_reviewed_context')
        result=self.run_live(expected=first['revision'])
        state=self.store.read()
        yell_source=next(s for s in state['events'][-1]['extraction']['sources']
                         if s['source_url']==PROFILES['yell']['url'])
        self.assertEqual(yell_source['reason'],'matching_reviewed_context')
        self.assertFalse(any(p['source_url']==PROFILES['yell']['url'] for p in state['register']['proposals']))
        yell_row=next(row for row in result['sources'] if row['park_code']=='yell')
        self.assertEqual(yell_row['packet_status'],'not_needed')

    def test_failed_source_is_durably_recorded_and_never_gets_fake_packet(self):
        result=self.run_live(failed_code='zion')
        state=self.store.read(); event=state['events'][-1]
        zion=next(c for c in event['request']['captures'] if c['source_url']==PROFILES['zion']['url'])
        row=next(r for r in result['sources'] if r['park_code']=='zion')
        self.assertEqual(zion['status'],'failed'); self.assertIsNone(zion['html'])
        self.assertFalse(result['capture_complete']); self.assertFalse(result['review_packets_ready'])
        self.assertFalse(result['review_ready']); self.assertEqual(row['packet_status'],'context_unavailable')
        self.assertIsNone(row['packet_id']); self.assertEqual(result['packet_count'],4)
        self.assertEqual(len(state['register']['proposals']),6)
        self.assertFalse(result['approval_performed']); self.assertFalse(result['publication_performed'])

    def test_packet_failure_does_not_roll_back_committed_live_evidence(self):
        with patch('tracker.entry_review_live.capture_source',side_effect=capture_all()), \
             patch('tracker.entry_review_live.prepare_review_packet',side_effect=ReviewStoreError('synthetic_packet_failure')):
            result=run_live_capture(self.store,self.packets,expected_revision=None,live=True,now=NOW)
        state=self.store.read()
        self.assertEqual(len(state['events']),1); self.assertEqual(result['ledger_revision'],state['revision'])
        self.assertFalse(result['review_packets_ready']); self.assertFalse(result['review_ready'])
        self.assertEqual(result['packet_count'],0)
        self.assertTrue(all(row['packet_status']=='failed' for row in result['sources']))
        self.assertNotIn('synthetic_packet_failure',json.dumps(result))

    def test_invalid_packet_destination_refuses_before_network_or_store_creation(self):
        insecure=self.base/'insecure'; insecure.mkdir(mode=0o755)
        with patch('tracker.entry_review_live.capture_source') as capture:
            with self.assertRaises(ReviewStoreError):
                run_live_capture(self.store,insecure/'packets',expected_revision=None,live=True,now=NOW)
            capture.assert_not_called()
        self.assertFalse(self.store.root.exists())

    def test_cli_requires_deliberate_live_opt_in_and_sanitizes_output(self):
        out,err=io.StringIO(),io.StringIO()
        with patch('tracker.entry_review_live.capture_source') as capture,redirect_stdout(out),redirect_stderr(err):
            code=main(['--store',str(self.store.root),'--packet-output-dir',str(self.packets),'--expected-revision','empty'])
        self.assertEqual(code,2); capture.assert_not_called(); self.assertEqual(out.getvalue(),'')
        self.assertNotIn(str(self.base),err.getvalue())

        out,err=io.StringIO(),io.StringIO()
        with patch('tracker.entry_review_live.capture_source',side_effect=capture_all()),redirect_stdout(out),redirect_stderr(err):
            code=main(['--live','--store',str(self.store.root),'--packet-output-dir',str(self.packets),'--expected-revision','empty'])
        self.assertEqual(code,0,err.getvalue())
        report=json.loads(out.getvalue())
        self.assertTrue(report['review_ready']); self.assertEqual(report['packet_count'],5)
        self.assertNotIn(str(self.base),out.getvalue()+err.getvalue())
        self.assertNotIn('Synthetic retained live-capture context',out.getvalue()+err.getvalue())

    def test_partial_capture_cli_returns_one_after_persisting_evidence(self):
        out,err=io.StringIO(),io.StringIO()
        with patch('tracker.entry_review_live.capture_source',side_effect=capture_all('grca')),redirect_stdout(out),redirect_stderr(err):
            code=main(['--live','--store',str(self.store.root),'--packet-output-dir',str(self.packets),'--expected-revision','empty'])
        self.assertEqual(code,1,err.getvalue())
        self.assertEqual(len(self.store.read()['events']),1)
        self.assertFalse(json.loads(out.getvalue())['review_ready'])
        self.assertEqual(err.getvalue(),'')

if __name__=='__main__': unittest.main()
