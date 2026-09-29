"""Ledger replay, sticky review and real process-interruption contracts."""
import copy
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from tracker.entry_review_store import EntryReviewStore, ReviewStoreError
from tracker.entry_review_model import gate
from tracker.entry_sources import digest, canonical
from tracker.entry_html import inspect_html
from test_entry_review_store import request, NOW, LATER, T1, T2, T0, URL

def matching(checked=T1):
    value=request(checked); ctx=inspect_html(value['captures'][0]['html'],'Entrance Reservations')
    value['baselines']=[{'schema_version':1,'source_url':URL,'profile_id':'nps-entry-body-v1:yose',
      'guidance_hashes':{value['records'][0]['id']:digest(value['records'][0])},
      'checked_at':'2026-09-28T10:30:00Z','reviewed_at':'2026-09-28T11:00:00Z',
      'context':ctx,'context_hash':digest(ctx)}]
    return value

class ReviewRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'store'; self.store=EntryReviewStore(self.root)
    def first(self,value=None):
        return self.store.record(value or request(),expected_revision=None,now=NOW)['revision']
    def test_matching_checks_are_retained_and_reject_older_checks_without_any_pending_proposal(self):
        head=self.first(matching()); state=self.store.read()
        self.assertEqual(state['register']['proposals'],[])
        self.assertEqual(state['events'][0]['checks'][0]['outcome'],'matching_excerpt')
        with self.assertRaises(ReviewStoreError):
            self.store.record(matching('2026-09-28T11:30:00Z'),expected_revision=head,now=LATER)
    def test_later_matching_context_retains_prior_hold_and_does_not_refresh_approval(self):
        head=self.first(); before=self.store.read()['register']
        self.store.record(matching(T2),expected_revision=head,now=LATER)
        state=self.store.read()
        self.assertEqual(state['register'],before); self.assertEqual(len(state['events']),2)
        self.assertEqual(state['records'][0]['reviewed_at'],T0)
        self.assertEqual(state['events'][-1]['extraction']['sources'][0]['reason'],'matching_reviewed_context')
    def test_replay_of_committed_ancestor_never_rolls_head_back(self):
        original=self.first(); current=self.store.record(request(T2),expected_revision=original,now=LATER)['revision']
        replay=self.store.record(request(),expected_revision=None,now=LATER+timedelta(hours=1))
        self.assertTrue(replay['replayed']); self.assertEqual(replay['committed_revision'],original)
        self.assertEqual(replay['revision'],current)
    def test_different_pending_seed_cannot_drop_earlier_evidence(self):
        head=self.first(); v=request(T2); v['seed_register']={'schema_version':1,'proposals':self.store.read()['register']['proposals']}
        with self.assertRaises(ReviewStoreError): self.store.record(v,expected_revision=head,now=LATER)
    def test_failed_transaction_keeps_prior_head_and_retry_works(self):
        head=self.first()
        with patch.object(self.store,'_commit',side_effect=OSError('private simulated disk error')):
            with self.assertRaises(ReviewStoreError): self.store.record(request(T2),expected_revision=head,now=LATER)
        self.assertEqual(self.store.read()['revision'],head)
        saved=self.store.record(request(T2),expected_revision=head,now=LATER)
        self.assertFalse(saved['replayed']); self.assertEqual(len(self.store.read()['events']),2)
    def test_error_after_commit_is_acknowledged_on_retry(self):
        head=self.first(); real=self.store._commit
        def lost_ack(conn):
            real(conn); raise OSError('private lost acknowledgement')
        with patch.object(self.store,'_commit',side_effect=lost_ack):
            with self.assertRaises(ReviewStoreError): self.store.record(request(T2),expected_revision=head,now=LATER)
        saved=self.store.record(request(T2),expected_revision=head,now=LATER+timedelta(hours=1))
        self.assertTrue(saved['replayed']); self.assertEqual(len(self.store.read()['events']),2)
    def test_writer_race_rechecks_expected_revision_inside_transaction(self):
        head=self.first(); competitor=EntryReviewStore(self.root); initialize=self.store._initialize
        def intervening():
            competitor.record(request(T2),expected_revision=head,now=LATER)
            initialize()
        with patch.object(self.store,'_initialize',side_effect=intervening):
            with self.assertRaises(ReviewStoreError):
                self.store.record(request('2026-09-28T14:30:00Z'),expected_revision=head,now=LATER+timedelta(hours=1))
        self.assertEqual(len(self.store.read()['events']),2)
    def test_rehashed_proposal_and_context_tampering_fail_replay(self):
        self.first(); path=self.root/'review.sqlite3'
        with sqlite3.connect(path) as conn:
            raw=conn.execute('SELECT payload FROM events WHERE seq=1').fetchone()[0]; event=json.loads(raw)
            event['register']['proposals']=[]
            conn.execute('UPDATE events SET payload=?,revision=? WHERE seq=1',(canonical(event),digest(event)))
            conn.execute('UPDATE meta SET head=?',(digest(event),))
        with self.assertRaises(ReviewStoreError): self.store.read()
    def test_rehashed_context_change_is_not_trusted_merely_because_digest_matches(self):
        self.first(); path=self.root/'review.sqlite3'
        with sqlite3.connect(path) as conn:
            event=json.loads(conn.execute('SELECT payload FROM events WHERE seq=1').fetchone()[0])
            event['extraction']['sources'][0]['reason']='matching_reviewed_context'
            conn.execute('UPDATE events SET payload=?,revision=? WHERE seq=1',(canonical(event),digest(event)))
            conn.execute('UPDATE meta SET head=?',(digest(event),))
        with self.assertRaises(ReviewStoreError): self.store.read()
    def test_capacity_refuses_without_discarding_records(self):
        head=self.first()
        with patch('tracker.entry_review_store.MAX_EVENTS',1):
            with self.assertRaises(ReviewStoreError): self.store.record(request(T2),expected_revision=head,now=LATER)
        self.assertEqual(self.store.read()['revision'],head)
    def test_bridge_does_not_inherit_keys_or_runtime_injection_flags(self):
        state=request(); fake=type('Result',(),{'returncode':0,'stdout':b'{"register":{},"checks":[]}'})()
        with patch.dict(os.environ,{'NPS_API_KEY':'not-a-key','NODE_OPTIONS':'--import=private-path'}),patch('tracker.entry_review_model.subprocess.run',return_value=fake) as run:
            gate(state['records'],[],{},'2026-09-28T15:00:00Z')
        env=run.call_args.kwargs['env']
        self.assertNotIn('NPS_API_KEY',env); self.assertNotIn('NODE_OPTIONS',env)
        self.assertEqual(run.call_args.kwargs['timeout'],10)
    def test_wal_database_refuses_before_read_can_create_sidecars(self):
        self.first()
        conn=sqlite3.connect(self.root/'review.sqlite3')
        self.assertEqual(conn.execute('PRAGMA journal_mode=WAL').fetchone()[0],'wal'); conn.close()
        before={p.name:p.read_bytes() for p in self.root.iterdir()}
        with self.assertRaises(ReviewStoreError): self.store.read()
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},before)
    def crash(self, phase):
        head=self.first(); value=request(T2)
        value['captures'][0]['html']=value['captures'][0]['html'].replace('</body>','<!--'+'x'*500000+'--></body>')
        script="""
import json,os,sys
from datetime import datetime,timezone
from pathlib import Path
from tracker.entry_review_store import EntryReviewStore
class Interrupted(EntryReviewStore):
    def _connect(self, *, write):
        conn=super()._connect(write=write)
        if write: conn.execute('PRAGMA cache_size=5')
        return conn
    def _commit(self,conn):
        if sys.argv[3]=='after': super()._commit(conn)
        os._exit(73)
Interrupted(Path(sys.argv[1])).record(json.load(sys.stdin),expected_revision=sys.argv[2],now=datetime(2026,9,28,16,tzinfo=timezone.utc))
"""
        result=subprocess.run([sys.executable,'-c',script,str(self.root),head,phase],input=json.dumps(value),text=True,capture_output=True,timeout=15)
        self.assertEqual(result.returncode,73,result.stderr)
        recovered=self.store.recover()
        self.assertEqual(recovered['recorded_batches'],1 if phase=='before' else 2)
        saved=self.store.record(value,expected_revision=head,now=LATER+timedelta(hours=1))
        self.assertEqual(saved['replayed'],phase=='after')
        self.assertEqual(len(self.store.read()['events']),2)
    def test_process_termination_before_commit_recovers_previous_evidence(self):
        self.crash('before')
    def test_process_termination_after_commit_retains_exact_commit(self):
        self.crash('after')

if __name__=='__main__': unittest.main()
