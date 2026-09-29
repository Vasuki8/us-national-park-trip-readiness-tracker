"""Offline synthetic evidence tests. No actual park/source claims."""
import copy
import hashlib
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from tracker.entry_review_store import EntryReviewStore, ReviewStoreError

T0 = '2026-09-28T10:00:00Z'
T1 = '2026-09-28T12:00:00Z'
T2 = '2026-09-28T14:00:00Z'
NOW = datetime(2026, 9, 28, 15, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 28, 16, tzinfo=timezone.utc)
URL = 'https://www.nps.gov/yose/planyourvisit/reservations.htm'
QUOTE = 'Synthetic guidance for testing, not actual park conditions.'

def request(checked=T1):
    r = {'id':'synthetic-yose', 'park_code':'yose','reviewed_at':T0,'review_status':'reviewed',
         'evidence':{'url':URL,'excerpt':QUOTE,'content_hash':hashlib.sha256(QUOTE.encode()).hexdigest(),
                     'reviewed_at':T0,'hash_scope':'excerpt'}}
    return {'records':[r], 'captures':[{'source_url':URL,'final_url':URL,'checked_at':checked,
           'status':'success','content_type':'text/html','html':f'<html><body><h1>Entrance Reservations</h1><p>{QUOTE}</p></body></html>'}],
            'baselines':[], 'seed_register':{'schema_version':1,'proposals':[]}}

class ReviewStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'private-review'; self.store = EntryReviewStore(self.root)
    def record(self, value=None, expected=None, now=NOW):
        return self.store.record(request() if value is None else value, expected_revision=expected, now=now)
    def test_read_absent_is_read_only(self):
        self.assertEqual(self.store.read()['revision'], None); self.assertFalse(self.root.exists())
    def test_capture_context_and_proposals_survive_restart_together(self):
        saved = self.record(); current = EntryReviewStore(self.root).read()
        self.assertEqual(current['revision'],saved['revision']); self.assertEqual(len(current['events']),1)
        event=current['events'][0]
        self.assertEqual(event['extraction']['sources'][0]['reason'],'context_not_reviewed')
        self.assertIn(QUOTE,event['extraction']['sources'][0]['context']['text'])
        self.assertEqual(current['register']['proposals'][0]['reason'],'check_failed')
        self.assertEqual(event['request'],request())
        self.assertEqual(current['records'][0]['reviewed_at'],T0)
    def test_private_files_have_owner_only_permissions(self):
        self.record(); self.assertEqual(self.root.stat().st_mode & 0o777,0o700)
        self.assertEqual((self.root/'review.sqlite3').stat().st_mode & 0o777,0o600)
    def test_invalid_capture_does_not_create_storage(self):
        v=request(); v['captures'][0]['final_url']='https://evil.example/'
        with self.assertRaises(ReviewStoreError): self.record(v)
        self.assertFalse(self.root.exists())
    def test_stale_expected_revision_refuses_and_keeps_current(self):
        head=self.record()['revision']
        with self.assertRaises(ReviewStoreError): self.record(request(T2),now=LATER)
        self.assertEqual(self.store.read()['revision'],head)
    def test_exact_retry_acknowledges_original_commit_without_duplicate(self):
        head=self.record()['revision']; again=self.record(now=LATER)
        self.assertTrue(again['replayed']); self.assertEqual(again['revision'],head)
        self.assertEqual(len(self.store.read()['events']),1)
    def test_old_attempt_cannot_replay_over_later_matching_or_failed_checks(self):
        head=self.record()['revision']; v=request('2026-09-28T11:00:00Z')
        with self.assertRaises(ReviewStoreError): self.record(v,expected=head,now=LATER)
    def test_revised_guidance_requires_explicit_reconciliation(self):
        head=self.record()['revision']; v=request(T2); v['records'][0]['summary']='Changed approved record'
        with self.assertRaises(ReviewStoreError): self.record(v,expected=head,now=LATER)
        self.assertEqual(self.store.read()['revision'],head)
    def test_reviewer_disposition_retains_hold_and_original_evidence(self):
        head=self.record()['revision']; before=self.store.read(); proposal=before['register']['proposals'][0]['id']
        decision={'proposal_id':proposal,'reviewer':'test-reviewer','decision':'retain_hold','rationale':'The synthetic exception needs another review.'}
        self.store.disposition(decision,expected_revision=head,now=LATER)
        after=self.store.read(); self.assertEqual(after['register'],before['register'])
        self.assertEqual(after['records'],before['records']); self.assertEqual(after['events'][-1]['request'],decision)
    def test_unknown_proposal_stale_decision_and_approve_cannot_clear_hold(self):
        head=self.record()['revision']; p=self.store.read()['register']['proposals'][0]['id']
        for decision, proposal, expected in [('approve',p,head),('retain_hold','0'*64,head),('retain_hold',p,None)]:
            with self.subTest(decision=decision,proposal=proposal),self.assertRaises(ReviewStoreError):
                self.store.disposition({'proposal_id':proposal,'decision':decision,'reviewer':'reviewer','rationale':'Review needed.'},expected_revision=expected,now=LATER)
        self.assertEqual(self.store.read()['revision'],head)
    def test_read_and_returned_objects_cannot_mutate_committed_state(self):
        self.record(); path=self.root/'review.sqlite3'; before=path.read_bytes()
        state=self.store.read(); state['register']['proposals'].clear()
        self.assertTrue(self.store.read()['register']['proposals']); self.assertEqual(path.read_bytes(),before)
    def test_database_tampering_is_not_a_new_empty_ledger(self):
        self.record()
        with sqlite3.connect(self.root/'review.sqlite3') as conn:
            conn.execute('DELETE FROM events')
        with self.assertRaises(ReviewStoreError): self.store.read()
    def test_public_repo_and_symlink_destinations_are_refused(self):
        repo=Path(__file__).resolve().parents[1]
        for target in (repo/'data'/'review-private',repo/'public'/'review-private'):
            with self.assertRaises(ReviewStoreError): EntryReviewStore(target).record(request(),expected_revision=None,now=NOW)
        self.root.symlink_to(Path(self.tmp.name),target_is_directory=True)
        with self.assertRaises(ReviewStoreError): self.record()
    def test_group_readable_store_is_not_silently_accepted_or_chmodded(self):
        self.record(); os.chmod(self.root,0o755)
        with self.assertRaises(ReviewStoreError): self.store.read()
        self.assertEqual(self.root.stat().st_mode & 0o777,0o755)
    def test_hardlinked_database_and_foreign_directory_refuse(self):
        self.record(); os.link(self.root/'review.sqlite3',Path(self.tmp.name)/'other.sqlite3')
        with self.assertRaises(ReviewStoreError): self.store.read()
    def test_foreign_files_are_not_adopted_or_overwritten(self):
        self.root.mkdir(mode=0o700); f=self.root/'evidence.txt'; f.write_text('keep me')
        with self.assertRaises(ReviewStoreError): self.record()
        self.assertEqual(f.read_text(),'keep me')

if __name__ == '__main__': unittest.main()
