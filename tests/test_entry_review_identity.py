"""Regression checks for exact JSON identity and non-approving reviewer writes."""
import copy
import json
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from tracker.entry_review_store import EntryReviewStore, ReviewStoreError
from tracker.entry_sources import canonical, digest
from test_entry_review_store import request, NOW, LATER, T2
from test_entry_review_recovery import matching


class ReviewIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'review'
        self.store = EntryReviewStore(self.root)

    def first(self, value=None):
        return self.store.record(request() if value is None else value,
                                 expected_revision=None, now=NOW)['revision']

    def decision(self, action='retain_hold'):
        return {'proposal_id': self.store.read()['register']['proposals'][0]['id'],
                'reviewer': 'synthetic-reviewer', 'decision': action,
                'rationale': 'Synthetic verification only; retain the source evidence.'}

    def test_rehashed_boolean_schema_versions_cannot_equal_integer_versions(self):
        for location in ('event', 'register'):
            with self.subTest(location=location):
                root = Path(self.tmp.name) / location
                store = EntryReviewStore(root)
                store.record(request(), expected_revision=None, now=NOW)
                path = root / 'review.sqlite3'
                with sqlite3.connect(path) as conn:
                    event = json.loads(conn.execute('SELECT payload FROM events WHERE seq=1').fetchone()[0])
                    target = event if location == 'event' else event['register']
                    target['schema_version'] = True  # Python equality must not erase JSON type differences.
                    identifier = digest(event)
                    conn.execute('UPDATE events SET payload=?,revision=? WHERE seq=1', (canonical(event), identifier))
                    conn.execute('UPDATE meta SET head=?', (identifier,))
                before = path.read_bytes()
                with self.assertRaisesRegex(ReviewStoreError, 'review_replay_mismatch'):
                    store.read()
                self.assertEqual(path.read_bytes(), before)
                with self.assertRaisesRegex(ReviewStoreError, 'review_replay_mismatch'):
                    store.recover()

    def test_numerically_equal_boolean_change_is_a_different_guidance_revision(self):
        original = matching()
        original['records'][0]['synthetic_extension'] = {'enabled': True}
        original['baselines'][0]['guidance_hashes'] = {
            r['id']: digest(r) for r in original['records']}
        head = self.first(original)
        self.assertEqual(self.store.read()['register']['proposals'], [])
        changed = copy.deepcopy(original)
        changed['records'][0]['synthetic_extension']['enabled'] = 1
        changed['captures'][0]['checked_at'] = T2
        changed['baselines'][0]['guidance_hashes'] = {
            r['id']: digest(r) for r in changed['records']}
        with self.assertRaisesRegex(ReviewStoreError, 'review_guidance_revision_mismatch'):
            self.store.record(changed, expected_revision=head, now=LATER)
        saved = self.store.read()
        self.assertEqual(saved['revision'], head)
        self.assertIs(saved['records'][0]['synthetic_extension']['enabled'], True)

    def test_lost_disposition_acknowledgement_replays_without_clearing_hold(self):
        head = self.first()
        before = self.store.read()
        decision = self.decision('request_guidance_revision')
        commit = self.store._commit
        def lost_ack(conn):
            commit(conn)
            raise OSError('synthetic lost acknowledgement')
        with patch.object(self.store, '_commit', side_effect=lost_ack):
            with self.assertRaises(ReviewStoreError):
                self.store.disposition(decision, expected_revision=head, now=LATER)
        replay = self.store.disposition(decision, expected_revision=head, now=LATER + timedelta(hours=1))
        self.assertTrue(replay['replayed'])
        self.assertEqual(replay['reviewer_dispositions'], 1)
        after = self.store.read()
        self.assertEqual(after['register'], before['register'])
        self.assertEqual(after['records'], before['records'])
        self.assertEqual(after['events'][-1]['request'], decision)
        self.assertEqual(after['events'][-1]['saved_at'], '2026-09-28T16:00:00.000Z')

    def test_competing_reviewer_disposition_is_not_silently_overwritten(self):
        head = self.first()
        before = self.store.read()['register']
        loser = self.decision()
        winner = self.decision('request_guidance_revision')
        competitor = EntryReviewStore(self.root)
        initialize = self.store._initialize
        def intervening():
            competitor.disposition(winner, expected_revision=head, now=LATER)
            initialize()
        with patch.object(self.store, '_initialize', side_effect=intervening):
            with self.assertRaisesRegex(ReviewStoreError, 'stale_review_revision'):
                self.store.disposition(loser, expected_revision=head, now=LATER + timedelta(hours=1))
        result = self.store.read()
        self.assertEqual(len(result['events']), 2)
        self.assertEqual(result['events'][-1]['request'], winner)
        self.assertEqual(result['register'], before)


if __name__ == '__main__':
    unittest.main()
